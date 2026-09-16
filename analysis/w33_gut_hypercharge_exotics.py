#!/usr/bin/env python3
"""Canonical SU(5) hypercharge and exotic-pairing audit for the frozen W33 GUT witness.

Continues data/w33_vacuum_three_family_gut.json.  This does NOT claim SU(5) is
already broken to the Standard Model.  It fixes the canonical SU(5) Cartan
hypercharge generator, computes k_Y, decomposes the exact witness content under
the selected SU(5), and asks whether the SU(5)-vectorlike exotics are also
conjugate under the complete rank-16 Cartan.
"""
from __future__ import annotations
import importlib.util, json
from collections import Counter
from fractions import Fraction
from pathlib import Path
import numpy as np
import sympy as sp

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data'/'w33_gut_hypercharge_exotics.json'
S=36

def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'analysis'/(name+'.py'))
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
fam=load('the_w33_vacuum_families_live_on_the_untwisted_planes')
gut=load('does_the_w33_vacuum_contain_a_three_family_gut')

def fundamental_weights(sr,A):
    Ai=sp.Matrix(A).inv(); out=[]
    for i in range(len(sr)):
        out.append([sum(Fraction(Ai[i,j])*int(sr[j][k]) for j in range(len(sr))) for k in range(16)])
    return out

def norm(v): return sum(x*x for x in v)/S
def dot(P,v): return sum(Fraction(int(P[i]))*v[i] for i in range(16))/S
def one(n,node):
    z=[0]*n; z[node]=1; return tuple(z)

def irrep_mults(C,states):
    sr,A,info=gut.diagram(C); M=gut.labels(states,sr); out={}
    for lam in [k for k in M if all(x>=0 for x in k)]:
        m=gut.N(M,A,list(lam))
        if m: out[tuple(lam)]=int(m)
    return sr,A,info,out

def full_opposite_pairing(states):
    c=Counter()
    for P,m in states:
        for row in P: c[tuple(int(x) for x in row)]+=int(m)
    seen=set(); paired=0
    for w,m in c.items():
        if w in seen: continue
        nw=tuple(-x for x in w); q=min(m,c.get(nw,0)); paired+=2*q; seen|={w,nw}
    return {'weighted_states':sum(c.values()),'opposite_paired_weighted_states':paired,
            'unmatched_weighted_states':sum(c.values())-paired}

def analyse_witness(tag,w,B,V):
    lines=[np.array(a,dtype=np.int64) for a in w['lines']]
    gauge,states=gut.model_states(B,V,lines); comps=fam.het.root_components(gauge)
    audits=[]
    for ci,C in enumerate(C for C in comps if fam.cname(C)=='A4'):
        fi=gut.family_indices(C,states); sr,A,info,mults=irrep_mults(C,states)
        p=info['path']; fw=fundamental_weights(sr,A)
        # A4 path p0-p1-p2-p3.  This is the conventional SU(5) hypercharge,
        # diag(-1/3,-1/3,-1/3,1/2,1/2), up to overall sign/Weyl conjugacy.
        Y=[-Fraction(5,6)*x for x in fw[p[2]]]
        yn=norm(Y); ky=2*yn
        reps={'5':one(4,p[0]),'10':one(4,p[1]),'10bar':one(4,p[2]),'5bar':one(4,p[3])}
        rm={name:mults.get(lam,0) for name,lam in reps.items()}
        # Conjugation follows reversal of the actual Dynkin path, not raw tuple reversal.
        pairs={'5_5bar':min(rm['5'],rm['5bar']),'10_10bar':min(rm['10'],rm['10bar'])}
        net={'10':rm['10']-rm['10bar'],'5bar':rm['5bar']-rm['5']}
        q=Counter()
        for P,m in states:
            for row in P: q[str(dot(row,Y))]+=int(m)
        extras={str(k):v for k,v in mults.items() if k not in set(reps.values()) and k!=(0,0,0,0)}
        audits.append({'component_index':ci,'family_indices':fi,'dynkin_path':p,
          'Y':'-(5/6) omega_3 in the displayed A4 path convention','Y_norm':str(yn),'k_Y':str(ky),
          'representation_multiplicities':rm,'SU5_vectorlike_pairs':pairs,'net_chiral_content':net,
          'other_nontrivial_SU5_irreps':extras,'SU5_singlets':mults.get((0,0,0,0),0),
          'hypercharge_weight_census':dict(sorted(q.items()))})
    return {'tag':tag,'gauge':sorted(fam.cname(C) for C in comps),'su5_components':audits,
            'full_cartan_pairing':full_opposite_pairing(states)}

