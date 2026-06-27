# QmtPlatform

A-share quant platform layer for **miniQMT / QMT**, built on `QuantPlatformKit` and `CnEquityStrategies`.

Current scope is **dry-run first**: evaluate strategy targets and preview orders without submitting to the broker.

## Supported profiles (P0)

| Profile | Input mode |
|---|---|
| `cn_index_etf_tactical_rotation` | `market_history` |
| `cn_dividend_quality_snapshot` | `feature_snapshot` (requires snapshot path) |

## Quick start

### ETF tactical rotation (market history)

```bash
python3 -m pip install -e '.[test]'
python3 -m pip install --no-deps -e ../QuantPlatformKit ../CnEquityStrategies

export STRATEGY_PROFILE=cn_index_etf_tactical_rotation
export QMT_DRY_RUN_ONLY=true
export QMT_MARKET_HISTORY_PATH=data/fixtures/market_history.sample.csv

python3 main.py
curl http://127.0.0.1:8080/probe
curl http://127.0.0.1:8080/dry-run
```

### Dividend quality snapshot (feature snapshot)

```bash
python3 -m pip install --no-deps -e ../CnEquitySnapshotPipelines

# Regenerate fixtures (uses sample factor CSV; sets as_of to today)
python3 scripts/build_fixtures.py

export STRATEGY_PROFILE=cn_dividend_quality_snapshot
export QMT_DRY_RUN_ONLY=true
export QMT_FEATURE_SNAPSHOT_PATH=data/fixtures/dividend_quality/cn_dividend_quality_snapshot_factor_snapshot_latest.csv
export QMT_FEATURE_SNAPSHOT_MANIFEST_PATH=data/fixtures/dividend_quality/cn_dividend_quality_snapshot_factor_snapshot_latest.csv.manifest.json

python3 main.py
curl http://127.0.0.1:8080/dry-run
```

End-to-end smoke (stage/build/run):

```bash
python3 scripts/smoke_cn_dividend_quality_dry_run_e2e.py
```

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `QMT_DRY_RUN_ONLY` | `true` | When true, never submit live orders |
| `STRATEGY_PROFILE` | required | Strategy profile id |
| `QMT_MARKET_HISTORY_PATH` | — | CSV with `date,symbol,close` for direct strategies |
| `QMT_FEATURE_SNAPSHOT_PATH` | — | Snapshot CSV for feature-snapshot strategies |
| `QMT_FEATURE_SNAPSHOT_MANIFEST_PATH` | — | Snapshot manifest JSON (required for dividend quality) |
| `RUNTIME_TARGET_JSON` | — | Optional runtime target override from QuantRuntimeSettings |

See `.env.example` and `CnEquityStrategies/docs/platform_integration.md`.

## HTTP endpoints

- `GET /probe` — health + active profile
- `GET /profiles` — platform profile matrix
- `GET|POST /dry-run` — evaluate strategy and return target weights + order previews

## Related repositories

- [CnEquityStrategies](https://github.com/QuantStrategyLab/CnEquityStrategies)
- [CnEquitySnapshotPipelines](https://github.com/QuantStrategyLab/CnEquitySnapshotPipelines)
- [QuantRuntimeSettings](https://github.com/QuantStrategyLab/QuantRuntimeSettings)
