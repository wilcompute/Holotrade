#!/usr/bin/env python3
"""Finite-state derivative automaton for exceptional W33 negativity depth.

For any certified parent excess e of mass 4k and exact integer negativity depth d,
the universal pencil derivative theorem gives

    d(e + P_p) = d-1  iff p is negative in some optimal preimage of e,
                     d otherwise.

Thus one does not need to re-optimize all 40 children.  We solve the finite
optimal-support feasibility problem at the parent, compute the parent stabilizer
inside the exact 25,920-element PSp(4,3) point action, quotient the 40 points by
that stabilizer, and emit one transition for each point orbit.  The target child
is independently canonicalized under PSp(4,3).

The regression parents are the unique mass-24 depth-3 birth and BOTH newly
certified mass-32 depth-4 births.  The latter predicts their complete immediate
mass-36 descendant depths exactly, extending the automaton beyond the census
that discovered them.
"""
from __future__ import annotations

from collections import deque
import json
from pathlib import Path

from ortools.sat.python import cp_model

import mass20_born_depth_and_extension_barcode as m20
import mass24_depth3_steinberg_real_l1 as m24
import mass24_1080_gset_character_fingerprint as fp

HERE=Path(__file__).resolve().parent
M32_PATH=HERE/"mass32_depth4_birth_certificate.json"


def addv(a,b): return tuple(x+y for x,y in zip(a,b))


def optimal_negative_support(parent, depth, lines):
    k=sum(parent)//4
    assert sum(parent)==4*k
    support=[]; witnesses={}
    lo,hi=-depth,k+depth
    for target in range(40):
        model=cp_model.CpModel()
        x=[model.NewIntVar(lo,hi,f"x{i}") for i in range(40)]
        neg=[]
        for i in range(40):
            z=model.NewIntVar(0,depth,f"n{i}")
            model.AddMaxEquality(z,[0,-x[i]]); neg.append(z)
        model.Add(sum(neg)==depth)
        model.Add(sum(x)==k)
        for li,L in enumerate(lines): model.Add(sum(x[p] for p in L)==int(parent[li]))
        model.Add(x[target] <= -1)
        sv=cp_model.CpSolver(); sv.parameters.num_workers=8; sv.parameters.max_time_in_seconds=20
        st=sv.Solve(model)
        if st in (cp_model.OPTIMAL,cp_model.FEASIBLE):
            w=tuple(int(sv.Value(v)) for v in x)
            assert sum(-v for v in w if v<0)==depth and sum(w)==k and w[target]<0
            support.append(target); witnesses[target]=w
        else:
            assert st==cp_model.INFEASIBLE, (target,sv.StatusName(st))
    return frozenset(support),witnesses


def parent_stabilizer_point_orbits(parent_h, h_lines):
    pts,wlines,all_point,all_line=fp.same_generators()
    hidx={frozenset(L):i for i,L in enumerate(h_lines)}
    assert set(hidx)=={frozenset(L) for L in wlines}
    parent_w=tuple(parent_h[hidx[frozenset(L)]] for L in wlines)
    line_selected=tuple(all_line[i] for i in fp.GENERATOR_INDICES)
    states,mass_selected=m24.mass_orbit_actions(parent_w,line_selected)
    point_selected=tuple(all_point[i] for i in fp.GENERATOR_INDICES)
    image,_=fp.build_group_with_base_images(point_selected,mass_selected,mass_selected)
    H={g for g,(bm,_dummy) in image.items() if bm==0}
    assert len(H)*len(states)==25920
    rem=set(range(40)); orbits=[]
    while rem:
        seed=min(rem); O={g[seed] for g in H}; rem.difference_update(O); orbits.append(tuple(sorted(O)))
    orbits.sort(key=lambda O:(len(O),O))
    assert sum(map(len,orbits))==40
    return len(states),len(H),orbits


