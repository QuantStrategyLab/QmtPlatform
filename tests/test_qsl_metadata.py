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
    assert requires["quant_platform_kit"] == "be45863ad75316e3c993338828da356ddfb42f65"
    assert requires["cn_equity_strategies"] == "38c0360a4e98aa4851280a90dc1d42a18b256e8f"
