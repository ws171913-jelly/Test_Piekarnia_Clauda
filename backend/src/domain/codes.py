import math
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.config import settings
from src.models.auth_code import AuthCode, AuthCodeStatus
from src.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

CODE_TTL_MINUTES = 15
COOLDOWN_MINUTES = 30
VERIFICATION_TOKEN_TTL_MINUTES = 10


def _generate_otp() -> str:
    """Kryptograficznie losowy 6-cyfrowy kod."""
    return f"{secrets.randbelow(900000) + 100000:06d}"


def _hash_code(code: str) -> str:
    return pwd_context.hash(code)


def _verify_code(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _calculate_discount(
    gross_amount: float,
    discount_pct: float,
    balance: float,
    monthly_limit: float | None = None,
) -> float:
    """min(saldo, floor(kwota × pct))"""
    raw = math.floor(gross_amount * discount_pct / 100)
    discount = min(balance, raw)
    if monthly_limit is not None:
        discount = min(discount, monthly_limit)
    return discount


async def generate_code(session: AsyncSession, user: User) -> tuple[str, AuthCode]:
    """
    Generuje kod OTP dla pracownika.

    Raises:
        ValueError: karencja 30 min lub zerowe saldo
    """
    now = datetime.now(timezone.utc)

    if float(user.current_balance) <= 0:
        raise ValueError("Brak salda — generowanie kodu niemożliwe")

    if user.last_code_generated_at is not None:
        elapsed = now - user.last_code_generated_at.replace(tzinfo=timezone.utc)
        if elapsed < timedelta(minutes=COOLDOWN_MINUTES):
            remaining = int((timedelta(minutes=COOLDOWN_MINUTES) - elapsed).total_seconds() / 60) + 1
            raise ValueError(f"Karencja — poczekaj {remaining} min przed wygenerowaniem nowego kodu")

    code = _generate_otp()
    code_hash = _hash_code(code)
    expires_at = now + timedelta(minutes=CODE_TTL_MINUTES)

    auth_code = AuthCode(
        user_id=user.id,
        code_hash=code_hash,
        status=AuthCodeStatus.AKTYWNY,
        expires_at=expires_at,
    )
    session.add(auth_code)
    user.last_code_generated_at = now
    await session.commit()
    await session.refresh(auth_code)

    return code, auth_code


async def verify_code(
    session: AsyncSession,
    code_plain: str,
    gross_amount_pln: float,
    pos_terminal_id: str,
    pos_transaction_ref: str | None = None,
) -> tuple[str, float, float, float, uuid.UUID]:
    """
    Weryfikacja kodu przez terminal POS.

    Returns:
        (verification_token, discount_amount, discount_pct, net_amount, code_id)

    Raises:
        ValueError: kod nieważny, wygasły, już użyty, niewystarczające saldo
    """
    now = datetime.now(timezone.utc)

    # Znajdź aktywne kody — bez blokady (weryfikacja tylko odczytuje)
    result = await session.execute(
        select(AuthCode)
        .where(AuthCode.status == AuthCodeStatus.AKTYWNY)
        .where(AuthCode.expires_at > now)
    )
    active_codes = result.scalars().all()

    matched_code: AuthCode | None = None
    for ac in active_codes:
        if _verify_code(code_plain, ac.code_hash):
            matched_code = ac
            break

    if matched_code is None:
        raise ValueError("Nieprawidłowy lub wygasły kod")

    # Pobierz użytkownika z blokadą wiersza i eager load koszyka
    result2 = await session.execute(
        select(User)
        .where(User.id == matched_code.user_id)
        .with_for_update()
        .options(selectinload(User.basket))
    )
    user = result2.scalar_one()

    discount_pct = float(user.basket.discount_pct) if user.basket else 0.0
    monthly_limit = user.basket.monthly_limit_pln if user.basket else None

    discount_amount = _calculate_discount(
        gross_amount_pln, discount_pct, float(user.current_balance), monthly_limit
    )
    net_amount = gross_amount_pln - discount_amount

    # Wydaj verification_token JWT z danymi transakcji
    payload = {
        "sub": str(user.id),
        "code_id": str(matched_code.id),
        "discount_amount": discount_amount,
        "discount_pct": discount_pct,
        "net_amount": net_amount,
        "gross_amount": gross_amount_pln,
        "pos_terminal_id": pos_terminal_id,
        "pos_transaction_ref": pos_transaction_ref,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=VERIFICATION_TOKEN_TTL_MINUTES),
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)

    return token, discount_amount, discount_pct, net_amount, matched_code.id
