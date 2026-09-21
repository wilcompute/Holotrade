from __future__ import annotations
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"analysis/w33_qutrit_frame_matter_parity_cubic_bridge.py"
def load():
    spec=importlib.util.spec_from_file_location("mpframes",SRC);assert spec and spec.loader
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def test_qutrit_frame_matter_parity_cubic_bridge():
    out=load().main(False)
    assert out["status"]=="PASS_OBJECTWISE_QUTRIT_MATTER_PARITY_AND_CUBIC_BRIDGE"
    assert out["frame_partition"]["matter_odd"]==16
    assert out["tritangent_cubic_census"]["by_SO10_roles"]=={"1+10+10":5,"10+16+16":40}
    assert out["tritangent_cubic_census"]["by_Qpsi"]=={"-2,-2,4":5,"-2,1,1":40}
    assert out["tritangent_cubic_census"]["all_matter_parity_even"] is True
