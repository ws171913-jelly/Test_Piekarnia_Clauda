"""
Fixtures dla testów kontraktowych — pełny stack HTTP z testową bazą.

Nadpisuje zależność get_session w FastAPI, by używać testowej sesji.
"""
import uuid
from datetime import date, timedelta
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user, get_pos_terminal_id, get_session
from src.domain.auth import create_jwt, hash_pin
from src.main import app
from src.models.basket import Basket
from src.models.user import User

# ---------------------------------------------------------------------------
# Import engine z globalnego conftest (session-scoped)
# ---------------------------------------------------------------------------

pytest_plugins = ["tests.conftest"]


# ---------------------------------------------------------------------------
# HTTP client z testową sesją
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def http_client(session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """AsyncClient skierowany do FastAPI ASGI z testową sesją DB."""

    async def override_session() -> AsyncGenerator[AsyncSession, None]:
        yield session

    app.dependency_overrides[get_session] = override_session
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_session, None)


@pytest_asyncio.fixture
async def authed_client(
    http_client: AsyncClient,
    session: AsyncSession,
    user: User,
) -> AsyncClient:
    """HTTP client z zalogowanym pracownikiem (Bearer token)."""
    jti = uuid.uuid4()
    user.current_jti = jti
    await session.flush()

    token = create_jwt(user.id, jti)
    http_client.headers["Authorization"] = f"Bearer {token}"
    return http_client


@pytest_asyncio.fixture
async def pos_client(http_client: AsyncClient) -> AsyncClient:
    """HTTP client z kluczem API terminala POS."""
    http_client.headers["X-POS-API-Key"] = "pos-key-terminal-dev"
    return http_client
