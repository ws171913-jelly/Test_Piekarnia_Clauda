import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class HrEventType(str, enum.Enum):
    NOWY_PRACOWNIK = "NOWY_PRACOWNIK"
    ZMIANA_KOSZYKA = "ZMIANA_KOSZYKA"
    DOLADOWANIE = "DOLADOWANIE"
    KONIEC_OKRESU = "KONIEC_OKRESU"
    DEZAKTYWACJA = "DEZAKTYWACJA"
    RESET_PIN = "RESET_PIN"


class HrEventStatus(str, enum.Enum):
    OCZEKUJACE = "OCZEKUJACE"
    PRZETWORZONE = "PRZETWORZONE"
    BLAD = "BLAD"


class HrEvent(Base):
    __tablename__ = "hr_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type: Mapped[HrEventType] = mapped_column(Enum(HrEventType), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[HrEventStatus] = mapped_column(
        Enum(HrEventStatus), nullable=False, default=HrEventStatus.OCZEKUJACE
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
