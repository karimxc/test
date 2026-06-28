from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, field_validator


class StockResponse(BaseModel):
    currency_code: str
    balance: Decimal
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class StockAdjust(BaseModel):
    amount: Decimal

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Amount must be greater than zero.")
        return v
