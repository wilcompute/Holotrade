#!/usr/bin/env python3
"""Structural classification of the five mass-28 children of the depth-3 parent.

Let e be the unique mass-24 depth-three representative and P_p the pencil at
point p.  On integer preimages, e -> e+P_p is exactly x -> x+unit_p.
Therefore

    depth(e+P_p) <= depth(e)-1

iff there exists an *optimal* preimage x of e with x_p < 0.  The reverse
implication follows by subtracting unit_p from any child preimage of depth at
most d-1.  This gives an intrinsic, stabilizer-invariant predictor of when a
pencil child drops from depth three to depth two.

For this parent, optimal negative mass is 3 and total point coefficient sum is
6, hence every optimal preimage has negative mass 3 and positive mass 9.  The
feasibility search is therefore finite with -3 <= x_p <= 9 and is exact.

We also recover the parent stabilizer (order 24) inside PSp(4,3), compute its
five point orbits, and attach simple local incidence signatures to each orbit.
"""
from __future__ import annotations

from collections import Counter, deque
import json
from pathlib import Path

from ortools.sat.python import cp_model

import mass20_born_depth_and_extension_barcode as m20
import mass24_depth3_steinberg_real_l1 as m24
import mass24_1080_gset_character_fingerprint as fp
import mass28_depth4_birth_frontier as m28

HERE=Path(__file__).resolve().parent
PARENT=m28.PARENT
DEPTH=3


def addv(a,b): return tuple(x+y for x,y in zip(a,b))


def optimal_negative_support(lines):
    """Exact set of p for which an optimum depth-3 preimage can have x_p<0."""
    out=[]; witnesses={}
    for target in range(40):
        model=cp_model.CpModel()
        x=[model.NewIntVar(-3,9,f"x{i}") for i in range(40)]
        n=[]
        for i in range(40):
            z=model.NewIntVar(0,3,f"n{i}")
            model.AddMaxEquality(z,[0,-x[i]]); n.append(z)
        model.Add(sum(n)==DEPTH)
        model.Add(sum(x)==6)
        for li,L in enumerate(lines): model.Add(sum(x[p] for p in L)==int(PARENT[li]))
        model.Add(x[target] <= -1)
        sv=cp_model.CpSolver(); sv.parameters.num_workers=8; sv.parameters.max_time_in_seconds=20
        st=sv.Solve(model)
        if st in (cp_model.OPTIMAL,cp_model.FEASIBLE):
            w=tuple(int(sv.Value(v)) for v in x)
            assert sum(-v for v in w if v<0)==3 and w[target]<0
            out.append(target); witnesses[target]=w
        else:
            assert st==cp_model.INFEASIBLE, f"point {target} support feasibility unresolved: {sv.StatusName(st)}"
    return frozenset(out),witnesses


def parent_stabilizer_point_orbits():
    pts,wlines,all_point,all_line=fp.same_generators()
    h_lines,_,_=m24.sp.build_geometry(); hidx={frozenset(L):i for i,L in enumerate(h_lines)}
    rep_w33=tuple(PARENT[hidx[frozenset(L)]] for L in wlines)
    states,mass_selected=m24.mass_orbit_actions(rep_w33,tuple(all_line[i] for i in fp.GENERATOR_INDICES))
    point_selected=tuple(all_point[i] for i in fp.GENERATOR_INDICES)
    # Use the mass action twice; only the first base-image coordinate matters.
    image,_=fp.build_group_with_base_images(point_selected,mass_selected,mass_selected)
    H={g for g,(bm,_dummy) in image.items() if bm==0}
    assert len(H)==24
    rem=set(range(40)); orbits=[]
    while rem:
        seed=min(rem); O={g[seed] for g in H}
        # H is a group, so a single image set is the full orbit.
        rem.difference_update(O); orbits.append(tuple(sorted(O)))
    orbits.sort(key=lambda O:(len(O),O))
    assert sum(map(len,orbits))==40
    return H,orbits


def child_depths(lines,pencils,gens):
    rows={}
    by_point={}
    for p,pen in enumerate(pencils):
        child=addv(PARENT,pen); ob=m20.orbit(child,gens); rep=min(ob)
        if rep not in rows:
            exact=m20.exact_depth(rep,lines,budget=60)
            assert exact is not None
            rows[rep]={"representative":rep,"representativeDigest":m20.digest(rep),"orbitSize":len(ob),"exactDepth":exact[0],"exactPreimage":exact[1],"seedPoints":[]}
        rows[rep]["seedPoints"].append(p); by_point[p]=rows[rep]
    assert len(rows)==5
    return rows,by_point


