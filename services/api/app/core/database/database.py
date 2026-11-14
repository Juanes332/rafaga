"""Async engine, session factory and the request-scoped session."""

import json
from collections.abc import AsyncIterator
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def build_engine(url: str) -> AsyncEngine:
    """Create the async engine; connections open lazily on first use."""
    return create_async_engine(url, pool_pre_ping=True, pool_size=10)


def build_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Return a session factory that keeps rows readable after commit."""
    return async_sessionmaker(engine, expire_on_commit=False)


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Yield a session; services commit explicitly, errors roll back."""
    async with request.app.state.session_factory() as session:
        yield session


def dumps(value: Any) -> str:
    """Serialize a value for a jsonb bind parameter."""
    return json.dumps(value, separators=(",", ":"))
