#!/usr/bin/env python3
"""Standard-selection-rule cubic mass channel for both local vectorlike 5+5bar packages.

The two T1 local E6 fixed points each carry one 27=16+10+1.  Under SU5, the
SO10 10 is a vectorlike 5+5bar.  We search the physical T4 N_L=0 singlet shell
for a state s such that the *full eight-dimensional shifted gauge momentum*
obeys q_5 + q_5bar + s = 0 for every component of one 5 and one of the two
5bar copies in the 27.

There is exactly such a channel with
  s=(1,-1,-3,3,3,3,3,3)/6,
a T4, n3=0 SM singlet.  Its unshifted lattice momentum s-4V is in E8, its norm
is 14/9, it passes q.W2 in Z, and the Z6-II B.8 T4 projection keeps it in the
left-chiral gamma=+1 sector.

The complete 5 orbit is translated by -s onto one complete 5bar orbit:
  q_bar = -s-q
for all three color-triplet weights and both weak-doublet weights.  Thus all
five component mass terms conserve the entire rank-8 first-E8 Cartan, not only
SM quantum numbers.

The ordinary orbifold coupling rules also pass:
  * point group: T1 T1 T4 -> 1+1+4=0 mod 6;
  * H momentum (no oscillators): 2*(-1,-2,-3)/6 + (-2,-1,0)/3
    = (-1,-1,-1), the required cubic value;
  * n3 fixed-point labels: 0+0+0=0 mod3;
  * for either local-E6 copy n2'=a, a+a=0 mod2;
  * gamma product: 1*1*1=1.

Therefore a VEV of this T4 singlet is a certified *standard-selection-rule*
mass channel for the vectorlike 5+5bar in each localized 27.

Boundary: modern heterotic-orbifold coupling analyses include extra worldsheet
instanton Rule 4/5/6 constraints.  Their evaluation and the actual nonzero CFT
coefficient are not yet certified here, so "the exotics decouple" is not yet
claimed.
"""
from __future__ import annotations
import itertools,json,math
from fractions import Fraction as F
from pathlib import Path
import w33_z6ii_t1_local_e6_shell as base
import w33_z6ii_t1_two_local_27s as fam

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/w33_z6ii_local_vectorlike_cubic_mass_channel.json'
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def in_e8(p):
    if all(x.denominator==1 for x in p):return sum(int(x) for x in p)%2==0
    if all(x.denominator==2 and abs(x.numerator)%2==1 for x in p):
        z=sum(p);return z.denominator==1 and int(z)%2==0
    return False
def shell(sh,target):
    R=float(target)**.5;out=[]
    for half in (False,True):
        cand=[]
        for s in sh:
            lo=math.floor(float(-s-R))-2;hi=math.ceil(float(-s+R))+2;vals=[]
            for n in range(lo,hi+1):
                p=F(n) if not half else F(2*n+1,2)
                if (p+s)**2<=target:vals.append(p)
            cand.append(vals)
        for P in itertools.product(*cand):
            if not in_e8(P):continue
            q=tuple(P[i]+sh[i] for i in range(8))
            if dot(q,q)==target:out.append(q)
    return sorted(set(out))
def orbit(qs,roots):
    Q=set(qs);rem=set(qs);out=[]
    while rem:
        x=next(iter(rem));O={x};st=[x]
        while st:
            q=st.pop()
            for a in roots:
                d=dot(q,a);z=tuple(q[i]-d*a[i] for i in range(8))
                if z in Q and z not in O:O.add(z);st.append(z)
        out.append(O);rem-=O
    return out

