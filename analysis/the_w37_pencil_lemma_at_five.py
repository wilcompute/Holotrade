#!/usr/bin/env python3
"""
The pencil lemma at x = 5 for W(3,7): every weighted 5-tight set of lines with
all weights at most 4 contains a full pencil. Together with the x <= 4 cases
already certified, the line excess of every 55-point blocker of W(3,7) whose
lines all meet it at most 5 times is a sum of five point-pencils.

WHERE IT IS USED.  tau1_of_w37_is_at_least_54.py (5b6a9b1) certifies the lemma
for x = 1, 2, 3 and tau1_of_w37_is_55.py (9d5751e) for x = 4. A blocker of size
q^2+1+delta has excess e with A_L e = (q-1)e + delta.1 and e <= delta (the
counting identity of those files). For the minimum blockers, delta = 5. A line
meeting B in 6 points (e = 5) is handled separately by the triangle-free
argument, so the remaining case has e <= 4, and it is exactly this lemma.

THE INSTANCES.  For max weight w = 4, 3, 2, line 0 attains the maximum, by
transitivity on lines. For w = 1 the case is split by maximum point load (see
below). Each instance asks for an integer e with 0 <= e <= w and
A_L e = 6e + 5.1, with no point carrying e >= 1 on all eight of its lines. Each is an exact CP-SAT
INFEASIBLE, and each carries a control -- the same model without the no-pencil
constraint -- which must be feasible. Subtracting a pencil leaves a 4-tight
set, which the x = 4 lemma handles, so by induction e = N^T y, y >= 0, sum 5.

THE LOAD CUT (what makes w = 2, 1 tractable).  Let f_p = sum of e over the
eight lines through p. Summing the tight equation over the points of a line L
gives sum_{p in L} f_p = 14 e_L + 5. If no pencil is full, every point p lies
on a line Z with e_Z = 0, and then f_p <= sum_{r in Z} f_r = 5. So every
no-pencil solution satisfies f_p <= 5 at every point. The cut is implied, and
adding it changes no verdict. It also settles w = 4 and 3 by hand: on a line
of weight w, 14w + 5 = sum f_p <= 8 * 5 = 40 forces w <= 2. The solver
confirms both. Without the cut, w = 2 and 1 ran six hours UNKNOWN; with it,
w = 2 is INFEASIBLE in about 13 minutes.

WEIGHT ONE, SPLIT BY THE MAXIMUM LOAD.  With all e <= 1 the solver still
stalls, so split by M = max_p f_p. An E-line carries load 19 on 8 points,
so M >= 3, and the cut gives M <= 5. Similitudes preserve the lines, and
PGSp(4,7) is transitive on points; its point stabiliser induces PGL(2,7) on
the 8 lines through the point, which is 3-transitive. So a point of load M
and three of its positive lines can be placed at point 0 and its first three
lines. Each of M = 5, 4, 3 is then an INFEASIBLE instance with f <= M, and
each has a feasible control.

SCOPE.  Exact solver verdicts with controls; the induction and the reduction
are argued in the cited files. Runtime is dominated by the small-w instances.
"""

import argparse
import itertools
import json
import os
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Q = 7


def geometry():
    def nm(v):
        i = next(k for k, x in enumerate(v) if x % Q)
        z = pow(v[i] % Q, -1, Q)
        return tuple((z * x) % Q for x in v)
    pts = sorted({nm(v) for v in itertools.product(range(Q), repeat=4) if any(v)})
    idx = {p: i for i, p in enumerate(pts)}
    n = len(pts)

    def sf(u, v):
        return (u[0] * v[2] - u[2] * v[0] + u[1] * v[3] - u[3] * v[1]) % Q
    lines = set()
    for a, b in itertools.combinations(range(n), 2):
        if sf(pts[a], pts[b]):
            continue
        lines.add(frozenset(idx[nm(tuple((x * pts[a][k] + y * pts[b][k]) % Q for k in range(4)))]
                            for x in range(Q) for y in range(Q) if x or y))
    lines = sorted(lines, key=sorted)
    assert n == 400 and len(lines) == 400
    return n, lines


