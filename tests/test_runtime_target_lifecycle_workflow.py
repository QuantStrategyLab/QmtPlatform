from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_disabled_qmt_lifecycle_workflow_stays_no_order() -> None:
    workflow = (ROOT / ".github" / "workflows" / "runtime-target-lifecycle.yml").read_text(encoding="utf-8")

    assert 'if get_supported_profiles_for_platform("qmt"):' in workflow
    assert "scripts/preflight_qmt_runtime.py" not in workflow
    assert "dry_run_e2e.py" not in workflow
    assert "configured-state: disabled" in workflow
    assert "execution-mode: dry_run" in workflow
    assert "execution_heartbeat=not_applicable" in workflow
    assert "platform: qmt" in workflow
    assert "STRATEGY_PROFILE:" not in workflow
