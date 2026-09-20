import json,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'analysis'))
from flagship_singlet_invariant_audit import audit,parse_weights

def test_actual_weights_and_all_coupling_channels_replay():
    assert audit()==json.loads((ROOT/'analysis/flagship_singlet_invariant_audit.json').read_text())

def test_unreliable_rational_reconstruction_is_rejected():
    line='W n_1 k=4 n=0,0,0,0,0,0 q=0,0,0,0 osc=0 P='+','.join(['0.14285714285714285']+['0']*15)
    with pytest.raises(ValueError):parse_weights(line)

def test_minimal_positive_charge_circuits_replay():
    from flagship_minimal_projected_higgs_circuits import audit as circuits
    assert circuits()==json.loads((ROOT/'analysis/flagship_minimal_projected_higgs_circuits.json').read_text())
