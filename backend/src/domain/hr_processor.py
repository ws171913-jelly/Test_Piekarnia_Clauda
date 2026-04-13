import uuid
from datetime import date, datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.auth import generate_temp_pin, hash_pin
from src.models.auth_code import AuthCode, AuthCodeStatus
from src.models.basket import Basket
from src.models.hr_event import HrEvent, HrEventStatus, HrEventType
from src.models.user import User
from src.schemas.hr_events import HrEventPayload


async def process_hr_event(
    session: AsyncSession,
    event_type: HrEventType,
    payload: HrEventPayload,
    event_id: uuid.UUID,
) -> str | None:
    """
    Przetwarza zdarzenie HR.

    Returns:
        temp_pin — tymczasowy PIN (tylko dla NOWY_PRACOWNIK i RESET_PIN), inaczej None

    Raises:
        ValueError: nieznany pracownik (poza NOWY_PRACOWNIK), brakujące dane
    """
    now = datetime.now(timezone.utc)

    if event_type == HrEventType.NOWY_PRACOWNIK:
        return await _handle_nowy_pracownik(session, payload, now, event_id)

    # Wszystkie pozostałe typy wymagają istniejącego pracownika
    if not payload.hr_employee_id:
        raise ValueError("Brak hr_employee_id w payload")

    result = await session.execute(
        select(User).where(User.hr_employee_id == payload.hr_employee_id).with_for_update()
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise ValueError(f"Nieznany pracownik: {payload.hr_employee_id}")

    if event_type == HrEventType.ZMIANA_KOSZYKA:
        await _handle_zmiana_koszyka(session, user, payload)
    elif event_type == HrEventType.DOLADOWANIE:
        await _handle_doladowanie(session, user, payload)
    elif event_type == HrEventType.KONIEC_OKRESU:
        await _handle_koniec_okresu(session, user, now)
    elif event_type == HrEventType.DEZAKTYWACJA:
        await _handle_dezaktywacja(session, user, now)
    elif event_type == HrEventType.RESET_PIN:
        return await _handle_reset_pin(session, user)

    return None


async def _handle_nowy_pracownik(
    session: AsyncSession,
    payload: HrEventPayload,
    now: datetime,
    event_id: uuid.UUID,
) -> str:
    if not payload.hr_employee_id:
        raise ValueError("Brak hr_employee_id w payload")
    if not payload.hr_basket_id:
        raise ValueError("Brak hr_basket_id w payload")
    if not payload.location_id:
        raise ValueError("Brak location_id w payload")
    if not payload.expiry_date:
        raise ValueError("Brak expiry_date w payload")

    basket_result = await session.execute(
        select(Basket).where(Basket.hr_basket_id == payload.hr_basket_id)
    )
    basket = basket_result.scalar_one_or_none()
    if basket is None:
        raise ValueError(f"Nieznany koszyk: {payload.hr_basket_id}")

    temp_pin = generate_temp_pin()

    user = User(
        hr_employee_id=payload.hr_employee_id,
        basket_id=basket.id,
        pin_hash=hash_pin(temp_pin),
        must_change_pin=True,
        current_balance=0,
        balance_expiry_date=payload.expiry_date,
        location_id=payload.location_id,
        is_active=True,
    )
    session.add(user)
    await session.flush()
    return temp_pin


async def _handle_zmiana_koszyka(
    session: AsyncSession,
    user: User,
    payload: HrEventPayload,
) -> None:
    if not payload.hr_basket_id:
        raise ValueError("Brak hr_basket_id w payload")

    basket_result = await session.execute(
        select(Basket).where(Basket.hr_basket_id == payload.hr_basket_id)
    )
    basket = basket_result.scalar_one_or_none()
    if basket is None:
        raise ValueError(f"Nieznany koszyk: {payload.hr_basket_id}")

    user.basket_id = basket.id
    await session.flush()


async def _handle_doladowanie(
    session: AsyncSession,
    user: User,
    payload: HrEventPayload,
) -> None:
    if payload.amount_pln is None:
        raise ValueError("Brak amount_pln w payload")
    if payload.expiry_date is None:
        raise ValueError("Brak expiry_date w payload")

    user.current_balance = float(user.current_balance) + float(payload.amount_pln)  # type: ignore[assignment]
    user.balance_expiry_date = payload.expiry_date
    await session.flush()


async def _handle_koniec_okresu(
    session: AsyncSession,
    user: User,
    now: datetime,
) -> None:
    """Atomowe zerowanie salda + unieważnienie wszystkich kodów AKTYWNY."""
    user.current_balance = 0  # type: ignore[assignment]

    await session.execute(
        update(AuthCode)
        .where(AuthCode.user_id == user.id)
        .where(AuthCode.status == AuthCodeStatus.AKTYWNY)
        .values(status=AuthCodeStatus.WYGASLY)
    )


async def _handle_dezaktywacja(
    session: AsyncSession,
    user: User,
    now: datetime,
) -> None:
    user.is_active = False
    user.current_balance = 0  # type: ignore[assignment]

    await session.execute(
        update(AuthCode)
        .where(AuthCode.user_id == user.id)
        .where(AuthCode.status == AuthCodeStatus.AKTYWNY)
        .values(status=AuthCodeStatus.WYGASLY)
    )


async def _handle_reset_pin(
    session: AsyncSession,
    user: User,
) -> str:
    temp_pin = generate_temp_pin()
    user.pin_hash = hash_pin(temp_pin)
    user.must_change_pin = True
    user.locked_until = None
    user.login_attempts = 0
    user.current_jti = None
    await session.flush()
    return temp_pin
