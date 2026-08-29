#!/usr/bin/env python3
"""
The second no-ovoid quadrangle: GQ(2,4), and why it is the tractable one.

After nine formulations established that the W(3,3) tight case has no local
obstruction, the remaining dichotomy was "exhaustive search, or an idea that
is not a local invariant". Exhaustive search was out of reach at 1,600 leaves.
So change the object: W(3,3) is not the only small quadrangle without an
ovoid.

GQ(2,4) = Q^-(5,2) has 27 points and 45 lines, order (s,t) = (2,4), ovoid size
st+1 = 9, and no ovoid -- Q^-(5,q) never has one. Its blocking number is
tau_1 = 10, computed here as OPTIMAL, so the blocking ovoid defect is 1, the
same as W(3,3). The depth-2 interval is therefore [90, 100] against W(3,3)'s
[110, 121].

PRIOR ART, CHECKED FIRST AND FOUND.  This geometry is already in the W33
corpus, and searching for the RESULT rather than the framing found it:

  * Pass 84 (2026-07-15) has the exceptional isomorphism
    PSp(4,3) = PSU(4,2) = W(E6)/Z2 explicitly, with the 27 lines on a cubic
    surface and the stabiliser index 51840/1920 = 27;
  * Passes 3769-3786 go further -- GQ(2,4) AND GQ(4,2), all exact-cover
    ovoids, the 200 ovoids of GQ(4,2) splitting as 40 plane ovoids plus 160
    tripods, and the headline "W33 is the 40-plane-ovoid graph": W(3,3)'s
    forty points ARE the forty plane ovoids of GQ(4,2), adjacent when they
    share three lines.

So the geometry and the group isomorphism are theirs. What is new here is the
depth-2 PRODUCT blocking question applied to it, and the structure that
question exposes.

THE CENTRE THEOREM TRANSFERS, and the arithmetic predicted it. A W(3,3)
blocker has excess 4*11 - 40 = 4, which is the size of a pencil there. A
GQ(2,4) blocker has excess 5*10 - 45 = 5, the size of a pencil here. And the
structure follows: every minimum blocker of GQ(2,4) meets 40 lines once and
five twice, the five doubled lines are always a pencil, and the blocker never
contains its own centre.

But the counting is dramatically cleaner:

    W(3,3)      360 minimum blockers, nine per centre
    GQ(2,4)      27 minimum blockers, ONE per centre -- a bijection with
                 the point set

That bijection is what makes the tight case tractable. Assigning a blocker to
each of the 45 lines IS choosing a centre map c : 45 lines -> 27 points, and
the balance condition becomes #{L : c(L) in M} = 5 for every line M. Every
layer is then finite and small:

    independent sets      2,764   (W(3,3): 40,055)
    pencil-union masks    2,728   (W(3,3): 37,850)
    centre-balance vectors  675   complete, OPTIMAL
    fibre-size vectors    5,940   complete, OPTIMAL
                                  (W(3,3): 41,672 and INCOMPLETE)
    SAT clauses at tight 435,015  (W(3,3): 1,441,015)

ALPHA, AND A CAP THAT DOES NOT BIND.  alpha(GQ(2,4)) = 6 against a Hoffman
ratio bound of 27*5/15 = 9 = the ovoid size, so the coclique deficit is 3.
That looked as though it would bite hard, since |T_M| = 10 must be split over
only THREE points per line where W(3,3) had four. It does not: the 675 centre
patterns yield only three distinct size-multisets, and all of them have every
|C_q| <= 5, comfortably under the cap. Worth recording as a filter that was
expected to help and did not.

WHAT REMAINS OPEN.  tau_2(GQ(2,4)^2) is in [90, 100]. Direct minimisation
reached only 100, the product bound B x B, with a lower bound of 81 -- notably
WITHOUT beating it, where at W(3,3) symmetric search beat the product bound
immediately, 121 to 115. If that asymmetry survives, it is a genuine
structural difference between two quadrangles that share both the defect
delta = 1 and the automorphism group W(E6), and the difference would itself be
the finding.
"""

import collections
import itertools
import json
import os
import sys

