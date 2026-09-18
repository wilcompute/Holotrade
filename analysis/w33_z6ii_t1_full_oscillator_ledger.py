#!/usr/bin/env python3
"""Exact T1/T5 oscillator ledger for the explicit Z6-II witness.

This repairs the earlier N_L=0-only local-GUT census by implementing the full
singly twisted T1 projection of Chemtob--Hosteins Appendix B, eqs. (B.3)-(B.5).

For each fixed-point label (n3,n2,n2') the local gauge shift is
    X_g = V + n3 W3 + n2 W2 + n2' W2',
with W2'=0.  T1 has gamma=1.  For every left oscillator configuration with
N_L <= 25/36, every shifted E8 shell is enumerated exactly and the six temporal
twists h=0,...,5 are tested using

 Delta_h = phi^h exp 2pi i[
   (P+X_g).X_h - (r+v).h v
   - 1/2 (X_g.X_h - h v^2)],
 X_h = h V + n3 W3 + n2 W2.

The oscillator frequencies and phases are taken directly from (B.3)-(B.5).
T5 is the CPT conjugate sector; it does not provide an independent additional
left-chiral multiplet ledger.

Important correction: the two n3=n2=0 local E6 fixed points still give two
complete 27s, but the other ten T1 fixed points contain additional chiral and
exotic states.  Therefore the previous shorthand "two 27s plus a split
untwisted ten, missing only one anti-five" is NOT a complete-spectrum theorem.
A complete anomaly statement requires T1 oscillators and the remaining sectors.
"""
from __future__ import annotations
import itertools, json, math
from collections import Counter, defaultdict
from fractions import Fraction as F
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/w33_z6ii_t1_full_oscillator_ledger.json'

V=(F(1,6),F(1,3),F(-1,2),0,0,0,0,0)
W2=(F(-1),F(1,2),0,F(-1),F(-1),F(-1,2),F(-1,2),F(-1,2))
W3=(F(-2,3),F(-2,3),F(2,3),0,F(2,3),F(-1,3),F(-1,3),0)
Y=tuple(F(x,12) for x in (-1,-1,-1,5,-7,3,3,-5))
v=(F(1,6),F(1,3),F(-1,2),F(0))
r=(F(-1,2),F(-1,2),F(1,2),F(-1,2))
rg=tuple(r[i]+v[i] for i in range(4))
delta=F(11,36)

def dot(a,b): return sum(x*y for x,y in zip(a,b))
def in_e8(p):
    if all(x.denominator==1 for x in p):
        return sum(int(x) for x in p)%2==0
    if all(x.denominator==2 and abs(x.numerator)%2==1 for x in p):
        z=sum(p); return z.denominator==1 and int(z)%2==0
    return False

def roots():
    out=[]
    for i,j in itertools.combinations(range(8),2):
        for si in (-1,1):
            for sj in (-1,1):
                a=[F(0)]*8;a[i]=F(si);a[j]=F(sj);out.append(tuple(a))
    for s in itertools.product((-1,1),repeat=8):
        if sum(x<0 for x in s)%2==0:
            out.append(tuple(F(x,2) for x in s))
    return out

def shell(sh,target):
    R=float(target)**.5;out=[]
    for half in (False,True):
        cand=[]
        for s in sh:
            lo=math.floor(float(-s-R))-2;hi=math.ceil(float(-s+R))+2;vals=[]
            for n in range(lo,hi+1):
                p=F(n) if not half else F(2*n+1,2)
                if (p+s)**2<=target: vals.append(p)
            cand.append(vals)
        for P in itertools.product(*cand):
            if not in_e8(P): continue
            q=tuple(P[i]+sh[i] for i in range(8))
            if dot(q,q)==target:out.append((P,q))
    return out

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
            for w in adj[u]:
                if w not in seen:seen.add(w);st.append(w)
        out.append(C)
    return out

def rankq(vs):
    A=[list(map(F,x)) for x in vs]
    if not A:return 0
    m=len(A);n=len(A[0]);rr=0
    for c in range(n):
        p=next((i for i in range(rr,m) if A[i][c]),None)
        if p is None:continue
        A[rr],A[p]=A[p],A[rr];z=A[rr][c]
        A[rr]=[x/z for x in A[rr]]
        for i in range(m):
            if i!=rr and A[i][c]:
                z=A[i][c];A[i]=[A[i][j]-z*A[rr][j] for j in range(n)]
        rr+=1
    return rr

def simple(C):
    g=[math.sqrt(p) for p in (2,3,5,7,11,13,17,19)]
    pos=[a for a in C if sum(float(a[i])*g[i] for i in range(8))>0];ps=set(pos)
    return [a for a in pos if not any(tuple(a[i]-b[i] for i in range(8)) in ps for b in pos if b!=a)]

R=roots();GR=[a for a in R if all(dot(a,w).denominator==1 for w in (V,W2,W3))]
CS=components(GR);A2=next(C for C in CS if len(C)==6);A1=next(C for C in CS if len(C)==2)
S=simple(A2)+simple(A1)

def orbits(qs):
    Q=set(qs);rem=set(qs);out=[]
    while rem:
        seed=next(iter(rem));O={seed};st=[seed]
        while st:
            q=st.pop()
            for a in GR:
                d=dot(q,a);z=tuple(q[i]-d*a[i] for i in range(8))
                if z in Q and z not in O:O.add(z);st.append(z)
        out.append(O);rem-=O
    return out

def label(O):
    hs=[]
    for q in O:
        h=tuple(dot(q,a) for a in S)
        if all(x>=0 for x in h):hs.append(h)
    assert len(hs)==1
    yy={dot(Y,q) for q in O};assert len(yy)==1
    return len(O),tuple(int(x) for x in hs[0]),next(iter(yy))