def main(write=True):
    parent=json.loads((ROOT/'data'/'w33_vacuum_three_family_gut.json').read_text()); assert parent['valid']
    B=fam.Builder(); V=np.concatenate([B.shift(72,1),B.shift(84,2)])
    su=analyse_witness('su5_three_families',parent['examples']['su5_three_families'],B,V)
    so=analyse_witness('so10_three_families',parent['examples']['so10_three_families'],B,V)
    famsu=next(a for a in su['su5_components'] if a['family_indices'] and a['family_indices'].get('n10')==3 and a['family_indices'].get('n5bar')==3)
    checks={
      'parent_gut_witnesses_reverified':parent['checks']['witnesses_reverified'],
      'canonical_su5_hypercharge_norm_5_over_6':famsu['Y_norm']=='5/6',
      'canonical_kY_5_over_3':famsu['k_Y']=='5/3',
      'three_chiral_tens':famsu['net_chiral_content']['10']==3,
      'three_net_antifives':famsu['net_chiral_content']['5bar']==3,
      'nine_vectorlike_5_pairs_at_su5_level':famsu['SU5_vectorlike_pairs']['5_5bar']==9,
      'no_other_nontrivial_su5_irreps':not famsu['other_nontrivial_SU5_irreps'],
      'full_cartan_has_no_direct_opposite_pairs':su['full_cartan_pairing']['opposite_paired_weighted_states']==0,
    }; assert all(checks.values())
    out={
      'schema':'holotrade.w33_gut_hypercharge_exotics.v1','status':'PASS',
      'headline':'The frozen three-family SU(5) witness carries the canonical SU(5) hypercharge embedding with Y^2=5/6 and k_Y=5/3. Its selected SU(5) content is 3 chiral 10s plus net 3 anti-5s, together with nine SU(5)-vectorlike 5+anti-5 pairs and no other nontrivial SU(5) irreps. However none of the 405 weighted massless states pairs with its exact opposite under the full rank-16 Cartan, so the nine GUT-vectorlike pairs are charged under spectator factors/U(1)s and are not certified removable by a bare mass term.',
      'standard_model_branching':{'10':'(3,2)_{1/6} + (3bar,1)_{-2/3} + (1,1)_1','5bar':'(3bar,1)_{1/3} + (1,2)_{-1/2}','scope':'formal canonical SU(5)->SM branching; the level-1 witness still has unbroken SU(5), so an actual GUT-breaking mechanism remains open'},
      'su5_witness':su,'so10_witness_su5_audit':so,
      'exotic_boundary':'At the selected SU(5) factor the extra 9*(5+5bar) is vectorlike. Under the complete unbroken gauge Cartan those states have spectator charges and no exact P<->-P partners. Their removal therefore requires additional symmetry breaking, singlet VEVs, or allowed higher couplings; this certificate does not assume such dynamics.',
      'w33_boundary':'The one-line GUT witnesses contribute a single nonzero first-E8 Pauli projective point, and PSp(4,3) is transitive on the 40 points. Bare W33 point incidence therefore cannot distinguish the successful GUT witnesses; extra lattice/spectral/second-E8 data are required.',
      'checks':checks}
    if write: OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2)); return out
if __name__=='__main__': main(True)
