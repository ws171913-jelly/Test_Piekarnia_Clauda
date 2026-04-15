"""
T026 — Testy jednostkowe: generowanie OTP.

Testuje:
- format 6-cyfrowy
- losowość (brak duplikatów w serii)
- weryfikację bcrypt hash
- blokadę karencji 30 min
- blokadę zerowego salda
"""
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.codes import (
    COOLDOWN_MINUTES,
    _generate_otp,
    _hash_code,
    _verify_code,
    generate_code,
)


class TestGenerateOtp:
    def test_length_is_six(self):
        code = _generate_otp()
        assert len(code) == 6

    def test_digits_only(self):
        code = _generate_otp()
        assert code.isdigit()

    def test_range_100000_to_999999(self):
        for _ in range(20):
            assert 100000 <= int(_generate_otp()) <= 999999

    def test_codes_are_random(self):
        codes = {_generate_otp() for _ in range(50)}
        # Przy 50 losowaniach z 900000 możliwości szansa kolizji wszystkich jest astronomicznie mała
        assert len(codes) > 1


class TestHashCode:
    def test_hash_differs_from_plain(self):
        h = _hash_code("123456")
        assert h != "123456"

    def test_verify_correct(self):
        h = _hash_code("123456")
        assert _verify_code("123456", h) is True

    def test_verify_wrong(self):
        h = _hash_code("123456")
        assert _verify_code("999999", h) is False


def _make_user(balance: float = 100.0, last_code_at: datetime | None = None) -> MagicMock:
    user = MagicMock()
    user.id = uuid.uuid4()
    user.current_balance = balance
    user.last_code_generated_at = last_code_at
    return user


class TestGenerateCode:
    async def _call(self, user: MagicMock):
        session = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        # generate_code wykonuje SELECT ... WITH FOR UPDATE — mock musi zwracać
        # MagicMock z .scalar_one() → user, żeby AsyncMock nie zwrócił coroutine
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = user
        session.execute = AsyncMock(return_value=mock_result)
        return await generate_code(session, user)

    async def test_returns_code_and_auth_code(self):
        user = _make_user()
        code, auth_code = await self._call(user)
        assert len(code) == 6
        assert code.isdigit()

    async def test_sets_last_code_generated_at(self):
        user = _make_user()
        await self._call(user)
        assert user.last_code_generated_at is not None

    async def test_zero_balance_raises(self):
        user = _make_user(balance=0.0)
        with pytest.raises(ValueError, match="Brak salda"):
            await self._call(user)

    async def test_cooldown_raises(self):
        recent = datetime.now(timezone.utc) - timedelta(minutes=10)
        user = _make_user(last_code_at=recent)
        with pytest.raises(ValueError, match="Karencja"):
            await self._call(user)

    async def test_after_cooldown_succeeds(self):
        old = datetime.now(timezone.utc) - timedelta(minutes=COOLDOWN_MINUTES + 1)
        user = _make_user(last_code_at=old)
        code, _ = await self._call(user)
        assert len(code) == 6
