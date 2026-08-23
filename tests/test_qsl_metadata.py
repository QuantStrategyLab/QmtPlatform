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
    assert requires["quant_platform_kit"] == "68fcad8c68ab48a1109d99715f8315af449de493"
    assert requires["cn_equity_strategies"] == "33d605622ded78a006efef4297b7e786cadf1a27"
