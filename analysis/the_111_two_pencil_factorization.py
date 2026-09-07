#!/usr/bin/env python3
"""
A smaller necessary-condition problem for a hypothetical 111-leaf tensor blocker.

The companion theorem the_mass_eight_excess_is_two_pencils.py proves that the
40x40 tile-excess matrix E of any 111 witness has an exact two-sided incidence
factorization

    E = U N^T = N V,

where N is W(3,3) line/point incidence.  On each axis the committed
pencil-excess theorem fixes 36 clean lines and four dirty lines forming one
point-pencil.  A clean row of U has token mass one; a dirty row has token mass
two.  Dually each clean column of V has mass one and each dirty column mass
two.  Hence there are 44 point tokens on either side, not 1600 leaf variables.

This file asks the exact feasibility question for that necessary condition in
the three lossless centre cases already certified by w33_tau2_111_three_cases.g:
row/column dirty-pencil centres equal, collinear, or noncollinear.

A SAT result does NOT produce a 111 blocker: it only survives this relaxation.
An UNSAT result excludes that complete centre case, because every true witness
must induce such a factorization.  UNKNOWN is no evidence.  The positive
control U=N, V=N^T verifies the same equality machinery at uniform token mass
four before any solve is attempted.
"""
from __future__ import annotations

import argparse
from collections import Counter
import itertools
import json
from pathlib import Path
import time

from ortools.sat.python import cp_model

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "the_111_two_pencil_factorization.json"
Q = 3


def norm(v):
    i = next(k for k, x in enumerate(v) if x % Q)
    z = pow(v[i] % Q, -1, Q)
    return tuple((z * x) % Q for x in v)


def form(u, v):
    return (u[0] * v[2] - u[2] * v[0]
            + u[1] * v[3] - u[3] * v[1]) % Q


def geometry():
    pts = sorted({norm(v) for v in itertools.product(range(Q), repeat=4) if any(v)})
    pidx = {p: i for i, p in enumerate(pts)}
    line_sets = set()
    for a, b in itertools.combinations(range(40), 2):
        if form(pts[a], pts[b]):
            continue
        span = set()
        for x, y in itertools.product(range(Q), repeat=2):
            if not (x or y):
                continue
            span.add(pidx[norm(tuple((x * pts[a][k] + y * pts[b][k]) % Q
                                     for k in range(4)))])
        if len(span) == 4:
            line_sets.add(frozenset(span))
    lines = sorted(line_sets, key=lambda s: tuple(sorted(s)))
    N = [[1 if p in line else 0 for p in range(40)] for line in lines]
    coll = [set() for _ in range(40)]
    for line in lines:
        for p in line:
            coll[p] |= set(line) - {p}
    return pts, lines, N, coll


def explicit_control(N):
    """U=N, V=N^T gives E=NN^T with four tokens on every row/column."""
    U = [row[:] for row in N]
    V = [[N[j][p] for j in range(40)] for p in range(40)]
    left = [[sum(U[i][p] * N[j][p] for p in range(40))
             for j in range(40)] for i in range(40)]
    right = [[sum(N[i][p] * V[p][j] for p in range(40))
              for j in range(40)] for i in range(40)]
    return {
        "rowTokenMasses": sorted(set(sum(row) for row in U)),
        "columnTokenMasses": sorted(set(sum(V[p][j] for p in range(40)) for j in range(40))),
        "equal": left == right,
        "diagonal": sorted(set(left[i][i] for i in range(40))),
        "offDiagonal": sorted(set(left[i][j] for i in range(40) for j in range(40) if i != j)),
    }


def dirty_lines(lines, centre):
    return frozenset(i for i, line in enumerate(lines) if centre in line)


