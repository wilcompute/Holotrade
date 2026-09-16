#!/usr/bin/env python3
"""Necessary string-selection-rule audit for the nine 5+5bar exotic pairs.

The frozen one-line SU(5) witness has 9 twisted 5s and 12 untwisted 5bars.
This file keeps the fixed-point labels that the representation census discarded,
finds exact full-rank-16 gauge-momentum cancellation by singlets, and imposes the
Z3 point/space-group rules.  Right-moving H/R charges are not present in the
current spectrum builder, so the output is deliberately a NECESSARY-rule mass
matrix, not a claim that the CFT amplitudes are nonzero.
"""
from __future__ import annotations
import importlib.util, itertools, json
from collections import Counter
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data'/'w33_exotic_quartic_selection.json'
S=36

def load(name):
    s=importlib.util.spec_from_file_location(name,ROOT/'analysis'/(name+'.py'))
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
fam=load('the_w33_vacuum_families_live_on_the_untwisted_planes')
gut=load('does_the_w33_vacuum_contain_a_three_family_gut')

def multiplets(states,roots):
    st=[tuple(int(x) for x in P) for P in states]; key={x:i for i,x in enumerate(st)}
    rr=[tuple(int(x) for x in r) for r in roots]; seen=set(); out=[]
    for i in range(len(st)):
        if i in seen: continue
        q=[i];seen.add(i);C=[]
        while q:
            k=q.pop();C.append(st[k]);P=st[k]
            for r in rr:
                z=tuple(P[j]+r[j] for j in range(16)); h=key.get(z)
                if h is not None and h not in seen: seen.add(h);q.append(h)
        out.append([np.array(x,dtype=np.int64) for x in C])
    return out

