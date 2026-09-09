#!/usr/bin/env python3
"""Turn the 45-octet gauge decoder into a theorem-or-counterexample test.

The 45 signed octet differences generate ker_Z(N^T) exactly.  The earlier local
decoder succeeded on seven hand-perturbed starts, but that does not imply local
descent is globally correct.  Here we ask an exact finite satisfiability
question: does a known exceptional coset contain a preimage whose negativity is
strictly above the certified optimum while *none* of the 90 signed one-octet
moves decreases it?

A SAT witness is an unconditional counterexample to radius-one greedy descent:
the coordinate bound is used only to find the witness; once found, all 90
neighbors are checked explicitly.  We then exhaustively inspect all 90^2
ordered two-move paths from the witness.  If none decreases negativity, the same
witness is also an exact radius-two local-minimum counterexample.  If a pair does
decrease it, radius two is shown to escape this particular radius-one trap but
is not promoted to a global theorem.
"""
from __future__ import annotations

import argparse
from collections import deque
import importlib.util
import json
from pathlib import Path

from ortools.sat.python import cp_model
import signed_pencil_sampling_witness as sp
import the_mass12_census_is_complete_and_has_one_exception as m12

ROOT = Path(__file__).resolve().parents[1]


def load_kernel_module():
    p = ROOT / "analysis" / "the_kernel_is_spanned_by_octet_differences.py"
    spec = importlib.util.spec_from_file_location("octet_kernel_local", p)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def addv(a, b): return tuple(x+y for x,y in zip(a,b))
def negmass(x): return sum(-v for v in x if v < 0)

def act(v, g):
    out=[0]*40
    for i,x in enumerate(v): out[g[i]]=x
    return tuple(out)

def orbit(v, gens):
    seen={tuple(v)};q=deque(seen)
    while q:
        x=q.popleft()
        for g in gens:
            y=act(x,g)
            if y not in seen: seen.add(y);q.append(y)
    return seen


def gauges(lines):
    kg=load_kernel_module()
    pts,sf,iso,hyp,perp=kg.geometry()
    assert tuple(map(tuple,iso))==tuple(map(tuple,lines))
    pairs={frozenset((frozenset(L),frozenset(perp(L)))) for L in hyp}
    rows=[]
    for pair in sorted(pairs,key=lambda z: sorted(sorted(x) for x in z)):
        A,B=sorted(pair,key=lambda z:tuple(sorted(z)))
        r=[0]*40
        for p in A:r[p]+=1
        for p in B:r[p]-=1
        r=tuple(r)
        assert all(sum(r[p] for p in L)==0 for L in lines)
        rows.append(r)
    assert len(rows)==45
    moves=tuple(rows)+tuple(tuple(-v for v in r) for r in rows)
    assert len(moves)==90
    return tuple(rows),moves


def parents(lines,thru,pencils,gens,cover):
    (e12,x12,d12),(e16new,x16new,d16new)=sp.discover(lines,thru,pencils,cover)
    assert (d12,d16new)==(1,2)
    out={}
    for c,pen in enumerate(pencils):
        child=addv(e12,pen)
        if cover(child) is not None: continue
        assert sp.depth_at_most_one(child,pencils,cover)[0]==1
        key=min(orbit(child,gens))
        # Transporting x to the canonical representative would require the
        # matching group element; it is unnecessary for the exact local-minimum
        # SAT search, which constrains N^T x directly from the canonical e.
        out.setdefault(key,{"e":key,"depth":1,"orbitSize":len(orbit(key,gens)),"kind":"inherited"})
    nk=min(orbit(e16new,gens))
    out[nk]={"e":nk,"depth":2,"orbitSize":len(orbit(nk,gens)),"kind":"born-at-16"}
    assert len(out)==7
    return sorted(out.values(),key=lambda r:(r["orbitSize"],r["depth"],r["e"]))


