import uuid
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.transaction import Transaction, OperationType
from app.schemas.transaction import TransactionCreate
from app.services.stock_service import StockService
from app.services.exchange_rate_service import ExchangeRateService
from app.core.exceptions import (
    CurrencyInactiveError,
    CurrencyNotFoundError,
    InsufficientStockError,
    ExchangeRateNotFoundError,
)


class TransactionService:

    def __init__(self, db: Session):
        self.db = db
        self.stock_service = StockService(db)
        self.rate_service = ExchangeRateService(db)

    def get_all(self, limit: int = 50, offset: int = 0) -> list[Transaction]:
        return (
            self.db.query(Transaction)
            .order_by(Transaction.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_by_id(self, transaction_id: str) -> Transaction:
        tx = self.db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not tx:
            raise ValueError(f"Transaction '{transaction_id}' not found.")
        return tx

    def get_today(self) -> list[Transaction]:
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        return (
            self.db.query(Transaction)
            .filter(Transaction.created_at >= today_start)
            .order_by(Transaction.created_at.desc())
            .all()
        )

    def execute(self, data: TransactionCreate) -> Transaction:
        """
        Execute a BUY or SELL operation.

        BUY  → client pays from_currency, receives to_currency.
               Deduct from_currency stock, add to_currency stock.
        SELL → client gives to_currency, receives from_currency.
               Add from_currency stock, deduct to_currency stock.
        """
        try:
            # 1. Validate both currencies exist and are active
            from app.models.currency import Currency
            for code in [data.from_currency_code, data.to_currency_code]:
                currency = self.db.query(Currency).filter(Currency.code == code).first()
                if not currency:
                    raise CurrencyNotFoundError(code)
                if not currency.is_active:
                    raise CurrencyInactiveError(code)

            # 2. Fetch rate — raises ExchangeRateNotFoundError if missing
            rate_value = self.rate_service.get_rate_value(
                data.from_currency_code, data.to_currency_code
            )
            converted_amount = Decimal(str(data.amount)) * rate_value

            # 3. Update stock atomically
            if data.operation_type == OperationType.BUY:
                self.stock_service.withdraw(data.from_currency_code, Decimal(str(data.amount)))
                self.stock_service.deposit(data.to_currency_code, converted_amount)
            else:
                self.stock_service.deposit(data.from_currency_code, Decimal(str(data.amount)))
                self.stock_service.withdraw(data.to_currency_code, converted_amount)

            # 4. Record the transaction
            transaction = Transaction(
                id=str(uuid.uuid4()),
                from_currency_code=data.from_currency_code,
                to_currency_code=data.to_currency_code,
                amount=Decimal(str(data.amount)),
                converted_amount=converted_amount,
                rate=rate_value,
                operation_type=data.operation_type,
            )
            self.db.add(transaction)
            self.db.commit()
            self.db.refresh(transaction)
            return transaction

        except (
            CurrencyNotFoundError,
            CurrencyInactiveError,
            InsufficientStockError,
            ExchangeRateNotFoundError,
        ):
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise RuntimeError(f"Transaction failed: {str(e)}") from e
