from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.basket import Basket
    from src.models.user import User


class TransactionType(str, enum.Enum):
    ZAKUP = "ZAKUP"
    ZWROT = "ZWROT"


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    code_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("auth_codes.id"), nullable=False
    )
    pos_terminal_id: Mapped[str] = mapped_column(String(64), nullable=False)
    pos_transaction_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    type: Mapped[TransactionType] = mapped_column(Enum(TransactionType), nullable=False)
    gross_amount_pln: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    discount_pct_snapshot: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    discount_amount_pln: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    net_amount_pln: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    basket_snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("baskets.id"), nullable=False
    )
    balance_before_pln: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    balance_after_pln: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    original_transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.clock_timestamp()
    )

    user: Mapped[User] = relationship("User", back_populates="transactions")
    basket_snapshot: Mapped[Basket] = relationship("Basket", foreign_keys=[basket_snapshot_id])
    original_transaction: Mapped["Transaction | None"] = relationship(
        "Transaction", remote_side="Transaction.id", foreign_keys=[original_transaction_id]
    )

    __table_args__ = (
        CheckConstraint("gross_amount_pln > 0", name="ck_tx_gross_positive"),
        CheckConstraint("discount_amount_pln >= 0", name="ck_tx_discount_nonneg"),
    )
