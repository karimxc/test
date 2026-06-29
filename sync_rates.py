"""
sync_rates.py — Fetch live exchange rates from Frankfurter (ECB data, no API key)
and sync them into the Currency Exchange backend.

Usage:
    python sync_rates.py                    # sync once
    python sync_rates.py --watch            # sync every 24h in a loop
    python sync_rates.py --dry-run          # print rates without posting

Frankfurter: https://api.frankfurter.dev — free, no key, ECB daily rates.
"""

import argparse
import time
import sys
import requests
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────────────────────────────

FRANKFURTER_URL = "https://api.frankfurter.dev/v2/latest"

# Your backend URL
BACKEND_URL = "http://localhost:8000/api/v1"

# Currency pairs to sync — from_currency → list of to_currencies
# Frankfurter uses EUR as native base; we fetch multiple bases via separate calls.
PAIRS_TO_SYNC = {
    "USD": ["TND", "EUR", "GBP", "MAD", "JPY", "CHF"],
    "EUR": ["TND", "USD", "GBP", "MAD"],
    "GBP": ["TND", "USD", "EUR"],
    "TND": ["USD", "EUR", "GBP"],
    "MAD": ["USD", "EUR", "TND"],
}

# ── FETCH ──────────────────────────────────────────────────────────────────────

def fetch_rates(base: str, targets: list[str]) -> dict[str, float]:
    """Fetch rates for a single base currency from Frankfurter."""
    quotes = ",".join(targets)
    url = f"{FRANKFURTER_URL}?base={base}&quotes={quotes}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("rates", {})
    except requests.RequestException as e:
        print(f"  [WARN] Failed to fetch {base} rates: {e}")
        return {}


def fetch_all_rates() -> list[tuple[str, str, float]]:
    """Fetch all configured pairs. Returns list of (from, to, rate)."""
    results = []
    for base, targets in PAIRS_TO_SYNC.items():
        print(f"  Fetching {base} → {', '.join(targets)} ...")
        rates = fetch_rates(base, targets)
        for target, rate in rates.items():
            if target in targets:
                results.append((base, target, float(rate)))
    return results


# ── ENSURE CURRENCIES EXIST ───────────────────────────────────────────────────

CURRENCY_NAMES = {
    "USD": "US Dollar",
    "EUR": "Euro",
    "TND": "Tunisian Dinar",
    "GBP": "British Pound",
    "MAD": "Moroccan Dirham",
    "JPY": "Japanese Yen",
    "CHF": "Swiss Franc",
}

def ensure_currencies(dry_run: bool = False):
    """Make sure all currencies exist in the backend before posting rates."""
    all_codes = set()
    for base, targets in PAIRS_TO_SYNC.items():
        all_codes.add(base)
        all_codes.update(targets)

    for code in sorted(all_codes):
        if dry_run:
            print(f"  [DRY] Would ensure currency: {code}")
            continue
        try:
            resp = requests.get(f"{BACKEND_URL}/currencies/{code}", timeout=5)
            if resp.status_code == 404:
                name = CURRENCY_NAMES.get(code, code)
                create = requests.post(
                    f"{BACKEND_URL}/currencies/",
                    json={"code": code, "name": name},
                    timeout=5,
                )
                if create.status_code == 201:
                    print(f"  Created currency: {code} ({name})")
                else:
                    print(f"  [WARN] Could not create {code}: {create.text}")
        except requests.RequestException as e:
            print(f"  [WARN] Could not check currency {code}: {e}")


# ── POST RATES ─────────────────────────────────────────────────────────────────

def post_rates(pairs: list[tuple[str, str, float]], dry_run: bool = False):
    """Post fetched rates to the backend."""
    ok = 0
    fail = 0
    for from_code, to_code, rate in pairs:
        if dry_run:
            print(f"  [DRY] {from_code} → {to_code}: {rate:.6f}")
            continue
        try:
            resp = requests.post(
                f"{BACKEND_URL}/rates/",
                json={
                    "from_currency_code": from_code,
                    "to_currency_code": to_code,
                    "rate": rate,
                },
                timeout=5,
            )
            if resp.status_code in (200, 201):
                print(f"  ✓  {from_code} → {to_code}: {rate:.6f}")
                ok += 1
            else:
                print(f"  ✗  {from_code} → {to_code}: {resp.status_code} {resp.text}")
                fail += 1
        except requests.RequestException as e:
            print(f"  ✗  {from_code} → {to_code}: {e}")
            fail += 1
    return ok, fail


# ── MAIN ───────────────────────────────────────────────────────────────────────

def sync(dry_run: bool = False):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'─'*52}")
    print(f"  FX Rate Sync — {now}")
    print(f"  Source : api.frankfurter.dev (ECB daily rates)")
    print(f"  Target : {BACKEND_URL}")
    print(f"{'─'*52}")

    print("\n[1/3] Ensuring currencies exist ...")
    ensure_currencies(dry_run)

    print("\n[2/3] Fetching live rates from Frankfurter ...")
    pairs = fetch_all_rates()

    if not pairs:
        print("  No rates fetched. Check your internet connection.")
        return

    print(f"\n[3/3] Posting {len(pairs)} rates to backend ...")
    ok, fail = post_rates(pairs, dry_run)

    print(f"\n  Done — {ok} updated, {fail} failed.")
    print(f"{'─'*52}\n")


def main():
    parser = argparse.ArgumentParser(description="Sync live FX rates into the backend.")
    parser.add_argument("--watch", action="store_true", help="Repeat every 24 hours")
    parser.add_argument("--dry-run", action="store_true", help="Print without posting")
    parser.add_argument("--interval", type=int, default=86400, help="Watch interval in seconds (default: 86400 = 24h)")
    args = parser.parse_args()

    if args.watch:
        print(f"Watch mode: syncing every {args.interval // 3600}h. Press Ctrl+C to stop.")
        while True:
            sync(dry_run=args.dry_run)
            print(f"  Next sync in {args.interval // 3600}h...")
            time.sleep(args.interval)
    else:
        sync(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
