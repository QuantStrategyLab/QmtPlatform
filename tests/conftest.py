from __future__ import annotations

import pandas as pd
import pytest

from cn_equity_strategies.strategies.cn_industry_etf_rotation import extract_managed_symbols


@pytest.fixture
def market_history_csv(tmp_path) -> str:
    dates = pd.bdate_range("2024-01-02", periods=320)
    rates = {
        "159819": 1.0010,
        "159995": 1.0009,
        "512760": 1.0008,
        "159994": 1.0007,
        "159852": 1.0006,
        "512170": 1.0004,
        "515030": 1.0009,
        "159792": 1.0005,
        "512800": 1.0003,
        "512690": 1.0002,
        "159928": 1.0001,
        "159915": 0.9998,
        "588000": 1.0000,
        "512100": 1.0003,
    }
    rows: list[dict[str, object]] = []
    for symbol in extract_managed_symbols():
        price = 20.0
        for idx, date in enumerate(dates):
            price *= rates.get(symbol, 1.0004)
            close = price * (1.0 + 0.04 * ((idx % 5) - 2) / 5)
            rows.append({"date": date, "symbol": symbol, "close": close, "volume": 1_000_000.0})
    frame = pd.DataFrame(rows)
    path = tmp_path / "market_history.csv"
    frame.to_csv(path, index=False)
    return str(path)
