# QmtPlatform


## QSL architecture role

- **Layer**: `runtime-platform`.
- **Responsibility**: QMT / miniQMT A-share execution runtime.
- **Owns**: QMT runtime controls and A-share platform integration.
- **Consumes**: CnEquityStrategies, QuantPlatformKit, QuantRuntimeSettings, market-history inputs.
- **Must not**: own strategy research logic or publish snapshot artifacts.

A-share quant platform layer for **miniQMT / QMT**, built on `QuantPlatformKit` and `CnEquityStrategies`.

Current scope is **dry-run first**: evaluate strategy targets and preview orders without submitting to the broker.

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
| `QMT_DRY_RUN_ONLY` | `true` | When true, never submit live orders |
| `STRATEGY_PROFILE` | required | QMT-enabled strategy profile id |
| `QMT_MARKET_HISTORY_PATH` | — | CSV with `date,symbol,close` for direct strategies |
| `RUNTIME_TARGET_JSON` | — | Optional runtime target override from QuantRuntimeSettings |

Use `.env.example` as the dry-run configuration template. Run `python3 scripts/preflight_qmt_runtime.py` before starting the service; it validates the selected profile and required input paths without touching any live account credentials.

## HTTP endpoints

- `GET /probe` — health + active profile
- `GET /profiles` — platform profile matrix
- `GET|POST /dry-run` — evaluate strategy and return target weights + order previews

## Related repositories

- [CnEquityStrategies](https://github.com/QuantStrategyLab/CnEquityStrategies)
- [CnEquitySnapshotPipelines](https://github.com/QuantStrategyLab/CnEquitySnapshotPipelines)
- [QuantRuntimeSettings](https://github.com/QuantStrategyLab/QuantRuntimeSettings)
