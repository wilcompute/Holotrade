#!/usr/bin/env python3
"""Outside-box localization of frozen leaf-lift UNSAT to 4x4 tile degree data.

For a fixed two-pencil factorization, every row line has a small exact domain of
point-multiplicity states (9 clean, 10/18 dirty), and similarly every column
line.  On a product tile L x M, choosing row state v and column state w fixes:

  column degrees of the 4x4 binary tile = (v[q])_{q in M},
  row degrees    of the 4x4 binary tile = (w[p])_{p in L}.

A binary 4x4 matrix with those margins exists iff the two degree sequences are
bipartite-graphical; Gale-Ryser decides this exactly.  This script discards the
1,600 global leaf variables and keeps only one local-state selector for each of
the 40 row lines and 40 column lines, with an allowed-pair table on every one
of 1,600 tiles.

If this selector-only CSP is UNSAT, the corresponding frozen factorization is
already impossible at the local tile degree-sequence layer.  SAT would show
that the stronger full leaf-lift obstruction comes from consistency of the same
point-pair leaf across overlapping W33 product tiles.
"""
from __future__ import annotations

import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path
import time

from ortools.sat.python import cp_model

ROOT = Path(__file__).resolve().parents[1]
FACTOR = ROOT / "data" / "the_111_two_pencil_factorization.json"
OUT = ROOT / "data" / "the_111_frozen_tile_degree_compatibility.json"


def load_leaf_module():
    path = ROOT / "analysis" / "the_111_factorization_leaf_lift.py"
    spec = importlib.util.spec_from_file_location("leaf_tile_degree", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import leaf-lift domains")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def bipartite_graphical(rows, cols):
    r = sorted((int(x) for x in rows), reverse=True)
    c = sorted((int(x) for x in cols), reverse=True)
    if any(x < 0 or x > 4 for x in r + c) or sum(r) != sum(c):
        return False
    for k in range(1, 5):
        if sum(r[:k]) > sum(min(k, x) for x in c):
            return False
    return True


def solve_case(name, frozen, lines, domains, budget, workers):
    row_domains = [domains(x) for x in frozen["rowTokens"]]
    col_domains = [domains(x) for x in frozen["columnTokens"]]
    model = cp_model.CpModel()
    R = [model.NewIntVar(0, len(row_domains[i]) - 1, f"r{i}") for i in range(40)]
    C = [model.NewIntVar(0, len(col_domains[j]) - 1, f"c{j}") for j in range(40)]

    allowed_counts = Counter()
    zero_relation_tiles = []
    for i, L in enumerate(lines):
        for j, M in enumerate(lines):
            allowed = []
            for a, (rv, _rmeta) in enumerate(row_domains[i]):
                coldeg = [rv[q] for q in M]
                for b, (cv, _cmeta) in enumerate(col_domains[j]):
                    rowdeg = [cv[p] for p in L]
                    if bipartite_graphical(rowdeg, coldeg):
                        allowed.append((a, b))
            allowed_counts[len(allowed)] += 1
            if not allowed:
                zero_relation_tiles.append((i, j))
            else:
                model.AddAllowedAssignments([R[i], C[j]], allowed)

    if zero_relation_tiles:
        return {
            "case": name,
            "status": "UNSAT",
            "reason": "at least one tile has no graphical local-state pair",
            "zeroRelationTiles": [list(x) for x in zero_relation_tiles],
            "allowedPairCountHistogram": {str(k): v for k, v in sorted(allowed_counts.items())},
            "branches": 0,
            "conflicts": 0,
            "seconds": 0.0,
        }

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(budget)
    solver.parameters.num_search_workers = int(workers)
    start = time.time(); result = solver.Solve(model); elapsed = round(time.time()-start, 3)
    status = {cp_model.OPTIMAL:"SAT", cp_model.FEASIBLE:"SAT", cp_model.INFEASIBLE:"UNSAT"}.get(result,"UNKNOWN")
    out = {
        "case": name,
        "status": status,
        "seconds": elapsed,
        "branches": solver.NumBranches(),
        "conflicts": solver.NumConflicts(),
        "allowedPairCountHistogram": {str(k): v for k, v in sorted(allowed_counts.items())},
        "zeroRelationTiles": [],
    }
    if status == "SAT":
        out["rowStateChoices"] = [solver.Value(x) for x in R]
        out["columnStateChoices"] = [solver.Value(x) for x in C]
    return out


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--budget',type=float,default=120.0); ap.add_argument('--workers',type=int,default=8); ap.add_argument('--write',action='store_true'); args=ap.parse_args()
    leaf=load_leaf_module(); lines, adj, N = leaf.B12.geometry(); domains=leaf.catalogue(lines,adj,N)
    factor=json.loads(FACTOR.read_text()); assert factor['status']=='PASS'
    cases={}
    for name,row in sorted(factor['cases'].items()):
        cases[name]=solve_case(name,row,lines,domains,args.budget,args.workers)
        print(f"{name:12s} -> {cases[name]['status']:7s} {cases[name]['seconds']:.3f}s",flush=True)
    all_unsat=all(v['status']=='UNSAT' for v in cases.values())
    out={
      'schema':'holotrade.tau2-111-frozen-tile-degree-compatibility.v1','status':'PASS','cases':cases,
      'allThreeFrozenFactorizationsLocallyUnsat':all_unsat,
      'reading':('UNSAT here localizes impossibility of the named frozen factorization to incompatible 4x4 tile margin choices among exact blocker states, before any global leaf-overlap constraint. SAT means the full leaf lift fails at a strictly more global layer.'),
      'boundary':'The model is exact for local tile degree compatibility of the three frozen E witnesses only. It is not a census of all two-pencil factorizations and cannot by itself raise the global tau_2 lower bound.'}
    print(json.dumps(out,indent=2,sort_keys=True))
    if args.write:
      OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')

if __name__=='__main__': main()
