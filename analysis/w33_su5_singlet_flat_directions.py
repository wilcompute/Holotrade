#!/usr/bin/env python3
"""Gauge-neutral singlet directions of the frozen SU(5) W33 witness.

Reconstruct the exact massless spectrum used by the exotic-mass certificates.
Among the selected-SU(5) singlets there are 24 untwisted momentum types and
22 twisted momentum types (4,9,9 over Wilson fixed-point labels n1=0,1,2).

We enumerate full 16D lattice-momentum-neutral holomorphic monomials.  There
are 36 neutral cubics and exactly 16 primitive neutral quartics.  Every quartic
has type U*T0*T1*T2.  For each of those 16 supports:

* no neutral cubic contains two support fields;
* no degree-5,6,7 neutral monomial can yield an F-term on the support locus;
* at degree 8 the sole dangerous monomial is the square of the quartic, but
  2U+6T is forbidden by the Z3 R rule;
* degrees 9,10,11 again have no dangerous neutral monomial;
* at degree 12 the cube of the quartic is the first gauge+R-admissible self
  coupling: 3U+9T, with the three U copies chosen one per untwisted plane.

Thus these are exact lattice-gauge-neutral D-flat *candidates* protected
against gauge+R superpotential F-terms through order 11.  The word candidate
is essential: the anomalous-U(1) Fayet-Iliopoulos term is not supplied by the
current spectrum certificate, and the order-12 space-group/Rule-4/Rule-5
amplitude has not been evaluated here.
"""
from __future__ import annotations
import importlib.util,itertools,json
from collections import Counter
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1];S=36
OUT=ROOT/'data'/'w33_su5_singlet_flat_directions.json'

