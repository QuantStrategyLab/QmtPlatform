from __future__ import annotations

import pytest

from main import app


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, market_history_csv: str):
    monkeypatch.setenv("STRATEGY_PROFILE", "cn_industry_etf_rotation")
    monkeypatch.setenv("QMT_DRY_RUN_ONLY", "true")
    monkeypatch.setenv("QMT_MARKET_HISTORY_PATH", market_history_csv)
    monkeypatch.delenv("RUNTIME_TARGET_JSON", raising=False)
    return app.test_client()


def test_probe_endpoint(client, historical_strategy_policy):
    response = client.get("/probe")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "ok"
    assert payload["platform_id"] == "qmt"
    assert payload["strategy_profile"] == "cn_industry_etf_rotation"


def test_dry_run_endpoint(client, historical_strategy_policy):
    response = client.get("/dry-run")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "ok"
    assert payload["target_weights"] == {}
    assert payload["order_previews"] == []
    assert payload["risk_flags"] == ["rejected:concentration"]
    assert payload["diagnostics"]["risk_gate"] == "REJECT"


def test_retired_profile_cannot_run_through_http(client, monkeypatch):
    import main

    def unexpected_cycle(**kwargs):
        pytest.fail("Retired profile reached the strategy cycle")

    monkeypatch.setattr(main, "run_dry_run_cycle", unexpected_cycle)
    assert client.get("/dry-run").status_code == 500


def test_profiles_endpoint_has_no_enabled_profiles(client):
    response = client.get("/profiles")
    assert response.status_code == 200
    assert not any(row["enabled"] for row in response.get_json()["profiles"])
