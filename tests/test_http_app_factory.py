from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import pytest

import main


@dataclass(frozen=True)
class _Settings:
    strategy_profile: str = "synthetic_profile"
    dry_run_only: bool = True
    market_history_path: str | None = "synthetic-history.csv"
    marker: str = "unchanged"


@pytest.fixture(params=["legacy", "factory"])
def http_app(request, monkeypatch: pytest.MonkeyPatch):
    application = main.app if request.param == "legacy" else main.create_app()
    monkeypatch.setitem(application.config, "TESTING", True)
    return application


@pytest.fixture
def dependencies(monkeypatch: pytest.MonkeyPatch):
    state = SimpleNamespace(
        settings=_Settings(),
        report={"status": "unknown", "order_previews": [], "reason": "synthetic"},
        profiles=[{"profile": "synthetic_profile", "available": False}],
        events=[],
        client=object(),
        settings_error=None,
        client_error=None,
        cycle_error=None,
        profiles_error=None,
    )

    def load_settings():
        state.events.append(("settings",))
        if state.settings_error is not None:
            raise state.settings_error
        return state.settings

    def create_client(*, market_history_path):
        state.events.append(("client", market_history_path))
        if state.client_error is not None:
            raise state.client_error
        return state.client

    def run_cycle(*, runtime_settings, client):
        state.events.append(("cycle", runtime_settings, client))
        if state.cycle_error is not None:
            raise state.cycle_error
        return state.report

    def profile_matrix():
        state.events.append(("profiles",))
        if state.profiles_error is not None:
            raise state.profiles_error
        return state.profiles

    def format_traceback():
        state.events.append(("traceback",))
        return "synthetic traceback"

    monkeypatch.delenv("QMT_MARKET_HISTORY_PATH", raising=False)
    monkeypatch.setattr(main, "load_platform_runtime_settings", load_settings)
    monkeypatch.setattr(main, "QmtBrokerClient", create_client)
    monkeypatch.setattr(main, "run_dry_run_cycle", run_cycle)
    monkeypatch.setattr(main, "get_platform_profile_status_matrix", profile_matrix)
    monkeypatch.setattr(main.traceback, "format_exc", format_traceback)
    return state


def test_route_inventory_and_exported_handlers(http_app):
    routes = {(rule.rule, rule.endpoint, tuple(sorted(rule.methods))) for rule in http_app.url_map.iter_rules()}
    assert routes == {
        ("/static/<path:filename>", "static", ("GET", "HEAD", "OPTIONS")),
        ("/probe", "probe", ("GET", "HEAD", "OPTIONS")),
        ("/profiles", "profiles", ("GET", "HEAD", "OPTIONS")),
        ("/dry-run", "dry_run", ("GET", "HEAD", "OPTIONS", "POST")),
    }
    assert http_app.name == main.__name__
    for endpoint in ("probe", "profiles", "dry_run"):
        assert http_app.view_functions[endpoint] is getattr(main, endpoint)


@pytest.mark.parametrize("method", ["GET", "HEAD"])
def test_probe_response_and_request_scoped_settings(http_app, dependencies, method):
    response = http_app.test_client().open("/probe", method=method)
    assert response.status_code == 200
    assert response.mimetype == "application/json"
    if method == "HEAD":
        assert response.data == b""
    else:
        assert response.get_json() == {
            "status": "ok",
            "platform_id": "qmt",
            "strategy_profile": "synthetic_profile",
            "dry_run_only": True,
        }
    assert dependencies.events == [("settings",)]


def test_profiles_response_does_not_load_runtime_settings(http_app, dependencies):
    response = http_app.test_client().get("/profiles")
    assert response.status_code == 200
    assert response.get_json() == {"profiles": dependencies.profiles}
    assert dependencies.events == [("profiles",)]


@pytest.mark.parametrize("method", ["GET", "POST"])
@pytest.mark.parametrize("configured_dry_run", [True, False])
def test_dry_run_preserves_settings_and_dependency_order(http_app, dependencies, method, configured_dry_run):
    original = _Settings(dry_run_only=configured_dry_run)
    dependencies.settings = original
    response = http_app.test_client().open("/dry-run", method=method)
    assert response.status_code == 200
    assert response.get_json() == dependencies.report
    assert dependencies.events[:2] == [("settings",), ("client", "synthetic-history.csv")]
    assert len(dependencies.events) == 3
    event, effective, client = dependencies.events[2]
    assert event == "cycle"
    assert client is dependencies.client
    assert effective == _Settings(dry_run_only=True)
    assert (effective is original) is configured_dry_run
    assert original.dry_run_only is configured_dry_run


