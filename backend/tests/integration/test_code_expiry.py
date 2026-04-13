"""
T052 — Test integracyjny: wygasanie kodów — weryfikacja kodu po upływie TTL.
"""
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.codes import generate_code, verify_code
from src.domain.transactions import finalize_transaction
from src.models.auth_code import AuthCode, AuthCodeStatus
from src.models.user import User


@pytest.mark.asyncio
class TestCodeExpiry:
    async def test_expired_code_cannot_be_verified(
        self, session: AsyncSession, user: User
    ):
        """Kod z wygasłym expires_at nie przechodzi weryfikacji."""
        _, auth_code = await generate_code(session, user)

        # Ustaw wygasłą datę ręcznie
        auth_code.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        await session.flush()

        with pytest.raises(ValueError, match="Nieprawidłowy lub wygasły"):
            await verify_code(session, "000000", 100.0, "terminal-dev")

    async def test_active_code_within_ttl_works(
        self, session: AsyncSession, user: User
    ):
        """Kod w TTL (15 min) przechodzi weryfikację."""
        code, auth_code = await generate_code(session, user)
        token, *_ = await verify_code(session, code, 100.0, "terminal-dev")
        assert token is not None

    async def test_expired_code_status_set_by_finalize(
        self, session: AsyncSession, user: User
    ):
        """
        Finalize wygasłego kodu (verify_token z wygasłym expires_at)
        zmienia status na WYGASLY.
        """
        code, auth_code = await generate_code(session, user)
        # Zdobądź token przed wygaśnięciem
        token, *_ = await verify_code(session, code, 100.0, "terminal-dev")

        # Teraz ustaw wygaśnięcie
        auth_code.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        await session.flush()

        with pytest.raises(ValueError, match="[Ww]ygasł"):
            await finalize_transaction(session, token)

        await session.refresh(auth_code)
        assert auth_code.status == AuthCodeStatus.WYGASLY

    async def test_code_ttl_is_15_minutes(
        self, session: AsyncSession, user: User
    ):
        """Wygenerowany kod wygasa za ~15 minut."""
        from src.domain.codes import CODE_TTL_MINUTES
        assert CODE_TTL_MINUTES == 15

        _, auth_code = await generate_code(session, user)
        now = datetime.now(timezone.utc)
        expires_at = auth_code.expires_at.replace(tzinfo=timezone.utc)

        diff_minutes = (expires_at - now).total_seconds() / 60
        assert 14 < diff_minutes <= 15

    async def test_code_invalid_after_wrong_otp(
        self, session: AsyncSession, user: User
    ):
        """Błędny kod OTP → 'Nieprawidłowy lub wygasły'."""
        await generate_code(session, user)
        with pytest.raises(ValueError, match="Nieprawidłowy lub wygasły"):
            await verify_code(session, "000000", 100.0, "terminal-dev")
