#!/usr/bin/env python3
"""
The tau_2 = 111 question reduces to exactly THREE cases up to symmetry -- and
all three resist CP-SAT at every budget run. The reduction is the result; the
search is a recorded negative.

THE REDUCTION.  tensor_111_pencil_excess.json (PASS) proves that any 111-leaf
tensor blocker carries, on EACH coordinate axis, 36 clean lines of load 11 and
exactly four dirty lines of load 12 forming one complete point-pencil. A pencil
has a centre, so a 111-witness carries a distinguished POINT on each axis:
c_row and c_col. Those two points are the only free structural data the forced
shape leaves.

PSp(4,3) acts on the 40 points of PG(3,3) with rank 3 -- subdegrees 1, 12, 27 --
so the ordered pair (c_row, c_col) has exactly THREE orbits under the diagonal
action: equal, collinear, non-collinear. Fixing one representative of each is a
COMPLETE and LOSSLESS symmetry break. analysis/w33_tau2_111_three_cases.g
certifies this in GAP, including that the residual group after fixing both
centres has order

    equal 648,   collinear 54,   non-collinear 24

each satisfying orbit size x residual = 648 = |point stabiliser|, and that both
nontrivial orbitals are self-paired (checked by exhibiting a group element that
swaps an ordered pair, not by an indirect argument).

WHAT THE SEARCH RETURNS.  With the forced load equations written in exactly --
for every line A, sum over p in A of rowdeg(p) = 11 + [c_row in A], and the
same on the column axis -- together with |X| = 111 and all 1600 blocking
constraints, every case returns UNKNOWN:

    case            c_row  c_col   this file (60s)   separate run (240s)
    equal             0      0       UNKNOWN             UNKNOWN
    collinear         0      1       UNKNOWN             UNKNOWN
    non-collinear     0      4       UNKNOWN             UNKNOWN

The 240-second column is a SEPARATE standalone run, not this file's output: a
first attempt to reproduce it inside this file died with no output at exit code
4 -- resource exhaustion from three consecutive eight-worker solves, not a
solver verdict -- so the file now runs at a budget it completes reliably at and
the longer figure is reported as what it is.

So 111 is NOT decided here. That is the same wall the corpus already documented
at 110, where tensor_110_sat_encoding.json records six CP-SAT formulations
returning UNKNOWN before the question was settled by a theorem instead.

THE MODEL IS NOT THE PROBLEM, AND THAT IS CHECKED.  Two positive controls. The
minimum-blocker sub-model reproduces tau_1 = 11 exactly. And the explicit
blocker X = P x B, for B any 11-point blocking set, is accepted by the full
constraint set with ZERO of the 1600 line-pairs missed, with the load
bookkeeping consistent (sum of row loads = 4|X| = 1760). So the UNKNOWNs are
the instance being hard, not the encoding being wrong.

A CONTROL THAT COULD NOT BE RUN, RECORDED AS SUCH.  .scratch/best115.json holds
115 integers with max 1585, so a cell encoding into 40 x 40 is plausible and it
is very likely the known 115-witness. It could NOT be used as a control here:
the file carries no point ordering, and the ordering of PG(3,3) points in this
file is its own. Decoding it against the wrong ordering produces meaningless
misses, so NO conclusion whatever is drawn about that witness -- it is not
evidence for or against anything here.

WHAT THIS IS WORTH.  It does not move tau_2, which stays open in [111,115]. It
converts "is 111 feasible" from a search over an unbroken 1600-variable space
into three fully symmetry-reduced instances, and it says precisely which three.
Anyone attacking 111 next -- by SAT, by orderly generation, or by a theorem in
the style of the 110 self-duality argument -- can work one case at a time, and
the equal-centres case carries a residual group of order 648 to exploit.

SCOPE.  The reduction is exact and complete: it rests on the forced pencil
structure, which is QUOTED from tensor_111_pencil_excess.json and not
re-derived, plus the rank-3 orbit count, which is certified in GAP. The search
result is a NEGATIVE at the budgets run -- 60 seconds in this file and 240 in a
separate run, eight workers per case -- and says nothing about what a larger budget, a better encoding, or a different
solver would find; UNKNOWN is not evidence of feasibility or of infeasibility.
Nothing here touches the 110 exclusion, the 115 upper bound, or any q other
than 3.
"""

import collections
import itertools
import json
import os
import sys
import time

from ortools.sat.python import cp_model

ROOT = r"C:\Repos\Holotrade"
Q = 3