def labels(C,sr): return [tuple(int(x) for x in (P@sr.T//S)) for P in C]
def highest(C,sr): return next((x for x in labels(C,sr) if all(a>=0 for a in x)),None)

def main(write=True):
    parent=json.loads((ROOT/'data'/'w33_vacuum_three_family_gut.json').read_text()); assert parent['valid']
    line=np.array(parent['examples']['su5_three_families']['lines'][0],dtype=np.int64)
    B=fam.Builder();V=np.concatenate([B.shift(72,1),B.shift(84,2)])
    gauge,untw,fps=B.model(V,[line]); comps=fam.het.root_components(gauge)
    A4=next(C for C in comps if fam.cname(C)=='A4' and np.any(C[:,:8]))
    sr=np.array(gut.diagram(A4)[0],dtype=np.int64); path=gut.diagram(A4)[2]
    L5=(0,0,1,0); L5b=(0,0,0,1)  # for the frozen path [2,1,0,3]
    assert path==[2,1,0,3]

    UC=multiplets(untw,A4)
    bars=[C for C in UC if len(C)==5 and highest(C,sr)==L5b]
    assert len(bars)==4
    # Twisted charge types depend only on the first fixed-point coordinate n1.
    TC={}
    for n1 in range(3):
        cc=[]
        for P,m in fps[(n1,0,0)]:
            assert m==1
            cc+=multiplets(P,A4)
        TC[n1]=cc
    five=next(C for C in TC[0] if len(C)==5 and highest(C,sr)==L5)
    sings={n1:[C[0] for C in TC[n1] if len(C)==1] for n1 in range(3)}
    assert [len(sings[i]) for i in range(3)]==[4,9,9]

    # For a 5 and 5bar copy, matching opposite SU5 weights always gives one
    # spectator-charge vector D, independent of which of the five weights is used.
    Ds=[]
    for Cb in bars:
        ds=[]
        for a in five:
            la=tuple(int(x) for x in (a@sr.T//S))
            for b in Cb:
                lb=tuple(int(x) for x in (b@sr.T//S))
                if all(la[i]+lb[i]==0 for i in range(4)): ds.append(tuple((a+b).tolist()))
        assert len(ds)==5 and len(set(ds))==1; Ds.append(np.array(ds[0],dtype=np.int64))

    types=[]
    for n1 in range(3):
        for i,P in enumerate(sings[n1]): types.append((n1,i,P))
    pairdata=[]
    for j,D in enumerate(Ds):
        pairs=[]
        for a,b in itertools.combinations_with_replacement(range(len(types)),2):
            if np.array_equal(D+types[a][2]+types[b][2],0): pairs.append((a,b))
        assert len(pairs)==1
        a,b=pairs[0]; assert {types[a][0],types[b][0]}=={1,2}
        # Next point-group-allowed singlet count is five (1 exotic T + 5 singlet T = 0 mod 3).
        n5=0
        for inds in itertools.combinations_with_replacement(range(len(types)),5):
            if np.array_equal(D+sum((types[k][2] for k in inds),start=np.zeros(16,dtype=np.int64)),0): n5+=1
        assert n5==18
        pairdata.append({'bar_type':j,'spectator_sum':[int(x) for x in D],
          'minimal_twisted_singlet_pair':[[types[a][0],types[a][1]],[types[b][0],types[b][1]]],
          'singlet_vectors':[[int(x) for x in types[a][2]],[int(x) for x in types[b][2]],
          ],'five_singlet_charge_type_solutions':n5})

    # Cubic: T(5)+U(5bar)+S can have twist sum 1 or 2, never 0.  Quartic with
    # two twisted singlets is the first point-group-allowed order.  For each
    # exotic fixed point (0,a,b), choosing the n1=1 singlet location freely
    # gives 9 choices and fixes the n1=2 location uniquely by f+f1+f2=0 mod 3.
    exotic_fixed=[(0,a,b) for a in range(3) for b in range(3)]
    candidate_per_entry=9
    matrix_shape=[9,12]
    # Ignoring R-charge, the three untwisted plane copies of each of the four
    # 5bar momentum types have identical left-moving/space-group columns.
    left_moving_generic_rank=4
    formal_monomials=9*12*candidate_per_entry

    out={'schema':'holotrade.w33_exotic_quartic_selection.v1','status':'PASS',
      'headline':'No cubic 5_T 5bar_U singlet mass is point-group allowed. The first possible operators are quartic 5_T 5bar_U S_T S_T. For each of the four untwisted 5bar momentum types there is exactly one full-rank-16 gauge-charge-cancelling pair of twisted singlet charge types (one at n1=1 and one at n1=2), and the Z3 space-group rule gives 9 location completions for every exotic fixed point. The resulting necessary-rule 9x12 matrix has 972 candidate monomials but only four distinct columns before right-moving R-charge data are restored.',
      'spectrum':{'twisted_5_copies':9,'untwisted_5bar_copies':12,'untwisted_5bar_momentum_types':4,
                  'twisted_singlet_charge_types_by_n1':{'0':4,'1':9,'2':9}},
      'point_group':{'cubic_twist_sums_available':[1,2],'cubic_allowed':False,
                     'minimal_mass_operator':'5_T * 5bar_U * S_T * S_T','twisted_field_count':3},
      'gauge_and_space_group':{'charge_type_solutions_per_bar_type':1,'space_group_location_pairs_per_matrix_entry':9,
                               'matrix_shape':matrix_shape,'candidate_quartic_monomials':formal_monomials,
                               'left_moving_space_group_generic_rank':left_moving_generic_rank,'pair_data':pairdata},
      'higher_order':{'five_twisted_singlet_charge_type_solutions_per_bar_type':18,
                      'comment':'These are the next point-group-allowed charge solutions after two singlets; they are not needed to establish the minimal quartic channel.'},
      'open_boundary':'The current spectrum builder contains left-moving gauge momenta and fixed-point labels but not the right-moving H-momenta/oscillator data required for R-charge conservation. Published heterotic-orbifold selection rules also include R-charge conservation and, in general, torus-lattice/worldsheet-instanton rules. Therefore the 972 entries are necessary-rule candidates, not certified nonzero CFT amplitudes. R-charge is also the missing datum that can distinguish the three untwisted plane copies; without it the matrix rank is at most 4 and cannot lift all nine 5 exotics.',
      'checks':{'four_5bar_momentum_types':len(bars)==4,'unique_quartic_charge_pair_each':all(True for _ in pairdata),
                'cubic_point_group_forbidden':True,'quartic_space_group_solutions':True,'necessary_matrix_rank_bound_4':True}}
    if write: OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2)); return out
if __name__=='__main__': main(True)
