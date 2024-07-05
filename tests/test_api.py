from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketState
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.game.game_manager import GameManager
from app.game.models import PlayerPoint
from app.game.schema import ClientAnswer, MessageType
from app.sample_data import sample_questions


@patch("app._security.uuid1", Mock(return_value="fake_client_id"))
def test_home_page(test_client: TestClient) -> None:
    res = test_client.get("/")
    assert "fake_client_id" in res.text
    assert str(sample_questions[0]["question_id"]) in res.text
    assert str(sample_questions[0]["question"]) in res.text
    for option in sample_questions[0]["options"]:
        assert option in res.text


@patch("app._security.uuid1", Mock(return_value="fake_client_id"))
def test_online_players(test_client: TestClient) -> None:
    res = test_client.get("/")
    assert "fake_client_id" in res.text
    assert str(sample_questions[0]["question_id"]) in res.text
    assert str(sample_questions[0]["question"]) in res.text
    for option in sample_questions[0]["options"]:
        assert option in res.text


@pytest.mark.asyncio
async def test_ws(test_client: TestClient, test_token1: tuple[str, str]) -> None:
    with test_client.websocket_connect(f"/ws?token={test_token1[0]}"):
        assert test_token1[1] in GameManager.online_players
        assert GameManager.online_players[test_token1[1]].client_state == WebSocketState.CONNECTED


@pytest.mark.asyncio
async def test_ws__terminate_connection(test_client: TestClient, test_token1: tuple[str, str]) -> None:
    with test_client.websocket_connect(f"/ws?token={test_token1[0]}"):
        assert test_token1[1] in GameManager.online_players

    # outside context manager connection will be closed
    assert GameManager.online_players == {}


@pytest.mark.asyncio
async def test_ws__correct_answer(
    test_client: TestClient,
    test_client_answer_obj: ClientAnswer,
    test_token1: tuple[str, str],
    test_token2: tuple[str, str],
) -> None:
    with test_client.websocket_connect(f"/ws?token={test_token1[0]}") as websocket1:
        with test_client.websocket_connect(f"/ws?token={test_token2[0]}") as websocket2:
            # making sure Game Manager is in the same state of test env in terms of game round
            GameManager._round_id = "round_id"
            test_client_answer_obj.question_id = str(GameManager.get_current_question()["question_id"])
            websocket1.send_json(test_client_answer_obj.model_dump())

            result_correct_answer_message = websocket1.receive_json()
            assert result_correct_answer_message == {"message_type": "correct_answer"}

            next_question_message_socket1 = websocket1.receive_json()
            assert next_question_message_socket1["message_type"] == MessageType.SERVER_NEW_QUESTION
            assert next_question_message_socket1["question_id"] == GameManager.get_current_question()["question_id"]

            result2 = websocket2.receive_json()
            assert result2 == {"message_type": "too_late"}

            next_question_message_socket2 = websocket2.receive_json()
            assert next_question_message_socket2["message_type"] == MessageType.SERVER_NEW_QUESTION
            assert next_question_message_socket2["question_id"] == GameManager.get_current_question()["question_id"]


@pytest.mark.asyncio
async def test_ws__wrong_answer(
    test_client: TestClient, test_client_answer_obj: ClientAnswer, test_token1: tuple[str, str]
) -> None:
    with test_client.websocket_connect(f"/ws?token={test_token1[0]}") as websocket:
        test_client_answer_obj.question_id = str(GameManager.get_current_question()["question_id"])
        websocket.send_json(test_client_answer_obj.model_dump())
        result = websocket.receive_json()
        assert result == {"message_type": "wrong_answer"}


# sqlite doesn't guarantee data consistency, test should be checked with a SQL database like postgres
# to keep pipeline easy for assignment, we stick to sqlite for now
@pytest.mark.asyncio
@pytest.mark.skip
async def test_ws__uniqueness_of_correct_answer_per_round(
    test_client: TestClient, test_client_answer_obj: ClientAnswer, test_token1: tuple[str, str]
) -> None:
    with test_client.websocket_connect(f"/ws?token={test_token1[0]}") as websocket:
        session: AsyncSession

        # save a point from another user in database
        async with get_session() as session:
            session.add(
                PlayerPoint(
                    client_id=test_token1[1], question_id=sample_questions[0]["question_id"], game_round_id="round_1"
                )
            )
            await session.commit()

        # making sure Game Manager is in the same state of test env in terms of game round
        GameManager._round_id = "round_id"
        test_client_answer_obj.question_id = str(GameManager.get_current_question()["question_id"])
        websocket.send_json(test_client_answer_obj.model_dump())

        result = websocket.receive_json()
        assert result == {"message_type": "too_late"}
