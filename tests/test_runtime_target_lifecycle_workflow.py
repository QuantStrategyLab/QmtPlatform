from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_disabled_qmt_lifecycle_workflow_stays_no_order() -> None:
    workflow = (ROOT / ".github" / "workflows" / "runtime-target-lifecycle.yml").read_text(encoding="utf-8")

    assert "python scripts/preflight_qmt_runtime.py" in workflow
    assert "python scripts/smoke_cn_industry_etf_rotation_dry_run_e2e.py" in workflow
    assert 'if [ "$smoke_status" -eq 2 ]; then' in workflow
    assert "safely blocked by the risk gate" in workflow
    assert "configured-state: disabled" in workflow
    assert "execution-mode: dry_run" in workflow
    assert "execution_heartbeat=not_applicable" in workflow
    assert "platform: qmt" in workflow
    assert 'QMT_DRY_RUN_ONLY: "true"' in workflow
    assert "QMT_DRY_RUN_ONLY=false" not in workflow
