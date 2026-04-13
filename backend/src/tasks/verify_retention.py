"""
T064 — Zadanie cron: weryfikacja retencji transakcji.

Alert gdy rekord transakcji starszy niż 24 miesiące nie jest zarchiwizowany.
Uruchamiać raz na tydzień.
"""
import calendar
import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import func, select

from src.database import async_sessionmaker
from src.models.transaction import Transaction


ARCHIVE_THRESHOLD_MONTHS = 24  # 24 miesiące (precyzyjnie, nie 730 dni)

logger = logging.getLogger(__name__)


async def _months_ago(months: int) -> datetime:
    """Zwraca datę `months` miesięcy temu, obsługując lata przestępne."""
    now = datetime.now(timezone.utc)
    year = now.year
    month = now.month - months
    while month <= 0:
        month += 12
        year -= 1
    day = min(now.day, calendar.monthrange(year, month)[1])
    return now.replace(year=year, month=month, day=day)


async def verify_transaction_retention() -> dict[str, int]:
    """
    Sprawdza czy istnieją transakcje starsze niż 24 miesiące.

    W środowisku produkcyjnym powinno to wyzwolić alert (np. przez monitoring).
    W obecnej implementacji loguje ostrzeżenie i zwraca liczbę rekordów.

    Returns:
        Słownik z kluczem "overdue_count" — liczba rekordów wymagających archiwizacji.
    """
    cutoff = await _months_ago(ARCHIVE_THRESHOLD_MONTHS)

    async with async_sessionmaker() as session:
        result = await session.execute(
            select(func.count(Transaction.id))
            .where(Transaction.created_at <= cutoff)
        )
        overdue_count = result.scalar_one()

    if overdue_count > 0:
        logger.warning(
            "RETENCJA: %d transakcji starszych niż 24 miesiące nie zostało zarchiwizowanych. "
            "Próg: %s",
            overdue_count,
            cutoff.date().isoformat(),
        )
    else:
        logger.info("Weryfikacja retencji: wszystkie transakcje w normie (próg: %s)", cutoff.date())

    return {"overdue_count": overdue_count}


if __name__ == "__main__":
    result = asyncio.run(verify_transaction_retention())
    if result["overdue_count"] > 0:
        print(f"[ALERT] {result['overdue_count']} transakcji wymaga archiwizacji!")
    else:
        print("OK — brak zaległych transakcji")
