"""
T050 — Test jednostkowy: blokada przy saldzie = 0 PLN.

Weryfikuje, że generate_code odrzuca generowanie kodu gdy
current_balance <= 0.
"""
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.codes import generate_code


def _make_user(balance: float) -> MagicMock:
    user = MagicMock()
    user.id = uuid.uuid4()
    user.current_balance = balance
    user.last_code_generated_at = None
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
class TestZeroBalanceBlock:
    async def test_zero_balance_raises(self):
        """Saldo = 0 PLN → ValueError."""
        user = _make_user(balance=0.0)
        with pytest.raises(ValueError, match="Brak salda"):
            await _call(user)

    async def test_negative_balance_raises(self):
        """Saldo ujemne → ValueError."""
        user = _make_user(balance=-10.0)
        with pytest.raises(ValueError, match="Brak salda"):
            await _call(user)

    async def test_small_positive_balance_allowed(self):
        """Saldo 0.01 PLN → generowanie dozwolone."""
        user = _make_user(balance=0.01)
        code, _ = await _call(user)
        assert len(code) == 6
        assert code.isdigit()

    async def test_normal_balance_allowed(self):
        """Saldo 100 PLN → generowanie dozwolone."""
        user = _make_user(balance=100.0)
        code, _ = await _call(user)
        assert len(code) == 6

    async def test_zero_balance_error_message(self):
        """Komunikat błędu zawiera informację o braku salda."""
        user = _make_user(balance=0.0)
        with pytest.raises(ValueError) as exc_info:
            await _call(user)
        assert "brak salda" in str(exc_info.value).lower()

    async def test_exact_zero_float_raises(self):
        """Saldo 0.0 (float) → blokada."""
        user = _make_user(balance=0.0)
        with pytest.raises(ValueError, match="Brak salda"):
            await _call(user)

    async def test_zero_parsed_from_string_raises(self):
        """Saldo 0.0 (float z konwersji stringa '0') → blokada."""
        user = _make_user(balance=float("0"))
        with pytest.raises(ValueError, match="Brak salda"):
            await _call(user)
