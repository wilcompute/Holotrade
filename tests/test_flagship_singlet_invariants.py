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
    import sympy as s
    actual=circuits();stored=json.loads((ROOT/'analysis/flagship_minimal_projected_higgs_circuits.json').read_text())
    fields,_,_=parse_weights((ROOT/'analysis/flagship_all_weights.txt').read_text())
    for r in stored['positive_full_rank_circuits']:
        columns=[(i,p) for i,n in enumerate(r['representative_fields']) for p in fields[n]]
        A=s.Matrix.hstack(*[s.Matrix(list(p)+[int(i==j) for j in range(5)]) for i,p in columns])
        b=s.Matrix([0]*16+r['primitive_squared_vev_ratios'])
        y=s.Matrix(r['full_zero_FI_Cartan_infeasibility']['dual_vector'])
        assert all(x>=0 for x in A.T*y) and (b.T*y)[0]<0
    # A valid Farkas witness need not be the same LP vertex across solver versions.
    for payload in (actual,stored):
        for r in payload['positive_full_rank_circuits']:
            r['full_zero_FI_Cartan_infeasibility'].pop('dual_vector')
            r['full_zero_FI_Cartan_infeasibility'].pop('dual_target_pairing')
    assert actual==stored
