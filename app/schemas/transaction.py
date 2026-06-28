from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, field_validator
from app.models.transaction import OperationType


class TransactionCreate(BaseModel):
    from_currency_code: str
    to_currency_code: str
    amount: Decimal
    operation_type: OperationType

    @field_validator("operation_type", mode="before")
    @classmethod
    def normalize_operation_type(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Transaction amount must be greater than zero.")
        return v

    @field_validator("from_currency_code", "to_currency_code")
    @classmethod
    def code_uppercase(cls, v: str) -> str:
        return v.strip().upper()


class TransactionResponse(BaseModel):
    id: str
    from_currency_code: str
    to_currency_code: str
    amount: Decimal
    converted_amount: Decimal
    rate: Decimal
    operation_type: OperationType
    created_at: datetime

    model_config = {"from_attributes": True}
