"""Retired profiles remain readable but cannot be selected by the platform."""

import pytest

from cn_equity_strategies import get_platform_runtime_adapter, get_strategy_catalog
from strategy_loader import load_strategy_definition
from strategy_registry import get_supported_profiles_for_platform, resolve_strategy_definition


RETIRED_PROFILES = ('cn_industry_etf_rotation', 'cn_industry_etf_rotation_aggressive')


@pytest.mark.parametrize("profile", RETIRED_PROFILES)
def test_retired_profiles_are_not_selectable(profile):
    assert profile not in get_supported_profiles_for_platform("qmt")
    with pytest.raises(ValueError, match="Unsupported STRATEGY_PROFILE"):
        resolve_strategy_definition(profile, platform_id="qmt")
    with pytest.raises(ValueError, match="Unsupported STRATEGY_PROFILE"):
        load_strategy_definition(profile)


@pytest.mark.parametrize("profile", RETIRED_PROFILES)
def test_retired_profile_aliases_are_not_selectable(profile):
    catalog = get_strategy_catalog()
    for alias, canonical in catalog.profile_aliases.items():
        if canonical == profile:
            with pytest.raises(ValueError, match="Unsupported STRATEGY_PROFILE"):
                resolve_strategy_definition(alias, platform_id="qmt")


@pytest.mark.parametrize("profile", RETIRED_PROFILES)
def test_retired_profile_history_and_adapters_remain_available(profile):
    catalog = get_strategy_catalog()
    assert profile in catalog.definitions
    assert profile in catalog.metadata
    assert get_platform_runtime_adapter(profile, platform_id="qmt") is not None


@pytest.mark.parametrize("profile", RETIRED_PROFILES)
def test_preflight_rejects_retired_profiles(monkeypatch, profile):
    from runtime_preflight import run_preflight

    monkeypatch.setenv("STRATEGY_PROFILE", profile)
    monkeypatch.setenv("QMT_DRY_RUN_ONLY", "true")
    monkeypatch.delenv("RUNTIME_TARGET_JSON", raising=False)
    report = run_preflight()
    assert report.status == "error"
    assert {issue.code for issue in report.issues} == {"runtime_config_error"}
    assert "Unsupported STRATEGY_PROFILE" in report.issues[0].message
