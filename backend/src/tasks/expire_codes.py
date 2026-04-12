"""
Zadanie cron: wygasanie aktywnych kodów OTP po przekroczeniu TTL.
Uruchamiać co minutę lub co 5 minut.
"""
import asyncio
from datetime import datetime, timezone

from sqlalchemy import update

from src.database import async_sessionmaker
from src.models.auth_code import AuthCode, AuthCodeStatus


async def expire_active_codes() -> int:
    """
    Zmienia status AKTYWNY → WYGASŁY dla wszystkich kodów po TTL.

    Returns:
        Liczba zaktualizowanych kodów
    """
    now = datetime.now(timezone.utc)

    async with async_sessionmaker() as session:
        result = await session.execute(
            update(AuthCode)
            .where(AuthCode.status == AuthCodeStatus.AKTYWNY)
            .where(AuthCode.expires_at <= now)
            .values(status=AuthCodeStatus.WYGASLY)
            .returning(AuthCode.id)
        )
        expired_ids = result.fetchall()
        await session.commit()

    return len(expired_ids)


if __name__ == "__main__":
    count = asyncio.run(expire_active_codes())
    print(f"Wygaszono {count} kodów")
