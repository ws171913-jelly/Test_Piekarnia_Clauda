from fastapi import APIRouter, Query
from sqlalchemy import func, select

from src.api.deps import CurrentUser, DBSession
from src.models.transaction import Transaction
from src.schemas.users import (
    BasketInfo,
    TransactionHistoryResponse,
    TransactionListItem,
    UserProfileResponse,
)

router = APIRouter()


@router.get("/me", response_model=UserProfileResponse)
async def get_profile(current_user: CurrentUser, session: DBSession) -> UserProfileResponse:
    """Profil operacyjny pracownika — saldo, koszyk, data ważności."""
    from src.models.basket import Basket

    basket = await session.get(Basket, current_user.basket_id)
    if basket is None:
        raise LookupError("Nie znaleziono koszyka pracownika")

    return UserProfileResponse(
        hr_employee_id=current_user.hr_employee_id,
        current_balance=float(current_user.current_balance),
        balance_expiry_date=current_user.balance_expiry_date,
        basket=BasketInfo(
            id=basket.id,
            name=basket.name,
            discount_pct=float(basket.discount_pct),
            monthly_limit_pln=float(basket.monthly_limit_pln) if basket.monthly_limit_pln else None,
        ),
        location_id=current_user.location_id,
        must_change_pin=current_user.must_change_pin,
    )


@router.get("/me/transactions", response_model=TransactionHistoryResponse)
async def get_transaction_history(
    current_user: CurrentUser,
    session: DBSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type_filter: str | None = Query(None, alias="type"),
) -> TransactionHistoryResponse:
    """Historia transakcji paginowana z opcjonalnym filtrowaniem po typie."""
    query = select(Transaction).where(Transaction.user_id == current_user.id)

    if type_filter:
        query = query.where(Transaction.type == type_filter.upper())

    count_result = await session.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    query = query.order_by(Transaction.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await session.execute(query)
    transactions = result.scalars().all()

    items = [
        TransactionListItem(
            id=tx.id,
            type=tx.type.value,
            gross_amount_pln=float(tx.gross_amount_pln),
            discount_amount_pln=float(tx.discount_amount_pln),
            net_amount_pln=float(tx.net_amount_pln),
            discount_pct_snapshot=float(tx.discount_pct_snapshot),
            pos_terminal_id=tx.pos_terminal_id,
            created_at=tx.created_at,
        )
        for tx in transactions
    ]

    return TransactionHistoryResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )
