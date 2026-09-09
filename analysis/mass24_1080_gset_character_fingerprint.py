#!/usr/bin/env python3
"""Exact representation-theoretic fingerprint of the two 1080-point PSp(4,3)-sets.

The unique mass-24 depth-three orbit and the existing obstruction carrier both
have degree 1080 and point stabilizer order 24, yet an explicit equivariant
bijection search found none.  This script explains *why* by working entirely in
PSp(4,3) acting faithfully on the 40 W(3,3) points.

For each action we recover the order-24 stabilizer of a base point.  Conjugacy
classes of the 25,920 projective group are generated exactly from the same four
certified transvections.  For a transitive G/H action,

    chi(g) = |C_G(g)| * |g^G cap H| / |H|.

Thus class intersections with the two stabilizers give both permutation
characters exactly.  From the characters we also obtain the orbital ranks
<chi,chi> and the complex permutation-module intertwiner dimension
<chi_mass,chi_obstruction>.

No physical interpretation is attached to these finite representation data.
"""
from __future__ import annotations

from collections import Counter, deque
from math import gcd
import json
import os
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
W33_ANALYSIS=os.environ.get("W33_ANALYSIS")
if W33_ANALYSIS:
    sys.path.insert(0,W33_ANALYSIS)

import mass24_depth3_steinberg_real_l1 as m24
import mass20_born_depth_and_extension_barcode as m20
import w33_20260829_216_clifford_torsor_nogo as wbase
import w33_20260901_obstruction_wedderburn_steinberg_projectors as obs

ORDER=25920
GENERATOR_INDICES=m24.GENERATOR_INDICES


def compose(a,b):
    """a o b for permutations stored as image tuples."""
    return tuple(a[b[i]] for i in range(len(a)))


def inv(p):
    q=[0]*len(p)
    for i,j in enumerate(p): q[j]=i
    return tuple(q)


def perm_order(p):
    seen=[False]*len(p); out=1
    for i in range(len(p)):
        if seen[i]: continue
        j=i; n=0
        while not seen[j]:
            seen[j]=True; n+=1; j=p[j]
        out=out*n//gcd(out,n)
    return out


def same_generators():
    pts,idx,wlines,_N=wbase.geometry()
    lidx={frozenset(L):i for i,L in enumerate(wlines)}
    all_point=[]; all_line=[]
    for v in pts:
        for alpha in (1,2):
            p=[]
            for q in pts:
                z=alpha*wbase.form(q,v)%3
                y=wbase.norm(tuple((q[k]+z*v[k])%3 for k in range(4)))
                p.append(idx[y])
            p=tuple(p); all_point.append(p)
            all_line.append(tuple(lidx[frozenset(p[q] for q in L)] for L in wlines))
    return pts,wlines,tuple(all_point),tuple(all_line)


def build_group_with_base_images(point_gens, mass_gens, obstruction_gens):
    ident=tuple(range(40))
    moves=[]
    for gp,gm,go in zip(point_gens,mass_gens,obstruction_gens):
        moves.append((gp,gm,go)); moves.append((inv(gp),inv(gm),inv(go)))
    image={ident:(0,0)}; q=deque([ident])
    while q:
        cur=q.popleft(); bm,bo=image[cur]
        for gp,gm,go in moves:
            nxt=compose(gp,cur); nm=gm[bm]; no=go[bo]
            if nxt not in image:
                image[nxt]=(nm,no); q.append(nxt)
            else:
                assert image[nxt]==(nm,no), "1080-action drift against faithful 40-point action"
    assert len(image)==ORDER
    return image, tuple(g for g,_,_ in moves)


def conjugacy_classes(elements, conjugators):
    E=set(elements); unseen=set(elements); out=[]
    invs={g:inv(g) for g in conjugators}
    while unseen:
        seed=min(unseen); cls={seed}; q=deque([seed])
        while q:
            x=q.popleft()
            for h in conjugators:
                y=compose(h,compose(x,invs[h]))
                assert y in E
                if y not in cls:
                    cls.add(y); q.append(y)
        unseen.difference_update(cls); out.append(frozenset(cls))
    out.sort(key=lambda C:(perm_order(min(C)),len(C),min(C)))
    assert sum(map(len,out))==ORDER
    return out


