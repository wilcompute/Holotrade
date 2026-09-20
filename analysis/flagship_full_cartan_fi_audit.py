"""Exact certificates for alternative component choices and the engine FI ray.
LP is a witness finder only; every published primal/dual equality is rationally checked.
Cartan feasibility is necessary, not sufficient, for a full D/F-flat vacuum.
"""
from pathlib import Path
import json, hashlib
import sympy as s
import numpy as np
from scipy.optimize import linprog
from flagship_singlet_invariant_audit import parse_weights
from w33_flagship_orbifolder_model import V,W3
ROOT=Path(__file__).resolve().parents[1]

def cert(A,b):
    lp=linprog(np.zeros(A.cols),A_eq=np.array(A,dtype=float),b_eq=np.array(b,dtype=float).ravel(),bounds=(0,None),method='highs')
    if lp.success:
        x=s.Matrix([s.Rational(str(v)).limit_denominator(10**7) for v in lp.x])
        assert A*x==b and all(v>=0 for v in x)
        return {'feasible':True,'primal':[str(v) for v in x]}
    assert lp.status==2,lp.message
    dual=linprog(np.zeros(A.rows),A_ub=np.vstack([-np.array(A.T,dtype=float),np.array(b.T,dtype=float)]),b_ub=np.r_[np.zeros(A.cols),-1],bounds=[(None,None)]*A.rows,method='highs')
    assert dual.success
    y=s.Matrix([s.Rational(str(v)).limit_denominator(10**7) for v in dual.x])
    assert all(v>=0 for v in A.T*y) and (b.T*y)[0]<0
    return {'feasible':False,'dual':[str(v) for v in y],'pairing':str((b.T*y)[0])}

def audit():
    raw=(ROOT/'analysis/flagship_fi_weights.txt').read_text()
    fields,_,_=parse_weights(raw)
    old,_,_=parse_weights((ROOT/'analysis/flagship_all_weights.txt').read_text());assert fields==old
    header=next(l.split() for l in raw.splitlines() if l.startswith('FI '))
    generators=[s.Matrix([s.Rational(x).limit_denominator(6) for x in l.split()[2:]]) for l in raw.splitlines() if l.startswith('U1 ')]
    assert len(generators)==7
    for l,g in zip([l for l in raw.splitlines() if l.startswith('U1 ')],generators):
        assert max(abs(float(a)-float(b)) for a,b in zip(l.split()[2:],g))<1e-10
    t=generators[0];assert header[1]=='1' and abs(float(header[2])-200)<1e-9
    assert t.dot(t)==s.Rational(50,3) and t.dot(generators[1])==0
    source=json.loads((ROOT/'analysis/flagship_minimal_projected_higgs_circuits.json').read_text())
    rows=[]
    for r in source['positive_full_rank_circuits']:
        cols=[(i,n,j,p) for i,options in enumerate(r['field_options_by_charge_type']) for n in options for j,p in enumerate(fields[n])]
        A=s.Matrix.hstack(*[s.Matrix(list(p)+[int(i==k) for k in range(5)]) for i,n,j,p in cols])
        b=s.Matrix([0]*16+r['primitive_squared_vev_ratios'])
        zero=cert(A,b)
        # Fixed type ratios and nonnegative FI coefficient eta: sum(6p*x)+6 eta*t=0.
        ray=cert(A.row_join(s.Matrix(list(6*t)+[0]*5)),b)
        rows.append({'representative_fields':r['representative_fields'],'columns':[[n,j] for i,n,j,p in cols],
                     'zero_FI':zero,'nonnegative_FI_ray':ray})
    labels=list(json.loads((ROOT/'analysis/flagship_singlet_invariant_audit.json').read_text())['extra_u1_higgs_rank_and_projected_D_flatness']['labels'])
    cols=[(n,j,p) for n in labels for j,p in enumerate(fields[n])]
    A=s.Matrix.hstack(*[s.Matrix(p) for n,j,p in cols])
    # Fix a positive unit on the FI ray; overall physical scale is deliberately unspecified.
    positive=cert(A,-6*t)
    normalized=cert(A.col_join(s.ones(1,A.cols)),s.Matrix([0]*16+[1]))
    singles=[n for n in labels if len(fields[n])==1]
    single_A=s.Matrix.hstack(*[s.Matrix(fields[n][0]) for n in singles])
    single_FI=cert(single_A,-6*t)
    assert not single_FI['feasible']
    # Check the stored sparse Cartan witness against one actual unbroken root.
    # A single active weight pair contributes to this root D term, so phases cannot cancel it.
    active={(n,j):s.Rational(v) for (n,j,p),v in zip(cols,positive['primal']) if s.Rational(v)>0}
    obstruction=None
    for (n,i),ti in active.items():
        for (m,j),tj in active.items():
            if m!=n or i==j:continue
            root=(s.Matrix(fields[n][i])-s.Matrix(fields[n][j]))/6
            if root.dot(root)!=2 or any(sum(a*b for a,b in zip(root,h)).q!=1 for h in (V,W3)):continue
            contributions=[(name,a,b) for name,a in active for other,b in active
                           if name==other and s.Matrix(fields[name][a])-s.Matrix(fields[name][b])==6*root]
            if len(contributions)==1:
                assert (s.Matrix(fields[n][j])/6).dot(root)==-1
                obstruction={'root':[str(v) for v in root],'only_active_transition':list(contributions[0]),
                             'squared_vev_product':str(ti*tj),'conclusion':'Nonzero root moment for every phase choice of this stored sparse Cartan witness; not a no-go for other mixtures.'}
                break
        if obstruction:break
    assert obstruction is not None
    organizer=json.loads((ROOT/'data/w33_flagship_a5_hypercharge_organizer.json').read_text())
    extra=s.Matrix(organizer['A5']['simple_roots_E8'])[1:,:]
    fi_projection=extra*t[8:,:];assert fi_projection!=s.zeros(4,1)
    return {'status':'PASS','source_sha256':hashlib.sha256(raw.encode()).hexdigest(),
            'FI_trace':200,'anomalous_generator':[str(x) for x in t],'generator_norm_squared':'50/3',
            'FI_equation':'sum_i p_i |v_i|^2 + eta t_A = 0; eta>0 is a dimensionless choice of ray scale, not a measured FI value',
            'circuits':rows,'all_singlet_columns':[[n,j] for n,j,p in cols],
            'single_component_fields':singles,'single_component_positive_FI':single_FI,
            'stored_positive_FI_nonabelian_obstruction':obstruction,
            'FI_projection_on_four_organizer_roots':[str(x) for x in fi_projection],
            'all_singlets_positive_FI':positive,'all_singlets_normalized_zero_FI':normalized,
            'scope':'All component mixtures of all alternative fields in each circuit. Full Cartan only; off-diagonal nonabelian D terms and F terms untested. The FI trace is not a dimensionful measurement.',
            'prior':'c555ac5 canonical representatives; babfd48 restricted mass-coupling singlets; these are different supports.'}
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();r=audit()
    if a.write:Path(__file__).with_suffix('.json').write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps({'circuits':len(r['circuits']),'zero_feasible':sum(x['zero_FI']['feasible'] for x in r['circuits']),'ray_feasible':sum(x['nonnegative_FI_ray']['feasible'] for x in r['circuits']),'all_positive_FI':r['all_singlets_positive_FI']['feasible'],'all_zero_FI':r['all_singlets_normalized_zero_FI']['feasible']}))
