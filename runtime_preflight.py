from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime_config_support import PlatformRuntimeSettings, load_platform_runtime_settings
from strategy_loader import load_strategy_entrypoint_for_profile


E3_RECEIPT_SCHEMA_VERSION = "qmt.e3.receipt.v1"
E3_RECEIPT_REQUIRED_SUMMARY_COUNTS = ("accounts", "positions", "orders", "fills", "cash", "ledger")
_E3_RECEIPT_FIELDS = frozenset(
    {
        "schema_version",
        "as_of",
        "freshness_seconds",
        "no_order",
        "verify_only",
        "summary_counts",
    }
)


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


@dataclass(frozen=True)
class E3ReceiptValidationReport:
    status: str
    schema_version: str | None
    issues: tuple[PreflightIssue, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "schema_version": self.schema_version,
            "required_summary_counts": list(E3_RECEIPT_REQUIRED_SUMMARY_COUNTS),
            "issues": [
                {"code": issue.code, "message": issue.message}
                for issue in self.issues
            ],
        }


def validate_e3_receipt(
    receipt: object,
    *,
    now: datetime | None = None,
) -> E3ReceiptValidationReport:
    """Validate a local E3 receipt without connecting to miniQMT or a provider."""
    if not isinstance(receipt, dict):
        return E3ReceiptValidationReport(
            status="error",
            schema_version=None,
            issues=(PreflightIssue("invalid_receipt", "Receipt must be a JSON object."),),
        )

    issues: list[PreflightIssue] = []
    schema_version = receipt.get("schema_version")
    reported_schema_version = schema_version if schema_version == E3_RECEIPT_SCHEMA_VERSION else None

    receipt_fields = frozenset(receipt)
    if _E3_RECEIPT_FIELDS - receipt_fields:
        issues.append(PreflightIssue("missing_receipt_fields", "Receipt has required fields missing."))
    if receipt_fields - _E3_RECEIPT_FIELDS:
        issues.append(PreflightIssue("unexpected_receipt_fields", "Receipt must not contain detail-bearing fields."))
    if schema_version != E3_RECEIPT_SCHEMA_VERSION:
        issues.append(PreflightIssue("invalid_schema_version", "Receipt schema version is not accepted."))

    _validate_e3_summary_counts(receipt.get("summary_counts"), issues)
    _validate_e3_declarations(receipt, issues)
    _validate_e3_freshness(receipt, now=now, issues=issues)

    return E3ReceiptValidationReport(
        status="ok" if not issues else "error",
        schema_version=reported_schema_version,
        issues=tuple(issues),
    )


def _validate_e3_summary_counts(value: object, issues: list[PreflightIssue]) -> None:
    if not isinstance(value, dict) or frozenset(value) != frozenset(E3_RECEIPT_REQUIRED_SUMMARY_COUNTS):
        issues.append(PreflightIssue("invalid_summary_counts", "Receipt must contain only the required summary counts."))
        return
    if any(not isinstance(count, int) or isinstance(count, bool) or count < 0 for count in value.values()):
        issues.append(PreflightIssue("invalid_summary_counts", "Receipt summary counts must be non-negative integers."))


def _validate_e3_declarations(receipt: dict[object, object], issues: list[PreflightIssue]) -> None:
    if receipt.get("no_order") is not True:
        issues.append(PreflightIssue("no_order_required", "Receipt must declare no_order=true."))
    if receipt.get("verify_only") is not True:
        issues.append(PreflightIssue("verify_only_required", "Receipt must declare verify_only=true."))


def _validate_e3_freshness(
    receipt: dict[object, object],
    *,
    now: datetime | None,
    issues: list[PreflightIssue],
) -> None:
    freshness_seconds = receipt.get("freshness_seconds")
    if not isinstance(freshness_seconds, int) or isinstance(freshness_seconds, bool) or freshness_seconds < 0:
        issues.append(PreflightIssue("invalid_freshness", "Receipt freshness must be a non-negative integer."))
        return

    as_of = receipt.get("as_of")
    if not isinstance(as_of, str):
        issues.append(PreflightIssue("invalid_as_of", "Receipt as_of must be a timezone-aware timestamp."))
        return
    try:
        as_of_time = datetime.fromisoformat(as_of.replace("Z", "+00:00"))
    except ValueError:
        issues.append(PreflightIssue("invalid_as_of", "Receipt as_of must be a timezone-aware timestamp."))
        return
    if as_of_time.tzinfo is None:
        issues.append(PreflightIssue("invalid_as_of", "Receipt as_of must be a timezone-aware timestamp."))
        return

    reference_time = now or datetime.now(timezone.utc)
    if reference_time.tzinfo is None:
        reference_time = reference_time.replace(tzinfo=timezone.utc)
    age_seconds = (reference_time - as_of_time).total_seconds()
    if age_seconds < 0:
        issues.append(PreflightIssue("invalid_as_of", "Receipt as_of cannot be in the future."))
    elif age_seconds > freshness_seconds:
        issues.append(PreflightIssue("stale_receipt", "Receipt is older than its declared freshness window."))


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
