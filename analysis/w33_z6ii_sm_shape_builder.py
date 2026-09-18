#!/usr/bin/env python3
"""Honest Z6-II gauge-embedding builder for the W33 heterotic branch.

This file does NOT reuse the old T^6/Z3 spectrum engine.  It implements the
Z6-II twist, E8 lattice-order checks, the standard Abelian-orbifold modular
invariance constraints, exact E8 root projection, subtwist sector data, and
an explicit modular-compatible (V6,W2,W3) witness.

Literature inputs:
  * Z6-II twist v6=(1/6,1/3,-1/2) on the G2 x SU(3) x SO(4) lattice;
    v3=2 v6 and v2=3 v6 (standard Z6-II heterotic construction).
  * Abelian heterotic modular-invariance conditions:
      N(V^2-v^2)=0 mod 2,
      N_i A_i.V=0 mod 2,
      N_i A_i^2=0 mod 2,
      gcd(N_i,N_j) A_i.A_j=0 mod 2.

The witness found by finite search is
  V6 = (1/6, 1/3,-1/2,0,0,0,0,0 ; 0^8)
  W2 = (-1,1/2,0,-1,-1,-1/2,-1/2,-1/2 ; 0^8)
  W3 = (-2/3,-2/3,2/3,0,2/3,-1/3,-1/3,0 ; 0^8).

It is an honest order-(6,2,3) embedding.  In the first E8:
  V6                -> E6
  V6 + W2           -> A5 + A1
  V6 + W3           -> A4 + A1
  V6 + W2 + W3      -> A2 + A1.

Moreover the final A2+A1 lies entirely inside the A4 parent.  Thus W2 breaks
that SU(5) to SU(3)xSU(2) with canonical hypercharge direction
  Y=(-1,-1,-1,5,-7,3,3,-5)/12,
Y^2=5/6 and k_Y=2Y^2=5/3.  On every SU(5) root, the W2 phase equals the
(3/5)Y phase, so the nontrivial broken-root phase is exactly 1/2.

Boundary: this is a gauge-embedding/root-system and sector-kinematics theorem,
not a full massless-spectrum calculation.  Three chiral families, anomaly
cancellation after spectrum projection, exotic decoupling, D/F flatness, and
phenomenology remain to be computed by a genuine Z6-II spectrum engine.
"""
from __future__ import annotations
import itertools, json, math
from collections import deque
from fractions import Fraction as F
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/w33_z6ii_sm_shape_builder.json'

def dot(a,b): return sum(x*y for x,y in zip(a,b))
def sq(a): return dot(a,a)
def mod1(x): return x % 1

def in_e8(v):
    v=tuple(F(x) for x in v)
    if all(x.denominator==1 for x in v):
        return sum(int(x) for x in v)%2==0
    if all(x.denominator==2 and abs(x.numerator)%2==1 for x in v):
        s=sum(v)
        return s.denominator==1 and int(s)%2==0
    return False

def e8_roots():
    roots=[]
    for i,j in itertools.combinations(range(8),2):
        for si in (-1,1):
            for sj in (-1,1):
                v=[F(0)]*8; v[i]=F(si); v[j]=F(sj); roots.append(tuple(v))
    for signs in itertools.product((-1,1),repeat=8):
        if sum(s<0 for s in signs)%2==0:
            roots.append(tuple(F(s,2) for s in signs))
    assert len(roots)==240 and all(sq(r)==2 for r in roots)
    return roots

def rankq(vs):
    M=[list(map(F,v)) for v in vs]
    if not M:return 0
    m=len(M);n=len(M[0]);r=0
    for c in range(n):
        p=next((i for i in range(r,m) if M[i][c]),None)
        if p is None:continue
        M[r],M[p]=M[p],M[r]
        z=M[r][c]; M[r]=[x/z for x in M[r]]
        for i in range(m):
            if i!=r and M[i][c]:
                z=M[i][c]; M[i]=[M[i][j]-z*M[r][j] for j in range(n)]
        r+=1
    return r

def components(rs):
    rs=list(rs); n=len(rs); adj=[set() for _ in range(n)]
    for i,j in itertools.combinations(range(n),2):
        if dot(rs[i],rs[j])!=0:
            adj[i].add(j);adj[j].add(i)
    seen=set(); out=[]
    for i in range(n):
        if i in seen:continue
        q=[i];seen.add(i);ind=[]
        while q:
            u=q.pop();ind.append(u)
            for w in adj[u]:
                if w not in seen:seen.add(w);q.append(w)
        C={rs[k] for k in ind}; out.append(C)
    return sorted(out,key=lambda C:(-len(C),-rankq(C)))

ADE={(72,6):'E6',(126,7):'E7',(60,6):'D6',
     (30,5):'A5',(20,4):'A4',(12,3):'A3',(6,2):'A2',(2,1):'A1'}

def label(rs):
    cs=components(rs)
    return '+'.join(ADE[(len(C),rankq(C))] for C in cs),[(len(C),rankq(C)) for C in cs]

def survive(roots,*shifts):
    return [r for r in roots if all(dot(r,s).denominator==1 for s in shifts)]

def even_integer(x):
    return x.denominator==1 and int(x)%2==0

