#!/usr/bin/env python3
"""
The two-step degradation 424111b recorded now has a mechanism: common
neighbours in the orthogonality graph are a function of the LINE TYPE alone,
they take only two values because a conic plane has only two point counts, and
the graph is strongly regular exactly at q = 3 and q = 5.

WHAT 424111b LEFT UNEXPLAINED.  It measured the perpendicularity graph on the
square O(5,q) orbit and found "a two-step degradation, not one": SRG(45,12,3,3)
and a quadrangle at q = 3, SRG(325,60,15,10) but no quadrangle at q = 5, and at
q = 7 not strongly regular at all -- 168-regular with lambda = [21] constant but
mu splitting into [21,28]. Three data points and no reason. Re-measured here in
a different model (Q = x0x1 + x2x3 + x4^2 rather than the Plucker one), all
three reproduce.

THE INVARIANT IS THE LINE TYPE.  Normalise Q to a fixed value t on the orbit --
t = 1 on the squares, a fixed nonsquare on the others -- which leaves only
u -> -u, so c = B(u,v) is well defined up to sign. Then
Q(au + bv) = t a^2 + abc + t b^2 has discriminant c^2 - 4t^2, so

    c^2 - 4t^2 a nonzero square  <=>  |<u,v> cap Q| = 2   (secant)
    c^2 - 4t^2 = 0               <=>  |<u,v> cap Q| = 1   (tangent)
    c^2 - 4t^2 a nonsquare       <=>  |<u,v> cap Q| = 0   (passant)

By Witt's extension theorem O(5,q) is transitive on pairs with a given Gram
matrix, so the (q+1)/2 folded values of c are exactly the orbitals. They form an
association scheme -- verified directly here, every intersection number
constant, on BOTH orbits at q = 3, 5, 7.

WHY THERE ARE EXACTLY TWO VALUES.  The common perpendicular neighbours of u and
v are the orbit points lying in the plane <u,v>^perp. That plane carries a
nondegenerate conic, so of its q^2 anisotropic points exactly q(q+1)/2 are of
one quadratic type and q(q-1)/2 of the other. There is no third count available,
and which type gets which is fixed by the discriminant of the plane -- that is,
by the line type of <u,v>. The two-valued law is forced by the conic, not fitted.

THE LAW.  For two points of the same orbit at folded angle c, the number of
common perpendicular neighbours is

    on the SQUARE orbit:      q(q+1)/2 if <u,v> is SECANT, else q(q-1)/2
    on the NONSQUARE orbit:   q(q-1)/2 if <u,v> is SECANT, else q(q+1)/2

-- the same law with the two values exchanged, which is what swapping the
quadratic type must do. Verified at eight primes on the square orbit, q = 3 to
23, the largest orbit carrying 140,185 points:

    q     n        hi=q(q+1)/2  lo=q(q-1)/2   values by class c = 0 .. (q-1)/2
    3       45          6            3        3 3
    5      325         15           10        15 10 10
    7     1225         28           21        21 28 21 21
   11     7381         66           55        55 55 55 66 66 55
   13    14365         91           78        91 91 78 78 91 78 78
   17    41905        153          136        153 136 136 136 136 153 153 136 153
   19    65341        190          171        171 190 171 190 171 171 171 190 171 190
   23   140185        276          253        253 253 253 253 276 253 276 253 253 276 276 276

53 numbers on the square orbit and 9 more on the nonsquare orbit at q = 3, 5, 7,
every one predicted from the square class of c^2 - 4t^2 alone, with no fitted
constant.

THE FUSION IS THE POINT.  The scheme SEPARATES tangent from passant; the
common-neighbour function does not -- they share a value, and only the secant
class differs. So the graph is strongly regular precisely when the secant type
does not occur among NON-perpendicular pairs, i.e. when no c in 1..(q-1)/2 has
c^2 - 4t^2 a nonzero square.

    q = 3:  the only off-diagonal class is c = 1, and 1 - 4 = 0 in F_3,
            tangent. Strong regularity is FREE -- there is nothing to fuse.  SRG
    q = 5:  c = 1 gives -3 = 2, a nonsquare (passant); c = 2 gives 0,
            tangent. Two genuinely DIFFERENT scheme classes landing on the
            same value -- a real fusion, not a degenerate case.               SRG
    q = 7:  c = 1 gives -3 = 4 = 2^2, a nonzero square. Secant appears off
            the diagonal and the mu values split, 28 against 21.          NOT SRG

and it never recovers: at every prime from 7 to 23 both types occur off the
diagonal. lambda obeys the same law at c = 0, where c^2 - 4t^2 = -4t^2 is a
square exactly when -1 is -- so lambda is q(q-1)/2 at q = 3, 7, 11, 19, 23 and
q(q+1)/2 at q = 5, 13, 17. The mod-4 alternation in lambda and the SRG break in
mu are one statement.

SO q = 5 IS NOT A SECOND ACCIDENT OF THE SAME KIND AS q = 3.  At q = 3 there is
one off-diagonal class and nothing to coincide. At q = 5 there are two, they are
different classes, and they fuse -- because there the secant solutions
c = (t^2 + 4)/(2t) all collapse onto c = 0, leaving the secant type confined to
the perpendicular class. That is the entire content of 424111b's "two-step"
observation, and it is arithmetic.

PRIOR ART, AND WHAT IS AND IS NOT CLAIMED.  The object is classical. Witt's
extension theorem gives the orbit structure, and Adriaensen and De Boeck,
"Association schemes and orthogonality graphs on anisotropic points of polar
spaces" (arXiv:2402.05055; Des. Codes Cryptogr. 2025), build the analogous
scheme on anisotropic points of ELLIPTIC and HYPERBOLIC quadrics for odd q --
indexed, as here, by the type of the line spanned together with the quadratic
type -- and state that they compute the spectrum of orthogonality graphs on
anisotropic points of non-degenerate quadrics in odd characteristic. Their
scheme sections cover elliptic and hyperbolic at odd q and parabolic only in
even characteristic, and the follow-up "Classification of Deza graphs from
anisotropic association schemes of quadrics" (arXiv:2608.20064) is explicitly
epsilon in {+,-} with no parabolic case. So the PARABOLIC odd-q graph studied
here is not the subject of either paper -- but its spectrum is plausibly covered
by, or immediate from, the first, and NO novelty is claimed for the scheme, for
the line-type indexing, or for the spectrum. What is claimed is narrow: the
explicit two-valued common-neighbour law with its conic reason, the
tangent-passant fusion that makes it two rather than three, the characterisation
SRG <=> q in {3,5} verified at eight primes, and the local use of turning
424111b's unexplained two-step degradation into a mechanism.

SCOPE.  q = 3, 5, 7 are EXACT and exhaustive on both orbits: every pair of
points is used, and the association-scheme property is checked by computing all
intersection numbers. q = 11 through 23 are SAMPLED -- 40 pairs per class, each
pair's count computed exactly against the whole orbit -- so constancy within a
class is evidence there rather than enumeration, with Witt's transitivity the
thing that upgrades it. SRG <=> q in {3,5} is verified for primes up to 23 and
is NOT proved beyond them, though the secant-solution argument says what would
have to fail. n = 2 and odd PRIME q only: no prime powers, no q even (where the
square/nonsquare split does not exist), no larger rank. Nothing here touches
tau_2, or the exterior-square correspondence, which is q-general for unrelated
reasons (64e6406).
"""

