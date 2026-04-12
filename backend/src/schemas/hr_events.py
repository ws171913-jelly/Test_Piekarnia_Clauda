import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from src.models.hr_event import HrEventType


class HrEventPayload(BaseModel):
    """Wspólne pola opcjonalne payload — różne typy zdarzeń wymagają różnych pól."""
    hr_employee_id: str | None = None
    hr_basket_id: str | None = None
    basket_name: str | None = None
    discount_pct: float | None = None
    monthly_limit_pln: float | None = None
    amount_pln: Decimal | None = None
    expiry_date: date | None = None
    location_id: str | None = None


class HrEventRequest(BaseModel):
    event_type: HrEventType
    payload: HrEventPayload


class HrEventResponse(BaseModel):
    event_id: uuid.UUID
    status: str
    temp_pin: str | None = Field(default=None, description="Zwracany tylko dla NOWY_PRACOWNIK i RESET_PIN")
