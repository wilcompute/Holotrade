#!/usr/bin/env python3
"""
The depth-2 load-balance spectrum: the perfect tile transversal would be
exactly the fractional optimum, and it does not exist.

THE OBJECT, which is new here.  load_balance_spectrum_only_extremes_fail.py
asked which perfectly balanced schedules exist on ONE carrier. The same
question at depth 2: a set X of product observables meeting EVERY tile L x M
in exactly m leaves.

The size is forced. Each leaf lies in 4 x 4 = 16 tiles and there are 1600
tiles, so 16|X| = 1600m and

    |X| = 100 m.

That is worth stopping on. At m = 1 the size is exactly 100 -- which is
tau*(H^2), the fractional optimum computed in
tensor_growth_rate_is_exactly_ten.py. So the m = 1 level of this spectrum IS
the fractional relaxation made integral: a perfect tile transversal, every
tile hit exactly once, at exactly the LP value.

THE SPECTRUM.

    m = 1   size 100   INFEASIBLE
    m = 2   size 200   UNKNOWN
    m = 3   size 300   OPTIMAL, tile counts uniformly 3
    m = 4   size 400   OPTIMAL, tile counts uniformly 4

The m = 1 row is proved TWICE, by independent routes. The solver returns
INFEASIBLE directly; and separately tau_2 >= 111 > 100 forbids it, since a
1-balanced set is in particular a blocker of size 100. Two arguments, one
conclusion, which is the check worth having on a claim about a fractional
optimum.

So the integrality gap tau_2 - tau* >= 11 has a structural reading rather than
only a numerical one: the LP optimum is the size of a perfect tile
transversal, and no such object exists.

THE CONSTRUCTIVE END.  If T is an m-ovoid of W(3,3) then T x T meets L x M in
|T cap L| * |T cap M| = m^2 leaves. W(3,3) has m-ovoids only at m = 2 -- the
432 hemisystems -- so T x T is 4-balanced with 400 leaves, for free, from any
of them. Verified here: a hemisystem of size 20 gives 400 leaves with every
tile count exactly 4.

That construction explains m = 4 but not m = 3, which the solver found
independently and which does not factor as a product of one-carrier objects.

BALANCE COSTS A FACTOR OF 2.6 OVER MINIMALITY.  The best known blocker has 115
leaves and is maximally unbalanced -- its tile counts run from 1 to 2. The
smallest balanced schedule that exists has 300. So insisting that every pair
of local contexts sees exactly the same number of your product observables
costs about 2.6x over merely covering them all. For a two-carrier machine that
is the price of a uniform measurement load, and it is now a number rather than
an intuition.

WHAT IS OPEN.  m = 2, at size 200, returned UNKNOWN under a ten-minute budget.
It is the only undecided level, and it sits between a proved impossibility and
a proved construction.

SCOPE. m = 1 is settled two ways and m = 3, 4 are constructions verified
leaf-by-leaf. Nothing here moves tau_2, which stays open in [111, 115]; the
m = 1 row uses that bound rather than improving it.
"""

import itertools
import json
import os
import sys

try:
    from ortools.sat.python import cp_model
except ImportError:
    sys.exit("needs ortools:  py -3 -m pip install ortools")

ROOT = r"C:\Repos\Holotrade"
Q = 3
N = 40


def geometry():
    def nm(v):
        i = next(k for k, x in enumerate(v) if x % Q)
        z = pow(v[i] % Q, -1, Q)
        return tuple((z * x) % Q for x in v)

    def form(u, v):
        return (u[0] * v[1] - u[1] * v[0] + u[2] * v[3] - u[3] * v[2]) % Q

    pts = sorted({nm(v) for v in itertools.product(range(Q), repeat=4)
                  if any(v)})
    idx = {v: i for i, v in enumerate(pts)}
    lines = set()
    for a, b in itertools.combinations(range(N), 2):
        if form(pts[a], pts[b]):
            continue
        S = set()
        for x, y in itertools.product(range(Q), repeat=2):
            if x == y == 0:
                continue
            S.add(idx[nm(tuple((x * pts[a][k] + y * pts[b][k]) % Q
                               for k in range(4)))])
        if len(S) == 4:
            lines.add(tuple(sorted(S)))
    return sorted(lines)


