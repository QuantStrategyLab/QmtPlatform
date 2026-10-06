# Contributing

Thanks for contributing to `QmtPlatform`.

## Ground Rules

- Prefer small, low-risk pull requests.
- Keep refactors separate from behavior changes.
- Add or update tests when changing runtime behavior.
- Do not use the scheduled `Runtime Target Lifecycle` workflow as a substitute for local verification; it runs a fixed, disabled dry-run target and is not a place to debug changes.
- This repository is **offline dry-run only**: any change touching order submission, the dry-run/paper-admission boundary, or the `QMT_EXECUTION_MODE` / `QMT_DRY_RUN_ONLY` guards must be verified locally with the preflight script, the test suite, and a dry-run smoke script before merging. A worked example or a green CI run on a disabled target is not proof that the safety boundary still holds — check it directly.

## Branching and Pull Requests

- Create a topic branch for each change.
- Open a pull request with a short summary and a concrete test plan.
- Wait for CI to pass before merging.

## Local Verification

```bash
python3 -m pip install -e '.[test]'
python3 -m pip install --no-deps -e ../QuantPlatformKit ../CnEquityStrategies

python3 -m ruff check .
PYTHONPATH=. PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q tests
```

For changes touching the QMT runtime guards or strategy profiles, also run the relevant dry-run preflight and smoke scripts, e.g.:

```bash
export QMT_DRY_RUN_ONLY=true
export STRATEGY_PROFILE=cn_industry_etf_rotation
export QMT_MARKET_HISTORY_PATH=data/fixtures/market_history.sample.csv

python3 scripts/preflight_qmt_runtime.py
python3 scripts/smoke_cn_industry_etf_rotation_dry_run_e2e.py
```

See `README.md` for the full list of supported profiles, environment variables, and the offline paper-admission flow.
