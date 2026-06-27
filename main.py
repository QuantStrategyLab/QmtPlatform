"""Cloud Run / local entrypoint for QMT platform dry-run cycles."""

from __future__ import annotations

import os
import traceback

from flask import Flask, jsonify

from application.dry_run_service import run_dry_run_cycle
from application.qmt_client import QmtBrokerClient
from runtime_config_support import load_platform_runtime_settings
from strategy_registry import get_platform_profile_status_matrix

app = Flask(__name__)


@app.get("/probe")
def probe():
    settings = load_platform_runtime_settings()
    return jsonify(
        {
            "status": "ok",
            "platform_id": "qmt",
            "strategy_profile": settings.strategy_profile,
            "dry_run_only": settings.dry_run_only,
        }
    )


@app.get("/profiles")
def profiles():
    return jsonify({"profiles": get_platform_profile_status_matrix()})


@app.route("/dry-run", methods=["GET", "POST"])
def dry_run():
    settings = load_platform_runtime_settings()
    effective_settings = settings
    if not settings.dry_run_only:
        effective_settings = settings.__class__(
            **{
                **settings.__dict__,
                "dry_run_only": True,
            }
        )
    try:
        client = QmtBrokerClient(
            market_history_path=effective_settings.market_history_path
            or os.getenv("QMT_MARKET_HISTORY_PATH"),
        )
        report = run_dry_run_cycle(runtime_settings=effective_settings, client=client)
        return jsonify(report)
    except Exception as exc:
        return jsonify({"status": "error", "error": str(exc), "traceback": traceback.format_exc()}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