# Oscillator modes that can occur below the T1 massless ceiling.
# (name, energy omega, B.5 phase-hat)
MODES=[
 ('I1',F(1,6),F(1,6)),
 ('I2',F(1,3),F(1,3)),
 ('I3',F(1,2),F(1,2)),
 ('bar2',F(2,3),F(-1,3)),
 ('bar3',F(1,2),F(-1,2)),
]
def oscillator_configs():
    out=[]
    def rec(i,E,ph,occ):
        if i==len(MODES):
            out.append((E,ph%1,tuple(occ)));return
        _,e,p=MODES[i]
        m=int((F(25,36)-E)//e)
        for n in range(m+1):rec(i+1,E+n*e,ph+n*p,occ+[n])
    rec(0,F(0),F(0),[])
    return out

CFGS=oscillator_configs()
BYE=defaultdict(list)
for E,ph,occ in CFGS:BYE[E].append((ph,occ))

def project(P,q,n3,n2,osc_phase):
    nW=tuple(n3*W3[i]+n2*W2[i] for i in range(8))
    Xg=tuple(V[i]+nW[i] for i in range(8))
    for h in range(6):
        Xh=tuple(h*V[i]+nW[i] for i in range(8))
        phase=(dot(q,Xh)-h*dot(rg,v)-F(1,2)*(dot(Xg,Xh)-h*dot(v,v))+h*osc_phase)
        if phase.denominator!=1:return False
    return True

def ks(k):
    d,h,y=k
    return f'{d}|{h}|{y}'

def main(write=True):
    local=[];aggregate=Counter()
    for n3 in range(3):
        for n2 in range(2):
            nW=tuple(n3*W3[i]+n2*W2[i] for i in range(8))
            sh=tuple(V[i]+nW[i] for i in range(8))
            rows=[];prof=Counter()
            for E in sorted(BYE):
                target=2*(1-delta-E)
                if target<0:continue
                raw=shell(sh,target)
                for osc_phase,occ in BYE[E]:
                    keep=[q for P,q in raw if project(P,q,n3,n2,osc_phase)]
                    if not keep:continue
                    rp=Counter(label(O) for O in orbits(keep))
                    rows.append({'N_L':str(E),'oscillator_phase':str(osc_phase),
                                 'occupations':{MODES[i][0]:occ[i] for i in range(len(MODES)) if occ[i]},
                                 'shifted_shell_raw':len(raw),'surviving_weights':len(keep),
                                 'representations':{ks(k):m for k,m in sorted(rp.items(),key=str)}})
                    for k,m in rp.items():
                        prof[k]+=2*m  # n2' unresolved: two actual T1 fixed points
                        aggregate[k]+=2*m
            local.append({'n3':n3,'n2':n2,'n2prime_multiplicity':2,'states':rows,
                          'representation_multiplicities_including_n2prime':{ks(k):m for k,m in sorted(prof.items(),key=str)}})

    expected={
      "1|(0, 0, 0)|-1/2":6,"1|(0, 0, 0)|0":26,"1|(0, 0, 0)|1":2,"1|(0, 0, 0)|1/2":4,
      "2|(0, 0, 1)|-1/2":6,"2|(0, 0, 1)|0":6,"2|(0, 0, 1)|1/2":4,
      "3|(0, 1, 0)|-2/3":2,"3|(0, 1, 0)|1/3":6,
      "3|(1, 0, 0)|-1/3":4,"3|(1, 0, 0)|1/6":6,
      "6|(1, 0, 1)|1/6":2}
    got={ks(k):m for k,m in sorted(aggregate.items(),key=str)}
    assert got==expected
    # Origin contains exactly two N=0 27s plus oscillator singlets.
    origin=next(x for x in local if x['n3']==0 and x['n2']==0)
    assert origin['representation_multiplicities_including_n2prime']["6|(1, 0, 1)|1/6"]==2
    assert origin['representation_multiplicities_including_n2prime']["3|(0, 1, 0)|-2/3"]==2
    out={'schema':'w33.z6ii_t1_full_oscillator_ledger.v1','status':'PASS_CORRECTS_PARTIAL_FRONTIER',
      'projection':'Chemtob--Hosteins B.3-B.5 full T1 six-h average with fixed n3,n2; gamma=1; W2prime=0',
      'oscillator_configuration_counts':{str(E):len(BYE[E]) for E in sorted(BYE)},
      'local_fixed_point_ledger':local,
      'aggregate_T1_left_chiral_representations':got,
      'aggregate_weight_dimension_including_fixed_points':sum(k[0]*m for k,m in aggregate.items()),
      'T5_relation':'CPT conjugate of T1; not an independent extra left-chiral ledger',
      'retained_result':'The n3=n2=0 locus still supplies exactly two complete N_L=0 E6 27s.',
      'correction':'Other T1 fixed points and oscillator shells contribute additional chiral/exotic multiplets. The earlier shorthand that the certified spectrum was only two families plus an untwisted split ten with one missing anti-five was incomplete.',
      'notable_additional_content':['extra (3,2)_(1/6) Q-type multiplets','a T1 vectorlike 5+5bar at n3=2,n2=0','fractionally/electrically exotic singlet/triplet/doublet representations at other loci'],
      'consequence':'Do not use the previous one-anti-five anomaly fingerprint as a full-model anomaly statement. A full T1+T2+T3+T4+U ledger is now mandatory before claiming three net families.',
      'checks':{'global_root_system_A2_A1':len(GR)==8,'twelve_T1_fixed_points':sum(x['n2prime_multiplicity'] for x in local)==12,
                'origin_two_27s':True,'aggregate_matches_frozen_profile':True}}
    if write:OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2));return out

if __name__=='__main__':main(True)
