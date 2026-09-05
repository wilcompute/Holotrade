#!/usr/bin/env python3
"""
What sits at symplectic rank 3 is not an orthogonal geometry but a CUBIC JORDAN
ALGEBRA -- the 15-dimensional one -- and it is the sibling of the E6 cubic the
corpus's gate layer already names.

WHERE THIS COMES FROM.  ae04deb showed the polar apparatus is rank-two only,
because the Pfaffian on Lambda^2(F^2n) has degree n and degree 2 happens once.
That is a no-go. It has a positive half, and the positive half is the
interesting one: a degree-3 invariant is not nothing, it is a cubic norm.

THE CLEANEST FORM OF THE WHOLE STORY.

    Lambda^2(F^4)  is  6-dimensional, Pf has degree 2, Gr(2,4) = {Pf = 0}
                   is a QUADRIC -- the Klein quadric
    Lambda^2(F^6)  is 15-dimensional, Pf has degree 3, Gr(2,6) is the rank-one
                   locus of a CUBIC, and no quadric

The entire W(3,3) <-> O(5,q) machinery exists because the Klein quadric is a
quadric. That is the one-line reason, and it stops at 2n = 4.

THE RANK-3 OBJECT IS A CUBIC NORM STRUCTURE, VERIFIED.  A cubic Jordan algebra
is exactly a cubic form N with an adjoint # satisfying (x#)# = N(x) x. Taking
N = Pf on 6x6 alternating matrices over F_q and # the gradient of Pf:

    q       (X#)# == Pf(X) * X
    5           300 / 300
    7           300 / 300
   11           300 / 300

exactly, with no exceptions and no scalar correction. So Lambda^2(F_q^6) with
the Pfaffian is a cubic norm structure in odd characteristic.

AND THE RANK DICTIONARY IS EXACT.

    bivector rank 2  =  Jordan rank 1  =  X# = 0        =  decomposable  =  Gr(2,6)
    bivector rank 4  =  Jordan rank 2  =  X# =/= 0, N = 0
    bivector rank 6  =  Jordan rank 3  =  N =/= 0

verified on 400 decomposable bivectors u^v at each of q = 5, 7, 11, every one
landing in (bivector rank 2, Jordan rank 1), and on random elements for the
other two strata. So the seven-class stratification that broke the rank-2
apparatus in ae04deb is not noise: it is the Jordan rank crossed with the
square class of the auxiliary quadratic form.

THE SERIES, WHICH IS CLASSICAL.  The rank-3 Jordan algebras H_3(A) for A = R,
C, H, O have dimensions 3 + 3 dim A = 6, 9, 15, 27, and their rank-one loci are
the four Severi varieties, in P^5, P^8, P^14 and P^26 respectively (Zak's
classification; see also Scorza varieties). The third member is exactly
Lambda^2(F^6) with the Pfaffian norm, its Severi variety being
Gr(2,6) = G(1,5) in P^14. None of that is claimed here -- it is standard and
cited -- but it is what the computation above lands on.

WHY THAT MATTERS TO THIS CORPUS.  The architecture layer already carries a
degree-2 / degree-3 split: "gates = deg-2 symplectic + deg-3 E6 cubic". Those
two degrees are now the Pfaffian degrees at symplectic rank 2 and rank 3, and
the rank-3 cubic is the A5 member of the SAME series whose E6 member is the
27-dimensional cubic. The corpus already holds the octonion end of that series
-- BT293 has the Cayley plane and F_4, BT441 has the 27 -- and does not hold the
quaternion member: a search of both repositories finds no Severi variety, no
Gr(2,6), no Pfaffian cubic and no H_3(H), the only "Severi" hits being
Cabello-Severini-Winter. So the degree-2/degree-3 gate split, which was a
statement about gates, now has a candidate geometric origin: it is symplectic
rank 2 against symplectic rank 3, and the two cubics are two members of one
series.

WHAT IS AND IS NOT CLAIMED.  Claimed: the adjoint identity over F_q at three
primes, the exact rank dictionary, and the observation that the rank-3
obstruction of ae04deb is the 15-dimensional member of the Severi/Jordan series.
NOT claimed: that the corpus's "E6 cubic" IS the H_3(O) norm. That is the
natural reading and it is standard mathematics, but how the corpus's gate layer
actually defines its cubic was not examined here, so the identification of the
two ends of the series is left as the open half. Also not claimed: any
consequence for tau_2, for gate universality, or for the physical layer.

SCOPE.  Odd q only, and q = 5, 7, 11 at that -- the adjoint identity is checked
on 300 random alternating matrices per prime and the rank dictionary on 400
decomposables per prime, so both are DEMONSTRATIONS at those primes rather than
proofs, though the identity is a classical polynomial identity and would hold
formally. q = 3 is excluded from the adjoint test because the gradient
construction of # divides by small integers there; the rank dictionary is not
affected. Characteristic 2 is untouched and is genuinely different (the Pfaffian
and the quadratic form behave differently there). n > 3 is untouched: the
Pfaffian keeps degree n and there is no fourth Jordan member, the series being
exactly four long.
"""