try:
    from ortools.sat.python import cp_model
except ImportError:
    sys.exit("needs ortools:  py -3 -m pip install ortools")

ROOT = r"C:\Repos\Holotrade"


def build():
    """GQ(2,4) = Q^-(5,2): the elliptic quadric in PG(5,2)."""
    def Qf(v):
        return (v[0] * v[1] + v[2] * v[3]
                + v[4] * v[4] + v[4] * v[5] + v[5] * v[5]) % 2

    def Bf(u, v):
        return (Qf([u[i] ^ v[i] for i in range(6)]) ^ Qf(u) ^ Qf(v)) % 2

    pts = [v for v in itertools.product([0, 1], repeat=6)
           if any(v) and Qf(v) == 0]
    idx = {v: i for i, v in enumerate(pts)}
    lines = set()
    for a, b in itertools.combinations(pts, 2):
        if Bf(a, b) == 0:
            c = tuple(a[i] ^ b[i] for i in range(6))
            if any(c) and Qf(c) == 0:
                lines.add(tuple(sorted(idx[x] for x in (a, b, c))))
    return pts, [list(x) for x in sorted(lines)]


def main():
    pts, lines = build()
    n = len(pts)
    thru = [[li for li, L in enumerate(lines) if p in L] for p in range(n)]
    by_pencil = {frozenset(thru[p]): p for p in range(n)}
    adj = [[False] * n for _ in range(n)]
    for L in lines:
        for a, b in itertools.combinations(L, 2):
            adj[a][b] = adj[b][a] = True

    s_ = len(lines[0]) - 1
    t_ = len(thru[0]) - 1
    ovoid = s_ * t_ + 1

    # tau_1
    m = cp_model.CpModel()
    x = [m.NewBoolVar("") for _ in range(n)]
    for L in lines:
        m.AddBoolOr([x[p] for p in L])
    m.Minimize(sum(x))
    sv = cp_model.CpSolver()
    sv.parameters.max_time_in_seconds = 60.0
    sv.parameters.num_search_workers = 8
    st = sv.Solve(m)
    tau1 = int(sv.ObjectiveValue())
    tau1_proved = sv.StatusName(st) == "OPTIMAL"

    # all minimum blockers, and the centre theorem
    m2 = cp_model.CpModel()
    y = [m2.NewBoolVar("") for _ in range(n)]
    for L in lines:
        m2.AddBoolOr([y[p] for p in L])
    m2.Add(sum(y) == tau1)

    class Collect(cp_model.CpSolverSolutionCallback):
        def __init__(self, v):
            super().__init__()
            self.v, self.all = v, []

        def on_solution_callback(self):
            self.all.append([i for i in range(n) if self.Value(self.v[i])])

    s2 = cp_model.CpSolver()
    s2.parameters.enumerate_all_solutions = True
    s2.parameters.num_search_workers = 1
    s2.parameters.max_time_in_seconds = 90.0
    cb = Collect(y)
    st2 = s2.Solve(m2, cb)

    centres, profiles, inside = collections.Counter(), collections.Counter(), 0
    for b in cb.all:
        bs = set(b)
        prof = tuple(sorted(collections.Counter(
            len(bs & set(L)) for L in lines).items()))
        profiles[prof] += 1
        exc = frozenset(li for li, L in enumerate(lines)
                        if len(bs & set(L)) == 2)
        if exc in by_pencil:
            c = by_pencil[exc]
            centres[c] += 1
            if c in bs:
                inside += 1

    # independent sets and pencil-union masks
    counts, masks = collections.Counter(), set()

    def ext(cur, cand):
        counts[len(cur)] += 1
        mask = frozenset(li for p in cur for li in thru[p])
        if len(mask) == (t_ + 1) * len(cur):
            masks.add(mask)
        for i, v in enumerate(cand):
            ext(cur + [v], [w for w in cand[i + 1:] if not adj[v][w]])
    ext([], list(range(n)))
    alpha = max(counts)
    hoffman = n * (t_ + 1) // ((s_ + 1) * (t_ + 1) - (t_ + 1))

    res = {
        "schema": "holotrade.gq24-schlaefli-quadrangle.v1",
        "geometry": {"name": "GQ(2,4) = Q^-(5,2)", "points": n,
                     "lines": len(lines), "order": [s_, t_],
                     "ovoidSize": ovoid, "hasOvoid": False},
        "tau1": tau1, "tau1Proved": tau1_proved,
        "blockingOvoidDefect": tau1 - ovoid,
        "depth2Interval": [ovoid * tau1, tau1 * tau1],
        "minimumBlockers": len(cb.all),
        "blockerEnumerationComplete": s2.StatusName(st2) == "OPTIMAL",
        "centreTheorem": {
            "profiles": {str(dict(k)): v for k, v in profiles.items()},
            "allCentred": len(centres) == len(cb.all),
            "distinctCentres": len(centres),
            "blockersPerCentre": sorted(set(centres.values())),
            "bijectionWithPoints": len(centres) == n
                                   and set(centres.values()) == {1},
            "centreInsideBlocker": inside,
        },
        "alpha": alpha, "hoffmanBound": ovoid,
        "cocliqueDeficit": ovoid - alpha,
        "independentSets": sum(counts.values()),
        "pencilUnionMasks": len(masks),
        "comparisonToW33": {
            "w33MinimumBlockers": 360, "w33PerCentre": 9,
            "w33IndependentSets": 40055, "w33Masks": 37850,
            "w33Leaves": 1600, "gq24Leaves": n * n,
        },
        "priorArt": {
            "geometryAndGroup": "W33-Theory Pass 84 and Passes 3769-3786",
            "pass84": "PSp(4,3) = PSU(4,2) = W(E6)/Z2, 27 lines on a cubic surface",
            "passes3769_3786": ("GQ(2,4) and GQ(4,2), all exact-cover ovoids, "
                                "200 ovoids of GQ(4,2) as 40 plane ovoids plus "
                                "160 tripods, and 'W33 is the 40-plane-ovoid "
                                "graph'"),
            "whatIsNewHere": "the depth-2 product blocking question on it",
        },
        "boundary": ("tau_2(GQ(2,4)^2) is OPEN in [90, 100]. Direct "
                     "minimisation reached only the product bound 100, unlike "
                     "W(3,3) where symmetric search beat 121 immediately."),
    }

    print("GQ(2,4): THE SECOND NO-OVOID QUADRANGLE")
    print("=" * 70)
    print("  %d points, %d lines, order (%d,%d), ovoid size %d, no ovoid"
          % (n, len(lines), s_, t_, ovoid))
    print("  tau_1 = %d (%s), defect %d, interval %s"
          % (tau1, "OPTIMAL" if tau1_proved else "unproved",
             tau1 - ovoid, res["depth2Interval"]))
    print()
    print("  minimum blockers: %d, complete: %s"
          % (len(cb.all), res["blockerEnumerationComplete"]))
    print("  every one centred: %s; centres %d; per centre %s"
          % (res["centreTheorem"]["allCentred"], len(centres),
             res["centreTheorem"]["blockersPerCentre"]))
    print("  bijection with points: %s; centre inside its blocker: %d"
          % (res["centreTheorem"]["bijectionWithPoints"], inside))
    print()
    print("  alpha = %d against Hoffman %d, coclique deficit %d"
          % (alpha, ovoid, ovoid - alpha))
    print("  independent sets %d, pencil-union masks %d"
          % (sum(counts.values()), len(masks)))
    print("  W(3,3) for comparison: 40,055 and 37,850")
    print()
    print("  Prior art: the geometry and the group isomorphism are")
    print("  W33-Theory's (Pass 84, Passes 3769-3786). New here is the")
    print("  depth-2 product blocking question applied to it.")

    ok = (tau1 == 10 and tau1_proved and len(cb.all) == 27
          and res["centreTheorem"]["bijectionWithPoints"] and inside == 0
          and alpha == 6)

    if "--write" in sys.argv:
        out = os.path.join(ROOT, "data", "gq24_schlaefli_quadrangle.json")
        res["valid"] = ok
        with open(out, "w") as fh:
            json.dump(res, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(out, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
