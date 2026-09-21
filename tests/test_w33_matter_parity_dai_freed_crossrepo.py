from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_crossrepo_matter_parity_anomaly_firewall():
    o=json.loads((ROOT/"data/w33_matter_parity_dai_freed_crossrepo.json").read_text())
    assert o["status"]=="PASS_CROSSREPO_MATTER_PARITY_ANOMALY_FIREWALL"
    assert o["w33SourceCommit"]=="5e0f8aa0ab0f044efe87b3cc899b640412cfa320"
    assert any("Z4_X" in x for x in o["block"])
    assert any("vacuum" in x for x in o["block"])
