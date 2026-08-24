from __future__ import annotations

from application.qmt_client import QmtBrokerClient
from quant_platform_kit.common.models import OrderIntent


def test_live_qmt_submission_is_not_reported_as_filled() -> None:
    report = QmtBrokerClient().submit_order(
        OrderIntent(symbol="510300.SH", side="buy", quantity=100.0),
        dry_run=False,
    )

    assert report.status == "submitted"
    assert report.filled_quantity == 0.0
    assert report.raw_payload["execution_status"] == "pending_reconciliation"


def test_qmt_dry_run_remains_an_unfilled_preview() -> None:
    report = QmtBrokerClient().submit_order(
        OrderIntent(symbol="510300.SH", side="buy", quantity=100.0),
        dry_run=True,
    )

    assert report.status == "previewed"
    assert report.filled_quantity == 0.0
    assert report.raw_payload["execution_status"] == "dry_run_preview"
