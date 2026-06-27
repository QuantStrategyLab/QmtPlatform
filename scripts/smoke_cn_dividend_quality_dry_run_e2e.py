#!/usr/bin/env python3
"""End-to-end smoke: stage/build dividend snapshot and run QMT dry-run."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIPELINES_ROOT = ROOT.parent / "CnEquitySnapshotPipelines"
SAMPLE_FACTOR = PIPELINES_ROOT / "examples" / "dividend_quality" / "factor_snapshot.sample.csv"


def _run(command: list[str], *, cwd: Path | None = None) -> None:
    subprocess.run(command, check=True, cwd=cwd)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--use-akshare-staging", action="store_true")
    parser.add_argument("--as-of", default=datetime.now(timezone.utc).date().isoformat())
    args = parser.parse_args(argv)

    with tempfile.TemporaryDirectory(prefix="qmt-dividend-smoke-") as tmp:
        work = Path(tmp)
        factor_path = work / "factor_snapshot.csv"
        snapshot_dir = work / "snapshot"

        if args.use_akshare_staging:
            _run(
                [
                    sys.executable,
                    "-m",
                    "cn_equity_snapshot_pipelines.akshare_staging",
                    "--output",
                    str(factor_path),
                    "--sample-fallback",
                    str(SAMPLE_FACTOR),
                ]
            )
        else:
            factor_path.write_text(SAMPLE_FACTOR.read_text(encoding="utf-8"), encoding="utf-8")

        _run(
            [
                sys.executable,
                "-m",
                "cn_equity_snapshot_pipelines.dividend_quality",
                "--factor-snapshot",
                str(factor_path),
                "--output-dir",
                str(snapshot_dir),
                "--as-of",
                args.as_of,
            ]
        )

        snapshot = snapshot_dir / "cn_dividend_quality_snapshot_factor_snapshot_latest.csv"
        manifest = snapshot_dir / "cn_dividend_quality_snapshot_factor_snapshot_latest.csv.manifest.json"
        os.environ["STRATEGY_PROFILE"] = "cn_dividend_quality_snapshot"
        os.environ["QMT_DRY_RUN_ONLY"] = "true"
        os.environ["QMT_FEATURE_SNAPSHOT_PATH"] = str(snapshot)
        os.environ["QMT_FEATURE_SNAPSHOT_MANIFEST_PATH"] = str(manifest)

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
