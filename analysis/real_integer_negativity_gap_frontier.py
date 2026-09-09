#!/usr/bin/env python3
"""Search higher mass for a certified real/integer negativity-depth separation.

For an admissible excess vector e of mass 4k,

    delta_Z(e) = minimum integer negative mass,
    gamma_R(e) = minimum real l1 norm of a preimage,
    delta_R(e) = (gamma_R(e)-k)/2.

Always delta_R <= delta_Z.  The lower-mass certificates repeatedly found
equality.  This program searches mass 28 and 32 with exact orbit reduction,
integer CP-SAT depth certificates, and the repository's rational primal/dual
l1 certificate.

Two modes are useful:
* full: enumerate every admissible vector of the requested mass;
* no-pencil: enumerate only vectors containing no point pencil.  At mass 32
  this is the only sector where depth four can be born because the global
  mass-28 maximum depth is now certified as three.

Enumeration completeness is recorded separately from any found separation.  A
found delta_R < delta_Z is unconditional for that orbit even if the surrounding
census is partial; absence is promoted only when enumeration and all per-orbit
optimizations are complete.
"""
from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction as F
import json
from pathlib import Path
import time

from ortools.sat.python import cp_model

import signed_pencil_sampling_witness as sp
import mass20_born_depth_and_extension_barcode as m20

HERE=Path(__file__).resolve().parent


def enumerate_vectors(mass, lines, thru, adj, *, no_pencil, budget, cap):
    assert mass%4==0; k=mass//4
    model=cp_model.CpModel(); e=[model.NewIntVar(0,mass,f"e{i}") for i in range(40)]
    model.Add(sum(e)==mass)
    for i in range(40): model.Add(sum(adj[i][j]*e[j] for j in range(40))==2*e[i]+k)
    if no_pencil:
        zero=[]
        for i in range(40):
            z=model.NewBoolVar(f"z{i}"); model.Add(e[i]==0).OnlyEnforceIf(z); model.Add(e[i]>=1).OnlyEnforceIf(z.Not()); zero.append(z)
        for p in range(40): model.AddBoolOr([zero[L] for L in thru[p]])
    class CB(cp_model.CpSolverSolutionCallback):
        def __init__(self): super().__init__(); self.rows=set(); self.hit=False
        def on_solution_callback(self):
            self.rows.add(tuple(self.Value(v) for v in e))
            if len(self.rows)>=cap: self.hit=True; self.StopSearch()
    cb=CB(); sv=cp_model.CpSolver(); sv.parameters.enumerate_all_solutions=True; sv.parameters.num_workers=1
    sv.parameters.max_time_in_seconds=float(budget); sv.parameters.random_seed=20260909+mass+(1 if no_pencil else 0)
    t0=time.time(); st=sv.Solve(model,cb); elapsed=time.time()-t0
    return cb.rows, sv.StatusName(st), st==cp_model.OPTIMAL and not cb.hit, cb.hit, elapsed


def rational_row(rep, mass, lines, depth_budget):
    exact=m20.exact_depth(rep,lines,budget=depth_budget)
    if exact is None: return {"representative":list(rep),"representativeDigest":m20.digest(rep),"integerDepth":None,"optimizationComplete":False}
    d,x=exact; frac=sp.fractional_certificate(rep,lines); gamma=F(frac["l1"]); k=F(mass,4); delta=(gamma-k)/2
    return {
      "representative":list(rep),"representativeDigest":m20.digest(rep),"integerDepth":d,"integerPreimage":list(x),
      "integerL1":str(k+2*d),"gammaReal":str(gamma),"deltaReal":str(delta),
      "realIntegerGap":str(F(d)-delta),"strictSeparation":delta<F(d),"equality":delta==F(d),
      "fractionalCertificate":frac,"optimizationComplete":True,
    }


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--mass",type=int,required=True); ap.add_argument("--mode",choices=["full","no-pencil"],default="full")
    ap.add_argument("--budget",type=float,default=1200); ap.add_argument("--cap",type=int,default=3000000); ap.add_argument("--depth-budget",type=float,default=60); a=ap.parse_args()
    assert a.mass in (28,32) and a.mass%4==0
    lines,thru,pencils,adj,gens,order=m20.geometry_data(); assert order==25920
    raw,status,complete,hit,elapsed=enumerate_vectors(a.mass,lines,thru,adj,no_pencil=a.mode=="no-pencil",budget=a.budget,cap=a.cap)
    rem=set(raw); rows=[]
    while rem:
        seed=min(rem); ob=m20.orbit(seed,gens); rem.difference_update(ob); rep=min(ob)
        row=rational_row(rep,a.mass,lines,a.depth_budget); row["orbitSize"]=len(ob); rows.append(row)
    rows.sort(key=lambda r:(999 if r.get("integerDepth") is None else r["integerDepth"],F(r.get("deltaReal","999")),r["orbitSize"],r["representativeDigest"]))
    unresolved=[r for r in rows if not r["optimizationComplete"]]
    gaps=[r for r in rows if r.get("strictSeparation")]
    equal=[r for r in rows if r.get("equality")]
    absence=complete and not unresolved and not gaps
    depth_hist=Counter(r["integerDepth"] for r in rows if r.get("integerDepth") is not None)
    delta_hist=Counter(r["deltaReal"] for r in rows if r.get("deltaReal") is not None)
    out={
      "schema":"holotrade.real-integer-negativity-gap-frontier.v1","status":"PASS","groupOrder":order,"mass":a.mass,"k":a.mass//4,"mode":a.mode,
      "solverStatus":status,"enumerationComplete":complete,"hitCap":hit,"rawSolutionsFound":len(raw),"orbitCount":len(rows),"seconds":elapsed,
      "integerDepthHistogram":{str(k):v for k,v in sorted(depth_hist.items())},"deltaRealHistogram":dict(sorted(delta_hist.items(),key=lambda kv:F(kv[0]))),
      "unresolvedOrbitCount":len(unresolved),"strictSeparationOrbitCount":len(gaps),"strictSeparations":gaps,
      "allResolvedRows":rows,"noSeparationInEnumeratedSectorProved":absence,
      "mass28Context":"Independent completed birth-frontier certificate proves the global mass-28 maximum integer depth is three; its no-pencil sector has four depth-three orbits and 43,200 solutions.",
      "theorem":("At least one exact orbit satisfies delta_R < delta_Z; each listed gap carries both an integer optimum and rational primal/dual l1 certificate." if gaps else ("The complete requested sector has delta_R=delta_Z on every orbit." if absence else "No gap was found in the enumerated portion, but incompleteness or unresolved integer optimization prevents an absence theorem.")),
      "boundary":"A separation is an exact property of signed preimage optimization. It is not physical energy, magic-state cost, or hardware performance. 'First' by mass is asserted only after all lower relevant masses/sectors are independently certified gap-free.",
    }
    path=HERE/f"real_integer_negativity_gap_frontier_m{a.mass}_{a.mode}.json"; path.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:out[k] for k in ["status","mass","mode","solverStatus","enumerationComplete","rawSolutionsFound","orbitCount","integerDepthHistogram","deltaRealHistogram","unresolvedOrbitCount","strictSeparationOrbitCount","noSeparationInEnumeratedSectorProved"]},indent=2,sort_keys=True)); print(f"written: {path}")

if __name__=="__main__": main()
