"""QMT broker client (dry-run first)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from quant_platform_kit.common.models import ExecutionReport, OrderIntent, PortfolioSnapshot


@dataclass(frozen=True)
class QmtBrokerClient:
    account_id: str = "QMT-PAPER"
    cash_cny: float = 1_000_000.0
    market_history_path: str | None = None

    def get_portfolio_snapshot(self) -> PortfolioSnapshot:
        return PortfolioSnapshot(
            as_of=datetime.now(timezone.utc),
            total_equity=float(self.cash_cny),
            buying_power=float(self.cash_cny),
            cash_balance=float(self.cash_cny),
            positions=(),
            metadata={"account_id": self.account_id, "currency": "CNY"},
        )

    def load_market_history(self) -> pd.DataFrame:
        path = self.market_history_path
        if not path:
            raise ValueError("QMT_MARKET_HISTORY_PATH is required for direct market-history strategies")
        frame = pd.read_csv(Path(path))
        required = {"date", "symbol", "close"}
        missing = required - set(frame.columns)
        if missing:
            missing_text = ", ".join(sorted(missing))
            raise ValueError(f"market history missing columns: {missing_text}")
        return frame

    def submit_order(self, order: OrderIntent, *, dry_run: bool = True) -> ExecutionReport:
        status = "previewed" if dry_run else "submitted"
        return ExecutionReport(
            symbol=order.symbol,
            side=order.side,
            quantity=float(order.quantity),
            status=status,
            filled_quantity=0.0 if dry_run else float(order.quantity),
            raw_payload={"dry_run": dry_run, "broker": "qmt"},
        )

    def preview_orders(self, orders: list[OrderIntent]) -> list[dict[str, Any]]:
        return [
            {
                "symbol": order.symbol,
                "side": order.side,
                "quantity": float(order.quantity),
                "order_type": order.order_type,
                "status": "previewed",
            }
            for order in orders
        ]
