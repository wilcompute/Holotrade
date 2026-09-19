#!/usr/bin/env python3
"""Global gauge-algebra closure for the W33 Z6-I flagship.

This reconstructs the complete unbroken E8xE8 root system directly from the
committed flagship shift V and order-three Wilson line W3.  A root p survives
iff p.V and p.W3 are integers.

Result:
  first E8 : A4 + A1 + A1 + u(1)^2
  second E8: A2 + A1 + u(1)^5

The second factor is the Standard-Model side because the committed hypercharge
vector lives there.  Its 16-dimensional algebra exactly matches the independent
W33 E8/A8-selector triple-centralizer certificate:
  A2 + A1 + u(1)^5, dim 16.

Therefore the four U(1) directions beyond hypercharge are not merely local
SU(9) centralizer directions: they survive the exact global shift/Wilson-line
root intersection.  Their eventual fate is a separate vacuum problem.

Literature boundary: at a strict heterotic orbifold point the conventional
Green--Schwarz anomalous-U(1) cancellation is universal, hence supplies one
anomalous/Stueckelberg direction.  Thus that mechanism alone cannot remove all
four extra hypercharge-orthogonal U(1)s.  Singlet Higgsing, or non-universal
axions after blow-up/resolution, are separate mechanisms and are not excluded.
"""
from __future__ import annotations
import itertools, json
from fractions import Fraction as F
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PARENT=ROOT/'data/w33_twist_hosts_sm_in_even_order_orbifold.json'
OUT=ROOT/'data/w33_flagship_global_u1_closure.json'

def parse8(text):
    return tuple(F(x.strip()) for x in text.split(','))

def split16(text):
    a,b=text.split('|')
    return parse8(a),parse8(b)

def dot(a,b): return sum(x*y for x,y in zip(a,b))

def roots_e8():
    out=[]
    for i,j in itertools.combinations(range(8),2):
        for a,b in itertools.product((1,-1),repeat=2):
            v=[F(0)]*8;v[i]=F(a);v[j]=F(b);out.append(tuple(v))
    for s in itertools.product((1,-1),repeat=8):
        if sum(x<0 for x in s)%2==0:
            out.append(tuple(F(x,2) for x in s))
    assert len(out)==len(set(out))==240
    assert all(dot(r,r)==2 for r in out)
    return out

def rank(rows):
    A=[list(r) for r in rows if any(r)]
    if not A:return 0
    m,n=len(A),len(A[0]);rr=0
    for c in range(n):
        p=next((i for i in range(rr,m) if A[i][c]),None)
        if p is None:continue
        A[rr],A[p]=A[p],A[rr]
        z=A[rr][c];A[rr]=[x/z for x in A[rr]]
        for i in range(m):
            if i!=rr and A[i][c]:
                z=A[i][c];A[i]=[A[i][j]-z*A[rr][j] for j in range(n)]
        rr+=1
    return rr

def components(rs):
    rem=set(range(len(rs)));out=[]
    while rem:
        i=rem.pop();C=[i];stack=[i]
        while stack:
            u=stack.pop()
            ns=[v for v in list(rem) if dot(rs[u],rs[v])!=0]
            for v in ns:
                rem.remove(v);stack.append(v);C.append(v)
        out.append(C)
    return sorted((len(C),rank([rs[i] for i in C])) for C in out)

def nullspace(rows):
    # exact rational RREF nullspace
    A=[list(r) for r in rows]
    if not A:return [tuple(F(int(i==j)) for i in range(8)) for j in range(8)]
    m,n=len(A),len(A[0]);rr=0;piv=[]
    for c in range(n):
        p=next((i for i in range(rr,m) if A[i][c]),None)
        if p is None:continue
        A[rr],A[p]=A[p],A[rr]
        z=A[rr][c];A[rr]=[x/z for x in A[rr]]
        for i in range(m):
            if i!=rr and A[i][c]:
                z=A[i][c];A[i]=[A[i][j]-z*A[rr][j] for j in range(n)]
        piv.append(c);rr+=1
    free=[c for c in range(n) if c not in piv]
    basis=[]
    for f in free:
        x=[F(0)]*n;x[f]=1
        for i,p in enumerate(piv):
            x[p]=-A[i][f]
        basis.append(tuple(x))
    return basis

def vstr(v):
    return [str(x) for x in v]

