#!/usr/bin/env python3
"""
Attack the interval from the TOP: is there a 114-leaf blocker?

Every previous attempt pushed at 110, the bottom. That was the wrong end.
We have a verified 115-leaf blocker, so tau_2 <= 115, and therefore

    no 114-leaf blocker exists   ==>   tau_2 = 115 EXACTLY,

and the interval closes. One infeasibility at 114 finishes the problem, where
at 110 an infeasibility would only move the floor by one.

WHY 114 IS BETTER POSED THAN 110.  The double count 4|X| >= sum of shadows
>= 440 has slack 4|X| - 440. At |X| = 110 the slack is zero, which is why
every consequence is forced -- and also why the search space is so rigid that
CP-SAT cannot navigate it. At |X| = 114 the slack is

    4 * 114 - 440 = 16

spread over 40 lines. Writing row(L) = sum over p in L of |X_p|, every line
has row(L) >= |S_L| >= tau_1 = 11, and

    sum over L of (row(L) - 11) = 16.

So at least 24 of the 40 lines are still FULLY TIGHT: their four fibres are
pairwise disjoint and their shadow is a minimum blocker. The structure is
almost all still there, but the model is no longer a knife edge, and a solver
has somewhere to move.

WHAT IS ENCODED.  The shadow gets its own variables rather than being left
implicit in the tile constraints:

    sh(L,q) = 1 iff some fibre over L contains q,
    sum over q of sh(L,q) >= tau_1 = 11          (the shadow must block, and
                                                  no blocker is smaller)
    sum over q in M of sh(L,q) >= 1  for all M   (the shadow blocks line M --
                                                  the tile constraint, but
                                                  stated where it propagates)

plus the slack identity above as an explicit budget. The per-line slack is
capped at 16 and the count of fully tight lines is bounded below by 24, both
of which are consequences rather than assumptions.

OUTCOMES.
    INFEASIBLE  ->  tau_2 = 115 exactly. The interval CLOSES.
    FEASIBLE    ->  a 114-leaf blocker, verified from scratch; the upper bound
                    improves to 114 and the interval narrows to [110, 114].
    UNKNOWN     ->  nothing, and reported as nothing.
"""

import json
import os
import subprocess
import sys

try:
    from ortools.sat.python import cp_model
except ImportError:
    sys.exit("needs ortools:  py -3 -m pip install ortools")

ROOT = r"C:\Repos\Holotrade"
N = 40
TAU1 = 11
WITNESS = 115           # verified upper bound
SHADOW_LOWER = 110


def load():
    out = subprocess.run(
        ["node", "-e",
         "global.window=global;const S=require('./js/substrate.js');"
         "process.stdout.write(JSON.stringify(S.LINES.map(l=>[...l]"
         ".sort((a,b)=>a-b))))"],
        cwd=ROOT, capture_output=True, text=True)
    if out.returncode:
        sys.exit("node failed: " + out.stderr[:400])
    return json.loads(out.stdout)


def build(lines, size):
    slack = 4 * size - N * TAU1          # 16 at size 114
    m = cp_model.CpModel()
    x = [[m.NewBoolVar("x%d_%d" % (p, q)) for q in range(N)] for p in range(N)]

    # the shadow of each line, given its own variables
    sh = [[m.NewBoolVar("s%d_%d" % (li, q)) for q in range(N)]
          for li in range(N)]
    for li, L in enumerate(lines):
        for q in range(N):
            for p in L:
                m.AddImplication(x[p][q], sh[li][q])
            m.Add(sh[li][q] <= sum(x[p][q] for p in L))
        # no blocking set is smaller than tau_1
        m.Add(sum(sh[li]) >= TAU1)
        # the shadow must meet every line: this is the tile constraint,
        # stated on sh where it propagates instead of on raw leaves
        for M in lines:
            m.Add(sum(sh[li][q] for q in M) >= 1)

    # per-line slack, and the global budget it must fit inside
    rows = []
    for li, L in enumerate(lines):
        r = m.NewIntVar(TAU1, TAU1 + slack, "r%d" % li)
        m.Add(r == sum(x[p][q] for p in L for q in range(N)))
        m.Add(r >= sum(sh[li]))          # union is at most the sum of parts
        rows.append(r)
    m.Add(sum(rows) == 4 * size)
    m.Add(sum(rows) - N * TAU1 == slack)

    # at least 40 - slack lines are fully tight (slack is a non-negative
    # integer per line, so at most `slack` lines can carry any of it)
    tight = [m.NewBoolVar("t%d" % li) for li in range(N)]
    for li in range(N):
        m.Add(rows[li] == TAU1).OnlyEnforceIf(tight[li])
        m.Add(rows[li] >= TAU1 + 1).OnlyEnforceIf(tight[li].Not())
    m.Add(sum(tight) >= N - slack)

    # a fully tight line has disjoint fibres and a minimum-blocker shadow
    for li, L in enumerate(lines):
        m.Add(sum(sh[li]) == TAU1).OnlyEnforceIf(tight[li])
        for q in range(N):
            m.Add(sum(x[p][q] for p in L) <= 1).OnlyEnforceIf(tight[li])

    m.Add(sum(x[p][q] for p in range(N) for q in range(N)) == size)
    return m, x, slack


