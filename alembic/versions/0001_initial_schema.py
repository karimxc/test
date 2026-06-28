"""initial schema

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "currencies",
        sa.Column("code", sa.String(10), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )

    op.create_table(
        "currency_stocks",
        sa.Column("currency_code", sa.String(10), sa.ForeignKey("currencies.code", ondelete="CASCADE"), primary_key=True),
        sa.Column("balance", sa.Numeric(precision=18, scale=4), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_table(
        "exchange_rates",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("from_currency_code", sa.String(10), sa.ForeignKey("currencies.code"), nullable=False),
        sa.Column("to_currency_code", sa.String(10), sa.ForeignKey("currencies.code"), nullable=False),
        sa.Column("rate", sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint("from_currency_code", "to_currency_code", name="uq_exchange_rate_pair"),
    )

    op.create_table(
        "transactions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("from_currency_code", sa.String(10), sa.ForeignKey("currencies.code"), nullable=False),
        sa.Column("to_currency_code", sa.String(10), sa.ForeignKey("currencies.code"), nullable=False),
        sa.Column("amount", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("converted_amount", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("rate", sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column("operation_type", sa.Enum("buy", "sell", name="operationtype"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("transactions")
    op.drop_table("exchange_rates")
    op.drop_table("currency_stocks")
    op.drop_table("currencies")
    op.execute("DROP TYPE IF EXISTS operationtype")
