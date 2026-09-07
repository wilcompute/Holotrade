#!/usr/bin/env python3
"""
Correcting eb6cfe8 and finishing it: the 40 isotropic points are W(3,3)'s
LINES, not its points -- and the 36 nonsquare points ARE the 36 spreads.
All three legs now equivariant.

THE CORRECTION.  eb6cfe8 stated the partition 121 = 40 + 45 + 36 of PG(4,3)
and labelled the isotropic class "the points of W(3,3) = the CHEAP opcodes".
That is wrong. Under the exterior-square isomorphism Sp(4,q) -> O(5,q), a point
of the O(5,q) space is a bivector, and an ISOTROPIC one is a decomposable
bivector -- a LINE of PG(3,q). Restricted to the omega-hyperplane those are the
totally isotropic lines, i.e. the LINES of W(3,q). Built explicitly:

    equivariant  isotropic class -> W(3,3) POINTS      False
    equivariant  isotropic class -> W(3,3) LINES       True

AND THE INVARIANTS COULD NOT HAVE CAUGHT IT.

    subdegrees on the 40 isotropic points   [1, 12, 27]
    subdegrees on W(3,3) POINTS             [1, 12, 27]
    subdegrees on W(3,3) LINES              [1, 12, 27]

All three identical. Subdegrees, rank, degree, orbit size -- every invariant
this repository has been using as evidence -- agree for BOTH candidates, and
only the explicit equivariant map separates them. 8982d36 and f04eec3 built
their maps after using subdegrees as evidence; this is the case that shows why
that order matters, because here the evidence points at two answers and one of
them is false.

THE LAST LEG, NOW PROVED.  eb6cfe8 left the 36 as a COUNT MATCH ONLY:

    subdegrees on the 36 nonsquare points   [1, 15, 20]
    subdegrees on the 36 spreads            [1, 15, 20]
    equivariant bijection                   yes
    intertwines all 80 generators           yes

So the nonsquare class IS the spread set.

THE CORRECTED PARTITION, ALL THREE LEGS EQUIVARIANT.

    PG(4,3), 121 points, cut by the quadratic form:

        40  isotropic    = the LINES of W(3,3)             proved here
        45  square       = the expensive instructions      proved in eb6cfe8
        36  nonsquare    = the 36 spreads                  proved here

and the fast-path opcode axes -- the POINTS of W(3,3) -- are NOT the isotropic
class but its DUAL. W(3,q) for odd q is not self-dual, so points and lines are
genuinely different PSp-sets of the same size with the same subdegrees, and the
machine's instruction index sits on the other side of that duality from the
isotropic class. The three-way partition is still the right picture; the label
on its first part was wrong.

WHAT SURVIVES UNCHANGED.  The counting identity at q = 3, 5, 7; the explicit
isomorphism from the cost anomalies onto the square class; the reading that
anticommutation in Sp is perpendicularity in O(5,q); and the explanation of the
closed forms as orthogonal-group orbit sizes and of the q-collapse as the NO
family losing strong regularity. None of those touched the mislabelled leg.

SCOPE.  The isomorphism Sp(4,q) -> O(5,q) is built explicitly here as the
exterior square: Lambda^2 of the 4-space, restricted to the kernel of the
symplectic functional (5-dimensional), with the Pfaffian as the quadratic form,
which a symplectic matrix preserves because its determinant is 1. Both new
equivariant bijections are verified against every one of the 80 transvection
generators, not sampled. The refutation of "isotropic = points" is a failed
exhaustive search over all 40 possible base-point choices, not a failure to find
one by luck. Only q = 3 is done here. tau_2 is untouched.
"""

import collections
import itertools
import json
import os
import sys

ROOT = r"C:\Repos\Holotrade"
Q = 3
D = 4
PAIR = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]


