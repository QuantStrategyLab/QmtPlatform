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
    assert requires["quant_platform_kit"] == "c7646a7168b3dafa763ef7751a182d23e8de7790"
    assert requires["cn_equity_strategies"] == "4a4ff37b068c0012ccb57f52486d1c6745cf113d"
