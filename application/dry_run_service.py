"""Dry-run strategy cycle for QMT platform."""

from __future__ import annotations

from typing import Any

from application.qmt_client import QmtBrokerClient
from quant_platform_kit.common.execution_outcomes import resolve_strategy_run_stage
from quant_platform_kit.strategy_contracts import PositionTarget
from runtime_config_support import PlatformRuntimeSettings
from strategy_runtime import load_strategy_runtime


def _weights_from_decision(decision) -> dict[str, float]:
    weights: dict[str, float] = {}
    for position in decision.positions:
        if not isinstance(position, PositionTarget):
            continue
        weight = float(position.target_weight or 0.0)
        if abs(weight) > 1e-12:
            weights[str(position.symbol)] = weight
    return weights


def _build_order_previews(
    *,
    weights: dict[str, float],
    portfolio,
    client: QmtBrokerClient,
) -> list[dict[str, Any]]:
    equity = float(getattr(portfolio, "total_equity", 0.0) or 0.0)
    previews: list[dict[str, Any]] = []
    for symbol, weight in sorted(weights.items()):
        target_value = equity * float(weight)
        previews.append(
            {
                "symbol": symbol,
                "side": "buy" if target_value >= 0 else "sell",
                "target_weight": float(weight),
                "target_value_cny": float(target_value),
                "status": "previewed",
            }
        )
    return previews


def run_dry_run_cycle(
    *,
    runtime_settings: PlatformRuntimeSettings,
    client: QmtBrokerClient | None = None,
) -> dict[str, Any]:
    broker = client or QmtBrokerClient(
        market_history_path=runtime_settings.market_history_path,
    )
    runtime = load_strategy_runtime(runtime_settings.strategy_profile, runtime_settings=runtime_settings)
    portfolio = broker.get_portfolio_snapshot()

    available_inputs: dict[str, Any] = {"portfolio_snapshot": portfolio}
    if "market_history" in frozenset(runtime.entrypoint.manifest.required_inputs):
        available_inputs["market_history"] = broker.load_market_history()

    evaluation = runtime.evaluate(available_inputs=available_inputs)
    weights = _weights_from_decision(evaluation.decision)
    order_previews = _build_order_previews(weights=weights, portfolio=portfolio, client=broker)
    stage = resolve_strategy_run_stage(
        dry_run_only=runtime_settings.dry_run_only,
        execution_blocked=False,
        terminal_funding_block=False,
        action_done=bool(order_previews),
    )

    return {
        "status": "ok",
        "platform_id": "qmt",
        "strategy_profile": runtime.profile,
        "dry_run_only": runtime_settings.dry_run_only,
        "strategy_run_stage": stage,
        "target_weights": weights,
        "order_previews": order_previews,
        "risk_flags": list(evaluation.decision.risk_flags),
        "diagnostics": dict(evaluation.decision.diagnostics),
        "metadata": dict(evaluation.metadata),
    }
