from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def load():
    p=ROOT/"analysis/w33_qutrit_frame_mu12_bundle_carrier.py"
    s=importlib.util.spec_from_file_location("mu12_frames",p)
    assert s and s.loader
    m=importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m

def test_objectwise_27_frame_mu12_bundle_carrier():
    o=load().main(False)
    assert o["status"]=="PASS_OBJECTWISE_27_FRAME_FIBREWISE_MU12_CARRIER"
    assert o["frame_Qpsi"]["roles"]=={"1":1,"10":10,"16":16}
    assert o["frame_Qpsi"]["phase_multiplicities"]=={"1":16,"4":1,"10":10}
    assert o["frame_Qpsi"]["D12_order"]==12
    assert o["bundle"]["total_direct_sum_dimension"]==243
    assert o["cubic_phase_conservation"]["all_phase_products_one"] is True
    assert o["single_C9_scalar_firewall"]["can_realize_relative_27_frame_phases"] is False
