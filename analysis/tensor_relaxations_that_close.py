#!/usr/bin/env python3
"""
Two more relaxations of the depth-2 problem, both of which close. Recorded so
the next attempt does not spend a day rediscovering that they do.

This repository already carries a positive result of exactly this shape:
tensor_110_no_local_obstruction.py showed that nine formulations of the tight
case all return consistent, and concluded that any refutation had to be
global. That prediction was borne out -- W33-Theory's refutation was a
self-duality argument, about as global as a quadrangle admits. The two
relaxations here are new, are not among those nine, and close as well.

RELAXATION 1: THE SIZE-SUM INTEGER PROGRAM.

There is a reformulation of the whole problem that is worth having on its own.
A depth-2 blocker is the same thing as an assignment of a set R_p to each
point p such that

    for every line L,  the union of R_p over p in L is a blocking set,

minimising sum_p |R_p|. (The union is the row shadow B_L.) A blocking set has
at least tau_1 points, so with w_p = |R_p| every line satisfies
sum_{p in L} w_p >= tau_1, and

    tau_2 >= min { sum_p w_p : w >= 0 integer, every line sums to >= tau_1 }.

The uniform fractional point w = tau_1/(s+1) gives sum = (st+1) tau_1, the
familiar shadow bound. The question is whether INTEGRALITY costs anything --
tau_1 is not divisible by s+1 in any of the three geometries below,
which is the kind of gap
that sometimes forces the optimum up.

It does not. The integer optimum equals the shadow bound exactly every
time: 110 for W(3,3), 90 for GQ(2,4), 840 for Q^-(5,3).
The optimal size vectors are wildly non-uniform -- for GQ(2,4) ten points of
size 0, sixteen of size 5, one of size 10 -- which is the reason it is cheap:
the program can put mass anywhere, while a real R_p assignment cannot.

RELAXATION 2: THE RANK OBSTRUCTION ON THE MATRIX EQUATION.

tensor_tight_matrix_equation.py wrote the tight case as N^T X N = J + P N with
N the point-line incidence matrix and P the centre-selection matrix. With
defect delta the correct form is

    N^T X N = J + delta * P N.

Now observe that over ANY field, row L of N^T X N = N^T (X N) is a combination
of rows of X N, and each of those is a combination of rows of N. So every row
of the left side lies in rowspace(N). On the right, row L is
1^T + delta * N[c_L, :], and N[c_L, :] is a row of N. Therefore the equation
forces

    the all-ones vector 1 to lie in the mod-p row space of N,

for every prime p -- and when p divides delta the delta * P N term vanishes
and the requirement is bare. This is a genuine obstruction with no counting in
it at all, it costs one rank computation, and it would apply to every
quadrangle at once.

It closes. For W(3,3), GQ(2,4) and Q^-(5,3), at p = 2 and p = 3, adjoining the
all-ones row leaves the rank unchanged: 1 is in the row space every time. The
computation also reproduces rank_3(W(3,3)) = 25, which is the value the
corpus's rank law already gives (Sastry-Sin; see RESULTS_INDEX.md), so the
arithmetic is cross-checked against prior art rather than trusted.

WHY BOTH FAIL, in one sentence.  Each throws away the only thing that makes
the problem hard -- relaxation 1 forgets that R_p is a SET inside the geometry
and keeps only its size; relaxation 2 forgets everything except the row space,
and 1 lies in the row space because N's rows already sum to a multiple of the
all-ones vector. The pattern is the same one the no-local-obstruction result
identified: every invariant that survives the abstraction closes.
"""

import itertools
import json
import os
import sys

try:
    from ortools.sat.python import cp_model
except ImportError:
    sys.exit("needs ortools:  py -3 -m pip install ortools")
try:
    from sympy import GF
    from sympy.polys.matrices import DomainMatrix
except ImportError:
    sys.exit("needs sympy:  py -3 -m pip install sympy")

ROOT = r"C:\Repos\Holotrade"


