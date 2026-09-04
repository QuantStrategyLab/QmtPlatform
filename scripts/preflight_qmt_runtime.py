#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime_preflight import run_preflight, validate_e3_receipt  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate QMT dry-run runtime configuration.")
    parser.add_argument(
        "--paper-admission",
        action="store_true",
        help="Validate the offline paper-admission contract without calling QMT or creating orders.",
    )
    parser.add_argument(
        "--e3-receipt",
        type=Path,
        help="Validate a local, sanitized E3 receipt without connecting to QMT or creating orders.",
    )
    args = parser.parse_args(argv)

    report = run_preflight(paper_admission=args.paper_admission)
    payload = report.to_payload()
    receipt_status = "ok"
    if args.e3_receipt:
        receipt_status = "error"
        try:
            receipt = json.loads(args.e3_receipt.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            receipt = None
        receipt_report = validate_e3_receipt(receipt)
        payload["e3_receipt"] = receipt_report.to_payload()
        receipt_status = receipt_report.status

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if report.status == "ok" and receipt_status == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
