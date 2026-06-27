#!/usr/bin/env python3
"""End-to-end smoke: QMT dry-run for cn_industry_etf_rotation (conservative v1)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data" / "fixtures" / "market_history.sample.csv"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--market-history", default=str(FIXTURE))
    args = parser.parse_args(argv)

    if not Path(args.market_history).exists():
        raise SystemExit(f"missing market history fixture: {args.market_history}")

    os.environ["STRATEGY_PROFILE"] = "cn_industry_etf_rotation"
    os.environ["QMT_DRY_RUN_ONLY"] = "true"
    os.environ["QMT_MARKET_HISTORY_PATH"] = str(args.market_history)

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from application.dry_run_service import run_dry_run_cycle
    from runtime_config_support import load_platform_runtime_settings

    report = run_dry_run_cycle(runtime_settings=load_platform_runtime_settings())
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    if report.get("status") != "ok":
        return 1
    if not report.get("target_weights"):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
