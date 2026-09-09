#!/usr/bin/env python3
"""Mass-28 lineage and depth-four birth frontier.

The unique mass-24 depth-three no-pencil orbit is used in two complementary
ways.

* INHERITED LINEAGE: add each of the 40 point pencils to its representative,
  quotient by PSp(4,3), and compute the exact integer negativity depth of every
  resulting mass-28 orbit.  These are the immediate children of the new
  depth-three class.
* BIRTH SECTOR: a mass-28 class of depth >=4 that contains a point pencil would
  descend to a mass-24 class of depth >=4, impossible because the complete
  mass-24 census has maximum depth 3.  Therefore depth four can only be born in
  the no-contained-pencil mass-28 sector.  CP-SAT enumerates that sector and
  every orbit representative is sent to exact integer depth minimization.

Enumeration completeness and per-orbit depth completeness are reported
separately.  Timeouts/caps are never promoted to absence theorems.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import time

from ortools.sat.python import cp_model
import signed_pencil_sampling_witness as sp
import mass20_born_depth_and_extension_barcode as m20

HERE=Path(__file__).resolve().parent
PARENT=(
    0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,2,
    1,2,0,0,1,1,2,2,0,1,2,2,1,2,2,0,1,1,0,0,
)
PARENT_X=(
    0,0,0,-1,0,0,0,0,0,1,0,0,0,-1,0,1,0,0,2,1,
    0,1,0,0,0,0,0,1,0,0,0,0,0,0,0,1,1,0,0,-1,
)
PARENT_SOURCE={
  "mass":24,"orbitSize":1080,"depth":3,
  "representativeDigest":"sha256:db8e5654204ace859e17291804dba3bf66c7bbd4a0a29f6bc7e6528e55c0e735",
  "workflowRun":34381463322,"workflowJob":102567085256,"artifactId":10116305671,
  "mass24MaximumDepth":3,"mass24NoPencilEnumerationComplete":True,
}

def addv(a,b): return tuple(x+y for x,y in zip(a,b))

def inherited(lines,pencils,gens,depth_budget):
    assert len(m20.orbit(PARENT,gens))==1080
    rows={}
    for p,pen in enumerate(pencils):
        child=addv(PARENT,pen); ob=m20.orbit(child,gens); rep=min(ob)
        if rep in rows: rows[rep]["parentPencilSeeds"].append(p); continue
        exact=m20.exact_depth(rep,lines,budget=depth_budget)
        rows[rep]={
          "representative":list(rep),"representativeDigest":m20.digest(rep),"orbitSize":len(ob),
          "parentPencilSeeds":[p],"exactDepth":None if exact is None else exact[0],
          "exactPreimage":None if exact is None else list(exact[1]),
        }
    out=list(rows.values()); out.sort(key=lambda r:(999 if r["exactDepth"] is None else r["exactDepth"],r["orbitSize"],r["representative"]))
    return {
      "orbitCount":len(out),"depthHistogram":{str(k):v for k,v in sorted(Counter(r["exactDepth"] for r in out if r["exactDepth"] is not None).items())},
      "unknownDepthOrbitCount":sum(r["exactDepth"] is None for r in out),"orbits":out,
      "reading":"These are exactly the PSp(4,3)-orbit classes among parent+pencil for the unique mass-24 depth-three parent. Addition of a pencil gives an explicit depth<=3 witness before possible further simplification.",
    }

def no_pencil(lines,thru,pencils,adj,gens,*,budget,cap,depth_budget):
    model=cp_model.CpModel(); e=[model.NewIntVar(0,28,f"e{i}") for i in range(40)]
    model.Add(sum(e)==28)
    for i in range(40): model.Add(sum(adj[i][j]*e[j] for j in range(40))==2*e[i]+7)
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
    sv.parameters.max_time_in_seconds=float(budget); sv.parameters.random_seed=20260909
    t0=time.time(); st=sv.Solve(model,cb); elapsed=time.time()-t0
    complete=st==cp_model.OPTIMAL and not cb.hit
    rem=set(cb.rows); rows=[]
    while rem:
        seed=min(rem); ob=m20.orbit(seed,gens); rem.difference_update(ob); rep=min(ob)
        exact=m20.exact_depth(rep,lines,budget=depth_budget)
        rows.append({
          "representative":list(rep),"representativeDigest":m20.digest(rep),"orbitSize":len(ob),
          "exactDepth":None if exact is None else exact[0],"exactPreimage":None if exact is None else list(exact[1]),
        })
    rows.sort(key=lambda r:(999 if r["exactDepth"] is None else r["exactDepth"],r["orbitSize"],r["representative"]))
    born4=[r for r in rows if r["exactDepth"] is not None and r["exactDepth"]>=4]
    unknown=[r["representativeDigest"] for r in rows if r["exactDepth"] is None]
    absence=complete and not unknown and not born4
    return {
      "solverStatus":sv.StatusName(st),"complete":complete,"hitCap":cb.hit,"solutionsFound":len(cb.rows),
      "orbitCount":len(rows),"seconds":elapsed,"budgetSeconds":budget,"solutionCap":cap,
      "depthHistogram":{str(k):v for k,v in sorted(Counter(r["exactDepth"] for r in rows if r["exactDepth"] is not None).items())},
      "unknownDepthRepresentatives":unknown,"bornDepthAtLeast4":born4,
      "depth4ExistenceProved":bool(born4),"noDepth4AtMass28Proved":absence,"orbits":rows,
      "proofBoundary":("Complete mass 24 has maximum depth 3, so any mass-28 depth>=4 vector containing a pencil is impossible: subtracting it would give a mass-24 parent of depth>=4. Thus depth>=4 can only be born in this no-pencil sector. " + ("This no-pencil enumeration is complete." if complete else "This no-pencil enumeration is partial; absence of a found depth-4 orbit is not a theorem.")),
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--mode",choices=["inherited","no-pencil","both"],default="both")
    ap.add_argument("--budget",type=float,default=900); ap.add_argument("--cap",type=int,default=1500000); ap.add_argument("--depth-budget",type=float,default=20); a=ap.parse_args()
    lines,thru,pencils,adj,gens,order=m20.geometry_data(); assert order==25920
    assert sum(PARENT)==24 and sum(PARENT_X)==6 and sum(-x for x in PARENT_X if x<0)==3
    out={"schema":"holotrade.mass28-depth4-birth-frontier.v1","status":"PASS","groupOrder":order,"parent":PARENT_SOURCE}
    if a.mode in ("inherited","both"): out["inheritedDepth3Lineage"]=inherited(lines,pencils,gens,a.depth_budget)
    if a.mode in ("no-pencil","both"): out["noPencilBirthSector"]=no_pencil(lines,thru,pencils,adj,gens,budget=a.budget,cap=a.cap,depth_budget=a.depth_budget)
    p=HERE/f"mass28_depth4_birth_frontier_{a.mode}.json"; p.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    summary={"status":"PASS","mode":a.mode}
    if "inheritedDepth3Lineage" in out: summary["inherited"]={k:out["inheritedDepth3Lineage"][k] for k in ("orbitCount","depthHistogram","unknownDepthOrbitCount")}
    if "noPencilBirthSector" in out: summary["noPencil"]={k:out["noPencilBirthSector"][k] for k in ("solverStatus","complete","solutionsFound","orbitCount","depthHistogram","depth4ExistenceProved","noDepth4AtMass28Proved")}
    print(json.dumps(summary,indent=2,sort_keys=True)); print(f"written: {p}")
if __name__=="__main__": main()