import itertools
import json
import os
import random
import sys

import numpy as np

ROOT = r"C:\Repos\Holotrade"
M5 = np.array([[0, 1, 0, 0, 0], [1, 0, 0, 0, 0], [0, 0, 0, 1, 0],
               [0, 0, 1, 0, 0], [0, 0, 0, 0, 2]], dtype=np.int64)


def orbit(q, which):
    rows = []
    for i in range(5):
        for m in range(q ** (4 - i)):
            v = [0] * i + [1]
            x = m
            for _ in range(4 - i):
                v.append(x % q)
                x //= q
            rows.append(v)
    P = np.array(rows, dtype=np.int64)
    Qv = (P[:, 0] * P[:, 1] + P[:, 2] * P[:, 3] + P[:, 4] ** 2) % q
    sq = {(x * x) % q for x in range(1, q)}
    keep = np.array([bool(x) and ((x in sq) == (which == "sq")) for x in Qv])
    V, Qs = P[keep], Qv[keep]
    tgt = 1 if which == "sq" else min(x for x in range(1, q) if x not in sq)
    W = np.array([(next(t for t in range(1, q) if (t * t * qq) % q == tgt) * v) % q
                  for v, qq in zip(V, Qs)], dtype=np.int64)
    return W


def bil(W, u, q):
    return (W[:, 0] * u[1] + W[:, 1] * u[0] + W[:, 2] * u[3]
            + W[:, 3] * u[2] + 2 * W[:, 4] * u[4]) % q


