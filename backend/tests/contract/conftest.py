"""
Fixtures dla testów kontraktowych — pełny stack HTTP z testową bazą.

Strategia izolacji:
- Dane testowe są commitowane (FastAPI musi widzieć committed rows)
- FastAPI dostaje świeże sesje per-request (brak współdzielenia połączenia asyncpg)
- po teście: TRUNCATE wszystkich tabel
- **Brak `session` fixture** — testy kontraktowe operują wyłącznie przez HTTP.
  Fixture `_setup_session` (z prefiksem `_`) jest dostępny tylko dla testów,
  które muszą przygotować stan bazy (np. zerowanie salda); jego użycie
  powinno być wyjątkiem, nie regułą.
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
# Internal session — commit-based, tylko do setupu stanu (nie do domain calls)
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def _setup_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Sesja commitująca dane — używana wyłącznie do przygotowania stanu bazy
    przed testem (np. ustawienie balansu na 0).  **Nie wywołuj na niej
    funkcji domenowych** — do tego służy HTTP API.

    Po teście: TRUNCATE wszystkich tabel.
    """
    async with AsyncSession(test_engine, expire_on_commit=False) as s:
        yield s
        await s.rollback()
        async with s.begin():
            await s.execute(
                text(
                    "TRUNCATE auth_codes, transactions, users, baskets"
                    " RESTART IDENTITY CASCADE"
                )
            )


# ---------------------------------------------------------------------------
# Fixtures domenowe — tworzone przez _setup_session, commitowane przed HTTP
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def basket(_setup_session: AsyncSession) -> Basket:
    """Koszyk testowy z 20% rabatem."""
    b = Basket(
        hr_basket_id="TEST_BASKET_001",
        name="Koszyk testowy",
        discount_pct=20.0,
        monthly_limit_pln=None,
        is_active=True,
    )
    _setup_session.add(b)
    await _setup_session.flush()
    return b


@pytest_asyncio.fixture
async def user(_setup_session: AsyncSession, basket: Basket) -> User:
    """Aktywny pracownik z saldem 500 PLN i PIN-em '123456'."""
    u = User(
        hr_employee_id=f"EMP_{uuid.uuid4().hex[:8]}",
        basket_id=basket.id,
        pin_hash=hash_pin("123456"),
        must_change_pin=False,
        login_attempts=0,
        locked_until=None,
        current_jti=None,
        current_balance=500.0,
        balance_expiry_date=date.today() + timedelta(days=30),
        last_code_generated_at=None,
        is_active=True,
        location_id="LOC_001",
    )
    _setup_session.add(u)
    await _setup_session.flush()
    await _setup_session.refresh(u)
    return u


# ---------------------------------------------------------------------------
# HTTP client z testową bazą
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def http_client(_setup_session: AsyncSession, test_engine) -> AsyncGenerator[AsyncClient, None]:
    """
    AsyncClient skierowany do FastAPI ASGI.

    Commituje dane setupowe (basket, user), żeby FastAPI mogło je
    zobaczyć.  FastAPI dostaje świeżą sesję per-request — brak współdzielenia
    połączenia asyncpg między taskami asyncio.
    """
    await _setup_session.commit()

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
    _setup_session: AsyncSession,
    user: User,
) -> AsyncClient:
    """HTTP client z zalogowanym pracownikiem (Bearer token)."""
    jti = uuid.uuid4()
    user.current_jti = jti
    await _setup_session.flush()
    await _setup_session.commit()

    token = create_jwt(user.id, jti)
    # Nowy klient z niezależnymi nagłówkami — nie mutuje http_client
    client = AsyncClient(
        transport=http_client._transport,
        base_url=http_client.base_url,
        headers={"Authorization": f"Bearer {token}"},
    )
    return client


@pytest_asyncio.fixture
async def pos_client(http_client: AsyncClient) -> AsyncClient:
    """HTTP client z kluczem API terminala POS — bez Authorization."""
    # Nowy klient z niezależnymi nagłówkami — nie mutuje http_client
    client = AsyncClient(
        transport=http_client._transport,
        base_url=http_client.base_url,
        headers={"X-POS-API-Key": "pos-key-terminal-dev"},
    )
    return client


@pytest_asyncio.fixture
async def authed_pos_client(authed_client: AsyncClient) -> AsyncClient:
    """Client z oboma nagłówkami: Bearer (user) + X-POS-API-Key (terminal)."""
    client = AsyncClient(
        transport=authed_client._transport,
        base_url=authed_client.base_url,
        headers={**authed_client.headers, "X-POS-API-Key": "pos-key-terminal-dev"},
    )
    return client
