# QmtPlatform

A 股量化平台层，基于 `QuantPlatformKit` 和 `CnEquityStrategies` 构建，对接 **miniQMT / QMT**。

当前范围为**仅干跑**：评估策略目标并预览订单，不向券商提交实盘。

## 支持策略

| Profile | 输入模式 |
|---|---|
| `cn_industry_etf_rotation` | `market_history`（主轨，runtime_enabled） |
| `cn_industry_etf_rotation_aggressive` | `market_history`（可选目标，vol25%） |
| `cn_dividend_quality_snapshot` | `feature_snapshot`（需快照路径） |
| `cn_index_etf_tactical_rotation` | `market_history`（旧版/research_backtest_only） |

## 快速开始

```bash
python3 -m pip install -e '.[test]'
export STRATEGY_PROFILE=cn_industry_etf_rotation
export QMT_DRY_RUN_ONLY=true
python3 main.py
curl http://127.0.0.1:8080/probe
```

详见 [README.md](README.md)（英文）。

## 许可证

详见 [LICENSE](LICENSE)。
