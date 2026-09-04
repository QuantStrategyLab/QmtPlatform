from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

from quant_platform_kit.common.models import PortfolioSnapshot
from quant_platform_kit.common.strategy_contracts import (
    StrategyDecision,
    StrategyManifest,
    StrategyRuntimeAdapter,
)
from runtime_config_support import PlatformRuntimeSettings
import strategy_runtime as strategy_runtime_module


def _runtime_settings() -> PlatformRuntimeSettings:
    return PlatformRuntimeSettings(
        strategy_profile="cn_industry_etf_rotation",
        strategy_display_name="CN Industry ETF Rotation",
        strategy_domain="cn_equity",
        dry_run_only=True,
        market_history_path=None,
        feature_snapshot_path=None,
        feature_snapshot_manifest_path=None,
    )


def test_evaluate_stamps_consecutive_losses_on_portfolio_snapshot():
    class _Entrypoint:
        manifest = StrategyManifest(
            profile="cn_industry_etf_rotation",
            domain="cn_equity",
            display_name="CN Industry ETF Rotation",
            description="test",
            required_inputs=frozenset({"portfolio_snapshot"}),
        )

        def evaluate(self, ctx):
            self.ctx = ctx
            return StrategyDecision()

    entrypoint = _Entrypoint()
    runtime = strategy_runtime_module.LoadedStrategyRuntime(
        entrypoint=entrypoint,
        runtime_adapter=StrategyRuntimeAdapter(portfolio_input_name="portfolio_snapshot"),
        runtime_settings=_runtime_settings(),
    )
    snapshot = PortfolioSnapshot(
        as_of=datetime.now(timezone.utc),
        total_equity=100_000.0,
        positions=(),
        metadata={},
    )
    stamped = PortfolioSnapshot(
        as_of=snapshot.as_of,
        total_equity=snapshot.total_equity,
        positions=(),
        metadata={"consecutive_losses": 3},
    )

    with patch(
        "quant_platform_kit.strategy_lifecycle.live_equity.stamp_consecutive_losses_on_snapshot",
        return_value=stamped,
    ) as stamp:
        result = runtime.evaluate(available_inputs={"portfolio_snapshot": snapshot})

    stamp.assert_called_once()
    assert entrypoint.ctx.portfolio is stamped
    assert entrypoint.ctx.portfolio.metadata["consecutive_losses"] == 3
    assert result.metadata["strategy_profile"] == "cn_industry_etf_rotation"
