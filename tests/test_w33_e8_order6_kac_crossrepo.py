from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_twin_order6_kac_crossrepo_admission():
    o=json.loads((ROOT/"data/w33_e8_order6_kac_crossrepo.json").read_text())
    assert o["status"]=="PASS_CROSSREPO_TWIN_ORDER6_E8_KAC_CLASSIFICATION"
    assert o["admit"]["structural_FI_x_matter_parity_Z6"]["kac_coordinates"]==[2,0,0,0,1,0,0,0,0]
    assert o["admit"]["flagship_holonomy_Z6"]["kac_coordinates"]==[0,0,0,0,1,0,0,1,0]
    assert o["admit"]["common_cube"].startswith("Both cubes are the D8")
    assert any("D/F-flat" in x for x in o["block"])
    assert any("0/24" in x for x in o["block"])
