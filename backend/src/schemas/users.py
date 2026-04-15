import uuid
from datetime import date, datetime

from pydantic import BaseModel


class BasketInfo(BaseModel):
    id: uuid.UUID
    name: str
    discount_pct: float
    monthly_limit_pln: float | None


class UserProfileResponse(BaseModel):
    hr_employee_id: str
    current_balance: float
    balance_expiry_date: date
    basket: BasketInfo
    location_id: str
    must_change_pin: bool


class TransactionListItem(BaseModel):
    id: uuid.UUID
    type: str
    gross_amount_pln: float
    discount_amount_pln: float
    net_amount_pln: float
    discount_pct_snapshot: float
    pos_terminal_id: str
    created_at: datetime


class TransactionHistoryResponse(BaseModel):
    items: list[TransactionListItem]
    total: int
    page: int
    page_size: int
