# QmtPlatform


## QSL 架构角色

- **层级**：`执行平台`。
- **职责**：QMT / miniQMT A 股执行运行时。
- **事实源/归属**：QMT runtime 控制和 A 股平台集成。
- **消费对象**：CnEquityStrategies、QuantPlatformKit、QuantRuntimeSettings、market-history 输入。
- **禁止事项**：承载策略研究逻辑或发布 snapshot artifacts。

A 股量化平台层，基于 `QuantPlatformKit` 和 `CnEquityStrategies` 构建，对接 **miniQMT / QMT**。

当前范围为**仅干跑**：评估策略目标并预览订单，不向券商提交实盘。

## 支持 dry-run 策略

| Profile | 输入模式 |
|---|---|
| `cn_industry_etf_rotation` | `market_history`（主轨，runtime_enabled） |
| `cn_industry_etf_rotation_aggressive` | `market_history`（可选目标，live_candidate） |

`cn_dividend_quality_snapshot`、`cn_index_etf_tactical_rotation` 等 research-only profile 不会进入 QMT runtime 配置；只有在 `CnEquityStrategies` 中完成提级后才允许启用。

## 快速开始

```bash
python3 -m pip install -e '.[test]'
export STRATEGY_PROFILE=cn_industry_etf_rotation
export QMT_DRY_RUN_ONLY=true
export QMT_MARKET_HISTORY_PATH=data/fixtures/market_history.sample.csv
python3 scripts/preflight_qmt_runtime.py
python3 main.py
curl http://127.0.0.1:8080/probe
```

`.env.example` 是当前 dry-run 配置模板；preflight 只校验 profile 与输入文件路径，不读取或写入账号、密码、token。

## 已停用目标的生命周期验证

QMT 当前没有配置券商运行面或实盘凭据。工作日定时的 `Runtime Target Lifecycle` 只运行确定性预检和基于
固定样本行情的 dry-run smoke，然后向统一管理端发布脱敏的 `disabled` / `dry_run` 状态。检查通过只表示
“无订单验证路径正常”，不表示 QMT 已部署、已连接 miniQMT、已启用 paper 或实盘。检查失败会发布为
`attention`；任何状态都不能改变目标开关或提交订单。

详见 [README.md](README.md)（英文）。

## 许可证

详见 [LICENSE](LICENSE)。
