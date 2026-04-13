"""
T054 — Test integracyjny: zwrot w oknie 48h i po przekroczeniu okna.
"""
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.codes import generate_code, verify_code
from src.domain.transactions import REFUND_WINDOW_HOURS, finalize_transaction, process_refund
from src.models.transaction import TransactionType
from src.models.user import User


@pytest.mark.asyncio
class TestRefundWindow:
    async def _setup_purchase(
        self, session: AsyncSession, user: User, amount: float = 100.0
    ):
        code, _ = await generate_code(session, user)
        token, *_ = await verify_code(session, code, amount, "terminal-dev")
        return await finalize_transaction(session, token)

    async def test_refund_within_window_succeeds(
        self, session: AsyncSession, user: User
    ):
        """Zwrot w ciągu 48h — powinien się powieść."""
        tx = await self._setup_purchase(session, user)
        refund = await process_refund(session, user, tx.id, "terminal-dev")
        assert refund.type == TransactionType.ZWROT

    async def test_refund_restores_balance(
        self, session: AsyncSession, user: User
    ):
        """Po zwrocie saldo wraca do wartości sprzed zakupu."""
        balance_before = float(user.current_balance)
        tx = await self._setup_purchase(session, user, 100.0)
        discount = float(tx.discount_amount_pln)

        await session.refresh(user)
        balance_after_purchase = float(user.current_balance)

        await process_refund(session, user, tx.id, "terminal-dev")
        await session.refresh(user)
        assert float(user.current_balance) == balance_after_purchase + discount

    async def test_refund_outside_window_raises(
        self, session: AsyncSession, user: User
    ):
        """Zwrot po 48h → ValueError."""
        tx = await self._setup_purchase(session, user)

        # Cofnij czas created_at o 49h
        tx.created_at = datetime.now(timezone.utc) - timedelta(hours=REFUND_WINDOW_HOURS + 1)
        await session.flush()

        with pytest.raises(ValueError, match="48h"):
            await process_refund(session, user, tx.id, "terminal-dev")

    async def test_refund_window_constant_is_48h(self):
        """Stała REFUND_WINDOW_HOURS = 48."""
        assert REFUND_WINDOW_HOURS == 48

    async def test_refund_amount_matches_original_discount(
        self, session: AsyncSession, user: User
    ):
        """Kwota zwrotu = kwota rabatu z zakupu."""
        tx = await self._setup_purchase(session, user, 100.0)
        original_discount = float(tx.discount_amount_pln)

        refund = await process_refund(session, user, tx.id, "terminal-dev")
        assert float(refund.discount_amount_pln) == original_discount

    async def test_refund_not_found_for_another_user(
        self,
        session: AsyncSession,
        user: User,
        user_zero_balance: User,
    ):
        """Zwrot transakcji innego użytkownika → LookupError."""
        # Nadaj saldo drugiemu userowi, żeby mógł kupić
        user_zero_balance.current_balance = 100.0  # type: ignore[assignment]
        await session.flush()

        tx = await self._setup_purchase(session, user, 50.0)

        # Drugi user próbuje zwrócić transakcję pierwszego
        with pytest.raises(LookupError):
            await process_refund(session, user_zero_balance, tx.id, "terminal-dev")

    async def test_refund_record_has_original_transaction_id(
        self, session: AsyncSession, user: User
    ):
        """Rekord zwrotu zawiera original_transaction_id."""
        tx = await self._setup_purchase(session, user)
        refund = await process_refund(session, user, tx.id, "terminal-dev")
        assert refund.original_transaction_id == tx.id
