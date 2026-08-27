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
    assert requires["quant_platform_kit"] == "0f1b5d9e806b1143b459976b8a6a98eee7a9bc37"
    assert requires["cn_equity_strategies"] == "beecdc9a894a289b625abe0199aa55b5ef5d8fc2"
