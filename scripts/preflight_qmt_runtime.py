#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime_preflight import run_preflight  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate QMT dry-run runtime configuration.")
    parser.add_argument(
        "--paper-admission",
        action="store_true",
        help="Validate the offline paper-admission contract without calling QMT or creating orders.",
    )
    args = parser.parse_args(argv)

    report = run_preflight(paper_admission=args.paper_admission)
    print(json.dumps(report.to_payload(), ensure_ascii=False, indent=2))
    return 0 if report.status == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
