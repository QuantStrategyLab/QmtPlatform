from __future__ import annotations

from pathlib import Path
import tomllib


def test_qsl_metadata_has_runtime_platform_fields() -> None:
    qsl_path = Path(__file__).resolve().parents[1] / "qsl.toml"
    with qsl_path.open("rb") as f:
        qsl = tomllib.load(f)["qsl"]

    assert qsl["tier"] == "runtime-platform"
    assert qsl["ring"] == 3
    assert qsl.get("repo") == "QmtPlatform"
    assert qsl["enforce_bundle"] is True
    assert qsl["compat"]["bundle"] == "2026.07.2"
    requires = qsl["requires"]
    assert requires["quant_platform_kit"] == "37c81901160c5b31127a27dba1c63944933fb6bf"
    assert requires["cn_equity_strategies"] == "73844e92a8570a61e5a9dc6c245809d0b27b89bc"
