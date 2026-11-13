# QmtPlatform

[English](README.md) | 简体中文

面向 miniQMT / QMT 的 A 股量化平台层，基于 `QuantPlatformKit` 和 `CnEquityStrategies` 构建。

## 状态

实验性项目。固定依赖中的 A 股政策已无可选运行策略；退役策略会在离线评估或订单预览之前被拒绝，历史策略元数据和适配器仍保留。本项目不构成投资建议，也不保证任何交易结果。

## 简介

QmtPlatform 提供 QMT 平台集成层。它从 `CnEquityStrategies` 加载策略配置，读取本地历史行情，并基于模拟投资组合评估目标权重。`QuantPlatformKit` 提供共享运行组件与策略契约，`QuantRuntimeSettings` 提供运行目标定义。

## 不适用范围

本仓库不实现策略研究，也不发布快照产物。它没有 miniQMT / QMT 券商连接。离线券商适配器对非 dry-run 的订单请求返回 `blocked`，不会将其报告为 `submitted`。

## 快速开始

需要 Python 3.11 或更高版本及 Git。在仓库根目录运行以下命令。安装包时会使用 `pyproject.toml` 声明的依赖版本。

```bash
python3 -m pip install -e '.[test]'
python3 -m pytest -q tests

python3 main.py
```

通过 `GET /profiles` 查看已停用的历史策略。目前没有策略能通过预检或运行 `/dry-run`；保留的行业 ETF smoke 脚本也会因策略退役而拒绝运行。

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

## 已退役策略

`cn_industry_etf_rotation` 和 `cn_industry_etf_rotation_aggressive` 均不可再选择，包括别名、环境变量及 `RUNTIME_TARGET_JSON` 入口。QMT 运行允许清单为空。历史定义和适配器供读取及隔离的契约测试使用，不赋予运行选择资格。

## 离线 paper-admission 检查

`--paper-admission` 目前会在配置检查时拒绝退役策略。下面保留的是具备选择资格时的离线检查契约：检查本地配置和固定输入文件。它要求 `QMT_EXECUTION_MODE=paper`、`QMT_DRY_RUN_ONLY=true`，且预先记录的 SHA-256 摘要与 `QMT_MARKET_HISTORY_PATH` 一致。

配置策略和输入路径后，将 `<expected-sha256>` 替换为预先记录的摘要：

```bash
export QMT_EXECUTION_MODE=paper
export QMT_DRY_RUN_ONLY=true
export QMT_PAPER_ADMISSION_INPUT_SHA256='<expected-sha256>'
python3 scripts/preflight_qmt_runtime.py --paper-admission
```

该命令加载策略契约并计算本地输入摘要，不调用 QMT SDK 或服务提供方，不读取凭据、创建订单或评估券商账户。这里的 `paper` 表示离线检查，不代表券商模拟交易连接。

## 已停用目标的生命周期验证

当前允许清单为空，保留的行业 ETF 目标会在预检失败并报告为 `attention`。工作日运行的 `Runtime Target Lifecycle` 工作流为固定的已停用目标执行确定性预检和基于样本的 dry-run，并发布 `disabled` / `dry_run` 状态。若周期已完成，但风控检查使目标权重为空，视为成功完成无订单检查；预检或 dry-run 失败则报告为 `attention`。这些报告不会修改目标设置、建立券商连接或提交订单。

## HTTP 接口

`main.create_app()` 创建独立的 Flask 应用，注册下表中的路由。现有的 `main.app` 导出继续供 WSGI 服务和本地入口使用；运行配置仍在每次请求时读取。

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
