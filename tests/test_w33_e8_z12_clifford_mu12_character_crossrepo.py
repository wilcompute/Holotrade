from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_e8_z12_clifford_mu12_character_crossrepo():
    o=json.loads((ROOT/"data/w33_e8_z12_clifford_mu12_character_crossrepo.json").read_text())
    assert o["status"]=="PASS_CROSSREPO_E8_Z12_TO_CLIFFORD_MU12_CHARACTER"
    assert any("faithful" in x for x in o["admit"])
    assert any("intertwiner" in x for x in o["block"])
    assert any("D/F-flat" in x for x in o["block"])
