from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app._settings import settings


def get_db_engine(database_url: str) -> AsyncEngine:
    """
    Creates async engine for a given database url
    """
    return create_async_engine(
        database_url,
        echo=False,
        future=True,
    )


async def session_injector() -> AsyncGenerator[AsyncSession, None]:
    """
    Returns a session for fastapi to inject into routers
    """
    engine = get_db_engine(settings.DATABASE_URI)
    async_session = async_sessionmaker(engine, class_=AsyncSession)
    async with async_session() as session:
        yield session


async_session_annotated_type = Annotated[AsyncSession, Depends(session_injector)]


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    """
    Creates async session for a given engine
    """
    engine = get_db_engine(settings.DATABASE_URI)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
