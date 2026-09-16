#!/usr/bin/env python3
"""Verify an explicit 56/120 alignment of the E8^3 root shadow with the Leech 90-tight set.

The Leech 3a reduction is regenerated from the existing exact Golay/Conway script.
F below maps its resulting F3^12 coordinates to the standard six-qutrit symplectic
basis.  In that basis the E8^3 root shadow is the union of the three 40-point
block-supported W(3,3)s.  The displayed map hits the Leech tight set in 56 points,
with block intersections 16+20+20.

This is an exact lower-bound witness, NOT a claim that 56 is globally maximal.
"""
from __future__ import annotations
import importlib.util, json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data'/'w33_e8cubed_leech_overlap56.json'
F=np.array([
[0,0,0,2,1,0,1,1,0,2,2,2],[0,1,1,1,0,0,0,2,0,2,1,0],
[1,2,0,2,2,2,2,1,1,2,1,0],[1,1,1,2,0,0,1,1,1,2,2,0],
[2,0,1,2,0,0,1,1,1,1,0,0],[1,0,0,0,0,0,0,2,1,1,0,0],
[1,1,0,2,0,2,0,2,1,1,0,0],[1,1,0,1,1,0,1,1,0,1,2,0],
[0,2,1,0,2,0,2,0,2,0,1,1],[0,1,0,1,0,2,2,1,1,1,2,0],
[1,1,0,2,1,2,0,1,0,1,2,0],[2,1,1,1,2,2,2,0,0,1,0,0]],dtype=np.int64)
J=np.zeros((12,12),dtype=np.int64)
for i in range(0,12,2): J[i,i+1]=1; J[i+1,i]=2

def load(name):
    s=importlib.util.spec_from_file_location(name,ROOT/'analysis'/(name+'.py'))
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
L=load('the_leech_rungs_are_the_suzuki_chain')

def main(write=True):
    code,octads,M,gens=L.leech(); key={tuple(v):i for i,v in enumerate(M)}
    g,pw=L.find_element(gens,M,key,3,-12,8,3)
    C,G,ok=L.reduce_mod_pi(M,pw,3,8,3)
    assert ok and np.array_equal((F@J@F.T)%3,G%3)
    T={L.proj_key(tuple((row@F)%3),3) for row in C if np.any(row)}
    assert len(T)==32760
    P4=sorted({L.proj_key(v,3) for v in __import__('itertools').product(range(3),repeat=4) if any(v)})
    blocks=[]
    for b in range(3):
        B=set()
        for p in P4:
            v=[0]*12; v[4*b:4*b+4]=p; B.add(L.proj_key(tuple(v),3))
        blocks.append(B)
    counts=[len(B&T) for B in blocks]; assert counts==[16,20,20]
    shadow=set().union(*blocks); assert len(shadow)==120 and len(shadow&T)==56
    support={1:0,2:0,3:0}
    for p in T:
        w=sum(any(p[4*b+j] for j in range(4)) for b in range(3)); support[w]+=1
    assert support=={1:56,2:1472,3:31232}
    out={
      'schema':'holotrade.w33_e8cubed_leech_overlap56.v1','status':'PASS',
      'headline':'An explicit symplectic identification of the Leech 3a quotient with the standard six-qutrit F3^12 phase space maps the E8^3 three-W33 root shadow onto 56 points of the 32760-point Leech 90-tight set, split 16+20+20 across the three W33 blocks.',
      'map_leech_coordinates_to_standard_F3_12':F.tolist(),
      'symplectic_identity':'F J_standard F^T = G_Leech mod 3',
      'overlap':{'root_shadow_points':120,'Leech_tight_points':32760,'overlap':56,'block_counts':counts,
                 'Leech_support_census_under_this_decomposition':{str(k):v for k,v in support.items()},
                 'random_120_set_expected_overlap':'1080/73 ~= 14.7945'},
      'search_boundary':'56 is a certified constructive lower bound from the deterministic search. No global-maximality claim is made by this certificate.',
      'checks':{'Leech_minimal_vectors_196560':len(M)==196560,'Leech_projective_tight_set_32760':len(T)==32760,
                'map_is_symplectic':True,'root_shadow_120':len(shadow)==120,'overlap_56':len(shadow&T)==56}
    }
    if write: OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2)); return out
if __name__=='__main__': main(True)
