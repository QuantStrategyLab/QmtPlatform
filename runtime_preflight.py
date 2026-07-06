from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from runtime_config_support import load_platform_runtime_settings
from strategy_loader import load_strategy_entrypoint_for_profile


@dataclass(frozen=True)
class PreflightIssue:
    code: str
    message: str


@dataclass(frozen=True)
class QmtPreflightReport:
    status: str
    strategy_profile: str | None
    dry_run_only: bool | None
    required_inputs: tuple[str, ...]
    issues: tuple[PreflightIssue, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "strategy_profile": self.strategy_profile,
            "dry_run_only": self.dry_run_only,
            "required_inputs": list(self.required_inputs),
            "issues": [
                {"code": issue.code, "message": issue.message}
                for issue in self.issues
            ],
        }


def run_preflight(*, allow_non_dry_run: bool = False) -> QmtPreflightReport:
    issues: list[PreflightIssue] = []
    try:
        settings = load_platform_runtime_settings()
        entrypoint = load_strategy_entrypoint_for_profile(settings.strategy_profile)
    except Exception as exc:
        return QmtPreflightReport(
            status="error",
            strategy_profile=None,
            dry_run_only=None,
            required_inputs=(),
            issues=(PreflightIssue("runtime_config_error", str(exc)),),
        )

    required_inputs = tuple(sorted(frozenset(entrypoint.manifest.required_inputs)))
    if not settings.dry_run_only and not allow_non_dry_run:
        issues.append(
            PreflightIssue(
                "non_dry_run_blocked",
                "QMT_DRY_RUN_ONLY=false is not accepted by preflight; live QMT submission is not wired in this repo.",
            )
        )

    if "market_history" in required_inputs:
        _check_existing_path(
            settings.market_history_path,
            code="missing_market_history",
            label="QMT_MARKET_HISTORY_PATH",
            issues=issues,
        )
    if "feature_snapshot" in required_inputs:
        _check_existing_path(
            settings.feature_snapshot_path,
            code="missing_feature_snapshot",
            label="QMT_FEATURE_SNAPSHOT_PATH",
            issues=issues,
        )
        _check_existing_path(
            settings.feature_snapshot_manifest_path,
            code="missing_feature_snapshot_manifest",
            label="QMT_FEATURE_SNAPSHOT_MANIFEST_PATH",
            issues=issues,
        )

    return QmtPreflightReport(
        status="ok" if not issues else "error",
        strategy_profile=settings.strategy_profile,
        dry_run_only=settings.dry_run_only,
        required_inputs=required_inputs,
        issues=tuple(issues),
    )


def _check_existing_path(value: str | None, *, code: str, label: str, issues: list[PreflightIssue]) -> None:
    if not value:
        issues.append(PreflightIssue(code, f"{label} is required."))
        return
    if not Path(value).expanduser().exists():
        issues.append(PreflightIssue(code, f"{label} does not exist."))
