from __future__ import annotations

import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
DIVIDEND_QUALITY_FIXTURES = ROOT / "data" / "fixtures" / "dividend_quality"
PATH_CASES = (
    (
        DIVIDEND_QUALITY_FIXTURES
        / "cn_dividend_quality_snapshot_factor_snapshot_latest.csv.manifest.json",
        "snapshot_path",
        "data/fixtures/dividend_quality/cn_dividend_quality_snapshot_factor_snapshot_latest.csv",
    ),
    (
        DIVIDEND_QUALITY_FIXTURES / "release_status_summary.json",
        "manifest_path",
        "data/fixtures/dividend_quality/"
        "cn_dividend_quality_snapshot_factor_snapshot_latest.csv.manifest.json",
    ),
    (
        DIVIDEND_QUALITY_FIXTURES / "release_status_summary.json",
        "ranking_path",
        "data/fixtures/dividend_quality/cn_dividend_quality_snapshot_ranking_latest.csv",
    ),
    (
        DIVIDEND_QUALITY_FIXTURES / "release_status_summary.json",
        "snapshot_path",
        "data/fixtures/dividend_quality/cn_dividend_quality_snapshot_factor_snapshot_latest.csv",
    ),
)


@pytest.mark.parametrize(("fixture", "field", "expected"), PATH_CASES)
def test_dividend_quality_fixture_paths_are_repository_relative(
    fixture: Path,
    field: str,
    expected: str,
) -> None:
    payload = json.loads(fixture.read_text(encoding="utf-8"))
    value = payload[field]

    assert value == expected
    assert not Path(value).is_absolute()
    target = (ROOT / value).resolve()
    target.relative_to(ROOT.resolve())
    assert target.is_file()
