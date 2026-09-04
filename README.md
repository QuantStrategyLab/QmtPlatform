# QmtPlatform


## QSL architecture role

- **Layer**: `runtime-platform`.
- **Responsibility**: QMT / miniQMT A-share execution runtime.
- **Owns**: QMT runtime controls and A-share platform integration.
- **Consumes**: CnEquityStrategies, QuantPlatformKit, QuantRuntimeSettings, market-history inputs.
- **Must not**: own strategy research logic or publish snapshot artifacts.

A-share quant platform layer for **miniQMT / QMT**, built on `QuantPlatformKit` and `CnEquityStrategies`.

Current scope is **offline dry-run only**: evaluate strategy targets and preview orders without submitting to the broker. This repository is not a shadow/live runtime; any non-dry-run order request is rejected as `blocked` and is never reported as `submitted`.

## Offline paper admission (not broker paper)

`--paper-admission` is a deterministic local configuration gate, not a miniQMT/QMT paper account connection. It requires all of the following:

- `QMT_EXECUTION_MODE=paper`;
- `QMT_DRY_RUN_ONLY=true`;
- a pre-recorded SHA-256 digest matching the fixed `QMT_MARKET_HISTORY_PATH` input.

It only loads the strategy contract and hashes the local input. It does not call a QMT SDK/provider, read credentials, create orders, evaluate a broker account, or make this repository broker-paper or live ready.

```bash
export QMT_EXECUTION_MODE=paper
export QMT_DRY_RUN_ONLY=true
export QMT_PAPER_ADMISSION_INPUT_SHA256=5612a923290ed9fb779ce39613c5ea875ee68f69bf2aade0358761f2b86b3afb
python3 scripts/preflight_qmt_runtime.py --paper-admission
```

## Supported dry-run profiles

| Profile | Input mode |
|---|---|
| `cn_industry_etf_rotation` | `market_history` (**主轨，runtime_enabled**) |
| `cn_industry_etf_rotation_aggressive` | `market_history` (**optional target，live_candidate**) |

Research-only profiles such as `cn_dividend_quality_snapshot` and `cn_index_etf_tactical_rotation` are intentionally rejected by QMT runtime settings until they are promoted in `CnEquityStrategies`.

## Quick start

### Industry ETF rotation (market history, primary)

```bash
python3 -m pip install -e '.[test]'
python3 -m pip install --no-deps -e ../QuantPlatformKit ../CnEquityStrategies

export STRATEGY_PROFILE=cn_industry_etf_rotation
export QMT_DRY_RUN_ONLY=true
export QMT_MARKET_HISTORY_PATH=data/fixtures/market_history.sample.csv

python3 scripts/preflight_qmt_runtime.py
python3 main.py
curl http://127.0.0.1:8080/probe
curl http://127.0.0.1:8080/dry-run
```

### Industry ETF rotation aggressive (optional second target, vol25%)

```bash
export STRATEGY_PROFILE=cn_industry_etf_rotation_aggressive
export QMT_DRY_RUN_ONLY=true
export QMT_MARKET_HISTORY_PATH=data/fixtures/market_history.sample.csv

python3 main.py
curl http://127.0.0.1:8080/dry-run
```

Runtime target example: `QuantRuntimeSettings/examples/targets/qmt/industry_etf_aggressive_dry_run.example.json`

End-to-end smoke (stage/build/run):

```bash
python3 scripts/smoke_cn_industry_etf_rotation_dry_run_e2e.py
python3 scripts/smoke_cn_industry_etf_rotation_aggressive_dry_run_e2e.py
```

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `QMT_DRY_RUN_ONLY` | `true` | Offline-only guard; non-dry-run requests remain blocked |
| `QMT_EXECUTION_MODE` | `dry_run` | Must be `paper` for offline paper admission; it never enables a broker connection |
| `QMT_PAPER_ADMISSION_INPUT_SHA256` | — | Required only for `--paper-admission`; pre-recorded digest of the fixed market-history input |
| `STRATEGY_PROFILE` | required | QMT-enabled strategy profile id |
| `QMT_MARKET_HISTORY_PATH` | — | CSV with `date,symbol,close` for direct strategies |
| `RUNTIME_TARGET_JSON` | — | Optional runtime target override from QuantRuntimeSettings |

Use `.env.example` as the dry-run configuration template. Run `python3 scripts/preflight_qmt_runtime.py` before starting the service; it validates the selected profile and required input paths without touching any live account credentials.

## Disabled-target lifecycle validation

QMT has no configured broker runtime or live credentials. The weekday `Runtime Target Lifecycle` workflow therefore runs only the deterministic preflight and fixture-backed dry-run smoke, then publishes a sanitized central status of `disabled` / `dry_run`. A completed dry-run with weights blocked by the deterministic risk gate is also a passing no-order validation: the platform and its safety boundary both worked. It does **not** mean that QMT is deployed, connected to miniQMT, paper-enabled, or live-enabled. A preflight or dry-run failure is published as `attention`; no status can change the target state or submit an order.

## HTTP endpoints

- `GET /probe` — health + active profile
- `GET /profiles` — platform profile matrix
- `GET|POST /dry-run` — evaluate strategy and return target weights + order previews

## Related repositories

- [CnEquityStrategies](https://github.com/QuantStrategyLab/CnEquityStrategies)
- [CnEquitySnapshotPipelines](https://github.com/QuantStrategyLab/CnEquitySnapshotPipelines)
- [QuantRuntimeSettings](https://github.com/QuantStrategyLab/QuantRuntimeSettings)
