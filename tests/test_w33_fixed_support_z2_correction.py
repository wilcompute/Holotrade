from __future__ import annotations
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_fixed_support_zero_is_not_z2():
    p=ROOT/"analysis/w33_fixed_support_z2_correction.py"
    s=importlib.util.spec_from_file_location("fixz2",p);assert s and s.loader
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    o=m.main(False)
    assert o["status"]=="CORRECTION_FIXED_SUPPORT_0_OF_24_IS_FULL_U1_NOT_Z2_EVIDENCE"
    assert o["legacy_result"]["reported_successes"]==0
    assert o["toy_separation"]=={"three_B_minus_L":2,"matter_even":True,"full_U1_neutral":False}
    assert o["checks"]["sampled_search_uses_even_integrality"] is True
