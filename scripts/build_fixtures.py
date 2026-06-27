#!/usr/bin/env python3
"""Regenerate committed QMT dry-run fixtures."""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "data" / "fixtures"
MARKET_HISTORY = FIXTURES / "market_history.sample.csv"
DIVIDEND_DIR = FIXTURES / "dividend_quality"
SAMPLE_FACTOR = (
    ROOT.parent / "CnEquitySnapshotPipelines" / "examples" / "dividend_quality" / "factor_snapshot.sample.csv"
)


def _build_market_history(path: Path, *, use_akshare: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if use_akshare:
        from cn_equity_snapshot_pipelines.akshare_market_history import write_market_history_csv

        write_market_history_csv(output_path=path)
        return

    from cn_equity_strategies.strategies.cn_index_etf_tactical_rotation import extract_managed_symbols

    dates = pd.bdate_range("2024-01-02", periods=320)
    rates = {
        "510300": 1.0002,
        "510500": 1.0001,
        "159915": 0.9998,
        "588000": 1.0000,
        "512100": 1.0003,
        "512170": 1.0004,
        "515030": 1.0009,
        "512760": 1.0008,
        "518880": 1.0005,
        "513100": 1.0007,
        "511880": 1.00001,
        "511260": 1.00002,
    }
    rows: list[dict[str, object]] = []
    for symbol in extract_managed_symbols():
        price = 20.0
        for idx, date in enumerate(dates):
            price *= rates[symbol]
            close = price * (1.0 + 0.04 * ((idx % 5) - 2) / 5)
            rows.append({"date": date, "symbol": symbol, "close": close})
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)


def _build_dividend_factor_csv(*, output_path: Path, as_of: str, use_akshare: bool, sample_factor: Path) -> Path:
    if use_akshare:
        from cn_equity_snapshot_pipelines.akshare_staging import write_staging_factor_snapshot

        write_staging_factor_snapshot(
            output_path=output_path,
            sample_fallback_path=sample_factor,
            as_of=as_of,
        )
        return output_path
    return sample_factor


def _build_dividend_snapshot(*, as_of: str, sample_factor: Path, output_dir: Path) -> None:
    command = [
        sys.executable,
        "-m",
        "cn_equity_snapshot_pipelines.dividend_quality",
        "--factor-snapshot",
        str(sample_factor),
        "--output-dir",
        str(output_dir),
        "--as-of",
        as_of,
    ]
    subprocess.run(command, check=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--as-of",
        default=datetime.now(timezone.utc).date().isoformat(),
        help="Snapshot as_of date for dividend quality fixture (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--sample-factor",
        type=Path,
        default=SAMPLE_FACTOR,
        help="Factor CSV used to build the dividend quality snapshot fixture.",
    )
    parser.add_argument(
        "--use-akshare",
        action="store_true",
        help="Fetch real ETF market history and dividend factor fields via AkShare when available.",
    )
    args = parser.parse_args(argv)

    _build_market_history(MARKET_HISTORY, use_akshare=args.use_akshare)
    if not args.sample_factor.exists() and not args.use_akshare:
        raise FileNotFoundError(f"sample factor CSV not found: {args.sample_factor}")
    factor_path = _build_dividend_factor_csv(
        output_path=FIXTURES / "staging" / "dividend_quality" / "factor_snapshot.latest.csv",
        as_of=args.as_of,
        use_akshare=args.use_akshare,
        sample_factor=args.sample_factor,
    )
    _build_dividend_snapshot(as_of=args.as_of, sample_factor=factor_path, output_dir=DIVIDEND_DIR)

    print(f"market_history={MARKET_HISTORY}")
    print(f"dividend_snapshot_dir={DIVIDEND_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
