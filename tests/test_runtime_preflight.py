from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from runtime_preflight import (
    E3_RECEIPT_MAX_FRESHNESS_SECONDS,
    E3_RECEIPT_SCHEMA_VERSION,
    run_preflight,
    validate_e3_receipt,
)
from scripts.preflight_qmt_runtime import main


def _issue_codes(report) -> set[str]:
    return {issue.code for issue in report.issues}


def _sha256(path: str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _valid_e3_receipt() -> dict[str, object]:
    return {
        "schema_version": E3_RECEIPT_SCHEMA_VERSION,
        "as_of": "2026-09-05T00:00:00+00:00",
        "freshness_seconds": 60,
        "no_order": True,
        "verify_only": True,
        "summary_counts": {
            "accounts": 1,
            "positions": 0,
            "orders": 0,
            "fills": 0,
            "cash": 1,
            "ledger": 1,
        },
    }


def test_preflight_accepts_primary_dry_run_config(monkeypatch, market_history_csv: str):
    monkeypatch.setenv("STRATEGY_PROFILE", "cn_industry_etf_rotation")
    monkeypatch.setenv("QMT_DRY_RUN_ONLY", "true")
    monkeypatch.setenv("QMT_MARKET_HISTORY_PATH", market_history_csv)
    monkeypatch.delenv("RUNTIME_TARGET_JSON", raising=False)

    report = run_preflight()

    assert report.status == "ok"
    assert report.strategy_profile == "cn_industry_etf_rotation"
    assert report.dry_run_only is True
    assert report.required_inputs == ("market_history",)
    assert report.issues == ()


def test_preflight_requires_market_history_for_direct_profile(monkeypatch):
    monkeypatch.setenv("STRATEGY_PROFILE", "cn_industry_etf_rotation")
    monkeypatch.setenv("QMT_DRY_RUN_ONLY", "true")
    monkeypatch.delenv("QMT_MARKET_HISTORY_PATH", raising=False)
    monkeypatch.delenv("RUNTIME_TARGET_JSON", raising=False)

    report = run_preflight()

    assert report.status == "error"
    assert _issue_codes(report) == {"missing_market_history"}


def test_preflight_blocks_non_dry_run_config(monkeypatch, market_history_csv: str):
    monkeypatch.setenv("STRATEGY_PROFILE", "cn_industry_etf_rotation")
    monkeypatch.setenv("QMT_DRY_RUN_ONLY", "false")
    monkeypatch.setenv("QMT_MARKET_HISTORY_PATH", market_history_csv)
    monkeypatch.delenv("RUNTIME_TARGET_JSON", raising=False)

    report = run_preflight()

    assert report.status == "error"
    assert _issue_codes(report) == {"non_dry_run_blocked"}


def test_paper_admission_requires_paper_mode_and_a_frozen_input_digest(monkeypatch, market_history_csv: str):
    monkeypatch.setenv("STRATEGY_PROFILE", "cn_industry_etf_rotation")
    monkeypatch.setenv("QMT_DRY_RUN_ONLY", "true")
    monkeypatch.setenv("QMT_EXECUTION_MODE", "paper")
    monkeypatch.setenv("QMT_MARKET_HISTORY_PATH", market_history_csv)
    monkeypatch.setenv(
        "QMT_PAPER_ADMISSION_INPUT_SHA256",
        _sha256(market_history_csv),
    )
    monkeypatch.delenv("RUNTIME_TARGET_JSON", raising=False)

    report = run_preflight(paper_admission=True)

    assert report.status == "ok"
    assert report.dry_run_only is True
    assert report.execution_mode == "paper"
    assert report.paper_admission is True
    assert report.to_payload() == run_preflight(paper_admission=True).to_payload()


def test_paper_admission_rejects_live_mode_and_non_dry_run(monkeypatch, market_history_csv: str):
    monkeypatch.setenv("STRATEGY_PROFILE", "cn_industry_etf_rotation")
    monkeypatch.setenv("QMT_DRY_RUN_ONLY", "false")
    monkeypatch.setenv("QMT_EXECUTION_MODE", "live")
    monkeypatch.setenv("QMT_MARKET_HISTORY_PATH", market_history_csv)
    monkeypatch.setenv("QMT_PAPER_ADMISSION_INPUT_SHA256", "0" * 64)
    monkeypatch.delenv("RUNTIME_TARGET_JSON", raising=False)

    report = run_preflight(paper_admission=True)

    assert report.status == "error"
    assert _issue_codes(report) == {
        "non_dry_run_blocked",
        "paper_admission_dry_run_required",
        "paper_admission_mode_required",
        "paper_admission_input_digest_mismatch",
    }


def test_paper_admission_rejects_an_unfrozen_input(monkeypatch, market_history_csv: str):
    monkeypatch.setenv("STRATEGY_PROFILE", "cn_industry_etf_rotation")
    monkeypatch.setenv("QMT_DRY_RUN_ONLY", "true")
    monkeypatch.setenv("QMT_EXECUTION_MODE", "paper")
    monkeypatch.setenv("QMT_MARKET_HISTORY_PATH", market_history_csv)
    monkeypatch.setenv("QMT_PAPER_ADMISSION_INPUT_SHA256", "0" * 64)
    monkeypatch.delenv("RUNTIME_TARGET_JSON", raising=False)

    report = run_preflight(paper_admission=True)

    assert report.status == "error"
    assert _issue_codes(report) == {"paper_admission_input_digest_mismatch"}


def test_preflight_cli_has_no_non_dry_run_bypass():
    with pytest.raises(SystemExit) as exc_info:
        main(["--allow-non-dry-run"])

    assert exc_info.value.code == 2


def test_preflight_cli_runs_offline_paper_admission(monkeypatch, market_history_csv: str):
    monkeypatch.setenv("STRATEGY_PROFILE", "cn_industry_etf_rotation")
    monkeypatch.setenv("QMT_DRY_RUN_ONLY", "true")
    monkeypatch.setenv("QMT_EXECUTION_MODE", "paper")
    monkeypatch.setenv("QMT_MARKET_HISTORY_PATH", market_history_csv)
    monkeypatch.setenv("QMT_PAPER_ADMISSION_INPUT_SHA256", _sha256(market_history_csv))
    monkeypatch.delenv("RUNTIME_TARGET_JSON", raising=False)

    assert main(["--paper-admission"]) == 0


def test_preflight_rejects_research_only_dividend_profile(monkeypatch):
    monkeypatch.setenv("STRATEGY_PROFILE", "cn_dividend_quality_snapshot")
    monkeypatch.setenv("QMT_DRY_RUN_ONLY", "true")
    monkeypatch.delenv("RUNTIME_TARGET_JSON", raising=False)

    report = run_preflight()

    assert report.status == "error"
    assert _issue_codes(report) == {"runtime_config_error"}


def test_e3_receipt_validator_accepts_complete_sanitized_receipt():
    report = validate_e3_receipt(
        _valid_e3_receipt(),
        now=datetime(2026, 9, 5, 0, 0, 30, tzinfo=timezone.utc),
    )

    assert report.status == "ok"
    assert report.schema_version == E3_RECEIPT_SCHEMA_VERSION
    assert report.issues == ()
    assert report.to_payload() == {
        "status": "ok",
        "schema_version": E3_RECEIPT_SCHEMA_VERSION,
        "required_summary_counts": ["accounts", "positions", "orders", "fills", "cash", "ledger"],
        "issues": [],
    }


@pytest.mark.parametrize(
    ("field", "value", "expected_code"),
    [
        ("summary_counts", {"accounts": 1}, "invalid_summary_counts"),
        ("as_of", "not-a-timestamp", "invalid_as_of"),
        ("freshness_seconds", -1, "invalid_freshness"),
        ("freshness_seconds", E3_RECEIPT_MAX_FRESHNESS_SECONDS + 1, "invalid_freshness"),
        ("no_order", False, "no_order_required"),
        ("verify_only", False, "verify_only_required"),
    ],
)
def test_e3_receipt_validator_fails_closed_for_missing_or_unsafe_fields(field, value, expected_code):
    receipt = _valid_e3_receipt()
    receipt[field] = value

    report = validate_e3_receipt(receipt, now=datetime(2026, 9, 5, tzinfo=timezone.utc))

    assert report.status == "error"
    assert expected_code in _issue_codes(report)


def test_e3_receipt_validator_fails_closed_for_stale_or_detail_bearing_receipts():
    stale_report = validate_e3_receipt(
        _valid_e3_receipt(),
        now=datetime(2026, 9, 5, 0, 6, tzinfo=timezone.utc),
    )
    detail_receipt = _valid_e3_receipt()
    detail_receipt["account"] = {"id": "must-not-be-accepted"}
    detail_report = validate_e3_receipt(detail_receipt, now=datetime(2026, 9, 5, tzinfo=timezone.utc))

    assert _issue_codes(stale_report) == {"stale_receipt"}
    assert _issue_codes(detail_report) == {"unexpected_receipt_fields"}
    assert "must-not-be-accepted" not in str(detail_report.to_payload())


def test_e3_receipt_validator_fails_closed_for_missing_required_fields():
    receipt = _valid_e3_receipt()
    receipt.pop("verify_only")

    report = validate_e3_receipt(receipt, now=datetime(2026, 9, 5, tzinfo=timezone.utc))

    assert _issue_codes(report) == {"missing_receipt_fields", "verify_only_required"}


def test_preflight_cli_validates_e3_receipt_offline(monkeypatch, market_history_csv: str, tmp_path, capsys):
    monkeypatch.setenv("STRATEGY_PROFILE", "cn_industry_etf_rotation")
    monkeypatch.setenv("QMT_DRY_RUN_ONLY", "true")
    monkeypatch.setenv("QMT_MARKET_HISTORY_PATH", market_history_csv)
    monkeypatch.delenv("RUNTIME_TARGET_JSON", raising=False)
    receipt_path = tmp_path / "e3-receipt.json"
    receipt = _valid_e3_receipt()
    receipt["as_of"] = datetime.now(timezone.utc).isoformat()
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    assert main(["--e3-receipt", str(receipt_path)]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["e3_receipt"]["status"] == "ok"
