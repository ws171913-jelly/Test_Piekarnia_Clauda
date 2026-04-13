"""
T013 — Test integracyjny: pełny przebieg logowania.

Scenariusze:
- sukces, błędny PIN ×5, blokada, ponowna próba po 15 min
- pierwsze logowanie PIN tymczasowym → wymuszona zmiana → dostęp
- nowe logowanie unieważnia poprzednią sesję (jti)
"""
from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.domain.auth import (
    MAX_LOGIN_ATTEMPTS,
    LOCKOUT_MINUTES,
    authenticate_user,
    change_pin,
)
from src.models.user import User


@pytest.mark.asyncio
class TestAuthFlowSuccess:
    async def test_correct_pin_returns_user_and_token(
        self, session: AsyncSession, user: User
    ):
        result_user, token = await authenticate_user(session, user.hr_employee_id, "123456")
        assert result_user.id == user.id
        assert isinstance(token, str)
        assert len(token) > 20

    async def test_token_is_valid_jwt(self, session: AsyncSession, user: User):
        _, token = await authenticate_user(session, user.hr_employee_id, "123456")
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        assert payload["sub"] == str(user.id)
        assert "jti" in payload
        assert "exp" in payload

    async def test_successful_login_resets_attempts(self, session: AsyncSession, user: User):
        # Najpierw kilka błędnych prób
        for _ in range(2):
            try:
                await authenticate_user(session, user.hr_employee_id, "wrong")
            except ValueError:
                pass
        await session.refresh(user)
        assert user.login_attempts == 2

        # Poprawne logowanie — zeruje licznik
        await authenticate_user(session, user.hr_employee_id, "123456")
        await session.refresh(user)
        assert user.login_attempts == 0

    async def test_successful_login_updates_jti(self, session: AsyncSession, user: User):
        old_jti = user.current_jti
        _, token = await authenticate_user(session, user.hr_employee_id, "123456")
        await session.refresh(user)
        assert user.current_jti is not None
        assert user.current_jti != old_jti

    async def test_jti_in_token_matches_db(self, session: AsyncSession, user: User):
        _, token = await authenticate_user(session, user.hr_employee_id, "123456")
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        await session.refresh(user)
        assert str(user.current_jti) == payload["jti"]


@pytest.mark.asyncio
class TestAuthFlowFailure:
    async def test_wrong_pin_raises(self, session: AsyncSession, user: User):
        with pytest.raises(ValueError, match="Błędny PIN"):
            await authenticate_user(session, user.hr_employee_id, "000000")

    async def test_wrong_pin_increments_attempts(self, session: AsyncSession, user: User):
        try:
            await authenticate_user(session, user.hr_employee_id, "000000")
        except ValueError:
            pass
        await session.refresh(user)
        assert user.login_attempts == 1

    async def test_unknown_employee_raises(self, session: AsyncSession):
        with pytest.raises(ValueError, match="Nieprawidłowy"):
            await authenticate_user(session, "NIEZNANY_EMP", "123456")

    async def test_inactive_user_raises(self, session: AsyncSession, user: User):
        user.is_active = False
        await session.flush()
        with pytest.raises(ValueError, match="dezaktywowane"):
            await authenticate_user(session, user.hr_employee_id, "123456")


@pytest.mark.asyncio
class TestAuthFlowLockout:
    async def test_lockout_after_5_failures(self, session: AsyncSession, user: User):
        for _ in range(MAX_LOGIN_ATTEMPTS):
            try:
                await authenticate_user(session, user.hr_employee_id, "wrong")
            except ValueError:
                pass
        await session.refresh(user)
        assert user.locked_until is not None
        assert user.locked_until > datetime.now(timezone.utc)

    async def test_locked_account_raises(self, session: AsyncSession, user: User):
        # Zablokuj konto ręcznie
        user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=10)
        user.login_attempts = MAX_LOGIN_ATTEMPTS
        await session.flush()

        with pytest.raises(ValueError, match="zablokowane"):
            await authenticate_user(session, user.hr_employee_id, "123456")

    async def test_expired_lockout_allows_login(self, session: AsyncSession, user: User):
        # Blokada już minęła
        user.locked_until = datetime.now(timezone.utc) - timedelta(minutes=1)
        user.login_attempts = MAX_LOGIN_ATTEMPTS
        await session.flush()

        _, token = await authenticate_user(session, user.hr_employee_id, "123456")
        assert isinstance(token, str)

    async def test_lockout_lasts_15_minutes(self, session: AsyncSession, user: User):
        for _ in range(MAX_LOGIN_ATTEMPTS):
            try:
                await authenticate_user(session, user.hr_employee_id, "wrong")
            except ValueError:
                pass
        await session.refresh(user)
        expected_min = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_MINUTES - 1)
        assert user.locked_until > expected_min


@pytest.mark.asyncio
class TestAuthFlowMustChangePin:
    async def test_temp_pin_login_returns_must_change_flag(
        self, session: AsyncSession, user_must_change_pin: User
    ):
        _, token = await authenticate_user(
            session,
            user_must_change_pin.hr_employee_id,
            user_must_change_pin._temp_pin,  # type: ignore[attr-defined]
        )
        assert isinstance(token, str)
        await session.refresh(user_must_change_pin)
        assert user_must_change_pin.must_change_pin is True

    async def test_change_pin_clears_flag(
        self, session: AsyncSession, user_must_change_pin: User
    ):
        _, _ = await authenticate_user(
            session,
            user_must_change_pin.hr_employee_id,
            user_must_change_pin._temp_pin,  # type: ignore[attr-defined]
        )
        await change_pin(session, user_must_change_pin, "111222", "111222")
        await session.refresh(user_must_change_pin)
        assert user_must_change_pin.must_change_pin is False

    async def test_change_pin_issues_new_jti(
        self, session: AsyncSession, user_must_change_pin: User
    ):
        _, _ = await authenticate_user(
            session,
            user_must_change_pin.hr_employee_id,
            user_must_change_pin._temp_pin,  # type: ignore[attr-defined]
        )
        old_jti = user_must_change_pin.current_jti
        await change_pin(session, user_must_change_pin, "111222", "111222")
        await session.refresh(user_must_change_pin)
        assert user_must_change_pin.current_jti != old_jti


@pytest.mark.asyncio
class TestJtiInvalidation:
    async def test_new_login_invalidates_old_jti(
        self, session: AsyncSession, user: User
    ):
        """Nowe logowanie zmienia jti — poprzedni token traci ważność."""
        _, token1 = await authenticate_user(session, user.hr_employee_id, "123456")
        payload1 = jwt.decode(token1, settings.secret_key, algorithms=[settings.jwt_algorithm])
        jti1 = payload1["jti"]

        # Nowe logowanie
        _, token2 = await authenticate_user(session, user.hr_employee_id, "123456")
        payload2 = jwt.decode(token2, settings.secret_key, algorithms=[settings.jwt_algorithm])

        await session.refresh(user)
        # Aktualny jti w bazie to jti2
        assert str(user.current_jti) == payload2["jti"]
        # Stary jti jest inny
        assert jti1 != payload2["jti"]