def main(write=True):
    p=json.loads(PARENT.read_text())
    f=p['flagship']
    V1,V2=split16(f['V']);W1,W2=split16(f['W3']);Y1,Y2=split16(f['tY'])
    assert all(x==0 for x in Y1)
    R=roots_e8()
    survive=lambda V,W:[r for r in R if dot(r,V).denominator==1 and dot(r,W).denominator==1]
    U1,U2=survive(V1,W1),survive(V2,W2)
    sig1,sig2=components(U1),components(U2)
    assert sig1==[(2,1),(2,1),(20,4)]
    assert sig2==[(2,1),(6,2)]
    r1,r2=rank(U1),rank(U2)
    assert (r1,r2)==(6,3)

    center2=nullspace(U2)
    assert len(center2)==5
    assert all(dot(Y2,r)==0 for r in U2)
    assert dot(Y2,Y2)==F(5,6)
    extra=nullspace(U2+[Y2])
    assert len(extra)==4
    assert all(dot(e,Y2)==0 and all(dot(e,r)==0 for r in U2) for e in extra)

    # Lie dimensions = root count + Cartan rank 8 for a maximal-rank torus shift.
    dim1=len(U1)+8;dim2=len(U2)+8
    assert (dim1,dim2)==(32,16)

    out={
      'schema':'holotrade.w33_flagship_global_u1_closure.v1',
      'status':'PASS_GLOBAL_GAUGE_INTERSECTION',
      'headline':'Exact E8 root filtering by the flagship V and W3 gives first-E8 A4+A1+A1+u(1)^2 (dim32) and Standard-Model-side second-E8 A2+A1+u(1)^5 (dim16). The latter exactly equals the independent W33 physical E8/A8-selector triple centralizer. Hypercharge is one of the five center directions, so four additional hypercharge-orthogonal U(1) directions survive the global shift/Wilson-line intersection.',
      'flagship':f['label'],
      'root_rule':'p survives iff p.V and p.W3 are integers',
      'first_E8':{
        'surviving_roots':len(U1),'root_rank':r1,'component_signature':sig1,
        'algebra':'A4 + A1 + A1 + u(1)^2','dimension':dim1},
      'second_E8_SM_side':{
        'surviving_roots':len(U2),'root_rank':r2,'component_signature':sig2,
        'algebra':'A2 + A1 + u(1)^5','dimension':dim2,
        'center_rank':len(center2),
        'hypercharge':vstr(Y2),'hypercharge_norm2':str(dot(Y2,Y2)),
        'extra_hypercharge_orthogonal_u1_basis':[vstr(x) for x in extra]},
      'cross_repo_lock':{
        'W33_parent':'data/w33_e8_a8_selector_holonomy_triple_intersection.json',
        'W33_algebra':'A2+A1+u(1)^5','W33_dimension':16,
        'global_root_filter_matches':True},
      'green_schwarz_boundary':{
        'orbifold_point_statement':'The conventional heterotic orbifold Green-Schwarz anomaly is universal and selects one anomalous U(1) direction.',
        'consequence_if_applied_to_flagship':'A rank-one universal GS/Stueckelberg direction cannot by itself remove all four extra hypercharge-orthogonal U(1)s; at least three require singlet Higgsing or another mechanism.',
        'blowup_escape':'After blow-up/resolution, localized/model-dependent axions can yield non-universal anomaly cancellation and multiple anomalous U(1)s.',
        'not_computed_here':'The flagship matter-charge anomaly matrix and singlet-VEV mass matrix are not yet frozen, so this certificate does not identify which extra U(1) is anomalous or which are Higgsed.'},
      'literature':[
        'Kobayashi--Nakano, hep-th/9612066, anomalous U(1) in heterotic orbifold models',
        'Groot Nibbelink--Nilles--Trapletti, hep-th/0703211, multiple anomalous U(1)s in heterotic blow-ups',
        'Luedeling--Ruehle--Wieck, arXiv:1203.5789, universal orbifold versus non-universal blow-up anomalies'],
      'checks':{
        'E8_roots_240':True,'first_root_signature_A4_A1_A1':True,
        'second_root_signature_A2_A1':True,'second_center_rank5':True,
        'hypercharge_in_center':True,'hypercharge_GUT_norm_5_over_6':True,
        'four_exact_extra_center_vectors_orthogonal_to_Y':True,
        'global_second_E8_dimension16':True}}
    if write:OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))
    return out

if __name__=='__main__':main(True)
