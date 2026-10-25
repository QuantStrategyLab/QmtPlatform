# QmtPlatform

[English](README.md) | 简体中文

面向 miniQMT / QMT 的 A 股量化平台层，基于 `QuantPlatformKit` 和 `CnEquityStrategies` 构建。

## 状态

实验性项目。当前实现离线评估策略并预览订单。本项目不构成投资建议，也不保证任何交易结果。

## 简介

QmtPlatform 提供 QMT 平台集成层。它从 `CnEquityStrategies` 加载策略配置，读取本地历史行情，并基于模拟投资组合评估目标权重。`QuantPlatformKit` 提供共享运行组件与策略契约，`QuantRuntimeSettings` 提供运行目标定义。

## 不适用范围

本仓库不实现策略研究，也不发布快照产物。它没有 miniQMT / QMT 券商连接。离线券商适配器对非 dry-run 的订单请求返回 `blocked`，不会将其报告为 `submitted`。

## 快速开始

需要 Python 3.11 或更高版本及 Git。在仓库根目录运行以下命令。安装包时会使用 `pyproject.toml` 声明的依赖版本。

```bash
python3 -m pip install -e '.[test]'
python3 -m pytest -q tests

unset RUNTIME_TARGET_JSON
export STRATEGY_PROFILE=cn_industry_etf_rotation
export QMT_DRY_RUN_ONLY=true
export QMT_EXECUTION_MODE=dry_run
export QMT_MARKET_HISTORY_PATH=data/fixtures/market_history.sample.csv

python3 scripts/preflight_qmt_runtime.py
python3 main.py
```

在另一个终端查询本地服务：

```bash
curl http://127.0.0.1:8080/probe
curl http://127.0.0.1:8080/profiles
curl http://127.0.0.1:8080/dry-run
```

以下 smoke 脚本使用固定样本运行本地策略周期，无需启动 HTTP 服务：

```bash
python3 scripts/smoke_cn_industry_etf_rotation_dry_run_e2e.py
python3 scripts/smoke_cn_industry_etf_rotation_aggressive_dry_run_e2e.py
```

## 配置

以 [`.env.example`](.env.example) 为 dry-run 配置参考，在 shell 中导出相应值；入口程序读取环境变量。预检命令检查所选策略及所需输入路径，不访问券商凭据。

| 变量 | 是否必需 | 默认值 | 用途 |
|---|---|---|---|
| `STRATEGY_PROFILE` | 未设置 `RUNTIME_TARGET_JSON` 时必需 | 无 | QMT 已启用的策略配置 ID。 |
| `QMT_DRY_RUN_ONLY` | 否 | `true` | 保持为 `true`；预检拒绝 `false`，HTTP dry-run 接口始终使用 dry-run 设置。 |
| `QMT_EXECUTION_MODE` | 否 | `dry_run` | 仅在离线 paper-admission 检查中设为 `paper`；该值不会建立券商连接。 |
| `QMT_PAPER_ADMISSION_INPUT_SHA256` | 使用 `--paper-admission` 时必需 | 无 | 预先记录的固定历史行情输入的 SHA-256 摘要。 |
| `QMT_MARKET_HISTORY_PATH` | 历史行情策略必需 | 无 | 包含 `date,symbol,close` 列的本地 CSV 路径。 |
| `RUNTIME_TARGET_JSON` | 否 | 无 | 来自 `QuantRuntimeSettings` 的 JSON 运行目标；优先于 `STRATEGY_PROFILE`。 |
| `PORT` | 否 | `8080` | HTTP 端口；Flask 入口绑定 `0.0.0.0`。 |

## 支持的 dry-run 策略

| 策略配置 | 输入模式 | 用途 |
|---|---|---|
| `cn_industry_etf_rotation` | `market_history` | 主要策略。 |
| `cn_industry_etf_rotation_aggressive` | `market_history` | 可选策略，目标波动率为 25%。 |

未设置 `RUNTIME_TARGET_JSON` 时，可通过 `STRATEGY_PROFILE=cn_industry_etf_rotation_aggressive` 选择可选策略。运行目标示例见 [QuantRuntimeSettings](https://github.com/QuantStrategyLab/QuantRuntimeSettings/blob/main/examples/targets/qmt/industry_etf_aggressive_dry_run.example.json)。

可用策略由 `CnEquityStrategies` 的策略目录和 QMT 启用清单决定。QMT 运行配置不接受 `cn_dividend_quality_snapshot`、`cn_index_etf_tactical_rotation` 等仅供研究的策略配置。

## 离线 paper-admission 检查

`--paper-admission` 检查本地配置和固定输入文件。它要求 `QMT_EXECUTION_MODE=paper`、`QMT_DRY_RUN_ONLY=true`，且预先记录的 SHA-256 摘要与 `QMT_MARKET_HISTORY_PATH` 一致。

配置策略和输入路径后，将 `<expected-sha256>` 替换为预先记录的摘要：

```bash
export QMT_EXECUTION_MODE=paper
export QMT_DRY_RUN_ONLY=true
export QMT_PAPER_ADMISSION_INPUT_SHA256='<expected-sha256>'
python3 scripts/preflight_qmt_runtime.py --paper-admission
```

该命令加载策略契约并计算本地输入摘要，不调用 QMT SDK 或服务提供方，不读取凭据、创建订单或评估券商账户。这里的 `paper` 表示离线检查，不代表券商模拟交易连接。

## 已停用目标的生命周期验证

工作日运行的 `Runtime Target Lifecycle` 工作流为固定的已停用目标执行确定性预检和基于样本的 dry-run，并发布 `disabled` / `dry_run` 状态。若周期已完成，但风控检查使目标权重为空，视为成功完成无订单检查；预检或 dry-run 失败则报告为 `attention`。这些报告不会修改目标设置、建立券商连接或提交订单。

## HTTP 接口

| 方法 | 路径 | 响应 |
|---|---|---|
| `GET` | `/probe` | 健康状态、当前策略和 dry-run 设置。 |
| `GET` | `/profiles` | 平台策略配置矩阵。 |
| `GET`、`POST` | `/dry-run` | 基于本地输入计算的策略目标权重和订单预览。 |

## 相关仓库

- [QuantPlatformKit](https://github.com/QuantStrategyLab/QuantPlatformKit)
- [CnEquityStrategies](https://github.com/QuantStrategyLab/CnEquityStrategies)
- [CnEquitySnapshotPipelines](https://github.com/QuantStrategyLab/CnEquitySnapshotPipelines)
- [QuantRuntimeSettings](https://github.com/QuantStrategyLab/QuantRuntimeSettings)

## 仓库结构

```text
application/    离线券商适配器和 dry-run 周期
data/fixtures/  历史行情和快照样本输入
scripts/        预检和本地 smoke 命令
tests/          自动化测试
main.py         Flask HTTP 入口
```

## 参与贡献

见 [CONTRIBUTING.md](CONTRIBUTING.md)。AI 助手与维护者遵循 [AGENTS.md](AGENTS.md)。文档遵循 [QuantStrategyLab 文档风格指南](https://github.com/QuantStrategyLab/.github/blob/main/docs/STYLE_GUIDE.md)。

## 安全

私下报告安全漏洞的方法见 [SECURITY.md](SECURITY.md)。请勿在 issue、示例或日志中填写凭据或账户标识。

## 许可证

[MIT](LICENSE)。
