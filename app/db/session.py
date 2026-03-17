from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None
_engine_url: str | None = None


def get_engine() -> AsyncEngine:
    global _engine, _sessionmaker, _engine_url
    settings = get_settings()
    if _engine is None or _engine_url != settings.database_url:
        _engine = create_async_engine(settings.database_url, pool_pre_ping=True)
        _sessionmaker = async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession)
        _engine_url = settings.database_url
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    if _sessionmaker is None:
        get_engine()
    assert _sessionmaker is not None
    return _sessionmaker


async def get_db_session() -> AsyncIterator[AsyncSession]:
    session_factory = get_sessionmaker()
    async with session_factory() as session:
        yield session


async def check_database_health() -> bool:
    engine = get_engine()
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))
    return True


async def dispose_engine() -> None:
    global _engine, _sessionmaker, _engine_url
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _sessionmaker = None
    _engine_url = None
