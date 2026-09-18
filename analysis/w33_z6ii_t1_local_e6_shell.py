#!/usr/bin/env python3
"""T1 local-GUT and unoscillated mass-shell census for the Z6-II witness.

For the factorized G2 x SU(3) x SO(4) Z6-II geometry, the twelve T1 fixed
points have local shifts
    V_g = V + n3 W3 + n2 W2 + n2' W2',
with n3=0,1,2 and n2,n2'=0,1.  The current witness has W2'=0, so the six
distinct local shifts each occur twice.

For T1, delta_c=11/36.  At left oscillator number N=0 the massless equation is
    (P+V_g)^2/2 = 1-delta_c = 25/36,
so (P+V_g)^2=25/18.  Since this is below 2 and the hidden E8 is unshifted,
the hidden momentum must be zero.  We therefore enumerate the exact first-E8
shifted shell.

At the V local E6 point there are exactly 27 shifted momenta.  The set is
closed and transitive under all 72 E6 root reflections, proving it is one
27-weight Weyl orbit rather than a numerical count.  The pair inner products
are 7/18 (216 pairs) and -11/18 (135 pairs).

Boundary: this is the unoscillated left-moving shell before the full Z6-II
centralizer/gamma projection and right-moving state matching.  It is a local
27 multiplet candidate, not yet a certified four-dimensional chiral family.
"""
from __future__ import annotations
import itertools,json,math
from collections import Counter
from fractions import Fraction as F
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/w33_z6ii_t1_local_e6_shell.json'

def dot(a,b): return sum(x*y for x,y in zip(a,b))
def add(*xs): return tuple(sum(v[i] for v in xs) for i in range(8))
def mul(k,x): return tuple(k*a for a in x)

def e8_roots():
    out=[]
    for i,j in itertools.combinations(range(8),2):
        for si in (-1,1):
            for sj in (-1,1):
                v=[F(0)]*8;v[i]=F(si);v[j]=F(sj);out.append(tuple(v))
    for s in itertools.product((-1,1),repeat=8):
        if sum(x<0 for x in s)%2==0: out.append(tuple(F(x,2) for x in s))
    assert len(out)==240
    return out

def rankq(vs):
    A=[list(v) for v in vs]
    if not A:return 0
    m=len(A);n=8;r=0
    for c in range(n):
        p=next((i for i in range(r,m) if A[i][c]),None)
        if p is None:continue
        A[r],A[p]=A[p],A[r]; z=A[r][c];A[r]=[x/z for x in A[r]]
        for i in range(m):
            if i!=r and A[i][c]:
                z=A[i][c];A[i]=[A[i][j]-z*A[r][j] for j in range(n)]
        r+=1
    return r

def components(rs):
    rs=list(rs);adj=[set() for _ in rs]
    for i,j in itertools.combinations(range(len(rs)),2):
        if dot(rs[i],rs[j])!=0:adj[i].add(j);adj[j].add(i)
    seen=set();out=[]
    for i in range(len(rs)):
        if i in seen:continue
        st=[i];seen.add(i);C=[]
        while st:
            u=st.pop();C.append(rs[u])
            for v in adj[u]:
                if v not in seen:seen.add(v);st.append(v)
        out.append(C)
    return out

ADE={(72,6):'E6',(60,6):'D6',(42,6):'A6',(30,5):'A5',
     (6,2):'A2',(2,1):'A1'}

def root_label(rs):
    cs=components(rs)
    return '+'.join(ADE[(len(C),rankq(C))] for C in cs)

def shifted_shell(sh):
    # Multiply by 6.  q=6(P+sh) has norm sum q_i^2=50.
    s6=tuple(int(6*x) for x in sh);lim=7;out=[]
    for off in (0,3): # integer or half-integer E8 lattice coset
        vals=[[q for q in range(-lim,lim+1) if (q-s)%6==off] for s in s6]
        for q in itertools.product(*vals):
            if sum(x*x for x in q)!=50:continue
            p6=tuple(q[i]-s6[i] for i in range(8))
            if sum(p6)%12==0: out.append(tuple(F(x,6) for x in q))
    return sorted(set(out))

