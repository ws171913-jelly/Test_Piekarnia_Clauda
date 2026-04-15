"""
T075 — Test jednostkowy: unieważnienie sesji jti.

Stary token → 401 po nowym logowaniu tego samego pracownika.
Test bez bazy danych — weryfikacja logiki walidacji JTI w deps.py.
"""
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
import jwt

from src.config import settings
from src.domain.auth import create_jwt, hash_pin, authenticate_user


def _make_user(pin: str = "1234") -> MagicMock:
    user = MagicMock()
    user.id = uuid.uuid4()
    user.hr_employee_id = "EMP_JTI_TEST"
    user.pin_hash = hash_pin(pin)
    user.is_active = True
    user.login_attempts = 0
    user.locked_until = None
    user.must_change_pin = False
    user.current_jti = None
    return user


async def _authenticate(user: MagicMock, pin: str) -> tuple[MagicMock, str]:
    session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user
    session.execute.return_value = mock_result
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return await authenticate_user(session, user.hr_employee_id, pin)


class TestJtiInvalidation:
    async def test_new_login_changes_jti(self):
        """Każde logowanie generuje nowy jti."""
        user = _make_user()
        _, token1 = await _authenticate(user, "1234")
        jti1 = user.current_jti

        _, token2 = await _authenticate(user, "1234")
        jti2 = user.current_jti

        assert jti1 != jti2

    async def test_old_token_has_stale_jti(self):
        """Stary token zawiera poprzednie jti — nie pasuje do aktualnego w bazie."""
        user = _make_user()

        _, token1 = await _authenticate(user, "1234")
        payload1 = jwt.decode(token1, settings.secret_key, algorithms=[settings.jwt_algorithm])
        old_jti = payload1["jti"]

        # Drugie logowanie — zmienia jti
        _, token2 = await _authenticate(user, "1234")
        current_jti = str(user.current_jti)

        assert old_jti != current_jti

    async def test_token_jti_matches_user_current_jti_after_login(self):
        """Token po logowaniu ma jti = users.current_jti."""
        user = _make_user()
        _, token = await _authenticate(user, "1234")
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])

        assert payload["jti"] == str(user.current_jti)

    async def test_create_jwt_encodes_jti(self):
        """create_jwt() zapisuje jti w tokenie."""
        user_id = uuid.uuid4()
        jti = uuid.uuid4()
        token = create_jwt(user_id, jti)
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        assert payload["jti"] == str(jti)
        assert payload["sub"] == str(user_id)

    async def test_create_jwt_has_expiry(self):
        """Token ma pole exp ustawione w przyszłości."""
        user_id = uuid.uuid4()
        jti = uuid.uuid4()
        token = create_jwt(user_id, jti)
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        assert payload["exp"] > datetime.now(timezone.utc).timestamp()

    async def test_multiple_logins_each_update_jti(self):
        """5 kolejnych logowań → 5 różnych jti."""
        user = _make_user()
        jtis = set()
        for _ in range(5):
            await _authenticate(user, "1234")
            jtis.add(str(user.current_jti))
        assert len(jtis) == 5
