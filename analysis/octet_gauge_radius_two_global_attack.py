#!/usr/bin/env python3
"""Direct radius-two local-minimum attack for the 45-octet gauge decoder.

A radius-two trap is a preimage x whose negativity is above the independently
certified optimum while no endpoint reachable by <=2 signed octet moves has
smaller negativity.  Since any radius-two trap is automatically a radius-one
trap, this is the exact finite condition the previous counterexample pass left
open.

For each of the seven mass-16 exceptional PSp(4,3) cosets we build one CP-SAT
model that includes every *distinct* displacement in the radius-two move ball.
If SAT, the returned witness is an unconditional counterexample (the coordinate
box was only used to find it, and every endpoint is explicitly rechecked).  If
INFEASIBLE, the result is an exact no-trap theorem inside the stated coordinate
box only.  We never promote bounded infeasibility to global convergence.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import time

from ortools.sat.python import cp_model
import signed_pencil_sampling_witness as sp
import octet_gauge_local_minimum_counterexample as g1
import the_mass12_census_is_complete_and_has_one_exception as m12


def addv(a,b): return tuple(x+y for x,y in zip(a,b))
def negmass(x): return sum(-v for v in x if v<0)


def radius_two_ball(moves):
    ds={tuple(m) for m in moves}
    ds.update(addv(a,b) for a in moves for b in moves)
    ds.discard((0,)*40)
    rows=tuple(sorted(ds))
    assert all(max(map(abs,d))<=2 for d in rows)
    return rows


def search_coset(e,optimum,lines,ball,*,bound,budget):
    model=cp_model.CpModel()
    x=[model.NewIntVar(-bound,bound,f"x{p}") for p in range(40)]
    neg=[]
    for p in range(40):
        z=model.NewIntVar(0,bound,f"n{p}"); model.AddMaxEquality(z,[0,-x[p]]); neg.append(z)
    D=model.NewIntVar(0,40*bound,"D"); model.Add(D==sum(neg)); model.Add(D>=optimum+1)
    for i,L in enumerate(lines): model.Add(sum(x[p] for p in L)==int(e[i]))
    # Exact endpoint negativity for every distinct displacement in the <=2 ball.
    for j,d in enumerate(ball):
        nn=[]
        for p in range(40):
            z=model.NewIntVar(0,bound+2,f"b{j}_{p}")
            model.AddMaxEquality(z,[0,-x[p]-int(d[p])]); nn.append(z)
        model.Add(sum(nn)>=D)
    sv=cp_model.CpSolver(); sv.parameters.max_time_in_seconds=float(budget); sv.parameters.num_workers=8
    t0=time.time(); st=sv.Solve(model); elapsed=time.time()-t0
    row={"solverStatus":sv.StatusName(st),"bound":bound,"budgetSeconds":budget,"seconds":elapsed,"witness":None}
    if st in (cp_model.OPTIMAL,cp_model.FEASIBLE):
        w=tuple(int(sv.Value(v)) for v in x); d0=negmass(w)
        assert d0>=optimum+1
        assert all(sum(w[p] for p in L)==e[i] for i,L in enumerate(lines))
        vals=[negmass(addv(w,d)) for d in ball]
        assert min(vals)>=d0
        row.update(witness=list(w),negativeMass=d0,bestRadiusTwo=min(vals),endpointsChecked=len(ball),counterexample=True)
    else:
        row["counterexample"]=False
        row["boundedNoTrapProved"]=(st==cp_model.INFEASIBLE)
    return row


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--bound",type=int,default=8); ap.add_argument("--budget",type=float,default=55.0); ap.add_argument("--write",action="store_true"); args=ap.parse_args()
    lines,thru,pencils=sp.build_geometry(); cover=sp.cover_solver(lines,thru)
    pts,idx,sf,lines2=m12.geometry(); assert tuple(map(tuple,lines2))==tuple(map(tuple,lines))
    gens,order=m12.line_action_generators(pts,idx,sf,lines2); assert order==25920
    gauge_rows,moves=g1.gauges(lines); ball=radius_two_ball(moves)
    parents=g1.parents(lines,thru,pencils,gens,cover); assert len(parents)==7
    rows=[]; first=None
    for p in parents:
        r=search_coset(p["e"],p["depth"],lines,ball,bound=args.bound,budget=args.budget)
        r.update(orbitSize=p["orbitSize"],kind=p["kind"],certifiedGlobalDepth=p["depth"])
        rows.append(r)
        if r["counterexample"] and first is None: first=r
    status_hist=Counter(r["solverStatus"] for r in rows)
    bounded_all=all(r.get("boundedNoTrapProved") is True for r in rows)
    out={
        "schema":"holotrade.octet-gauge-radius-two-global-attack.v1","status":"PASS","groupOrder":order,
        "kernelGaugeGenerators":len(gauge_rows),"signedMoves":len(moves),"distinctRadiusTwoNonzeroDisplacements":len(ball),
        "coordinateBound":args.bound,"rows":rows,"solverStatusHistogram":dict(status_hist),
        "radiusTwoCounterexampleFound":first is not None,"firstRadiusTwoCounterexample":first,
        "boundedNoRadiusTwoTrapOnAllSevenCosets":bounded_all,
        "reading":("SAT is an unconditional radius-two decoder counterexample because all distinct <=2 endpoints are rechecked explicitly. "
                   "INFEASIBLE is an exact theorem only for preimages with every coordinate in the stated box. If all seven are INFEASIBLE, that is a complete bounded-box theorem across the exceptional mass-16 orbit census."),
        "boundary":"The kernel lattice is unbounded. Bounded-box infeasibility is not a proof of global convergence unless a separate saturation/bounding theorem is supplied.",
    }
    print(json.dumps({"status":"PASS","radiusTwoDisplacements":len(ball),"counterexample":first is not None,"boundedAllSeven":bounded_all,"statuses":dict(status_hist),"rows":[{k:v for k,v in r.items() if k!="witness"} for r in rows]},indent=2,sort_keys=True))
    if args.write:
        p=Path(__file__).with_name("octet_gauge_radius_two_global_attack_certificate.json"); p.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n"); print(f"written: {p}")

if __name__=="__main__": main()
