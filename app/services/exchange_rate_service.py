import uuid
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.exchange_rate import ExchangeRate
from app.schemas.exchange_rate import ExchangeRateCreate, ExchangeRateUpdate
from app.core.exceptions import ExchangeRateNotFoundError


class ExchangeRateService:

    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> list[ExchangeRate]:
        return self.db.query(ExchangeRate).all()

    def get_rate(self, from_code: str, to_code: str) -> ExchangeRate:
        rate = self.db.query(ExchangeRate).filter(
            ExchangeRate.from_currency_code == from_code.upper(),
            ExchangeRate.to_currency_code == to_code.upper(),
        ).first()
        if not rate:
            raise ExchangeRateNotFoundError(from_code, to_code)
        return rate

    def get_rate_value(self, from_code: str, to_code: str) -> Decimal:
        rate = self.get_rate(from_code, to_code)
        return Decimal(str(rate.rate))

    def create_or_update(self, data: ExchangeRateCreate) -> ExchangeRate:
        existing = self.db.query(ExchangeRate).filter(
            ExchangeRate.from_currency_code == data.from_currency_code,
            ExchangeRate.to_currency_code == data.to_currency_code,
        ).first()

        if existing:
            existing.rate = data.rate
            self.db.commit()
            self.db.refresh(existing)
            return existing

        rate = ExchangeRate(
            id=str(uuid.uuid4()),
            from_currency_code=data.from_currency_code,
            to_currency_code=data.to_currency_code,
            rate=data.rate,
        )
        self.db.add(rate)
        self.db.commit()
        self.db.refresh(rate)
        return rate

    def update(self, from_code: str, to_code: str, data: ExchangeRateUpdate) -> ExchangeRate:
        rate = self.get_rate(from_code, to_code)
        rate.rate = data.rate
        self.db.commit()
        self.db.refresh(rate)
        return rate

    def delete(self, from_code: str, to_code: str) -> None:
        rate = self.get_rate(from_code, to_code)
        self.db.delete(rate)
        self.db.commit()
