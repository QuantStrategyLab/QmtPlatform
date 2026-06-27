from __future__ import annotations

import pytest

from cn_equity_strategies.catalog import (
    CN_DIVIDEND_QUALITY_SNAPSHOT_PROFILE,
    CN_INDUSTRY_ETF_ROTATION_AGGRESSIVE_PROFILE,
    CN_INDUSTRY_ETF_ROTATION_PROFILE,
)
from runtime_config_support import PlatformRuntimeSettings, load_platform_runtime_settings
from strategy_registry import QMT_PLATFORM, PLATFORM_POLICY, get_enabled_profiles_for_platform


def test_qmt_enabled_profiles_include_primary_runtime_strategies():
    profiles = get_enabled_profiles_for_platform(QMT_PLATFORM, policy=PLATFORM_POLICY)
    assert CN_INDUSTRY_ETF_ROTATION_PROFILE in profiles
    assert CN_INDUSTRY_ETF_ROTATION_AGGRESSIVE_PROFILE in profiles
    assert CN_DIVIDEND_QUALITY_SNAPSHOT_PROFILE in profiles


def test_load_platform_runtime_settings_from_env(monkeypatch: pytest.MonkeyPatch, market_history_csv: str):
    monkeypatch.setenv("STRATEGY_PROFILE", CN_INDUSTRY_ETF_ROTATION_PROFILE)
    monkeypatch.setenv("QMT_DRY_RUN_ONLY", "true")
    monkeypatch.setenv("QMT_MARKET_HISTORY_PATH", market_history_csv)
    monkeypatch.delenv("RUNTIME_TARGET_JSON", raising=False)

    settings = load_platform_runtime_settings()
    assert settings.strategy_profile == CN_INDUSTRY_ETF_ROTATION_PROFILE
    assert settings.dry_run_only is True
    assert settings.market_history_path == market_history_csv


def test_dry_run_cycle_returns_target_weights(monkeypatch: pytest.MonkeyPatch, market_history_csv: str):
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
    assert report["target_weights"]
    assert report["order_previews"]
    assert report["dry_run_only"] is True


def test_dry_run_cycle_supports_aggressive_industry_profile(
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
    assert report["target_weights"]
