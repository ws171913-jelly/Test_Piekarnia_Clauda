"""
T053 — Test integracyjny: webhook HR DOŁADOWANIE — saldo zaktualizowane po zdarzeniu.
"""
import uuid
from datetime import date, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.hr_processor import process_hr_event
from src.models.hr_event import HrEventType
from src.models.user import User
from src.schemas.hr_events import HrEventPayload


def _event_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.mark.asyncio
class TestHrWebhookDoladowanie:
    async def test_doladowanie_increases_balance(
        self, session: AsyncSession, user: User
    ):
        """DOŁADOWANIE = saldo wzrasta o podaną kwotę."""
        balance_before = float(user.current_balance)
        payload = HrEventPayload(
            hr_employee_id=user.hr_employee_id,
            amount_pln=200.0,
            expiry_date=date.today() + timedelta(days=30),
        )
        await process_hr_event(session, HrEventType.DOLADOWANIE, payload, _event_id())
        await session.refresh(user)
        assert float(user.current_balance) == balance_before + 200.0

    async def test_doladowanie_updates_expiry_date(
        self, session: AsyncSession, user: User
    ):
        new_expiry = date.today() + timedelta(days=60)
        payload = HrEventPayload(
            hr_employee_id=user.hr_employee_id,
            amount_pln=100.0,
            expiry_date=new_expiry,
        )
        await process_hr_event(session, HrEventType.DOLADOWANIE, payload, _event_id())
        await session.refresh(user)
        assert user.balance_expiry_date == new_expiry

    async def test_doladowanie_unknown_employee_raises(
        self, session: AsyncSession
    ):
        payload = HrEventPayload(
            hr_employee_id="NIEZNANY_999",
            amount_pln=100.0,
            expiry_date=date.today() + timedelta(days=30),
        )
        with pytest.raises(ValueError, match="Nieznany"):
            await process_hr_event(session, HrEventType.DOLADOWANIE, payload, _event_id())


@pytest.mark.asyncio
class TestHrWebhookZmianaKoszyka:
    async def test_zmiana_koszyka_updates_basket(
        self, session: AsyncSession, user: User, basket_with_limit
    ):
        payload = HrEventPayload(
            hr_employee_id=user.hr_employee_id,
            hr_basket_id=basket_with_limit.hr_basket_id,
        )
        await process_hr_event(session, HrEventType.ZMIANA_KOSZYKA, payload, _event_id())
        await session.refresh(user)
        assert user.basket_id == basket_with_limit.id


@pytest.mark.asyncio
class TestHrWebhookKoniecOkresu:
    async def test_koniec_okresu_zeroes_balance(
        self, session: AsyncSession, user: User
    ):
        assert float(user.current_balance) > 0
        payload = HrEventPayload(hr_employee_id=user.hr_employee_id)
        await process_hr_event(session, HrEventType.KONIEC_OKRESU, payload, _event_id())
        await session.refresh(user)
        assert float(user.current_balance) == 0.0

    async def test_koniec_okresu_invalidates_active_codes(
        self, session: AsyncSession, user: User
    ):
        from src.domain.codes import generate_code
        from src.models.auth_code import AuthCodeStatus

        _, auth_code = await generate_code(session, user)
        assert auth_code.status == AuthCodeStatus.AKTYWNY

        payload = HrEventPayload(hr_employee_id=user.hr_employee_id)
        await process_hr_event(session, HrEventType.KONIEC_OKRESU, payload, _event_id())
        await session.refresh(auth_code)
        assert auth_code.status == AuthCodeStatus.WYGASLY


@pytest.mark.asyncio
class TestHrWebhookDezaktywacja:
    async def test_dezaktywacja_deactivates_user(
        self, session: AsyncSession, user: User
    ):
        payload = HrEventPayload(hr_employee_id=user.hr_employee_id)
        await process_hr_event(session, HrEventType.DEZAKTYWACJA, payload, _event_id())
        await session.refresh(user)
        assert user.is_active is False
        assert float(user.current_balance) == 0.0
