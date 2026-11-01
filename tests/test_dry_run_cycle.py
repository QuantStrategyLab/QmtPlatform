from __future__ import annotations

import pytest

from cn_equity_strategies.catalog import (
    CN_INDUSTRY_ETF_ROTATION_AGGRESSIVE_PROFILE,
    CN_INDUSTRY_ETF_ROTATION_PROFILE,
)
from runtime_config_support import PlatformRuntimeSettings, load_platform_runtime_settings
from strategy_registry import QMT_PLATFORM, PLATFORM_POLICY, get_enabled_profiles_for_platform


def test_qmt_enabled_profiles_are_empty_after_retirement():
    assert get_enabled_profiles_for_platform(QMT_PLATFORM, policy=PLATFORM_POLICY) == frozenset()


@pytest.mark.parametrize("profile", [CN_INDUSTRY_ETF_ROTATION_PROFILE, CN_INDUSTRY_ETF_ROTATION_AGGRESSIVE_PROFILE])
def test_load_platform_runtime_settings_rejects_retired_profiles(monkeypatch, market_history_csv, profile):
    monkeypatch.setenv("STRATEGY_PROFILE", profile)
    monkeypatch.setenv("QMT_DRY_RUN_ONLY", "true")
    monkeypatch.setenv("QMT_MARKET_HISTORY_PATH", market_history_csv)
    monkeypatch.delenv("RUNTIME_TARGET_JSON", raising=False)
    with pytest.raises(ValueError, match="Unsupported STRATEGY_PROFILE"):
        load_platform_runtime_settings()


@pytest.mark.usefixtures("historical_strategy_policy")
def test_dry_run_cycle_fails_closed_on_concentrated_target(
    monkeypatch: pytest.MonkeyPatch,
    market_history_csv: str,
):
    monkeypatch.setenv("STRATEGY_PROFILE", CN_INDUSTRY_ETF_ROTATION_PROFILE)
    monkeypatch.setenv("QMT_DRY_RUN_ONLY", "true")
    monkeypatch.setenv("QMT_MARKET_HISTORY_PATH", market_history_csv)

    from application.dry_run_service import run_dry_run_cycle
    from application.qmt_client import QmtBrokerClient

    settings = PlatformRuntimeSettings(
        strategy_profile=CN_INDUSTRY_ETF_ROTATION_PROFILE,
        strategy_display_name="CN Industry ETF Rotation",
        strategy_domain="cn_equity",
        dry_run_only=True,
        market_history_path=market_history_csv,
        feature_snapshot_path=None,
        feature_snapshot_manifest_path=None,
    )
    report = run_dry_run_cycle(
        runtime_settings=settings,
        client=QmtBrokerClient(market_history_path=market_history_csv),
    )
    assert report["status"] == "ok"
    assert report["strategy_profile"] == CN_INDUSTRY_ETF_ROTATION_PROFILE
    assert report["target_weights"] == {}
    assert report["order_previews"] == []
    assert report["risk_flags"] == ["rejected:concentration"]
    assert report["diagnostics"]["risk_gate"] == "REJECT"
    assert report["dry_run_only"] is True


@pytest.mark.usefixtures("historical_strategy_policy")
def test_aggressive_industry_profile_fails_closed_on_concentration(
    monkeypatch: pytest.MonkeyPatch,
    market_history_csv: str,
):
    monkeypatch.setenv("STRATEGY_PROFILE", CN_INDUSTRY_ETF_ROTATION_AGGRESSIVE_PROFILE)
    monkeypatch.setenv("QMT_DRY_RUN_ONLY", "true")
    monkeypatch.setenv("QMT_MARKET_HISTORY_PATH", market_history_csv)

    from application.dry_run_service import run_dry_run_cycle
    from application.qmt_client import QmtBrokerClient

    settings = PlatformRuntimeSettings(
        strategy_profile=CN_INDUSTRY_ETF_ROTATION_AGGRESSIVE_PROFILE,
        strategy_display_name="CN Industry ETF Rotation Aggressive",
        strategy_domain="cn_equity",
        dry_run_only=True,
        market_history_path=market_history_csv,
        feature_snapshot_path=None,
        feature_snapshot_manifest_path=None,
    )
    report = run_dry_run_cycle(
        runtime_settings=settings,
        client=QmtBrokerClient(market_history_path=market_history_csv),
    )
    assert report["status"] == "ok"
    assert report["strategy_profile"] == CN_INDUSTRY_ETF_ROTATION_AGGRESSIVE_PROFILE
    assert report["target_weights"] == {}
    assert report["order_previews"] == []
    assert report["risk_flags"] == ["rejected:concentration"]
    assert report["diagnostics"]["risk_gate"] == "REJECT"