def target(q, which):
    """Q is normalised to this value on the orbit: 1, or a fixed nonsquare."""
    sq = {(x * x) % q for x in range(1, q)}
    return 1 if which == "sq" else min(x for x in range(1, q) if x not in sq)


def linetype(q, c, which="sq"):
    """0 passant, 1 tangent, 2 secant -- the classical |<u,v> cap Q|.

    With Q(u) = Q(v) = t on the orbit, Q(au+bv) = t a^2 + abc + t b^2, whose
    discriminant is c^2 - 4t^2.  For the square orbit t = 1 and this is the
    familiar c^2 - 4; for the nonsquare orbit the t must be carried.
    """
    sq = {(x * x) % q for x in range(1, q)}
    t = target(q, which)
    d = (c * c - 4 * t * t) % q
    return 1 if d == 0 else (2 if d in sq else 0)


def predict(q, c, which="sq"):
    """Common neighbours = points of the orbit's type in the plane <u,v>^perp.

    That plane carries a nondegenerate conic, so of its q^2 anisotropic points
    q(q+1)/2 have one type and q(q-1)/2 the other; which is which is fixed by
    the discriminant, i.e. by the line type -- and swaps with the orbit.
    """
    hi, lo = q * (q + 1) // 2, q * (q - 1) // 2
    return hi if (linetype(q, c, which) == 2) == (which == "sq") else lo


