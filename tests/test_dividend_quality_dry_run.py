from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from cn_equity_strategies.catalog import CN_DIVIDEND_QUALITY_SNAPSHOT_PROFILE
from runtime_config_support import PlatformRuntimeSettings


def _pipelines_root() -> Path:
    repo_root = Path(__file__).resolve().parents[1]
    for candidate in (
        repo_root.parent / "CnEquitySnapshotPipelines",
        repo_root / "external" / "CnEquitySnapshotPipelines",
    ):
        if candidate.exists():
            return candidate
    raise FileNotFoundError("CnEquitySnapshotPipelines checkout not found")


@pytest.fixture
def dividend_snapshot_paths(tmp_path) -> dict[str, str]:
    pipelines_root = _pipelines_root()
    sample_factor = pipelines_root / "examples" / "dividend_quality" / "factor_snapshot.sample.csv"
    output_dir = tmp_path / "dividend_quality"
    as_of = datetime.now(timezone.utc).date().isoformat()
    subprocess.run(
        [
            sys.executable,
            "-m",
            "cn_equity_snapshot_pipelines.dividend_quality",
            "--factor-snapshot",
            str(sample_factor),
            "--output-dir",
            str(output_dir),
            "--as-of",
            as_of,
        ],
        check=True,
    )
    snapshot = output_dir / "cn_dividend_quality_snapshot_factor_snapshot_latest.csv"
    manifest = output_dir / "cn_dividend_quality_snapshot_factor_snapshot_latest.csv.manifest.json"
    return {
        "snapshot": str(snapshot),
        "manifest": str(manifest),
    }


def test_dividend_quality_dry_run_cycle_returns_target_weights(dividend_snapshot_paths: dict[str, str]):
    from application.dry_run_service import run_dry_run_cycle
    from application.qmt_client import QmtBrokerClient

    settings = PlatformRuntimeSettings(
        strategy_profile=CN_DIVIDEND_QUALITY_SNAPSHOT_PROFILE,
        strategy_display_name="CN Dividend Quality Snapshot",
        strategy_domain="cn_equity",
        dry_run_only=True,
        market_history_path=None,
        feature_snapshot_path=dividend_snapshot_paths["snapshot"],
        feature_snapshot_manifest_path=dividend_snapshot_paths["manifest"],
    )
    report = run_dry_run_cycle(runtime_settings=settings, client=QmtBrokerClient())
    assert report["status"] == "ok"
    assert report["strategy_profile"] == CN_DIVIDEND_QUALITY_SNAPSHOT_PROFILE
    assert report["target_weights"]
    assert report["order_previews"]
    assert report["diagnostics"].get("actionable") is True


def test_committed_dividend_fixture_dry_run_if_fresh():
    root = Path(__file__).resolve().parents[1]
    snapshot = root / "data/fixtures/dividend_quality/cn_dividend_quality_snapshot_factor_snapshot_latest.csv"
    manifest = root / "data/fixtures/dividend_quality/cn_dividend_quality_snapshot_factor_snapshot_latest.csv.manifest.json"
    if not snapshot.exists() or not manifest.exists():
        pytest.skip("committed dividend fixtures are not present")
    import pandas as pd

    frame = pd.read_csv(snapshot)
    if "as_of" not in frame.columns:
        pytest.skip("committed dividend fixture missing as_of column")
    as_of = pd.to_datetime(frame["as_of"].iloc[0], errors="coerce")
    if pd.isna(as_of):
        pytest.skip("committed dividend fixture has invalid as_of")
    month_lag = (datetime.now(timezone.utc).year - as_of.year) * 12 + (datetime.now(timezone.utc).month - as_of.month)
    if month_lag > 1:
        pytest.skip("committed dividend fixture is stale; run scripts/build_fixtures.py")

    from application.dry_run_service import run_dry_run_cycle
    from application.qmt_client import QmtBrokerClient
    from runtime_config_support import PlatformRuntimeSettings

    settings = PlatformRuntimeSettings(
        strategy_profile=CN_DIVIDEND_QUALITY_SNAPSHOT_PROFILE,
        strategy_display_name="CN Dividend Quality Snapshot",
        strategy_domain="cn_equity",
        dry_run_only=True,
        market_history_path=None,
        feature_snapshot_path=str(snapshot),
        feature_snapshot_manifest_path=str(manifest),
    )
    report = run_dry_run_cycle(runtime_settings=settings, client=QmtBrokerClient())
    assert report["target_weights"]
