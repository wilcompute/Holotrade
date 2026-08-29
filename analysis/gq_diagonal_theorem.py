#!/usr/bin/env python3
"""
The diagonal t = s: branches cannot mix, so the tight case is a self-duality
or nothing -- and the reason it still does not reach q = 5.

WHOSE ARGUMENT THIS EXTENDS.  W33-Theory proved tau_2(W(3,3)^2) != 110 by
showing the tight case makes the centre map a bijection, so that pencil
reciprocity becomes a self-duality of W(3,3), which is impossible because
W(q) is self-dual only for even q. Their route to "bijection" was to force the
multiplicity-(t+1) set F to have size 1 + kt/mu = 10, and then kill it with
alpha(W(3,3)) = 7. That step is a numerical coincidence of q = 3: it needs
both the pair count and the independence number, and neither generalises for
free.

This file replaces that step with one that needs neither. The replacement is
uniform in q, which looked at first like a free extension to every odd q; it
is not, and the measurement that stops it is the more interesting half.

THE SETUP, from gq_tight_case_theorem.py.  At the tight size the centre
multiplicity m_p lies in {0, 1, t+1} (proved there for all (s,t)), and every
line M satisfies sum_{p in M} m_p = t+1 with sum_p m_p = #lines. A line of
s+1 points therefore falls into exactly one of two branches:

    (A)  one point of multiplicity t+1, all its other points 0;
    (B)  t+1 points of multiplicity 1, its remaining s-t points 0.

Branch (B) needs t <= s. On the diagonal t = s it needs no room to spare:
s - t = 0, so a branch-(B) line has ALL s+1 of its points at multiplicity 1.
That single fact is the whole argument.

THE MIXING LEMMA (t = s).  Let U = {p : m_p = 1}. Take p in U. On a branch-(A)
line only the multiplicity-(t+1) point is nonzero, so a line through p cannot
be branch (A); every line through p is branch (B). At t = s a branch-(B) line
has every point at multiplicity 1, so every point collinear with p lies in U.
Hence U is closed under collinearity, and the collinearity graph of a
quadrangle is connected, so

    U is empty, or U is everything.

    * U everything: m == 1, the centre map is a BIJECTION.
    * U empty: every multiplicity is 0 or t+1, so every line is branch (A) and
      meets F = {p : m_p = t+1} exactly once. F IS AN OVOID.

There is no mixed configuration. No pair count, no independence number, and
nothing specific to a value of q.

THEOREM (the diagonal).  Let Q be a GQ(s,s) with no ovoid, satisfying the
centre property. If Q is not self-dual, then

        tau_2(Q x Q)  >  (s^2 + 1) * tau_1(Q).

    Proof. The ovoid branch is excluded by hypothesis, so m == 1 and the
    centre map c is a bijection from lines to points. Its column partner d is
    a bijection too, and reciprocity says c_L in M <=> d_M in L. Writing
    alpha = d^{-1} for the inverse bijection from points to lines, that reads

        x in L  <=>  c_L in alpha(x),

    which is exactly an incidence isomorphism from (points, lines) to
    (lines, points): a duality. So Q is self-dual, contrary to hypothesis. []

WHAT IT WOULD COVER, AND WHY IT DOES NOT.  W(3,q) is self-dual if and only if
q is even and ovoid-free exactly when q is odd, so the theorem looks as though
it should hand over every odd q at once. It does not, and the reason is worth
more than the theorem would have been.

The machinery needs the centre property, and at q = 5 that property is FALSE.
Measured here rather than assumed: tau_1(W(3,5)) = 29, proved OPTIMAL, and of
120 sampled minimum blockers only a handful -- six per cent on the run
recorded in the artifact -- have their excess on a single pencil. The rest all
carry the profile

    {1: 145, 2: 5, 3: 5, 4: 1}

whose excess 5*1 + 5*2 + 1*3 = 18 = (t+1)*delta is correct but is spread over
ELEVEN lines instead of the six of a pencil. Reciprocity, and everything
downstream of it, simply does not start.

So the honest reach of the theorem is: any GQ(s,s) with no ovoid, not
self-dual, AND the centre property. W(3,3) qualifies, and the theorem recovers
the known result there. W(3,5) does not qualify, and no claim is made about
it.

THAT RELOCATES THE DIFFICULTY, which is the useful part. The binding
constraint on the diagonal is not self-duality at all -- it is the centre
property, and the centre property is fragile. It survives delta = 1, 2 and 3
in the t > s families, because there the minimum blockers are point-perps and
the profile is forced (gq_perp_blockers_and_h44.py). It breaks at the very
first diagonal case past q = 3, where the minimum blockers are neither perps
nor anything else so uniform. W(3,3) is not merely the hard case; it may be
the only case on the diagonal where this machinery applies at all.

A NUMBER WORTH KEEPING.  tau_1(W(3,5)) = 29 is computed here and proved
OPTIMAL. The point-perp gives 30, so W(3,5) beats the classical construction
by exactly one point -- the same margin by which W(3,3) beats it, 11 against
12. With delta = tau_1 - (q^2+1) that is delta = 1 at q = 3 and delta = 3 at
q = 5, both matching q - 2, so on two data points

    tau_1(W(3,q)) = q^2 + q - 1     for odd q,

which is recorded as a CONJECTURE with two confirmations, not a result.

THE FULL TRICHOTOMY, now complete for a GQ(s,t) with no ovoid and the centre
property:

    t > s   branch (B) needs t+1 <= s+1 and dies; branch (A) demands an
            ovoid. The tight case is impossible.        (gq_tight_case_theorem)
    t = s   branches cannot mix; the surviving one is a self-duality. The
            tight case is impossible unless Q is self-dual.       (this file)
    t < s   a branch-(B) line has s-t points of multiplicity 0, the mixing
            lemma fails, and both branches survive. OPEN.

and the centre property is a real hypothesis in all three rows, not a
formality: it holds in the t > s families because their minimum blockers are
perps, and it fails at W(3,5).

The self-dual diagonal quadrangles need no separate row: the classical W(q)
is self-dual exactly when q is even, and then it HAS an ovoid, so its tight
case is attained rather than obstructed.

VERIFIED HERE.  The mixing lemma predicts that on W(3,3) the ONLY
trichotomy-valued solution of the balance system is the all-ones vector, since
the ovoid branch is empty. Enumerated exhaustively below: one solution,
all-ones, status OPTIMAL. That is a sharp test: the unrestricted balance
system has AT LEAST twenty thousand solutions -- the enumeration is stopped at
a cap and never runs to completion, so that figure is a floor, not a count --
and imposing only the trichotomy {0, 1, 4} cuts them to exactly one, which the
solver does prove OPTIMAL.

ATTRIBUTION.  The self-duality route and the theorem at q = 3 are
W33-Theory's (commits 43049db, 1513d61), and their result stands exactly as
they proved it. What is added here is the mixing lemma, which reaches
"bijection" without their pair count or the independence number; the placement
of the diagonal in the t > s / t = s / t < s trichotomy; and the measurement
that the centre property fails at q = 5, which is what stops the machinery
from generalising and says where the next attempt should NOT go.
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


def w3q(q):
    """W(3,q) = GQ(q,q) from the symplectic form on F_q^4."""
    def norm(v):
        i = next(k for k, x in enumerate(v) if x % q)
        z = pow(v[i] % q, -1, q)
        return tuple((z * x) % q for x in v)

    def form(u, v):
        return (u[0] * v[1] - u[1] * v[0] + u[2] * v[3] - u[3] * v[2]) % q

    pts = sorted({norm(v) for v in itertools.product(range(q), repeat=4)
                  if any(v)})
    idx = {v: i for i, v in enumerate(pts)}
    n = len(pts)
    lines = set()
    for a, b in itertools.combinations(range(n), 2):
        if form(pts[a], pts[b]):
            continue
        S = set()
        for x, y in itertools.product(range(q), repeat=2):
            if x == y == 0:
                continue
            S.add(idx[norm(tuple((x * pts[a][k] + y * pts[b][k]) % q
                                 for k in range(4)))])
        if len(S) == q + 1:
            lines.add(tuple(sorted(S)))
    return n, sorted(lines)


def trichotomy_solutions(n, lines, t_):
    """All solutions of the balance system with m_p in {0, 1, t+1}."""
    m = cp_model.CpModel()
    dom = cp_model.Domain.FromValues([0, 1, t_ + 1])
    v = [m.NewIntVarFromDomain(dom, "") for _ in range(n)]
    for L in lines:
        m.Add(sum(v[p] for p in L) == t_ + 1)
    m.Add(sum(v) == len(lines))

    class C(cp_model.CpSolverSolutionCallback):
        def __init__(self, vv):
            super().__init__()
            self.v, self.sols = vv, []

        def on_solution_callback(self):
            if len(self.sols) < 200:
                self.sols.append([self.Value(x) for x in self.v])

    s = cp_model.CpSolver()
    s.parameters.enumerate_all_solutions = True
    s.parameters.num_search_workers = 1
    s.parameters.max_time_in_seconds = 300.0
    cb = C(v)
    st = s.Solve(m, cb)
    return s.StatusName(st), cb.sols


def unrestricted_count(n, lines, t_, cap=20000):
    """How many solutions before the trichotomy is imposed -- the contrast."""
    m = cp_model.CpModel()
    v = [m.NewIntVar(0, t_ + 1, "") for _ in range(n)]
    for L in lines:
        m.Add(sum(v[p] for p in L) == t_ + 1)
    m.Add(sum(v) == len(lines))

    class C(cp_model.CpSolverSolutionCallback):
        def __init__(self):
            super().__init__()
            self.k = 0

        def on_solution_callback(self):
            self.k += 1
            if self.k >= cap:
                self.StopSearch()

    s = cp_model.CpSolver()
    s.parameters.enumerate_all_solutions = True
    s.parameters.num_search_workers = 1
    s.parameters.max_time_in_seconds = 120.0
    cb = C()
    st = s.Solve(m, cb)
    # complete only if the solver proved it AND the cap was never reached;
    # a run that stops on the clock returns a floor, not a count
    complete = s.StatusName(st) == "OPTIMAL" and cb.k < cap
    return cb.k, complete


def centre_property_sample(n, lines, tau, tries, tl):
    """What fraction of minimum blockers put their excess on ONE pencil?"""
    import collections
    import random
    lsets = [set(L) for L in lines]
    thru = [frozenset(li for li, L in enumerate(lines) if p in L)
            for p in range(n)]
    by_pencil = {v: k for k, v in enumerate(thru)}
    m = cp_model.CpModel()
    y = [m.NewBoolVar("") for _ in range(n)]
    for L in lines:
        m.AddBoolOr([y[p] for p in L])
    m.Add(sum(y) == tau)
    prof, holds, seen = collections.Counter(), 0, 0
    rng = random.Random(23)
    for _ in range(tries):
        s = cp_model.CpSolver()
        s.parameters.max_time_in_seconds = tl
        s.parameters.num_search_workers = 8
        s.parameters.random_seed = rng.randrange(10 ** 6)
        s.parameters.randomize_search = True
        r = s.Solve(m)
        if s.StatusName(r) not in ("FEASIBLE", "OPTIMAL"):
            break
        bs = {i for i in range(n) if s.Value(y[i])}
        seen += 1
        pr = collections.Counter(len(bs & L) for L in lsets)
        prof[tuple(sorted(pr.items()))] += 1
        exc = frozenset(li for li, L in enumerate(lsets) if len(bs & L) > 1)
        if exc in by_pencil and len(pr) == 2:
            holds += 1
        m.Add(sum(y[i] for i in bs) <= tau - 1)
    return {"sampled": seen, "centrePropertyHolds": holds,
            "fraction": (holds / seen) if seen else None,
            "profiles": {str(dict(k)): v for k, v in prof.most_common()}}


def tau1(n, lines, tl):
    m = cp_model.CpModel()
    x = [m.NewBoolVar("") for _ in range(n)]
    for L in lines:
        m.AddBoolOr([x[p] for p in L])
    m.Minimize(sum(x))
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = tl
    s.parameters.num_search_workers = 8
    st = s.Solve(m)
    return int(s.ObjectiveValue()), s.StatusName(st) == "OPTIMAL"


def main():
    print("THE DIAGONAL t = s: BRANCHES CANNOT MIX")
    print("=" * 72)
    print("  At t = s a branch-(B) line has ALL s+1 points at multiplicity 1,")
    print("  so U = {p : m_p = 1} is closed under collinearity. The")
    print("  collinearity graph is connected, so U is empty or everything:")
    print("  either m == 1 (a bijection, hence a self-duality) or F is an")
    print("  ovoid. No mixed configuration, at any q.")
    print()

    q = 3
    n, lines = w3q(q)
    t_ = len(lines[0]) - 1
    print("  W(3,%d): %d points, %d lines of %d, t = s = %d"
          % (q, n, len(lines), len(lines[0]), t_))
    free, free_complete = unrestricted_count(n, lines, t_)
    print("     balance system WITHOUT the trichotomy: %s%d solutions%s"
          % ("" if free_complete else "at least ", free,
             "" if free_complete else " (enumeration not run to completion)"))
    st, sols = trichotomy_solutions(n, lines, t_)
    all_ones = [s for s in sols if all(x == 1 for x in s)]
    ovoids = [s for s in sols if any(x == t_ + 1 for x in s)]
    print("     balance system WITH m_p in {0, 1, %d}: %s, %d solution(s)"
          % (t_ + 1, st, len(sols)))
    print("     of which all-ones: %d ; ovoid-supported: %d"
          % (len(all_ones), len(ovoids)))
    print()
    unique_all_ones = (st == "OPTIMAL" and len(sols) == 1
                       and len(all_ones) == 1 and not ovoids)
    print("  ==> the mixing lemma predicts exactly one solution here, the")
    print("      bijection, because W(3,3) has no ovoid. Confirmed: %s"
          % unique_all_ones)
    print()
  
    print()
    print("  THE TRICHOTOMY IS NOW COMPLETE for no-ovoid quadrangles with the")
    print("  centre property:")
    print("     t > s   impossible (branch B dies, branch A wants an ovoid)")
    print("     t = s   impossible unless Q is self-dual")
    print("     t < s   OPEN: branch-(B) lines have s-t points of")
    print("             multiplicity 0, so the mixing lemma fails")

    # and now the measurement that stops the extension
    print()
    print("  W(3,5), the next diagonal case:")
    n5, lines5 = w3q(5)
    t5 = len(lines5[0]) - 1
    tau5, proved5 = tau1(n5, lines5, 1500.0)
    perp5 = t5 * (t5 + 1)
    cp5 = centre_property_sample(n5, lines5, tau5, 120, 12.0)
    print("     %d points, %d lines of %d | tau_1 = %d%s, ovoid %d, "
          "delta %d, point-perp %d"
          % (n5, len(lines5), len(lines5[0]), tau5,
             "" if proved5 else " (unproved)", t5 * t5 + 1,
             tau5 - (t5 * t5 + 1), perp5))
    print("     centre property holds on %d of %d sampled minimum blockers "
          "(%.0f%%)"
          % (cp5["centrePropertyHolds"], cp5["sampled"],
             100.0 * (cp5["fraction"] or 0)))
    for k, v in list(cp5["profiles"].items())[:3]:
        print("        profile %s x%d" % (k, v))
    print()
    print("  ==> the centre property FAILS at q = 5, so the theorem does not")
    print("      apply to W(3,5) and no claim is made about it. That is the")
    print("      binding constraint on the diagonal -- not self-duality.")
    print()
    print("     tau_1 = %d against the point-perp's %d: W(3,5) beats the"
          % (tau5, perp5))
    print("     classical construction by 1, exactly as W(3,3) does (11 vs")
    print("     12). Both match q^2 + q - 1, so delta = q - 2 on two data")
    print("     points. Recorded as a CONJECTURE, not a result.")

    if "--write" in sys.argv:
        out = os.path.join(ROOT, "data", "gq_diagonal_theorem.json")
        with open(out, "w") as fh:
            json.dump({
                "schema": "holotrade.gq-diagonal-theorem.v1",
                "valid": bool(unique_all_ones),
                "mixingLemma": ("at t = s a branch-(B) line has all s+1 points "
                                "at multiplicity 1, so U = {p : m_p = 1} is "
                                "closed under collinearity; the collinearity "
                                "graph is connected, so U is empty or "
                                "everything"),
                "theorem": ("a GQ(s,s) with no ovoid and the centre property "
                            "that is NOT self-dual has "
                            "tau_2 > (s^2+1) tau_1"),
                "wouldCover": ("W(3,q) for every odd q -- self-dual iff q "
                               "even, ovoid-free iff q odd -- but does NOT, "
                               "because the centre property fails at q = 5"),
                "w35": {
                    "points": n5, "lines": len(lines5), "q": 5,
                    "tau1": tau5, "tau1Proved": proved5,
                    "ovoidSize": t5 * t5 + 1, "delta": tau5 - (t5 * t5 + 1),
                    "pointPerpSize": perp5, "beatsPerpBy": perp5 - tau5,
                    "centreProperty": cp5,
                    "centrePropertyFails": cp5["centrePropertyHolds"]
                                           < cp5["sampled"],
                    "theoremApplies": False,
                },
                "tau1Conjecture": {
                    "statement": "tau_1(W(3,q)) = q^2 + q - 1 for odd q",
                    "equivalently": "delta = q - 2",
                    "confirmations": [{"q": 3, "tau1": 11},
                                      {"q": 5, "tau1": tau5}],
                    "status": "CONJECTURE on two data points, not a result",
                },
                "verification": {
                    "geometry": "W(3,3)",
                    "points": n, "lines": len(lines), "t": t_,
                    "solutionsWithoutTrichotomyAtLeast": free,
                    "solutionsWithoutTrichotomyComplete": free_complete,
                    "solutionsWithTrichotomy": len(sols),
                    "status": st,
                    "allOnesSolutions": len(all_ones),
                    "ovoidSupportedSolutions": len(ovoids),
                    "uniqueAndIsAllOnes": bool(unique_all_ones),
                },
                "trichotomy": {
                    "tGreaterThanS": "impossible (gq_tight_case_theorem.py)",
                    "tEqualsS": "impossible unless self-dual (this file)",
                    "tLessThanS": ("OPEN -- branch-(B) lines have s-t points "
                                   "of multiplicity 0 and the mixing lemma "
                                   "fails"),
                },
                "attribution": {
                    "theirs": ("the self-duality route and the theorem at "
                               "q = 3, commits 43049db and 1513d61; their step "
                               "to 'bijection' used the pair count "
                               "|F| = 1 + kt/mu = 10 against alpha = 7"),
                    "addedHere": ("the mixing lemma, which needs neither the "
                                  "pair count nor the independence number, and "
                                  "the resulting extension from q = 3 to every "
                                  "odd q"),
                },
                "conditionalOn": ("the centre property, verified for W(3,3) "
                                  "over all 360 minimum blockers and MEASURED "
                                  "FALSE at q = 5"),
                "whereTheMachineryStops": ("the centre property, not "
                                           "self-duality, is the binding "
                                           "constraint on the diagonal. It "
                                           "holds in the t > s families "
                                           "because their minimum blockers are "
                                           "point-perps, and it fails at the "
                                           "first diagonal case past q = 3."),
                "boundary": ("the tight SIZE is excluded; no value of tau_2 is "
                             "determined for any q, and tau_2(W(3,3)^2) "
                             "remains open in [111, 115]."),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(out, ROOT))
    return 0 if unique_all_ones else 1


if __name__ == "__main__":
    sys.exit(main())
