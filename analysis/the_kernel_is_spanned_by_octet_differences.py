#!/usr/bin/env python3
"""
ker(N^T) is spanned by the 45 octet differences, the pencil encoding is
injective up to mass 12 and first degenerates at mass 16, and the obstruction
is nonnegativity rather than arithmetic.

WHERE THIS COMES FROM.  The other track's mass-excess programme
(the_mass_eight_excess_is_two_pencils.py, the_mass12_mass16_excess_pencil_
induction.py, the_mass12_mass16_exact_orbit_census.py) works with the axis
load-excess e of a tensor blocker: for |X| = 110 + k, summing loads over the 40
lines gives 4|X|, so e = load - 11 is a nonnegative integer vector of mass 4k
satisfying A e = 2 e + k 1. Those files prove mass 4 is exactly one point-pencil
and mass 8 exactly two, and then report that the same induction FAILS at mass 12
and 16, with CP-SAT finding counterexamples in milliseconds. This file explains
the linear algebra underneath that failure, and finds the kernel.

FIRST, THE SPECTRAL RESTATEMENT.  A has eigenvalues 12, 2, -4 on the SRG, and
ker(N^T) is the (-4)-eigenspace, which the mass-eight file already records. So
A e = 2 e + k 1 says (A - 2I) e = k 1, and decomposing e in the three
eigenspaces kills the (-4) component outright: e must lie in the REAL image of
N^T. Writing e = N^T x, the mass identity sum(e) = 4 sum(x) forces sum(x) = k.
So an excess is "k point-pencils" exactly when that preimage x can be taken
nonnegative and integral, and the whole question is about the preimage.

SECOND, INTEGRALITY IS NEVER THE OBSTRUCTION.  The Smith normal form of N^T
over Z is

        1^25  0^15,

so Z^40 / im(N^T) is TORSION-FREE. Hence any integral e in the real image is
already in the INTEGER image: N^T x = e is solvable over Z whenever it is
solvable over Q. The exceptional excesses therefore fail on NONNEGATIVITY
alone. There is no mod-p invariant separating them, and looking for one is a
closed direction -- which is the practical value of computing the form.

THIRD, THE PENCIL ENCODING IS INJECTIVE UNTIL MASS 16, AND THEN FAILS EXACTLY
ON THE OCTETS.  Mapping a multiset of k points to the sum of their pencils:

        k = 1   mass  4      40 multisets ->     40 vectors    injective
        k = 2   mass  8     820 multisets ->    820 vectors    injective
        k = 3   mass 12   11480 multisets ->  11480 vectors    injective
        k = 4   mass 16  123410 multisets -> 123365 vectors    45 COLLISIONS

and every collision is a PAIR, so there are exactly 45 of them. They are
exactly the 45 octet polarity pairs: for a hyperbolic line L of PG(3,3),

        sum over p in L of pencil(p)  =  sum over p in L^perp of pencil(p).

Checked as a set equality against the 45 pairs {L, L^perp} built independently
from the form, not matched by count.

FOURTH, THE SPANNING STATEMENT -- AND ITS CORRECT SCOPE.  That relation says
1_L - 1_{L^perp} lies in ker(N^T). All 45 of them do, and their rank is
15 = dim ker(N^T). So

        ker(N^T) is SPANNED by the 45 octet differences.

THE SPACE ITSELF IS NOT NEW, AND IS CITED.  o5_polar_incidence_splits_the_w33_
24_15_modules.py already identifies this 15-dimensional kernel as the SPREAD /
nonsquare sector, records N C0 = 0 exactly, and spans it from the 36 NONSQUARE
O(5,3) polar points; the 24/15 split and the rank-25 fast/slow channel are that
file's, from c9e6be7 and ba74506. What is added here is a SECOND and
differently-indexed spanning set, from the 45 SQUARE side: the signed octet
differences. The two descriptions are of the same space, they come from
opposite halves of the O(5,3) orbit census, and neither is derived from the
other here. Reading this as "the 15-sector has been identified" is reading it
wrong.

WHAT THIS DOES AND DOES NOT SAY ABOUT 114.  Mass 16 is 4(114 - 110), so the
first degeneracy of the pencil encoding falls exactly on the size that resisted
the clock, the group, the encoding and the transpose. That is a structural
coincidence worth recording and it is NOT a proof that 114 is hard, still less
a bound on tau_2. It is also a DIFFERENT degeneracy from the one the other
track reports: theirs is the appearance of admissible excesses that are not
pencil-generated at all, already at mass 12; mine is the failure of distinct
pencil multisets to stay distinct, first at mass 16. Both are real and they are
not the same phenomenon.

SCOPE.  Exact and exhaustive: the Smith form is computed over Z, the injectivity
census enumerates all multisets of size up to 4 over the 40 points, and the
identification of the collisions with the octets is a set equality. Nothing here
constrains tau_2, which stays open in [111, 115].
"""

