#!/usr/bin/env python3
"""
Decide the tight case |X| = 110 for depth-2 tensor blocking.

The interval [110, 121] has one question in it: is the double-count lower
bound attained? Everything else follows -- 121 is constructive and proved
forced once the support is a minimum blocker.

At exactly 110 the problem becomes enormously more constrained, and all
of the following are FORCED rather than assumed:

  * summing the line condition gives 4|X| = 440 = 40 x 11, so every
    line-sum is exactly 11, in BOTH the row and the column view;
  * exactness forces the four fibres on each line to be pairwise
    disjoint, so no two points of a row lie on a common line -- every
    row is an independent set, and alpha = 7 caps it;
  * by transpose symmetry every column is independent too;
  * each line's union of fibres is an 11-element blocking set, hence a
    MINIMUM one, of which there are exactly 360.

That last family turns out to be 2-colourable to a set: all 360 minimum
blockers induce bipartite subgraphs. So the natural obstruction -- "a
line supplies only 4 fibres, can a minimum blocker even split into 4
independent sets" -- does not fire. It has to be decided by search.

This model loads every one of those facts as constraints and asks CP-SAT
for feasibility. UNSAT proves tau >= 111 and closes the interval from
below; SAT produces a 110-element witness and closes it from above.
"""

import json
import os
import subprocess
import sys
import time

try:
    from ortools.sat.python import cp_model
except ImportError:
    sys.exit("needs ortools:  py -3 -m pip install ortools")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
N = 40
TAU1 = 11


def load():
    out = subprocess.run(
        ["node", "-e",
         "global.window=global;const S=require('./js/substrate.js');"
         "process.stdout.write(JSON.stringify({lines:S.LINES.map(l=>[...l].sort((a,b)=>a-b)),adj:S.ADJ}))"],
        cwd=ROOT, capture_output=True, text=True, check=True).stdout
    d = json.loads(out)
    return d["lines"], d["adj"]


def build(lines, adj, target=110, break_symmetry=True):
    m = cp_model.CpModel()
    x = [[m.NewBoolVar(f"x_{p}_{q}") for q in range(N)] for p in range(N)]
    per_line = target * 4 // N          # 11 when target is 110

    # the actual requirement
    for A in lines:
        for B in lines:
            m.AddBoolOr([x[p][q] for p in A for q in B])

    # exact total
    m.Add(sum(x[p][q] for p in range(N) for q in range(N)) == target)

    # forced: every line-sum is exactly per_line, in both views
    for L in lines:
        m.Add(sum(x[p][q] for p in L for q in range(N)) == per_line)
        m.Add(sum(x[p][q] for q in L for p in range(N)) == per_line)

    # forced: every row and every column is an independent set, i.e. no two
    # of its members are collinear. Encoded on lines, which is equivalent
    # and much tighter than pairwise adjacency clauses.
    for p in range(N):
        for L in lines:
            m.Add(sum(x[p][q] for q in L) <= 1)
    for q in range(N):
        for L in lines:
            m.Add(sum(x[p][q] for p in L) <= 1)

    # implied cap, stated so the LP sees it: alpha = 7
    for p in range(N):
        m.Add(sum(x[p][q] for q in range(N)) <= 7)
    for q in range(N):
        m.Add(sum(x[p][q] for p in range(N)) <= 7)

    if break_symmetry:
        # the group is transitive on leaves, so some solution contains (0,0)
        m.Add(x[0][0] == 1)

    return m, x


def main():
    seconds = int(sys.argv[sys.argv.index("--seconds") + 1]) if "--seconds" in sys.argv else 900
    target = int(sys.argv[sys.argv.index("--target") + 1]) if "--target" in sys.argv else 110
    lines, adj = load()

    print("THE TIGHT CASE: IS THE DOUBLE-COUNT BOUND ATTAINED?")
    print("=" * 70)
    print(f"  target |X| = {target}, budget {seconds}s")
    print("  every forced consequence loaded as a constraint:")
    print("    exact line-sums 11 in both views; rows and columns independent;")
    print("    alpha = 7 caps; one leaf fixed for symmetry")
    print()

    m, x = build(lines, adj, target=target)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(seconds)
    solver.parameters.num_search_workers = 8
    t = time.time()
    status = solver.Solve(m)
    elapsed = round(time.time() - t, 1)

    names = {cp_model.OPTIMAL: "OPTIMAL", cp_model.FEASIBLE: "FEASIBLE",
             cp_model.INFEASIBLE: "INFEASIBLE", cp_model.UNKNOWN: "UNKNOWN"}
    st = names.get(status, str(status))
    print(f"  status: {st}   ({elapsed}s)")

    result = {
        "schema": "holotrade.tensor-tight-case.v1",
        "target": target, "status": st, "seconds": elapsed,
        "solver": "OR-Tools CP-SAT",
    }

    if status == cp_model.INFEASIBLE:
        print()
        print(f"  ==> UNSAT. No tile-blocking set of size {target} exists.")
        print(f"      tau >= {target + 1}, and the interval closes from below.")
        result["conclusion"] = f"tau >= {target + 1}"
        result["proved"] = True
    elif status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        w = sorted(p * N + q for p in range(N) for q in range(N) if solver.Value(x[p][q]))
        S = set(w)
        ok = all(any((p * N + q) in S for p in A for q in B)
                 for A in lines for B in lines)
        print(f"  ==> SAT. Witness of size {len(w)}, blocks all 1600 tiles: {ok}")
        result["witness"] = w
        result["witnessVerified"] = ok
        result["conclusion"] = f"tau <= {target}"
        result["proved"] = ok
    else:
        print()
        print("  ==> no verdict inside the budget; the tight case stays open")
        result["conclusion"] = "undecided in budget"
        result["proved"] = False

    if "--write" in sys.argv:
        out = os.path.join(ROOT, "data", "tensor_tight_case.json")
        with open(out, "w") as fh:
            json.dump(result, fh, indent=2)
        print(f"\n  written: {os.path.relpath(out, os.getcwd())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