def pencil_is_three_transitive(n, lines):
    """The similitudes g = (A on e0,e2; det A on e1; 1 on e3) fix point 0 = <e3>; check they preserve the
    line set and induce a 3-transitive group of order 336 = |PGL(2,7)| on the 8 lines through point 0."""
    def nm(v):
        i = next(k for k, x in enumerate(v) if x % Q)
        z = pow(v[i] % Q, -1, Q)
        return tuple((z * x) % Q for x in v)
    pts = sorted({nm(v) for v in itertools.product(range(Q), repeat=4) if any(v)})
    idx = {p: i for i, p in enumerate(pts)}
    assert pts[0] == (0, 0, 0, 1)
    lid = {L: j for j, L in enumerate(lines)}
    thru0 = [j for j, L in enumerate(lines) if 0 in L]
    gens = []
    for A in (((3, 0), (0, 1)), ((1, 1), (0, 1)), ((0, 1), (Q - 1, 0))):
        lam = (A[0][0] * A[1][1] - A[0][1] * A[1][0]) % Q

        def g(v):
            return nm(((A[0][0] * v[0] + A[0][1] * v[2]) % Q, (lam * v[1]) % Q,
                       (A[1][0] * v[0] + A[1][1] * v[2]) % Q, v[3]))
        img = {j: lid.get(frozenset(idx[g(pts[i])] for i in L)) for j, L in enumerate(lines)}
        if any(v is None for v in img.values()):
            return False
        gens.append(tuple(thru0.index(img[j]) for j in thru0))
    group = {tuple(range(8))}
    frontier = list(group)
    while frontier:
        nxt = []
        for a in frontier:
            for s in gens:
                b = tuple(s[i] for i in a)
                if b not in group:
                    group.add(b)
                    nxt.append(b)
        frontier = nxt
    triples = {(p[0], p[1], p[2]) for p in group}
    return len(group) == 336 and len(triples) == 8 * 7 * 6


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--budget", type=float, default=21600.0)
    args = ap.parse_args()
    from ortools.sat.python import cp_model

    n, lines = geometry()
    thru = [[j for j, L in enumerate(lines) if p in L] for p in range(n)]
    meet = [[k for k, M in enumerate(lines) if k != j and lines[j] & M] for j in range(n)]
    assert all(len(r) == Q * (Q + 1) for r in meet)
    three_transitive = pencil_is_three_transitive(n, lines)
    print("  point-0 pencil: similitude stabiliser 3-transitive, order 336: %s" % three_transitive)
    out = {}
    print("THE W(3,7) PENCIL LEMMA AT x = 5")
    print("=" * 74)
    # (label, max weight w, max point load M or None)
    for label, w, M in (("w4", 4, None), ("w3", 3, None), ("w2", 2, None),
                        ("w1_M5", 1, 5), ("w1_M4", 1, 4), ("w1_M3", 1, 3)):
        row = {}
        for mode in ("noPencil", "control"):
            m = cp_model.CpModel()
            e = [m.NewIntVar(0, w, "") for _ in range(n)]
            for j in range(n):
                m.Add(sum(e[k] for k in meet[j]) == (Q - 1) * e[j] + 5)
            if M is None:
                m.Add(e[0] == w)
            else:
                m.Add(sum(e[j] for j in thru[0]) == M)
                for j in thru[0][:3]:
                    m.Add(e[j] == 1)
            if mode == "noPencil":
                for p in range(n):
                    pos = []
                    for j in thru[p]:
                        b = m.NewBoolVar("")
                        m.Add(e[j] >= 1).OnlyEnforceIf(b)
                        m.Add(e[j] == 0).OnlyEnforceIf(b.Not())
                        pos.append(b)
                    m.Add(sum(pos) <= Q)
                    # the load cut: p lies on a zero line, whose points carry load 5 in total
                    m.Add(sum(e[j] for j in thru[p]) <= (5 if M is None else M))
            sv = cp_model.CpSolver()
            sv.parameters.num_workers = 8
            sv.parameters.max_time_in_seconds = args.budget
            t0 = time.time()
            row[mode] = (sv.StatusName(sv.Solve(m)), round(time.time() - t0, 1))
            print("  %-6s %-9s %s %ss" % (label, mode, row[mode][0], row[mode][1]), flush=True)
        out[label] = row
    ok = three_transitive and all(r["noPencil"][0] == "INFEASIBLE" and r["control"][0] in ("OPTIMAL", "FEASIBLE")
                                  for r in out.values())
    print()
    print("VALID: %s" % ok)
    if args.write:
        assert ok, "checks failed -- refusing to write"
        rec = {
            "schema": "holotrade.w37-pencil-lemma-x5.v1",
            "valid": True,
            "q": Q, "x": 5,
            "instances": {lab: {k: v[0] for k, v in r.items()} for lab, r in out.items()},
            "seconds": {lab: {k: v[1] for k, v in r.items()} for lab, r in out.items()},
            "weightOneSplit": ("all e <= 1: the maximum point load M is >= 3 (a positive line carries load 19 on "
                               "8 points) and <= 5 (load cut); a point of load M and three of its positive lines "
                               "are moved to point 0 and its first three lines by PGSp(4,7), whose point "
                               "stabiliser induces PGL(2,7), 3-transitive, on the pencil"),
            "statement": (
                "every integer e on the lines of W(3,7) with 0 <= e <= 4 and A_L e = 6e + 5.1 contains a full pencil; "
                "with the x <= 4 lemmas (5b6a9b1, 9d5751e) the excess of a 55-point blocker with all counts <= 5 is "
                "N^T y with y >= 0 integer and sum 5."),
            "loadCut": ("no full pencil => every point is on a zero line Z, whose points carry total load 5, so "
                        "f_p <= 5; with sum_{p in L} f_p = 14 e_L + 5 this forces e <= 2"),
            "boundary": "exact CP-SAT verdicts with feasible controls; induction and reduction argued in the cited files.",
        }
        p = os.path.join(ROOT, "data", "w37_pencil_lemma_x5.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=2)
        print("written: %s" % p)


if __name__ == "__main__":
    main()