def solve_case(lines, N, c_row, c_col, budget, workers):
    dirty_r = dirty_lines(lines, c_row)
    dirty_c = dirty_lines(lines, c_col)
    assert len(dirty_r) == len(dirty_c) == 4

    model = cp_model.CpModel()
    row_tokens = []
    col_tokens = []
    for i in range(40):
        row = [model.NewIntVar(0, 39, f"r_{i}_{k}")
               for k in range(2 if i in dirty_r else 1)]
        if len(row) == 2:
            model.Add(row[0] <= row[1])
        row_tokens.append(row)
    for j in range(40):
        col = [model.NewIntVar(0, 39, f"c_{j}_{k}")
               for k in range(2 if j in dirty_c else 1)]
        if len(col) == 2:
            model.Add(col[0] <= col[1])
        col_tokens.append(col)

    # Cache membership bits: rmem[i][k][j] says row token (i,k) lies on
    # column line j; cmem[j][k][i] is its column-token dual.
    rmem = [[[] for _ in row_tokens[i]] for i in range(40)]
    for i in range(40):
        for k, token in enumerate(row_tokens[i]):
            for j in range(40):
                b = model.NewBoolVar(f"rm_{i}_{k}_{j}")
                model.AddElement(token, [N[j][p] for p in range(40)], b)
                rmem[i][k].append(b)
    cmem = [[[] for _ in col_tokens[j]] for j in range(40)]
    for j in range(40):
        for k, token in enumerate(col_tokens[j]):
            for i in range(40):
                b = model.NewBoolVar(f"cm_{j}_{k}_{i}")
                model.AddElement(token, [N[i][p] for p in range(40)], b)
                cmem[j][k].append(b)

    for i in range(40):
        for j in range(40):
            model.Add(sum(rmem[i][k][j] for k in range(len(row_tokens[i])))
                      == sum(cmem[j][k][i] for k in range(len(col_tokens[j]))))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(budget)
    solver.parameters.num_search_workers = int(workers)
    start = time.time()
    res = solver.Solve(model)
    seconds = round(time.time() - start, 3)
    status = {
        cp_model.OPTIMAL: "SAT",
        cp_model.FEASIBLE: "SAT",
        cp_model.INFEASIBLE: "UNSAT",
    }.get(res, "UNKNOWN")

    record = {
        "cRow": c_row,
        "cCol": c_col,
        "dirtyRows": sorted(dirty_r),
        "dirtyColumns": sorted(dirty_c),
        "status": status,
        "seconds": seconds,
        "budgetSeconds": float(budget),
        "workers": int(workers),
        "branches": solver.NumBranches(),
        "conflicts": solver.NumConflicts(),
    }
    if status == "SAT":
        rt = [[solver.Value(x) for x in row] for row in row_tokens]
        ct = [[solver.Value(x) for x in col] for col in col_tokens]
        E1 = [[sum(N[j][p] for p in rt[i]) for j in range(40)] for i in range(40)]
        E2 = [[sum(N[i][p] for p in ct[j]) for j in range(40)] for i in range(40)]
        assert E1 == E2
        assert sum(sum(row) for row in E1) == 176
        assert all(sum(E1[i]) == (8 if i in dirty_r else 4) for i in range(40))
        assert all(sum(E1[i][j] for i in range(40)) == (8 if j in dirty_c else 4)
                   for j in range(40))
        record.update({
            "rowTokens": rt,
            "columnTokens": ct,
            "excessEntryHistogram": dict(sorted(Counter(x for row in E1 for x in row).items())),
            "rowTokenMultiplicityHistogram": dict(sorted(Counter(p for row in rt for p in row).values()).items()),
            "columnTokenMultiplicityHistogram": dict(sorted(Counter(p for col in ct for p in col).values()).items()),
            "independentEqualityCheck": True,
            "totalExcess": 176,
        })
    return record


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=float, default=60.0)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    if args.budget <= 0 or args.workers <= 0:
        raise ValueError("positive budget and worker count required")

    pts, lines, N, coll = geometry()
    assert len(pts) == len(lines) == 40
    control = explicit_control(N)
    assert control["equal"] and control["rowTokenMasses"] == [4] and control["columnTokenMasses"] == [4]

    c_row = 0
    reps = [
        ("equal", 0),
        ("collinear", min(coll[0])),
        ("noncollinear", min(set(range(40)) - {0} - coll[0])),
    ]
    cases = {}
    for name, c_col in reps:
        row = solve_case(lines, N, c_row, c_col, args.budget, args.workers)
        cases[name] = row
        print(f"{name:12s} -> {row['status']:7s}  {row['seconds']:.3f}s", flush=True)

    statuses = Counter(row["status"] for row in cases.values())
    all_unsat = statuses == Counter({"UNSAT": 3})
    any_sat = statuses["SAT"] > 0
    interval = [112, 115] if all_unsat else [111, 115]
    checks = {
        "geometry_40_by_40": len(pts) == len(lines) == 40,
        "positive_control_exact": control["equal"],
        "three_lossless_centre_cases": set(cases) == {"equal", "collinear", "noncollinear"},
        "each_dirty_set_is_a_four_line_pencil": all(len(x["dirtyRows"]) == len(x["dirtyColumns"]) == 4
                                                    for x in cases.values()),
        "solver_statuses_are_scoped": all(x["status"] in {"SAT", "UNSAT", "UNKNOWN"}
                                      for x in cases.values()),
        "sat_rows_reverified": all(x["status"] != "SAT" or x.get("independentEqualityCheck")
                                  for x in cases.values()),
    }
    out = {
        "schema": "holotrade.tau2-111-two-pencil-factorization.v1",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "control": control,
        "cases": cases,
        "statusHistogram": dict(sorted(statuses.items())),
        "allThreeCasesUnsat": all_unsat,
        "anyCaseSat": any_sat,
        "certifiedTau2IntervalAfterThisPass": interval,
        "necessaryCondition": (
            "For E=tile_occupancy-J, the mass-eight theorem gives E=U N^T=N V. "
            "U has one point token on each of the 36 clean row lines and two on "
            "the four dirty row lines through c_row; V has the column-dual token "
            "masses through c_col. The three ordered centre relations equal, "
            "collinear and noncollinear are complete under diagonal PSp(4,3)."
        ),
        "reading": (
            "UNSAT excludes that entire centre case. SAT only survives this "
            "44-token-per-axis relaxation and is not a 111-leaf witness. UNKNOWN "
            "is no mathematical evidence. The interval improves to [112,115] "
            "only if all three exact factorization cases are UNSAT."
        ),
        "sourceTheorem": "analysis/the_mass_eight_excess_is_two_pencils.py",
        "sourcePencilReduction": "analysis/tensor_111_pencil_excess.py",
        "sourceThreeCases": "analysis/w33_tau2_111_three_cases.g",
        "boundary": (
            "This factorization forgets the actual leaf set and the blocker-support "
            "labels beyond their line-excess pencils. A SAT factorization can be "
            "spurious. Solver budgets affect UNKNOWN only; an INFEASIBLE/UNSAT "
            "return is an exact CP-SAT proof for this finite model."
        ),
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    if args.write:
        if out["status"] != "PASS":
            raise AssertionError("checks failed; refusing to write")
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
