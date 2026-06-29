"""
app/core/rate_scheduler.py

Background task that fetches live FX rates from Frankfurter (ECB, no API key)
and upserts them into the database every 24 hours.
Runs automatically when the FastAPI app starts.
"""

import logging
from decimal import Decimal
import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.schemas.exchange_rate import ExchangeRateCreate
from app.services.exchange_rate_service import ExchangeRateService
from app.services.currency_service import CurrencyService
from app.schemas.currency import CurrencyCreate

logger = logging.getLogger("rate_scheduler")

FRANKFURTER_URL = "https://api.frankfurter.dev/v2/latest"

# Currency pairs to keep live
SYNC_PAIRS: dict[str, list[str]] = {
    "USD": ["TND", "EUR", "GBP", "MAD"],
    "EUR": ["TND", "USD", "GBP", "MAD"],
    "GBP": ["TND", "USD", "EUR"],
    "TND": ["USD", "EUR", "GBP"],
    "MAD": ["USD", "EUR", "TND"],
}

CURRENCY_NAMES = {
    "USD": "US Dollar",
    "EUR": "Euro",
    "TND": "Tunisian Dinar",
    "GBP": "British Pound",
    "MAD": "Moroccan Dirham",
}


async def _fetch_rates_for_base(client: httpx.AsyncClient, base: str, targets: list[str]) -> dict[str, float]:
    quotes = ",".join(targets)
    try:
        resp = await client.get(
            FRANKFURTER_URL,
            params={"base": base, "quotes": quotes},
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("rates", {})
    except Exception as e:
        logger.warning(f"Failed to fetch rates for base {base}: {e}")
        return {}


def _ensure_currency(db: Session, code: str):
    svc = CurrencyService(db)
    try:
        svc.get_by_code(code)
    except Exception:
        try:
            svc.create(CurrencyCreate(code=code, name=CURRENCY_NAMES.get(code, code)))
            logger.info(f"Auto-created currency: {code}")
        except Exception:
            pass  # already exists or constraint error


async def sync_rates_from_frankfurter():
    """Fetch live rates and upsert into DB. Called on startup and every 24h."""
    logger.info("Starting FX rate sync from api.frankfurter.dev ...")
    db: Session = SessionLocal()
    rate_svc = ExchangeRateService(db)
    updated = 0

    try:
        async with httpx.AsyncClient() as client:
            for base, targets in SYNC_PAIRS.items():
                rates = await _fetch_rates_for_base(client, base, targets)
                for target, rate in rates.items():
                    if target not in targets:
                        continue
                    # Ensure both currencies exist
                    _ensure_currency(db, base)
                    _ensure_currency(db, target)
                    try:
                        rate_svc.create_or_update(ExchangeRateCreate(
                            from_currency_code=base,
                            to_currency_code=target,
                            rate=Decimal(str(rate)),
                        ))
                        updated += 1
                    except Exception as e:
                        logger.warning(f"Could not upsert rate {base}/{target}: {e}")

        logger.info(f"FX rate sync complete — {updated} rates updated.")
    except Exception as e:
        logger.error(f"FX rate sync failed: {e}")
    finally:
        db.close()


_scheduler = AsyncIOScheduler()


def start_rate_scheduler():
    """Register and start the background scheduler."""
    # Sync immediately on startup, then every 24 hours
    _scheduler.add_job(
        sync_rates_from_frankfurter,
        trigger="interval",
        hours=24,
        id="fx_rate_sync",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("Rate scheduler started — syncing every 24h.")


def stop_rate_scheduler():
    _scheduler.shutdown(wait=False)
