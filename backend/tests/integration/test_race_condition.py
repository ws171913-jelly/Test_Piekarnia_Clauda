"""
T051 — Test integracyjny: wyścig procesów.

Dwa jednoczesne POST /codes/verify dla tego samego kodu —
tylko jedno żądanie może się powieść (SELECT FOR UPDATE).

Uwaga: pełny test race condition wymaga dwóch równoległych transakcji
bazodanowych. Ten test weryfikuje, że kod po pierwszym verify+finalize
nie może być ponownie finalizowany (mechanizm ochronny).
"""
import asyncio

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.codes import generate_code, verify_code
from src.domain.transactions import finalize_transaction
from src.models.auth_code import AuthCodeStatus
from src.models.user import User


@pytest.mark.asyncio
class TestRaceCondition:
    async def test_sequential_double_finalize_protection(
        self, session: AsyncSession, user: User
    ):
        """
        Symulacja wyścigu: oba verify mogą przejść (odczyt bez blokady),
        ale tylko jeden finalize może się powieść — drugi dostaje 'już wykorzystany'.
        """
        code, _auth_code = await generate_code(session, user)

        # Oba verify zwrócą token (odczyt without FOR UPDATE)
        token1, *_ = await verify_code(session, code, 100.0, "terminal-001")
        token2, *_ = await verify_code(session, code, 100.0, "terminal-002")

        # Pierwszy finalize — sukces
        tx1 = await finalize_transaction(session, token1)
        assert tx1 is not None

        # Drugi finalize tego samego kodu — blokada
        with pytest.raises(ValueError, match="już wykorzystany"):
            await finalize_transaction(session, token2)

    async def test_code_status_after_race(
        self, session: AsyncSession, user: User
    ):
        """Po wyścigu status kodu = WYKORZYSTANY (nie AKTYWNY)."""
        code, auth_code = await generate_code(session, user)
        token, *_ = await verify_code(session, code, 100.0, "terminal-dev")
        await finalize_transaction(session, token)

        await session.refresh(auth_code)
        assert auth_code.status == AuthCodeStatus.WYKORZYSTANY

    async def test_balance_not_double_deducted(
        self, session: AsyncSession, user: User
    ):
        """Saldo nie jest odjęte dwa razy po wyścigu."""
        balance_before = float(user.current_balance)
        code, _ = await generate_code(session, user)
        token1, *_ = await verify_code(session, code, 100.0, "terminal-001")
        token2, *_ = await verify_code(session, code, 100.0, "terminal-002")

        await finalize_transaction(session, token1)
        try:
            await finalize_transaction(session, token2)
        except ValueError:
            pass

        await session.refresh(user)
        # Saldo odjęte tylko raz (20 PLN = 20% z 100)
        assert float(user.current_balance) == balance_before - 20.0

    async def test_sequential_codes_work(
        self, session: AsyncSession, user: User
    ):
        """Dwa kody wygenerowane sekwencyjnie (po 30 min karencji) działają niezależnie."""
        code1, _ = await generate_code(session, user)
        # Resetuj cooldown
        user.last_code_generated_at = None
        await session.flush()
        code2, _ = await generate_code(session, user)

        # Oba kody muszą być różne
        assert code1 != code2