def main():
    lines,thru,pencils,adj,gens,order=m20.geometry_data(); assert order==25920
    support,witnesses=optimal_negative_support(lines)
    H,point_orbits=parent_stabilizer_point_orbits()
    child_rows,by_point=child_depths(lines,pencils,gens)

    types=[]
    for oi,O in enumerate(point_orbits):
        ds={by_point[p]["exactDepth"] for p in O}; assert len(ds)==1
        child_keys={by_point[p]["representative"] for p in O}; assert len(child_keys)==1
        p=O[0]; vals=tuple(sorted(PARENT[L] for L in thru[p])); neg_flags={q in support for q in O}; assert len(neg_flags)==1
        r=by_point[p]
        types.append({
          "stabilizerPointOrbitIndex":oi,"pointOrbitSize":len(O),"points":list(O),
          "pointStabilizerOrderInsideParentStabilizer":24//len(O),
          "parentIncidentLineValueMultiset":list(vals),"parentIncidentLineValueHistogram":{str(k):v for k,v in sorted(Counter(vals).items())},
          "parentIncidentLineValueSum":sum(vals),
          "canBeNegativeInOptimalParentPreimage":p in support,
          "childRepresentativeDigest":r["representativeDigest"],"childOrbitSize":r["orbitSize"],"childExactDepth":r["exactDepth"],
          "depthDropsByOne":r["exactDepth"]==2,
        })

    support_equals_drop={p for p in range(40) if by_point[p]["exactDepth"]<=2}==set(support)
    assert support_equals_drop
    assert Counter(t["childExactDepth"] for t in types)==Counter({3:3,2:2})
    simple_signature_predicts=True
    seen={}
    for t in types:
        sig=tuple(t["parentIncidentLineValueMultiset"])
        if sig in seen and seen[sig]!=t["childExactDepth"]: simple_signature_predicts=False
        seen[sig]=t["childExactDepth"]

    out={
      "schema":"holotrade.mass28-depth3-descendant-structure.v1","status":"PASS",
      "groupOrder":order,"parentOrbitSize":1080,"parentStabilizerOrder":24,"parentDepth":3,
      "parentStabilizerPointOrbitCount":len(point_orbits),"pointOrbitSizes":[len(O) for O in point_orbits],
      "optimalParentNegativeSupportSize":len(support),"optimalParentNegativeSupport":sorted(support),
      "negativeSupportOrbitIndices":[t["stabilizerPointOrbitIndex"] for t in types if t["canBeNegativeInOptimalParentPreimage"]],
      "childDepthHistogram":{str(k):v for k,v in sorted(Counter(t["childExactDepth"] for t in types).items())},
      "fiveStructuralTypes":types,
      "optimalNegativeSupportExactlyPredictsDepthDrop":support_equals_drop,
      "incidentValueMultisetAlonePredictsDepthOnTheseFiveTypes":simple_signature_predicts,
      "theorem":"For any point p, the child e+P_p has depth at most 2 iff p is negative in some depth-3 optimal preimage of the parent. For the unique mass-24 depth-3 orbit, the parent stabilizer has five point orbits; exactly two lie in this intrinsic optimal-negativity support and they are exactly the two depth-2 child classes, while the other three remain depth 3.",
      "proof":"If optimal x for e has x_p<0, then x+unit_p is a child preimage with one less negative unit. Conversely, if y represents e+P_p with negative mass <=2, x=y-unit_p represents e with negative mass <=3; parent optimality forces depth 3 and x_p<0. The pointwise support feasibility is exact because depth=3 and sum(x)=6 imply coordinates lie in [-3,9].",
      "boundary":"This classifies the immediate pencil descendants of the certified mass-24 parent. It does not assert that the same local incidence signature predicts depth for unrelated exceptional orbits.",
    }
    path=HERE/"mass28_depth3_descendant_structure_certificate.json"; path.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:out[k] for k in ["status","parentStabilizerPointOrbitCount","pointOrbitSizes","optimalParentNegativeSupportSize","negativeSupportOrbitIndices","childDepthHistogram","optimalNegativeSupportExactlyPredictsDepthDrop","incidentValueMultisetAlonePredictsDepthOnTheseFiveTypes"]},indent=2,sort_keys=True))
    print(f"written: {path}")

if __name__=="__main__": main()
