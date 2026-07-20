#!/usr/bin/env python3
"""Regenerate committed QMT dry-run fixtures."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "data" / "fixtures"
MARKET_HISTORY = FIXTURES / "market_history.sample.csv"


def _build_market_history(path: Path, *, use_akshare: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if use_akshare:
        from cn_equity_snapshot_pipelines.akshare_market_history import write_market_history_csv

        write_market_history_csv(output_path=path)
        return

    from cn_equity_strategies.strategies.cn_industry_etf_rotation import extract_managed_symbols

    dates = pd.bdate_range("2024-01-02", periods=320)
    rates = {
        "159819": 1.0010,
        "159995": 1.0009,
        "512760": 1.0008,
        "159994": 1.0007,
        "159852": 1.0006,
        "512170": 1.0004,
        "515030": 1.0009,
        "159792": 1.0005,
        "512800": 1.0003,
        "512690": 1.0002,
        "159928": 1.0001,
        "159915": 0.9998,
        "588000": 1.0000,
        "512100": 1.0003,
    }
    rows: list[dict[str, object]] = []
    for symbol in extract_managed_symbols():
        price = 20.0
        for idx, date in enumerate(dates):
            price *= rates.get(symbol, 1.0004)
            close = price * (1.0 + 0.04 * ((idx % 5) - 2) / 5)
            rows.append({"date": date, "symbol": symbol, "close": close, "volume": 1_000_000.0})
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--use-akshare",
        action="store_true",
        help="Fetch real ETF market history via AkShare when available.",
    )
    args = parser.parse_args(argv)

    _build_market_history(MARKET_HISTORY, use_akshare=args.use_akshare)
    print(f"market_history={MARKET_HISTORY}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
