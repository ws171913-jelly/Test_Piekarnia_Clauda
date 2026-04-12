"""Initial schema — all tables

Revision ID: 001
Revises:
Create Date: 2026-04-12
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "baskets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("hr_basket_id", sa.String(64), unique=True, nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("discount_pct", sa.Numeric(5, 2), nullable=False),
        sa.Column("monthly_limit_pln", sa.Numeric(10, 2), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("discount_pct > 0 AND discount_pct <= 100", name="ck_basket_discount_pct"),
    )

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("hr_employee_id", sa.String(64), unique=True, nullable=False),
        sa.Column("basket_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("baskets.id"), nullable=False),
        sa.Column("pin_hash", sa.String(128), nullable=False),
        sa.Column("must_change_pin", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("login_attempts", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_jti", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("current_balance", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("balance_expiry_date", sa.Date(), nullable=False),
        sa.Column("last_code_generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("location_id", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("current_balance >= 0", name="ck_user_balance_nonneg"),
    )

    op.create_table(
        "transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("code_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("pos_terminal_id", sa.String(64), nullable=False),
        sa.Column("pos_transaction_ref", sa.String(128), nullable=True),
        sa.Column("type", sa.Enum("ZAKUP", "ZWROT", name="transactiontype"), nullable=False),
        sa.Column("gross_amount_pln", sa.Numeric(10, 2), nullable=False),
        sa.Column("discount_pct_snapshot", sa.Numeric(5, 2), nullable=False),
        sa.Column("discount_amount_pln", sa.Numeric(10, 2), nullable=False),
        sa.Column("net_amount_pln", sa.Numeric(10, 2), nullable=False),
        sa.Column("basket_snapshot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("baskets.id"), nullable=False),
        sa.Column("balance_before_pln", sa.Numeric(10, 2), nullable=False),
        sa.Column("balance_after_pln", sa.Numeric(10, 2), nullable=False),
        sa.Column("original_transaction_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("transactions.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("gross_amount_pln > 0", name="ck_tx_gross_positive"),
        sa.CheckConstraint("discount_amount_pln >= 0", name="ck_tx_discount_nonneg"),
    )

    op.create_table(
        "auth_codes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("code_hash", sa.String(128), nullable=False),
        sa.Column("status", sa.Enum("AKTYWNY", "WYKORZYSTANY", "WYGASLY", name="authcodestatus"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("transaction_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("transactions.id"), nullable=True),
    )

    op.create_table(
        "hr_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_type", sa.Enum("NOWY_PRACOWNIK", "ZMIANA_KOSZYKA", "DOLADOWANIE", "KONIEC_OKRESU", "DEZAKTYWACJA", "RESET_PIN", name="hreventtype"), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.Enum("OCZEKUJACE", "PRZETWORZONE", "BLAD", name="hreventstatus"), nullable=False, server_default="OCZEKUJACE"),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
    )

    # Indexes
    op.create_index("ix_auth_codes_user_status", "auth_codes", ["user_id", "status"])
    op.create_index("ix_auth_codes_expires_at", "auth_codes", ["expires_at"])
    op.create_index("ix_transactions_user_created", "transactions", ["user_id", sa.text("created_at DESC")])
    op.create_index("ix_hr_events_status_received", "hr_events", ["status", "received_at"])


def downgrade() -> None:
    op.drop_table("auth_codes")
    op.drop_table("hr_events")
    op.drop_table("transactions")
    op.drop_table("users")
    op.drop_table("baskets")
    op.execute("DROP TYPE IF EXISTS transactiontype")
    op.execute("DROP TYPE IF EXISTS authcodestatus")
    op.execute("DROP TYPE IF EXISTS hreventtype")
    op.execute("DROP TYPE IF EXISTS hreventstatus")
