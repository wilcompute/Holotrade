#!/usr/bin/env python3
"""Untwisted Z6-II spectrum of the explicit W33 even-order witness.

For an untwisted internal gauge-field chiral multiplet U_i, the root P obeys
  P.W2, P.W3 in Z,   P.V = v_i mod 1
in the convention used here.  The conjugate phases -v_i give the CPT-conjugate
weights.

For the explicit modular-compatible witness, exact E8-root enumeration gives:
  U1 (v1=1/6): (3bar,1)_(-2/3) + (1,1)_1  = u^c + e^c
  U2 (v2=1/3): (3,2)_(1/6)                 = Q
  U3 (v3=1/2): (1,2)_(1/2)+(1,2)_(-1/2)+2(1,1)_0.

Thus U1+U2 form an exact split SU(5) ten of a third family, while U3 contains
a vectorlike Higgs-doublet pair.  The missing d^c+L anti-five must come from
a twisted sector if the complete model has a third family.
"""
from __future__ import annotations
import itertools,json,math
from collections import Counter
from fractions import Fraction as F
from pathlib import Path

import w33_z6ii_t1_local_e6_shell as base
import w33_z6ii_t1_two_local_27s as fam

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/w33_z6ii_untwisted_split_ten.json'

def mod1(x):return x%1

def orbits(qs,roots):
    Q=set(qs);rem=set(qs);out=[]
    while rem:
        seed=next(iter(rem));O={seed};st=[seed]
        while st:
            q=st.pop()
            for a in roots:
                d=base.dot(q,a);z=tuple(q[i]-d*a[i] for i in range(8))
                if z in Q and z not in O:O.add(z);st.append(z)
        out.append(O);rem-=O
    return out

def main(write=True):
    emb=json.loads((ROOT/'data/w33_z6ii_sm_shape_builder.json').read_text())
    V=tuple(map(F,emb['embedding']['V6']));W2=tuple(map(F,emb['embedding']['W2']));W3=tuple(map(F,emb['embedding']['W3']))
    Y=tuple(map(F,emb['SU5_to_SM']['hypercharge_Y']))
    R=base.e8_roots()
    global_roots=[r for r in R if all(base.dot(r,s).denominator==1 for s in (V,W2,W3))]
    cs=base.components(global_roots)
    A2=next(C for C in cs if len(C)==6);A1=next(C for C in cs if len(C)==2)
    simps=fam.simple_roots(A2)+fam.simple_roots(A1)
    phases=[F(1,6),F(1,3),F(1,2)]
    rows=[]
    profiles=[]
    for plane,ph in enumerate(phases,1):
        weights=[p for p in R if base.dot(p,W2).denominator==1 and base.dot(p,W3).denominator==1 and mod1(base.dot(p,V))==ph]
        O=orbits(weights,global_roots); reps=[]
        for orb in O:
            highs=[]
            for q in orb:
                lab=tuple(base.dot(q,a) for a in simps)
                if all(x>=0 for x in lab):highs.append(lab)
            assert len(highs)==1
            y={base.dot(Y,q) for q in orb};assert len(y)==1
            reps.append({'dimension':len(orb),'A2_highest':[int(highs[0][0]),int(highs[0][1])],
                         'A1_highest':int(highs[0][2]),'Y':str(next(iter(y)))})
        rows.append({'plane':plane,'phase':str(ph),'root_weights':len(weights),'representations':reps})
        profiles.append(Counter((x['dimension'],tuple(x['A2_highest']),x['A1_highest'],x['Y']) for x in reps))
    assert profiles[0]==Counter({(3,(0,1),0,'-2/3'):1,(1,(0,0),0,'1'):1})
    assert profiles[1]==Counter({(6,(1,0),1,'1/6'):1})
    assert profiles[2]==Counter({(2,(0,0),1,'1/2'):1,(2,(0,0),1,'-1/2'):1,(1,(0,0),0,'0'):2})

    out={
      'schema':'w33.z6ii_untwisted_split_ten.v1','status':'PASS',
      'projection_rule':'P.W2,P.W3 integral and P.V=v_i mod 1 for chiral U_i; -v_i gives conjugate weights',
      'planes':rows,
      'SM_reading':{
        'U1':'u^c + e^c',
        'U2':'Q',
        'U1_plus_U2':'exact split third-family SU5 ten = Q+u^c+e^c',
        'U3':'one vectorlike electroweak doublet pair plus two neutral singlets'},
      'even_order_crosscheck':'The u^c/e^c pairing occurs because the order-two Wilson character has t=1/2, exactly the previously proved all-orders splitting theorem.',
      'missing_third_family_piece':'d^c + L = one SU5 anti-five, which must be supplied by a twisted sector for a complete third family',
      'boundary':'Exact untwisted root-spectrum theorem. It does not yet identify the twisted anti-five, compute all singlets/exotics, or establish net three-family chirality globally.',
      'checks':{'global_SM_roots':len(global_roots)==8,'U1_uc_ec':True,'U2_Q':True,'U3_vectorlike_doublets':True,'split_ten_complete':True}}
    if write:OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2));return out

if __name__=='__main__':main(True)
