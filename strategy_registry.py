from __future__ import annotations

from quant_platform_kit.common.strategies import (
    PlatformCapabilityMatrix,
    PlatformStrategyPolicy,
    StrategyDefinition,
    StrategyMetadata,
    build_platform_profile_matrix,
    build_platform_profile_status_matrix,
    derive_enabled_profiles_for_platform,
    derive_eligible_profiles_for_platform,
    get_catalog_strategy_metadata,
    get_enabled_profiles_for_platform,
    resolve_platform_strategy_definition,
)
from cn_equity_strategies import (
    CN_EQUITY_DOMAIN,
    get_platform_runtime_adapter,
    get_qmt_rollout_allowlist,
    get_runtime_enabled_profiles,
    get_strategy_catalog,
)

QMT_PLATFORM = "qmt"

PLATFORM_SUPPORTED_DOMAINS: dict[str, frozenset[str]] = {
    QMT_PLATFORM: frozenset({CN_EQUITY_DOMAIN}),
}

STRATEGY_CATALOG = get_strategy_catalog()
QMT_ROLLOUT_ALLOWLIST = get_qmt_rollout_allowlist()
PLATFORM_CAPABILITY_MATRIX = PlatformCapabilityMatrix(
    platform_id=QMT_PLATFORM,
    supported_domains=PLATFORM_SUPPORTED_DOMAINS[QMT_PLATFORM],
    supported_target_modes=frozenset({"weight", "value"}),
    supported_inputs=frozenset({"market_history", "feature_snapshot", "portfolio_snapshot"}),
    supported_capabilities=frozenset({"broker_client"}),
)
ELIGIBLE_STRATEGY_PROFILES = derive_eligible_profiles_for_platform(
    STRATEGY_CATALOG,
    capability_matrix=PLATFORM_CAPABILITY_MATRIX,
    runtime_adapter_loader=lambda profile: get_platform_runtime_adapter(profile, platform_id=QMT_PLATFORM),
)
QMT_ENABLED_PROFILES = derive_enabled_profiles_for_platform(
    STRATEGY_CATALOG,
    capability_matrix=PLATFORM_CAPABILITY_MATRIX,
    runtime_adapter_loader=lambda profile: get_platform_runtime_adapter(profile, platform_id=QMT_PLATFORM),
    rollout_allowlist=QMT_ROLLOUT_ALLOWLIST,
)
PLATFORM_POLICY = PlatformStrategyPolicy(
    platform_id=QMT_PLATFORM,
    supported_domains=PLATFORM_SUPPORTED_DOMAINS[QMT_PLATFORM],
    enabled_profiles=QMT_ENABLED_PROFILES,
    default_profile="",
    rollback_profile="",
    require_explicit_profile=True,
)


def get_eligible_profiles_for_platform(platform_id: str) -> frozenset[str]:
    if platform_id != QMT_PLATFORM:
        return frozenset()
    return ELIGIBLE_STRATEGY_PROFILES


def get_supported_profiles_for_platform(platform_id: str) -> frozenset[str]:
    return get_enabled_profiles_for_platform(platform_id, policy=PLATFORM_POLICY)


def get_platform_profile_matrix() -> list[dict[str, object]]:
    return list(build_platform_profile_matrix(STRATEGY_CATALOG, policy=PLATFORM_POLICY))


def get_platform_profile_status_matrix() -> list[dict[str, object]]:
    return list(
        build_platform_profile_status_matrix(
            STRATEGY_CATALOG,
            policy=PLATFORM_POLICY,
            eligible_profiles=ELIGIBLE_STRATEGY_PROFILES,
        )
    )


def resolve_strategy_definition(raw_value: str | None, *, platform_id: str) -> StrategyDefinition:
    return resolve_platform_strategy_definition(
        raw_value,
        platform_id=platform_id,
        strategy_catalog=STRATEGY_CATALOG,
        policy=PLATFORM_POLICY,
    )


def resolve_strategy_metadata(raw_value: str | None, *, platform_id: str) -> StrategyMetadata:
    definition = resolve_strategy_definition(raw_value, platform_id=platform_id)
    return get_catalog_strategy_metadata(STRATEGY_CATALOG, definition.profile)
