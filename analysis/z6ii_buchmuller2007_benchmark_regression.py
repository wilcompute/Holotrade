#!/usr/bin/env python3
"""Published Z6-II benchmark regression fixture.

Benchmark: Buchmueller--Hamaguchi--Lebedev--Ratz, Nucl.Phys.B785 (2007),
Section 5.2, Eq. (5.2), gauge group Eq. (5.4), Appendix A.

The published 16D data are
 V6 = (1/2,1/2,1/3,0,0,0,0,0)(1/3,0,0,0,0,0,0,0)
 W2 = (1/2,0,1/2,1/2,1/2,0,0,0)(-3/4,1/4,1/4,-1/4,1/4,1/4,1/4,-1/4)
 W3 = (1/3,0,0,1/3,1/3,1/3,1/3,1/3)(1,1/3,1/3,1/3,0,0,0,0).

Exact E8-root enumeration must reproduce:
  visible roots: A2+A1 = SU3 x SU2, 8 roots;
  hidden roots:  A3+A1 = SU4 x SU2, 14 roots.

At the origin T1 local shift, the first-E8 mass shell has
 (p+V6)_obs^2 = 23/18
and exactly 16 weights; the second-E8 shell has norm 1/9 and exactly one
shifted weight.  This reproduces the published complete local SO(10) 16-plet
before any model-specific downstream phenomenology.

This is a regression fixture, not yet a full reproduction of every row in
Table D.2/D.3.  Its purpose is to fail loudly if the shared E8 lattice,
Wilson-line, or T1 shell conventions drift.
"""
from __future__ import annotations
import itertools,json,math
from fractions import Fraction as F
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/z6ii_buchmuller2007_benchmark_regression.json'

V1=(F(1,2),F(1,2),F(1,3),0,0,0,0,0)
V2=(F(1,3),0,0,0,0,0,0,0)
W21=(F(1,2),0,F(1,2),F(1,2),F(1,2),0,0,0)
W22=(F(-3,4),F(1,4),F(1,4),F(-1,4),F(1,4),F(1,4),F(1,4),F(-1,4))
W31=(F(1,3),0,0,F(1,3),F(1,3),F(1,3),F(1,3),F(1,3))
W32=(F(1),F(1,3),F(1,3),F(1,3),0,0,0,0)

def dot(a,b):return sum(x*y for x,y in zip(a,b))
def roots():
    out=[]
    for i,j in itertools.combinations(range(8),2):
        for si in (-1,1):
            for sj in (-1,1):
                v=[F(0)]*8;v[i]=F(si);v[j]=F(sj);out.append(tuple(v))
    for s in itertools.product((-1,1),repeat=8):
        if sum(x<0 for x in s)%2==0:out.append(tuple(F(x,2) for x in s))
    assert len(out)==240
    return out
def rankq(vs):
    A=[list(map(F,v)) for v in vs]
    if not A:return 0
    m=len(A);n=8;r=0
    for c in range(n):
        p=next((i for i in range(r,m) if A[i][c]),None)
        if p is None:continue
        A[r],A[p]=A[p],A[r];z=A[r][c];A[r]=[x/z for x in A[r]]
        for i in range(m):
            if i!=r and A[i][c]:
                z=A[i][c];A[i]=[A[i][j]-z*A[r][j] for j in range(n)]
        r+=1
    return r
def comps(rs):
    rs=list(rs);adj=[set() for _ in rs]
    for i,j in itertools.combinations(range(len(rs)),2):
        if dot(rs[i],rs[j])!=0:adj[i].add(j);adj[j].add(i)
    seen=set();out=[]
    for i in range(len(rs)):
        if i in seen:continue
        st=[i];seen.add(i);C=[]
        while st:
            u=st.pop();C.append(rs[u])
            for w in adj[u]:
                if w not in seen:seen.add(w);st.append(w)
        out.append((len(C),rankq(C)))
    return sorted(out)
def in_e8(p):
    if all(x.denominator==1 for x in p):return sum(int(x) for x in p)%2==0
    if all(x.denominator==2 and abs(x.numerator)%2==1 for x in p):
        z=sum(p);return z.denominator==1 and int(z)%2==0
    return False
def shell(sh,target):
    R=math.sqrt(float(target));out=[]
    for half in (False,True):
        choices=[]
        for s in sh:
            vals=[]
            for n in range(-3,4):
                p=F(n) if not half else F(2*n+1,2)
                if (p+s)**2<=target:vals.append(p)
            choices.append(vals)
        for P in itertools.product(*choices):
            if not in_e8(P):continue
            q=tuple(P[i]+sh[i] for i in range(8))
            if dot(q,q)==target:out.append(q)
    return sorted(set(out))

def main(write=True):
    R=roots()
    vis=[a for a in R if all(dot(a,w).denominator==1 for w in (V1,W21,W31))]
    hid=[a for a in R if all(dot(a,w).denominator==1 for w in (V2,W22,W32))]
    assert len(vis)==8 and comps(vis)==[(2,1),(6,2)]
    assert len(hid)==14 and comps(hid)==[(2,1),(12,3)]
    local=[a for a in R if dot(a,V1).denominator==1]
    assert comps(local)==[(2,1),(2,1),(40,5)]
    qvis=shell(V1,F(23,18)); qhid=shell(V2,F(1,9))
    assert len(qvis)==16 and len(qhid)==1
    out={'schema':'holotrade.z6ii_buchmuller2007_benchmark_regression.v1','status':'PASS_CORE_EXTERNAL_BENCHMARK',
      'source':'Buchmueller et al., Nucl.Phys.B785 (2007) 149-209, Sec.5.2 Eq.(5.2), Eq.(5.4), Appendix A',
      'published_model':{
        'V6_first_E8':[str(x) for x in V1],'V6_second_E8':[str(x) for x in V2],
        'W2_first_E8':[str(x) for x in W21],'W2_second_E8':[str(x) for x in W22],
        'W3_first_E8':[str(x) for x in W31],'W3_second_E8':[str(x) for x in W32]},
      'regressions':{
        'visible_global_roots':8,'visible_ADE':'A2+A1',
        'hidden_global_roots':14,'hidden_ADE':'A3+A1',
        'published_nonabelian_group':'SU(3)xSU(2)x[SU(4)xSU(2)]',
        'origin_local_first_E8':'D5+A1+A1',
        'T1_visible_shell_norm':'23/18','T1_visible_shell_weights':16,
        'T1_hidden_shell_norm':'1/9','T1_hidden_shell_weights':1,
        'local_SO10_16_reproduced':True},
      'benchmark_scope':'Core lattice/gauge/T1 regression is reproduced exactly. Full row-by-row reproduction of Tables D.2-D.3 is the next extension and is not claimed here.',
      'checks':{'E8_roots_240':True,'visible_group':True,'hidden_group':True,'T1_16':True}}
    if write:OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2));return out
if __name__=='__main__':main(True)