def main(write=True):
    emb=json.loads((ROOT/'data/w33_z6ii_sm_shape_builder.json').read_text())
    V=tuple(map(F,emb['embedding']['V6']));W2=tuple(map(F,emb['embedding']['W2']));W3=tuple(map(F,emb['embedding']['W3']))
    Y=tuple(map(F,emb['SU5_to_SM']['hypercharge_Y']))
    R=base.e8_roots(); GR=[r for r in R if all(dot(r,a).denominator==1 for a in (V,W2,W3))]
    cs=base.components(GR);A2=next(C for C in cs if len(C)==6);A1=next(C for C in cs if len(C)==2)
    S=fam.simple_roots(A2)+fam.simple_roots(A1)
    def lab(O):
        hs=[]
        for q in O:
            z=tuple(dot(q,a) for a in S)
            if all(x>=0 for x in z):hs.append(z)
        assert len(hs)==1
        yy={dot(Y,q) for q in O};assert len(yy)==1
        return len(O),tuple(int(x) for x in hs[0]),next(iter(yy))
    t1=base.shifted_shell(V); O1=orbit(t1,GR)
    five3=next(O for O in O1 if lab(O)==(3,(1,0,0),F(-1,3)))
    five2=next(O for O in O1 if lab(O)==(2,(0,0,1),F(1,2)))
    bars3=[O for O in O1 if lab(O)==(3,(0,1,0),F(1,3))]
    bars2=[O for O in O1 if lab(O)==(2,(0,0,1),F(-1,2))]
    assert len(bars3)==2 and len(bars2)==2

    s=tuple(F(x,6) for x in (1,-1,-3,3,3,3,3,3))
    Ps=tuple(s[i]-4*V[i] for i in range(8))
    assert in_e8(Ps) and dot(s,s)==F(14,9) and dot(s,W2).denominator==1 and dot(s,Y)==0
    t4=shell(tuple(4*x for x in V),F(14,9));assert s in t4
    # unique bar orbits matched by the same singlet translation.
    def match(A,B):return len(A)==len(B) and all(tuple(-s[i]-q[i] for i in range(8)) in B for q in A)
    mb3=[B for B in bars3 if match(five3,B)];mb2=[B for B in bars2 if match(five2,B)]
    assert len(mb3)==len(mb2)==1
    assert all(tuple(-s[i]-q[i] for i in range(8)) in mb3[0] for q in five3)
    assert all(tuple(-s[i]-q[i] for i in range(8)) in mb2[0] for q in five2)

    # T4 left-chiral gamma=+1 projection, B.8 with N=0.
    v=(F(1,6),F(1,3),F(-1,2),0);r=(0,-1,2,0);g=4
    rg=tuple(F(r[i])+g*v[i] for i in range(4))
    phase=3*(-dot(rg,v)+dot(s,V))
    assert phase.denominator==1
    # no-oscillator H momenta from standard Z6-II table.
    h1=(F(-1,6),F(-1,3),F(-1,2));h4=(F(-2,3),F(-1,3),F(0))
    hsum=tuple(2*h1[i]+h4[i] for i in range(3));assert hsum==(F(-1),F(-1),F(-1))
    out={'schema':'w33.z6ii_local_vectorlike_cubic_mass_channel.v1','status':'PASS_STANDARD_SELECTION_RULES_RULE456_OPEN',
      'channel':'T1(local E6 5) * T1(local E6 5bar_exotic) * T4 singlet',
      'T4_singlet':{'shifted_gauge_momentum':[str(x) for x in s],'unshifted_P':[str(x) for x in Ps],
        'norm':'14/9','n3':0,'SM':'(1,1)_0','W2_integral':True,'left_gamma':'+1','gamma_multiplicity':1,'B8_phase_integer':str(phase)},
      'full_cartan_momentum_conservation':{
        'triplet_orbit_size':3,'doublet_orbit_size':2,
        'identity':'q_5bar=-s-q_5 for every weight in both SU5 components',
        'rank8_first_E8_gauge_invariance':True},
      'ordinary_selection_rules':{
        'point_group':'1+1+4=6=0 mod6',
        'H_momentum':'2*(-1,-2,-3)/6 + (-2,-1,0)/3 = (-1,-1,-1)',
        'n3_space_group':'0+0+0=0 mod3',
        'SO4_fixed_point':'for either local copy n2prime=a, a+a=0 mod2; T4 is a fixed torus',
        'gamma_product':'1*1*1=1'},
      'two_local_copies':'The same T4 fixed-torus singlet channel applies to both n2prime=0 and n2prime=1 local-E6 27s.',
      'consequence':'If this T4 singlet acquires a VEV and the deeper worldsheet rules/coefficient are nonzero, both localized vectorlike 5+5bar packages have a cubic mass channel.',
      'open_rules':['Rule 4 enhanced torus-lattice symmetry','Rule 5 worldsheet-instanton existence','Rule 6 coset-vector rule','actual CFT coefficient','flat direction containing this singlet VEV'],
      'boundary':'Standard gauge, point-group, space-group, gamma and H-momentum rules pass exactly; exotic decoupling is not claimed until the open worldsheet rules and vacuum are checked.'}
    if write:OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2));return out
if __name__=='__main__':main(True)
