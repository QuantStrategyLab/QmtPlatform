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
    assert qsl["compat"]["bundle"] == "2026.07.3"
    requires = qsl["requires"]
    assert requires["quant_platform_kit"] == "3b74a445b370745fcb7bc380b4f37e9bf2f7cf56"
    assert requires["cn_equity_strategies"] == "48f9823a16da8e45b5c58c19ef77b0db4aa084f4"
