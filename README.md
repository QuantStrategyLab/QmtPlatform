# QmtPlatform

English | [简体中文](README.zh-CN.md)

A-share quant platform layer for miniQMT / QMT, built on `QuantPlatformKit` and `CnEquityStrategies`.

## Status

Experimental. The current implementation evaluates strategies offline and previews orders. This project is not financial advice and does not guarantee any trading result.

## What this is

QmtPlatform provides the QMT platform integration layer. It loads strategy profiles from `CnEquityStrategies`, reads local market-history inputs, and evaluates target weights against a synthetic portfolio. `QuantPlatformKit` supplies shared runtime and strategy contracts; `QuantRuntimeSettings` supplies runtime target definitions.

## What this is not

This repository does not implement strategy research or publish snapshot artifacts. It has no miniQMT / QMT broker connection. The offline broker adapter returns `blocked` for non-dry-run order requests and never reports them as `submitted`.

## Quick start

Requirements: Python 3.11 or later and Git. Run these commands from the repository root. The package installation resolves the dependency revisions declared in `pyproject.toml`.

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

In another terminal, query the local service:

```bash
curl http://127.0.0.1:8080/probe
curl http://127.0.0.1:8080/profiles
curl http://127.0.0.1:8080/dry-run
```

The fixture-backed smoke scripts run a local strategy cycle without starting the HTTP service:

```bash
python3 scripts/smoke_cn_industry_etf_rotation_dry_run_e2e.py
python3 scripts/smoke_cn_industry_etf_rotation_aggressive_dry_run_e2e.py
```

## Configuration

Use [`.env.example`](.env.example) as the dry-run configuration reference. Export its values in your shell; the entrypoint reads environment variables. The preflight command validates the selected profile and required input paths without accessing broker credentials.

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `STRATEGY_PROFILE` | Unless `RUNTIME_TARGET_JSON` is set | none | QMT-enabled strategy profile ID. |
| `QMT_DRY_RUN_ONLY` | No | `true` | Keep `true`; preflight rejects `false`, and the HTTP dry-run endpoint always uses dry-run settings. |
| `QMT_EXECUTION_MODE` | No | `dry_run` | Set to `paper` only for offline paper admission; this value does not create a broker connection. |
| `QMT_PAPER_ADMISSION_INPUT_SHA256` | For `--paper-admission` | none | Pre-recorded SHA-256 digest of the fixed market-history input. |
| `QMT_MARKET_HISTORY_PATH` | For market-history profiles | none | Local CSV path with `date,symbol,close` columns. |
| `RUNTIME_TARGET_JSON` | No | none | JSON runtime target from `QuantRuntimeSettings`; takes precedence over `STRATEGY_PROFILE`. |
| `PORT` | No | `8080` | HTTP port; the Flask entrypoint binds to `0.0.0.0`. |

## Supported dry-run profiles

| Profile | Input mode | Role |
|---|---|---|
| `cn_industry_etf_rotation` | `market_history` | Primary profile. |
| `cn_industry_etf_rotation_aggressive` | `market_history` | Optional profile with a 25% volatility target. |

Set `STRATEGY_PROFILE=cn_industry_etf_rotation_aggressive` to select the optional profile when `RUNTIME_TARGET_JSON` is unset. The QMT target layout is documented in [QuantRuntimeSettings](https://github.com/QuantStrategyLab/QuantRuntimeSettings/blob/main/examples/targets/qmt/README.md).

Profile availability follows the `CnEquityStrategies` catalog and QMT rollout allowlist. Research-only profiles such as `cn_dividend_quality_snapshot` and `cn_index_etf_tactical_rotation` are rejected by the QMT runtime policy.

## Offline paper admission

`--paper-admission` checks a local configuration and fixed input file. It requires `QMT_EXECUTION_MODE=paper`, `QMT_DRY_RUN_ONLY=true`, and a pre-recorded SHA-256 digest matching `QMT_MARKET_HISTORY_PATH`.

After configuring the profile and input path, replace `<expected-sha256>` with that recorded digest:

```bash
export QMT_EXECUTION_MODE=paper
export QMT_DRY_RUN_ONLY=true
export QMT_PAPER_ADMISSION_INPUT_SHA256='<expected-sha256>'
python3 scripts/preflight_qmt_runtime.py --paper-admission
```

The command loads the strategy contract and hashes the local input. It does not call a QMT SDK or provider, read credentials, create orders, or evaluate a broker account. The word `paper` here names an offline check, not a broker paper-trading connection.

## Disabled-target lifecycle validation

The weekday `Runtime Target Lifecycle` workflow runs deterministic preflight and a fixture-backed dry-run for a fixed disabled target. It publishes `disabled` / `dry_run` status. A completed cycle whose target weights are empty because of the risk gate is a successful no-order check; a preflight or dry-run failure is reported as `attention`. These reports do not change target settings, establish a broker connection, or submit orders.

## HTTP endpoints

| Method | Path | Response |
|---|---|---|
| `GET` | `/probe` | Health, active profile, and dry-run setting. |
| `GET` | `/profiles` | Platform profile matrix. |
| `GET`, `POST` | `/dry-run` | Strategy target weights and order previews using local inputs. |

## Related repositories

- [QuantPlatformKit](https://github.com/QuantStrategyLab/QuantPlatformKit)
- [CnEquityStrategies](https://github.com/QuantStrategyLab/CnEquityStrategies)
- [CnEquitySnapshotPipelines](https://github.com/QuantStrategyLab/CnEquitySnapshotPipelines)
- [QuantRuntimeSettings](https://github.com/QuantStrategyLab/QuantRuntimeSettings)

## Repository layout

```text
application/    offline broker adapter and dry-run cycle
data/fixtures/  sample market-history and snapshot inputs
scripts/        preflight and local smoke commands
tests/          automated tests
main.py         Flask HTTP entrypoint
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). AI assistants and maintainers also follow [AGENTS.md](AGENTS.md). Documentation follows the [QuantStrategyLab documentation style guide](https://github.com/QuantStrategyLab/.github/blob/main/docs/STYLE_GUIDE.md).

## Security

See [SECURITY.md](SECURITY.md) for private vulnerability reporting. Do not put credentials or account identifiers in issues, examples, or logs.

## License

[MIT](LICENSE).
