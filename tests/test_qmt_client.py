from __future__ import annotations

from application.qmt_client import QmtBrokerClient
from quant_platform_kit.common.models import OrderIntent


def test_non_dry_run_qmt_submission_is_blocked() -> None:
    report = QmtBrokerClient().submit_order(
        OrderIntent(symbol="510300.SH", side="buy", quantity=100.0),
        dry_run=False,
    )

    assert report.status == "blocked"
    assert report.filled_quantity == 0.0
    assert report.raw_payload["execution_status"] == "dry_run_only_blocked"
    assert report.raw_payload["executable"] is False


def test_qmt_dry_run_remains_an_unfilled_preview() -> None:
    report = QmtBrokerClient().submit_order(
        OrderIntent(symbol="510300.SH", side="buy", quantity=100.0),
        dry_run=True,
    )

    assert report.status == "previewed"
    assert report.filled_quantity == 0.0
    assert report.raw_payload["execution_status"] == "dry_run_preview"


def test_qmt_portfolio_snapshot_is_explicitly_synthetic_and_not_reconciled() -> None:
    snapshot = QmtBrokerClient().get_portfolio_snapshot()

    assert snapshot.metadata["evidence_source"] == "synthetic"
    assert snapshot.metadata["reconciliation_status"] == "not_available"
