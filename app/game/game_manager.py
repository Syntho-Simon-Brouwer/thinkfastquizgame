import asyncio
import uuid
from logging import getLogger

from fastapi.websockets import WebSocket, WebSocketDisconnect
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.game.schema import ClientAnswer, Message, MessageType, Question
from app.game.services import save_user_point
from app.sample_data import sample_questions

logger = getLogger(__file__)


class GameManager:
    online_players: dict[str, WebSocket] = {}
    _current_question_cursor: int = 0
    _round_id: str = str(uuid.uuid1())

    @classmethod
    async def add_player(cls, client_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        cls.online_players[client_id] = websocket
        try:
            while True:
                parsed_data = await websocket.receive_json()
                validated_data = ClientAnswer(**parsed_data)
                await cls.receive_answer(client_id, validated_data)
        except ValidationError as err:
            logger.error(str(err))
        except WebSocketDisconnect:
            await cls.kickout_player(client_id)

    @classmethod
    def is_player_online(cls, client_id: str) -> bool:
        return client_id in cls.online_players  # loop-up with order BIG-O(1)

    @classmethod
    async def kickout_player(cls, client_id: str) -> None:
        cls.online_players.pop(client_id, None)

    @classmethod
    def get_current_question(cls) -> dict[str, str | list[str]]:
        current_question = sample_questions[cls._current_question_cursor]
        return current_question

    @classmethod
    def _move_to_next_question(cls) -> None:
        cls._current_question_cursor += 1
        cls._current_question_cursor %= len(sample_questions)

        if cls._current_question_cursor == 0:
            cls._round_id = str(uuid.uuid1())

    @classmethod
    async def receive_answer(cls, client_id: str, message: ClientAnswer) -> None:
        if cls.get_current_question()["question_id"] == message.question_id:
            if cls.get_current_question()["answer"] != message.answer:
                return await cls._send_single_message(
                    Message(message_type=MessageType.SERVER_FAILED_WRONG_ANSWER), client_id
                )

            session: AsyncSession
            async with get_session() as session:
                try:
                    # saving clients point in case of correct answer , consistency of data is guaranteed by Postgresql
                    # if two concurrent requests try to commit a correct answer only the first one will be successful
                    await save_user_point(client_id, message.question_id, cls._round_id, session)

                    # send failure message to all players except who answered correctly concurrently
                    await asyncio.gather(
                        cls._broadcast_message(Message(message_type=MessageType.SERVER_FAILED_TOO_LATE), {client_id}),
                        cls._send_single_message(Message(message_type=MessageType.SERVER_CORRECT_ANSWER), client_id),
                    )

                    # move to the next question
                    cls._move_to_next_question()

                    # send the next question to every player
                    await cls._broadcast_message(
                        Question(
                            message_type=MessageType.SERVER_NEW_QUESTION,
                            question_id=str(sample_questions[cls._current_question_cursor]["question_id"]),
                            question=str(sample_questions[cls._current_question_cursor]["question"]),
                            answer=str(sample_questions[cls._current_question_cursor]["answer"]),
                            options=list(sample_questions[cls._current_question_cursor]["options"]),
                        ),
                        set(),
                    )

                    return None

                except IntegrityError as error:
                    logger.error(str(error))
                    return await cls._send_single_message(
                        Message(message_type=MessageType.SERVER_FAILED_TOO_LATE), client_id
                    )

        return await cls._send_single_message(Message(message_type=MessageType.SERVER_INVALID_MESSAGE), client_id)

    @classmethod
    async def _send_single_message(cls, message: Message, client_id: str) -> None:
        player_socket = cls.online_players[client_id]
        if player_socket.client_state.CONNECTED:
            await player_socket.send_json(message.model_dump())

    @classmethod
    async def _broadcast_message(cls, message: Message, ignored_ids: set[str]) -> None:
        for client_id, player_socket in cls.online_players.items():
            if client_id not in ignored_ids and player_socket.client_state.CONNECTED:
                await player_socket.send_json(message.model_dump())
