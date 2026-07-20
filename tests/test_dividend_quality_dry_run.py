from __future__ import annotations

import pytest

from strategy_registry import QMT_PLATFORM, resolve_strategy_definition


def test_dividend_quality_snapshot_is_research_only_for_qmt_runtime():
    with pytest.raises(ValueError, match="cn_dividend_quality_snapshot"):
        resolve_strategy_definition("cn_dividend_quality_snapshot", platform_id=QMT_PLATFORM)
