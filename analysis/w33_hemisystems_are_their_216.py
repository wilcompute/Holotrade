#!/usr/bin/env python3
"""
Their 216 hemisystem lines are our 432 hemisystems modulo complementation.
Two tracks converged on the same object from opposite directions.

WHAT EACH SIDE HAD, INDEPENDENTLY.

W33-Theory's w33_20260831 Schlaefli hemisystem bundle works inside the rank-15
integral trade lattice ker_Z(N). It takes the 45 projective minimum-vector
lines of norm 8, observes that their orthogonality graph is GQ(4,2) and hence
carries 27 maximal 5-cliques, and finds that five pairwise orthogonal minima
have every signed sum at norm 40 -- "exactly the norm of a centered W33
2-ovoid/hemisystem vector". That gives them 27 x 8 = 216 hemisystem lines.

On this side the same object arrived from the blocking problem.
gq_tight_case_is_an_m_ovoid.py showed the depth-2 tight case is a
{0,1,t+1}-weighting whose pure cases are an ovoid and a (t+1)-ovoid, which put
m-ovoids at the centre of the question; and analysis/w33_shape_catalogue.js
already carried the census, with W(3,3) admitting m-ovoids at exactly one set
size, 20, with 432 of them.

For W(3,3) a hemisystem is an m-ovoid with m = (t+1)/2 = 2, so "2-ovoid" and
"hemisystem" are the same word here, and 432 and 216 are one factor of two
apart. This file checks whether that factor is complementation, which is the
only candidate worth testing.

THE CHECK, done geometrically rather than by the graph condition.  Enumerate
every point set meeting EVERY line of W(3,3) in exactly two points. The
enumeration is exhaustive:

  * 432 of them, every one of size 20 -- independently reproducing the shape
    catalogue's census by a different definition;
  * the family is CLOSED under complementation, which it must be, since a line
    meeting T twice meets its complement 4 - 2 = 2 times;
  * no set is self-complementary, since 20 and 40 - 20 name different sets;
  * so the 432 fall into exactly 216 complementary PAIRS.

216 is their count. A centered hemisystem vector 1_T - (1/2) 1 negates exactly
when T is replaced by its complement, so a complementary pair is one
PROJECTIVE line -- which is what their 27 x 8 counts. The two numbers are the
same object counted with and without the sign.

WHY IT IS WORTH RECORDING.  Neither derivation used the other. Theirs is
lattice-theoretic, ours is a census of intriguing sets reached from a blocking
problem, and the objects meet exactly. It also puts a name on their 27 x 8
split from this side: the 27 is the GQ(2,4) carrier that
gq42_bridge_to_85_point_module.py already identified with their 45 minimum
lines' GQ(4,2), so the same 27/45 pair now carries both the Hermitian module
and the hemisystem bundle.

WHAT IS NOT CLAIMED.  That their eight-element fibres correspond to any
particular eight of our pairs, or that the bundle structure 27 x 8 is
reproduced here -- only the total count and the complementation mechanism are
checked. The fibre-level correspondence is theirs to certify and is not
touched. Nor does any of this bear on tau_2, which stays open in [111, 115].
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
    m = cp_model.CpModel()
    x = [m.NewBoolVar("") for _ in range(N)]
    for L in lines:
        m.Add(sum(x[p] for p in L) == 2)
    found = []

    class C(cp_model.CpSolverSolutionCallback):
        def __init__(self, v):
            super().__init__()
            self.v = v

        def on_solution_callback(self):
            found.append(frozenset(i for i in range(N) if self.Value(self.v[i])))

    s = cp_model.CpSolver()
    s.parameters.enumerate_all_solutions = True
    s.parameters.num_search_workers = 1
    s.parameters.max_time_in_seconds = 600.0
    st = s.Solve(m, C(x))

    full = frozenset(range(N))
    S = set(found)
    all20 = all(len(t) == 20 for t in found)
    closed = all(full - t in S for t in found)
    selfc = sum(1 for t in found if full - t == t)
    pairs = {frozenset([t, full - t]) for t in found}

    print("THEIR 216 IS OUR 432, MODULO COMPLEMENTATION")
    print("=" * 72)
    print("  geometric hemisystems of W(3,3) -- sets meeting EVERY line twice")
    print("     count %d (%s), all of size 20: %s"
          % (len(found), s.StatusName(st), all20))
    print("     closed under complementation: %s   self-complementary: %d"
          % (closed, selfc))
    print("     complementary PAIRS: %d" % len(pairs))
    print()
    print("  W33-Theory's Schlaefli hemisystem bundle counts 27 x 8 = 216")
    print("  hemisystem LINES. A centered hemisystem vector 1_T - (1/2)1")
    print("  negates under T -> complement, so a complementary pair is one")
    print("  projective line. The counts agree: %s"
          % ("MATCH" if len(pairs) == 216 else "MISMATCH"))
    print()
    print("  Independently derived on both sides -- theirs from the trade")
    print("  lattice's norm-8 minima, ours from the m-ovoid census that the")
    print("  depth-2 blocking problem forced. The 27 carrier is the GQ(2,4)")
    print("  already bridged to their 45 minimum lines' GQ(4,2).")
    print()
    print("  Not claimed: any fibre-level correspondence with their 8s, nor")
    print("  the 27 x 8 bundle structure. Only the count and the mechanism.")

    ok = (len(found) == 432 and all20 and closed and selfc == 0
          and len(pairs) == 216 and s.StatusName(st) == "OPTIMAL")

    if "--write" in sys.argv:
        out = os.path.join(ROOT, "data", "w33_hemisystems_are_their_216.json")
        with open(out, "w") as fh:
            json.dump({
                "schema": "holotrade.w33-hemisystems-216.v1",
                "valid": bool(ok),
                "definition": ("geometric: a set meeting every line of W(3,3) "
                               "in exactly two points; for W(3,3) this is both "
                               "the 2-ovoid and the hemisystem, since "
                               "(t+1)/2 = 2"),
                "count": len(found),
                "enumerationComplete": s.StatusName(st) == "OPTIMAL",
                "allSize20": all20,
                "closedUnderComplementation": closed,
                "selfComplementary": selfc,
                "complementaryPairs": len(pairs),
                "matchesTheir216": len(pairs) == 216,
                "theirSide": {
                    "source": "W33-Theory w33_20260831 Schlaefli hemisystem bundle",
                    "count": 216, "structure": "27 x 8 hemisystem lines",
                    "route": ("45 norm-8 trade-lattice minimum lines whose "
                              "orthogonality graph is GQ(4,2), 27 maximal "
                              "5-cliques, signed sums of five orthogonal "
                              "minima at norm 40"),
                },
                "ourSide": {
                    "route": ("the m-ovoid census forced by the depth-2 "
                              "blocking problem; w33_shape_catalogue.js "
                              "already records 432 at set size 20"),
                },
                "mechanism": ("a centered hemisystem vector 1_T - (1/2)1 "
                              "negates under complementation, so one "
                              "complementary pair is one projective line"),
                "notClaimed": ("no fibre-level correspondence with their "
                               "eights and no reproduction of the 27 x 8 "
                               "bundle structure; only the total count and "
                               "the complementation mechanism are checked"),
                "boundary": "bears on no bound; tau_2 stays open in [111, 115]",
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(out, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
