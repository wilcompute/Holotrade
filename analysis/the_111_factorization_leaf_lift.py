#!/usr/bin/env python3
"""Lift frozen SAT two-pencil factorizations to the actual 111-leaf problem.

The 44-token factorization E=U N^T=N V is only a necessary condition because it
forgets which concrete blocker shadow and which actual leaves realize each row
and column.  The complete local catalogues are now known, so this file restores
exactly the forgotten layer for each of the three frozen SAT factorization
witnesses (equal, collinear, noncollinear dirty-pencil centres).

Let X be the 40x40 binary point-pair matrix of actual leaves and N the 40x40
W(3,3) line/point incidence.  The frozen factorization fixes

    T = 1 + E = N X N^T,

with 1,424 tiles of occupancy one and 176 tiles of occupancy two.  For every row
line, N X exposes a point-multiplicity state on the second coordinate; for every
column line, X N^T exposes the dual first-coordinate state.

The local state domain is exact, not heuristic:

* clean one-pencil token c: the nine minimum 11-blockers B(c,m);
* dirty equal pair {a,a}: the ten 12-point blockers with excess 2P_a;
* dirty distinct pair {a,b}: all 12-point blockers with excess P_a+P_b, plus
  every minimum blocker centred at a containing b with b duplicated and the
  symmetric b-centred possibilities.  The resulting domain has 18 states for
  both collinear and noncollinear pairs.

CP-SAT chooses one state per row/column line and 1,600 binary leaves, enforcing
all row/column point multiplicities, all 1,600 exact tile occupancies, and
|X|=111.  A SAT result is independently rebuilt from the leaf list and is an
actual 111-leaf depth-two blocker.  UNSAT excludes only that particular frozen
factorization witness, not all possible E.  UNKNOWN is no evidence.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import importlib.util
import json
from pathlib import Path
import time

from ortools.sat.python import cp_model

ROOT = Path(__file__).resolve().parents[1]
FACTOR = ROOT / "data" / "the_111_two_pencil_factorization.json"
OUT = ROOT / "data" / "the_111_factorization_leaf_lift.json"


def load_module(name: str, filename: str):
    path = ROOT / "analysis" / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {filename}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


B12 = load_module("blockers12_lift", "the_10480_twelve_point_blockers.py")


def catalogue(lines, adj, N):
    mins = B12.minimum_blockers(adj)
    mins_by_center = defaultdict(list)
    for c, B in mins:
        mins_by_center[c].append(B)
    for c in range(40):
        mins_by_center[c] = sorted(mins_by_center[c], key=lambda s: tuple(sorted(s)))
        assert len(mins_by_center[c]) == 9

    pair_for_excess = {}
    pair_type = {}
    for a in range(40):
        for b in range(a, 40):
            e = tuple(N[i][a] + N[i][b] for i in range(40))
            assert e not in pair_for_excess
            pair_for_excess[e] = (a, b)
            pair_type[(a, b)] = (
                "equal" if a == b else "collinear" if b in adj[a]
                else "noncollinear"
            )

    blockers_by_pair = defaultdict(set)
    for _, B in mins:
        for x in range(40):
            if x in B:
                continue
            S = frozenset(set(B) | {x})
            e = tuple(z - 1 for z in B12.line_counts(S, lines))
            blockers_by_pair[pair_for_excess[e]].add(S)
    for c in range(40):
        S = frozenset(adj[c])
        e = tuple(z - 1 for z in B12.line_counts(S, lines))
        blockers_by_pair[pair_for_excess[e]].add(S)
    assert sum(len(v) for v in blockers_by_pair.values()) == 10480

    def candidate_states(tokens):
        tokens = tuple(sorted(int(x) for x in tokens))
        rows = []
        if len(tokens) == 1:
            c = tokens[0]
            for B in mins_by_center[c]:
                v = tuple(1 if p in B else 0 for p in range(40))
                rows.append((v, {"kind": "minimum11", "centre": c,
                                 "support": sorted(B), "duplicate": None}))
            assert len(rows) == 9
            target = tuple(1 + N[i][c] for i in range(40))
        elif len(tokens) == 2:
            a, b = tokens
            pair = (a, b)
            typ = pair_type[pair]
            for S in sorted(blockers_by_pair[pair], key=lambda s: tuple(sorted(s))):
                v = tuple(1 if p in S else 0 for p in range(40))
                rows.append((v, {"kind": "blocker12", "pairType": typ,
                                 "support": sorted(S), "duplicate": None}))
            if a != b:
                for centre, duplicate in ((a, b), (b, a)):
                    for B in mins_by_center[centre]:
                        if duplicate not in B:
                            continue
                        v = [1 if p in B else 0 for p in range(40)]
                        v[duplicate] += 1
                        rows.append((tuple(v), {
                            "kind": "minimum11_plus_duplicate",
                            "pairType": typ,
                            "centre": centre,
                            "support": sorted(B),
                            "duplicate": duplicate,
                        }))
            rows.sort(key=lambda row: (row[0], json.dumps(row[1], sort_keys=True)))
            assert len(rows) == len({row[0] for row in rows})
            expected = 10 if typ == "equal" else 18
            assert len(rows) == expected
            target = tuple(1 + N[i][a] + N[i][b] for i in range(40))
        else:
            raise ValueError("factorization line must have one or two tokens")

        for v, _ in rows:
            assert sum(v) == (11 if len(tokens) == 1 else 12)
            counts = tuple(sum(N[i][p] * v[p] for p in range(40))
                           for i in range(40))
            assert counts == target
        return rows

    return candidate_states


def target_occupancy(row_tokens, col_tokens, N):
    E1 = [[sum(N[j][p] for p in row_tokens[i]) for j in range(40)]
          for i in range(40)]
    E2 = [[sum(N[i][p] for p in col_tokens[j]) for j in range(40)]
          for i in range(40)]
    assert E1 == E2
    T = [[1 + E1[i][j] for j in range(40)] for i in range(40)]
    assert Counter(x for row in E1 for x in row) == Counter({0: 1424, 1: 176})
    assert Counter(x for row in T for x in row) == Counter({1: 1424, 2: 176})
    assert sum(sum(row) for row in T) == 16 * 111
    return T


def solve_case(name, frozen, lines, N, candidate_states, budget, workers):
    row_tokens = frozen["rowTokens"]
    col_tokens = frozen["columnTokens"]
    assert len(row_tokens) == len(col_tokens) == 40
    T = target_occupancy(row_tokens, col_tokens, N)

    row_domains = [candidate_states(tokens) for tokens in row_tokens]
    col_domains = [candidate_states(tokens) for tokens in col_tokens]
    domain_hist = {
        "rows": dict(sorted(Counter(len(x) for x in row_domains).items())),
        "columns": dict(sorted(Counter(len(x) for x in col_domains).items())),
    }

    model = cp_model.CpModel()
    X = [[model.NewBoolVar(f"x_{p}_{q}") for q in range(40)] for p in range(40)]
    row_sel = []
    col_sel = []

    for i in range(40):
        sels = [model.NewBoolVar(f"rs_{i}_{k}") for k in range(len(row_domains[i]))]
        model.AddExactlyOne(sels)
        row_sel.append(sels)
        L = lines[i]
        for q in range(40):
            model.Add(
                sum(X[p][q] for p in L)
                == sum(sels[k] * row_domains[i][k][0][q]
                       for k in range(len(sels)))
            )

    for j in range(40):
        sels = [model.NewBoolVar(f"cs_{j}_{k}") for k in range(len(col_domains[j]))]
        model.AddExactlyOne(sels)
        col_sel.append(sels)
        M = lines[j]
        for p in range(40):
            model.Add(
                sum(X[p][q] for q in M)
                == sum(sels[k] * col_domains[j][k][0][p]
                       for k in range(len(sels)))
            )

    # Redundant but high-value propagation: every product tile has its exact
    # factorization occupancy, one or two leaves.
    for i, L in enumerate(lines):
        for j, M in enumerate(lines):
            model.Add(sum(X[p][q] for p in L for q in M) == T[i][j])
    model.Add(sum(X[p][q] for p in range(40) for q in range(40)) == 111)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(budget)
    solver.parameters.num_search_workers = int(workers)
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
        "status": status,
        "seconds": elapsed,
        "budgetSeconds": float(budget),
        "workers": int(workers),
        "branches": solver.NumBranches(),
        "conflicts": solver.NumConflicts(),
        "localDomainSizeHistogram": domain_hist,
        "frozenFactorizationStatus": frozen["status"],
    }
    if status != "SAT":
        return out

    leaves = [(p, q) for p in range(40) for q in range(40)
              if solver.Value(X[p][q])]
    assert len(leaves) == 111
    chosen_rows = [next(k for k, s in enumerate(row_sel[i]) if solver.Value(s))
                   for i in range(40)]
    chosen_cols = [next(k for k, s in enumerate(col_sel[j]) if solver.Value(s))
                   for j in range(40)]

    # Independent reconstruction from the 111 returned leaves only.
    leaf_set = set(leaves)
    tile = [[sum((p, q) in leaf_set for p in lines[i] for q in lines[j])
             for j in range(40)] for i in range(40)]
    assert tile == T and min(x for row in tile for x in row) >= 1

    row_mult = [[sum((p, q) in leaf_set for p in lines[i]) for q in range(40)]
                for i in range(40)]
    col_mult = [[sum((p, q) in leaf_set for q in lines[j]) for p in range(40)]
                for j in range(40)]
    assert all(tuple(row_mult[i]) == row_domains[i][chosen_rows[i]][0]
               for i in range(40))
    assert all(tuple(col_mult[j]) == col_domains[j][chosen_cols[j]][0]
               for j in range(40))

    out.update({
        "actual111LeafWitness": True,
        "independentTileReconstruction": True,
        "tileOccupancyHistogram": dict(sorted(Counter(x for row in tile for x in row).items())),
        "leaves": [list(x) for x in leaves],
        "rowStateChoices": [row_domains[i][chosen_rows[i]][1] for i in range(40)],
        "columnStateChoices": [col_domains[j][chosen_cols[j]][1] for j in range(40)],
    })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=float, default=180.0)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--case", choices=["equal", "collinear", "noncollinear", "all"], default="all")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    if args.budget <= 0 or args.workers <= 0:
        raise ValueError("positive budget and worker count required")

    factor = json.loads(FACTOR.read_text())
    assert factor["status"] == "PASS" and factor["statusHistogram"] == {"SAT": 3}
    lines, adj, N = B12.geometry()
    candidate_states = catalogue(lines, adj, N)
    names = [args.case] if args.case != "all" else ["equal", "collinear", "noncollinear"]
    cases = {}
    for name in names:
        row = solve_case(name, factor["cases"][name], lines, N, candidate_states,
                         args.budget, args.workers)
        cases[name] = row
        print(f"{name:12s} -> {row['status']:7s} {row['seconds']:.3f}s", flush=True)

    actual = [name for name, row in cases.items() if row["status"] == "SAT"]
    out = {
        "schema": "holotrade.tau2-111-factorization-leaf-lift.v1",
        "status": "PASS",
        "cases": cases,
        "actual111WitnessCases": actual,
        "actual111WitnessFound": bool(actual),
        "provedTau2Equals111": bool(actual),
        "reading": (
            "SAT is independently verified as a binary 111-leaf set meeting every one of the 1600 W33 product lines, so together with the repository lower bound tau_2>=111 it proves tau_2=111. UNSAT excludes only the named frozen factorization witness. UNKNOWN is no evidence."
        ),
        "boundary": (
            "This pass tests the three specific SAT factorization witnesses frozen in data/the_111_two_pencil_factorization.json. Unless SAT produces an actual leaf witness, it is not a census of all possible factorization matrices E and cannot raise the lower bound."
        ),
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    if args.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
