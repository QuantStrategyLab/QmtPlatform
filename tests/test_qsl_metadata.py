from __future__ import annotations

from pathlib import Path
import tomllib


def test_qsl_metadata_has_runtime_platform_fields() -> None:
    qsl_path = Path(__file__).resolve().parents[1] / "qsl.toml"
    with qsl_path.open("rb") as f:
        qsl = tomllib.load(f)["qsl"]

    assert qsl["tier"] == "runtime"
    assert qsl["upgrade_ring"] == "ring_d"
    assert qsl.get("repo") == "QmtPlatform"
    assert qsl["enforce_bundle"] is True
    assert qsl["compat"]["bundle"] == "2026.09.1"
    requires = qsl["requires"]
    assert requires["quant_platform_kit"] == "ac1d07c6b0188c8b0abc682e99315bdc056879b5"
    assert requires["cn_equity_strategies"] == "f54f71f4051293f38f0acb7b3b86b5bd5d20d899"
