from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from runtime_config_support import PlatformRuntimeSettings, load_platform_runtime_settings
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
    execution_mode: str | None
    paper_admission: bool
    required_inputs: tuple[str, ...]
    issues: tuple[PreflightIssue, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "strategy_profile": self.strategy_profile,
            "dry_run_only": self.dry_run_only,
            "execution_mode": self.execution_mode,
            "paper_admission": self.paper_admission,
            "required_inputs": list(self.required_inputs),
            "issues": [
                {"code": issue.code, "message": issue.message}
                for issue in self.issues
            ],
        }


def run_preflight(*, paper_admission: bool = False) -> QmtPreflightReport:
    issues: list[PreflightIssue] = []
    try:
        settings = load_platform_runtime_settings()
        entrypoint = load_strategy_entrypoint_for_profile(settings.strategy_profile)
    except Exception as exc:  # noqa: BLE001 - preflight must fail closed for any runtime configuration error.
        return QmtPreflightReport(
            status="error",
            strategy_profile=None,
            dry_run_only=None,
            execution_mode=None,
            paper_admission=paper_admission,
            required_inputs=(),
            issues=(PreflightIssue("runtime_config_error", str(exc)),),
        )

    required_inputs = tuple(sorted(frozenset(entrypoint.manifest.required_inputs)))
    execution_mode = os.getenv("QMT_EXECUTION_MODE", "dry_run").strip().lower()
    if not settings.dry_run_only:
        issues.append(
            PreflightIssue(
                "non_dry_run_blocked",
                "QMT_DRY_RUN_ONLY=false is not accepted by preflight; live QMT submission is not wired in this repo.",
            )
        )

    if paper_admission:
        _check_paper_admission(
            settings=settings,
            execution_mode=execution_mode,
            required_inputs=required_inputs,
            issues=issues,
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
        execution_mode=execution_mode,
        paper_admission=paper_admission,
        required_inputs=required_inputs,
        issues=tuple(issues),
    )


def _check_existing_path(value: str | None, *, code: str, label: str, issues: list[PreflightIssue]) -> None:
    if not value:
        issues.append(PreflightIssue(code, f"{label} is required."))
        return
    if not Path(value).expanduser().exists():
        issues.append(PreflightIssue(code, f"{label} does not exist."))


def _check_paper_admission(
    *,
    settings: PlatformRuntimeSettings,
    execution_mode: str,
    required_inputs: tuple[str, ...],
    issues: list[PreflightIssue],
) -> None:
    if not settings.dry_run_only:
        issues.append(PreflightIssue("paper_admission_dry_run_required", "Paper admission requires QMT_DRY_RUN_ONLY=true."))
    if execution_mode != "paper":
        issues.append(PreflightIssue("paper_admission_mode_required", "Paper admission requires QMT_EXECUTION_MODE=paper."))
    if required_inputs != ("market_history",):
        issues.append(
            PreflightIssue(
                "paper_admission_fixed_input_required",
                "Paper admission supports only the fixed market_history input contract.",
            )
        )
        return

    expected_digest = os.getenv("QMT_PAPER_ADMISSION_INPUT_SHA256", "").strip().lower()
    if not re.fullmatch(r"[0-9a-f]{64}", expected_digest):
        issues.append(
            PreflightIssue(
                "paper_admission_input_digest_required",
                "QMT_PAPER_ADMISSION_INPUT_SHA256 must be a SHA-256 digest for the fixed market history input.",
            )
        )
        return

    market_history_path = settings.market_history_path
    if market_history_path and Path(market_history_path).expanduser().is_file():
        with Path(market_history_path).expanduser().open("rb") as input_file:
            actual_digest = hashlib.file_digest(input_file, "sha256").hexdigest()
        if actual_digest != expected_digest:
            issues.append(
                PreflightIssue(
                    "paper_admission_input_digest_mismatch",
                    "QMT_MARKET_HISTORY_PATH does not match QMT_PAPER_ADMISSION_INPUT_SHA256.",
                )
            )
