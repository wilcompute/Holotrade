#!/usr/bin/env python3
"""Cutting-plane search for radius-two octet-gauge traps.

The direct formulation materializes 4,140 endpoint negativity expressions at
once and timed out on all seven mass-16 exceptional cosets.  Here we use an
exact separation oracle: solve the current bounded trap relaxation, enumerate
all 4,140 radius-two displacements on the integer candidate, add the most
violated endpoint inequalities, and repeat.

A SAT candidate with no improving displacement is an unconditional radius-two
counterexample (the coordinate box is only a search device).  INFEASIBLE is a
no-trap theorem only inside the stated coordinate box.
"""
from __future__ import annotations
import argparse, json, time
from pathlib import Path
from ortools.sat.python import cp_model
import signed_pencil_sampling_witness as sp
import octet_gauge_local_minimum_counterexample as g1
import the_mass12_census_is_complete_and_has_one_exception as m12


def addv(a,b): return tuple(x+y for x,y in zip(a,b))
def negmass(x): return sum(-v for v in x if v<0)

def ball2(moves):
    ds={tuple(m) for m in moves}
    ds.update(addv(a,b) for a in moves for b in moves)
    ds.discard((0,)*40)
    return tuple(sorted(ds))

def add_endpoint_cut(model,x,D,d,bound,tag):
    nn=[]
    for p in range(40):
        z=model.NewIntVar(0,bound+2,f"c{tag}_{p}")
        model.AddMaxEquality(z,[0,-x[p]-int(d[p])]); nn.append(z)
    model.Add(sum(nn)>=D)

def attack(index,*,bound,budget,batch):
    lines,thru,pencils=sp.build_geometry(); cover=sp.cover_solver(lines,thru)
    pts,idx,sf,lines2=m12.geometry(); assert tuple(map(tuple,lines2))==tuple(map(tuple,lines))
    gens,order=m12.line_action_generators(pts,idx,sf,lines2); assert order==25920
    gauge_rows,moves=g1.gauges(lines); ball=ball2(moves); parents=g1.parents(lines,thru,pencils,gens,cover); assert len(parents)==7
    parent=parents[index]; e=parent["e"]; optimum=parent["depth"]
    model=cp_model.CpModel(); x=[model.NewIntVar(-bound,bound,f"x{p}") for p in range(40)]; neg=[]
    for p in range(40):
        z=model.NewIntVar(0,bound,f"n{p}"); model.AddMaxEquality(z,[0,-x[p]]); neg.append(z)
    D=model.NewIntVar(optimum+1,40*bound,"D"); model.Add(D==sum(neg))
    for i,L in enumerate(lines): model.Add(sum(x[p] for p in L)==int(e[i]))
    model.Minimize(D)
    started=time.time(); cuts=set(); iterations=[]; witness=None; final="UNKNOWN"
    while time.time()-started < budget:
        remain=budget-(time.time()-started); sv=cp_model.CpSolver(); sv.parameters.num_workers=8; sv.parameters.random_seed=20260909+index
        sv.parameters.max_time_in_seconds=max(1.0,min(20.0,remain)); st=sv.Solve(model); status=sv.StatusName(st)
        if st==cp_model.INFEASIBLE:
            final="INFEASIBLE"; break
        if st not in (cp_model.OPTIMAL,cp_model.FEASIBLE):
            final=status; break
        w=tuple(int(sv.Value(v)) for v in x); d0=negmass(w); assert d0>=optimum+1
        vals=[]
        for j,d in enumerate(ball): vals.append((negmass(addv(w,d)),j))
        vals.sort(); best=vals[0][0]
        improving=[j for val,j in vals if val<d0 and j not in cuts]
        iterations.append({"solverStatus":status,"negativeMass":d0,"bestRadiusTwo":best,"cutsBefore":len(cuts),"newViolations":len(improving)})
        if not improving:
            assert all(val>=d0 for val,_ in vals)
            witness=w; final="COUNTEREXAMPLE"; break
        # Add the strongest distinct violated cuts first.  Each cut is exact.
        chosen=improving[:batch]
        for j in chosen:
            add_endpoint_cut(model,x,D,ball[j],bound,len(cuts)); cuts.add(j)
    elapsed=time.time()-started
    out={
      "schema":"holotrade.octet-gauge-radius-two-cutting-plane.v1","status":"PASS","index":index,"groupOrder":order,
      "kind":parent["kind"],"orbitSize":parent["orbitSize"],"certifiedGlobalDepth":optimum,
      "coordinateBound":bound,"budgetSeconds":budget,"seconds":elapsed,"signedMoves":len(moves),"distinctRadiusTwoDisplacements":len(ball),
      "cutsAdded":len(cuts),"iterations":iterations,"finalStatus":final,"counterexample":witness is not None,
      "witness":None if witness is None else list(witness),"negativeMass":None if witness is None else negmass(witness),
      "boundedNoTrapProved":final=="INFEASIBLE",
      "reading":"COUNTEREXAMPLE is unconditional: every one of the 4,140 radius-two endpoints was explicitly checked. INFEASIBLE proves no radius-two trap only with all preimage coordinates inside the stated box. UNKNOWN remains inconclusive.",
      "boundary":"The kernel lattice is unbounded; bounded infeasibility is not a global decoder theorem without a separate saturation/bounding result."
    }
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--index",type=int,required=True); ap.add_argument("--bound",type=int,default=8); ap.add_argument("--budget",type=float,default=150); ap.add_argument("--batch",type=int,default=32); ap.add_argument("--write",action="store_true"); a=ap.parse_args()
    if not 0<=a.index<7: raise SystemExit("--index must be 0..6")
    out=attack(a.index,bound=a.bound,budget=a.budget,batch=a.batch)
    print(json.dumps({k:out[k] for k in ["index","kind","orbitSize","certifiedGlobalDepth","distinctRadiusTwoDisplacements","cutsAdded","finalStatus","counterexample","negativeMass","boundedNoTrapProved","seconds"]},indent=2,sort_keys=True))
    if a.write:
        p=Path(__file__).with_name(f"octet_gauge_radius_two_cutting_plane_{a.index}.json"); p.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n"); print(f"written: {p}")
if __name__=="__main__": main()
