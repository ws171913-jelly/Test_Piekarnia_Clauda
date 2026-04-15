"""
T063 — Zadanie cron: usuwanie logów operacyjnych starszych niż 6 miesięcy.

Dotyczy rekordów hr_events oraz auth_codes z datą starszą niż 6 miesięcy.
Uruchamiać raz na dobę (np. o 02:00).
"""
import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func

from src.database import async_sessionmaker
from src.models.auth_code import AuthCode
from src.models.hr_event import HrEvent


RETENTION_DAYS = 180  # 6 miesięcy


async def purge_old_logs() -> dict[str, int]:
    """
    Usuwa logi operacyjne starsze niż RETENTION_DAYS dni.

    Usuwa:
    - auth_codes (wykorzystane lub wygasłe) starsze niż 6 miesięcy
    - hr_events starsze niż 6 miesięcy

    Returns:
        Słownik z liczbą usuniętych rekordów per tabela.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    counts: dict[str, int] = {}

    async with async_sessionmaker() as session:
        # Usuń wygasłe/wykorzystane auth_codes
        result = await session.execute(
            delete(AuthCode)
            .where(AuthCode.created_at <= cutoff)
            .where(
                AuthCode.status.in_(["WYKORZYSTANY", "WYGASLY"])
            )
            .returning(AuthCode.id)
        )
        counts["auth_codes"] = len(result.fetchall())

        # Usuń stare zdarzenia HR
        result = await session.execute(
            delete(HrEvent)
            .where(HrEvent.received_at <= cutoff)
            .returning(HrEvent.id)
        )
        counts["hr_events"] = len(result.fetchall())

        await session.commit()

    return counts


if __name__ == "__main__":
    result = asyncio.run(purge_old_logs())
    total = sum(result.values())
    print(f"Usunięto {total} rekordów: {result}")
