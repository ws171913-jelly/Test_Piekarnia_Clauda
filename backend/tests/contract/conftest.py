"""
Fixtures dla testów kontraktowych — pełny stack HTTP z testową bazą.

Strategia izolacji:
- session commituje dane (FastAPI musi widzieć committed rows przez własne sesje)
- FastAPI dostaje świeże sesje per-request (brak współdzielenia połączenia asyncpg)
- po teście: TRUNCATE wszystkich tabel
"""
import uuid
from datetime import date, timedelta
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_session
from src.domain.auth import create_jwt, hash_pin
from src.main import app
from src.models.basket import Basket
from src.models.user import User

# ---------------------------------------------------------------------------
# Nadpisanie session — commit zamiast savepoint
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Contract session — rzeczywiście commituje dane, żeby FastAPI mogło je
    zobaczyć przez własne sesje.  Po teście: TRUNCATE wszystkich tabel.
    """
    async with AsyncSession(test_engine, expire_on_commit=False) as s:
        yield s
        await s.rollback()  # anuluj niezacommitowane resztki
        async with s.begin():
            await s.execute(
                text(
                    "TRUNCATE auth_codes, transactions, users, baskets"
                    " RESTART IDENTITY CASCADE"
                )
            )


# ---------------------------------------------------------------------------
# HTTP client z testową bazą
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def http_client(session: AsyncSession, test_engine) -> AsyncGenerator[AsyncClient, None]:
    """
    AsyncClient skierowany do FastAPI ASGI.

    Commituje dane sesji testowej (basket, user), żeby FastAPI mogło je
    zobaczyć.  FastAPI dostaje świeżą sesję per-request — brak współdzielenia
    połączenia asyncpg między taskami asyncio.
    """
    # Commit danych ustawionych przez fixture basket/user
    await session.commit()

    async def override_session() -> AsyncGenerator[AsyncSession, None]:
        async with AsyncSession(test_engine, expire_on_commit=False) as s:
            yield s

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
    await session.commit()  # jti musi być widoczne dla FastAPI

    token = create_jwt(user.id, jti)
    http_client.headers["Authorization"] = f"Bearer {token}"
    return http_client


@pytest_asyncio.fixture
async def pos_client(http_client: AsyncClient) -> AsyncClient:
    """HTTP client z kluczem API terminala POS."""
    http_client.headers["X-POS-API-Key"] = "pos-key-terminal-dev"
    return http_client
