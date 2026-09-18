#!/usr/bin/env python3
"""Close the T2/T4 anti-five route for the explicit Z6-II witness.

Implements the Z6-II fixed-torus projection of Chemtob--Hosteins, Appendix B:
for g=2,4 one imposes shifted-momentum integrality against W2,W2' and
  3[q_gamma + phi - (r+gv).v + (P+gV+n3 W3).V] in Z.
Here W2'=0.  Gamma=+1,-1 have geometric multiplicities D=1,2.

The third-family target is one net SM anti-five:
  d^c = (3bar,1)_(1/3),  L=(1,2)_(-1/2).

For T2 the only possible left oscillator energies below the mass shell are
N_L=0,1/3,2/3.  The exact shifted-lattice shells after the W2 projection are:
  N=0   : 28,16,16 states for n3=0,1,2;
  N=1/3 : 1,5,5 states;
  N=2/3 : empty.
The N=1/3 shells contain no d^c representation at all.  At N=0 the n3=2
d^c orbit occurs in both gamma sectors and both 4D chiralities; after the
D=(1,2) gamma multiplicities its d^c count is exactly balanced L=R=3.
T4 is the CPT partner fixed-torus sector.  Therefore T2/T4 cannot provide the
missing net chiral anti-five.

This is a targeted anti-five no-go, not a complete T2/T4 spectrum dump.
"""
from __future__ import annotations
import itertools,json,math
from collections import Counter
from fractions import Fraction as F
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/w33_z6ii_t2_t4_antifive_nogo.json'

def dot(a,b): return sum(x*y for x,y in zip(a,b))
def in_e8(p):
    if all(x.denominator==1 for x in p): return sum(int(x) for x in p)%2==0
    if all(x.denominator==2 and abs(x.numerator)%2==1 for x in p):
        s=sum(p); return s.denominator==1 and int(s)%2==0
    return False
def shell(sh,target):
    R=float(target)**.5;out=[]
    for half in (False,True):
        cand=[]
        for s in sh:
            lo=math.floor(float(-s-R))-2; hi=math.ceil(float(-s+R))+2
            vals=[]
            for n in range(lo,hi+1):
                p=F(n) if not half else F(2*n+1,2)
                if (p+s)**2<=target: vals.append(p)
            cand.append(vals)
        for P in itertools.product(*cand):
            if not in_e8(P): continue
            q=tuple(P[i]+sh[i] for i in range(8))
            if dot(q,q)==target: out.append((P,q))
    return out
def roots():
    out=[]
    for i,j in itertools.combinations(range(8),2):
        for si in (-1,1):
            for sj in (-1,1):
                v=[F(0)]*8;v[i]=F(si);v[j]=F(sj);out.append(tuple(v))
    for s in itertools.product((-1,1),repeat=8):
        if sum(x<0 for x in s)%2==0:out.append(tuple(F(x,2) for x in s))
    return out
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
        out.append(C)
    return out
def simple(C):
    g=[math.sqrt(p) for p in (2,3,5,7,11,13,17,19)]
    pos=[r for r in C if sum(float(r[i])*g[i] for i in range(8))>0]; ps=set(pos)
    return [r for r in pos if not any(tuple(r[i]-s[i] for i in range(8)) in ps for s in pos if s!=r)]
def orbits(qs,rs):
    Q=set(qs);rem=set(qs);out=[]
    while rem:
        seed=next(iter(rem));O={seed};st=[seed]
        while st:
            q=st.pop()
            for a in rs:
                d=dot(q,a);z=tuple(q[i]-d*a[i] for i in range(8))
                if z in Q and z not in O:O.add(z);st.append(z)
        out.append(O);rem-=O
    return out

