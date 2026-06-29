"""
Seed script — populates the database with initial currencies, stock balances, and exchange rates.
Safe to run multiple times — skips existing data.
Run with: python seed.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.db.session import SessionLocal
from app.models.currency import Currency
from app.services.currency_service import CurrencyService
from app.services.stock_service import StockService
from app.services.exchange_rate_service import ExchangeRateService
from app.schemas.currency import CurrencyCreate
from app.schemas.exchange_rate import ExchangeRateCreate
from decimal import Decimal


CURRENCIES = [
    {"code": "USD", "name": "US Dollar"},
    {"code": "EUR", "name": "Euro"},
    {"code": "TND", "name": "Tunisian Dinar"},
    {"code": "GBP", "name": "British Pound"},
    {"code": "MAD", "name": "Moroccan Dirham"},
]

INITIAL_STOCK = {
    "USD": Decimal("15000"),
    "EUR": Decimal("8300"),
    "TND": Decimal("42000"),
    "GBP": Decimal("5000"),
    "MAD": Decimal("20000"),
}

RATES = [
    ("USD", "TND", "2.9100"),
    ("TND", "USD", "0.3436"),
    ("EUR", "TND", "3.3700"),
    ("TND", "EUR", "0.2967"),
    ("USD", "EUR", "0.8710"),
    ("EUR", "USD", "1.1480"),
    ("GBP", "TND", "3.9500"),
    ("TND", "GBP", "0.2532"),
    ("USD", "MAD", "9.3100"),
    ("MAD", "USD", "0.1074"),
    ("EUR", "GBP", "0.8450"),
    ("GBP", "EUR", "1.1834"),
]


def seed():
    db = SessionLocal()
    try:
        # Check if already seeded
        existing = db.query(Currency).count()
        if existing > 0:
            print(f"Database already has {existing} currencies — skipping seed.")
            return

        currency_svc = CurrencyService(db)
        stock_svc = StockService(db)
        rate_svc = ExchangeRateService(db)

        print("Seeding currencies...")
        for c in CURRENCIES:
            try:
                currency_svc.create(CurrencyCreate(**c))
                print(f"  Created: {c['code']}")
            except Exception as e:
                print(f"  Skipped {c['code']}: {e}")

        print("\nSeeding stock balances...")
        for code, amount in INITIAL_STOCK.items():
            try:
                stock_svc.deposit(code, amount)
                db.commit()
                print(f"  {code}: +{amount}")
            except Exception as e:
                db.rollback()
                print(f"  Skipped {code}: {e}")

        print("\nSeeding exchange rates...")
        for from_code, to_code, rate in RATES:
            try:
                rate_svc.create_or_update(ExchangeRateCreate(
                    from_currency_code=from_code,
                    to_currency_code=to_code,
                    rate=Decimal(rate),
                ))
                print(f"  {from_code} → {to_code}: {rate}")
            except Exception as e:
                print(f"  Skipped {from_code}/{to_code}: {e}")

        print("\nSeed complete.")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
