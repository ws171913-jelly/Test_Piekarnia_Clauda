import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base


class AuthCodeStatus(str, enum.Enum):
    AKTYWNY = "AKTYWNY"
    WYKORZYSTANY = "WYKORZYSTANY"
    WYGASLY = "WYGASLY"


class AuthCode(Base):
    __tablename__ = "auth_codes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    code_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[AuthCodeStatus] = mapped_column(
        Enum(AuthCodeStatus), nullable=False, default=AuthCodeStatus.AKTYWNY
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=True
    )

    user: Mapped["User"] = relationship("User", back_populates="auth_codes")  # type: ignore[name-defined]
    transaction: Mapped["Transaction | None"] = relationship(  # type: ignore[name-defined]
        "Transaction", foreign_keys=[transaction_id]
    )
