#!/usr/bin/env python3
"""
The depth-n blocking number grows at rate exactly 10, not 10.7238. The
fractional cover number settles the exponential, and it also explains where
the SDP's 100 came from.

WHAT WAS OPEN.  js/tensor-sharding.js reports, for depth n,

    lower = 11 * 10^(n-1)          from the recursive shadow double-count
    upper = 115^floor(n/2) * 11^(n mod 2)

so the EXPONENTIAL BASE was pinned only to the interval [10, 115^(1/2)] =
[10, 10.7238...]. Which end is the truth was not decided anywhere in either
repository. It is 10, and the proof is three short steps.

STEP 1: tau* = 10, with a certificate anyone can check by eye.  The line
hypergraph of W(3,3) has 40 points and 40 lines, four points per line and four
lines per point. Take y = 1/4 on every point: each line sums to 4 * 1/4 = 1,
so y is a fractional cover of weight 10. Take z = 1/4 on every line: each
point sums to 4 * 1/4 = 1, so z is a fractional matching of weight 10. Weak
duality sandwiches everything between them, so

    nu*(H) = tau*(H) = 10   exactly,

against tau_1 = 11. The integrality gap of the single-level problem is
therefore exactly 11/10, and it is that gap -- not the geometry -- that the
whole depth-n question inherits.

STEP 2: tau* is exactly multiplicative on this product.  For hypergraphs H1,
H2 with product edges L x M:

  * if y1, y2 are fractional covers then y1 (x) y2 is one, because
    sum over (p,q) in L x M of y1(p) y2(q) = (sum_{p in L} y1)(sum_{q in M} y2)
    >= 1. So tau*(H1 x H2) <= tau*(H1) tau*(H2).
  * if z1, z2 are fractional matchings then z1 (x) z2 is one, by the same
    factorisation on the point (p,q). So nu*(H1 x H2) >= nu*(H1) nu*(H2).

LP duality equates nu* and tau* on both sides, and the two inequalities close:

    tau*(H^n) = tau*(H)^n = 10^n,    exactly.

Verified below by solving the 1,600-variable product LP directly: it returns
100.

AND THAT IDENTIFIES A NUMBER THE REPOSITORY ALREADY HAD.
tensor_110_no_local_obstruction.py records that the symmetry-reduced
Lasserre-1 SDP "returns 100, below even the elementary shadow bound of 110",
and treats it as a weakness of the relaxation. It is not a weakness or an
artifact: 100 IS tau*(H^2), the exact fractional optimum. No relaxation
sitting above the LP can do better, so the SDP was reporting the truth of its
own level.

STEP 3: greedy closes the rate from above.  Set cover's greedy bound gives
tau <= (1 + ln s) tau*, with s the largest number of edges through one vertex.
In H^n a vertex (p_1..p_n) lies in 4^n product edges, so

    10^n  <=  tau(H^n)  <=  10^n (1 + n ln 4),

and taking n-th roots squeezes the base:

    lim tau(H^n)^(1/n)  =  10.                                       []

WHAT THIS DOES AND DOES NOT CHANGE.  It does NOT beat the 115 witness at any
depth people will use. 115^(n/2) is smaller than 10^n (1 + n ln 4) until the
crossover computed below, which is far beyond any practical depth, and greedy
run directly on H^2 returns 128 -- worse than 115. The recursive lower bound
11 * 10^(n-1) also stays better than 10^n for every n.

What it settles is the exponent. The base is 10, the lower bound's base was
already right, and 115^(n/2) is a good finite bound with the wrong exponential
attached to it. Any future attempt to push the upper bound below 10^n is
attempting something impossible, and any hope that the true base exceeds 10 is
misplaced.

THE HONEST BOUNDARY.  This is an asymptotic statement about the exponential
base and nothing more. It determines no exact value: tau_2(W(3,3)^2) stays
open in [111, 115], and the ratio tau(H^n)/10^n is only known to lie between
1.1 (from the recursive bound) and 1 + n ln 4.
"""

import itertools
import json
import math
import os
import sys

try:
    from ortools.linear_solver import pywraplp
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


def lp_cover(n, edges):
    s = pywraplp.Solver.CreateSolver("GLOP")
    y = [s.NumVar(0, 1, "") for _ in range(n)]
    for E in edges:
        s.Add(sum(y[p] for p in E) >= 1)
    s.Minimize(sum(y))
    s.Solve()
    return sum(v.solution_value() for v in y)


def lp_match(n, edges):
    s = pywraplp.Solver.CreateSolver("GLOP")
    z = [s.NumVar(0, 1, "") for _ in edges]
    for p in range(n):
        s.Add(sum(z[i] for i, E in enumerate(edges) if p in E) <= 1)
    s.Maximize(sum(z))
    s.Solve()
    return sum(v.solution_value() for v in z)


def greedy(nv, edges):
    cover_of = [[] for _ in range(nv)]
    for ei, E in enumerate(edges):
        for v in E:
            cover_of[v].append(ei)
    uncovered = set(range(len(edges)))
    chosen = 0
    while uncovered:
        best = max(range(nv),
                   key=lambda v: len(uncovered.intersection(cover_of[v])))
        chosen += 1
        uncovered -= set(cover_of[best])
    return chosen


