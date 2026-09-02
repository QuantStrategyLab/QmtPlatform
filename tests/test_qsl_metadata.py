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
    assert requires["quant_platform_kit"] == "b13e28759a880dcb446dbfbc580dc032333b065e"
    assert requires["cn_equity_strategies"] == "9cb62eb34e16bb6dde300595b74f38a3b6a2d4c1"