V=(F(1,6),F(1,3),F(-1,2),0,0,0,0,0)
W2=(F(-1),F(1,2),0,F(-1),F(-1),F(-1,2),F(-1,2),F(-1,2))
W3=(F(-2,3),F(-2,3),F(2,3),0,F(2,3),F(-1,3),F(-1,3),0)
Y=tuple(F(x,12) for x in (-1,-1,-1,5,-7,3,3,-5))
v=(F(1,6),F(1,3),F(-1,2),0)
rL=(0,0,1,0);rR=(-1,-1,1,0)
R=roots();GR=[a for a in R if all(dot(a,s).denominator==1 for s in (V,W2,W3))]
CS=comps(GR);A2=next(C for C in CS if len(C)==6);A1=next(C for C in CS if len(C)==2);S=simple(A2)+simple(A1)
def label(O):
    hs=[]
    for q in O:
        l=tuple(dot(q,a) for a in S)
        if all(x>=0 for x in l):hs.append(l)
    assert len(hs)==1
    yy={dot(Y,q) for q in O};assert len(yy)==1
    return (len(O),tuple(int(x) for x in hs[0]),next(iter(yy)))
def project(q,chir,gamma):
    r=rL if chir=='L' else rR; qg=F(0) if gamma==1 else F(1,2)
    rg=tuple(F(r[i])+2*v[i] for i in range(4))
    return (3*(qg-dot(rg,v)+dot(q,V))).denominator==1

def main(write=True):
    rows=[];dc_balance=None
    for N,target in ((F(0),F(14,9)),(F(1,3),F(8,9)),(F(2,3),F(2,9))):
        for n3 in range(3):
            sh=tuple(2*V[i]+n3*W3[i] for i in range(8))
            qs=[q for P,q in shell(sh,target) if dot(q,W2).denominator==1]
            prof=Counter(label(O) for O in orbits(qs,GR))
            row={'N_L':str(N),'n3':n3,'states_after_W2':len(qs),
                 'reps':{f'{d}|{h}|{y}':m for (d,h,y),m in sorted(prof.items(),key=str)}}
            if N==0:
                pp={}
                for chir in ('L','R'):
                    for gamma,D in ((1,1),(-1,2)):
                        qg=[q for q in qs if project(q,chir,gamma)]
                        p=Counter(label(O) for O in orbits(qg,GR))
                        pp[f'{chir}_gamma{gamma:+d}']={'D':D,'states':len(qg),
                            'reps':{f'{d}|{h}|{y}':m for (d,h,y),m in sorted(p.items(),key=str)}}
                row['gamma_projection']=pp
                if n3==2:
                    key="3|(0, 1, 0)|1/3"
                    L=sum(pp[f'L_gamma{g:+d}']['D']*pp[f'L_gamma{g:+d}']['reps'].get(key,0) for g in (1,-1))
                    RR=sum(pp[f'R_gamma{g:+d}']['D']*pp[f'R_gamma{g:+d}']['reps'].get(key,0) for g in (1,-1))
                    dc_balance={'left':L,'right':RR}
                    assert L==RR==3
            rows.append(row)
    n13=[x for x in rows if x['N_L']=='1/3']
    assert [x['states_after_W2'] for x in n13]==[1,5,5]
    assert all('3|(0, 1, 0)|1/3' not in x['reps'] for x in n13)
    assert all(x['states_after_W2']==0 for x in rows if x['N_L']=='2/3')
    out={'schema':'w33.z6ii_t2_t4_antifive_nogo.v1','status':'PASS_TARGETED_NO_GO',
      'literature_projection':'Z6-II T2/T4 fixed-torus GSO: gamma=+1,-1 with D=1,2; B.7/B.8 shifted-momentum and phase conditions',
      'shells':rows,'n3_2_N0_dc_gamma_weighted_balance':dc_balance,
      'conclusion':'T2/T4 do not supply the missing net chiral third-family anti-five. N=1/3 has no d^c at all, N=2/3 is empty, and the only N=0 d^c candidate is L/R balanced before adding the CPT-related T4 partner.',
      'next_target':'T1 oscillator shells or another genuinely N=1 chiral sector; fixed-torus N=2 sectors are not the source of the missing net family chirality.',
      'boundary':'Targeted d^c+L chirality no-go, not a complete published T2/T4 spectrum or coupling calculation.'}
    if write:OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2));return out
if __name__=='__main__':main(True)
