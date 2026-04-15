"""
T025 — Test integracyjny: pełny przebieg zakupu.

Scenariusz: generowanie → weryfikacja → finalizacja → weryfikacja salda.
"""
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.codes import generate_code, verify_code
from src.domain.transactions import finalize_transaction
from src.models.auth_code import AuthCode, AuthCodeStatus
from src.models.transaction import Transaction, TransactionType
from src.models.user import User


@pytest.mark.asyncio
class TestPurchaseFlow:
    async def test_full_purchase_flow(
        self, session: AsyncSession, user: User
    ):
        """Pełny przebieg: generowanie → weryfikacja → finalizacja."""
        balance_before = float(user.current_balance)
        gross_amount = 100.0

        # Krok 1: Generowanie kodu
        code, auth_code = await generate_code(session, user)
        assert len(code) == 6
        assert auth_code.status == AuthCodeStatus.AKTYWNY

        # Krok 2: Weryfikacja przez POS
        token, discount, _discount_pct, net, code_id = await verify_code(
            session, code, gross_amount, "terminal-dev"
        )
        assert discount == 20.0  # 20% z 100 PLN
        assert net == 80.0
        assert str(code_id) == str(auth_code.id)

        # Krok 3: Finalizacja
        tx = await finalize_transaction(session, token)
        assert tx.type == TransactionType.ZAKUP
        assert float(tx.discount_amount_pln) == 20.0
        assert float(tx.balance_after_pln) == balance_before - 20.0

        # Weryfikacja salda w bazie
        await session.refresh(user)
        assert float(user.current_balance) == balance_before - 20.0

    async def test_code_status_changes_to_used(
        self, session: AsyncSession, user: User
    ):
        """Po finalizacji status kodu = WYKORZYSTANY."""
        code, auth_code = await generate_code(session, user)
        token, *_ = await verify_code(session, code, 100.0, "terminal-dev")
        await finalize_transaction(session, token)

        await session.refresh(auth_code)
        assert auth_code.status == AuthCodeStatus.WYKORZYSTANY

    async def test_transaction_record_created(
        self, session: AsyncSession, user: User
    ):
        """Rekord transakcji istnieje w bazie po finalizacji."""
        code, _auth_code = await generate_code(session, user)
        token, *_ = await verify_code(session, code, 100.0, "terminal-dev")
        tx = await finalize_transaction(session, token)

        result = await session.execute(
            select(Transaction).where(Transaction.id == tx.id)
        )
        db_tx = result.scalar_one_or_none()
        assert db_tx is not None
        assert db_tx.user_id == user.id

    async def test_balance_capped_by_actual_balance(
        self, session: AsyncSession, user: User
    ):
        """
        Kwota zakupu = 10000 PLN, rabat 20% = 2000 PLN,
        ale saldo = 500 PLN → rabat = 500 PLN.
        """
        balance_before = float(user.current_balance)  # 500 PLN
        code, _ = await generate_code(session, user)
        token, discount, *_ = await verify_code(session, code, 10000.0, "terminal-dev")

        assert discount == balance_before  # ograniczony saldem

        tx = await finalize_transaction(session, token)
        await session.refresh(user)
        assert float(user.current_balance) == 0.0

    async def test_floor_rounding_in_discount(
        self, session: AsyncSession, user: User
    ):
        """99 PLN × 20% = 19.8 → floor = 19 PLN."""
        code, _ = await generate_code(session, user)
        token, discount, *_ = await verify_code(session, code, 99.0, "terminal-dev")
        # floor(99 * 20 / 100) = floor(19.8) = 19
        assert discount == 19.0

    async def test_last_code_generated_at_updated(
        self, session: AsyncSession, user: User
    ):
        """Po generowaniu kodu pole last_code_generated_at jest ustawione."""
        assert user.last_code_generated_at is None
        await generate_code(session, user)
        await session.refresh(user)
        assert user.last_code_generated_at is not None

    async def test_balance_immutable_after_failed_finalize(
        self, session: AsyncSession, user: User
    ):
        """Nieważny token nie modyfikuje salda."""
        balance_before = float(user.current_balance)
        with pytest.raises(ValueError, match="Nieważny|wygasły|token"):
            await finalize_transaction(session, "nieprawidlowy.token.jwt")
        await session.refresh(user)
        assert float(user.current_balance) == balance_before

    async def test_double_finalize_blocked(
        self, session: AsyncSession, user: User
    ):
        """Drugi finalize dla tego samego kodu → ValueError."""
        code, _ = await generate_code(session, user)
        token, *_ = await verify_code(session, code, 100.0, "terminal-dev")

        await finalize_transaction(session, token)

        with pytest.raises(ValueError, match="już wykorzystany"):
            await finalize_transaction(session, token)