import argparse
import itertools
import json
import os
from collections import Counter

Q = 3
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def geometry():
    def nm(v):
        i = next(k for k, x in enumerate(v) if x % Q)
        z = pow(v[i] % Q, -1, Q)
        return tuple((z * x) % Q for x in v)

    pts = sorted({nm(v) for v in itertools.product(range(Q), repeat=4)
                  if any(v)})
    idx = {p: i for i, p in enumerate(pts)}

    def sf(u, v):
        return (u[0] * v[1] - u[1] * v[0] + u[2] * v[3] - u[3] * v[2]) % Q

    alllines = set()
    for a, b in itertools.combinations(range(40), 2):
        S = set()
        for x in range(Q):
            for y in range(Q):
                if x or y:
                    w = tuple((x * pts[a][k] + y * pts[b][k]) % Q
                              for k in range(4))
                    if any(w):
                        S.add(idx[nm(w)])
        alllines.add(frozenset(S))

    def isotropic(L):
        return all(sf(pts[x], pts[y]) % Q == 0
                   for x, y in itertools.combinations(sorted(L), 2))

    def hyperbolic(L):
        return all(sf(pts[x], pts[y]) % Q
                   for x, y in itertools.combinations(sorted(L), 2))

    iso = sorted(sorted(L) for L in alllines if isotropic(L))
    hyp = [L for L in alllines if hyperbolic(L)]

    def perp(L):
        return frozenset(p for p in range(40)
                         if all(sf(pts[p], pts[y]) % Q == 0 for y in L))

    return pts, sf, iso, hyp, perp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    from sympy import Matrix
    from sympy.matrices.normalforms import smith_normal_form

    pts, sf, iso, hyp, perp = geometry()
    assert len(iso) == 40, len(iso)
    Nt = Matrix([[1 if p in L else 0 for p in range(40)] for L in iso])
    rank = Nt.rank()
    kerdim = 40 - rank

    S = smith_normal_form(Nt)
    diag = [S[i, i] for i in range(min(S.shape))]
    factors = dict(Counter(int(x) for x in diag))
    torsion = {k: v for k, v in factors.items() if k not in (0, 1)}

    thru = [[i for i, L in enumerate(iso) if p in L] for p in range(40)]

    census = {}
    collisions = None
    for k in (1, 2, 3, 4):
        seen = {}
        for combo in itertools.combinations_with_replacement(range(40), k):
            v = [0] * 40
            for c in combo:
                for i in thru[c]:
                    v[i] += 1
            seen.setdefault(tuple(v), []).append(combo)
        total = sum(len(c) for c in seen.values())
        census[k] = {"mass": 4 * k, "multisets": total,
                     "distinctVectors": len(seen),
                     "collisions": total - len(seen),
                     "injective": total == len(seen)}
        if k == 4:
            collisions = {v: c for v, c in seen.items() if len(c) > 1}

    octets = {frozenset([L, perp(L)]) for L in hyp}
    predicted = set()
    for o in octets:
        A, B = sorted(o, key=lambda s: sorted(s))
        predicted.add(frozenset([tuple(sorted(A)), tuple(sorted(B))]))
    actual = {frozenset(tuple(sorted(c)) for c in v)
              for v in collisions.values()}
    collisions_are_octets = predicted == actual
    class_sizes = dict(Counter(len(c) for c in collisions.values()))

    D = []
    for o in octets:
        A, B = sorted(o, key=lambda s: sorted(s))
        v = [0] * 40
        for p in A:
            v[p] += 1
        for p in B:
            v[p] -= 1
        D.append(v)
    D = Matrix(D)
    in_kernel = (Nt * D.T).is_zero_matrix
    drank = D.rank()
    spans = (drank == kerdim)

    print("ker(N^T) IS SPANNED BY THE OCTET DIFFERENCES")
    print("=" * 74)
    print("  N^T is %dx%d, rank %d, dim ker = %d"
          % (Nt.shape[0], Nt.shape[1], rank, kerdim))
    print("  Smith normal form: %s  -> torsion %s"
          % (factors, torsion if torsion else "NONE (torsion-free)"))
    print("  so N^T x = e is solvable over Z whenever over Q:")
    print("  the exceptional excesses fail on NONNEGATIVITY, not arithmetic.")
    print()
    print("  pencil-sum map on k-multisets of the 40 points:")
    for k in (1, 2, 3, 4):
        c = census[k]
        print("    k=%d  mass %2d  %6d multisets -> %6d vectors   %s"
              % (k, c["mass"], c["multisets"], c["distinctVectors"],
                 "injective" if c["injective"]
                 else "%d COLLISIONS" % c["collisions"]))
    print()
    print("  the %d collisions at mass 16 are all pairs %s"
          % (census[4]["collisions"], class_sizes))
    print("  and they are EXACTLY the %d octet polarity pairs {L, L^perp}: %s"
          % (len(octets), collisions_are_octets))
    print()
    print("  the 45 differences 1_L - 1_Lperp lie in ker(N^T): %s" % in_kernel)
    print("  their rank is %d = dim ker(N^T): they SPAN it: %s"
          % (drank, spans))

    ok = (rank == 25 and kerdim == 15 and not torsion
          and all(census[k]["injective"] for k in (1, 2, 3))
          and census[4]["collisions"] == 45
          and collisions_are_octets and in_kernel and spans)
    print()
    print("VALID: %s" % ok)

    if args.write:
        assert ok, "checks failed -- refusing to write"
        rec = {
            "schema": "holotrade.kernel-spanned-by-octet-differences.v1",
            "valid": True,
            "ntShape": list(Nt.shape),
            "rank": rank,
            "kernelDimension": kerdim,
            "smithInvariantFactors": {str(k): v for k, v in factors.items()},
            "cokernelIsTorsionFree": not torsion,
            "pencilSumCensus": {str(k): census[k] for k in census},
            "collisionsAtMass16": census[4]["collisions"],
            "collisionClassSizes": {str(k): v for k, v in class_sizes.items()},
            "octetPolarityPairs": len(octets),
            "collisionsAreExactlyTheOctets": collisions_are_octets,
            "differencesLieInKernel": in_kernel,
            "differenceRank": drank,
            "differencesSpanTheKernel": spans,
            "theSpectralRestatement": (
                "A has eigenvalues 12, 2, -4 and ker(N^T) is the (-4)-eigenspace, "
                "so A e = 2 e + k 1 reads (A - 2I) e = k 1 and kills the (-4) "
                "component: e must lie in the real image of N^T. Writing e = N^T x, "
                "the mass identity sum(e) = 4 sum(x) forces sum(x) = k. An excess "
                "is 'k point-pencils' exactly when that preimage can be taken "
                "nonnegative and integral."),
            "integralityIsNeverTheObstruction": (
                "the Smith normal form of N^T over Z is 1^25 0^15, so "
                "Z^40 / im(N^T) is TORSION-FREE and N^T x = e is solvable over Z "
                "whenever it is solvable over Q. The exceptional excesses "
                "therefore fail on NONNEGATIVITY alone; no mod-p invariant can "
                "separate them, and looking for one is a closed direction. That is "
                "the practical value of computing the form."),
            "theEncodingFirstFailsAtMass16": (
                "the map from a multiset of k points to the sum of their pencils "
                "is injective at k = 1, 2 and 3 -- 40, 820 and 11480 multisets "
                "giving as many distinct vectors -- and at k = 4 sends 123410 "
                "multisets to 123365 vectors. All 45 collisions are pairs, and "
                "they are EXACTLY the 45 octet polarity pairs: for a hyperbolic "
                "line L, the pencils of the points of L sum to the same vector as "
                "the pencils of the points of L^perp. Checked as a set equality "
                "against octets built independently from the form, not matched by "
                "count."),
            "theSpaceItselfIsPriorArt": (
                "o5_polar_incidence_splits_the_w33_24_15_modules.py already "
                "identifies this 15-dimensional kernel as the SPREAD / nonsquare "
                "sector, records the exact law N C0 = 0, and spans it from the 36 "
                "NONSQUARE O(5,3) polar points; the 24/15 split and the rank-25 "
                "fast/slow channel are that file's, from c9e6be7 and ba74506. What "
                "is added here is a SECOND, differently-indexed spanning set from "
                "the 45 SQUARE side -- the signed octet differences -- not the "
                "identification of the space. The two spanning sets come from "
                "opposite halves of the O(5,3) orbit census and neither is derived "
                "from the other here. Reading this file as 'the 15-sector has been "
                "identified' is reading it wrong."),
            "theKernelResult": (
                "that relation says 1_L - 1_{L^perp} lies in ker(N^T). All 45 do, "
                "and their rank is 15 = dim ker(N^T), so ker(N^T) is SPANNED by "
                "the octet differences. The 15-dimensional kernel behind every "
                "excess argument in this thread is generated by exactly the "
                "objects the L u L^perp work was already about. See "
                "theSpaceItselfIsPriorArt: the SPACE is prior art; only this "
                "spanning set is new."),
            "whatItDoesNotSayAbout114": (
                "mass 16 is 4(114 - 110), so the first degeneracy of the pencil "
                "encoding falls exactly on the size that resisted the clock, the "
                "group, the encoding and the transpose. That is a structural "
                "coincidence worth recording and is NOT a proof that 114 is hard, "
                "still less a bound on tau_2. It is also a DIFFERENT degeneracy "
                "from the one the other track reports: theirs is the appearance of "
                "admissible excesses that are not pencil-generated at all, already "
                "at mass 12; this one is distinct pencil multisets failing to stay "
                "distinct, first at mass 16. Both are real and they are not the "
                "same phenomenon."),
            "priorArtCited": (
                "the excess formulation, the equation A e = 2 e + k 1, the "
                "identification ker(N^T) = E_{-4}, and the mass-4 and mass-8 "
                "pencil theorems are the other track's, in "
                "the_mass_eight_excess_is_two_pencils.py and the mass12/mass16 "
                "files. The octets as L u L^perp are this track's, from "
                "the_cost_anomalies_are_the_tritangent_structure.py (3f93821). "
                "Nothing of either is re-derived; this file adds the Smith form, "
                "the injectivity census and the spanning statement."),
            "boundary": (
                "exact and exhaustive: the Smith form is computed over Z, the "
                "injectivity census enumerates ALL multisets of size up to 4 over "
                "the 40 points, and the identification of the collisions with the "
                "octets is a set equality rather than a count match. The spanning "
                "claim is a rank computation over Q. Nothing here constrains "
                "tau_2, which stays open in [111, 115]."),
        }
        p = os.path.join(ROOT, "data", "kernel_spanned_by_octet_differences.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=2)
        print("written: %s" % p)


if __name__ == "__main__":
    main()
