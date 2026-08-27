#!/usr/bin/env python3
"""
Close the interval from the top, with BOTH axes: is there a 114-leaf blocker?

We have a verified 115-leaf blocker, so tau_2 <= 115 and

    no 114-leaf blocker exists   ==>   tau_2 = 115 EXACTLY.

One infeasibility here finishes a problem that has been open all session.

WHY 114 AND NOT 110.  The double count 4|X| >= sum of shadows >= 440 has
slack 4|X| - 440. At 110 that slack is ZERO: every consequence is forced, and
the search space is a knife edge with nowhere for a solver to move -- which is
why eight attacks there all returned UNKNOWN. At 114 the slack is 16, spread
over 40 lines. Almost all the structure survives, but the model can breathe.

WHAT THE SLACK BUYS, ON BOTH AXES.  Write row(L) = sum over p in L of |X_p|.
Every line has row(L) >= |S_L| >= tau_1 = 11, and sum over L of (row(L) - 11)
= 16. Since each excess is a non-negative integer, at most 16 lines carry any
of it, so

    at least 24 of the 40 lines are FULLY TIGHT:
    their four fibres are pairwise disjoint and their shadow is a
    minimum blocker of exactly 11 points.

Blocking is symmetric in the two coordinates and |X| = |X^T|, so the same
holds transposed for the column shadows T_M = union of the co-fibres over M.
The previous version of this file encoded only the row half; this one encodes
both, together with the cross-implication that couples them:

    if column-line M is fully tight, its co-fibres are pairwise disjoint,
    so no single fibre X_p can contain two points of M.

That last constraint is what the one-sided model had no way to say. It is the
114-analogue of the step that produced the independence result at 110: there,
full tightness made EVERY fibre and co-fibre an independent set; here, at
least 24 of the 40 lines impose it, and which 24 is left to the solver.

OUTCOMES.
    INFEASIBLE  ->  tau_2 = 115 exactly. THE INTERVAL CLOSES.
    FEASIBLE    ->  a 114-leaf blocker, re-verified from scratch against all
                    1,600 tiles; the upper bound improves and the interval
                    narrows to [110, 114].
    UNKNOWN     ->  nothing, reported as nothing.
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
WITNESS = 115
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
    slack = 4 * size - N * TAU1
    m = cp_model.CpModel()
    x = [[m.NewBoolVar("x%d_%d" % (p, q)) for q in range(N)] for p in range(N)]

    def axis(get):
        """Build shadows, slack and tightness for one axis.

        get(li, p, q) returns the leaf variable indexed so that `p` runs over
        the line and `q` over the transverse coordinate.
        """
        sh = [[m.NewBoolVar("") for _ in range(N)] for _ in range(N)]
        rows, tight = [], []
        for li, L in enumerate(lines):
            for q in range(N):
                for p in L:
                    m.AddImplication(get(p, q), sh[li][q])
                m.Add(sh[li][q] <= sum(get(p, q) for p in L))
            m.Add(sum(sh[li]) >= TAU1)          # no blocker is smaller
            for M in lines:                      # the shadow blocks every line
                m.Add(sum(sh[li][q] for q in M) >= 1)
            r = m.NewIntVar(TAU1, TAU1 + slack, "")
            m.Add(r == sum(get(p, q) for p in L for q in range(N)))
            m.Add(r >= sum(sh[li]))              # union <= sum of parts
            rows.append(r)
            t = m.NewBoolVar("")
            m.Add(r == TAU1).OnlyEnforceIf(t)
            m.Add(r >= TAU1 + 1).OnlyEnforceIf(t.Not())
            tight.append(t)
            # a fully tight line: shadow is a MINIMUM blocker and the parts
            # over it are pairwise disjoint
            m.Add(sum(sh[li]) == TAU1).OnlyEnforceIf(t)
            for q in range(N):
                m.Add(sum(get(p, q) for p in L) <= 1).OnlyEnforceIf(t)
        m.Add(sum(rows) == 4 * size)
        m.Add(sum(tight) >= N - slack)
        return sh, rows, tight

    shR, rowR, tightR = axis(lambda p, q: x[p][q])
    shC, rowC, tightC = axis(lambda p, q: x[q][p])

    # THE CROSS-IMPLICATION, which the one-sided model could not express.
    # If column-line M is fully tight its co-fibres are pairwise disjoint,
    # so no single fibre X_p may hold two points of M.
    for mi, M in enumerate(lines):
        for p in range(N):
            m.Add(sum(x[p][q] for q in M) <= 1).OnlyEnforceIf(tightC[mi])
    for li, L in enumerate(lines):
        for q in range(N):
            m.Add(sum(x[p][q] for p in L) <= 1).OnlyEnforceIf(tightR[li])

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

    print("CLOSING FROM THE TOP, TWO-SIDED")
    print("=" * 70)
    print("  verified upper bound     : %d" % WITNESS)
    print("  testing size             : %d" % size)
    print("  slack 4*%d - 440         : %d" % (size, slack))
    print("  fully tight lines, each axis: at least %d of %d" % (N - slack, N))
    print("  cross-implication        : a tight column forbids two points of")
    print("                             it in any single fibre")
    print()
    print("  INFEASIBLE => tau_2 = %d exactly and the interval CLOSES." % WITNESS)
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
        "schema": "holotrade.tensor-close-at-114-two-sided.v1",
        "size": size, "status": name,
        "wallSeconds": round(s.WallTime(), 1),
        "slackBudget": slack,
        "linesForcedFullyTightPerAxis": N - slack,
        "verifiedUpperBound": WITNESS,
        "encodes": ["row shadows", "column shadows", "per-axis slack budget",
                    "per-axis tightness indicators",
                    "cross-implication coupling the axes"],
    }
    if st == cp_model.INFEASIBLE:
        print("  ==> INFEASIBLE.  No %d-leaf blocker exists." % size)
        print("      With the verified %d-leaf witness:" % WITNESS)
        print("      tau_2 = %d EXACTLY.  THE INTERVAL CLOSES." % WITNESS)
        res.update({"proved": True, "exactTau": WITNESS,
                    "conclusion": "tau_2 = %d exactly" % WITNESS})
    elif st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        X = sorted(p * N + q for p in range(N) for q in range(N)
                   if s.Value(x[p][q]))
        ok = verify(X, lines)
        print("  ==> FEASIBLE: %d leaves; verified against all 1600 tiles: %s"
              % (len(X), ok))
        if ok:
            print("      UPPER BOUND %d -> %d" % (WITNESS, len(X)))
        res.update({"witness": X, "witnessVerified": ok, "proved": ok,
                    "conclusion": "upper bound improves to %d" % len(X)})
    else:
        print("  ==> UNKNOWN in budget.  Nothing proved.")
        res.update({"proved": False, "conclusion": "undecided in budget",
                    "intervalUnchanged": [SHADOW_LOWER, WITNESS]})

    if "--write" in sys.argv:
        out = os.path.join(ROOT, "data", "tensor_close_at_114_two_sided.json")
        with open(out, "w") as fh:
            json.dump(res, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(out, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
