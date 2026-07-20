from __future__ import annotations

from runtime_preflight import run_preflight


def _issue_codes(report) -> set[str]:
    return {issue.code for issue in report.issues}


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


def test_preflight_rejects_research_only_dividend_profile(monkeypatch):
    monkeypatch.setenv("STRATEGY_PROFILE", "cn_dividend_quality_snapshot")
    monkeypatch.setenv("QMT_DRY_RUN_ONLY", "true")
    monkeypatch.delenv("RUNTIME_TARGET_JSON", raising=False)

    report = run_preflight()

    assert report.status == "error"
    assert _issue_codes(report) == {"runtime_config_error"}