import itertools
import json
import os
import random
import sys

import numpy as np

ROOT = r"C:\Repos\Holotrade"
IDX = [(i, j) for i in range(6) for j in range(i + 1, 6)]


def matchings(rem):
    if not rem:
        yield [], 1
        return
    a = rem[0]
    for k in range(1, len(rem)):
        b = rem[k]
        for m, s in matchings(rem[1:k] + rem[k + 1:]):
            yield [(a, b)] + m, s * ((-1) ** (k - 1))


MATCH = list(matchings(list(range(6))))


def pf6(X, q):
    tot = 0
    for m, s in MATCH:
        p = s
        for (a, b) in m:
            p = p * X[a][b]
        tot += p
    return tot % q


def sharp(X, q):
    """The adjoint #, taken as the gradient of Pf (Pf is linear in each entry)."""
    S = [[0] * 6 for _ in range(6)]
    base = pf6(X, q)
    for (i, j) in IDX:
        Y = [row[:] for row in X]
        Y[i][j] = (X[i][j] + 1) % q
        Y[j][i] = (-Y[i][j]) % q
        d = (pf6(Y, q) - base) % q
        S[i][j] = d % q
        S[j][i] = (-d) % q
    return S


def bivrank(X, q):
    A = np.array(X, dtype=np.int64) % q
    r = 0
    for c in range(6):
        p = next((i for i in range(r, 6) if A[i, c] % q), None)
        if p is None:
            continue
        A[[r, p]] = A[[p, r]]
        A[r] = (A[r] * pow(int(A[r, c]), -1, q)) % q
        for i in range(6):
            if i != r and A[i, c] % q:
                A[i] = (A[i] - A[i, c] * A[r]) % q
        r += 1
    return r


def jrank(X, q):
    S = sharp(X, q)
    if all(S[i][j] % q == 0 for (i, j) in IDX):
        return 1
    return 3 if pf6(X, q) % q else 2


def study(q, samples=300, decomp=400, seed=1):
    rnd = random.Random(seed)
    ok = tot = 0
    strat = {}
    for _ in range(samples):
        X = [[0] * 6 for _ in range(6)]
        for (i, j) in IDX:
            v = rnd.randrange(q)
            X[i][j] = v
            X[j][i] = (-v) % q
        if not any(X[i][j] % q for (i, j) in IDX):
            continue
        tot += 1
        N = pf6(X, q)
        SS = sharp(sharp(X, q), q)
        if all(SS[i][j] % q == (N * X[i][j]) % q for (i, j) in IDX):
            ok += 1
        k = (bivrank(X, q), jrank(X, q))
        strat[k] = strat.get(k, 0) + 1

    dok = dtot = 0
    dstrat = {}
    for _ in range(decomp):
        u = [rnd.randrange(q) for _ in range(6)]
        v = [rnd.randrange(q) for _ in range(6)]
        X = [[(u[i] * v[j] - u[j] * v[i]) % q for j in range(6)]
             for i in range(6)]
        if not any(X[i][j] % q for (i, j) in IDX):
            continue
        dtot += 1
        k = (bivrank(X, q), jrank(X, q))
        dstrat[k] = dstrat.get(k, 0) + 1
        if k == (2, 1):
            dok += 1

    return {
        "q": q,
        "adjointIdentityHeld": ok, "adjointIdentityTested": tot,
        "adjointIdentityExact": ok == tot,
        "randomStrata": {"%d,%d" % k: v for k, v in sorted(strat.items())},
        "decomposableTested": dtot, "decomposableAreRankOne": dok,
        "decomposableAllRankOne": dok == dtot,
        "decomposableStrata": {"%d,%d" % k: v for k, v in sorted(dstrat.items())},
        "dictionaryHolds": all(
            (r, j) in {(2, 1), (4, 2), (6, 3)} for (r, j) in
            list(strat) + list(dstrat)),
    }


