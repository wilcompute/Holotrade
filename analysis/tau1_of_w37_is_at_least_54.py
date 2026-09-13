#!/usr/bin/env python3
"""
tau_1(W(3,7)) >= 54. The open interval [53, 55] narrows to [54, 55]: no
blocking set of W(3,7) has 53 points.

WHERE THIS STOOD.  the_minimality_fence_was_wrong.py (92124f1) narrowed
tau_1(W(3,7)) to [53, 55] -- 53 from Eisfeld, Storme, Szonyi and Sziklai
(a cover of Q(4,q), q odd, needs more than q^2+1+(q-1)/3 lines), 55 from the
octet construction -- and recorded that a direct CP-SAT attempt at 53 returned
UNKNOWN after 2700 seconds.

THE METHOD is the one that classified the minimum blockers of W(3,5) in
the_q5_tight_case_dies_without_the_centre_property.py (b9f5d5b), transported.

 (a) THE COUNTING IDENTITY.  Let B be a blocker with |B| = q^2+1+delta and
     excess e(M) = |B n M| - 1 >= 0. A point off a line M lies on exactly one
     line meeting M, so summing |B n N| over the q(q+1) lines N meeting M gives
            A_L e  =  (q-1) e  +  delta * 1,
     A_L the line adjacency: e is a WEIGHTED delta-TIGHT SET of lines. Summing
     the identity over all lines gives sum e = (q+1) delta, and then the lines
     disjoint from any line L carry q(delta - e(L)) >= 0, so e <= delta.

 (b) THE PENCIL LEMMA AT q = 7.  For x = 1, 2, 3, every integer e with
     0 <= e <= x and A_L e = 6e + x.1 contains a full pencil (some point with
     e >= 1 on all eight of its lines). Each is an exact CP-SAT INFEASIBLE with
     a control, the same model without "no pencil", that must be feasible.
     Removing a pencil turns an x-tight set into an (x-1)-tight set, so by
     induction, for delta = 3,
            e  =  N^T y,     y >= 0 integer on points,     sum y = 3.

 (c) THE PATTERNS.  y is 3p, 2p+q or p+q+r. Each pattern fixes EVERY line
     count |B n L| = 1 + sum_{p in L} y_p, which is a small feasibility problem.
     Sp(4,7) is transitive on points and on collinear and on non-collinear
     pairs, and by Witt's theorem two triples of projective points lie in one
     orbit iff, after rescaling representatives, their Gram matrices and their
     linear relations agree. That splits r into 4 classes for a collinear pair
     (sizes 6, 49, 49, 294) and 7 for a non-collinear pair (3, 3, 8, 48, 48,
     144, 144), each count checked to total 398. Deciding one representative
     per class, together with 3p and the two orbits of 2p+q:
            every one of the 14 patterns is INFEASIBLE.
     A control, the octet pattern 5p at size 55, must be and is feasible.

 (d) SO NO 53-POINT BLOCKER EXISTS. And blocking is upward closed -- adding
     any point to a blocker gives a blocker -- so nothing smaller exists either.
     Hence tau_1(W(3,7)) >= 54, independently of the published bound, and the
     octet construction keeps tau_1 <= 55.

WHAT IT SAYS ABOUT THE CONJECTURE.  gq_diagonal_theorem.py (972e5cd) conjectured
tau_1(W(3,q)) = q^2 + q - 1 for odd q on the data 11 and 29. At q = 7 that is 55.
This result is CONSISTENT with it and moves the question to one number: does a
54-point blocker exist? It is not evidence for the conjecture beyond removing 53.

SCOPE.  The identity and the induction are argued; the three lemma instances,
the 14 pattern verdicts and the control are exact solver results; the orbit
classification rests on Witt's extension theorem (classical) and is checked by
the class sizes summing correctly. 54 is not decided here.
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
        S = set()
        for x in range(Q):
            for y in range(Q):
                if x or y:
                    S.add(idx[nm(tuple((x * pts[a][k] + y * pts[b][k]) % Q for k in range(4)))])
        lines.add(frozenset(S))
    lines = sorted(lines, key=sorted)
    assert n == 400 and len(lines) == 400 and all(len(L) == 8 for L in lines)
    return pts, n, lines, sf


def solver(budget):
    from ortools.sat.python import cp_model
    sv = cp_model.CpSolver()
    sv.parameters.num_workers = 8
    sv.parameters.max_time_in_seconds = budget
    return sv


def pencil_lemma(n, lines, budget):
    from ortools.sat.python import cp_model
    thru = [[j for j, L in enumerate(lines) if p in L] for p in range(n)]
    meet = [[k for k, M in enumerate(lines) if k != j and lines[j] & M] for j in range(n)]
    assert all(len(r) == Q * (Q + 1) for r in meet)
    pen = [1 if 0 in L else 0 for L in lines]
    one_tight = all(sum(pen[k] for k in meet[j]) == (Q - 1) * pen[j] + 1 for j in range(n))
    out = {}
    for x in (1, 2, 3):
        for mode in ("noPencil", "control"):
            m = cp_model.CpModel()
            e = [m.NewIntVar(0, x, "") for _ in range(n)]
            for j in range(n):
                m.Add(sum(e[k] for k in meet[j]) == (Q - 1) * e[j] + x)
            m.Add(e[0] >= 1)
            if mode == "noPencil":
                for p in range(n):
                    pos = []
                    for j in thru[p]:
                        b = m.NewBoolVar("")
                        m.Add(e[j] >= 1).OnlyEnforceIf(b)
                        m.Add(e[j] == 0).OnlyEnforceIf(b.Not())
                        pos.append(b)
                    m.Add(sum(pos) <= Q)
            sv = solver(budget)
            t0 = time.time()
            out["x%d_%s" % (x, mode)] = (sv.StatusName(sv.Solve(m)), round(time.time() - t0, 1))
    return one_tight, out


def pattern_test(n, lines, y, size, budget):
    from ortools.sat.python import cp_model
    m = cp_model.CpModel()
    x = [m.NewBoolVar("") for _ in range(n)]
    m.Add(sum(x) == size)
    delta = size - Q * Q - 1
    for L in lines:
        ex = sum(y.get(p, 0) for p in L)
        if ex > delta:
            return "INFEASIBLE"          # contradicts e <= delta from (a)
        m.Add(sum(x[i] for i in L) == 1 + ex)
    sv = solver(budget)
    return sv.StatusName(sv.Solve(m))


def witt_key(pts, sf, idxs):
    vs = [pts[i] for i in idxs]
    best = None
    for sc in itertools.product(range(1, Q), repeat=len(vs)):
        u = [tuple((s * c) % Q for c in v) for s, v in zip(sc, vs)]
        G = tuple(sf(u[i], u[j]) for i in range(len(u)) for j in range(len(u)))
        rel = tuple(sorted(x for x in itertools.product(range(Q), repeat=len(u))
                           if any(x) and all(sum(x[i] * u[i][k] for i in range(len(u))) % Q == 0
                                             for k in range(4))))
        k = (G, rel)
        if best is None or k < best:
            best = k
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--budget", type=float, default=1800.0)
    args = ap.parse_args()

    pts, n, lines, sf = geometry()

    def col(a, b):
        return sf(pts[a], pts[b]) == 0

    print("tau_1(W(3,7)) >= 54")
    print("=" * 74)
    one_tight, lemma = pencil_lemma(n, lines, args.budget)
    print("  (b) pencil lemma (a pencil is 1-tight: %s)" % one_tight)
    for k, v in lemma.items():
        print("        %-14s %s  %ss" % (k, v[0], v[1]))
    lemma_ok = one_tight and all(lemma["x%d_noPencil" % x][0] == "INFEASIBLE"
                                 and lemma["x%d_control" % x][0] in ("OPTIMAL", "FEASIBLE")
                                 for x in (1, 2, 3))

    p = 0
    qc = next(j for j in range(1, n) if col(p, j))
    qn = next(j for j in range(1, n) if not col(p, j))
    control = pattern_test(n, lines, {p: 5}, 55, 600)
    print("  CONTROL octet pattern 5p at size 55: %s" % control)
    rows = {"3p": pattern_test(n, lines, {p: 3}, 53, 600),
            "2p+q collinear": pattern_test(n, lines, {p: 2, qc: 1}, 53, 600),
            "2p+q noncollinear": pattern_test(n, lines, {p: 2, qn: 1}, 53, 600)}
    print("  (c) %s" % rows)
    classes = {}
    for q, lab in ((qc, "collinearPair"), (qn, "noncollinearPair")):
        cls = {}
        for r in range(n):
            if r not in (p, q):
                cls.setdefault(witt_key(pts, sf, [p, q, r]), []).append(r)
        res = []
        for members in cls.values():
            r = members[0]
            st = pattern_test(n, lines, {p: 1, q: 1, r: 1}, 53, 1800)
            res.append({"representative": r, "classSize": len(members), "status": st})
            print("      %-17s class size %3d -> %s" % (lab, len(members), st))
        classes[lab] = sorted(res, key=lambda t: t["classSize"])
    sizes_ok = (sorted(c["classSize"] for c in classes["collinearPair"]) == [6, 49, 49, 294]
                and sorted(c["classSize"] for c in classes["noncollinearPair"]) == [3, 3, 8, 48, 48, 144, 144])
    all_inf = (all(v == "INFEASIBLE" for v in rows.values())
               and all(c["status"] == "INFEASIBLE" for v in classes.values() for c in v))
    patterns = len(rows) + sum(len(v) for v in classes.values())

    ok = lemma_ok and control in ("OPTIMAL", "FEASIBLE") and sizes_ok and all_inf and patterns == 14
    print()
    print("  %d patterns, all INFEASIBLE: %s   class sizes as expected: %s" % (patterns, all_inf, sizes_ok))
    print("  => no 53-point blocker; blocking is upward closed; tau_1(W(3,7)) in [54, 55]")
    print()
    print("VALID: %s" % ok)

    if args.write:
        assert ok, "checks failed -- refusing to write"
        rec = {
            "schema": "holotrade.tau1-w37-at-least-54.v1",
            "valid": True,
            "q": Q, "points": n, "lines": len(lines),
            "interval": [54, 55], "previousInterval": [53, 55],
            "pencilIsOneTight": one_tight,
            "pencilLemma": {k: v[0] for k, v in lemma.items()},
            "pencilLemmaSeconds": {k: v[1] for k, v in lemma.items()},
            "controlOctetAt55": control,
            "patterns": rows,
            "tripleClasses": classes,
            "patternCount": patterns,
            "whereThisStood": (
                "the_minimality_fence_was_wrong.py (92124f1) narrowed tau_1(W(3,7)) to [53, 55] using the "
                "Eisfeld-Storme-Szonyi-Sziklai cover bound and the octet construction, and a direct CP-SAT "
                "attempt at 53 returned UNKNOWN after 2700 seconds."),
            "theCountingIdentity": (
                "for |B| = q^2+1+delta the excess e satisfies A_L e = (q-1)e + delta.1, a weighted delta-tight "
                "set of lines; summing gives sum e = (q+1)delta and lines disjoint from L carry q(delta - e(L)), "
                "so e <= delta."),
            "thePencilLemma": (
                "for x = 1, 2, 3 every 0 <= e <= x with A_L e = 6e + x.1 contains a full pencil (three INFEASIBLE "
                "verdicts with feasible controls); removing pencils gives e = N^T y, y >= 0, sum y = 3."),
            "thePatterns": (
                "3p, 2p+q (two pair orbits) and p+q+r, with r split into Sp(4,7)-orbit classes by Witt's theorem "
                "(Gram matrix and linear relation up to rescaling): 4 classes for a collinear pair and 7 for a "
                "non-collinear pair. Each pattern fixes every line count; all 14 are INFEASIBLE."),
            "upwardClosed": (
                "adding any point to a blocker gives a blocker, so no blocker of size <= 53 exists and "
                "tau_1(W(3,7)) >= 54 independently of the published bound; the octet construction gives <= 55."),
            "theConjecture": (
                "gq_diagonal_theorem.py (972e5cd) conjectured tau_1(W(3,q)) = q^2+q-1 for odd q, i.e. 55 here. "
                "This is consistent with it and reduces the question to whether a 54-point blocker exists; it is "
                "not further evidence for the conjecture."),
            "boundary": (
                "the identity and induction are argued; the lemma instances, pattern verdicts and control are exact "
                "solver results; the orbit classification rests on Witt's theorem and is checked by class sizes. "
                "54 is not decided."),
        }
        pth = os.path.join(ROOT, "data", "tau1_w37_at_least_54.json")
        with open(pth, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=2)
        print("written: %s" % pth)


if __name__ == "__main__":
    main()
