import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.models.auth_code import AuthCode, AuthCodeStatus
from src.models.transaction import Transaction, TransactionType
from src.models.user import User

REFUND_WINDOW_HOURS = 48


async def finalize_transaction(
    session: AsyncSession,
    verification_token: str,
    pos_transaction_ref: str | None = None,
) -> Transaction:
    """
    Atomowa finalizacja transakcji: UPDATE salda + INSERT transaction + zmiana statusu kodu.

    Raises:
        ValueError: nieważny token weryfikacji, kod już użyty, niewystarczające saldo
    """
    try:
        payload = jwt.decode(
            verification_token, settings.secret_key, algorithms=[settings.jwt_algorithm]
        )
    except JWTError:
        raise ValueError("Nieważny lub wygasły token weryfikacji")

    user_id = uuid.UUID(payload["sub"])
    code_id = uuid.UUID(payload["code_id"])
    discount_amount = float(payload["discount_amount"])
    discount_pct = float(payload["discount_pct"])
    gross_amount = float(payload["gross_amount"])
    net_amount = float(payload["net_amount"])
    pos_terminal_id = payload["pos_terminal_id"]
    ref = pos_transaction_ref or payload.get("pos_transaction_ref")

    # Pobierz użytkownika z blokadą wiersza
    result = await session.execute(
        select(User).where(User.id == user_id).with_for_update()
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise ValueError("Nie znaleziono pracownika")

    # Pobierz kod z blokadą
    code_result = await session.execute(
        select(AuthCode).where(AuthCode.id == code_id).with_for_update()
    )
    code = code_result.scalar_one_or_none()
    if code is None or code.status != AuthCodeStatus.AKTYWNY:
        raise ValueError("Kod został już wykorzystany lub wygasł")

    now = datetime.now(timezone.utc)
    if code.expires_at.replace(tzinfo=timezone.utc) < now:
        code.status = AuthCodeStatus.WYGASLY
        await session.commit()
        raise ValueError("Kod wygasł")

    balance_before = float(user.current_balance)
    if balance_before < discount_amount:
        discount_amount = balance_before

    balance_after = balance_before - discount_amount

    transaction = Transaction(
        user_id=user_id,
        code_id=code_id,
        pos_terminal_id=pos_terminal_id,
        pos_transaction_ref=ref,
        type=TransactionType.ZAKUP,
        gross_amount_pln=gross_amount,
        discount_pct_snapshot=discount_pct,
        discount_amount_pln=discount_amount,
        net_amount_pln=gross_amount - discount_amount,
        basket_snapshot_id=user.basket_id,
        balance_before_pln=balance_before,
        balance_after_pln=balance_after,
    )
    session.add(transaction)
    await session.flush()  # uzyskaj ID transakcji

    user.current_balance = balance_after  # type: ignore[assignment]
    code.status = AuthCodeStatus.WYKORZYSTANY
    code.used_at = now
    code.transaction_id = transaction.id

    await session.commit()
    await session.refresh(transaction)
    return transaction


async def process_refund(
    session: AsyncSession,
    user: User,
    original_transaction_id: uuid.UUID,
    pos_terminal_id: str,
    pos_transaction_ref: str | None = None,
) -> Transaction:
    """
    Zwrot w oknie 48h — uznanie rabatu na saldo pracownika.

    Raises:
        ValueError: poza oknem zwrotu, nie znaleziono transakcji
    """
    result = await session.execute(
        select(Transaction)
        .where(Transaction.id == original_transaction_id)
        .where(Transaction.user_id == user.id)
        .where(Transaction.type == TransactionType.ZAKUP)
        .with_for_update()
    )
    orig = result.scalar_one_or_none()
    if orig is None:
        raise LookupError("Nie znaleziono transakcji zakupu dla tego pracownika")

    now = datetime.now(timezone.utc)
    created_at = orig.created_at.replace(tzinfo=timezone.utc)
    if now - created_at > timedelta(hours=REFUND_WINDOW_HOURS):
        raise ValueError(
            "Zwrot niemożliwy — przekroczono okno 48h. Skontaktuj się z HR/finansami."
        )

    # Pobierz użytkownika z blokadą
    user_result = await session.execute(
        select(User).where(User.id == user.id).with_for_update()
    )
    locked_user = user_result.scalar_one()

    balance_before = float(locked_user.current_balance)
    refund_amount = float(orig.discount_amount_pln)
    balance_after = balance_before + refund_amount

    refund_tx = Transaction(
        user_id=user.id,
        code_id=orig.code_id,
        pos_terminal_id=pos_terminal_id,
        pos_transaction_ref=pos_transaction_ref,
        type=TransactionType.ZWROT,
        gross_amount_pln=orig.gross_amount_pln,
        discount_pct_snapshot=orig.discount_pct_snapshot,
        discount_amount_pln=refund_amount,
        net_amount_pln=orig.net_amount_pln,
        basket_snapshot_id=orig.basket_snapshot_id,
        balance_before_pln=balance_before,
        balance_after_pln=balance_after,
        original_transaction_id=original_transaction_id,
    )
    session.add(refund_tx)
    locked_user.current_balance = balance_after  # type: ignore[assignment]

    await session.commit()
    await session.refresh(refund_tx)
    return refund_tx
