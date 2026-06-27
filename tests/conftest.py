from __future__ import annotations

import pandas as pd
import pytest

from cn_equity_strategies.strategies.cn_index_etf_tactical_rotation import extract_managed_symbols


@pytest.fixture
def market_history_csv(tmp_path) -> str:
    dates = pd.bdate_range("2024-01-02", periods=320)
    rates = {
        "510300": 1.0002,
        "510500": 1.0001,
        "159915": 0.9998,
        "588000": 1.0000,
        "512100": 1.0003,
        "512170": 1.0004,
        "515030": 1.0009,
        "512760": 1.0008,
        "518880": 1.0005,
        "513100": 1.0007,
        "511880": 1.00001,
        "511260": 1.00002,
    }
    rows: list[dict[str, object]] = []
    for symbol in extract_managed_symbols():
        price = 20.0
        for idx, date in enumerate(dates):
            price *= rates[symbol]
            close = price * (1.0 + 0.04 * ((idx % 5) - 2) / 5)
            rows.append({"date": date, "symbol": symbol, "close": close})
    frame = pd.DataFrame(rows)
    path = tmp_path / "market_history.csv"
    frame.to_csv(path, index=False)
    return str(path)
