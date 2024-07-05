from enum import StrEnum

from pydantic import BaseModel


class MessageType(StrEnum):
    CLIENT_PUSH_ANSWER = "push_answer"
    SERVER_NEW_QUESTION = "new_question"
    SERVER_CORRECT_ANSWER = "correct_answer"
    SERVER_FAILED_TOO_LATE = "too_late"
    SERVER_FAILED_WRONG_ANSWER = "wrong_answer"
    SERVER_INVALID_MESSAGE = "invalid_message"


class Message(BaseModel):
    message_type: MessageType


class Question(Message):
    question_id: str
    question: str
    options: list[str]

    # TODO(alireza) this field is only for reviewers and should be removed in real world app
    answer: str


class ClientAnswer(Message):
    question_id: str
    answer: str
