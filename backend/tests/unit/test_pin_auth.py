"""
T012 — Testy jednostkowe: logika PIN auth.

Testuje:
- weryfikację hash PIN (bcrypt)
- generowanie PIN tymczasowego (format 6-cyfrowy)
- logikę blokady po 5 nieudanych próbach
- mocking — bez bazy danych
"""
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domain.auth import (
    MAX_LOGIN_ATTEMPTS,
    LOCKOUT_MINUTES,
    generate_temp_pin,
    hash_pin,
    verify_pin,
    authenticate_user,
    change_pin,
)


# ---------------------------------------------------------------------------
# Testy pomocnicze (bez DB)
# ---------------------------------------------------------------------------

class TestHashPin:
    def test_hash_is_not_plaintext(self):
        h = hash_pin("1234")
        assert h != "1234"

    def test_verify_correct_pin(self):
        h = hash_pin("1234")
        assert verify_pin("1234", h) is True

    def test_verify_wrong_pin(self):
        h = hash_pin("1234")
        assert verify_pin("9999", h) is False

    def test_hashes_are_unique(self):
        """Bcrypt stosuje salt — dwa skróty tego samego PIN muszą być różne."""
        h1 = hash_pin("1234")
        h2 = hash_pin("1234")
        assert h1 != h2


class TestGenerateTempPin:
    def test_length_is_six(self):
        pin = generate_temp_pin()
        assert len(pin) == 6

    def test_is_digits_only(self):
        pin = generate_temp_pin()
        assert pin.isdigit()

    def test_range_100000_to_999999(self):
        for _ in range(20):
            pin = int(generate_temp_pin())
            assert 100000 <= pin <= 999999


# ---------------------------------------------------------------------------
# Testy authenticate_user (z mockowaną sesją)
# ---------------------------------------------------------------------------

def _make_user(
    *,
    pin: str = "1234",
    is_active: bool = True,
    login_attempts: int = 0,
    locked_until: datetime | None = None,
    must_change_pin: bool = False,
) -> MagicMock:
    user = MagicMock()
    user.id = uuid.uuid4()
    user.hr_employee_id = "EMP001"
    user.pin_hash = hash_pin(pin)
    user.is_active = is_active
    user.login_attempts = login_attempts
    user.locked_until = locked_until
    user.must_change_pin = must_change_pin
    user.current_jti = None
    return user


class TestAuthenticateUser:
    async def _call(self, user: MagicMock, pin: str):
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user
        session.execute.return_value = mock_result
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        return await authenticate_user(session, "EMP001", pin)

    async def test_correct_pin_returns_token(self):
        user = _make_user(pin="1234")
        _, token = await self._call(user, "1234")
        assert isinstance(token, str)
        assert len(token) > 20

    async def test_correct_pin_resets_attempts(self):
        user = _make_user(pin="1234", login_attempts=3)
        await self._call(user, "1234")
        assert user.login_attempts == 0

    async def test_correct_pin_updates_jti(self):
        user = _make_user(pin="1234")
        old_jti = user.current_jti
        await self._call(user, "1234")
        assert user.current_jti != old_jti

    async def test_wrong_pin_raises(self):
        user = _make_user(pin="1234")
        with pytest.raises(ValueError, match="Błędny PIN"):
            await self._call(user, "9999")

    async def test_wrong_pin_increments_attempts(self):
        user = _make_user(pin="1234", login_attempts=0)
        with pytest.raises(ValueError):
            await self._call(user, "9999")
        assert user.login_attempts == 1

    async def test_lockout_after_5_failures(self):
        user = _make_user(pin="1234", login_attempts=MAX_LOGIN_ATTEMPTS - 1)
        with pytest.raises(ValueError):
            await self._call(user, "9999")
        assert user.locked_until is not None

    async def test_locked_account_raises(self):
        future = datetime.now(timezone.utc) + timedelta(minutes=10)
        user = _make_user(pin="1234", locked_until=future)
        with pytest.raises(ValueError, match="zablokowane"):
            await self._call(user, "1234")

    async def test_expired_lockout_allows_login(self):
        past = datetime.now(timezone.utc) - timedelta(minutes=1)
        user = _make_user(pin="1234", locked_until=past)
        _, token = await self._call(user, "1234")
        assert isinstance(token, str)

    async def test_inactive_user_raises(self):
        user = _make_user(pin="1234", is_active=False)
        with pytest.raises(ValueError, match="dezaktywowane"):
            await self._call(user, "1234")

    async def test_unknown_user_raises(self):
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result
        with pytest.raises(ValueError, match="Nieprawidłowy"):
            await authenticate_user(session, "UNKNOWN", "1234")


# ---------------------------------------------------------------------------
# Testy change_pin
# ---------------------------------------------------------------------------

class TestChangePin:
    async def _call(self, user: MagicMock, new_pin: str, confirm_pin: str):
        session = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        return await change_pin(session, user, new_pin, confirm_pin)

    async def test_change_pin_success(self):
        user = _make_user(pin="1234", must_change_pin=True)
        token = await self._call(user, "5678", "5678")
        assert isinstance(token, str)
        assert user.must_change_pin is False

    async def test_change_pin_updates_hash(self):
        user = _make_user(pin="1234")
        old_hash = user.pin_hash
        await self._call(user, "5678", "5678")
        assert user.pin_hash != old_hash

    async def test_change_pin_mismatched_raises(self):
        user = _make_user(pin="1234")
        with pytest.raises(ValueError, match="nie pasują"):
            await self._call(user, "5678", "9999")

    async def test_change_pin_issues_new_jti(self):
        user = _make_user(pin="1234")
        old_jti = user.current_jti
        await self._call(user, "5678", "5678")
        assert user.current_jti != old_jti
