#!/usr/bin/env python3
"""Exact-certificate candidate hunt inside the mass-40 no-pencil sector.

The exhaustive mass-40 census is the absence-proof lane. This companion is a
finding lane: optimize deterministic pseudo-random linear functionals over the
exact admissible/no-pencil polytope, quotient each solution by PSp(4,3), and run
exact integer-depth plus rational primal/dual l1 certificates on every new
orbit.

Because mass 36 is globally certified to have maximum depth four, every first
mass-40 depth-five birth must be no-pencil. Any depth >=5 orbit or
Delta_R < Delta_Z found here is unconditional. Failure to find one proves
nothing about the rest of the sector.
"""
from __future__ import annotations

import argparse, json, random, time
from fractions import Fraction as F
from pathlib import Path
from ortools.sat.python import cp_model

import mass20_born_depth_and_extension_barcode as m20
import signed_pencil_sampling_witness as sp

HERE=Path(__file__).resolve().parent
MASS=40
K=10


def build_model(lines,thru,adj,weights):
    model=cp_model.CpModel(); e=[model.NewIntVar(0,MASS,f"e{i}") for i in range(40)]
    model.Add(sum(e)==MASS)
    for i in range(40): model.Add(sum(adj[i][j]*e[j] for j in range(40))==2*e[i]+K)
    zero=[]
    for i in range(40):
        z=model.NewBoolVar(f"z{i}")
        model.Add(e[i]==0).OnlyEnforceIf(z); model.Add(e[i]>=1).OnlyEnforceIf(z.Not()); zero.append(z)
    for p in range(40): model.AddBoolOr([zero[L] for L in thru[p]])
    model.Maximize(sum(int(weights[i])*e[i] for i in range(40)))
    return model,e


def exact_row(rep,lines,budget):
    exact=m20.exact_depth(rep,lines,budget=budget)
    if exact is None:
        return {"representative":list(rep),"representativeDigest":m20.digest(rep),"optimizationComplete":False}
    d,x=exact; frac=sp.fractional_certificate(rep,lines); gamma=F(frac["l1"]); delta=(gamma-F(K))/2
    return {
      "representative":list(rep),"representativeDigest":m20.digest(rep),"optimizationComplete":True,
      "integerDepth":d,"integerPreimage":list(x),"integerL1":str(F(K)+2*d),
      "gammaReal":str(gamma),"deltaReal":str(delta),"strictSeparation":delta<F(d),"realIntegerGap":str(F(d)-delta),
      "fractionalCertificate":frac,
    }


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--trials",type=int,default=96); ap.add_argument("--seed",type=int,default=20260911)
    ap.add_argument("--solve-budget",type=float,default=8); ap.add_argument("--depth-budget",type=float,default=50); a=ap.parse_args()
    lines,thru,pencils,adj,gens,order=m20.geometry_data(); assert order==25920
    rng=random.Random(a.seed); seen={}; statuses={}; t0=time.time()
    for trial in range(a.trials):
        w=[rng.randint(-1200,1200) for _ in range(40)]
        if trial%8==0:
            hot=trial//8%40; w[hot]+=6000
        if trial%16==8:
            hot=(trial//8+13)%40; w[hot]-=6000
        model,e=build_model(lines,thru,adj,w); sv=cp_model.CpSolver(); sv.parameters.num_workers=8
        sv.parameters.max_time_in_seconds=a.solve_budget; sv.parameters.random_seed=a.seed+trial
        st=sv.Solve(model); name=sv.StatusName(st); statuses[name]=statuses.get(name,0)+1
        if st not in (cp_model.OPTIMAL,cp_model.FEASIBLE): continue
        raw=tuple(int(sv.Value(v)) for v in e); ob=m20.orbit(raw,gens); rep=min(ob); dg=m20.digest(rep)
        if dg in seen: continue
        row=exact_row(rep,lines,a.depth_budget); row["orbitSize"]=len(ob); row["firstTrial"]=trial; seen[dg]=row
        if row.get("integerDepth",-1)>=5 or row.get("strictSeparation") is True: break
    rows=sorted(seen.values(),key=lambda r:(-(r.get("integerDepth") or -1),r["representativeDigest"]))
    depth5=[r for r in rows if r.get("integerDepth",-1)>=5]; gaps=[r for r in rows if r.get("strictSeparation") is True]
    out={
      "schema":"holotrade.mass40-no-pencil-candidate-hunt.v1","status":"PASS","mass":MASS,"k":K,"mode":"no-pencil",
      "groupOrder":order,"seed":a.seed,"requestedTrials":a.trials,"solverStatusHistogram":statuses,"distinctOrbitCount":len(rows),
      "rows":rows,"depth5WitnessFound":bool(depth5),"depth5Witnesses":depth5,"strictSeparationFound":bool(gaps),"strictSeparations":gaps,
      "elapsedSeconds":time.time()-t0,
      "birthLogic":"The exhaustive mass-36 theorem gives global maximum depth four. A mass-40 class containing a point pencil descends to mass 36, so every first depth-five mass-40 birth must be no-pencil.",
      "reading":"Every returned row is an exact admissible no-pencil orbit with exact integer-depth optimization and rational primal/dual l1 certificate. A reported depth-five or strict real/integer gap is unconditional. No-witness output is only a search result, not an absence theorem.",
      "boundary":"Random linear objectives sample extremal integer solutions and do not exhaust the sector. Only the separate exhaustive census can promote nonexistence."
    }
    path=HERE/f"mass40_no_pencil_candidate_hunt_seed{a.seed}.json"; path.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:out[k] for k in ["status","seed","requestedTrials","solverStatusHistogram","distinctOrbitCount","depth5WitnessFound","strictSeparationFound","elapsedSeconds"]},indent=2,sort_keys=True)); print(f"written: {path}")

if __name__=="__main__": main()