def exact(q, which):
    W = orbit(q, which)
    n = len(W)
    G = (W @ M5 @ W.T) % q
    Gf = np.minimum(G, (q - G) % q)
    np.fill_diagonal(Gf, -1)
    cls = list(range((q + 1) // 2))
    R = {c: (Gf == c).astype(np.int32) for c in cls}
    deg = {c: int(R[c].sum(1)[0]) for c in cls}
    degOK = all(len(set(R[c].sum(1).tolist())) == 1 for c in cls)
    isScheme = True
    for i in cls:
        for j in cls:
            Pij = R[i] @ R[j]
            for k in cls:
                if len(set(Pij[R[k].astype(bool)].tolist())) > 1:
                    isScheme = False
    CN = R[0] @ R[0]
    vals = {c: sorted(set(CN[R[c].astype(bool)].tolist())) for c in cls}
    lawOK = all(v == [predict(q, c, which)] for c, v in vals.items())
    return {"q": q, "orbit": which, "n": n, "degrees": deg,
            "degreesConstant": degOK, "isAssociationScheme": isScheme,
            "valuesByClass": {str(c): v for c, v in vals.items()},
            "predicted": {str(c): predict(q, c, which) for c in cls},
            "lineTypes": {str(c): linetype(q, c, which) for c in cls},
            "lawHolds": lawOK,
            "stronglyRegular": len({predict(q, c, which)
                                    for c in cls[1:]}) == 1,
            "exhaustive": True}


def sampled(q, npairs=40, seed=1):
    W = orbit(q, "sq")
    n = len(W)
    rnd = random.Random(seed)
    b0 = bil(W, W[0], q)
    A0 = (b0 == 0)
    cls = list(range((q + 1) // 2))
    got = {}
    for _ in range(npairs * q * 8):
        if all(len(got.get(k, [])) >= npairs for k in cls):
            break
        j = rnd.randrange(n)
        if j == 0:
            continue
        c = int(min(b0[j], (q - b0[j]) % q))
        if len(got.get(c, [])) >= npairs:
            continue
        got.setdefault(c, []).append(
            int(np.count_nonzero(A0 & (bil(W, W[j], q) == 0))))
    vals = {c: sorted(set(got.get(c, []))) for c in cls}
    lawOK = all(v == [predict(q, c)] for c, v in vals.items())
    return {"q": q, "orbit": "sq", "n": n,
            "valuesByClass": {str(c): v for c, v in vals.items()},
            "predicted": {str(c): predict(q, c) for c in cls},
            "lineTypes": {str(c): linetype(q, c) for c in cls},
            "lawHolds": lawOK, "pairsPerClass": npairs,
            "stronglyRegular": len({predict(q, c) for c in cls[1:]}) == 1,
            "exhaustive": False}


def main():
    ex = [exact(q, w) for q in (3, 5, 7) for w in ("sq", "ns")]
    sa = [sampled(q) for q in (11, 13, 17, 19, 23)]
    rows = [r for r in ex if r["orbit"] == "sq"] + sa

    print("THE SRG IS A TANGENT-PASSANT FUSION")
    print("=" * 72)
    print("  424111b called q = 3 / 5 / 7 'a two-step degradation, not one'")
    print("  and left it at three data points. Here is the mechanism.")
    print()
    print("  Normalise Q to t on the orbit (1 on the squares, a fixed")
    print("  nonsquare on the others); then c = B(u,v) is defined up to sign")
    print("  and Q(au+bv) = t a^2 + abc + t b^2 has discriminant c^2 - 4t^2,")
    print("  so c IS the line type: nonzero square = secant, 0 = tangent,")
    print("  nonsquare = passant.")
    print()
    print("  WHY ONLY TWO VALUES: the common neighbours of u,v are the orbit")
    print("  points of the plane <u,v>^perp, which carries a nondegenerate")
    print("  conic -- and a conic plane has exactly q(q+1)/2 anisotropic")
    print("  points of one type and q(q-1)/2 of the other. No third count")
    print("  exists. The law is forced by the conic, not fitted.")
    print()
    print("  THE LAW:  common perpendicular neighbours =")
    print("     squares:    q(q+1)/2 if SECANT, else q(q-1)/2")
    print("     nonsquares: q(q-1)/2 if SECANT, else q(q+1)/2")
    print("  the same law with the two values exchanged, as swapping the")
    print("  quadratic type must do.")
    print()
    print("    q       n     hi    lo   values by class c = 0 .. (q-1)/2")
    for r in rows:
        q = r["q"]
        vs = " ".join(str(r["valuesByClass"][str(c)][0])
                      for c in range((q + 1) // 2))
        print("   %2d  %6d   %4d  %4d   %s"
              % (q, r["n"], q * (q + 1) // 2, q * (q - 1) // 2, vs))
    tot = sum((r["q"] + 1) // 2 for r in rows)
    extra = sum((r["q"] + 1) // 2 for r in ex if r["orbit"] == "ns")
    print("  %d numbers here and %d more on the nonsquare orbit at q = 3,5,7,"
          % (tot, extra))
    print("  every one predicted from the square class of c^2 - 4t^2 alone,")
    print("  with no fitted constant: %s"
          % (all(r["lawHolds"] for r in rows) and all(r["lawHolds"]
                                                      for r in ex)))
    print()
    print("  THE FUSION IS THE POINT. The scheme separates tangent from")
    print("  passant; the common-neighbour function does not. So the graph is")
    print("  strongly regular exactly when SECANT never occurs off the")
    print("  perpendicular class:")
    for r in rows:
        q = r["q"]
        lt = [r["lineTypes"][str(c)] for c in range(1, (q + 1) // 2)]
        print("     q=%2d  off-diagonal line types %s   SRG=%s"
              % (q, lt, r["stronglyRegular"]))
    print()
    print("  q = 3 is free (one class). q = 5 is a GENUINE FUSION of two")
    print("  distinct classes, passant and tangent, onto one value. From")
    print("  q = 7 to 23 the secant type always appears and it never returns.")
    print("  lambda obeys the same law at c = 0, where c^2-4 = -4 is a square")
    print("  iff q = 1 mod 4 -- the mod-4 alternation in lambda and the SRG")
    print("  break in mu are one statement.")
    print()
    print("  PRIOR ART: the object is classical (Witt). Adriaensen-De Boeck,")
    print("  arXiv:2402.05055, build the analogous scheme for ELLIPTIC and")
    print("  HYPERBOLIC quadrics at odd q with the same line-type indexing.")
    print("  No novelty is claimed for the scheme or the spectrum -- only for")
    print("  the two-valued law, the fusion, and SRG <=> q in {3,5}.")

    ok = (all(r["lawHolds"] for r in rows)
          and all(r["isAssociationScheme"] and r["degreesConstant"] for r in ex)
          and all(r["lawHolds"] for r in ex)
          and [r["stronglyRegular"] for r in rows]
          == [True, True, False, False, False, False, False, False])

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "srg_is_a_tangent_passant_fusion.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.srg-tangent-passant-fusion.v1",
                "valid": bool(ok),
                "whatWasUnexplained": ("424111b measured SRG(45,12,3,3) and a "
                                       "quadrangle at q = 3, SRG(325,60,15,10) "
                                       "and no quadrangle at q = 5, and no "
                                       "strong regularity at q = 7 (lambda = "
                                       "[21] constant, mu splitting [21,28]), "
                                       "calling it 'a two-step degradation, not "
                                       "one'. That was three data points and no "
                                       "reason"),
                "reproducedInASecondModel": ("re-measured here with "
                                             "Q = x0x1 + x2x3 + x4^2 instead of "
                                             "the Plucker model, and all three "
                                             "reproduce"),
                "theInvariantIsTheLineType": ("normalise Q to t on the orbit -- "
                                              "1 on the squares, a fixed nonsquare "
                                              "on the others -- which leaves only "
                                              "u -> -u, so c = B(u,v) is defined "
                                              "up to sign; "
                                              "Q(au+bv) = t a^2 + abc + t b^2 has "
                                              "discriminant c^2 - 4t^2, hence "
                                              "c^2 - 4t^2 a nonzero square means "
                                              "SECANT, zero means TANGENT and a "
                                              "nonsquare means PASSANT -- the "
                                              "classical |<u,v> cap Q| in {2,1,0}"),
                "whyExactlyTwoValues": ("the common perpendicular neighbours of u "
                                        "and v are the orbit points lying in the "
                                        "plane <u,v>^perp, which carries a "
                                        "nondegenerate conic; of its q^2 "
                                        "anisotropic points exactly q(q+1)/2 have "
                                        "one quadratic type and q(q-1)/2 the "
                                        "other, so no third count is available "
                                        "and which type gets which is fixed by "
                                        "the discriminant of the plane, i.e. by "
                                        "the line type. The two-valued law is "
                                        "FORCED by the conic, not fitted"),
                "theLaw": ("on the SQUARE orbit the number of common "
                           "perpendicular neighbours is q(q+1)/2 if <u,v> is a "
                           "secant and q(q-1)/2 if it is tangent or passant; on "
                           "the NONSQUARE orbit it is the same law with the two "
                           "values EXCHANGED, which is what swapping the "
                           "quadratic type must do. Two values, never three"),
                "theFusion": ("the association scheme SEPARATES tangent from "
                              "passant but the common-neighbour function does "
                              "not -- both give q(q-1)/2, and only the secant "
                              "class differs. That fusion is why the graph can "
                              "be strongly regular at all"),
                "srgCharacterisation": ("strongly regular exactly when the secant "
                                        "type does not occur off the "
                                        "perpendicular class, i.e. when no c in "
                                        "1..(q-1)/2 has c^2-4 a nonzero square: "
                                        "true at q = 3 (one class, and 1-4 = 0 in "
                                        "F_3) and q = 5 (c=1 passant, c=2 "
                                        "tangent, a GENUINE fusion of two "
                                        "distinct classes), false at every prime "
                                        "from 7 to 23"),
                "lambdaObeysTheSameLaw": ("at c = 0, c^2-4 = -4 is a square "
                                          "exactly when q = 1 mod 4, so lambda is "
                                          "q(q-1)/2 at q = 3,7,11,19,23 and "
                                          "q(q+1)/2 at q = 5,13,17; the mod-4 "
                                          "alternation in lambda and the SRG "
                                          "break in mu are the same statement"),
                "whyQ5IsNotASecondAccidentOfTheSameKind": ("at q = 3 there is one "
                                                           "off-diagonal class and "
                                                           "strong regularity is "
                                                           "free; at q = 5 there "
                                                           "are two genuinely "
                                                           "different classes that "
                                                           "fuse, because the "
                                                           "secant solutions "
                                                           "c = (t^2+4)/(2t) all "
                                                           "collapse onto c = 0 "
                                                           "there"),
                "exactRows": ex,
                "sampledRows": sa,
                "exhaustiveCorroborationAtQ11": {
                    "provenance": ("computed by a SEPARATE longer run, not by "
                                   "this file, which samples at q = 11 to stay "
                                   "cheap: all 7381*7380/2 pairs on the square "
                                   "orbit and all 7260*7259/2 on the nonsquare, "
                                   "with common neighbours from the full "
                                   "adjacency product rather than per-pair"),
                    "square": {"n": 7381, "degree": 660, "lambda": [55],
                               "mu": [55, 66], "stronglyRegular": False},
                    "nonsquare": {"n": 7260, "degree": 671, "lambda": [66],
                                  "mu": [55, 66], "stronglyRegular": False},
                    "agreesWithTheLaw": ("both orbits take only the two conic "
                                         "counts q(q+1)/2 = 66 and q(q-1)/2 = 55, "
                                         "lambda is 55 on the squares and 66 on "
                                         "the nonsquares -- the roles exchanged, "
                                         "as the law requires -- and mu splits on "
                                         "both, so q = 11 is NOT strongly regular "
                                         "exhaustively and not merely on a "
                                         "sample"),
                    "upgradesTheSampledRow": ("the q = 11 sampled row in "
                                              "sampledRows reports the same "
                                              "values; this raises it from "
                                              "evidence to enumeration for that "
                                              "prime, on both orbits"),
                },
                "priorArt": ("the object is classical: Witt's extension theorem "
                             "gives the orbit structure, and Adriaensen and De "
                             "Boeck, 'Association schemes and orthogonality "
                             "graphs on anisotropic points of polar spaces' "
                             "(arXiv:2402.05055; Des. Codes Cryptogr. 2025), "
                             "build the analogous scheme on anisotropic points of "
                             "ELLIPTIC and HYPERBOLIC quadrics for odd q with the "
                             "same line-type indexing, and state that they "
                             "compute the spectrum of orthogonality graphs on "
                             "anisotropic points of non-degenerate quadrics in "
                             "odd characteristic. Their scheme sections cover "
                             "elliptic and hyperbolic at odd q and parabolic only "
                             "in even characteristic, and the follow-up "
                             "arXiv:2608.20064 is explicitly epsilon in {+,-} "
                             "with no parabolic case, so the parabolic odd-q "
                             "graph here is not the subject of either -- but its "
                             "spectrum is plausibly covered by or immediate from "
                             "the first"),
                "whatIsClaimed": ("NOT the scheme, NOT the line-type indexing and "
                                  "NOT the spectrum. Only the explicit two-valued "
                                  "common-neighbour law, the tangent-passant "
                                  "fusion that makes it two rather than three, "
                                  "the characterisation SRG <=> q in {3,5} "
                                  "verified at eight primes, and the local use of "
                                  "turning 424111b's unexplained two-step "
                                  "degradation into a mechanism"),
                "boundary": ("q = 3, 5, 7 are EXACT and exhaustive on BOTH "
                             "orbits -- every pair of points is used, and the "
                             "association-scheme property is checked by "
                             "computing all intersection numbers. q = 11 through "
                             "23 are SAMPLED at 40 pairs per class, each pair's "
                             "count computed exactly against the whole orbit, so "
                             "constancy within a class is evidence there rather "
                             "than enumeration, with Witt's transitivity the "
                             "thing that upgrades it. SRG <=> q in {3,5} is "
                             "verified for primes up to 23 and is NOT proved "
                             "beyond them, though the secant-solution argument "
                             "says what would have to fail. n = 2 and odd PRIME q "
                             "only: no prime powers, no q even (where the "
                             "square/nonsquare split does not exist), no larger "
                             "rank. Nothing here touches tau_2, or the "
                             "exterior-square correspondence, which is q-general "
                             "for unrelated reasons (64e6406)"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