def load(name):
    s=importlib.util.spec_from_file_location(name,ROOT/'analysis'/(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
fam=load('the_w33_vacuum_families_live_on_the_untwisted_planes')
gut=load('does_the_w33_vacuum_contain_a_three_family_gut')

def multiplets(states,roots):
    st=[tuple(int(x) for x in P) for P in states];key={x:i for i,x in enumerate(st)};rr=[tuple(int(x) for x in r) for r in roots];seen=set();out=[]
    for i in range(len(st)):
        if i in seen:continue
        q=[i];seen.add(i);C=[]
        while q:
            k=q.pop();C.append(st[k]);P=st[k]
            for r in rr:
                z=tuple(P[j]+r[j] for j in range(16));h=key.get(z)
                if h is not None and h not in seen:seen.add(h);q.append(h)
        out.append([np.array(x,dtype=np.int64) for x in C])
    return out

def neutral(vecs,degree):
    out=[]
    for inds in itertools.combinations_with_replacement(range(len(vecs)),degree):
        if not np.any(sum((vecs[i] for i in inds),start=np.zeros(16,dtype=np.int64))):out.append(inds)
    return out

def dangerous(vecs,support,degree):
    """Degree-d neutral terms with >=d-1 factors on the VEV support."""
    mp={tuple(v.tolist()):i for i,v in enumerate(vecs)};out=set()
    for m in (degree-1,degree):
        for ss in itertools.combinations_with_replacement(support,m):
            v=sum((vecs[i] for i in ss),start=np.zeros(16,dtype=np.int64))
            if m==degree:
                if not np.any(v):out.add(tuple(ss))
            else:
                j=mp.get(tuple((-v).tolist()))
                if j is not None:out.add(tuple(sorted(ss+(j,))))
    return sorted(out)

def r_allowed(term,kinds):
    nT=sum(kinds[i].startswith('T') for i in term);nU=len(term)-nT
    if nT%3:return False
    # Oscillatorless T1 ground states contribute nT/3 to each picture-independent
    # R charge.  Untwisted fields can be assigned among the three plane copies.
    r=(1-nT//3)%3;minimum=3*r
    return nU>=minimum and (nU-minimum)%3==0

def main(write=True):
    parent=json.loads((ROOT/'data'/'w33_vacuum_three_family_gut.json').read_text());line=np.array(parent['examples']['su5_three_families']['lines'][0],dtype=np.int64)
    B=fam.Builder();V=np.concatenate([B.shift(72,1),B.shift(84,2)]);gauge,untw,fps=B.model(V,[line]);comps=fam.het.root_components(gauge)
    A4=next(C for C in comps if fam.cname(C)=='A4' and np.any(C[:,:8]));sr=np.array(gut.diagram(A4)[0],dtype=np.int64)
    UC=multiplets(untw,A4);US=[C[0] for C in UC if len(C)==1];assert len(US)==24
    TC={}
    for n1 in range(3):
        cc=[]
        for P,m in fps[(n1,0,0)]:assert m==1;cc+=multiplets(P,A4)
        TC[n1]=cc
    TS=[(n1,C[0]) for n1 in range(3) for C in TC[n1] if len(C)==1];assert [sum(1 for n,_ in TS if n==i) for i in range(3)]==[4,9,9]
    vecs=US+[v for _,v in TS];kinds=['U']*24+[f'T{n}' for n,_ in TS]
    z3=neutral(vecs,3);z4=neutral(vecs,4)
    assert len(z3)==36 and len(z4)==16
    assert Counter(tuple(kinds[i][0] for i in z) for z in z3)==Counter({('U','U','U'):20,('T','T','T'):16})
    assert all(sorted(kinds[i] for i in z)==['T0','T1','T2','U'] for z in z4)
    records=[]
    for z in z4:
        S0=tuple(sorted(set(z)));assert len(S0)==4
        # No cubic can source an F term on this VEV locus.
        assert not any(len(set(c)&set(S0))>=2 for c in z3)
        profile={}
        for d in range(5,13):
            ds=dangerous(vecs,S0,d);ra=[t for t in ds if r_allowed(t,kinds)]
            profile[str(d)]={'gauge_neutral_dangerous':len(ds),'R_allowed':len(ra)}
        assert all(profile[str(d)]['gauge_neutral_dangerous']==0 for d in (5,6,7,9,10,11))
        assert profile['8']=={'gauge_neutral_dangerous':1,'R_allowed':0}
        assert profile['12']=={'gauge_neutral_dangerous':1,'R_allowed':1}
        d8=dangerous(vecs,S0,8)[0];d12=dangerous(vecs,S0,12)[0]
        assert d8==tuple(sorted(z+z)) and d12==tuple(sorted(z+z+z))
        labels=[]
        for i in z:
            if i<24:labels.append(['U',i])
            else:labels.append([kinds[i],i-24])
        records.append({'support':labels,'protection':profile})
    out={'schema':'holotrade.w33_su5_singlet_flat_directions.v1','status':'PASS',
      'headline':'The frozen SU(5) witness has 16 primitive full-lattice-neutral quartic singlet monomials U*T0*T1*T2. None is F-lifted by any gauge+R-allowed superpotential monomial through order 11; the first gauge+R-admissible self-lift is the degree-12 cube with three untwisted copies assigned one per plane.',
      'singlet_types':{'untwisted':24,'twisted_by_n1':[4,9,9],'total':46},
      'neutral_monomials':{'degree3':36,'degree3_type_census':{'UUU':20,'TTT':16},'primitive_degree4':16,'degree4_type':'U*T0*T1*T2'},
      'flat_direction_protection':{'through_order':11,'degree8':'only self-square exists; R forbidden','degree12':'self-cube is first gauge+R-admissible dangerous monomial'},
      'directions':records,
      'D_flat_boundary':'Exact 16D lattice-momentum neutrality gives holomorphic gauge-neutral monomials and the standard zero-FI D-flat candidates. The anomalous-U(1) Fayet-Iliopoulos term is not fixed here and can shift the physical D-flat locus.',
      'F_flat_boundary':'Protection through order 11 uses exact lattice gauge neutrality plus the picture-independent Z3 R rule. Degree-12 space-group, Rule-4/Rule-5 and actual CFT coefficient/VEV data remain to be checked.',
      'checks':{'24_U':True,'22_T':True,'36_neutral_cubics':True,'16_quartic_directions':True,'no_cubic_pair_completion':True,'protected_through_11':True,'first_gauge_R_self_lift_12':True}}
    if write:OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2));return out
if __name__=='__main__':main(True)
