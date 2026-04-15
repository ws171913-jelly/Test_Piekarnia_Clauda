#!/usr/bin/env python3
"""
Skrypt seed danych deweloperskich.
Tworzy: 3 koszyki, 5 pracowników z PIN-ami, 2 terminale POS (env config).
"""
import asyncio
import sys
import uuid
from datetime import datetime, timedelta, timezone

sys.path.insert(0, ".")

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.dialects.postgresql import insert as pg_insert

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
    try:
        Session = async_sessionmaker(engine, expire_on_commit=False)

        async with Session() as session:
            # 3 koszyki — ON CONFLICT DO NOTHING przy ponownym uruchomieniu
            basket_rows = [
                dict(
                    id=uuid.uuid4(),
                    hr_basket_id="BASKET_STANDARD",
                    name="Koszyk Standard",
                    discount_pct=15,
                    monthly_limit_pln=200,
                    is_active=True,
                ),
                dict(
                    id=uuid.uuid4(),
                    hr_basket_id="BASKET_PREMIUM",
                    name="Koszyk Premium",
                    discount_pct=25,
                    monthly_limit_pln=None,
                    is_active=True,
                ),
                dict(
                    id=uuid.uuid4(),
                    hr_basket_id="BASKET_BASIC",
                    name="Koszyk Basic",
                    discount_pct=10,
                    monthly_limit_pln=100,
                    is_active=True,
                ),
            ]
            await session.execute(
                pg_insert(Basket).values(basket_rows).on_conflict_do_nothing(
                    index_elements=["hr_basket_id"]
                )
            )
            await session.flush()

            # Pobierz koszyki z bazy (mogły już istnieć)
            from sqlalchemy import select
            result = await session.execute(
                select(Basket).where(
                    Basket.hr_basket_id.in_(["BASKET_STANDARD", "BASKET_PREMIUM", "BASKET_BASIC"])
                )
            )
            baskets_by_id = {b.hr_basket_id: b for b in result.scalars().all()}
            
            expected_baskets = ["BASKET_STANDARD", "BASKET_PREMIUM", "BASKET_BASIC"]
            missing = [b for b in expected_baskets if b not in baskets_by_id]
            if missing:
                raise RuntimeError(f"Brakujące koszyki w bazie: {missing}")
            
            basket_std = baskets_by_id["BASKET_STANDARD"]
            basket_prm = baskets_by_id["BASKET_PREMIUM"]
            basket_bsc = baskets_by_id["BASKET_BASIC"]

            # 5 pracowników — ON CONFLICT DO NOTHING przy ponownym uruchomieniu
            expiry = datetime.now(timezone.utc).date() + timedelta(days=365)
            employees = [
                ("EMP001", "1234", basket_std, 150.00, "LOC_WARSZAWA"),
                ("EMP002", "5678", basket_prm, 300.00, "LOC_KRAKOW"),
                ("EMP003", "9012", basket_bsc, 80.00, "LOC_WARSZAWA"),
                ("EMP004", "3456", basket_std, 0.00, "LOC_GDANSK"),
                ("EMP005", "7890", basket_prm, 250.00, "LOC_WROCLAW"),
            ]
            user_rows = [
                {
                    "id": uuid.uuid4(),
                    "hr_employee_id": hr_id,
                    "basket_id": basket.id,
                    "pin_hash": hash_pin(pin),
                    "must_change_pin": False,
                    "current_balance": balance,
                    "balance_expiry_date": expiry,
                    "location_id": location,
                    "is_active": True,
                }
                for hr_id, pin, basket, balance, location in employees
            ]
            await session.execute(
                pg_insert(User).values(user_rows).on_conflict_do_nothing(
                    index_elements=["hr_employee_id"]
                )
            )

            await session.commit()

        print("✅ Seed danych deweloperskich zakończony")
        print("\nPracownicy:")
        for hr_id, pin, basket, balance, _location in employees:
            print(f"  {hr_id}: PIN={pin}, koszyk={basket.name}, saldo={balance:.2f} PLN")
        print("\nTerminale POS (ustaw POS_API_KEYS w .env):")
        print("  POS_TERMINAL_001: klucz=pos-key-terminal-001")
        print("  POS_TERMINAL_002: klucz=pos-key-terminal-002")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
