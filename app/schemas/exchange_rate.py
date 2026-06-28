from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, field_validator


class ExchangeRateCreate(BaseModel):
    from_currency_code: str
    to_currency_code: str
    rate: Decimal

    @field_validator("rate")
    @classmethod
    def rate_must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Exchange rate must be greater than zero.")
        return v

    @field_validator("from_currency_code", "to_currency_code")
    @classmethod
    def code_uppercase(cls, v: str) -> str:
        return v.strip().upper()


class ExchangeRateUpdate(BaseModel):
    rate: Decimal

    @field_validator("rate")
    @classmethod
    def rate_must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Exchange rate must be greater than zero.")
        return v


class ExchangeRateResponse(BaseModel):
    id: str
    from_currency_code: str
    to_currency_code: str
    rate: Decimal
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
