#!/usr/bin/env python3
"""
The depth-2 tight case IS an m-ovoid question, with m = t+1. That reduces it
to a classical object -- and proves no counting argument can close W(3,3).

PRIOR ART, IN THIS REPOSITORY, FOUND BEFORE CLAIMING ANYTHING.
analysis/w33_shape_catalogue.js and data/w33_shape_catalogue.json already
compute the m-ovoids and tight sets of W(3,3) as intriguing sets of its
collinearity graph, with the negative-type condition |N(v) cap T| = 2m/5 - 4
inside and 2m/5 outside. Their census is complete: for W(3,3) an m-ovoid
exists only at set size 20 -- 432 of them -- and NOT at size 10, which is the
ovoid case Thas excludes. The object, the graph-theoretic characterisation and
the W(3,3) census are all already here.

Nothing in either repository connects m-ovoids to the depth-2 blocking
problem. That connection is what this file adds.

(The two definitions agree: a geometric m-ovoid meets every line in exactly m
points, so a point inside it sees 4(m-1) of its members and a point outside
sees 4m; with set size M = 10m those are exactly 2M/5 - 4 and 2M/5.)

THE EQUIVALENCE.  gq_tight_case_theorem.py showed that at the tight size the
centre multiplicity m_p lies in {0, 1, t+1} with every line summing to t+1.
Read that as a WEIGHTING of the point set rather than as a map, and the tight
case is exactly:

    a {0, 1, t+1}-valued weight on the points, every line summing to t+1.

Write F for the weight-(t+1) points and U for the weight-1 points. Then

  * F is a partial ovoid -- two F-points on a line would sum to 2(t+1) > t+1;
  * a line meeting F is already saturated, so it carries no U-point;
  * a line missing F must take its whole weight from U, so it meets U in
    exactly t+1 points.

The two pure cases name themselves:

    U empty   ==>  F meets every line exactly once:  F IS AN OVOID.
    F empty   ==>  U meets every line in t+1 points: U IS A (t+1)-OVOID.

So the tight case exists only if the quadrangle has an ovoid, a (t+1)-ovoid,
or a hybrid of the two -- and m-ovoid existence is a classical, heavily
studied question rather than a bespoke one.

WHAT IT SETTLES.

  t > s.  A (t+1)-ovoid would need t+1 points on a line that holds only
          s+1 < t+1 of them. Impossible. With no ovoid by hypothesis, nothing
          survives and the tight case is impossible. This is the theorem of
          gq_tight_case_theorem.py, now with a one-line reason -- and it is
          verified below by exhaustive solver INFEASIBILITY on GQ(2,4),
          Q^-(5,3) and H(4,4), rather than only by argument.

  t = s.  The (s+1)-ovoid is the set of ALL points: every line meets it in
          s+1 points, trivially. It always exists. So the weighting always
          admits a solution on the diagonal, and

              NO COUNTING ARGUMENT OF THIS KIND CAN EVER CLOSE t = s.

          That is a proof of why W(3,3) needed a geometric argument, where
          before this repository could only observe that it did. W33-Theory's
          self-duality step is not one route among several; on the diagonal it
          is the only kind of route there is.

  t < s.  Genuinely open, and now for a nameable reason: it needs a
          (t+1)-ovoid not to exist. Measured on the two available cases,
          both HAVE one, so the counting closes neither:

            GQ(4,2)  18,840 weightings: 200 pure-A, 16,120 pure-B, 2,520
                     mixed. The 200 are exactly the 200 ovoids of GQ(4,2)
                     that the corpus already records, recovered here as a
                     by-product. The 16,120 are 3-ovoids.
            GQ(8,4)  no ovoid at all -- proved INFEASIBLE, equivalently
                     H(4,4) has no spread -- but a 5-ovoid EXISTS, so the
                     tight case is not excluded.

A CONJECTURE THIS REFUTED, recorded because it was wrong in an informative
way. Reasoning that every line through a U-point is a branch-(B) line and
meets U in exactly t+1 points, it looked as though U carried a subquadrangle
of order (t,t) -- which for GQ(4,2) would have 15 points and would have forced
s >= t^2 by the classical subquadrangle bound. The computation says |U| = 27,
not 15. U is a 3-ovoid, not a subquadrangle: the GQ axiom fails on it, because
the unique point of a U-line collinear with a given U-point need not itself
lie in U. The m-ovoid is the right object and the subquadrangle was not.

SCOPE.  Everything here is downstream of the centre property, which is an
input verified per geometry (gq_perp_blockers_and_h44.py) and known FALSE for
W(3,5). The equivalence itself is exact and proved; the per-geometry verdicts
below are solver results, complete where marked OPTIMAL or INFEASIBLE.
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


# ---------------------------------------------------------------- geometries

def dual(n, lines):
    thru = [[li for li, L in enumerate(lines) if p in L] for p in range(n)]
    return len(lines), [sorted(t) for t in thru]


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
    return len(P), [list(x) for x in sorted(L)]


def q53():
    q = 3

    def Qf(v):
        return (v[0] * v[1] + v[2] * v[3] + v[4] * v[4] + v[5] * v[5]) % q

    def Bf(u, v):
        return (Qf(tuple((u[i] + v[i]) % q for i in range(6)))
                - Qf(u) - Qf(v)) % q

    def nm(v):
        return min(tuple((c * m) % q for c in v) for m in range(1, q))

    seen, reps = set(), []
    for v in itertools.product(range(q), repeat=6):
        if not any(v):
            continue
        k = nm(v)
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
                L.add(idx[nm(w)])
            if not ok:
                break
        if ok and len(L) == q + 1:
            lines.add(tuple(sorted(L)))
    return len(pts), [list(x) for x in sorted(lines)]


_ADD = [[0, 1, 2, 3], [1, 0, 3, 2], [2, 3, 0, 1], [3, 2, 1, 0]]
_MUL = [[0, 0, 0, 0], [0, 1, 2, 3], [0, 2, 3, 1], [0, 3, 1, 2]]
_CJ = [0, 1, 3, 2]


def h44():
    def herm(u, v):
        a = 0
        for i in range(5):
            a = _ADD[a][_MUL[u[i]][_CJ[v[i]]]]
        return a

    def nm(v):
        best = v
        for c in (1, 2, 3):
            w = tuple(_MUL[c][x] for x in v)
            if w < best:
                best = w
        return best

    pts, seen = [], set()
    for v in itertools.product(range(4), repeat=5):
        if not any(v):
            continue
        k = nm(v)
        if k in seen:
            continue
        seen.add(k)
        if herm(k, k) == 0:
            pts.append(k)
    idx = {p: i for i, p in enumerate(pts)}
    lines = set()
    for a, b in itertools.combinations(pts, 2):
        if herm(a, b) or herm(b, a):
            continue
        L, ok = set(), True
        for x in range(4):
            for y in range(4):
                if x == 0 and y == 0:
                    continue
                w = tuple(_ADD[_MUL[x][a[i]]][_MUL[y][b[i]]] for i in range(5))
                if herm(w, w) != 0:
                    ok = False
                    break
                L.add(idx[nm(w)])
            if not ok:
                break
        if ok and len(L) == 5:
            lines.add(tuple(sorted(L)))
    return len(pts), [list(x) for x in sorted(lines)]


def w33():
    def nm(v):
        i = next(k for k, x in enumerate(v) if x % 3)
        z = pow(v[i] % 3, -1, 3)
        return tuple((z * x) % 3 for x in v)

    def form(u, v):
        return (u[0] * v[1] - u[1] * v[0] + u[2] * v[3] - u[3] * v[2]) % 3

    pts = sorted({nm(v) for v in itertools.product(range(3), repeat=4)
                  if any(v)})
    idx = {v: i for i, v in enumerate(pts)}
    lines = set()
    for a, b in itertools.combinations(range(40), 2):
        if form(pts[a], pts[b]):
            continue
        S = set()
        for x, y in itertools.product(range(3), repeat=2):
            if x == y == 0:
                continue
            S.add(idx[nm(tuple((x * pts[a][k] + y * pts[b][k]) % 3
                               for k in range(4)))])
        if len(S) == 4:
            lines.add(tuple(sorted(S)))
    return 40, sorted(lines)


# ---------------------------------------------------------------- the model

def weighting_model(n, lines, t_):
    m = cp_model.CpModel()
    dom = cp_model.Domain.FromValues([0, 1, t_ + 1])
    v = [m.NewIntVarFromDomain(dom, "") for _ in range(n)]
    for L in lines:
        m.Add(sum(v[p] for p in L) == t_ + 1)
    m.Add(sum(v) == len(lines))
    return m, v


def census(n, lines, t_, cap, tl):
    """Enumerate the weightings and verify the (F, U) structure on each."""
    lsets = [set(L) for L in lines]
    m, v = weighting_model(n, lines, t_)
    state = {"k": 0, "partialOvoid": 0, "structure": 0,
             "pureA": 0, "pureAisOvoid": 0,
             "pureB": 0, "pureBisMOvoid": 0, "mixed": 0}

    class C(cp_model.CpSolverSolutionCallback):
        def __init__(self, vv):
            super().__init__()
            self.v = vv

        def on_solution_callback(self):
            state["k"] += 1
            sol = [self.Value(z) for z in self.v]
            F = {i for i, z in enumerate(sol) if z == t_ + 1}
            U = {i for i, z in enumerate(sol) if z == 1}
            if all(len(F & L) <= 1 for L in lsets):
                state["partialOvoid"] += 1
            ok = True
            for L in lsets:
                if F & L:
                    if U & L:
                        ok = False
                        break
                elif len(U & L) != t_ + 1:
                    ok = False
                    break
            if ok:
                state["structure"] += 1
            if not U:
                state["pureA"] += 1
                if all(len(F & L) == 1 for L in lsets):
                    state["pureAisOvoid"] += 1
            elif not F:
                state["pureB"] += 1
                if all(len(U & L) == t_ + 1 for L in lsets):
                    state["pureBisMOvoid"] += 1
            else:
                state["mixed"] += 1
            if state["k"] >= cap:
                self.StopSearch()

    s = cp_model.CpSolver()
    s.parameters.enumerate_all_solutions = True
    s.parameters.num_search_workers = 1
    s.parameters.max_time_in_seconds = tl
    cb = C(v)
    st = s.Solve(m, cb)
    state["status"] = s.StatusName(st)
    state["complete"] = s.StatusName(st) == "OPTIMAL" and state["k"] < cap
    return state


def pure_case(n, lines, t_, which, tl):
    """Is there an ovoid (which='A') or a (t+1)-ovoid (which='B')?"""
    m, v = weighting_model(n, lines, t_)
    for z in v:
        m.Add(z != 1) if which == "A" else m.Add(z != t_ + 1)
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = tl
    s.parameters.num_search_workers = 8
    return s.StatusName(s.Solve(m))


def main():
    print("THE TIGHT CASE IS AN m-OVOID QUESTION, WITH m = t+1")
    print("=" * 72)
    print("  A {0, 1, t+1} weight on the points with every line summing to")
    print("  t+1. Weight-(t+1) points form a partial ovoid F; lines meeting F")
    print("  are saturated so carry no weight-1 point; lines missing F take")
    print("  their whole weight from U, meeting it in exactly t+1 points.")
    print("      U empty -> F is an OVOID.   F empty -> U is a (t+1)-OVOID.")
    print()

    cases = [
        ("GQ(2,4)", gq24, False, 4000, 240.0),
        ("Q^-(5,3)", q53, False, 4000, 300.0),
        ("H(4,4)", h44, False, 4000, 360.0),
        ("W(3,3)", w33, False, 4000, 240.0),
        ("GQ(4,2)", gq24, True, 30000, 300.0),
        ("GQ(8,4)", h44, True, 200, 420.0),
    ]
    rows = []
    for name, builder, take_dual, cap, tl in cases:
        n, lines = builder()
        if take_dual:
            n, lines = dual(n, lines)
        spl = len(lines[0])
        per = sum(1 for L in lines if 0 in L)
        s_, t_ = spl - 1, per - 1
        a = pure_case(n, lines, t_, "A", tl)
        b = pure_case(n, lines, t_, "B", tl)
        c = census(n, lines, t_, cap, tl)
        rows.append({
            "name": name, "points": n, "lines": len(lines),
            "s": s_, "t": t_, "pointsPerLine": spl, "linesPerPoint": per,
            "mOvoidNeeded": t_ + 1,
            "mExceedsLineSize": t_ + 1 > s_ + 1,
            "ovoidExists": a != "INFEASIBLE",
            "ovoidStatus": a,
            "mOvoidExists": b != "INFEASIBLE",
            "mOvoidStatus": b,
            "census": c,
            "tightCaseExcluded": c["k"] == 0 and c["status"] == "INFEASIBLE",
        })
        print("  %-9s s=%d t=%d | need a %d-ovoid; lines hold %d points%s"
              % (name, s_, t_, t_ + 1, spl,
                 "  <-- IMPOSSIBLE" if t_ + 1 > spl else ""))
        print("        ovoid: %-11s   (t+1)-ovoid: %-11s"
              % (rows[-1]["ovoidStatus"], rows[-1]["mOvoidStatus"]))
        print("        weightings: %d%s (%s)  pureA %d (ovoids %d), "
              "pureB %d (m-ovoids %d), mixed %d"
              % (c["k"], "" if c["complete"] else "+", c["status"],
                 c["pureA"], c["pureAisOvoid"], c["pureB"],
                 c["pureBisMOvoid"], c["mixed"]))
        print("        (F,U) structure held on %d of %d; F a partial ovoid on "
              "%d" % (c["structure"], c["k"], c["partialOvoid"]))
        print("        ==> %s" % ("tight case EXCLUDED"
                                  if rows[-1]["tightCaseExcluded"]
                                  else "tight case NOT excluded by counting"))
        print()

    diag = next(r for r in rows if r["s"] == r["t"])
    print("  THE DIAGONAL IS PROVABLY BEYOND THIS METHOD. At t = s the")
    print("  (s+1)-ovoid is the whole point set -- every line meets it in")
    print("  s+1 points, trivially -- so a solution ALWAYS exists and no")
    print("  counting argument of this kind can close t = s. W(3,3) needed")
    print("  self-duality not by accident but of necessity.")
    print("     W(3,3) weightings found: %d (the all-ones vector)" % diag["census"]["k"])

    ok = all(r["census"]["structure"] == r["census"]["k"] for r in rows) and \
        all(r["census"]["pureA"] == r["census"]["pureAisOvoid"] and
            r["census"]["pureB"] == r["census"]["pureBisMOvoid"] for r in rows)

    if "--write" in sys.argv:
        out = os.path.join(ROOT, "data", "gq_tight_case_is_an_m_ovoid.json")
        with open(out, "w") as fh:
            json.dump({
                "schema": "holotrade.gq-tight-case-m-ovoid.v1",
                "valid": bool(ok),
                "equivalence": ("the depth-2 tight case is exactly a "
                                "{0,1,t+1}-valued weight on the points with "
                                "every line summing to t+1; the pure cases are "
                                "an ovoid and a (t+1)-ovoid"),
                "priorArt": {
                    "inThisRepository": ("analysis/w33_shape_catalogue.js and "
                                         "data/w33_shape_catalogue.json already "
                                         "compute m-ovoids and tight sets of "
                                         "W(3,3) as intriguing sets of its "
                                         "collinearity graph"),
                    "theirCensus": ("complete: an m-ovoid of W(3,3) exists only "
                                    "at set size 20, 432 of them, and not at "
                                    "size 10, the ovoid case"),
                    "whatIsNewHere": ("the connection to the depth-2 blocking "
                                      "problem; no file in either repository "
                                      "linked m-ovoids to it"),
                },
                "instances": rows,
                "diagonalIsBeyondCounting": (
                    "at t = s the (s+1)-ovoid is the entire point set and "
                    "always exists, so no weighting argument can ever close "
                    "the diagonal. This PROVES that W(3,3) required a "
                    "geometric argument rather than merely observing it."),
                "refutedConjecture": (
                    "that U carries a subquadrangle of order (t,t), which for "
                    "GQ(4,2) would have 15 points and would have forced "
                    "s >= t^2. The computation gives |U| = 27: U is a 3-ovoid, "
                    "not a subquadrangle, because the GQ axiom fails on it."),
                "boundary": ("this reformulates and verifies; it determines no "
                             "value of tau_2. tau_2(W(3,3)^2) stays open in "
                             "[111, 115]."),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(out, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
