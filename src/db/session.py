"""Database engine, connection pooling, SQLite WAL configuration and session management."""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import settings
from src.db.models import Base

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
)


@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enforce SQLite WAL mode, busy timeout and normal synchronous mode for concurrent reliability."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()


async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Async context manager providing an isolated AsyncSession with auto-rollback on exception."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an AsyncSession with managed commit/rollback."""
    async with get_db_session() as session:
        yield session


async def init_db() -> None:
    """Initialize database tables according to SQLAlchemy DeclarativeBase schema."""
    # Ensure directory exists for sqlite database file
    if "sqlite" in settings.DATABASE_URL:
        db_path = settings.DATABASE_URL.split(":///")[-1]
        dir_name = os.path.dirname(db_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
