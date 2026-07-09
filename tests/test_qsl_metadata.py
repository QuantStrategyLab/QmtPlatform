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
    assert requires["quant_platform_kit"] == "69a0256934d081b5ef309a885384b9eb9f62cf90"
    assert requires["cn_equity_strategies"] == "12c0cd4801060fcb2f9452ffd9a7f48df446ddd0"