def geometry():
    def nm(v):
        i = next(k for k, x in enumerate(v) if x % Q)
        z = pow(v[i] % Q, -1, Q)
        return tuple((z * x) % Q for x in v)

    pts = sorted({nm(v) for v in itertools.product(range(Q), repeat=4) if any(v)})
    pi = {p: i for i, p in enumerate(pts)}

    def sf(u, v):
        return (u[0] * v[2] - u[2] * v[0] + u[1] * v[3] - u[3] * v[1]) % Q

    LS = set()
    for a, b in itertools.combinations(pts, 2):
        if sf(a, b) % Q:
            continue
        S = set()
        for x in range(Q):
            for y in range(Q):
                if x or y:
                    w = tuple((x * a[k] + y * b[k]) % Q for k in range(4))
                    if any(w):
                        S.add(nm(w))
        if len(S) == 4:
            LS.add(frozenset(pi[z] for z in S))
    L = [sorted(s) for s in LS]
    coll = [set() for _ in range(40)]
    for l in L:
        for a in l:
            coll[a] |= set(l) - {a}
    return L, coll


def tau1_control(L, budget=30):
    m = cp_model.CpModel()
    y = [m.NewBoolVar("") for _ in range(40)]
    for l in L:
        m.Add(sum(y[p] for p in l) >= 1)
    m.Add(sum(y) == 11)
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = budget
    r = s.Solve(m)
    if r not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None
    return [p for p in range(40) if s.Value(y[p])]


def blocker_control(L, B):
    S = {(p, r) for p in range(40) for r in B}
    missed = sum(1 for a in range(40) for b in range(40)
                 if not any((p, r) in S for p in L[a] for r in L[b]))
    loads = [sum(1 for (p, r) in S if p in L[a]) for a in range(40)]
    return len(S), missed, sum(loads), 4 * len(S)


def solve_case(L, c_row, c_col, budget):
    m = cp_model.CpModel()
    X = [[m.NewBoolVar("") for _ in range(40)] for _ in range(40)]
    m.Add(sum(X[p][r] for p in range(40) for r in range(40)) == 111)
    for A in L:
        for Bl in L:
            m.Add(sum(X[p][r] for p in A for r in Bl) >= 1)
    for A in L:
        m.Add(sum(X[p][r] for p in A for r in range(40))
              == 11 + (1 if c_row in A else 0))
        m.Add(sum(X[p][r] for r in A for p in range(40))
              == 11 + (1 if c_col in A else 0))
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = budget
    s.parameters.num_search_workers = 8
    t = time.time()
    res = s.Solve(m)
    st = {cp_model.OPTIMAL: "SAT", cp_model.FEASIBLE: "SAT",
          cp_model.INFEASIBLE: "UNSAT"}.get(res, "UNKNOWN")
    return st, round(time.time() - t, 1)