def main(write=True):
    roots=e8_roots()
    v6=(F(1,6),F(1,3),F(-1,2))
    V6=(F(1,6),F(1,3),F(-1,2),F(0),F(0),F(0),F(0),F(0))
    W2=(F(-1),F(1,2),F(0),F(-1),F(-1),F(-1,2),F(-1,2),F(-1,2))
    W3=(F(-2,3),F(-2,3),F(2,3),F(0),F(2,3),F(-1,3),F(-1,3),F(0))

    # Exact orders in the E8 lattice.
    assert in_e8(tuple(6*x for x in V6)) and all(not in_e8(tuple(k*x for x in V6)) for k in range(1,6))
    assert in_e8(tuple(2*x for x in W2)) and not in_e8(W2)
    assert in_e8(tuple(3*x for x in W3)) and not in_e8(W3)

    # Standard modular-invariance constraints.
    checks={
      '6(V6^2-v6^2)':6*(sq(V6)-sq(v6)),
      '2(V6.W2)':2*dot(V6,W2),
      '3(V6.W3)':3*dot(V6,W3),
      '2(W2^2)':2*sq(W2),
      '3(W3^2)':3*sq(W3),
      'gcd(2,3)(W2.W3)':dot(W2,W3)}
    assert all(even_integer(x) for x in checks.values())

    cases={
      'V6':(V6,),
      'V6+W2':(V6,W2),
      'V6+W3':(V6,W3),
      'V6+W2+W3':(V6,W2,W3),
      '2V6_Z3':(tuple(2*x for x in V6),),
      '2V6_Z3+W3':(tuple(2*x for x in V6),W3),
      '3V6_Z2':(tuple(3*x for x in V6),),
      '3V6_Z2+W2':(tuple(3*x for x in V6),W2)}
    expected={
      'V6':'E6','V6+W2':'A5+A1','V6+W3':'A4+A1','V6+W2+W3':'A2+A1',
      '2V6_Z3':'E7','2V6_Z3+W3':'A5+A2','3V6_Z2':'E7+A1','3V6_Z2+W2':'D6+A1+A1'}
    groups={}
    rootsets={}
    for name,sh in cases.items():
        rs=survive(roots,*sh); lab,profile=label(rs)
        assert lab==expected[name]
        rootsets[name]=set(rs)
        groups[name]={'semisimple':lab,'root_count':len(rs),'rank':rankq(rs),
                      'component_root_rank_pairs':profile,'U1_rank_first_E8':8-rankq(rs)}

    # The SM nonabelian factors are literally inside the SU(5)=A4 parent.
    parent_components=components(rootsets['V6+W3'])
    A4=next(C for C in parent_components if (len(C),rankq(C))==(20,4))
    spectator_A1=next(C for C in parent_components if (len(C),rankq(C))==(2,1))
    final=rootsets['V6+W2+W3']
    assert final <= A4 and not (final & spectator_A1)

    # Canonical hypercharge in the A4 span, normalized to kY=5/3.
    Y=tuple(F(x,12) for x in (-1,-1,-1,5,-7,3,3,-5))
    assert sq(Y)==F(5,6)
    assert all(dot(Y,r)==0 for r in final)
    charges={dot(Y,r) for r in A4}
    assert charges=={F(-5,6),F(0),F(5,6)}
    # On SU(5) roots W2 is exactly the t=1/2 hypercharge breaker.
    for r in A4:
        assert mod1(dot(W2,r))==mod1(F(3,5)*dot(Y,r))
    assert {mod1(dot(W2,r)) for r in A4}=={F(0),F(1,2)}

    sectors=[]
    for k in range(1,6):
        eta=tuple(mod1(k*x) for x in v6)
        dc=F(1,2)*sum(x*(1-x) for x in eta)
        zeros=sum(x==0 for x in eta)
        sectors.append({'k':k,'twist_fractions':[str(x) for x in eta],
                        'delta_c':str(dc),'invariant_complex_planes':zeros,
                        'fixed_locus':'fixed_tori' if zeros else 'fixed_points'})

    out={
      'schema':'w33.z6ii_sm_shape_builder.v1','status':'PASS_GAUGE_EMBEDDING_NOT_SPECTRUM',
      'geometry':{'orbifold':'T6/Z6-II','twist_v6':['1/6','1/3','-1/2'],
                  'subtwists':{'Z3':'2 v6','Z2':'3 v6'},
                  'sector_zero_point_data':sectors},
      'embedding':{'V6':[str(x) for x in V6],'W2':[str(x) for x in W2],
                   'W3':[str(x) for x in W3],
                   'orders':{'V6':6,'W2':2,'W3':3}},
      'modular_invariance':{k:str(v) for k,v in checks.items()},
      'first_E8_root_chain':groups,
      'global_gauge_root_algebra':'A2+A1+u1^5 in first E8, with second E8 untouched',
      'SU5_to_SM':{
        'parent':'V6+W3 gives A4+A1; the final A2+A1 is entirely inside the A4 parent',
        'spectator_A1_survives_W2':False,
        'hypercharge_Y':[str(x) for x in Y],
        'Y_squared':str(sq(Y)),'kY=2Y2':str(2*sq(Y)),
        'SU5_root_Y_charges':['-5/6','0','5/6'],
        'W2_phase_on_SU5_roots':['0','1/2'],
        'identity':'W2 phase = (3/5) Y phase on every SU(5) root',
        'consequence':'canonical SU(5) breaking to SU(3)xSU(2)xU(1)_Y at the root/Cartan level'},
      'hidden_factor':'second E8 untouched by this witness',
      'what_is_closed':['correct Z6-II twist/subtwist kinematics','exact Wilson-line orders',
                        'modular-invariant gauge embedding','local/global ADE root systems',
                        'SM nonabelian gauge shape','canonical SU5 hypercharge normalization kY=5/3'],
      'what_is_open':['full massless spectrum and orbifold projections','three net chiral families',
                      'hypercharge anomaly after spectrum enumeration','vectorlike-exotic decoupling',
                      'D/F-flat vacuum','Yukawas and phenomenology'],
      'boundary':'This is the first honest even-order gauge-embedding builder on this branch, not a claimed MSSM vacuum.'}
    if write:OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2));return out

if __name__=='__main__':main(True)
