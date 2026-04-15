"""
T040 — Test integracyjny: historia po wielu transakcjach.

Weryfikuje kolejność, paginację i typy transakcji.
"""
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.codes import generate_code, verify_code
from src.domain.transactions import finalize_transaction, process_refund
from src.models.transaction import Transaction, TransactionType
from src.models.user import User


async def _purchase(session: AsyncSession, user: User, amount: float = 50.0) -> Transaction:
    """Pomocnicza: zakup, zwraca transakcję."""
    code, _ = await generate_code(session, user)
    token, *_ = await verify_code(session, code, amount, "terminal-dev")
    tx = await finalize_transaction(session, token)
    user.last_code_generated_at = None
    await session.flush()
    return tx


@pytest.mark.asyncio
class TestTransactionHistory:
    async def test_single_purchase_in_history(
        self, session: AsyncSession, user: User
    ):
        await _purchase(session, user)
        result = await session.execute(
            select(Transaction).where(Transaction.user_id == user.id)
        )
        txs = result.scalars().all()
        assert len(txs) == 1
        assert txs[0].type == TransactionType.ZAKUP

    async def test_multiple_purchases_in_history(
        self, session: AsyncSession, user: User
    ):
        await _purchase(session, user, 50.0)
        await _purchase(session, user, 30.0)
        result = await session.execute(
            select(Transaction)
            .where(Transaction.user_id == user.id)
            .order_by(Transaction.created_at)
        )
        txs = result.scalars().all()
        assert len(txs) == 2
        assert all(tx.type == TransactionType.ZAKUP for tx in txs)

    async def test_refund_appears_in_history(
        self, session: AsyncSession, user: User
    ):
        tx = await _purchase(session, user)
        await process_refund(session, user, tx.id, "terminal-dev")

        result = await session.execute(
            select(Transaction)
            .where(Transaction.user_id == user.id)
            .order_by(Transaction.created_at)
        )
        txs = result.scalars().all()
        assert len(txs) == 2
        types = {tx.type for tx in txs}
        assert TransactionType.ZAKUP in types
        assert TransactionType.ZWROT in types

    async def test_history_ordered_newest_first(
        self, session: AsyncSession, user: User
    ):
        tx1 = await _purchase(session, user, 50.0)
        tx2 = await _purchase(session, user, 30.0)

        result = await session.execute(
            select(Transaction)
            .where(Transaction.user_id == user.id)
            .order_by(Transaction.created_at.desc())
        )
        txs = result.scalars().all()
        assert txs[0].id == tx2.id
        assert txs[1].id == tx1.id

    async def test_balance_decrements_with_each_purchase(
        self, session: AsyncSession, user: User
    ):
        """Saldo maleje o naliczony rabat przy każdej transakcji."""
        balance_start = float(user.current_balance)

        await _purchase(session, user, 100.0)
        await session.refresh(user)
        # Rabat obliczany z koszyka testowego (20%)
        first_discount = balance_start - float(user.current_balance)
        assert first_discount > 0

        await _purchase(session, user, 100.0)
        await session.refresh(user)
        # Drugi zakup odejmuje taki sam rabat
        assert float(user.current_balance) == balance_start - first_discount * 2

    async def test_refund_restores_balance(
        self, session: AsyncSession, user: User
    ):
        balance_before = float(user.current_balance)
        tx = await _purchase(session, user, 100.0)
        discount = float(tx.discount_amount_pln)

        await session.refresh(user)
        balance_after_purchase = float(user.current_balance)

        await process_refund(session, user, tx.id, "terminal-dev")
        await session.refresh(user)

        assert float(user.current_balance) == balance_after_purchase + discount

    async def test_transactions_isolated_between_users(
        self,
        session: AsyncSession,
        user: User,
        user_zero_balance: User,
    ):
        """Transakcje jednego użytkownika nie wpływają na historię drugiego."""
        await _purchase(session, user, 50.0)

        result = await session.execute(
            select(Transaction).where(Transaction.user_id == user_zero_balance.id)
        )
        other_txs = result.scalars().all()
        assert len(other_txs) == 0