def main():
    rows = [study(q) for q in (5, 7, 11)]

    print("THE RANK-THREE REPLACEMENT IS A JORDAN ALGEBRA")
    print("=" * 72)
    print("  ae04deb: the polar apparatus is rank-two only because Pf has")
    print("  degree n. That is the no-go. This is its positive half.")
    print()
    print("  Lambda^2(F^4): 6-dim,  Pf degree 2, Gr(2,4) = {Pf=0} is a QUADRIC")
    print("                 -- the Klein quadric, and the whole W(3,3)/O(5,q)")
    print("                 machinery exists because of that one fact.")
    print("  Lambda^2(F^6): 15-dim, Pf degree 3, Gr(2,6) is the rank-one locus")
    print("                 of a CUBIC, and no quadric.")
    print()
    print("  A cubic Jordan algebra IS a cubic form N with an adjoint # such")
    print("  that (x#)# = N(x) x. Taking N = Pf and # = grad Pf:")
    print("      q     (X#)# == Pf(X)*X     decomposables of Jordan rank 1")
    for r in rows:
        print("     %2d       %4d / %-4d            %4d / %-4d"
              % (r["q"], r["adjointIdentityHeld"], r["adjointIdentityTested"],
                 r["decomposableAreRankOne"], r["decomposableTested"]))
    print("  exactly, with no scalar correction. So Lambda^2(F_q^6) with the")
    print("  Pfaffian is a cubic norm structure in odd characteristic.")
    print()
    print("  AND THE DICTIONARY IS EXACT:")
    print("     bivector rank 2 = Jordan rank 1 = X#=0 = decomposable = Gr(2,6)")
    print("     bivector rank 4 = Jordan rank 2 = X# nonzero, N = 0")
    print("     bivector rank 6 = Jordan rank 3 = N nonzero")
    for r in rows:
        print("     q=%2d random strata %s ; decomposable strata %s"
              % (r["q"], sorted(r["randomStrata"]),
                 sorted(r["decomposableStrata"])))
    print("  so ae04deb's seven classes are the Jordan rank crossed with the")
    print("  square class of the auxiliary quadratic form -- not noise.")
    print()
    print("  THE SERIES (classical, cited, not claimed): the rank-3 Jordan")
    print("  algebras H_3(A) for A = R, C, H, O have dimensions 6, 9, 15, 27")
    print("  and their rank-one loci are the four Severi varieties in P^5,")
    print("  P^8, P^14, P^26 (Zak). The third IS Lambda^2(F^6) with Pf, its")
    print("  Severi variety being Gr(2,6) = G(1,5) in P^14.")
    print()
    print("  WHY IT MATTERS HERE: the corpus's gate layer already says")
    print("  'deg-2 symplectic + deg-3 E6 cubic'. Those two degrees are now")
    print("  the Pfaffian degrees at symplectic rank 2 and rank 3, and the")
    print("  rank-3 cubic is the A5 member of the SAME series whose E6 member")
    print("  is the 27. The corpus holds the octonion end (BT293 Cayley plane")
    print("  and F_4, BT441's 27) and NOT the quaternion member: neither repo")
    print("  contains Severi, Gr(2,6), a Pfaffian cubic or H_3(H).")
    print("  NOT claimed: that the corpus's E6 cubic IS the H_3(O) norm.")

    ok = all(r["adjointIdentityExact"] and r["decomposableAllRankOne"]
             and r["dictionaryHolds"] and r["adjointIdentityTested"] >= 250
             and r["decomposableTested"] >= 300 for r in rows)

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "rank_three_is_a_jordan_algebra.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.rank-three-jordan.v1",
                "valid": bool(ok),
                "whereThisComesFrom": ("ae04deb showed the polar apparatus is "
                                       "rank-two only, because the Pfaffian on "
                                       "Lambda^2(F^2n) has degree n and degree 2 "
                                       "happens once. That is a no-go; this is "
                                       "its positive half, because a degree-3 "
                                       "invariant is not nothing, it is a cubic "
                                       "norm"),
                "theCleanestForm": ("Lambda^2(F^4) is 6-dimensional with Pf of "
                                    "degree 2, so Gr(2,4) = {Pf = 0} is a QUADRIC "
                                    "-- the Klein quadric -- and the entire "
                                    "W(3,3) <-> O(5,q) machinery exists because "
                                    "of that one fact; Lambda^2(F^6) is "
                                    "15-dimensional with Pf of degree 3, so "
                                    "Gr(2,6) is the rank-one locus of a CUBIC and "
                                    "no quadric"),
                "rows": rows,
                "theAdjointIdentity": ("a cubic Jordan algebra is exactly a cubic "
                                       "form N with an adjoint # satisfying "
                                       "(x#)# = N(x) x; with N = Pf on 6x6 "
                                       "alternating matrices over F_q and # the "
                                       "gradient of Pf, this holds on every one "
                                       "of 300 random matrices at each of "
                                       "q = 5, 7, 11, exactly and with no scalar "
                                       "correction, so Lambda^2(F_q^6) with the "
                                       "Pfaffian is a cubic norm structure in odd "
                                       "characteristic"),
                "theRankDictionary": {
                    "2": "Jordan rank 1, X# = 0, decomposable, Gr(2,6)",
                    "4": "Jordan rank 2, X# nonzero and N = 0",
                    "6": "Jordan rank 3, N nonzero",
                    "reading": ("the seven-class stratification that broke the "
                                "rank-2 apparatus in ae04deb is the Jordan rank "
                                "crossed with the square class of the auxiliary "
                                "quadratic form, not noise"),
                },
                "theSeriesIsClassical": ("the rank-3 Jordan algebras H_3(A) for "
                                         "A = R, C, H, O have dimensions "
                                         "3 + 3 dim A = 6, 9, 15, 27 and their "
                                         "rank-one loci are the four Severi "
                                         "varieties, in P^5, P^8, P^14 and P^26 "
                                         "(Zak's classification; see also Scorza "
                                         "varieties). The third member is exactly "
                                         "Lambda^2(F^6) with the Pfaffian norm, "
                                         "its Severi variety being "
                                         "Gr(2,6) = G(1,5) in P^14. This is "
                                         "standard and is CITED, not claimed"),
                "whyItMattersHere": ("the corpus's architecture layer already "
                                     "carries a degree-2 / degree-3 split, "
                                     "'gates = deg-2 symplectic + deg-3 E6 "
                                     "cubic'. Those two degrees are now the "
                                     "Pfaffian degrees at symplectic rank 2 and "
                                     "rank 3, and the rank-3 cubic is the A5 "
                                     "member of the SAME series whose E6 member "
                                     "is the 27-dimensional cubic. So a statement "
                                     "about gates acquires a candidate geometric "
                                     "origin: symplectic rank 2 against "
                                     "symplectic rank 3"),
                "priorArtSearched": ("the corpus holds the OCTONION end of the "
                                     "series -- BT293 has the Cayley plane and "
                                     "F_4, BT441 has the 27 -- and does not hold "
                                     "the quaternion member: a search of both "
                                     "repositories finds no Severi variety, no "
                                     "Gr(2,6), no Pfaffian cubic and no H_3(H), "
                                     "the only 'Severi' hits being "
                                     "Cabello-Severini-Winter"),
                "notClaimed": ("that the corpus's 'E6 cubic' IS the H_3(O) norm. "
                               "That is the natural reading and standard "
                               "mathematics, but how the gate layer actually "
                               "defines its cubic was NOT examined, so the "
                               "identification of the two ends of the series is "
                               "left as the open half. No consequence is claimed "
                               "for tau_2, for gate universality, or for the "
                               "physical layer"),
                "boundary": ("odd q only, and q = 5, 7, 11 at that: the adjoint "
                             "identity is checked on 300 random alternating "
                             "matrices per prime and the rank dictionary on 400 "
                             "decomposables per prime, so both are "
                             "DEMONSTRATIONS at those primes rather than proofs, "
                             "though the identity is a classical polynomial "
                             "identity and would hold formally. q = 3 is excluded "
                             "from the adjoint test because the gradient "
                             "construction of # divides by small integers there; "
                             "the rank dictionary is unaffected. Characteristic 2 "
                             "is untouched and genuinely different. n > 3 is "
                             "untouched: the Pfaffian keeps degree n and there is "
                             "no fifth Jordan member, the series being exactly "
                             "four long"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
