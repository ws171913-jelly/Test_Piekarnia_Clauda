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

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

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


# ---------------------------------------------------------------------------
# Engine i schema — tworzone raz na całą sesję pytest
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Async engine dla testowej bazy — tworzy i niszczy tabele raz na sesję."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, pool_pre_ping=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Async session z rollbackiem po każdym teście.

    Używa SAVEPOINT (nested transaction) żeby test nie modyfikował bazy trwale.
    """
    factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        async with s.begin():
            yield s
            await s.rollback()


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
