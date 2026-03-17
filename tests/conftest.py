from __future__ import annotations

import os
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient


@pytest.fixture(scope="session", autouse=True)
def configure_test_environment(tmp_path_factory: pytest.TempPathFactory):
    data_dir = tmp_path_factory.mktemp("dot_swahili")
    db_path = Path(data_dir) / "test.db"
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_path.as_posix()}"
    os.environ["ALEMBIC_DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
    os.environ["SCHEDULER_ENABLED"] = "false"
    os.environ["SEED_SAMPLE_DATA"] = "false"
    os.environ["SMS_PROVIDER"] = "mock"
    os.environ["SMS_WEBHOOK_TOKEN"] = "local-webhook-token"
    os.environ["WEATHER_PROVIDER"] = "visual_crossing"
    from app.core.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest_asyncio.fixture(autouse=True)
async def reset_database(configure_test_environment):
    from app.db.base import Base
    from app.db.session import dispose_engine, get_engine

    await dispose_engine()
    engine = get_engine()
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    yield
    await dispose_engine()


@pytest_asyncio.fixture
async def session(configure_test_environment, reset_database):
    from app.db.session import get_sessionmaker

    session_factory = get_sessionmaker()
    async with session_factory() as db_session:
        yield db_session


@pytest_asyncio.fixture
async def client(configure_test_environment, reset_database):
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client