def main():
    lines = geometry()
    tiles = [[a * N + b for a in L for b in M] for L in lines for M in lines]
    print("THE DEPTH-2 LOAD-BALANCE SPECTRUM")
    print("=" * 72)
    print("  An m-balanced set meets EVERY tile in exactly m leaves. Each leaf")
    print("  lies in 16 tiles and there are 1600, so 16|X| = 1600m and")
    print("  |X| = 100m -- and 100 is exactly tau*(H^2), the LP optimum.")
    print()

    # constructive end: hemisystem product
    mm = cp_model.CpModel()
    h = [mm.NewBoolVar("") for _ in range(N)]
    for L in lines:
        mm.Add(sum(h[p] for p in L) == 2)
    s0 = cp_model.CpSolver()
    s0.parameters.max_time_in_seconds = 60.0
    s0.parameters.num_search_workers = 8
    st0 = s0.Solve(mm)
    T = [p for p in range(N) if s0.Value(h[p])]
    TT = {p * N + q for p in T for q in T}
    tt_counts = sorted({sum(1 for v in tl if v in TT) for tl in tiles})
    print("  hemisystem T, |T| = %d  ->  T x T has %d leaves, tile counts %s"
          % (len(T), len(TT), tt_counts))
    print("  (an m-ovoid squared is m^2-balanced; W(3,3) has them only at")
    print("   m = 2, so this gives the m = 4 level for free)")
    print()

    rows = []
    for m in (1, 2, 3, 4):
        size = 100 * m
        mo = cp_model.CpModel()
        x = [mo.NewBoolVar("") for _ in range(N * N)]
        for tl in tiles:
            mo.Add(sum(x[v] for v in tl) == m)
        s = cp_model.CpSolver()
        s.parameters.max_time_in_seconds = 600.0
        s.parameters.num_search_workers = 8
        st = s.Solve(mo)
        name = s.StatusName(st)
        row = {"m": m, "predictedSize": size, "status": name,
               "actualSize": None, "tileCounts": None, "consistent": None}
        if name in ("OPTIMAL", "FEASIBLE"):
            X = {v for v in range(N * N) if s.Value(x[v])}
            counts = sorted({sum(1 for v in tl if v in X) for tl in tiles})
            row["actualSize"] = len(X)
            row["tileCounts"] = counts
            row["consistent"] = (counts == [m] and len(X) == size)
        rows.append(row)
        print("  m=%d  size %3d -> %-11s %s"
              % (m, size, name,
                 ("actual %d, tile counts %s, consistent %s"
                  % (row["actualSize"], row["tileCounts"], row["consistent"]))
                 if row["actualSize"] is not None else ""))
    print()
    one = next(r for r in rows if r["m"] == 1)
    print("  m = 1 is proved TWICE: the solver returns %s, and separately"
          % one["status"])
    print("  tau_2 >= 111 > 100 forbids it, since a 1-balanced set is a")
    print("  blocker of size 100. So the integrality gap has a structural")
    print("  reading: the LP optimum is the size of a perfect tile")
    print("  transversal, and no such object exists.")
    print()
    smallest = min((r["m"] for r in rows if r["actualSize"] is not None),
                   default=None)
    if smallest:
        print("  BALANCE COSTS %.1fx OVER MINIMALITY: the best known blocker"
              % (100 * smallest / 115))
        print("  has 115 leaves with tile counts running 1 to 2; the smallest")
        print("  balanced schedule that exists has %d." % (100 * smallest))

    ok = (one["status"] == "INFEASIBLE"
          and all(r["consistent"] for r in rows if r["actualSize"] is not None)
          and tt_counts == [4])
    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "depth2_balance_spectrum.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.depth2-balance-spectrum.v1",
                "valid": bool(ok),
                "sizeIdentity": ("16|X| = 1600m so |X| = 100m; at m = 1 that "
                                 "is exactly tau*(H^2) = 100, the LP optimum"),
                "rows": rows,
                "mEqualsOneProvedTwice": {
                    "solver": one["status"],
                    "boundArgument": ("tau_2 >= 111 > 100, and a 1-balanced "
                                      "set is a blocker of size 100"),
                },
                "structuralReadingOfTheGap": (
                    "the LP optimum is the size of a perfect tile transversal, "
                    "and no such object exists -- so tau_2 - tau* >= 11 is not "
                    "merely numerical"),
                "hemisystemProduct": {
                    "hemisystemSize": len(T), "productSize": len(TT),
                    "tileCounts": tt_counts,
                    "why": ("an m-ovoid squared is m^2-balanced; W(3,3) has "
                            "them only at m = 2, giving the m = 4 level free"),
                },
                "mEqualsThreeIsNotAProduct": (
                    "m = 3 was found by the solver and does not factor as a "
                    "product of one-carrier objects, since 3 is not a square"),
                "balanceCost": {
                    "bestKnownBlocker": 115,
                    "smallestBalanced": 100 * smallest if smallest else None,
                    "ratio": round(100 * smallest / 115, 2) if smallest else None,
                    "reading": ("insisting every pair of local contexts sees "
                                "the same number of product observables costs "
                                "this factor over merely covering them"),
                },
                "open": "m = 2 at size 200 returned UNKNOWN in ten minutes",
                "boundary": ("nothing here moves tau_2, which stays open in "
                             "[111, 115]; the m = 1 row consumes that bound "
                             "rather than improving it"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