def main():
    pts,wlines,all_point,all_line=same_generators()
    h_lines,_,_=m24.sp.build_geometry()
    hidx={frozenset(L):i for i,L in enumerate(h_lines)}
    rep_w33=tuple(m24.REP[hidx[frozenset(L)]] for L in wlines)
    states,mass_selected=m24.mass_orbit_actions(rep_w33,tuple(all_line[i] for i in GENERATOR_INDICES))
    assert len(states)==1080
    obstruction_all,charts,wlines2=obs.build_action()
    assert tuple(map(frozenset,wlines2))==tuple(map(frozenset,wlines))
    point_selected=tuple(all_point[i] for i in GENERATOR_INDICES)
    obstruction_selected=tuple(obstruction_all[i] for i in GENERATOR_INDICES)

    image,conjugators=build_group_with_base_images(point_selected,mass_selected,obstruction_selected)
    Hm={g for g,(m,o) in image.items() if m==0}
    Ho={g for g,(m,o) in image.items() if o==0}
    assert len(Hm)==len(Ho)==24

    classes=conjugacy_classes(image.keys(),conjugators)
    rows=[]
    for ci,C in enumerate(classes):
        size=len(C); centralizer=ORDER//size
        hm=len(C & Hm); ho=len(C & Ho)
        assert (centralizer*hm)%24==0 and (centralizer*ho)%24==0
        cm=centralizer*hm//24; co=centralizer*ho//24
        rep=min(C)
        rows.append({
            "classIndex":ci,"elementOrder":perm_order(rep),"classSize":size,"centralizerOrder":centralizer,
            "massStabilizerIntersection":hm,"obstructionStabilizerIntersection":ho,
            "massCharacter":cm,"obstructionCharacter":co,
            "characterDifference":cm-co,
        })

    def inner(a,b):
        num=sum(r["classSize"]*r[a]*r[b] for r in rows)
        assert num%ORDER==0
        return num//ORDER

    rm=inner("massCharacter","massCharacter")
    ro=inner("obstructionCharacter","obstructionCharacter")
    hom=inner("massCharacter","obstructionCharacter")
    differing=[r for r in rows if r["characterDifference"]]
    hm_orders=Counter(perm_order(g) for g in Hm)
    ho_orders=Counter(perm_order(g) for g in Ho)
    fingerprint_mass=[r["massStabilizerIntersection"] for r in rows]
    fingerprint_obs=[r["obstructionStabilizerIntersection"] for r in rows]

    out={
      "schema":"holotrade.mass24-1080-gset-character-fingerprint.v1","status":"PASS",
      "groupOrder":ORDER,"degree":1080,"sameGeneratorIndices":list(GENERATOR_INDICES),
      "conjugacyClassCount":len(rows),
      "massStabilizerOrder":len(Hm),"obstructionStabilizerOrder":len(Ho),
      "massStabilizerElementOrderHistogram":{str(k):v for k,v in sorted(hm_orders.items())},
      "obstructionStabilizerElementOrderHistogram":{str(k):v for k,v in sorted(ho_orders.items())},
      "stabilizerClassIntersectionFingerprintsEqual":fingerprint_mass==fingerprint_obs,
      "permutationCharactersEqual":not differing,
      "differingCharacterClassCount":len(differing),
      "firstDifferingCharacterClasses":differing[:12],
      "massOrbitalRank":rm,"obstructionOrbitalRank":ro,
      "complexPermutationModuleHomDimension":hom,
      "massPermutationModuleEndDimension":rm,
      "obstructionPermutationModuleEndDimension":ro,
      "classTable":rows,
      "theorem":(
        "The two degree-1080 transitive PSp(4,3)-sets have different point-stabilizer conjugacy-class intersection fingerprints and hence different permutation characters. They are therefore not equivariantly isomorphic; the orbital ranks and cross Hom-space dimension give additional exact representation-theoretic invariants."
        if differing else
        "The two actions have equal permutation characters despite being non-isomorphic as certified by the direct equivariant-bijection search; they are a Gassmann-equivalent pair at the character level."
      ),
      "boundary":"Exact finite PSp(4,3) representation data only; no physical identification is implied by equal degree, stabilizer order, character constituents, or Hom-space dimension.",
    }
    path=HERE/"mass24_1080_gset_character_fingerprint_certificate.json"
    path.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:out[k] for k in ["status","conjugacyClassCount","permutationCharactersEqual","differingCharacterClassCount","massOrbitalRank","obstructionOrbitalRank","complexPermutationModuleHomDimension","massStabilizerElementOrderHistogram","obstructionStabilizerElementOrderHistogram"]},indent=2,sort_keys=True))
    print(f"written: {path}")

if __name__=="__main__": main()