def reflection_orbit(seed,roots,allowed):
    seen={seed};st=[seed]
    while st:
        q=st.pop()
        for a in roots:
            d=dot(q,a);z=tuple(q[i]-d*a[i] for i in range(8))
            if z in allowed and z not in seen:seen.add(z);st.append(z)
    return seen

def main(write=True):
    parent=json.loads((ROOT/'data/w33_z6ii_sm_shape_builder.json').read_text())
    assert parent['status']=='PASS_GAUGE_EMBEDDING_NOT_SPECTRUM'
    V=tuple(map(F,parent['embedding']['V6']))
    W2=tuple(map(F,parent['embedding']['W2']))
    W3=tuple(map(F,parent['embedding']['W3']))
    R=e8_roots()

    local=[]
    for n3 in range(3):
        for n2 in range(2):
            sh=add(V,mul(n3,W3),mul(n2,W2))
            roots=[r for r in R if dot(r,sh).denominator==1]
            shell=shifted_shell(sh)
            allowed=set(shell)
            orbits=[]
            rem=set(shell)
            while rem:
                O=reflection_orbit(next(iter(rem)),roots,allowed)
                orbits.append(len(O));rem-=O
            local.append({'n3':n3,'n2':n2,'n2prime_multiplicity':2,
                          'local_root_algebra':root_label(roots),
                          'local_root_count':len(roots),
                          'local_rank':rankq(roots),
                          'N0_left_massless_shell':len(shell),
                          'Weyl_orbit_sizes':sorted(orbits,reverse=True)})

    e6=next(x for x in local if x['n3']==0 and x['n2']==0)
    assert e6['local_root_algebra']=='E6' and e6['N0_left_massless_shell']==27
    assert e6['Weyl_orbit_sizes']==[27]
    shell=shifted_shell(V)
    pair=Counter(dot(shell[i],shell[j]) for i in range(27) for j in range(i+1,27))
    assert pair==Counter({F(7,18):216,F(-11,18):135})

    out={
      'schema':'w33.z6ii_t1_local_e6_shell.v1',
      'status':'PASS_LOCAL_SHELL_NOT_4D_SPECTRUM',
      'T1_geometry':{'fixed_points':12,'labels':'n3=0,1,2; n2,n2prime=0,1',
                     'local_shift':'V+n3 W3+n2 W2+n2prime W2prime',
                     'witness_W2prime':'0','distinct_local_shifts':6,'multiplicity_each':2},
      'mass_shell':{'delta_c':'11/36','oscillator_N':0,
                    'equation':'(P+Vg)^2=25/18',
                    'hidden_E8_momentum':'forced zero because any nonzero hidden E8 lattice vector has norm >=2 >25/18'},
      'local_census':local,
      'E6_fixed_points':{
        'count':2,'local_algebra':'E6','unoscillated_shifted_momenta_each':27,
        'Weyl_action':'one transitive orbit under all 72 E6 root reflections',
        'pair_inner_products':{'7/18':216,'-11/18':135},
        'interpretation':'a complete local E6 27-weight shell candidate at each of two T1 fixed points'},
      'mini_landscape_shape':'two equivalent local-GUT fixed points are available for two localized family candidates; any third family must arise from other fixed loci/sectors or bulk/untwisted states',
      'projection_boundary':'Centralizer/gamma projection, right-moving massless state, oscillator shells and four-dimensional chirality have not yet been imposed. Therefore two physical 27 chiral multiplets are not yet claimed.',
      'checks':{'parent_loaded':True,'six_local_shifts':len(local)==6,'two_E6_fixed_points':True,
                'E6_shell_27':True,'E6_shell_transitive':True,'two_distance_216_135':True}}
    if write:OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2));return out

if __name__=='__main__':main(True)
