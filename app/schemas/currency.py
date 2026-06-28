from pydantic import BaseModel, field_validator


class CurrencyCreate(BaseModel):
    code: str
    name: str
    is_active: bool = True

    @field_validator("code")
    @classmethod
    def code_must_be_uppercase(cls, v: str) -> str:
        v = v.strip().upper()
        if not v.isalpha() or len(v) > 10:
            raise ValueError("Currency code must be alphabetic and at most 10 characters.")
        return v

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Currency name must not be empty.")
        return v


class CurrencyUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None


class CurrencyResponse(BaseModel):
    code: str
    name: str
    is_active: bool

    model_config = {"from_attributes": True}
