from __future__ import annotations

import pytest

from main import app


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, market_history_csv: str):
    monkeypatch.setenv("STRATEGY_PROFILE", "cn_index_etf_tactical_rotation")
    monkeypatch.setenv("QMT_DRY_RUN_ONLY", "true")
    monkeypatch.setenv("QMT_MARKET_HISTORY_PATH", market_history_csv)
    monkeypatch.delenv("RUNTIME_TARGET_JSON", raising=False)
    return app.test_client()


def test_probe_endpoint(client):
    response = client.get("/probe")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "ok"
    assert payload["platform_id"] == "qmt"
    assert payload["strategy_profile"] == "cn_index_etf_tactical_rotation"


def test_dry_run_endpoint(client):
    response = client.get("/dry-run")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "ok"
    assert payload["target_weights"]
