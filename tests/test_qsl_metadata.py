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
    assert requires["quant_platform_kit"] == "54d4ba901ae4e72e09c143c051747b900de55022"
    assert requires["cn_equity_strategies"] == "3ee004e7e8c3f528c04ffb500d65fc401ce8e4ec"
