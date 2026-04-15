"""
T072 — Test integracyjny: zdarzenie RESET_PIN.

- nowy PIN tymczasowy w odpowiedzi
- wymuszona zmiana przy pierwszym logowaniu
- zerowanie blokady konta
"""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.auth import authenticate_user, change_pin
from src.domain.hr_processor import process_hr_event
from src.models.hr_event import HrEventType
from src.models.user import User
from src.schemas.hr_events import HrEventPayload


@pytest.mark.asyncio
class TestResetPin:
    async def test_reset_pin_returns_temp_pin(
        self, session: AsyncSession, user: User
    ):
        """RESET_PIN zwraca tymczasowy PIN."""
        payload = HrEventPayload(hr_employee_id=user.hr_employee_id)
        temp_pin = await process_hr_event(
            session, HrEventType.RESET_PIN, payload, uuid.uuid4()
        )
        assert temp_pin is not None
        assert len(temp_pin) == 6
        assert temp_pin.isdigit()

    async def test_reset_pin_sets_must_change_pin(
        self, session: AsyncSession, user: User
    ):
        payload = HrEventPayload(hr_employee_id=user.hr_employee_id)
        await process_hr_event(session, HrEventType.RESET_PIN, payload, uuid.uuid4())
        await session.refresh(user)
        assert user.must_change_pin is True

    async def test_reset_pin_clears_lockout(
        self, session: AsyncSession, user: User
    ):
        """RESET_PIN zeruje blokadę konta."""
        user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=10)
        user.login_attempts = 5
        await session.flush()

        payload = HrEventPayload(hr_employee_id=user.hr_employee_id)
        await process_hr_event(session, HrEventType.RESET_PIN, payload, uuid.uuid4())
        await session.refresh(user)

        assert user.locked_until is None
        assert user.login_attempts == 0

    async def test_reset_pin_clears_current_jti(
        self, session: AsyncSession, user: User
    ):
        """RESET_PIN unieważnia bieżącą sesję (jti = None)."""
        user.current_jti = uuid.uuid4()
        await session.flush()

        payload = HrEventPayload(hr_employee_id=user.hr_employee_id)
        await process_hr_event(session, HrEventType.RESET_PIN, payload, uuid.uuid4())
        await session.refresh(user)
        assert user.current_jti is None

    async def test_login_with_temp_pin_after_reset(
        self, session: AsyncSession, user: User
    ):
        """Logowanie nowym tymczasowym PIN-em po resecie — sukces, must_change_pin = True."""
        payload = HrEventPayload(hr_employee_id=user.hr_employee_id)
        temp_pin = await process_hr_event(
            session, HrEventType.RESET_PIN, payload, uuid.uuid4()
        )
        await session.commit()  # zatwierdź zmianę PIN-u

        result_user, token = await authenticate_user(
            session, user.hr_employee_id, temp_pin
        )
        await session.refresh(result_user)
        assert result_user.must_change_pin is True
        assert isinstance(token, str)

    async def test_forced_pin_change_after_reset(
        self, session: AsyncSession, user: User
    ):
        """Po resecie: logowanie tymczasowym PIN → zmiana PIN → must_change_pin = False."""
        payload = HrEventPayload(hr_employee_id=user.hr_employee_id)
        temp_pin = await process_hr_event(
            session, HrEventType.RESET_PIN, payload, uuid.uuid4()
        )

        result_user, _ = await authenticate_user(session, user.hr_employee_id, temp_pin)
        await change_pin(session, result_user, "444555", "444555")
        await session.refresh(result_user)
        assert result_user.must_change_pin is False

    async def test_reset_pin_unknown_employee_raises(
        self, session: AsyncSession
    ):
        payload = HrEventPayload(hr_employee_id="NIEZNANY_EMP_001")
        with pytest.raises(ValueError, match="Nieznany"):
            await process_hr_event(
                session, HrEventType.RESET_PIN, payload, uuid.uuid4()
            )