@pytest.mark.parametrize("path", [None, "", " ", "selected.csv"])
def test_history_path_fallback_keeps_existing_truthiness(http_app, dependencies, monkeypatch, path):
    dependencies.settings = _Settings(market_history_path=path)
    monkeypatch.setenv("QMT_MARKET_HISTORY_PATH", "environment.csv")
    response = http_app.test_client().get("/dry-run")
    assert response.status_code == 200
    expected = "environment.csv" if path in (None, "") else path
    assert dependencies.events[1] == ("client", expected)


@pytest.mark.parametrize("report", [{"status": "unknown"}, {"status": "blocked"}, None])
def test_cycle_report_is_returned_without_reclassification(http_app, dependencies, report):
    dependencies.report = report
    response = http_app.test_client().get("/dry-run")
    assert response.status_code == 200
    assert response.get_json() == report
    assert [event[0] for event in dependencies.events] == ["settings", "client", "cycle"]


def test_settings_error_stays_outside_the_cycle_exception_handler(http_app, dependencies):
    error = ValueError("synthetic settings failure")
    dependencies.settings_error = error
    with pytest.raises(ValueError) as caught:
        http_app.test_client().get("/dry-run")
    assert caught.value is error
    assert dependencies.events == [("settings",)]


def test_profile_error_keeps_framework_error_handling(http_app, dependencies):
    error = LookupError("synthetic catalog failure")
    dependencies.profiles_error = error
    with pytest.raises(LookupError) as caught:
        http_app.test_client().get("/profiles")
    assert caught.value is error
    assert dependencies.events == [("profiles",)]


@pytest.mark.parametrize("stage", ["client", "cycle"])
def test_cycle_errors_preserve_status_message_and_traceback_passthrough(http_app, dependencies, stage):
    setattr(dependencies, stage + "_error", RuntimeError("synthetic " + stage + " failure"))
    response = http_app.test_client().get("/dry-run")
    assert response.status_code == 500
    assert response.get_json() == {
        "status": "error",
        "error": "synthetic " + stage + " failure",
        "traceback": "synthetic traceback",
    }
    expected = ["settings", "client"] + (["cycle"] if stage == "cycle" else []) + ["traceback"]
    assert [event[0] for event in dependencies.events] == expected


def test_base_exception_is_not_converted_into_an_error_report(http_app, dependencies):
    error = BaseException("synthetic stop")
    dependencies.cycle_error = error
    with pytest.raises(BaseException) as caught:
        http_app.test_client().get("/dry-run")
    assert caught.value is error
    assert [event[0] for event in dependencies.events] == ["settings", "client", "cycle"]


@pytest.mark.parametrize(
    ("method", "path", "status"),
    [("PUT", "/dry-run", 405), ("POST", "/probe", 405), ("GET", "/absent", 404), ("OPTIONS", "/dry-run", 200)],
)
def test_framework_routes_do_not_call_application_dependencies(http_app, dependencies, method, path, status):
    response = http_app.test_client().open(path, method=method)
    assert response.status_code == status
    assert dependencies.events == []
    if method == "OPTIONS":
        assert {value.strip() for value in response.headers["Allow"].split(",")} == {"GET", "HEAD", "POST", "OPTIONS"}


def test_each_request_loads_its_own_settings(http_app, dependencies):
    client = http_app.test_client()
    assert client.get("/probe").get_json()["strategy_profile"] == "synthetic_profile"
    dependencies.settings = _Settings(strategy_profile="another_synthetic_profile")
    assert client.get("/probe").get_json()["strategy_profile"] == "another_synthetic_profile"
    assert dependencies.events == [("settings",), ("settings",)]


def test_factory_instances_have_independent_configuration_and_routes(dependencies):
    first = main.create_app()
    second = main.create_app()
    assert first is not second
    assert first is not main.app
    first.config["SYNTHETIC_TEST_SETTING"] = "first only"
    assert "SYNTHETIC_TEST_SETTING" not in second.config
    assert "SYNTHETIC_TEST_SETTING" not in main.app.config
    first.add_url_rule("/synthetic-only", view_func=lambda: "first only")
    assert first.test_client().get("/synthetic-only").status_code == 200
    assert second.test_client().get("/synthetic-only").status_code == 404
    assert main.app.test_client().get("/synthetic-only").status_code == 404
    assert dependencies.events == []
