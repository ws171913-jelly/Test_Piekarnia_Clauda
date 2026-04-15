"""
T073 — Test integracyjny: zdarzenie KONIEC_OKRESU.

- atomowe zerowanie sald + unieważnienie wszystkich kodów AKTYWNY
- kod użyty po zdarzeniu → błąd WYGASŁY
"""
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.codes import generate_code, verify_code
from src.domain.hr_processor import process_hr_event
from src.models.auth_code import AuthCode, AuthCodeStatus
from src.models.hr_event import HrEventType
from src.models.user import User
from src.schemas.hr_events import HrEventPayload


@pytest.mark.asyncio
class TestPeriodEndCodes:
    async def test_koniec_okresu_zeroes_balance(
        self, session: AsyncSession, user: User
    ):
        assert float(user.current_balance) > 0
        payload = HrEventPayload(hr_employee_id=user.hr_employee_id)
        await process_hr_event(session, HrEventType.KONIEC_OKRESU, payload, uuid.uuid4())
        await session.refresh(user)
        assert float(user.current_balance) == 0.0

    async def test_koniec_okresu_invalidates_active_codes(
        self, session: AsyncSession, user: User
    ):
        """Aktywne kody zmieniają status na WYGASLY."""
        _, code1 = await generate_code(session, user)
        # Resetuj cooldown
        user.last_code_generated_at = None
        await session.flush()
        _, code2 = await generate_code(session, user)

        assert code1.status == AuthCodeStatus.AKTYWNY
        assert code2.status == AuthCodeStatus.AKTYWNY

        payload = HrEventPayload(hr_employee_id=user.hr_employee_id)
        await process_hr_event(session, HrEventType.KONIEC_OKRESU, payload, uuid.uuid4())

        await session.refresh(code1)
        await session.refresh(code2)
        assert code1.status == AuthCodeStatus.WYGASLY
        assert code2.status == AuthCodeStatus.WYGASLY

    async def test_code_verify_fails_after_period_end(
        self, session: AsyncSession, user: User
    ):
        """Weryfikacja kodu po KONIEC_OKRESU → 'Nieprawidłowy lub wygasły'."""
        code_str, _ = await generate_code(session, user)

        payload = HrEventPayload(hr_employee_id=user.hr_employee_id)
        await process_hr_event(session, HrEventType.KONIEC_OKRESU, payload, uuid.uuid4())

        with pytest.raises(ValueError, match="Nieprawidłowy lub wygasły"):
            await verify_code(session, code_str, 50.0, "terminal-dev")

    async def test_koniec_okresu_does_not_affect_other_users_codes(
        self,
        session: AsyncSession,
        user: User,
        user_zero_balance: User,
    ):
        """KONIEC_OKRESU nie unieważnia kodów innego użytkownika."""
        # Daj saldo drugiemu userowi
        user_zero_balance.current_balance = 100.0  # type: ignore[assignment]
        await session.flush()
        _, other_code = await generate_code(session, user_zero_balance)
        assert other_code.status == AuthCodeStatus.AKTYWNY

        # KONIEC_OKRESU dla pierwszego użytkownika
        payload = HrEventPayload(hr_employee_id=user.hr_employee_id)
        await process_hr_event(session, HrEventType.KONIEC_OKRESU, payload, uuid.uuid4())

        await session.refresh(other_code)
        assert other_code.status == AuthCodeStatus.AKTYWNY

    async def test_no_active_codes_no_error(
        self, session: AsyncSession, user: User
    ):
        """KONIEC_OKRESU bez aktywnych kodów nie rzuca błędu."""
        payload = HrEventPayload(hr_employee_id=user.hr_employee_id)
        await process_hr_event(session, HrEventType.KONIEC_OKRESU, payload, uuid.uuid4())
        await session.refresh(user)
        assert float(user.current_balance) == 0.0
