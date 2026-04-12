import secrets
import uuid
from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


def hash_pin(pin: str) -> str:
    return pwd_context.hash(pin)


def verify_pin(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def generate_temp_pin() -> str:
    """Generuje losowy 6-cyfrowy PIN tymczasowy."""
    return str(secrets.randbelow(900000) + 100000)


def create_jwt(user_id: uuid.UUID, jti: uuid.UUID) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "jti": str(jti),
        "iat": now,
        "exp": now + timedelta(hours=settings.jwt_ttl_hours),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


async def authenticate_user(
    session: AsyncSession, hr_employee_id: str, pin: str
) -> tuple[User, str]:
    """
    Weryfikuje dane logowania, zarządza blokadą konta i wydaje JWT.

    Returns:
        (user, access_token)

    Raises:
        ValueError: błędne dane, konto zablokowane, nieaktywne
    """
    result = await session.execute(select(User).where(User.hr_employee_id == hr_employee_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise ValueError("Nieprawidłowy numer pracownika lub PIN")

    if not user.is_active:
        raise ValueError("Konto jest dezaktywowane")

    now = datetime.now(timezone.utc)

    if user.locked_until and user.locked_until > now:
        remaining = int((user.locked_until - now).total_seconds() / 60) + 1
        raise ValueError(f"Konto zablokowane na {remaining} min")

    if not verify_pin(pin, user.pin_hash):
        user.login_attempts += 1
        if user.login_attempts >= MAX_LOGIN_ATTEMPTS:
            user.locked_until = now + timedelta(minutes=LOCKOUT_MINUTES)
        await session.commit()
        remaining_attempts = max(0, MAX_LOGIN_ATTEMPTS - user.login_attempts)
        raise ValueError(f"Błędny PIN. Pozostało prób: {remaining_attempts}")

    # Sukces — zeruj licznik, wydaj nowy JTI
    user.login_attempts = 0
    user.locked_until = None
    new_jti = uuid.uuid4()
    user.current_jti = new_jti
    await session.commit()
    await session.refresh(user)

    token = create_jwt(user.id, new_jti)
    return user, token


async def change_pin(
    session: AsyncSession, user: User, new_pin: str, confirm_pin: str
) -> str:
    """
    Zmienia PIN użytkownika i zeruje flagę must_change_pin.

    Returns:
        access_token — nowy JWT po zmianie PIN
    """
    if new_pin != confirm_pin:
        raise ValueError("PIN-y nie pasują do siebie")

    user.pin_hash = hash_pin(new_pin)
    user.must_change_pin = False
    new_jti = uuid.uuid4()
    user.current_jti = new_jti
    await session.commit()
    await session.refresh(user)

    return create_jwt(user.id, new_jti)