def main():
    def mul(A, B):
        return tuple(tuple(sum(A[i][k] * B[k][j] for k in range(D)) % Q
                           for j in range(D)) for i in range(D))

    I = tuple(tuple(1 if i == j else 0 for j in range(D)) for i in range(D))

    def form(u, v):
        return (u[0] * v[2] - u[2] * v[0] + u[1] * v[3] - u[3] * v[1]) % Q

    E = [tuple(1 if k == j else 0 for k in range(D)) for j in range(D)]

    def tv(vv, lam):
        return tuple(tuple(((1 if i == j else 0)
                            + lam * form(E[j], vv) * vv[i]) % Q
                           for j in range(D)) for i in range(D))

    vecs = [v for v in itertools.product(range(Q), repeat=D) if any(v)]
    T = sorted({tv(v, l) for v in vecs for l in (1, 2)} - {I})

    def wedge(g):
        M = [[0] * 6 for _ in range(6)]
        for c, (i, j) in enumerate(PAIR):
            for r, (k, l) in enumerate(PAIR):
                M[r][c] = (g[k][i] * g[l][j] - g[l][i] * g[k][j]) % Q
        return M

    def inW(b):
        return (b[1] + b[4]) % Q == 0

    def Qf(b):
        return (b[0] * b[5] - b[1] * b[4] + b[2] * b[3]) % Q

    def nm6(b):
        i = next(k for k, x in enumerate(b) if x % Q)
        z = pow(b[i] % Q, -1, Q)
        return tuple((z * x) % Q for x in b)

    P6 = sorted({nm6(b) for b in itertools.product(range(Q), repeat=6)
                 if any(b) and inW(b)})
    sqset = {(x * x) % Q for x in range(1, Q)}
    ISO = [b for b in P6 if Qf(b) % Q == 0]
    SQ = [b for b in P6 if Qf(b) % Q in sqset]
    NS = [b for b in P6 if Qf(b) % Q and Qf(b) % Q not in sqset]

    def actP6(g, S):
        M = wedge(g)
        idx = {b: i for i, b in enumerate(S)}
        return tuple(idx[nm6(tuple(sum(M[r][c] * b[c] for c in range(6)) % Q
                                   for r in range(6)))] for b in S)

    def nm4(v):
        i = next(k for k, x in enumerate(v) if x % Q)
        z = pow(v[i] % Q, -1, Q)
        return tuple((z * x) % Q for x in v)

    pts = sorted({nm4(v) for v in vecs})
    pidx = {p: i for i, p in enumerate(pts)}
    wl = set()
    for a, b in itertools.combinations(pts, 2):
        if form(a, b) % Q:
            continue
        S = set()
        for x in range(Q):
            for y in range(Q):
                if x == y == 0:
                    continue
                w = tuple((x * a[k] + y * b[k]) % Q for k in range(D))
                if any(w):
                    S.add(nm4(w))
        if len(S) == 4 and all(form(u, v) % Q == 0
                               for u, v in itertools.combinations(sorted(S), 2)):
            wl.add(frozenset(pidx[z] for z in S))
    WL = sorted(map(sorted, wl))
    NL = len(WL)
    WLi = {frozenset(l): i for i, l in enumerate(WL)}

    def actPts(g):
        return tuple(pidx[nm4(tuple(sum(g[i][k] * p[k] for k in range(D)) % Q
                                    for i in range(D)))] for p in pts)

    def actLines(g):
        pp = actPts(g)
        return tuple(WLi[frozenset(pp[x] for x in WL[k])] for k in range(NL))

    spreads = []

    def spd(ch, used):
        if len(used) == 40:
            spreads.append(frozenset(ch))
            return
        rem = [p for p in range(40) if p not in used]
        if not rem:
            return
        p = rem[0]
        for k in range(NL):
            if p in WL[k] and not (set(WL[k]) & used):
                spd(ch + [k], used | set(WL[k]))

    spd([], set())
    Sidx = {s: i for i, s in enumerate(spreads)}

    aISO = [actP6(g, ISO) for g in T]
    aNS = [actP6(g, NS) for g in T]
    aPTS = [actPts(g) for g in T]
    aLIN = [actLines(g) for g in T]
    aSP = []
    for g in T:
        lp = actLines(g)
        aSP.append(tuple(Sidx[frozenset(lp[k] for k in s)] for s in spreads))

    def subdeg(acts, n):
        out, cov = [], set()
        for b in range(n):
            if b in cov:
                continue
            S, fr = {(0, b)}, [(0, b)]
            while fr:
                nx = []
                for (x, y) in fr:
                    for p in acts:
                        z = (p[x], p[y])
                        if z not in S:
                            S.add(z)
                            nx.append(z)
                fr = nx
            blk = {y for (x, y) in S if x == 0}
            out.append(len(blk))
            cov |= blk
        return sorted(out)

    def equivar(A, B, n):
        for b0 in range(n):
            cand, fr, good = {0: b0}, [0], True
            while fr and good:
                nx = []
                for a in fr:
                    for k in range(len(A)):
                        a2, b2 = A[k][a], B[k][cand[a]]
                        if a2 in cand:
                            if cand[a2] != b2:
                                good = False
                                break
                        else:
                            cand[a2] = b2
                            nx.append(a2)
                    if not good:
                        break
                fr = nx
            if good and len(cand) == n and len(set(cand.values())) == n:
                return cand
        return None

    sd_iso, sd_pts, sd_lin = (subdeg(aISO, 40), subdeg(aPTS, 40),
                              subdeg(aLIN, 40))
    to_pts = equivar(aISO, aPTS, 40)
    to_lin = equivar(aISO, aLIN, 40)
    sd_ns, sd_sp = subdeg(aNS, 36), subdeg(aSP, 36)
    to_sp = equivar(aNS, aSP, 36)
    sp_ok = to_sp is not None and all(
        to_sp[aNS[k][a]] == aSP[k][to_sp[a]]
        for k in range(len(aNS)) for a in range(36))

    print("THE PARTITION IS LINES, NOT POINTS")
    print("=" * 72)
    print("  PG(4,3): %d points = %d isotropic + %d square + %d nonsquare"
          % (len(P6), len(ISO), len(SQ), len(NS)))
    print()
    print("  CORRECTION to eb6cfe8, which called the isotropic class")
    print("  'the points of W(3,3)':")
    print("     equivariant  isotropic -> W(3,3) POINTS    %s"
          % (to_pts is not None))
    print("     equivariant  isotropic -> W(3,3) LINES     %s"
          % (to_lin is not None))
    print()
    print("  AND THE INVARIANTS COULD NOT HAVE CAUGHT IT:")
    print("     subdegrees, 40 isotropic points   %s" % sd_iso)
    print("     subdegrees, W(3,3) POINTS         %s" % sd_pts)
    print("     subdegrees, W(3,3) LINES          %s" % sd_lin)
    print("     all three identical -- only the explicit map separates them.")
    print()
    print("  THE LAST LEG, NOW PROVED:")
    print("     subdegrees, 36 nonsquare points   %s" % sd_ns)
    print("     subdegrees, 36 spreads            %s" % sd_sp)
    print("     equivariant bijection             %s" % (to_sp is not None))
    print("     intertwines all %d generators      %s" % (len(aNS), sp_ok))
    print()
    print("  CORRECTED PARTITION, all three legs equivariant:")
    print("     40  isotropic  = the LINES of W(3,3)         proved here")
    print("     45  square     = the expensive instructions  eb6cfe8")
    print("     36  nonsquare  = the 36 spreads              proved here")
    print()
    print("  The fast-path opcode axes are the POINTS of W(3,3), which are NOT")
    print("  the isotropic class but its DUAL: W(3,q) is not self-dual at odd")
    print("  q, so points and lines are different PSp-sets of the same size")
    print("  with the same subdegrees. The picture stands; the first label")
    print("  was wrong.")

    ok = (len(P6) == 121 and len(ISO) == 40 and len(SQ) == 45
          and len(NS) == 36 and to_pts is None and to_lin is not None
          and sd_iso == sd_pts == sd_lin == [1, 12, 27]
          and sd_ns == sd_sp == [1, 15, 20] and sp_ok and len(spreads) == 36)

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "partition_is_lines_not_points.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.partition-is-lines-not-points.v1",
                "valid": bool(ok),
                "correction": {
                    "of": "eb6cfe8",
                    "whatItSaid": ("labelled the isotropic class 'the points of "
                                   "W(3,3) = the CHEAP opcodes'"),
                    "whyItIsWrong": ("under the exterior-square isomorphism an "
                                     "ISOTROPIC point of the O(5,q) space is a "
                                     "decomposable bivector, i.e. a LINE of "
                                     "PG(3,q); restricted to the omega-"
                                     "hyperplane those are the LINES of W(3,q)"),
                    "equivariantToPoints": to_pts is not None,
                    "equivariantToLines": to_lin is not None,
                },
                "invariantsCouldNotCatchIt": {
                    "subdegreesIsotropic": sd_iso,
                    "subdegreesW33Points": sd_pts,
                    "subdegreesW33Lines": sd_lin,
                    "allIdentical": sd_iso == sd_pts == sd_lin,
                    "lesson": ("subdegrees, rank, degree and orbit size -- every "
                               "invariant this repository has been using as "
                               "evidence -- agree for BOTH candidates, and only "
                               "the explicit equivariant map separates them. "
                               "Here the evidence points at two answers and one "
                               "is false"),
                },
                "lastLegProved": {
                    "subdegreesNonsquare": sd_ns,
                    "subdegreesSpreads": sd_sp,
                    "equivariantBijection": to_sp is not None,
                    "intertwinesAllGenerators": bool(sp_ok),
                    "generators": len(aNS),
                    "wasPreviously": "a COUNT MATCH ONLY in eb6cfe8",
                },
                "correctedPartition": {
                    "total": len(P6),
                    "isotropic": {"count": len(ISO),
                                  "is": "the LINES of W(3,3)",
                                  "status": "proved here"},
                    "square": {"count": len(SQ),
                               "is": "the expensive instructions",
                               "status": "proved in eb6cfe8"},
                    "nonsquare": {"count": len(NS), "is": "the 36 spreads",
                                  "status": "proved here"},
                    "whereTheOpcodesSit": ("the fast-path opcode axes are the "
                                           "POINTS of W(3,3), which are NOT the "
                                           "isotropic class but its DUAL; "
                                           "W(3,q) is not self-dual at odd q, so "
                                           "points and lines are different "
                                           "PSp-sets of the same size with the "
                                           "same subdegrees"),
                },
                "whatSurvivesUnchanged": ("the counting identity at q = 3, 5, 7; "
                                          "the explicit isomorphism from the "
                                          "cost anomalies onto the square class; "
                                          "the reading that anticommutation in "
                                          "Sp is perpendicularity in O(5,q); and "
                                          "the explanation of the closed forms "
                                          "as orbit sizes and of the q-collapse "
                                          "as the NO family losing strong "
                                          "regularity -- none of those touched "
                                          "the mislabelled leg"),
                "boundary": ("the isomorphism Sp(4,q) -> O(5,q) is built "
                             "explicitly as the exterior square: Lambda^2 of the "
                             "4-space restricted to the kernel of the symplectic "
                             "functional, with the Pfaffian as quadratic form, "
                             "preserved because a symplectic matrix has "
                             "determinant 1. Both new bijections are verified "
                             "against every one of the 80 generators, not "
                             "sampled. The refutation of 'isotropic = points' is "
                             "a failed EXHAUSTIVE search over all 40 base-point "
                             "choices, not a failure to find one by luck. Only "
                             "q = 3 is done here. tau_2 is untouched"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
