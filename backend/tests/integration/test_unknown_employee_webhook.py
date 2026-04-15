"""
T074 — Test integracyjny: webhook z nieznanym hr_employee_id.

- DOŁADOWANIE/ZMIANA_KOSZYKA/RESET_PIN → ValueError (nieznany pracownik)
- NOWY_PRACOWNIK → sukces (tworzy rekord)
"""
import uuid
from datetime import date, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.hr_processor import process_hr_event
from src.models.hr_event import HrEventType
from src.models.user import User
from src.schemas.hr_events import HrEventPayload


UNKNOWN_EMPLOYEE = "NIEZNANY_EMP_XYZ_999"


@pytest.mark.asyncio
class TestUnknownEmployeeWebhook:
    async def test_doladowanie_unknown_employee_raises(
        self, session: AsyncSession
    ):
        payload = HrEventPayload(
            hr_employee_id=UNKNOWN_EMPLOYEE,
            amount_pln=100.0,
            expiry_date=date.today() + timedelta(days=30),
        )
        with pytest.raises(ValueError, match="Nieznany"):
            await process_hr_event(session, HrEventType.DOLADOWANIE, payload, uuid.uuid4())

    async def test_zmiana_koszyka_unknown_employee_raises(
        self, session: AsyncSession
    ):
        payload = HrEventPayload(
            hr_employee_id=UNKNOWN_EMPLOYEE,
            hr_basket_id="TEST_BASKET_001",
        )
        with pytest.raises(ValueError, match="Nieznany"):
            await process_hr_event(session, HrEventType.ZMIANA_KOSZYKA, payload, uuid.uuid4())

    async def test_reset_pin_unknown_employee_raises(
        self, session: AsyncSession
    ):
        payload = HrEventPayload(hr_employee_id=UNKNOWN_EMPLOYEE)
        with pytest.raises(ValueError, match="Nieznany"):
            await process_hr_event(session, HrEventType.RESET_PIN, payload, uuid.uuid4())

    async def test_koniec_okresu_unknown_employee_raises(
        self, session: AsyncSession
    ):
        payload = HrEventPayload(hr_employee_id=UNKNOWN_EMPLOYEE)
        with pytest.raises(ValueError, match="Nieznany"):
            await process_hr_event(session, HrEventType.KONIEC_OKRESU, payload, uuid.uuid4())

    async def test_dezaktywacja_unknown_employee_raises(
        self, session: AsyncSession
    ):
        payload = HrEventPayload(hr_employee_id=UNKNOWN_EMPLOYEE)
        with pytest.raises(ValueError, match="Nieznany"):
            await process_hr_event(session, HrEventType.DEZAKTYWACJA, payload, uuid.uuid4())

    async def test_nowy_pracownik_creates_user(
        self, session: AsyncSession, basket
    ):
        """NOWY_PRACOWNIK z nieznanym ID → tworzy nowy rekord pracownika."""
        new_emp_id = f"NOWY_{uuid.uuid4().hex[:8]}"
        payload = HrEventPayload(
            hr_employee_id=new_emp_id,
            hr_basket_id=basket.hr_basket_id,
            location_id="LOC_001",
            expiry_date=date.today() + timedelta(days=30),
        )
        temp_pin = await process_hr_event(
            session, HrEventType.NOWY_PRACOWNIK, payload, uuid.uuid4()
        )
        assert temp_pin is not None
        assert len(temp_pin) == 6

        result = await session.execute(
            select(User).where(User.hr_employee_id == new_emp_id)
        )
        new_user = result.scalar_one_or_none()
        assert new_user is not None
        assert new_user.must_change_pin is True
        assert float(new_user.current_balance) == 0.0
