#!/usr/bin/env python3
"""
Skrypt seed danych deweloperskich.
Tworzy: 3 koszyki, 5 pracowników z PIN-ami, 2 terminale POS (env config).
"""
import asyncio
import sys
import uuid
from datetime import date

sys.path.insert(0, ".")

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from src.config import settings
from src.domain.auth import hash_pin
from src.models.basket import Basket
from src.models.user import User


async def seed() -> None:
    if settings.environment not in {"development", "dev", "local"}:
        raise RuntimeError(
            "seed_dev_data.py can only run in development environment. "
            f"Current environment: {settings.environment!r}"
        )

    engine = create_async_engine(settings.database_url, echo=True)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as session:
        # 3 koszyki
        baskets = [
            Basket(
                id=uuid.uuid4(),
                hr_basket_id="BASKET_STANDARD",
                name="Koszyk Standard",
                discount_pct=15,
                monthly_limit_pln=200,
                is_active=True,
            ),
            Basket(
                id=uuid.uuid4(),
                hr_basket_id="BASKET_PREMIUM",
                name="Koszyk Premium",
                discount_pct=25,
                monthly_limit_pln=None,
                is_active=True,
            ),
            Basket(
                id=uuid.uuid4(),
                hr_basket_id="BASKET_BASIC",
                name="Koszyk Basic",
                discount_pct=10,
                monthly_limit_pln=100,
                is_active=True,
            ),
        ]
        for b in baskets:
            session.add(b)
        await session.flush()

        # 5 pracowników
        employees = [
            ("EMP001", "1234", baskets[0], 150.00, "LOC_WARSZAWA"),
            ("EMP002", "5678", baskets[1], 300.00, "LOC_KRAKOW"),
            ("EMP003", "9012", baskets[2], 80.00, "LOC_WARSZAWA"),
            ("EMP004", "3456", baskets[0], 0.00, "LOC_GDANSK"),
            ("EMP005", "7890", baskets[1], 250.00, "LOC_WROCLAW"),
        ]

        for hr_id, pin, basket, balance, location in employees:
            user = User(
                id=uuid.uuid4(),
                hr_employee_id=hr_id,
                basket_id=basket.id,
                pin_hash=hash_pin(pin),
                must_change_pin=False,
                current_balance=balance,
                balance_expiry_date=date(2026, 12, 31),
                location_id=location,
                is_active=True,
            )
            session.add(user)

        await session.commit()

    print("✅ Seed danych deweloperskich zakończony")
    print("\nPracownicy:")
    for hr_id, pin, basket, balance, location in employees:
        print(f"  {hr_id}: PIN={pin}, koszyk={basket.name}, saldo={balance:.2f} PLN")
    print("\nTerminale POS (ustaw POS_API_KEYS w .env):")
    print("  POS_TERMINAL_001: klucz=pos-key-terminal-001")
    print("  POS_TERMINAL_002: klucz=pos-key-terminal-002")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
