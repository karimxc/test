from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.stock import CurrencyStock
from app.core.exceptions import CurrencyNotFoundError, InsufficientStockError


class StockService:

    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> list[CurrencyStock]:
        return self.db.query(CurrencyStock).all()

    def get_by_code(self, currency_code: str) -> CurrencyStock:
        stock = self.db.query(CurrencyStock).filter(
            CurrencyStock.currency_code == currency_code.upper()
        ).first()
        if not stock:
            raise CurrencyNotFoundError(currency_code)
        return stock

    def deposit(self, currency_code: str, amount: Decimal) -> CurrencyStock:
        stock = self.get_by_code(currency_code)
        stock.balance = Decimal(str(stock.balance)) + Decimal(str(amount))
        # Note: commit is handled by the caller (TransactionService)
        # so partial updates don't get committed on error
        self.db.flush()
        return stock

    def withdraw(self, currency_code: str, amount: Decimal) -> CurrencyStock:
        stock = self.get_by_code(currency_code)
        current = Decimal(str(stock.balance))
        amount = Decimal(str(amount))
        if current < amount:
            raise InsufficientStockError(currency_code, float(amount), float(current))
        stock.balance = current - amount
        self.db.flush()
        return stock
