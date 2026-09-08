#!/usr/bin/env python3
"""Exact size-112 tensor-blocker decision after the mass-eight theorem.

For |X|=112, summing first-axis leaf loads over the 40 W33 lines gives
4|X|=448.  Since every row shadow must block all 40 W33 lines, each row-line
load is at least 11; relative to the 40*11 baseline the nonnegative excess has
mass 8.  The committed theorem says every such incidence-image excess is
exactly P_a+P_b.  The same holds independently on the second axis.

PSp(4,3) has three orbits on unordered point pairs with repetition: equal,
collinear distinct, and noncollinear distinct.  Independent automorphisms on
the two product coordinates therefore reduce every possible 112 load-profile
pair to 3x3=9 exact cases.

For one representative case this script uses the actual 1,600 binary leaves,
fixes the exact two-pencil row and column loads, and requires every product line
LxM to be hit.  SAT is independently reconstructed and is an actual 112-leaf
blocker. UNSAT excludes that complete profile-pair orbit. UNKNOWN is no evidence.
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
MASS8 = ROOT / "analysis" / "the_mass_eight_excess_is_two_pencils.py"
TYPES = ("equal", "collinear", "noncollinear")


def load_base():
    spec = importlib.util.spec_from_file_location("mass8_for_112", MASS8)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import mass-eight theorem")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    pts, lines, line_index, pencils, adj = mod.geometry()
    cert = json.loads((ROOT / "data" / "mass_eight_excess_two_pencils.json").read_text())
    if cert.get("status") != "PASS" or cert.get("checks", {}).get("mass_eight_is_exactly_two_pencils") is not True:
        raise RuntimeError("mass-eight two-pencil certificate is not PASS")
    return lines, pencils, adj


def representative_pairs(adj):
    p = 0
    q_col = min(adj[p])
    q_non = min(set(range(40)) - set(adj[p]) - {p})
    return {
        "equal": (p, p),
        "collinear": (p, q_col),
        "noncollinear": (p, q_non),
    }


def profile(pair, pencils):
    a, b = pair
    return tuple(pencils[a][i] + pencils[b][i] for i in range(40))


def solve(row_type, col_type, *, budget, workers):
    lines, pencils, adj = load_base()
    reps = representative_pairs(adj)
    rp, cp = reps[row_type], reps[col_type]
    re, ce = profile(rp, pencils), profile(cp, pencils)
    assert sum(re) == sum(ce) == 8

    model = cp_model.CpModel()
    X = [[model.NewBoolVar(f"x_{p}_{q}") for q in range(40)] for p in range(40)]
    model.Add(sum(X[p][q] for p in range(40) for q in range(40)) == 112)
    for i, L in enumerate(lines):
        model.Add(sum(X[p][q] for p in L for q in range(40)) == 11 + re[i])
    for j, M in enumerate(lines):
        model.Add(sum(X[p][q] for p in range(40) for q in M) == 11 + ce[j])
    for L in lines:
        for M in lines:
            model.Add(sum(X[p][q] for p in L for q in M) >= 1)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(budget)
    solver.parameters.num_search_workers = int(workers)
    solver.parameters.random_seed = 20260912 + 3*TYPES.index(row_type) + TYPES.index(col_type)
    start = time.time()
    st = solver.Solve(model)
    elapsed = round(time.time() - start, 3)
    status = {
        cp_model.OPTIMAL: "SAT", cp_model.FEASIBLE: "SAT", cp_model.INFEASIBLE: "UNSAT"
    }.get(st, "UNKNOWN")
    out = {
        "schema": "holotrade.tau2-112-exact-two-pencil-profile.v1",
        "status": "PASS",
        "rowPairType": row_type,
        "columnPairType": col_type,
        "rowPairRepresentative": list(rp),
        "columnPairRepresentative": list(cp),
        "rowExcessHistogram": {str(a): b for a, b in sorted(Counter(re).items())},
        "columnExcessHistogram": {str(a): b for a, b in sorted(Counter(ce).items())},
        "solverStatus": status,
        "seconds": elapsed,
        "budgetSeconds": float(budget),
        "workers": int(workers),
        "branches": solver.NumBranches(),
        "conflicts": solver.NumConflicts(),
        "scope": "One of the nine exhaustive row/column two-pencil profile-pair orbits forced at |X|=112.",
    }
    if status == "SAT":
        leaves = [(p, q) for p in range(40) for q in range(40) if solver.Value(X[p][q])]
        S = set(leaves)
        row_loads = [sum((p,q) in S for p in L for q in range(40)) for L in lines]
        col_loads = [sum((p,q) in S for p in range(40) for q in M) for M in lines]
        tiles = [[sum((p,q) in S for p in L for q in M) for M in lines] for L in lines]
        assert len(S) == 112
        assert row_loads == [11+x for x in re]
        assert col_loads == [11+x for x in ce]
        assert min(x for row in tiles for x in row) >= 1
        assert sum(map(sum, tiles)) == 16*112
        out.update({
            "actual112Witness": True,
            "independentReconstruction": True,
            "leaves": [list(x) for x in leaves],
            "tileOccupancyHistogram": {str(a): b for a,b in sorted(Counter(x for row in tiles for x in row).items())},
        })
    else:
        out["actual112Witness"] = False
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--row-type", choices=TYPES, required=True)
    ap.add_argument("--col-type", choices=TYPES, required=True)
    ap.add_argument("--budget", type=float, default=180.0)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    if args.budget <= 0 or args.workers <= 0:
        raise ValueError("positive budget/workers required")
    out = solve(args.row_type, args.col_type, budget=args.budget, workers=args.workers)
    print(json.dumps(out, indent=2, sort_keys=True))
    if args.write:
        path = ROOT / "data" / f"the_112_exact_two_pencil_{args.row_type}_{args.col_type}.json"
        path.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