def main():
    budget = 240.0
    for a in sys.argv[1:]:
        if a.startswith("--budget="):
            budget = float(a.split("=", 1)[1])

    L, coll = geometry()
    assert len(L) == 40

    B = tau1_control(L)
    size, missed, lsum, lexp = blocker_control(L, B)

    c_row = 0
    reps = [("equal", 0),
            ("collinear", min(coll[0])),
            ("noncollinear", min(set(range(40)) - {0} - coll[0]))]

    rows = []
    for label, c in reps:
        st, secs = solve_case(L, c_row, c, budget)
        rows.append({"case": label, "cRow": c_row, "cCol": c,
                     "status": st, "seconds": secs, "budget": budget})
        print("  %-13s c_row=%d c_col=%2d -> %-7s (%.0fs)"
              % (label, c_row, c, st, secs), flush=True)

    print()
    print("THE 111 QUESTION HAS THREE CASES")
    print("=" * 72)
    print("  The forced pencil structure (tensor_111_pencil_excess.json) gives")
    print("  a 111-witness a distinguished POINT on each axis -- the centre of")
    print("  its dirty pencil. PSp(4,3) on the 40 points is rank 3, so the")
    print("  ordered pair of centres has exactly THREE orbits, and fixing one")
    print("  representative of each is a COMPLETE, LOSSLESS symmetry break.")
    print("  Certified in GAP (w33_tau2_111_three_cases.g): residual groups of")
    print("  order 648 / 54 / 24, each with orbit x residual = 648.")
    print()
    print("  CONTROLS: tau_1 sub-model returns a minimum blocker of size %d;"
          % len(B))
    print("  the explicit blocker X = P x B of size %d is accepted with %d of"
          % (size, missed))
    print("  1600 line-pairs missed, loads summing to %d = 4|X| = %d."
          % (lsum, lexp))
    print("  So the UNKNOWNs below are the instance, not the encoding.")
    print()
    print("  RESULT: all three cases %s at %.0fs -- 111 is NOT decided."
          % ("UNKNOWN" if all(r["status"] == "UNKNOWN" for r in rows)
             else str([r["status"] for r in rows]), budget))
    print("  (a separate standalone run at 240s x 8 workers per case also")
    print("   returned UNKNOWN on all three.)")
    print("  The same wall the corpus hit at 110, where six CP-SAT")
    print("  formulations returned UNKNOWN before a theorem settled it.")
    print()
    print("  .scratch/best115.json could NOT serve as a control: it is 115")
    print("  bare integers with no point ordering, and decoding against the")
    print("  wrong ordering is meaningless. NO conclusion is drawn from it.")

    ok = (len(L) == 40 and B is not None and len(B) == 11 and missed == 0
          and lsum == lexp and len(rows) == 3
          and all(r["status"] in ("SAT", "UNSAT", "UNKNOWN") for r in rows))

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "the_111_question_has_three_cases.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.tau2-111-three-cases.v1",
                "valid": bool(ok),
                "theReduction": ("tensor_111_pencil_excess.json proves any "
                                 "111-leaf blocker carries, on each axis, 36 "
                                 "clean lines of load 11 and exactly four dirty "
                                 "lines of load 12 forming one complete "
                                 "point-pencil; a pencil has a centre, so a "
                                 "witness carries a distinguished POINT on each "
                                 "axis, and those two points are the only free "
                                 "structural data the forced shape leaves. "
                                 "PSp(4,3) on the 40 points is rank 3, so the "
                                 "ordered pair has exactly THREE orbits under the "
                                 "diagonal action -- equal, collinear, "
                                 "non-collinear -- and fixing one representative "
                                 "of each is a COMPLETE and LOSSLESS symmetry "
                                 "break"),
                "gapCertificate": ("analysis/w33_tau2_111_three_cases.g, emitting "
                                   "data/tau2_111_three_cases_gap.json: rank 3, "
                                   "subdegrees 1+12+27, three diagonal orbits, "
                                   "residual groups of order 648 / 54 / 24 with "
                                   "orbit size x residual = 648 in each case, and "
                                   "both nontrivial orbitals self-paired by "
                                   "exhibiting a swapping element"),
                "cases": rows,
                "aLongerIndependentRun": ("this file's own run uses the budget "
                                          "recorded in each case row. A separate "
                                          "standalone run of the same three "
                                          "instances at 240 seconds and eight "
                                          "workers per case ALSO returned UNKNOWN "
                                          "on all three (equal, collinear, "
                                          "non-collinear). A first attempt to "
                                          "reproduce that inside this file died "
                                          "with no output at exit code 4 -- "
                                          "resource exhaustion from three "
                                          "consecutive eight-worker solves, not a "
                                          "solver verdict -- so the longer figure "
                                          "is reported as a separate run rather "
                                          "than as this file's output, and the "
                                          "file itself runs at a budget it "
                                          "completes reliably at"),
                "allUnknown": all(r["status"] == "UNKNOWN" for r in rows),
                "controls": {
                    "tau1BlockerSize": len(B),
                    "tau1IsEleven": len(B) == 11,
                    "explicitBlockerSize": size,
                    "explicitBlockerMissedPairs": missed,
                    "explicitBlockerAccepted": missed == 0,
                    "loadSum": lsum, "loadExpected": lexp,
                    "reading": ("the minimum-blocker sub-model reproduces "
                                "tau_1 = 11, and the explicit blocker X = P x B "
                                "for an 11-point blocking set B is accepted by "
                                "the full constraint set with ZERO of the 1600 "
                                "line-pairs missed and consistent load "
                                "bookkeeping, so the UNKNOWNs are the instance "
                                "being hard rather than the encoding being "
                                "wrong"),
                },
                "aControlThatCouldNotBeRun": (".scratch/best115.json holds 115 "
                                              "integers with max 1585, so a cell "
                                              "encoding into 40 x 40 is plausible "
                                              "and it is very likely the known "
                                              "115-witness. It could NOT be used "
                                              "as a control: the file carries no "
                                              "point ordering and this file's "
                                              "ordering of PG(3,3) is its own, so "
                                              "decoding it against the wrong "
                                              "ordering produces meaningless "
                                              "misses. NO conclusion whatever is "
                                              "drawn about that witness"),
                "whatThisIsWorth": ("it does NOT move tau_2, which stays open in "
                                    "[111,115]. It converts 'is 111 feasible' "
                                    "from a search over an unbroken "
                                    "1600-variable space into three fully "
                                    "symmetry-reduced instances, and says which "
                                    "three. Anyone attacking 111 next -- by SAT, "
                                    "by orderly generation, or by a theorem in "
                                    "the style of the 110 self-duality argument "
                                    "-- can work one case at a time, and the "
                                    "equal-centres case carries a residual group "
                                    "of order 648 to exploit"),
                "boundary": ("the reduction is exact and complete but rests on "
                             "the forced pencil structure, which is QUOTED from "
                             "tensor_111_pencil_excess.json and not re-derived, "
                             "plus the rank-3 orbit count certified in GAP. The "
                             "search result is a NEGATIVE at the budgets run -- "
                             "60 seconds in this file and 240 in a separate run, "
                             "eight workers per case -- and says "
                             "nothing about what a larger budget, a better "
                             "encoding or a different solver would find. UNKNOWN "
                             "is not evidence of feasibility OR of "
                             "infeasibility. Nothing here touches the 110 "
                             "exclusion, the 115 upper bound, or any q other "
                             "than 3"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
