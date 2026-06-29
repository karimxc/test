"""
Unit tests for service layer business logic.
Run with: pytest tests/
"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from app.models.currency import Currency
from app.models.stock import CurrencyStock
from app.models.exchange_rate import ExchangeRate
from app.models.transaction import OperationType
from app.schemas.currency import CurrencyCreate, CurrencyUpdate
from app.schemas.exchange_rate import ExchangeRateCreate, ExchangeRateUpdate
from app.schemas.transaction import TransactionCreate
from app.core.exceptions import (
    CurrencyNotFoundError,
    DuplicateCurrencyError,
    InsufficientStockError,
    ExchangeRateNotFoundError,
)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def make_currency(code="USD", name="US Dollar", is_active=True):
    c = Currency()
    c.code = code
    c.name = name
    c.is_active = is_active
    return c


def make_stock(currency_code="USD", balance=Decimal("10000")):
    s = CurrencyStock()
    s.currency_code = currency_code
    s.balance = balance
    return s


def make_rate(from_code="USD", to_code="TND", rate=Decimal("3.12")):
    r = ExchangeRate()
    r.id = "test-id"
    r.from_currency_code = from_code
    r.to_currency_code = to_code
    r.rate = rate
    return r


# ─── Currency Service ─────────────────────────────────────────────────────────

class TestCurrencyService:

    def test_get_by_code_raises_if_not_found(self):
        from app.services.currency_service import CurrencyService
        db = MagicMock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = None
        svc = CurrencyService(db)
        with pytest.raises(CurrencyNotFoundError):
            svc.get_by_code("XYZ")

    def test_create_raises_on_duplicate(self):
        from app.services.currency_service import CurrencyService
        db = MagicMock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = make_currency("USD")
        svc = CurrencyService(db)
        with pytest.raises(DuplicateCurrencyError):
            svc.create(CurrencyCreate(code="USD", name="US Dollar"))


# ─── Stock Service ────────────────────────────────────────────────────────────

class TestStockService:

    def test_withdraw_raises_on_insufficient_stock(self):
        from app.services.stock_service import StockService
        db = MagicMock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = make_stock(balance=Decimal("100"))
        svc = StockService(db)
        with pytest.raises(InsufficientStockError):
            svc.withdraw("USD", Decimal("9999"))

    def test_deposit_increases_balance(self):
        from app.services.stock_service import StockService
        stock = make_stock(balance=Decimal("1000"))
        db = MagicMock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = stock
        svc = StockService(db)
        result = svc.deposit("USD", Decimal("500"))
        assert result.balance == Decimal("1500")

    def test_withdraw_reduces_balance(self):
        from app.services.stock_service import StockService
        stock = make_stock(balance=Decimal("1000"))
        db = MagicMock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = stock
        svc = StockService(db)
        result = svc.withdraw("USD", Decimal("300"))
        assert result.balance == Decimal("700")


# ─── Exchange Rate Service ────────────────────────────────────────────────────

class TestExchangeRateService:

    def test_get_rate_raises_if_not_found(self):
        from app.services.exchange_rate_service import ExchangeRateService
        db = MagicMock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = None
        svc = ExchangeRateService(db)
        with pytest.raises(ExchangeRateNotFoundError):
            svc.get_rate("USD", "XYZ")

    def test_get_rate_value_returns_decimal(self):
        from app.services.exchange_rate_service import ExchangeRateService
        rate = make_rate(rate=Decimal("3.12"))
        db = MagicMock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = rate
        svc = ExchangeRateService(db)
        val = svc.get_rate_value("USD", "TND")
        assert val == Decimal("3.12")


# ─── Pydantic Schema Validation ───────────────────────────────────────────────

class TestSchemas:

    def test_currency_code_uppercased(self):
        c = CurrencyCreate(code="usd", name="US Dollar")
        assert c.code == "USD"

    def test_currency_code_rejects_numbers(self):
        with pytest.raises(Exception):
            CurrencyCreate(code="U5D", name="Bad")

    def test_exchange_rate_rejects_zero(self):
        from app.schemas.exchange_rate import ExchangeRateCreate
        with pytest.raises(Exception):
            ExchangeRateCreate(from_currency_code="USD", to_currency_code="TND", rate=Decimal("0"))

    def test_transaction_rejects_negative_amount(self):
        with pytest.raises(Exception):
            TransactionCreate(
                from_currency_code="USD",
                to_currency_code="TND",
                amount=Decimal("-100"),
                operation_type=OperationType.BUY,
            )
