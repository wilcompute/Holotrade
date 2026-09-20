"""Replay actual projected singlet weights and necessary coupling invariants.
No identification of necessary lattice neutrality with a nonzero CFT amplitude.
"""
from pathlib import Path
from fractions import Fraction
from itertools import product
from collections import defaultdict,Counter
import json,hashlib,re
import sympy as sp
import numpy as np
from scipy.optimize import linprog
from local_nine_spurion_algebra import audit as local_audit
ROOT=Path(__file__).resolve().parents[1]


def parse_weights(text):
    fields=defaultdict(list);meta={};error=0.0
    for line in text.splitlines():
        if not line.startswith('W '):continue
        m=re.fullmatch(r'W (\S+) k=(\d+) n=(\S+) q=(\S+) osc=(\d+) P=(\S+)',line)
        assert m is not None
        label,k,n,q,osc,p=m.groups();raw=[Fraction(x) for x in p.split(',')]
        scaled=tuple(round(6*x) for x in raw)
        err=max(abs(float(x-Fraction(y,6))) for x,y in zip(raw,scaled));error=max(error,err)
        if len(scaled)!=16 or err>1e-12:raise ValueError('momentum not a reliable sixth-denominator reconstruction')
        fields[label].append(scaled);meta[label]={'sector':int(k),'fixed_point':[str(Fraction(x)) for x in n.split(',')],'oscillators':int(osc)}
    return fields,meta,error


def audit():
    path=ROOT/'analysis/flagship_all_weights.txt';fields,meta,error=parse_weights(path.read_text())
    parent=local_audit();W=[tuple(w) for w in parent['weights_scale_6']]
    singlets={n:ps for n,ps in fields.items() if n.startswith('n_')}
    simples=[tuple(a-b for a,b in zip(W[i],W[i+1])) for i in range(4)]
    dot=lambda a,b:sum(x*y for x,y in zip(a,b))
    assert all(dot(p,r)==0 for ps in singlets.values() for p in ps for r in simples)
    expected=['n_14','n_15','n_16','n_17'];assert {fields[n][0] for n in expected}==set(W[5:])
    assert all(meta[n]['sector']==4 and meta[n]['fixed_point']==['-1','1','0','0','0','0'] for n in expected)
    X=sp.Matrix(9,9,sp.symbols('x:81')); equations=[]
    for i in range(8):
        for a,b in ((i,i+1),(i+1,i)):
            E=sp.zeros(9);E[a,b]=1;equations.extend(list(E*X-X*E))
    constraint,_=sp.linear_eq_to_matrix(equations,list(X))
    invariant_dimension=81-constraint.rank();assert invariant_dimension==1
    inputs=json.loads((ROOT/'analysis/flagship_singlet_coupling_inputs.json').read_text())
    records={}
    for kind in ('mu','triplet'):
        rows=[]
        for line in inputs[kind]:
            if not line.startswith('C '):continue
            tokens=line.split();degree=int(tokens[1]);labels=tokens[2:];assert len(labels)==degree
            channels=[]
            for ps in product(*(fields[n] for n in labels)):
                if all(sum(p[j] for p in ps)==0 for j in range(16)):
                    channels.append([fields[n].index(p) for n,p in zip(labels,ps)])
            assert channels, (kind,line)
            rows.append({'labels':labels,'degree':degree,'neutral_weight_channels':channels})
        records[kind]=rows
    organizer=json.loads((ROOT/'data/w33_flagship_a5_hypercharge_organizer.json').read_text())
    extra=sp.Matrix(organizer['A5']['simple_roots_E8'])[1:,:]
    hyper=sp.Matrix([organizer['hypercharge']['Y']])
    selected=sp.Matrix(simples)[:,8:]/6
    assert selected*extra.T==sp.zeros(4)
    labels=sorted(singlets,key=lambda n:int(n.split('_')[1]));charge_rows=[]
    for n in labels:
        qs=[extra*sp.Matrix(p[8:])/6 for p in singlets[n]]
        assert all(q==qs[0] for q in qs)
        assert all((hyper*sp.Matrix(p[8:]))[0]==0 for p in singlets[n])
        charge_rows.append(list(qs[0]))
    Q=sp.Matrix(charge_rows);pivots=Q.T.rref()[1];assert Q.rank()==4
    n=len(labels)
    equality=np.vstack([np.column_stack([np.array(Q.T,dtype=float),np.zeros(4)]),np.r_[np.ones(n),0]])
    lp=linprog(np.r_[np.zeros(n),-1],A_ub=np.column_stack([-np.eye(n),np.ones(n)]),b_ub=np.zeros(n),
               A_eq=equality,b_eq=[0,0,0,0,1],bounds=[(0,None)]*(n+1),method='highs')
    assert lp.success and lp.x[-1]>0
    # Freeze the discovered rational witness; LP basis choices must not change replay output.
    special={'n_32':sp.Rational(19,100),'n_42':sp.Rational(3,20),'n_60':sp.Rational(1,25)}
    vevs=sp.Matrix([special.get(label,sp.Rational(1,100)) for label in labels])
    assert Q.T*vevs==sp.zeros(4,1) and sum(vevs)==1 and min(vevs)>0
    mass=Q.T*sp.diag(*vevs)*Q
    minors=[mass[:i,:i].det() for i in range(1,5)];assert all(x>0 for x in minors)
    center={'labels':labels,'charges':[[str(x) for x in row] for row in charge_rows],
            'rank':4,'independent_fields':[labels[i] for i in pivots],
            'positive_vev_squared_weights':[str(x) for x in vevs],
            'minimum_vev_squared_weight':str(min(vevs)),
            'gram_mass_matrix':[[str(x) for x in mass.row(i)] for i in range(4)],
            'positive_leading_principal_minors':[str(x) for x in minors],
            'selected_nonabelian_A4_orthogonal_to_extra_u1_A4':True,
            'scope':'All65 singlet fields, hypercharge zero; positive solution only of four extra-U1 zero-FI D equations. Other D terms, FI terms, F terms and CFT amplitudes not solved.'}
    # One exact local fundamental invariant is delta, whose two visible blocks agree.
    # E_ij X = X E_ij for all matrix units forces X scalar on the nine.
    # This test is local and does not assume bulk/Wilson-line-dressed invariants reduce to it.
    return {'status':'PASS','weight_rows':sum(map(len,fields.values())), 'field_count':len(fields),
            'singlet_fields':len(singlets),'singlet_weight_rows':sum(map(len,singlets.values())),
            'all_singlet_selected_A4_Cartan_charges_zero':True,
            'co_local_extra_fundamental_fields':expected,'local_fundamental_bilinear_invariant_dimension':invariant_dimension,
            'co_local_branching':'9 -> 5 + 1 + 1 + 1 + 1 under the selected A4',
            'extra_u1_higgs_rank_and_projected_D_flatness':center,
            'coupling_counts':{k:len(v) for k,v in records.items()},'couplings':records,
            'maximum_reconstruction_error':error,'weight_dump_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'scope':'Actual one-model projected weights and cached order<=5 selection-rule couplings; momentum neutrality is necessary, not a CFT amplitude or all-vacuum splitting no-go.'}

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--write',action='store_true');a=ap.parse_args();r=audit()
    if a.write:Path(__file__).with_suffix('.json').write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps({k:v for k,v in r.items() if k!='couplings'},indent=2))