def automaton_parent(name,parent,depth,lines,pencils,gens):
    support,_witnesses=optimal_negative_support(parent,depth,lines)
    orbit_size,stab_order,point_orbits=parent_stabilizer_point_orbits(parent,lines)
    transitions=[]
    for oi,O in enumerate(point_orbits):
        flags={p in support for p in O}; assert len(flags)==1
        drop=next(iter(flags)); expected=depth-1 if drop else depth
        targets=set()
        for p in O:
            child=addv(parent,pencils[p]); targets.add(min(m20.orbit(child,gens)))
        assert len(targets)==1
        target=next(iter(targets))
        transitions.append({
          "symbol":f"HpointOrbit:{oi}","pointOrbitIndex":oi,"pointOrbitSize":len(O),"points":list(O),
          "optimalNegativeSupport":drop,"depthDerivative":-1 if drop else 0,"targetDepth":expected,
          "targetMass":sum(parent)+4,"targetRepresentativeDigest":m20.digest(target),"targetOrbitSize":len(m20.orbit(target,gens)),
        })
    assert sum(t["pointOrbitSize"] for t in transitions)==40
    assert sum(t["pointOrbitSize"] for t in transitions if t["optimalNegativeSupport"])==len(support)
    return {
      "name":name,"mass":sum(parent),"depth":depth,"representativeDigest":m20.digest(parent),
      "orbitSize":orbit_size,"stabilizerOrder":stab_order,"pointOrbitCount":len(point_orbits),
      "optimalNegativeSupportSize":len(support),"transitionCount":len(transitions),"transitions":transitions,
    }


def main():
    lines,thru,pencils,adj,gens,order=m20.geometry_data(); assert order==25920
    m32=json.loads(M32_PATH.read_text()); assert m32["status"]=="PASS" and m32["firstDepth4MassProved"] is True
    parents=[("mass24-depth3",tuple(m24.REP),3)]
    for i,row in enumerate(m32["depth4Births"]):
        assert row["integerDepth"]==4
        parents.append((f"mass32-depth4-birth-{i}",tuple(row["representative"]),4))
    states=[automaton_parent(name,p,d,lines,pencils,gens) for name,p,d in parents]
    # Known mass24 structural regression: exactly five symbols and 2 drop / 3 flat symbols.
    first=states[0]
    assert first["pointOrbitCount"]==5
    assert sum(t["depthDerivative"]==-1 for t in first["transitions"])==2
    assert sum(t["depthDerivative"]==0 for t in first["transitions"])==3
    out={
      "schema":"holotrade.exceptional-depth-derivative-automaton.v1","status":"PASS","group":"PSp(4,3)","groupOrder":25920,
      "transitionLaw":"For a parent of exact depth d, +P_p has depth d-1 exactly on optimal-negative support and depth d otherwise.",
      "alphabet":"Parent-stabilizer point orbits. Every point in one symbol has the same derivative and the same PSp child orbit.",
      "states":states,
      "mass24Regression":{"symbolCount":5,"dropSymbols":2,"flatSymbols":3},
      "mass32Extension":{"parentCount":2,"targetMass":36,"completeImmediateTransitions":True},
      "theorem":"The universal discrete derivative law turns every certified exceptional orbit into a finite deterministic depth-transition state once its optimal-negative support is known. Quotienting points by the exact parent stabilizer compresses forty pencil additions to a finite alphabet without losing depth or target-orbit information. The certificate instantiates this for the mass-24 depth-3 birth and both first mass-32 depth-4 births, thereby predicting all their immediate mass-36 child depths without child depth optimization.",
      "boundary":"This is an exact finite W33 orbit/optimization automaton for pencil extension. It is not a physical time evolution or dynamical-system claim."
    }
    path=HERE/"exceptional_depth_derivative_automaton_certificate.json"; path.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":"PASS","states":[{"name":s["name"],"depth":s["depth"],"pointOrbitCount":s["pointOrbitCount"],"support":s["optimalNegativeSupportSize"],"targetDepthHistogram":{str(d):sum(t["pointOrbitSize"] for t in s["transitions"] if t["targetDepth"]==d) for d in sorted({t["targetDepth"] for t in s["transitions"]})}} for s in states]},indent=2,sort_keys=True)); print(f"written: {path}")

if __name__=="__main__": main()
