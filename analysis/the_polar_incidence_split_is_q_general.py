#!/usr/bin/env python3
"""
The parallel track's 24/15 polar-incidence split is q-general, with a closed
form for every one of its constants: (24,15) -> (q(q+1)^2/2, q(q^2+1)/2).

WHAT WAS SHOWN.  analysis/o5_polar_incidence_splits_the_w33_24_15_modules.py
(19cddc9) computes, for W(3,3), the isotropic-by-square incidence D and the
isotropic-by-nonsquare incidence C in O(5,3) and finds

    D D^T = 12I + 6J + 3A,   C C^T = 6I + 3J - 3A,   sum = 18I + 9J,
    D0 D0^T = 18 P_24,       C0 C0^T = 18 P_15,      N C = J,  N D = J + 3B,

concluding that point-line incidence annihilates the 15-dimensional nonsquare
sector and transmits the 24-dimensional square sector. Every number there is
exact, and every number there is q = 3.

THE TWO ORBITS ARE HYPERBOLIC AND ELLIPTIC SECTIONS.  A nonsingular point p of
PG(4,q) meets the quadric in p^perp cap Q(4,q), which is Q+(3,q) or Q-(3,q)
according to the square class of Q(p). Their own column weights say which is
which: 16 = (q+1)^2 = |Q+(3,q)| for the squares, 10 = q^2+1 = |Q-(3,q)| for the
nonsquares. An elliptic section has q^2+1 pairwise non-collinear points, i.e. it
is an OVOID of Q(4,q) -- dually a SPREAD of W(3,q). So "every nonsquare polar
section is a spread" is the classical elliptic-section fact and not a q = 3
accident. That is the reason the constants should close, and they do.

    q     v = (q+1)(q^2+1)   squares   nonsquares   w_D=(q+1)^2   w_C=q^2+1
    3            40             45          36           16           10
    5           156            325         300           36           26
    7           400           1225        1176           64           50

EVERY CONSTANT HAS A CLOSED FORM, VERIFIED AT q = 3, 5, 7.

    D D^T = q(q^2-1)/2 I + q(q+1)/2 J + q(q-1)/2 A
    C C^T = q(q-1)^2/2 I + q(q-1)/2 J - q(q-1)/2 A

              D D^T (I, J, A)          C C^T (I, J, A)
    q=3        12    6    3              6    3   -3
    q=5        60   15   10             40   10  -10
    q=7       168   28   21            126   21  -21

THE A-TERMS CANCEL AT EVERY q, EXACTLY.  c_D = -c_C = q(q-1)/2 identically, so

    D D^T + C C^T = q^2(q-1) I + q^2 J

with no A at all -- 18I + 9J is the q = 3 instance of that. The cancellation is
not a coincidence of one prime; it is an identity in q.

AND THE TIGHT-FRAME CONSTANT IS THE SAME FOR BOTH ORBITS, AT EVERY q:

    D0 D0^T = q^2(q-1) P_f,   rank D0 = f = q(q+1)^2/2
    C0 C0^T = q^2(q-1) P_g,   rank C0 = g = q(q^2+1)/2

    q     lambda = q^2(q-1)     f        g      f+g+1 = v
    3            18            24       15         40
    5           100            90       65        156
    7           294           224      175        400

f and g are exactly the two nontrivial eigenvalue multiplicities of the GQ(q,q)
collinearity graph SRG((q+1)(q^2+1), q(q+1), q-1, q+1). So the general statement
is: THE TWO NONSINGULAR O(5,q) ORBITS ARE TIGHT-FRAME REALIZATIONS OF THE TWO
NONTRIVIAL W(3,q) LINE-PERMUTATION MODULES, with the same frame constant
q^2(q-1). Their 18 was q^2(q-1) at q = 3, and the equality of their two 18s
across the two orbits was not an accident either.

THE TRANSMISSION LAW GENERALISES TOO.

    N C = J          at q = 3, 5, 7  (every nonsquare section is a spread)
    N D = J + q B    at q = 3, 5, 7  (entries are only 1 and q+1)
    column weight of B = 2(q+1):  8, 12, 16

So N C0 = 0 and N D0 = q B0 in general: incidence annihilates the g-dimensional
nonsquare sector and transmits the f-dimensional square sector, at every q
tested. Their 3 in "N D = J + 3B" is q, and their 8-axis K(4,4) support is the
2(q+1) points where a grid section is thick.

WHY 2(q+1) IS FORCED.  A section carries (q+1)^2 lines of q+1 points each, so
(q+1)^3 incidences over (q+1)(q^2+1) points. If the only multiplicities are 1
and q+1, then a thick points satisfy (q+1)a + (v - a) = (q+1)^3, giving
qa = (q+1)[(q+1)^2 - q^2 - 1] = 2q(q+1), so a = 2(q+1) with no freedom. The
count is forced; what is CHECKED here is that the multiplicities really are only
1 and q+1.

SCOPE.  q = 3, 5, 7 only. The closed forms are FITTED to three primes and then
verified against them, not proved -- three points determine these quadratics in
q uniquely, so agreement at three primes is consistency rather than proof, and a
fourth prime would be a real test. What IS proved here for each q tested is the
decomposition itself: D D^T and C C^T are checked ENTRYWISE against aI + bJ + cA
over the whole matrix, and the projector identities in exact integer arithmetic
scaled by v^2, not numerically. q even is untouched -- the square/nonsquare
split does not exist there -- and so is n > 2. Nothing here touches the
identification of the square orbit with a GQ, which stays q = 3 only (424111b),
or tau_2.
"""

