import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hr_employee_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    basket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("baskets.id"), nullable=False
    )
    pin_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    must_change_pin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    login_attempts: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_jti: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    current_balance: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    balance_expiry_date: Mapped[date] = mapped_column(Date, nullable=False)
    last_code_generated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    location_id: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    basket: Mapped["Basket"] = relationship("Basket", back_populates="users")  # type: ignore[name-defined]
    auth_codes: Mapped[list["AuthCode"]] = relationship("AuthCode", back_populates="user")  # type: ignore[name-defined]
    transactions: Mapped[list["Transaction"]] = relationship("Transaction", back_populates="user")  # type: ignore[name-defined]

    __table_args__ = (
        CheckConstraint("current_balance >= 0", name="ck_user_balance_nonneg"),
    )
