"""Minimal positive rank-four circuits in the actual extra-U1 charge ledger.
Charge-type enumeration, not enumeration of physical vacua or nonabelian invariants.
"""
from pathlib import Path
from itertools import combinations
import json
import sympy as s
import numpy as np
from scipy.optimize import linprog
from flagship_singlet_invariant_audit import parse_weights
ROOT=Path(__file__).resolve().parents[1]

def audit():
    source=json.loads((ROOT/'analysis/flagship_singlet_invariant_audit.json').read_text())
    p=source['extra_u1_higgs_rank_and_projected_D_flatness'];types={}
    for label,q in zip(p['labels'],p['charges']):
        if any(s.Rational(x) for x in q):types.setdefault(tuple(q),[]).append(label)
    fields,_,_=parse_weights((ROOT/'analysis/flagship_all_weights.txt').read_text())
    keys=list(types);records=[]
    for inds in combinations(range(len(keys)),5):
        Q=s.Matrix([keys[i] for i in inds]);ns=Q.T.nullspace()
        if len(ns)!=1:continue
        v=ns[0]
        if not (all(x>0 for x in v) or all(x<0 for x in v)):continue
        v=v*s.ilcm(*[x.q for x in v]);v=v/s.igcd(*[int(x) for x in v]);v*=1 if v[0]>0 else -1
        assert Q.rank()==4 and Q.T*v==s.zeros(4,1)
        mass=Q.T*s.diag(*v)*Q;assert all(mass[:i,:i].det()>0 for i in range(1,5))
        labels=[types[keys[i]][0] for i in inds]
        columns=[(i,p) for i,n in enumerate(labels) for p in fields[n]]
        A=s.Matrix.hstack(*[s.Matrix(list(p)+[int(i==j) for j in range(5)]) for i,p in columns])
        b=s.Matrix([0]*16+list(v))
        # Farkas: A x=b, x>=0 impossible if A^T y>=0 and b^T y<0.
        lp=linprog(np.zeros(21),A_ub=np.vstack([-np.array(A.T,dtype=float),np.array(b.T,dtype=float)]),
                   b_ub=np.r_[np.zeros(A.cols),-1],bounds=[(None,None)]*21,method='highs')
        assert lp.success
        y=s.Matrix([s.Rational(str(x)).limit_denominator(100000) for x in lp.x])
        assert all(x>=0 for x in A.T*y) and (b.T*y)[0]<0
        records.append({'representative_fields':labels,
                        'full_zero_FI_Cartan_infeasibility':{'dual_vector':[str(x) for x in y],
                            'dual_target_pairing':str((b.T*y)[0]),
                            'proof':'A^T y >=0 but b^T y <0; A columns are scaled16Dweights and5field-total indicators',
                            'scope':'Canonical representative fields and their fixed positive ratios, allowing all component mixtures; not all alternative field choices or nonzero FI'},
                        'field_options_by_charge_type':[types[keys[i]] for i in inds],
                        'primitive_squared_vev_ratios':[int(x) for x in v],
                        'mass_gram_determinant':str(mass.det())})
    assert len(records)==14
    return {'status':'PASS','nonzero_charge_types':len(types),'five_type_subsets_checked':252,
            'positive_full_rank_circuits':records,'circuit_count':len(records),'minimal_support':5,
            'minimality_proof':'A rank-four charge matrix on at most four active fields has zero kernel; a positive zero-D vector requires a nonzero kernel. Exhibited five-field positive circuits attain the bound.',
            'scope':'Projected four-U1 zero-FI equations only. Choosing different physical fields with the same four charges can change hidden charges, localization and F terms; options are not interchangeable physical vacua.'}

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--write',action='store_true');a=ap.parse_args();r=audit()
    if a.write:Path(__file__).with_suffix('.json').write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps({'status':r['status'],'minimal_support':5,'circuits':r['circuit_count'],'first':r['positive_full_rank_circuits'][0]},indent=2))