import itertools
import json
import os
import sys

import numpy as np

ROOT = r"C:\Repos\Holotrade"
PAIR = ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3))


def study(q):
    def nm(v):
        i = next(k for k, x in enumerate(v) if x % q)
        z = pow(v[i] % q, -1, q)
        return tuple((z * x) % q for x in v)

    P3 = sorted({nm(v) for v in itertools.product(range(q), repeat=4) if any(v)})
    i3 = {p: i for i, p in enumerate(P3)}

    def sf(u, v):
        return (u[0] * v[2] - u[2] * v[0] + u[1] * v[3] - u[3] * v[1]) % q

    def wed(u, v):
        return tuple((u[i] * v[j] - u[j] * v[i]) % q for (i, j) in PAIR)

    lines = {}
    for a, b in itertools.combinations(P3, 2):
        if sf(a, b) % q:
            continue
        pts = set()
        for x in range(q):
            for y in range(q):
                if x or y:
                    w = tuple((x * a[k] + y * b[k]) % q for k in range(4))
                    if any(w):
                        pts.add(nm(w))
        lines.setdefault(nm(wed(a, b)), set()).update(pts)
    L = sorted(lines)

    def Qf(b):
        return (b[0] * b[5] - b[1] * b[4] + b[2] * b[3]) % q

    def nm6(b):
        i = next(k for k, x in enumerate(b) if x % q)
        z = pow(b[i] % q, -1, q)
        return tuple((z * x) % q for x in b)

    PW = sorted({nm6(b) for b in itertools.product(range(q), repeat=6)
                 if any(b) and (b[1] + b[4]) % q == 0})

    def Bf(u, v):
        s = tuple((u[i] + v[i]) % q for i in range(6))
        return (Qf(s) - Qf(u) - Qf(v)) % q

    sq = {(x * x) % q for x in range(1, q)}
    SQ = [b for b in PW if Qf(b) % q in sq]
    NS = [b for b in PW if Qf(b) % q and Qf(b) % q not in sq]
    assert {b for b in PW if Qf(b) % q == 0} == set(L)

    v = len(L)
    D = np.array([[1 if Bf(y, c) % q == 0 else 0 for c in SQ] for y in L],
                 dtype=np.int64)
    C = np.array([[1 if Bf(y, z) % q == 0 else 0 for z in NS] for y in L],
                 dtype=np.int64)
    A = np.array([[1 if (y != z and Bf(y, z) % q == 0) else 0 for z in L]
                  for y in L], dtype=np.int64)
    I = np.eye(v, dtype=np.int64)
    J = np.ones((v, v), dtype=np.int64)

    def decomp(M):
        oA = next((i, j) for i in range(v) for j in range(v)
                  if i != j and A[i, j])
        oN = next((i, j) for i in range(v) for j in range(v)
                  if i != j and not A[i, j])
        b = int(M[oN])
        c = int(M[oA]) - b
        a = int(M[0, 0]) - b
        return a, b, c, bool(np.array_equal(M, a * I + b * J + c * A))

    DD, CC = D @ D.T, C @ C.T
    aD, bD, cD, okD = decomp(DD)
    aC, bC, cC, okC = decomp(CC)

    fD = (q * (q * q - 1) // 2, q * (q + 1) // 2, q * (q - 1) // 2)
    fC = (q * (q - 1) ** 2 // 2, q * (q - 1) // 2, -(q * (q - 1) // 2))
    lam = q * q * (q - 1)
    f, g = q * (q + 1) ** 2 // 2, q * (q * q + 1) // 2

    def frame(M, n, w, sign):
        # M0 = M - (n w^2 / v^2) J, claimed equal to lam * P where
        # P = [ sign*A + e I + jc J/v ] / (2q).  The two eigenprojections carry
        # OPPOSITE-signed J terms: P_f has -(q+1)^2 J/v, P_g has +(q^2+1) J/v.
        # Scaled by v^2 throughout so the check is exact integer arithmetic.
        e = (q + 1) if sign > 0 else (q - 1)
        jc = -((q + 1) ** 2) if sign > 0 else (q * q + 1)
        lhs = M * v * v - n * w * w * J
        rhs = (lam // (2 * q)) * (sign * A * v * v + e * v * v * I + jc * v * J)
        return bool(np.array_equal(lhs, rhs))

    okFD = frame(DD, len(SQ), (q + 1) ** 2, +1)
    okFC = frame(CC, len(NS), q * q + 1, -1)

    D0 = D.astype(np.float64) - ((q + 1) ** 2) / v
    C0 = C.astype(np.float64) - (q * q + 1) / v
    rD, rC = int(np.linalg.matrix_rank(D0)), int(np.linalg.matrix_rank(C0))

    N = np.zeros((len(P3), v), dtype=np.int64)
    for li, lp in enumerate(L):
        for p in lines[lp]:
            N[i3[p], li] = 1
    ND, NC = N @ D, N @ C
    B = (ND - 1) // q
    okND = bool(np.array_equal(ND, np.ones_like(ND) + q * B))
    wB = sorted(set(B.sum(axis=0).tolist()))

    return {
        "q": q, "v": v, "squares": len(SQ), "nonsquares": len(NS),
        "wD": int(D[:, 0].sum()), "wC": int(C[:, 0].sum()),
        "srg": [v, q * (q + 1), q - 1, q + 1],
        "DD": [aD, bD, cD], "CC": [aC, bC, cC],
        "DDexact": okD, "CCexact": okC,
        "DDclosedForm": list(fD), "CCclosedForm": list(fC),
        "closedFormsMatch": ([aD, bD, cD] == list(fD)
                             and [aC, bC, cC] == list(fC)),
        "aTermsCancel": cD + cC == 0,
        "sumIJ": [aD + aC, bD + bC],
        "sumClosedForm": [q * q * (q - 1), q * q],
        "lambda": lam, "frameD": okFD, "frameC": okFC,
        "rankD0": rD, "rankC0": rC, "f": f, "g": g,
        "ranksAreMultiplicities": rD == f and rC == g and 1 + f + g == v,
        "NCisAllOnes": bool((NC == 1).all()),
        "NDvalues": sorted(set(ND.ravel().tolist())),
        "NDisJplusQB": okND, "columnWeightsOfB": wB,
        "forcedTwoQPlusTwo": wB == [2 * (q + 1)],
    }


def main():
    rows = [study(q) for q in (3, 5, 7)]

    print("THE POLAR-INCIDENCE SPLIT IS q-GENERAL")
    print("=" * 72)
    print("  19cddc9 proves the 24/15 split of W(3,3) by O(5,3) polar")
    print("  incidence. Every number in it is exact; every number is q = 3.")
    print()
    print("  The orbits are HYPERBOLIC and ELLIPTIC sections -- their own")
    print("  column weights say so, 16 = (q+1)^2 = |Q+(3,q)| and 10 = q^2+1 =")
    print("  |Q-(3,q)| -- and an elliptic section IS an ovoid, dually a spread.")
    print()
    print("     q       v   squares  nonsq    w_D    w_C")
    for r in rows:
        print("    %2d    %4d     %5d  %5d   %4d   %4d"
              % (r["q"], r["v"], r["squares"], r["nonsquares"],
                 r["wD"], r["wC"]))
    print()
    print("  D D^T = q(q^2-1)/2 I + q(q+1)/2 J + q(q-1)/2 A")
    print("  C C^T = q(q-1)^2/2 I + q(q-1)/2 J - q(q-1)/2 A")
    print("     q     D D^T (I,J,A)       C C^T (I,J,A)     closed form")
    for r in rows:
        print("    %2d    %5d %4d %4d     %5d %4d %4d       %s"
              % (r["q"], r["DD"][0], r["DD"][1], r["DD"][2],
                 r["CC"][0], r["CC"][1], r["CC"][2], r["closedFormsMatch"]))
    print()
    print("  THE A-TERMS CANCEL AT EVERY q -- c_D = -c_C = q(q-1)/2:")
    for r in rows:
        print("     q=%d:  D D^T + C C^T = %3d I + %2d J   (= q^2(q-1) I + q^2 J)"
              % (r["q"], r["sumIJ"][0], r["sumIJ"][1]))
    print("  18I + 9J is the q = 3 instance of an identity in q.")
    print()
    print("  AND THE FRAME CONSTANT IS SHARED BY BOTH ORBITS, AT EVERY q:")
    print("     q   lambda=q^2(q-1)      f      g   f+g+1    frames+ranks")
    for r in rows:
        print("    %2d         %4d         %4d   %4d    %4d        %s"
              % (r["q"], r["lambda"], r["f"], r["g"], 1 + r["f"] + r["g"],
                 r["ranksAreMultiplicities"] and r["frameD"] and r["frameC"]))
    print("  f and g are the two nontrivial multiplicities of")
    print("  SRG((q+1)(q^2+1), q(q+1), q-1, q+1). Their 18 was q^2(q-1), and")
    print("  the equality of their two 18s was not an accident either.")
    print()
    print("  TRANSMISSION GENERALISES: N C = J and N D = J + q B at all three")
    print("  primes, B of column weight 2(q+1) = %s."
          % [2 * (r["q"] + 1) for r in rows])
    print("  So N C0 = 0 and N D0 = q B0: incidence annihilates the g-sector")
    print("  and transmits the f-sector. Their 3 is q; their 8-axis K(4,4)")
    print("  support is the 2(q+1) points where a grid section is thick.")

    ok = all(r["DDexact"] and r["CCexact"] and r["closedFormsMatch"]
             and r["aTermsCancel"] and r["sumIJ"] == r["sumClosedForm"]
             and r["frameD"] and r["frameC"] and r["ranksAreMultiplicities"]
             and r["NCisAllOnes"] and r["NDisJplusQB"]
             and r["NDvalues"] == [1, r["q"] + 1] and r["forcedTwoQPlusTwo"]
             for r in rows)

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "polar_incidence_split_q_general.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.polar-incidence-q-general.v1",
                "valid": bool(ok),
                "extends": ("analysis/o5_polar_incidence_splits_the_w33_24_15_"
                            "modules.py (19cddc9), which proves the 24/15 split "
                            "of W(3,3) by O(5,3) polar incidence exactly and "
                            "entirely at q = 3"),
                "whyItShouldGeneralise": ("the two nonsingular orbits are the "
                                          "HYPERBOLIC and ELLIPTIC sections of "
                                          "Q(4,q): their own column weights say "
                                          "so, 16 = (q+1)^2 = |Q+(3,q)| for the "
                                          "squares and 10 = q^2+1 = |Q-(3,q)| for "
                                          "the nonsquares, and an elliptic "
                                          "section has q^2+1 pairwise "
                                          "non-collinear points, i.e. it is an "
                                          "OVOID of Q(4,q), dually a SPREAD of "
                                          "W(3,q). 'Every nonsquare polar section "
                                          "is a spread' is the classical "
                                          "elliptic-section fact, not a q = 3 "
                                          "accident"),
                "rows": rows,
                "closedForms": {
                    "DDT": "q(q^2-1)/2 I + q(q+1)/2 J + q(q-1)/2 A",
                    "CCT": "q(q-1)^2/2 I + q(q-1)/2 J - q(q-1)/2 A",
                    "sum": "q^2(q-1) I + q^2 J",
                    "frameConstant": "q^2(q-1), the SAME for both orbits",
                    "ranks": "f = q(q+1)^2/2 and g = q(q^2+1)/2",
                    "transmission": ("N C = J and N D = J + q B, with B of "
                                     "column weight 2(q+1)"),
                },
                "theATermsCancel": ("c_D = -c_C = q(q-1)/2 identically, so "
                                    "D D^T + C C^T = q^2(q-1) I + q^2 J with no A "
                                    "at all; 18I + 9J is the q = 3 instance of an "
                                    "identity in q, not a coincidence of one "
                                    "prime"),
                "theFrameConstantIsShared": ("q^2(q-1) is the frame constant for "
                                             "BOTH orbits at every q tested, so "
                                             "the equality of their two 18s was "
                                             "not an accident either"),
                "theGeneralStatement": ("the two nonsingular O(5,q) orbits are "
                                        "tight-frame realizations of the two "
                                        "nontrivial W(3,q) line-permutation "
                                        "modules, with the same frame constant "
                                        "q^2(q-1); f and g are exactly the "
                                        "nontrivial eigenvalue multiplicities of "
                                        "SRG((q+1)(q^2+1), q(q+1), q-1, q+1)"),
                "whyTwoQPlusTwoIsForced": ("a section carries (q+1)^2 lines of "
                                           "q+1 points, so (q+1)^3 incidences "
                                           "over (q+1)(q^2+1) points; if the only "
                                           "multiplicities are 1 and q+1 then "
                                           "qa = 2q(q+1) forces a = 2(q+1) with "
                                           "no freedom. The count is forced; what "
                                           "is CHECKED here is that the "
                                           "multiplicities really are only 1 and "
                                           "q+1"),
                "boundary": ("q = 3, 5, 7 only. The closed forms are FITTED to "
                             "three primes and then verified against them, not "
                             "proved -- three points determine these quadratics "
                             "in q uniquely, so agreement at three primes is "
                             "consistency rather than proof, and a fourth prime "
                             "would be a real test. What IS proved for each q "
                             "tested is the decomposition itself: D D^T and C C^T "
                             "are checked ENTRYWISE against aI + bJ + cA over the "
                             "whole matrix, and the projector identities in exact "
                             "integer arithmetic scaled by v^2, not numerically. "
                             "q even is untouched (the square/nonsquare split "
                             "does not exist there) and so is n > 2. Nothing here "
                             "touches the identification of the square orbit with "
                             "a GQ, which stays q = 3 only (424111b), or tau_2"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
