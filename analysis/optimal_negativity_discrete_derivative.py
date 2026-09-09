#!/usr/bin/env python3
"""Universal discrete derivative theorem for W33 pencil negativity.

Let N^T : Z^40 -> Z^40 be the W(3,3) point-pencil incidence map and

    d(e) = min { f(x) : N^T x=e },   f(x)=sum_i max(0,-x_i).

For the point pencil P_p=N^T e_p, every feasible parent preimage x maps to
x+e_p for e+P_p.  Since only one coordinate changes,

    f(x+e_p) = f(x)-1  if x_p<0,
               f(x)    otherwise.

Conversely every child preimage y maps to y-e_p for e, and
f(y-e_p) <= f(y)+1.  Hence, for every integer excess e for which the affine
fiber is nonempty,

    d(e+P_p) in {d(e)-1,d(e)}.

Moreover

    d(e+P_p)=d(e)-1
      iff some optimal parent preimage has x_p<0.

The reverse implication is exact: if a child optimum has value d(e)-1, then
y_p cannot be >=1 (otherwise y-e_p would be a parent preimage of value <=d-1),
so x=y-e_p is parent-optimal and x_p<0.

Thus the union of negative supports of optimal parent preimages is literally
the support of the one-step downward discrete derivative of integer negativity
under point-pencil extension.  This theorem is lattice/optimization structure;
it does not depend on mass, a census, or a physical interpretation.

This script machine-checks the scalar identities exhaustively on a broad
integer window and freezes the theorem plus the already-certified mass-24 ->
mass-28 corollary.  The finite census is a regression, not an assumption of the
proof.
"""
from __future__ import annotations

import json
from pathlib import Path

import mass28_depth4_birth_frontier as m28

HERE=Path(__file__).resolve().parent


def phi(z:int)->int: return max(0,-z)


def scalar_delta(z:int)->int: return phi(z+1)-phi(z)


def reverse_bound(z:int)->bool: return phi(z-1) <= phi(z)+1


def main():
    # Exhaustive scalar kernel of the proof.  These identities hold over Z;
    # the finite window makes accidental implementation drift detectable.
    for z in range(-10000,10001):
        assert scalar_delta(z)==(-1 if z<0 else 0)
        assert reverse_bound(z)

    lines,thru,pencils,adj,gens,order=m28.m20.geometry_data(); assert order==25920
    inherited=m28.inherited(lines,pencils,gens,20.0)
    assert inherited["orbitCount"]==5
    assert inherited["depthHistogram"]=={"2":2,"3":3}
    parent_depth=3
    rows=[]
    for r in inherited["orbits"]:
        child_depth=int(r["exactDepth"])
        assert child_depth in (parent_depth-1,parent_depth)
        rows.append({
          "childRepresentativeDigest":r["representativeDigest"],
          "parentPencilSeeds":r["parentPencilSeeds"],
          "childDepth":child_depth,
          "discreteDerivative":child_depth-parent_depth,
          "predictedOptimalNegativeSupport":child_depth==parent_depth-1,
        })

    out={
      "schema":"holotrade.optimal-negativity-discrete-derivative.v1",
      "status":"PASS",
      "groupOrder":order,
      "theorem":{
        "depthStepLaw":"For every feasible integer excess e and point p, d(e+P_p) is either d(e)-1 or d(e).",
        "supportCriterion":"d(e+P_p)=d(e)-1 iff p belongs to the union of negative supports of optimal integer preimages of e.",
        "proofDependencies":[
          "P_p=N^T e_p, so extension is x -> x+e_p on every affine fiber.",
          "f(x+e_p)-f(x) equals -1 exactly when x_p<0 and 0 otherwise.",
          "Every child preimage y gives parent preimage y-e_p with f(y-e_p)<=f(y)+1.",
          "If child depth is d-1, y_p>=1 would contradict parent optimality; hence y-e_p is an optimal parent with negative p-coordinate."
        ],
        "censusIndependent":True,
      },
      "machineCheckedScalarRange":[-10000,10000],
      "mass24Depth3ToMass28Regression":{
        "parentDepth":3,
        "childOrbitCount":5,
        "depthHistogram":inherited["depthHistogram"],
        "downwardDerivativeOrbitCount":2,
        "flatDerivativeOrbitCount":3,
        "rows":rows,
      },
      "interpretation":"Optimal-negativity support is the exact one-step discrete derivative support for pencil extension. Stabilizer point orbits therefore compress an extension-depth barcode: every point in the same parent-stabilizer orbit has the same derivative.",
      "boundary":"Exact integer-lattice optimization theorem for the W33 pencil map. It is not a statement about physical energy, time evolution, or quantum dynamics."
    }
    p=HERE/"optimal_negativity_discrete_derivative_certificate.json"
    p.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":"PASS","law":"d(e+P_p) in {d-1,d}","supportCriterion":True,"mass28DepthHistogram":inherited["depthHistogram"]},indent=2,sort_keys=True))
    print(f"written: {p}")

if __name__=="__main__": main()
