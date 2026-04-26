"""
SecureDx AI — Database Connection Pool

Uses async SQLAlchemy 2.0 with asyncpg for all runtime queries.
Sync psycopg2 connection is available for Alembic migrations only.

All PHI fields use pgcrypto AES-256 encryption at the column level.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

logger = structlog.get_logger(__name__)

# =============================================================================
# ENGINE & SESSION FACTORY
# =============================================================================

engine: AsyncEngine | None = None
AsyncSessionLocal: async_sessionmaker | None = None


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


async def init_db() -> None:
    """Initialize the database engine and session factory."""
    global engine, AsyncSessionLocal

    engine = create_async_engine(
        settings.DATABASE_URL,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_pre_ping=True,          # Verify connections before use
        echo=settings.is_development(),
    )

    AsyncSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    # Verify connectivity
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))

    logger.info("Database pool initialized", pool_size=settings.DB_POOL_SIZE)


async def close_db() -> None:
    """Gracefully close the database engine."""
    global engine
    if engine:
        await engine.dispose()
        logger.info("Database pool closed")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency: yields an async database session per request.

    Usage:
        @router.get("/endpoint")
        async def endpoint(db: AsyncSession = Depends(get_session)):
            ...
    """
    if AsyncSessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def check_db_health() -> bool:
    """Check if the database is reachable. Used by health check endpoint."""
    try:
        if engine is None:
            return False
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return False