def local_min_sat(e, optimum, lines, moves, *, bound=8, budget=30.0):
    model=cp_model.CpModel()
    x=[model.NewIntVar(-bound,bound,f"x{p}") for p in range(40)]
    n=[]
    for p in range(40):
        z=model.NewIntVar(0,bound,f"n{p}")
        model.AddMaxEquality(z,[0,-x[p]])
        n.append(z)
    D=model.NewIntVar(0,40*bound,"D");model.Add(D==sum(n));model.Add(D>=optimum+1)
    for i,L in enumerate(lines): model.Add(sum(x[p] for p in L)==int(e[i]))
    # Every signed octet move must have negativity >= current D.
    for j,mv in enumerate(moves):
        nn=[]
        for p in range(40):
            z=model.NewIntVar(0,bound+1,f"m{j}_{p}")
            model.AddMaxEquality(z,[0,-x[p]-mv[p]])
            nn.append(z)
        model.Add(sum(nn)>=D)
    model.Minimize(D)
    sv=cp_model.CpSolver();sv.parameters.max_time_in_seconds=float(budget);sv.parameters.num_workers=8
    st=sv.Solve(model)
    if st not in (cp_model.OPTIMAL,cp_model.FEASIBLE):
        return {"status":sv.StatusName(st),"witness":None}
    w=tuple(int(sv.Value(v)) for v in x);d=negmass(w)
    assert d>=optimum+1
    assert all(sum(w[p] for p in L)==e[i] for i,L in enumerate(lines))
    neigh=[negmass(addv(w,mv)) for mv in moves]
    assert min(neigh)>=d
    return {"status":sv.StatusName(st),"witness":w,"negativeMass":d,"bestRadius1":min(neigh)}


def radius_two(w,moves):
    d=negmass(w);best=d;best_pair=None;checked=0
    for i,a in enumerate(moves):
        y=addv(w,a)
        for j,b in enumerate(moves):
            checked+=1
            z=addv(y,b);nz=negmass(z)
            if nz<best:
                best=nz;best_pair=(i,j)
    return {"pathsChecked":checked,"bestNegativeMass":best,"decreasingPair":None if best_pair is None else list(best_pair),
            "isRadius2LocalMinimum":best>=d}


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--bound",type=int,default=8);ap.add_argument("--budget",type=float,default=30.0);ap.add_argument("--write",action="store_true");args=ap.parse_args()
    lines,thru,pencils=sp.build_geometry();cover=sp.cover_solver(lines,thru)
    pts,idx,sf,lines2=m12.geometry();assert tuple(map(tuple,lines2))==tuple(map(tuple,lines))
    gens,order=m12.line_action_generators(pts,idx,sf,lines2);assert order==25920
    gauge_rows,moves=gauges(lines)
    rows=[];first_counterexample=None;radius2_counterexample=None
    for r in parents(lines,thru,pencils,gens,cover):
        hit=local_min_sat(r["e"],r["depth"],lines,moves,bound=args.bound,budget=args.budget)
        row={"orbitSize":r["orbitSize"],"kind":r["kind"],"certifiedGlobalDepth":r["depth"],"solverStatus":hit["status"],"boundUsedForSearch":args.bound}
        if hit["witness"] is not None:
            r2=radius_two(hit["witness"],moves)
            row.update({"localMinimumNegativeMass":hit["negativeMass"],"bestRadius1":hit["bestRadius1"],"witness":list(hit["witness"]),"radius2":r2})
            if first_counterexample is None:first_counterexample=row
            if r2["isRadius2LocalMinimum"] and radius2_counterexample is None:radius2_counterexample=row
        rows.append(row)
    assert len(gauge_rows)==45 and len(moves)==90
    result={
        "schema":"holotrade.octet-gauge-local-minimum-counterexample.v1",
        "status":"PASS",
        "kernelGaugeGenerators":45,
        "signedMoves":90,
        "globalDepthSource":"1075622 / exact depth certificates; all seven mass-16 exceptional orbit depths are 1 except orbit 1080 depth 2",
        "rows":rows,
        "radius1CounterexampleFound":first_counterexample is not None,
        "radius2CounterexampleFound":radius2_counterexample is not None,
        "firstRadius1Counterexample":first_counterexample,
        "firstRadius2Counterexample":radius2_counterexample,
        "reading":("A returned witness is an exact counterexample to greedy descent using one signed octet generator: all 90 neighbors are explicitly checked and its negativity is above the independently certified global optimum. "
                   "The coordinate bound only scopes the SAT search for a witness; it does not weaken the local-minimum verification once a witness is found. Radius-two status is checked by all 8100 ordered two-move paths from that fixed witness."),
        "boundary":"Absence of a witness within the requested coordinate bound would not prove global convergence. Presence proves failure of the corresponding local descent radius for that exact coset.",
    }
    print(json.dumps({"status":result["status"],"radius1CounterexampleFound":result["radius1CounterexampleFound"],"radius2CounterexampleFound":result["radius2CounterexampleFound"],
                      "rows":[{k:v for k,v in r.items() if k not in ("witness",)} for r in rows]},indent=2,sort_keys=True))
    if args.write:
        p=Path(__file__).with_name("octet_gauge_local_minimum_counterexample_certificate.json");p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");print(f"written: {p}")

if __name__=="__main__":main()
