import sys,json
from pathlib import Path
import sympy as s
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'analysis'))
from flagship_full_cartan_fi_audit import audit,cert
from flagship_singlet_invariant_audit import parse_weights
from flagship_joint_holonomy_tensors import audit as tensors
from flatness_scope_counterexamples import audit as scope

def verify(A,b,witness):
    if witness['feasible']:
        x=s.Matrix(witness['primal']);assert A*x==b and all(v>=0 for v in x)
    else:
        y=s.Matrix(witness['dual']);assert all(v>=0 for v in A.T*y) and (b.T*y)[0]<0

def test_stored_exact_certificates_and_alternative_union():
    r=json.loads((ROOT/'analysis/flagship_full_cartan_fi_audit.json').read_text())
    source=json.loads((ROOT/'analysis/flagship_minimal_projected_higgs_circuits.json').read_text())
    fields,_,_=parse_weights((ROOT/'analysis/flagship_fi_weights.txt').read_text());t=s.Matrix(r['anomalous_generator'])
    for row,old in zip(r['circuits'],source['positive_full_rank_circuits']):
        columns=[(i,n,j,p) for i,opts in enumerate(old['field_options_by_charge_type']) for n in opts for j,p in enumerate(fields[n])]
        assert row['columns']==[[n,j] for i,n,j,p in columns]
        A=s.Matrix.hstack(*[s.Matrix(list(p)+[int(i==k) for k in range(5)]) for i,n,j,p in columns]);b=s.Matrix([0]*16+old['primitive_squared_vev_ratios'])
        verify(A,b,row['zero_FI']);verify(A.row_join(s.Matrix(list(6*t)+[0]*5)),b,row['nonnegative_FI_ray'])
        assert not row['zero_FI']['feasible'] and not row['nonnegative_FI_ray']['feasible']
    A=s.Matrix.hstack(*[s.Matrix(fields[n][j]) for n,j in r['all_singlet_columns']])
    verify(A,-6*t,r['all_singlets_positive_FI'])
    verify(A.col_join(s.ones(1,A.cols)),s.Matrix([0]*16+[1]),r['all_singlets_normalized_zero_FI'])
    single=s.Matrix.hstack(*[s.Matrix(fields[n][0]) for n in r['single_component_fields']])
    assert len(r['single_component_fields'])==34
    verify(single,-6*t,r['single_component_positive_FI'])
    obs=r['stored_positive_FI_nonabelian_obstruction'];root=s.Matrix(obs['root']);n,i,j=obs['only_active_transition']
    assert (s.Matrix(fields[n][i])-s.Matrix(fields[n][j]))/6==root
    assert (s.Matrix(fields[n][j])/6).dot(root)==-1
    active={(n,j):s.Rational(v) for (n,j),v in zip(r['all_singlet_columns'],r['all_singlets_positive_FI']['primal']) if s.Rational(v)>0}
    transitions=[(n,i,j) for n,i in active for m,j in active if n==m and s.Matrix(fields[n][i])-s.Matrix(fields[n][j])==6*root]
    assert transitions==[tuple(obs['only_active_transition'])]
    fresh=audit();assert all(not x['nonnegative_FI_ray']['feasible'] for x in fresh['circuits'])
    assert fresh['all_singlets_positive_FI']['feasible']

def test_holonomy_tensors_and_counterexamples():
    assert tensors()==json.loads((ROOT/'analysis/flagship_joint_holonomy_tensors.json').read_text())
    assert scope()==json.loads((ROOT/'analysis/flatness_scope_counterexamples.json').read_text())

def test_dual_and_primal_paths_on_tiny_cones():
    A=s.Matrix([[1,1]]);assert not cert(A,s.Matrix([-1]))['feasible']
    assert cert(A,s.Matrix([1]))['feasible']
