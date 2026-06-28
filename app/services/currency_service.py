from sqlalchemy.orm import Session
from app.models.currency import Currency
from app.models.stock import CurrencyStock
from app.schemas.currency import CurrencyCreate, CurrencyUpdate
from app.core.exceptions import CurrencyNotFoundError, DuplicateCurrencyError


class CurrencyService:

    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> list[Currency]:
        return self.db.query(Currency).all()

    def get_by_code(self, code: str) -> Currency:
        currency = self.db.query(Currency).filter(Currency.code == code.upper()).first()
        if not currency:
            raise CurrencyNotFoundError(code)
        return currency

    def create(self, data: CurrencyCreate) -> Currency:
        existing = self.db.query(Currency).filter(Currency.code == data.code).first()
        if existing:
            raise DuplicateCurrencyError(data.code)

        currency = Currency(code=data.code, name=data.name, is_active=data.is_active)
        self.db.add(currency)

        # Automatically create a zero-balance stock entry
        stock = CurrencyStock(currency_code=data.code, balance=0)
        self.db.add(stock)

        self.db.commit()
        self.db.refresh(currency)
        return currency

    def update(self, code: str, data: CurrencyUpdate) -> Currency:
        currency = self.get_by_code(code)
        if data.name is not None:
            currency.name = data.name
        if data.is_active is not None:
            currency.is_active = data.is_active
        self.db.commit()
        self.db.refresh(currency)
        return currency

    def delete(self, code: str) -> None:
        currency = self.get_by_code(code)
        self.db.delete(currency)
        self.db.commit()
