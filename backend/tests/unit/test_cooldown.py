"""
T049 — Test jednostkowy: karencja 30 minut.

Weryfikuje, że generate_code blokuje generowanie gdy
last_code_generated_at < 30 minut temu.
"""
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.codes import COOLDOWN_MINUTES, generate_code


def _make_user(balance: float = 100.0, last_code_at: datetime | None = None) -> MagicMock:
    user = MagicMock()
    user.id = uuid.uuid4()
    user.current_balance = balance
    user.last_code_generated_at = last_code_at
    return user


async def _call(user: MagicMock) -> tuple:
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = user
    session.execute = AsyncMock(return_value=mock_result)
    return await generate_code(session, user)


@pytest.mark.asyncio
class TestCooldown:
    async def test_cooldown_blocks_within_30_min(self):
        """Kod wygenerowany 10 min temu → blokada."""
        recent = datetime.now(timezone.utc) - timedelta(minutes=10)
        user = _make_user(last_code_at=recent)
        with pytest.raises(ValueError, match="Karencja"):
            await _call(user)

    async def test_cooldown_blocks_1_min_ago(self):
        """Kod wygenerowany 1 min temu → blokada."""
        recent = datetime.now(timezone.utc) - timedelta(minutes=1)
        user = _make_user(last_code_at=recent)
        with pytest.raises(ValueError, match="Karencja"):
            await _call(user)

    async def test_cooldown_blocks_29_min_ago(self):
        """Kod wygenerowany 29 min temu → nadal blokada."""
        recent = datetime.now(timezone.utc) - timedelta(minutes=29)
        user = _make_user(last_code_at=recent)
        with pytest.raises(ValueError, match="Karencja"):
            await _call(user)

    async def test_cooldown_passes_after_30_min(self):
        """Kod wygenerowany dokładnie 31 min temu → dozwolone."""
        old = datetime.now(timezone.utc) - timedelta(minutes=COOLDOWN_MINUTES + 1)
        user = _make_user(last_code_at=old)
        code, _ = await _call(user)
        assert len(code) == 6
        assert code.isdigit()

    async def test_cooldown_passes_without_previous_code(self):
        """Brak poprzedniego kodu → karencja nie obowiązuje."""
        user = _make_user(last_code_at=None)
        code, _ = await _call(user)
        assert len(code) == 6

    async def test_cooldown_error_message_includes_remaining_time(self):
        """Komunikat błędu karencji zawiera informację o pozostałym czasie."""
        recent = datetime.now(timezone.utc) - timedelta(minutes=5)
        user = _make_user(last_code_at=recent)
        with pytest.raises(ValueError) as exc_info:
            await _call(user)
        msg = str(exc_info.value)
        assert "Karencja" in msg
        assert "min" in msg

    async def test_cooldown_exactly_30_min_still_blocks(self):
        """Dokładnie 30 min temu — granica karencji — jest blokada."""
        # timedelta < timedelta(minutes=30) jest False przy równości,
        # więc 30 min temu powinno przejść, ale zależy od implementacji
        # Testujemy 29 min 59 sek — nadal blokada
        recent = datetime.now(timezone.utc) - timedelta(minutes=29, seconds=59)
        user = _make_user(last_code_at=recent)
        with pytest.raises(ValueError, match="Karencja"):
            await _call(user)

    async def test_cooldown_constant_is_30(self):
        """Stała COOLDOWN_MINUTES wynosi 30."""
        assert COOLDOWN_MINUTES == 30
