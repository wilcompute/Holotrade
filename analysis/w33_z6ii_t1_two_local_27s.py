#!/usr/bin/env python3
"""Two complete local E6 27s and their exact SM decomposition in the Z6-II witness.

The parent local-shell certificate proves that the two T1 fixed points with local
shift V each carry one unoscillated 27-weight Weyl orbit of the local E6.

Classical Z6-II projection input: massless T1 solutions are twist invariant and
survive in four dimensions as complete multiplets of the local gauge group.
This is the standard local-GUT mechanism used in the heterotic mini-landscape.

Here we add an internal computation: restrict the exact 27 shifted momenta to
the globally surviving A2+A1 roots and the canonical kY=5/3 hypercharge of the
parent gauge-embedding certificate.  The 27 decomposes exactly as

 (3,2)_(1/6) + (3bar,1)_(-2/3) + 2(3bar,1)_(1/3)
 + (3,1)_(-1/3) + 2(1,2)_(-1/2) + (1,2)_(1/2)
 + (1,1)_1 + 2(1,1)_0.

This is 16+10+1 under SO(10): one complete SM family (including nu^c),
one vectorlike 5+5bar exotic/Higgs package, and one extra singlet.

Boundary: two complete localized family multiplets are certified; a third net
family, global anomaly accounting, exotic decoupling and the full spectrum of
T2/T3/T4/T5 and untwisted sectors remain open.
"""
from __future__ import annotations
import itertools,json,math
from collections import Counter
from fractions import Fraction as F
from pathlib import Path

import w33_z6ii_t1_local_e6_shell as base

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/w33_z6ii_t1_two_local_27s.json'

def simple_roots(C):
    primes=[2,3,5,7,11,13,17,19]
    gen=[math.sqrt(p) for p in primes]
    pos=[r for r in C if sum(float(r[i])*gen[i] for i in range(8))>0]
    ps=set(pos);out=[]
    for r in pos:
        if not any(tuple(r[i]-s[i] for i in range(8)) in ps for s in pos if s!=r):
            out.append(r)
    assert len(out)==base.rankq(C)
    return out

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
    shell_parent=json.loads((ROOT/'data/w33_z6ii_t1_local_e6_shell.json').read_text())
    emb=json.loads((ROOT/'data/w33_z6ii_sm_shape_builder.json').read_text())
    assert shell_parent['status']=='PASS_LOCAL_SHELL_NOT_4D_SPECTRUM'
    assert shell_parent['E6_fixed_points']['count']==2
    V=tuple(map(F,emb['embedding']['V6']))
    W2=tuple(map(F,emb['embedding']['W2']))
    W3=tuple(map(F,emb['embedding']['W3']))
    Y=tuple(map(F,emb['SU5_to_SM']['hypercharge_Y']))
    R=base.e8_roots()
    global_roots=[r for r in R if all(base.dot(r,s).denominator==1 for s in (V,W2,W3))]
    cs=base.components(global_roots)
    A2=next(C for C in cs if len(C)==6)
    A1=next(C for C in cs if len(C)==2)
    a2=simple_roots(A2);a1=simple_roots(A1)
    assert len(a2)==2 and len(a1)==1
    simps=a2+a1

    qs=base.shifted_shell(V);assert len(qs)==27
    O=orbits(qs,global_roots)
    rows=[]
    for orb in O:
        labels=[]
        for q in orb:
            lab=tuple(base.dot(q,a) for a in simps)
            if all(x>=0 for x in lab): labels.append(lab)
        assert len(labels)==1
        lab=labels[0];ych={base.dot(Y,q) for q in orb};assert len(ych)==1
        rows.append({'dimension':len(orb),'A2_highest':[int(lab[0]),int(lab[1])],
                     'A1_highest':int(lab[2]),'Y':str(next(iter(ych)))})
    profile=Counter((r['dimension'],tuple(r['A2_highest']),r['A1_highest'],r['Y']) for r in rows)
    expected=Counter({
      (6,(1,0),1,'1/6'):1,
      (3,(0,1),0,'-2/3'):1,
      (3,(0,1),0,'1/3'):2,
      (3,(1,0),0,'-1/3'):1,
      (2,(0,0),1,'-1/2'):2,
      (2,(0,0),1,'1/2'):1,
      (1,(0,0),0,'1'):1,
      (1,(0,0),0,'0'):2})
    assert profile==expected and sum(r['dimension'] for r in rows)==27

    out={
      'schema':'w33.z6ii_t1_two_local_27s.v1',
      'status':'PASS_WITH_CLASSICAL_T1_PROJECTION_INPUT',
      'local_family_count':2,
      'reason':'W2prime=0 makes the n3=0,n2=0 local E6 point occur at both n2prime=0,1; each has the same 27-weight massless shell',
      'classical_projection_input':'In Z6-II, massless T1 solutions are twist invariant and survive in 4D as complete local-GUT multiplets.',
      'global_group':'SU(3)xSU(2)xU(1)_Y subgroup with kY=5/3',
      'one_27_decomposition':{
        '(3,2)_1/6':1,'(3bar,1)_-2/3':1,'(3bar,1)_1/3':2,
        '(3,1)_-1/3':1,'(1,2)_-1/2':2,'(1,2)_1/2':1,
        '(1,1)_1':1,'(1,1)_0':2},
      'one_27_interpretation':{
        'SO10_16':'one SM family Q,u^c,d^c,L,e^c,nu^c',
        'SO10_10':'vectorlike SU5 5+5bar = color triplet pair plus doublet pair',
        'SO10_1':'one additional singlet'},
      'two_fixed_points_consequence':'two complete localized SM-family multiplets plus two local vectorlike 10 packages and two extra singlets before studying cross-sector masses',
      'third_family_status':'OPEN; must arise from untwisted/bulk or T2/T3/T4/T5 sectors if the final model has three net families',
      'projection_sources':[
        'Buchmueller et al., heterotic mini-landscape Z6-II: T1 massless states are twist invariant and complete local GUT multiplets',
        'Wingerter, Aspects of Grand Unification in Higher Dimensions: explicit T1 mass equations and complete 27 multiplets in standard embedding'],
      'boundary':'This does not yet establish three net families or an MSSM spectrum; oscillator states, all other sectors, vectorlike pairing, anomalies and flatness remain to be assembled globally.',
      'checks':{'two_E6_points':True,'27_shell_each':True,'global_A2_A1':True,
                'exact_27_SM_decomposition':True,'dimensions_sum_27':True}}
    if write:OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2));return out

if __name__=='__main__':main(True)
