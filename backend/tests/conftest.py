"""
Fixtures wspólne dla testów integracyjnych.

Wymaga działającej bazy PostgreSQL.
URL testowej bazy konfiguruje się przez zmienną:
  TEST_DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/bonusapp_test

Domyślnie używa tej samej bazy co aplikacja z przyrostkiem _test w nazwie.
"""
import os
import uuid
from datetime import date, timedelta, timezone
from typing import AsyncGenerator

import asyncio

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.domain.auth import hash_pin
from src.models.auth_code import AuthCode, AuthCodeStatus
from src.models.base import Base
from src.models.basket import Basket
from src.models.transaction import Transaction  # noqa: F401 — needed for metadata
from src.models.user import User

# ---------------------------------------------------------------------------
# Konfiguracja URL testowej bazy
# ---------------------------------------------------------------------------

_DEFAULT_TEST_URL = (
    "postgresql+asyncpg://bonusapp:bonusapp_secret@localhost:5432/bonusapp_test"
)
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", _DEFAULT_TEST_URL)


def _is_test_database(url: str) -> bool:
    """Sprawdza czy URL bazy wygląda jak testowa (zawiera _test suffix)."""
    return "_test" in url.split("/")[-1].split("?")[0]


if not _is_test_database(TEST_DATABASE_URL):
    raise RuntimeError(
        f"TEST_DATABASE_URL musi zawierać '_test' w nazwie bazy, otrzymano: {TEST_DATABASE_URL!r}"
    )


# ---------------------------------------------------------------------------
# Engine i schema — tworzone raz na całą sesję pytest
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def event_loop():
    """Session-scoped event loop — wymaga tego asyncpg z session-scoped fixtures."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Async engine dla testowej bazy — tworzy i niszczy tabele raz na sesję."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
    await engine.dispose()


@pytest_asyncio.fixture
async def session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Async session izolowana przez transakcję na poziomie połączenia.
    join_transaction_mode="create_savepoint" sprawia, że session.commit()
    tworzy SAVEPOINT zamiast commitować zewnętrzną transakcję, dzięki
    czemu po teście możemy wszystko wycofać.
    """
    conn = await test_engine.connect()
    await conn.begin()
    s = AsyncSession(
        bind=conn,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    try:
        yield s
    finally:
        await s.close()
        await conn.rollback()
        await conn.close()


# ---------------------------------------------------------------------------
# Fixtures domenowe
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def basket(session: AsyncSession) -> Basket:
    """Koszyk testowy z 20% rabatem."""
    b = Basket(
        hr_basket_id="TEST_BASKET_001",
        name="Koszyk testowy",
        discount_pct=20.0,
        monthly_limit_pln=None,
        is_active=True,
    )
    session.add(b)
    await session.flush()
    return b


@pytest_asyncio.fixture
async def basket_with_limit(session: AsyncSession) -> Basket:
    """Koszyk testowy z 20% rabatem i limitem miesięcznym 100 PLN."""
    b = Basket(
        hr_basket_id="TEST_BASKET_002",
        name="Koszyk z limitem",
        discount_pct=20.0,
        monthly_limit_pln=100.0,
        is_active=True,
    )
    session.add(b)
    await session.flush()
    return b


@pytest_asyncio.fixture
async def user(session: AsyncSession, basket: Basket) -> User:
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
    session.add(u)
    await session.flush()
    await session.refresh(u)
    return u


@pytest_asyncio.fixture
async def user_zero_balance(session: AsyncSession, basket: Basket) -> User:
    """Aktywny pracownik z saldem 0 PLN."""
    u = User(
        hr_employee_id=f"EMP_ZERO_{uuid.uuid4().hex[:8]}",
        basket_id=basket.id,
        pin_hash=hash_pin("123456"),
        must_change_pin=False,
        login_attempts=0,
        locked_until=None,
        current_jti=None,
        current_balance=0.0,
        balance_expiry_date=date.today() + timedelta(days=30),
        last_code_generated_at=None,
        is_active=True,
        location_id="LOC_001",
    )
    session.add(u)
    await session.flush()
    await session.refresh(u)
    return u


@pytest_asyncio.fixture
async def user_must_change_pin(session: AsyncSession, basket: Basket) -> User:
    """Pracownik z PIN tymczasowym — musi zmienić PIN przy pierwszym logowaniu."""
    temp_pin = "999888"
    u = User(
        hr_employee_id=f"EMP_TEMP_{uuid.uuid4().hex[:8]}",
        basket_id=basket.id,
        pin_hash=hash_pin(temp_pin),
        must_change_pin=True,
        login_attempts=0,
        locked_until=None,
        current_jti=None,
        current_balance=200.0,
        balance_expiry_date=date.today() + timedelta(days=30),
        last_code_generated_at=None,
        is_active=True,
        location_id="LOC_001",
    )
    session.add(u)
    await session.flush()
    await session.refresh(u)
    # Zwróć też tymczasowy PIN w atrybucie
    u._temp_pin = temp_pin  # type: ignore[attr-defined]
    return u