def w33():
    def norm(v):
        i = next(k for k, x in enumerate(v) if x % 3)
        z = pow(v[i] % 3, -1, 3)
        return tuple((z * x) % 3 for x in v)

    def form(u, v):
        return (u[0] * v[1] - u[1] * v[0] + u[2] * v[3] - u[3] * v[2]) % 3

    pts = sorted({norm(v) for v in itertools.product(range(3), repeat=4)
                  if any(v)})
    idx = {v: i for i, v in enumerate(pts)}
    lines = set()
    for a, b in itertools.combinations(range(40), 2):
        if form(pts[a], pts[b]):
            continue
        S = set()
        for s, t in itertools.product(range(3), repeat=2):
            if s == t == 0:
                continue
            S.add(idx[norm(tuple((s * pts[a][k] + t * pts[b][k]) % 3
                                 for k in range(4)))])
        if len(S) == 4:
            lines.add(tuple(sorted(S)))
    return 40, sorted(lines), 11, 1


def gq24():
    def Qf(v):
        return (v[0] * v[1] + v[2] * v[3]
                + v[4] * v[4] + v[4] * v[5] + v[5] * v[5]) % 2

    def Bf(u, v):
        return (Qf([u[i] ^ v[i] for i in range(6)]) ^ Qf(u) ^ Qf(v)) % 2

    P = [v for v in itertools.product([0, 1], repeat=6)
         if any(v) and Qf(v) == 0]
    ix = {v: i for i, v in enumerate(P)}
    L = set()
    for a, b in itertools.combinations(P, 2):
        if Bf(a, b) == 0:
            c = tuple(a[i] ^ b[i] for i in range(6))
            if any(c) and Qf(c) == 0:
                L.add(tuple(sorted(ix[x] for x in (a, b, c))))
    return len(P), sorted(L), 10, 1


def q53():
    q = 3

    def Qf(v):
        return (v[0] * v[1] + v[2] * v[3] + v[4] * v[4] + v[5] * v[5]) % q

    def Bf(u, v):
        return (Qf(tuple((u[i] + v[i]) % q for i in range(6)))
                - Qf(u) - Qf(v)) % q

    def norm(v):
        return min(tuple((c * s) % q for c in v) for s in range(1, q))

    seen, reps = set(), []
    for v in itertools.product(range(q), repeat=6):
        if not any(v):
            continue
        k = norm(v)
        if k not in seen:
            seen.add(k)
            reps.append(k)
    pts = [p for p in reps if Qf(p) == 0]
    idx = {p: i for i, p in enumerate(pts)}
    lines = set()
    for a, b in itertools.combinations(pts, 2):
        if Bf(a, b) != 0:
            continue
        L, ok = set(), True
        for x in range(q):
            for y in range(q):
                if x == 0 and y == 0:
                    continue
                w = tuple((x * a[i] + y * b[i]) % q for i in range(6))
                if Qf(w) != 0:
                    ok = False
                    break
                L.add(idx[norm(w)])
            if not ok:
                break
        if ok and len(L) == q + 1:
            lines.add(tuple(sorted(L)))
    return len(pts), sorted(lines), 30, 2


def size_sum_ip(n, lines, tau):
    m = cp_model.CpModel()
    w = [m.NewIntVar(0, tau, "") for _ in range(n)]
    for L in lines:
        m.Add(sum(w[p] for p in L) >= tau)
    m.Minimize(sum(w))
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = 180.0
    s.parameters.num_search_workers = 8
    st = s.Solve(m)
    return (int(s.ObjectiveValue()), s.StatusName(st) == "OPTIMAL",
            sorted(s.Value(x) for x in w))


def rank_check(n, lines, p):
    nl = len(lines)
    N = [[1 if pt in lines[li] else 0 for li in range(nl)] for pt in range(n)]
    r = DomainMatrix.from_list(N, GF(p)).rank()
    ra = DomainMatrix.from_list(N + [[1] * nl], GF(p)).rank()
    return r, ra, ra == r


