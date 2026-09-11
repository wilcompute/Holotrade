#!/usr/bin/env python3
"""Exact mass-36 lineage of the two first W33 depth-four births.

The frozen derivative-automaton certificate predicts all immediate pencil
children of the two mass-32 depth-four birth orbits.  This script reconstructs
every target orbit from the certified parents, deduplicates across both parent
lineages, and independently re-solves each target in two ways:

* integer negative-mass optimum delta_Z via CP-SAT;
* real l1 optimum gamma_R via exact rational primal/dual certificate, with
  delta_R=(gamma_R-k)/2 for k=9.

Thus it simultaneously audits the derivative transition law and tests whether
real/integer equality delta_R=delta_Z survives every depth-four descendant.
These quantities are finite signed-preimage optimization invariants, not
physical energy, magic-state cost, or hardware performance.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from fractions import Fraction as F
import json
from pathlib import Path

import mass20_born_depth_and_extension_barcode as m20
import signed_pencil_sampling_witness as sp

HERE=Path(__file__).resolve().parent
AUTOMATON=HERE/"exceptional_depth_derivative_automaton_certificate.json"
M32=HERE/"mass32_depth4_birth_certificate.json"


def addv(a,b): return tuple(x+y for x,y in zip(a,b))


def exact_row(rep,lines,predicted_depth,depth_budget=120):
    exact=m20.exact_depth(rep,lines,budget=depth_budget)
    assert exact is not None, f"integer optimization unresolved for {m20.digest(rep)}"
    d,x=exact
    assert d==predicted_depth,(m20.digest(rep),d,predicted_depth)
    frac=sp.fractional_certificate(rep,lines)
    gamma=F(frac["l1"]); k=F(sum(rep),4); delta=(gamma-k)/2
    return {
      "representative":list(rep),"representativeDigest":m20.digest(rep),
      "integerDepth":d,"integerPreimage":list(x),"integerL1":str(k+2*d),
      "gammaReal":str(gamma),"deltaReal":str(delta),"realIntegerGap":str(F(d)-delta),
      "strictSeparation":delta<F(d),"equality":delta==F(d),"fractionalCertificate":frac,
    }


def main():
    A=json.loads(AUTOMATON.read_text()); C=json.loads(M32.read_text())
    assert A["status"]==C["status"]=="PASS" and C["firstDepth4MassProved"] is True
    lines,thru,pencils,adj,gens,order=m20.geometry_data(); assert order==25920
    parents=[tuple(r["representative"]) for r in C["depth4Births"]]
    astates={s["name"]:s for s in A["states"]}
    source_states=[astates["mass32-depth4-birth-0"],astates["mass32-depth4-birth-1"]]

    by_digest={}
    ancestry=defaultdict(list)
    predicted={}
    direction_depth=Counter()
    parent_direction_depth={}
    for pi,(parent,state) in enumerate(zip(parents,source_states)):
        assert m20.digest(parent)==state["representativeDigest"] and state["depth"]==4
        pd=Counter()
        for t in state["transitions"]:
            p=t["points"][0]
            child=addv(parent,pencils[p]); ob=m20.orbit(child,gens); rep=min(ob); dg=m20.digest(rep)
            assert dg==t["targetRepresentativeDigest"] and len(ob)==t["targetOrbitSize"]
            if dg in predicted: assert predicted[dg]==t["targetDepth"]
            predicted[dg]=t["targetDepth"]; by_digest[dg]=rep
            ancestry[dg].append({"parentBirthIndex":pi,"parentDigest":state["representativeDigest"],"pointOrbitIndex":t["pointOrbitIndex"],
              "pointOrbitSize":t["pointOrbitSize"],"points":t["points"],"predictedDepth":t["targetDepth"]})
            pd[t["targetDepth"]]+=t["pointOrbitSize"]; direction_depth[t["targetDepth"]]+=t["pointOrbitSize"]
        assert sum(pd.values())==40
        parent_direction_depth[str(pi)]={str(k):v for k,v in sorted(pd.items())}

    rows=[]
    for dg in sorted(by_digest):
        rep=by_digest[dg]; row=exact_row(rep,lines,predicted[dg])
        row["orbitSize"]=len(m20.orbit(rep,gens)); row["ancestry"]=ancestry[dg]
        rows.append(row)
    depth_hist=Counter(r["integerDepth"] for r in rows)
    delta_hist=Counter(r["deltaReal"] for r in rows)
    gaps=[r for r in rows if r["strictSeparation"]]
    shared=[r for r in rows if len(r["ancestry"])>1]
    depth4=[r for r in rows if r["integerDepth"]==4]
    out={
      "schema":"holotrade.mass36-depth4-lineage-real-integer.v1","status":"PASS","group":"PSp(4,3)","groupOrder":25920,
      "sourceParentMass":32,"targetMass":36,"parentBirthCount":2,"rawPencilDirections":80,
      "uniqueChildOrbitCount":len(rows),"crossParentSharedChildOrbitCount":len(shared),
      "parentDirectionDepthHistograms":parent_direction_depth,
      "combinedDirectionDepthHistogram":{str(k):v for k,v in sorted(direction_depth.items())},
      "uniqueOrbitDepthHistogram":{str(k):v for k,v in sorted(depth_hist.items())},
      "deltaRealHistogram":dict(sorted(delta_hist.items(),key=lambda kv:F(kv[0]))),
      "depth4ChildOrbitCount":len(depth4),"strictSeparationOrbitCount":len(gaps),
      "allLineageOrbitsSatisfyDeltaRealEqualsIntegerDepth":not gaps and all(r["equality"] for r in rows),
      "rows":rows,
      "theorem":"Every immediate pencil descendant of either first mass-32 depth-four birth lies in one of the listed PSp(4,3) mass-36 orbits. The derivative-law depth is independently reproduced by exact integer optimization for every target. The rational primal/dual l1 certificate then decides delta_R exactly for the same orbit.",
      "birthBoundary":"This certifies only descendants containing at least one removable point pencil. A genuinely new mass-36 exceptional birth can occur only in the no-contained-pencil sector and must be analyzed separately.",
      "physicalBoundary":"Negativity depth and rational l1 are signed-preimage representation invariants, not physical energy, magic-state cost, or measured hardware performance."
    }
    path=HERE/"mass36_depth4_lineage_real_integer_certificate.json"; path.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:out[k] for k in ["status","uniqueChildOrbitCount","crossParentSharedChildOrbitCount","parentDirectionDepthHistograms","combinedDirectionDepthHistogram","uniqueOrbitDepthHistogram","deltaRealHistogram","depth4ChildOrbitCount","strictSeparationOrbitCount","allLineageOrbitsSatisfyDeltaRealEqualsIntegerDepth"]},indent=2,sort_keys=True));print(f"written: {path}")

if __name__=="__main__":main()
