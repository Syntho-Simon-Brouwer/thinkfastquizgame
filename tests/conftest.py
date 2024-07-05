import os
from collections.abc import AsyncGenerator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel

from app._security import create_signed_token
from app.db import get_db_engine
from app.game.schema import ClientAnswer, MessageType
from app.main import app
from app.sample_data import sample_questions


@pytest.fixture(autouse=True)
async def setup_test_env() -> AsyncGenerator[None, None]:
    engine = get_db_engine(os.environ.get("DATABASE_URI", "sqlite+aiosqlite:///testdb.db"))
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        yield
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture
def test_client() -> TestClient:
    return TestClient(app)


@pytest.fixture
async def test_token1() -> tuple[str, str]:
    return await create_signed_token()


@pytest.fixture
async def test_token2() -> tuple[str, str]:
    return await create_signed_token()


@pytest.fixture
def test_client_answer_obj() -> ClientAnswer:
    return ClientAnswer(
        message_type=MessageType.CLIENT_PUSH_ANSWER,
        answer=str(sample_questions[0]["answer"]),
        question_id=str(sample_questions[0]["question_id"]),
    )