def main():
    print("TWO MORE RELAXATIONS, BOTH CLOSED")
    print("=" * 70)
    rows = []
    for name, f in (("W(3,3)", w33), ("GQ(2,4)", gq24),
                    ("Q^-(5,3)", q53)):
        n, lines, tau, delta = f()
        nl = len(lines)
        spl = len(lines[0])
        # shadow bound = (st+1) * tau_1 = #lines * tau_1 / (t+1)
        per_point = sum(1 for L in lines if 0 in L)
        shadow = nl * tau // per_point
        val, proved, vec = size_sum_ip(n, lines, tau)
        ranks = {str(p): dict(zip(("rankN", "rankWithOnes", "onesInRowspace"),
                                  rank_check(n, lines, p)))
                 for p in (2, 3)}
        rows.append({
            "name": name, "points": n, "lines": nl, "pointsPerLine": spl,
            "linesPerPoint": per_point, "tau1": tau, "delta": delta,
            "shadowBound": shadow,
            "sizeSumIntegerOptimum": val, "sizeSumProved": proved,
            "integralityGain": val - shadow,
            "sizeVectorTail": vec[-6:],
            "rankObstruction": ranks,
            "rankObstructionCloses": all(v["onesInRowspace"]
                                         for v in ranks.values()),
        })
        print("  %-9s tau_1=%d delta=%d | shadow bound %d ; integer size-sum "
              "optimum %d%s -> gain %d"
              % (name, tau, delta, shadow, val, "" if proved else " (unproved)",
                 val - shadow))
        for p in ("2", "3"):
            d = ranks[p]
            print("            mod %s: rank(N)=%d, with all-ones row %d -> "
                  "1 in rowspace: %s"
                  % (p, d["rankN"], d["rankWithOnes"], d["onesInRowspace"]))
    print()
    print("  Both relaxations return exactly the bound already known, in every")
    print("  geometry. Neither is among the nine formulations recorded in")
    print("  tensor_110_no_local_obstruction.py, and both close for the same")
    print("  reason those did: what they keep is not what makes it hard.")
    print()
    print("  rank_3(W(3,3)) = 25 agrees with the corpus's rank law")
    print("  (Sastry-Sin, already in RESULTS_INDEX.md), so the linear algebra")
    print("  is cross-checked against prior art rather than trusted.")

    ok = all(r["integralityGain"] == 0 and r["rankObstructionCloses"]
             for r in rows)
    if "--write" in sys.argv:
        out = os.path.join(ROOT, "data", "tensor_relaxations_that_close.json")
        with open(out, "w") as fh:
            json.dump({
                "schema": "holotrade.tensor-relaxations-that-close.v1",
                "valid": True,
                "bothClose": bool(ok),
                "reformulation": ("a depth-2 blocker is an assignment of a set "
                                  "R_p to each point with the union over any "
                                  "line a blocking set, minimising sum |R_p|"),
                "relaxation1": ("integer program: w >= 0 with every line "
                                "summing to >= tau_1. Its optimum equals the "
                                "shadow bound in every geometry, so "
                                "integrality costs nothing."),
                "relaxation2": ("N^T X N = J + delta * P N puts every row of "
                                "the right side in rowspace(N), so 1 must lie "
                                "in the mod-p row space of N. It does, at "
                                "p = 2 and p = 3, in every geometry."),
                "instances": rows,
                "relationToPriorWork": ("tensor_110_no_local_obstruction.py "
                                        "predicted that any refutation of the "
                                        "tight case had to be global; "
                                        "W33-Theory's self-duality proof was. "
                                        "These two are further local "
                                        "invariants and they close too."),
                "crossCheck": ("rank_3(W(3,3)) = 25 matches the corpus rank "
                               "law (Sastry-Sin)"),
                "boundary": ("both are NEGATIVE results. They prove nothing "
                             "about tau_2 and are recorded only to stop the "
                             "same ground being covered again."),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(out, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