def main():
    lines = geometry()
    E1 = [set(L) for L in lines]
    print("THE GROWTH RATE IS EXACTLY 10")
    print("=" * 72)
    print("  W(3,3): %d points, %d lines of 4, 4 lines per point" % (N, len(lines)))

    # the hand certificate, checked rather than asserted
    unit_cover = all(abs(sum(0.25 for _ in L) - 1.0) < 1e-12 for L in lines)
    deg = [sum(1 for L in lines if p in L) for p in range(N)]
    unit_match = all(abs(d * 0.25 - 1.0) < 1e-12 for d in deg)
    tstar = lp_cover(N, E1)
    nstar = lp_match(N, E1)
    print("  y = 1/4 everywhere is a fractional COVER of weight 10: %s"
          % unit_cover)
    print("  z = 1/4 everywhere is a fractional MATCHING of weight 10: %s"
          % unit_match)
    print("  LP confirms tau* = %.6f, nu* = %.6f -> equal, so both optimal"
          % (tstar, nstar))
    print("  against tau_1 = 11: single-level integrality gap = 11/10")
    print()

    E2 = [frozenset(a * N + b for a in L for b in M)
          for L in lines for M in lines]
    tstar2 = lp_cover(N * N, E2)
    print("  product LP over %d variables: tau*(H^2) = %.4f (= tau*^2 = %.0f)"
          % (N * N, tstar2, tstar * tstar))
    print("  ==> the SDP's 100, recorded in tensor_110_no_local_obstruction.py")
    print("      as 'below even the elementary bound', is EXACTLY tau*(H^2).")
    print("      Not an artifact: the truth of its own level.")
    print()

    g2 = greedy(N * N, E2)
    bound2 = tstar2 * (1 + 2 * math.log(4))
    print("  greedy on H^2: %d leaves (its guarantee is %.1f; the 115 witness"
          % (g2, bound2))
    print("  is better than both, so greedy does not threaten the upper bound)")
    print()

    rows = []
    cross = None
    for n in range(1, 121):
        lo = 11 * 10 ** (n - 1)
        prod = 115 ** (n // 2) * 11 ** (n % 2)
        gre = (10 ** n) * (1 + n * math.log(4))
        if cross is None and n >= 2 and gre < prod:
            cross = n
        if n <= 6 or n in (10, 20, 50, 70, 80, 100, 120):
            rows.append({"depth": n, "lowerRecursive": lo,
                         "upperProduct": float(prod),
                         "upperGreedy": gre})
    print("  base comparison:  lower 11*10^(n-1) has base 10;")
    print("                    upper 115^(n/2)   has base %.4f" % math.sqrt(115))
    print("                    greedy 10^n(1+n ln4) has base 10")
    print("  the product bound is the better NUMBER until depth %s," % cross)
    print("  but its exponential base is not the truth. The base is 10.")
    print()
    print("  ==> lim tau(H^n)^(1/n) = tau*(H) = 10, exactly.")
    print("      The recursive lower bound already had the right base; the")
    print("      upper bound's 10.7238 does not survive the limit.")

    ok = (abs(tstar - 10) < 1e-6 and abs(nstar - 10) < 1e-6
          and abs(tstar2 - 100) < 1e-4 and unit_cover and unit_match)

    if "--write" in sys.argv:
        out = os.path.join(ROOT, "data",
                           "tensor_growth_rate_is_exactly_ten.json")
        with open(out, "w") as fh:
            json.dump({
                "schema": "holotrade.tensor-growth-rate-ten.v1",
                "valid": bool(ok),
                "tauStar": tstar, "nuStar": nstar,
                "certificate": ("y = 1/4 on every point is a fractional cover "
                                "of weight 10; z = 1/4 on every line is a "
                                "fractional matching of weight 10; weak "
                                "duality makes both optimal"),
                "certificateChecked": {"coverIsUnitOnEveryLine": unit_cover,
                                       "matchingIsUnitOnEveryPoint": unit_match},
                "tau1": 11,
                "integralityGapDepth1": "11/10",
                "tauStarProduct": tstar2,
                "multiplicativity": ("tau*(H1 x H2) = tau*(H1) tau*(H2): the "
                                     "tensor of covers is a cover and the "
                                     "tensor of matchings is a matching, and "
                                     "LP duality closes both directions"),
                "sdpIdentified": ("the 100 reported by the symmetry-reduced "
                                  "Lasserre-1 SDP in "
                                  "tensor_110_no_local_obstruction.py is "
                                  "exactly tau*(H^2), not an artifact of the "
                                  "relaxation"),
                "greedyOnH2": g2,
                "greedyGuaranteeH2": bound2,
                "theorem": "lim tau(H^n)^(1/n) = tau*(H) = 10",
                "proof": ["tau*(H^n) = 10^n exactly",
                          "tau(H^n) >= tau*(H^n) = 10^n",
                          "greedy gives tau(H^n) <= 10^n (1 + n ln 4)",
                          "take n-th roots"],
                "basesBefore": {"lower": 10.0, "upper": math.sqrt(115)},
                "baseAfter": 10.0,
                "productBoundBetterUntilDepth": cross,
                "depthTable": rows,
                "boundary": ("an asymptotic statement about the exponential "
                             "base only. It determines no exact value: "
                             "tau_2(W(3,3)^2) stays open in [111, 115], and "
                             "tau(H^n)/10^n is known only to lie in "
                             "[1.1, 1 + n ln 4]."),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(out, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
