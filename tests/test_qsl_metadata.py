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
    assert requires["quant_platform_kit"] == "e7d8659ef5b8f66660ea58f58202735fa3508cc1"
    assert requires["cn_equity_strategies"] == "45970d5ccad0cecb97bea739c635078fa9aff1e1"
