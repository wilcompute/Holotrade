#!/usr/bin/env python3
"""Exact, witness-independent decision model for tau_2(W(3,3)) at size 111.

This closes the sampling gap left by ``the_111_factorization_leaf_lift``.
That pass fixes one SAT two-pencil factorization E per centre orbit.  Here E and
all blocker labels are eliminated entirely: the variables are exactly the
1,600 possible leaves X[p,q].

The already-certified pencil-excess theorem implies that any 111-leaf blocker
has, on each coordinate axis, 36 line loads 11 and four line loads 12, with the
four dirty lines forming a complete point-pencil.  PSp(4,3) has exactly three
orbits on ordered pairs of pencil centres: equal, collinear, noncollinear.
Therefore, after fixing one representative centre pair, a 111 witness exists
iff this finite 0/1 system is feasible:

  * X[p,q] in {0,1};
  * |X| = 111;
  * each first-coordinate W33 line has total leaf load 11 or 12 according to
    the fixed dirty pencil;
  * each second-coordinate W33 line has the analogous exact load;
  * every one of the 1,600 product lines L x M contains at least one leaf.

No factorization witness, minimum-blocker label, support fingerprint, parity
ansatz, or symmetry assumption beyond the proved three centre orbits is used.
SAT is independently reconstructed from the leaf list.  UNSAT in all three
cases proves tau_2 >= 112; combined with the committed 115 construction this
would improve the certified interval to [112,115].
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
OUT = ROOT / "data" / "the_111_exact_three_centre_leaf_csp.json"


def load_geometry():
    path = ROOT / "analysis" / "the_10480_twelve_point_blockers.py"
    spec = importlib.util.spec_from_file_location("b12_exact111", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import W33 blocker geometry")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    lines, adj, N = mod.geometry()
    assert len(lines) == 40 and all(len(L) == 4 for L in lines)
    return lines, adj


def centre_representatives(adj):
    c0 = 0
    col = min(adj[c0])
    non = min(set(range(40)) - adj[c0] - {c0})
    return {
        "equal": (c0, c0),
        "collinear": (c0, col),
        "noncollinear": (c0, non),
    }


def solve_case(name, centres, lines, *, budget, workers):
    c_row, c_col = centres
    dirty_rows = {i for i, L in enumerate(lines) if c_row in L}
    dirty_cols = {j for j, L in enumerate(lines) if c_col in L}
    assert len(dirty_rows) == len(dirty_cols) == 4

    model = cp_model.CpModel()
    X = [[model.NewBoolVar(f"x_{p}_{q}") for q in range(40)] for p in range(40)]

    model.Add(sum(X[p][q] for p in range(40) for q in range(40)) == 111)

    for i, L in enumerate(lines):
        model.Add(sum(X[p][q] for p in L for q in range(40)) == (12 if i in dirty_rows else 11))
    for j, M in enumerate(lines):
        model.Add(sum(X[p][q] for p in range(40) for q in M) == (12 if j in dirty_cols else 11))

    for L in lines:
        for M in lines:
            model.Add(sum(X[p][q] for p in L for q in M) >= 1)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(budget)
    solver.parameters.num_search_workers = int(workers)
    # Deterministic seed; parallel search may still change the first SAT witness,
    # but SAT/UNSAT semantics are independent of witness ordering.
    solver.parameters.random_seed = 20260907
    start = time.time()
    result = solver.Solve(model)
    elapsed = round(time.time() - start, 3)
    status = {
        cp_model.OPTIMAL: "SAT",
        cp_model.FEASIBLE: "SAT",
        cp_model.INFEASIBLE: "UNSAT",
    }.get(result, "UNKNOWN")

    out = {
        "case": name,
        "centres": [c_row, c_col],
        "status": status,
        "seconds": elapsed,
        "budgetSeconds": float(budget),
        "workers": int(workers),
        "branches": solver.NumBranches(),
        "conflicts": solver.NumConflicts(),
        "dirtyRows": sorted(dirty_rows),
        "dirtyColumns": sorted(dirty_cols),
    }
    if status != "SAT":
        return out

    leaves = [(p, q) for p in range(40) for q in range(40) if solver.Value(X[p][q])]
    assert len(leaves) == 111 and len(set(leaves)) == 111
    leaf_set = set(leaves)
    row_loads = [sum((p, q) in leaf_set for p in L for q in range(40)) for L in lines]
    col_loads = [sum((p, q) in leaf_set for p in range(40) for q in M) for M in lines]
    tiles = [[sum((p, q) in leaf_set for p in L for q in M) for M in lines] for L in lines]
    assert all(row_loads[i] == (12 if i in dirty_rows else 11) for i in range(40))
    assert all(col_loads[j] == (12 if j in dirty_cols else 11) for j in range(40))
    assert min(x for row in tiles for x in row) >= 1
    assert sum(sum(row) for row in tiles) == 16 * 111
    out.update({
        "independentReconstruction": True,
        "leaves": [list(x) for x in leaves],
        "tileOccupancyHistogram": {str(k): v for k, v in sorted(Counter(x for row in tiles for x in row).items())},
        "rowLoadHistogram": {str(k): v for k, v in sorted(Counter(row_loads).items())},
        "columnLoadHistogram": {str(k): v for k, v in sorted(Counter(col_loads).items())},
    })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=float, default=300.0)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--case", choices=["equal", "collinear", "noncollinear", "all"], default="all")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    if args.budget <= 0 or args.workers <= 0:
        raise ValueError("positive budget and worker count required")

    lines, adj = load_geometry()
    reps = centre_representatives(adj)
    names = list(reps) if args.case == "all" else [args.case]
    cases = {}
    for name in names:
        row = solve_case(name, reps[name], lines, budget=args.budget, workers=args.workers)
        cases[name] = row
        print(f"{name:12s} -> {row['status']:7s} {row['seconds']:.3f}s", flush=True)

    all_three = set(cases) == {"equal", "collinear", "noncollinear"}
    all_unsat = all_three and all(row["status"] == "UNSAT" for row in cases.values())
    sats = [name for name, row in cases.items() if row["status"] == "SAT"]
    out = {
        "schema": "holotrade.tau2-111-exact-three-centre-leaf-csp.v1",
        "status": "PASS",
        "cases": cases,
        "actual111WitnessCases": sats,
        "actual111WitnessFound": bool(sats),
        "allThreeCentreCasesUnsat": all_unsat,
        "certifiedTau2Interval": [112, 115] if all_unsat else ([111, 111] if sats else [111, 115]),
        "theoremScope": (
            "The pencil-excess theorem makes the three fixed centre relations exhaustive under diagonal PSp(4,3). This model otherwise uses the actual 1,600 leaf variables and exact product-line blocking constraints, so three UNSAT results exclude every 111-leaf tensor blocker."
        ),
        "reading": (
            "SAT returns and independently verifies an actual 111-leaf blocker, proving tau_2=111 with the existing lower bound. Three exact UNSAT results prove tau_2>=112. UNKNOWN is no mathematical evidence."
        ),
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    if args.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