def verify(X, lines):
    S = set(X)
    return all(any((p * N + q) in S for p in A for q in B)
               for A in lines for B in lines)


def main():
    size = (int(sys.argv[sys.argv.index("--size") + 1])
            if "--size" in sys.argv else WITNESS - 1)
    seconds = (float(sys.argv[sys.argv.index("--seconds") + 1])
               if "--seconds" in sys.argv else 2400.0)
    lines = load()
    m, x, slack = build(lines, size)

    print("CLOSING THE INTERVAL FROM THE TOP")
    print("=" * 70)
    print("  verified upper bound   : %d" % WITNESS)
    print("  testing size           : %d" % size)
    print("  double-count slack     : 4*%d - 440 = %d" % (size, slack))
    print("  lines forced fully tight: at least %d of %d" % (N - slack, N))
    print()
    print("  INFEASIBLE here means tau_2 = %d exactly and the interval closes."
          % WITNESS)
    print()
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = seconds
    s.parameters.num_search_workers = 8
    s.parameters.symmetry_level = 4
    print("  solving, budget %.0f s ..." % seconds)
    st = s.Solve(m)
    name = s.StatusName(st)
    print("  status: %s   (%.1f s)" % (name, s.WallTime()))
    print()

    res = {
        "schema": "holotrade.tensor-close-at-114.v1",
        "size": size,
        "status": name,
        "wallSeconds": round(s.WallTime(), 1),
        "slackBudget": slack,
        "linesForcedFullyTight": N - slack,
        "verifiedUpperBound": WITNESS,
    }
    if st == cp_model.INFEASIBLE:
        print("  ==> INFEASIBLE.  No %d-leaf blocker exists." % size)
        print("      tau_2 >= %d, and the verified witness gives tau_2 <= %d."
              % (size + 1, WITNESS))
        if size + 1 == WITNESS:
            print("      THEREFORE tau_2 = %d EXACTLY.  THE INTERVAL CLOSES."
                  % WITNESS)
            res["exactTau"] = WITNESS
        res.update({"proved": True,
                    "conclusion": "tau_2 = %d exactly" % WITNESS
                                  if size + 1 == WITNESS
                                  else "lower bound rises to %d" % (size + 1)})
    elif st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        X = sorted(p * N + q for p in range(N) for q in range(N)
                   if s.Value(x[p][q]))
        ok = verify(X, lines)
        print("  ==> FEASIBLE: %d leaves; verified against all 1600 tiles: %s"
              % (len(X), ok))
        if ok:
            print("      UPPER BOUND %d -> %d;  tau_2 in [%d, %d]"
                  % (WITNESS, len(X), SHADOW_LOWER, len(X)))
        res.update({"witness": X, "witnessVerified": ok, "proved": ok,
                    "conclusion": "upper bound improves to %d" % len(X)
                                  if ok else "solver returned an invalid set"})
    else:
        print("  ==> UNKNOWN in budget.  Nothing proved; tau_2 stays [110, 115].")
        res.update({"proved": False, "conclusion": "undecided in budget",
                    "intervalUnchanged": [SHADOW_LOWER, WITNESS]})

    if "--write" in sys.argv:
        out = os.path.join(ROOT, "data", "tensor_close_at_114.json")
        with open(out, "w") as fh:
            json.dump(res, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(out, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
