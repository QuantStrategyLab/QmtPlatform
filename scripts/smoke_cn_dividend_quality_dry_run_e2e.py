#!/usr/bin/env python3
"""Guard smoke: dividend quality is research-only and must not run in QMT runtime."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime_preflight import run_preflight  # noqa: E402


def main() -> int:
    os.environ["STRATEGY_PROFILE"] = "cn_dividend_quality_snapshot"
    os.environ["QMT_DRY_RUN_ONLY"] = "true"
    report = run_preflight()
    payload = report.to_payload()
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    codes = {issue["code"] for issue in payload["issues"]}
    return 0 if report.status == "error" and "runtime_config_error" in codes else 1


if __name__ == "__main__":
    raise SystemExit(main())
