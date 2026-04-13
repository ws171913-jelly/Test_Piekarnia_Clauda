"""
T069 — Dodatkowe testy jednostkowe: przypadki brzegowe.

- wygasła data ważności środków (balance_expiry_date)
- dezaktywowany pracownik
- wygasły JWT
"""
import uuid
from datetime import date, datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from jose import ExpiredSignatureError, jwt

from src.config import settings
from src.domain.auth import authenticate_user, create_jwt, hash_pin
from src.domain.codes import generate_code


def _make_user(
    pin: str = "1234",
    is_active: bool = True,
    balance: float = 100.0,
    balance_expiry: date | None = None,
) -> MagicMock:
    user = MagicMock()
    user.id = uuid.uuid4()
    user.hr_employee_id = "EMP_EDGE_TEST"
    user.pin_hash = hash_pin(pin)
    user.is_active = is_active
    user.login_attempts = 0
    user.locked_until = None
    user.must_change_pin = False
    user.current_jti = None
    user.current_balance = balance
    user.last_code_generated_at = None
    user.balance_expiry_date = balance_expiry or date.today() + timedelta(days=30)
    return user


async def _auth(user: MagicMock, pin: str = "1234") -> tuple[MagicMock, str]:
    session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user
    session.execute.return_value = mock_result
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return await authenticate_user(session, user.hr_employee_id, pin)


@pytest.mark.asyncio
class TestDeactivatedEmployee:
    async def test_deactivated_employee_cannot_login(self):
        """Dezaktywowany pracownik → ValueError 'dezaktywowane'."""
        user = _make_user(is_active=False)
        with pytest.raises(ValueError, match="dezaktywowane"):
            await _auth(user)

    async def test_active_employee_can_login(self):
        """Aktywny pracownik może się zalogować."""
        user = _make_user(is_active=True)
        _, token = await _auth(user)
        assert isinstance(token, str)

    async def test_deactivated_employee_cannot_generate_code(self):
        """Dezaktywowany pracownik z is_active=False — generowanie kodu powinno być niemożliwe.

        Weryfikujemy, że generate_code sprawdza saldo, nie is_active
        (blokada jest na poziomie auth, nie generate_code).
        Jeśli dezaktywowany user ma saldo 0 — kod nie może być wygenerowany.
        """
        user = _make_user(is_active=False, balance=0.0)
        session = AsyncMock()
        with pytest.raises(ValueError, match="Brak salda"):
            await generate_code(session, user)


@pytest.mark.asyncio
class TestExpiredBalanceDate:
    async def test_generate_code_ignores_expiry_date(self):
        """generate_code nie weryfikuje balance_expiry_date — to zadanie warstwy HR.

        Domyślnie kod może być wygenerowany nawet po dacie ważności salda
        (logika wygasania salda to zdarzenie KONIEC_OKRESU, nie generate_code).
        Ten test dokumentuje obecne zachowanie.
        """
        user = _make_user(
            balance=50.0,
            balance_expiry=date.today() - timedelta(days=1),  # przeszłość
        )
        session = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.add = MagicMock()

        # generate_code nie rzuca — sprawdza tylko saldo, nie datę ważności
        code, auth_code = await generate_code(session, user)
        assert len(code) == 6
        assert code.isdigit()

    async def test_zero_balance_after_expiry_blocks_code(self):
        """Po KONIEC_OKRESU saldo = 0 → Brak salda."""
        user = _make_user(
            balance=0.0,
            balance_expiry=date.today() - timedelta(days=1),
        )
        session = AsyncMock()
        with pytest.raises(ValueError, match="Brak salda"):
            await generate_code(session, user)


@pytest.mark.asyncio
class TestExpiredJwt:
    async def test_expired_jwt_raises_on_decode(self):
        """Token z przeszłą datą exp → ExpiredSignatureError przy dekodowaniu."""
        user_id = uuid.uuid4()
        jti = uuid.uuid4()

        # Stwórz token z exp w przeszłości
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user_id),
            "jti": str(jti),
            "iat": now - timedelta(hours=10),
            "exp": now - timedelta(hours=2),  # wygasł 2h temu
        }
        expired_token = jwt.encode(
            payload, settings.secret_key, algorithm=settings.jwt_algorithm
        )

        with pytest.raises(ExpiredSignatureError):
            jwt.decode(
                expired_token,
                settings.secret_key,
                algorithms=[settings.jwt_algorithm],
            )

    async def test_valid_jwt_is_decodable(self):
        """Token z przyszłą datą exp dekoduje się poprawnie."""
        user_id = uuid.uuid4()
        jti = uuid.uuid4()
        token = create_jwt(user_id, jti)

        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        assert payload["sub"] == str(user_id)
        assert payload["jti"] == str(jti)

    async def test_jwt_expires_after_ttl(self):
        """Token wygasa po settings.jwt_ttl_hours godzinach."""
        user_id = uuid.uuid4()
        jti = uuid.uuid4()
        token = create_jwt(user_id, jti)
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        exp = payload["exp"]
        now_ts = datetime.now(timezone.utc).timestamp()

        expected_ttl_seconds = settings.jwt_ttl_hours * 3600
        actual_ttl = exp - now_ts
        # Dopuszczamy ±5s margines
        assert abs(actual_ttl - expected_ttl_seconds) < 5
