#!/usr/bin/env python3
"""
Attack the depth-2 lower bound: what tightness at 110 actually forces.

Every previous run pushed on the UPPER bound (121 -> 116).  The lower bound
has sat at 110 since it was first derived, and nothing has tested whether it
is attainable.  This script derives the full consequence of tightness and
hands the resulting system to CP-SAT.

THE DOUBLE COUNT, AND WHERE ITS SLACK IS.  Write X_p = {q : (p,q) in X} for
the fibre over point p, and S_L = union of X_p over p in L for the shadow of
X over line L.  Blocking every tile L x M means S_L meets every line, so
|S_L| >= tau_1 = 11.  Then

    4|X|  =  sum over L of sum over p in L of |X_p|      (each p is on 4 lines)
          >= sum over L of |S_L|                          (union <= sum)
          >= 40 * 11  =  440,

so |X| >= 110.  There are exactly two inequalities.  At |X| = 110 BOTH are
equalities simultaneously, for every one of the 40 lines:

    (T1)  the four fibres X_p, p in L, are PAIRWISE DISJOINT;
    (T2)  S_L is a MINIMUM line blocker -- one of the exactly 360 such sets.

THE STEP THAT IS NEW HERE.  The blocking condition is symmetric: X blocks
every tile iff its transpose does, and |X| = |X^T|.  So (T1) and (T2) hold in
the transposed problem too.  Writing Y_q = {p : (p,q) in X} for the co-fibre,
(T1) transposed says the Y_q for q in M are pairwise disjoint, for every line
M.  Now suppose some fibre X_p contained two points q1, q2 of a common line M.
Then p lies in Y_q1 and in Y_q2, two sets that transposed-(T1) says are
disjoint.  Contradiction.  Therefore

    every fibre X_p meets every line at most once,

i.e. every X_p is an INDEPENDENT SET of W(3,3), and symmetrically so is every
co-fibre Y_q.  Since alpha(W(3,3)) = 7 (Hoffman gives 10; the true value is 7,
which is why W(3,3) has no ovoid), every row and every column of the 40 x 40
incidence matrix of X has at most 7 entries and is a partial ovoid.

That is a far tighter system than "row sums are 11 on each line", which is all
the earlier tight-case model encoded -- and that model ran 1,500 s and
returned UNKNOWN.  Here every row and every column carries 40 at-most-one
constraints, one per line, and each line's shadow is pinned to an explicit
table of 360 sets rather than to the predicate "blocks and has size 11".

WHAT THE ANSWER MEANS.

    INFEASIBLE  ->  110 is unattainable and the LOWER bound rises to 111.
                    Combined with the 115 construction: tau_2 in [111, 115].
    FEASIBLE    ->  tau_2 = 110 exactly and the interval CLOSES, because the
                    solution is a 110-leaf blocker and 110 is already proved
                    to be a lower bound.
    UNKNOWN     ->  nothing; the bounds stand where they are.

Either of the first two closes or narrows a gap that has been open since the
bound was written down.  All three outcomes are reported honestly.
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
TIGHT = 110
ALPHA = 7


def load():
    """Lines of W(3,3) and the complete list of minimum line blockers."""
    out = subprocess.run(
        ["node", "-e",
         "global.window=global;"
         "const S=require('./js/substrate.js');"
         "const R=require('./analysis/tensor_blocking_reformulation.js');"
         "const mb=R.minimumBlockers();"
         "process.stdout.write(JSON.stringify({"
         "lines:S.LINES.map(l=>[...l].sort((a,b)=>a-b)),"
         "blockers:mb.map(b=>[...b].sort((a,b)=>a-b))}));"],
        cwd=ROOT, capture_output=True, text=True)
    if out.returncode:
        sys.exit("node failed: " + out.stderr[:600])
    d = json.loads(out.stdout)
    return d["lines"], d["blockers"]


def build(lines, blockers, target):
    m = cp_model.CpModel()
    x = [[m.NewBoolVar("x%d_%d" % (p, q)) for q in range(N)] for p in range(N)]

    # (T2) each line's shadow is one of the 360 minimum blockers: pick which.
    sel = [[m.NewBoolVar("b%d_%d" % (li, bi)) for bi in range(len(blockers))]
           for li in range(len(lines))]
    for li in range(len(lines)):
        m.AddExactlyOne(sel[li])

    # Channelling + (T1): for line L and point q,
    #   sum over p in L of x[p][q]  ==  1 if q is in the chosen blocker else 0.
    # The "== 1" half is (T2); the "<= 1" half is (T1) pairwise disjointness.
    inblk = [[q in set(b) for q in range(N)] for b in blockers]
    for li, L in enumerate(lines):
        for q in range(N):
            lhs = sum(x[p][q] for p in L)
            ind = sum(sel[li][bi] for bi in range(len(blockers)) if inblk[bi][q])
            m.Add(lhs == ind)

    # Every fibre X_p is an independent set: at most one point per line.
    for p in range(N):
        for M in lines:
            m.AddAtMostOne([x[p][q] for q in M])
        m.Add(sum(x[p][q] for q in range(N)) <= ALPHA)

    # Every co-fibre Y_q is an independent set (the transposed statement).
    for q in range(N):
        for L in lines:
            m.AddAtMostOne([x[p][q] for p in L])
        m.Add(sum(x[p][q] for p in range(N)) <= ALPHA)

    m.Add(sum(x[p][q] for p in range(N) for q in range(N)) == target)

    # Symmetry break: Aut(W33) is transitive on points, so some fibre may be
    # assumed non-empty at the lowest-indexed occupied row.
    m.Add(sum(x[0][q] for q in range(N)) >= 1)
    return m, x, sel


def verify(X, lines):
    S = set(X)
    return all(any((p * N + q) in S for p in A for q in B)
               for A in lines for B in lines)


def main():
    seconds = (float(sys.argv[sys.argv.index("--seconds") + 1])
               if "--seconds" in sys.argv else 900.0)
    target = (int(sys.argv[sys.argv.index("--target") + 1])
              if "--target" in sys.argv else TIGHT)

    lines, blockers = load()
    print("IS THE DEPTH-2 LOWER BOUND OF 110 ATTAINABLE?")
    print("=" * 72)
    print("  minimum line blockers available : %d" % len(blockers))
    print("  all of size tau_1               : %s"
          % all(len(b) == TAU1 for b in blockers))
    print("  alpha(W(3,3))                   : %d  (Hoffman bound is 10)" % ALPHA)
    print()
    print("  forced at |X| = %d, on every one of the 40 lines:" % TIGHT)
    print("    (T1) the four fibres over a line are pairwise disjoint")
    print("    (T2) their union is one of the %d minimum blockers" % len(blockers))
    print("    (T3) NEW: every fibre and every co-fibre is an independent set,")
    print("         because (T1) transposed forbids two co-fibres sharing a point")
    print()

    m, x, sel = build(lines, blockers, target)
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = seconds
    s.parameters.num_search_workers = 8
    s.parameters.log_search_progress = False
    print("  solving at |X| = %d with a %.0f s budget ..." % (target, seconds))
    st = s.Solve(m)
    name = s.StatusName(st)
    print("  status: %s   (%.1f s)" % (name, s.WallTime()))
    print()

    result = {
        "schema": "holotrade.tensor-tight-rows-and-columns.v1",
        "target": target,
        "status": name,
        "wallSeconds": round(s.WallTime(), 1),
        "minimumBlockersUsed": len(blockers),
        "alpha": ALPHA,
        "forced": {
            "T1_fibresDisjointOnEveryLine": True,
            "T2_shadowIsAMinimumBlocker": True,
            "T3_everyFibreAndCofibreIsIndependent": True,
        },
        "derivation": ("4|X| >= sum of shadows >= 440 has exactly two "
                       "inequalities; at 110 both are equalities on all 40 "
                       "lines, and transposing (T1) forces (T3)"),
    }

    if st == cp_model.INFEASIBLE:
        print("  ==> INFEASIBLE.  No blocker of size %d exists." % target)
        print("      The LOWER BOUND RISES: tau_2 >= %d." % (target + 1))
        print("      With the 115 construction, tau_2 in [%d, 115]." % (target + 1))
        result["conclusion"] = "lower bound rises to %d" % (target + 1)
        result["newLowerBound"] = target + 1
        result["proved"] = True
    elif st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        X = sorted(p * N + q for p in range(N) for q in range(N)
                   if s.Value(x[p][q]))
        ok = verify(X, lines)
        print("  ==> FEASIBLE: a %d-leaf blocker." % len(X))
        print("      independently verified against all 1600 tiles: %s" % ok)
        if ok and len(X) == target == TIGHT:
            print("      tau_2 = %d EXACTLY; the interval CLOSES." % TIGHT)
            result["conclusion"] = "tau_2 = %d exactly" % TIGHT
            result["exactTau"] = TIGHT
        else:
            result["conclusion"] = "feasible but not the tight case"
        result["witness"] = X
        result["witnessVerified"] = ok
        result["proved"] = ok
    else:
        print("  ==> UNKNOWN within the budget.  Nothing is proved either way;")
        print("      tau_2 stays in [110, 115] exactly as before.")
        result["conclusion"] = "undecided in budget"
        result["proved"] = False

    if "--write" in sys.argv:
        out = os.path.join(ROOT, "data", "tensor_tight_rows_and_columns.json")
        with open(out, "w") as fh:
            json.dump(result, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(out, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
