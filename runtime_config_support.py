from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from quant_platform_kit.common.runtime_config import resolve_bool_value, resolve_strategy_runtime_path_settings
from quant_platform_kit.common.runtime_target import RuntimeTarget, build_runtime_target, resolve_runtime_target_from_env

from strategy_registry import QMT_PLATFORM, resolve_strategy_definition, resolve_strategy_metadata
from cn_equity_strategies import get_strategy_catalog


@dataclass(frozen=True)
class PlatformRuntimeSettings:
    strategy_profile: str
    strategy_display_name: str
    strategy_domain: str
    dry_run_only: bool
    market_history_path: str | None
    feature_snapshot_path: str | None
    feature_snapshot_manifest_path: str | None
    runtime_target: RuntimeTarget | None = None


def load_platform_runtime_settings() -> PlatformRuntimeSettings:
    dry_run_only = resolve_bool_value(os.getenv("QMT_DRY_RUN_ONLY", "true"))
    runtime_target = _resolve_runtime_target(dry_run_only=dry_run_only)
    strategy_definition = resolve_strategy_definition(runtime_target.strategy_profile, platform_id=QMT_PLATFORM)
    strategy_metadata = resolve_strategy_metadata(strategy_definition.profile, platform_id=QMT_PLATFORM)
    runtime_paths = resolve_strategy_runtime_path_settings(
        strategy_catalog=get_strategy_catalog(),
        strategy_definition=strategy_definition,
        strategy_metadata=strategy_metadata,
        platform_env_prefix="QMT",
        env=os.environ,
        repo_root=Path(__file__).resolve().parent,
    )
    return PlatformRuntimeSettings(
        strategy_profile=runtime_paths.strategy_profile,
        strategy_display_name=runtime_paths.strategy_display_name,
        strategy_domain=runtime_paths.strategy_domain,
        dry_run_only=dry_run_only,
        market_history_path=os.getenv("QMT_MARKET_HISTORY_PATH") or None,
        feature_snapshot_path=runtime_paths.feature_snapshot_path,
        feature_snapshot_manifest_path=runtime_paths.feature_snapshot_manifest_path,
        runtime_target=runtime_target,
    )


def _resolve_runtime_target(*, dry_run_only: bool) -> RuntimeTarget:
    if os.getenv("RUNTIME_TARGET_JSON"):
        return resolve_runtime_target_from_env(env=os.environ, expected_platform_id=QMT_PLATFORM)
    profile = os.getenv("STRATEGY_PROFILE")
    if not profile:
        raise EnvironmentError("STRATEGY_PROFILE or RUNTIME_TARGET_JSON is required")
    return build_runtime_target(
        platform_id=QMT_PLATFORM,
        strategy_profile=profile,
        dry_run_only=dry_run_only,
        deployment_selector=os.getenv("K_SERVICE"),
        account_selector=os.getenv("QMT_ACCOUNT"),
        account_scope=os.getenv("ACCOUNT_REGION") or "CN",
        service_name=os.getenv("K_SERVICE") or "qmt-quant-service",
    )
