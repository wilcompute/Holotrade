#!/usr/bin/env python3
"""
All three legs of the Schlaefli 27-36-45 triangle are features of ONE
polynomial: the coordinates, the monomials, and the sections of the E6 Cartan
cubic.

WHAT WAS ALREADY HELD, AND BY WHOM.  Two of the three legs are in place.
gq24_schlaefli_quadrangle.py has GQ(2,4) = Q-(5,2) with 27 points and 45 lines
and its link to the 27 lines on a cubic surface, citing corpus Pass 84 for
PSp(4,3) = PSU(4,2) = W(E6)/Z2. And Theory-of-Everything fdc9f1d75 / 8a4933dde
proves that each of the 36 Schlaefli double-sixes cuts an exact signed Pfaffian
section from the 27-coordinate Cartan cubic, C_E6 restricted to S_D = Pf_6
coefficient-by-coefficient, with 1de360304 making the whole 36-chain
PSp(4,3)-equivariant. So the 36 are SECTIONS of the cubic and the 27 are its
COORDINATES.

The 45 were the leg with no stated relation to the polynomial. They have one,
and it is the simplest possible: they are its MONOMIALS.

THE CUBIC, IN THE MODEL 9a202a2 VERIFIED.  On the minuscule 27 restricted to
SL(3)^3 as three copies of M_3,

    N(A,B,C) = det A + det B + det C - tr(ABC)

which 9a202a2 checked satisfies the cubic-norm adjoint identity exactly at
q = 3, 5, 7, 11. Count its terms: three determinants contribute 6 each, and
tr(ABC) = sum over i,j,k of A_ij B_jk C_ki contributes 27. That is

    18 + 27 = 45 monomials, on 27 coordinates,

each monomial a product of three DISTINCT coordinates, and all 45 supports
distinct.

AND THOSE 45 SUPPORTS ARE A GENERALIZED QUADRANGLE.  Taking the 27 coordinates
as points and the 45 monomial supports as lines:

    every line has 3 points                                       yes
    every point lies on 5 lines                                   yes
    incidences 45 x 3 = 27 x 5 = 135                              yes
    no two points lie on more than one common line                yes
    for every non-incident point-line pair, EXACTLY ONE point of
      the line is collinear with the point -- all 1080 cases      yes

which is precisely the GQ axiom set for order (s,t) = (2,4):
(s+1)(st+1) = 3 x 9 = 27 points and (t+1)(st+1) = 5 x 9 = 45 lines. The
collinearity graph comes out SRG(27,10,1,5), the complement of the Schlaefli
graph SRG(27,16,10,8) -- which is right, since two of the 27 lines share a
tritangent exactly when they MEET, and each meets 10 of the others.

SO THE TRIANGLE IS ONE OBJECT.

    27  =  the coordinates of the cubic        =  the 27 lines
    45  =  the monomials of the cubic          =  the 45 tritangent planes
    36  =  the Pfaffian sections of the cubic  =  the 36 double-sixes

Coordinates, monomials, sections. Nothing is imported: given the polynomial,
all three legs and their incidences are readable off it.

WHAT IS AND IS NOT CLAIMED.  The geometry is classical and already in this
corpus: that the 27 lines and 45 tritangent planes of a cubic surface form
GQ(2,4) is standard, gq24_schlaefli_quadrangle.py already carries GQ(2,4) with
those parameters, and Pass 84 already has PSp(4,3) = W(E6)/Z2. NO novelty is
claimed for any of that. What is offered is the realization: that this
incidence is literally the TERM STRUCTURE of the Cartan cubic in the SL(3)^3
coordinates -- points are variables, lines are monomials -- verified here
against all four quadrangle axioms rather than asserted; and the observation
that, once the parallel track's sections are added, the whole 27-36-45 triangle
is three different features of a single polynomial. A search of both
repositories for "45 monomials" and for a monomial/GQ(2,4) identification found
nothing, which is weak evidence and is treated as none.

SCOPE.  Exact and exhaustive over the integers: all 45 monomials enumerated
from the closed form, all 135 incidences, all 351 coordinate pairs, and all
1080 non-incident point-line pairs checked for the GQ axiom. There is no field
here and no q -- the monomial structure is a statement about the polynomial's
shape, not about any F_q realization, though 9a202a2's adjoint check gives the
same polynomial cubic-norm status over F_q. The identification of the 36
sections is QUOTED from Theory-of-Everything fdc9f1d75 and not re-derived. This
says nothing about tau_2, about the rank ceiling, or about the physical layer.
"""

import collections
import itertools
import json
import os
import sys

import numpy as np

ROOT = r"C:\Repos\Holotrade"


def cubic_terms():
    """N(A,B,C) = det A + det B + det C - tr(ABC), as (sign, support) pairs."""
    coords = [(f, i, j) for f in range(3) for i in range(3) for j in range(3)]
    ci = {c: k for k, c in enumerate(coords)}
    mons = []
    for f in range(3):
        for p in itertools.permutations(range(3)):
            sgn = (-1) ** sum(1 for a in range(3) for b in range(a + 1, 3)
                              if p[a] > p[b])
            mons.append((sgn, frozenset(ci[(f, r, p[r])] for r in range(3))))
    for i in range(3):
        for j in range(3):
            for k in range(3):
                mons.append((-1, frozenset({ci[(0, i, j)], ci[(1, j, k)],
                                            ci[(2, k, i)]})))
    return coords, mons


def gq_checks(lines, npts=27):
    rep = collections.Counter()
    for l in lines:
        for p in l:
            rep[p] += 1
    pair = collections.Counter()
    for l in lines:
        for a, b in itertools.combinations(sorted(l), 2):
            pair[(a, b)] += 1
    coll = {p: set() for p in range(npts)}
    for l in lines:
        for p in l:
            coll[p] |= set(l) - {p}
    axiom = collections.Counter()
    for l in lines:
        for p in range(npts):
            if p in l:
                continue
            axiom[sum(1 for x in l if x in coll[p])] += 1
    A = np.zeros((npts, npts), dtype=np.int64)
    for l in lines:
        for a, b in itertools.combinations(sorted(l), 2):
            A[a, b] = 1
            A[b, a] = 1
    deg = sorted(set(A.sum(1).tolist()))
    CN = A @ A
    iu = np.triu_indices(npts, 1)
    e = A[iu].astype(bool)
    c = CN[iu]
    lam = sorted(set(c[e].tolist()))
    mu = sorted(set(c[~e].tolist()))
    return {
        "lines": len(lines),
        "allLinesSizeThree": all(len(l) == 3 for l in lines),
        "allSupportsDistinct": len({frozenset(l) for l in lines}) == len(lines),
        "linesPerPoint": sorted(set(rep.values())),
        "incidences": sum(rep.values()),
        "maxLinesThroughAPointPair": max(pair.values()),
        "gqAxiomCounts": {str(k): v for k, v in sorted(axiom.items())},
        "gqAxiomHolds": set(axiom) == {1},
        "collinearitySRG": [npts, deg[0], lam[0] if lam else None,
                            mu[0] if mu else None],
        "isSRG": len(deg) == 1 and len(lam) == 1 and len(mu) == 1,
    }


def main():
    coords, mons = cubic_terms()
    lines = [m for _, m in mons]
    r = gq_checks(lines)
    r["coordinates"] = len(coords)
    r["monomials"] = len(mons)
    r["determinantTerms"] = 18
    r["traceTerms"] = 27

    schlafli = [27, 16, 10, 8]
    comp = [27, 27 - 1 - 16, 27 - 2 - 2 * 16 + 8, 27 - 2 * 16 + 10]

    print("THE SCHLAEFLI TRIANGLE IS ONE POLYNOMIAL")
    print("=" * 72)
    print("  N(A,B,C) = det A + det B + det C - tr(ABC)  on 27 coordinates")
    print("     3 determinants x 6 terms  = 18")
    print("     tr(ABC), i,j,k over 3     = 27")
    print("     total monomials           = %d" % r["monomials"])
    print("  each a product of 3 DISTINCT coordinates: %s ; all supports"
          % r["allLinesSizeThree"])
    print("  distinct: %s" % r["allSupportsDistinct"])
    print()
    print("  27 coordinates as POINTS, 45 monomial supports as LINES:")
    print("     lines per point          %s" % r["linesPerPoint"])
    print("     incidences               %d = 45 x 3 = 27 x 5" % r["incidences"])
    print("     max lines per point pair %d   (a GQ needs 1)"
          % r["maxLinesThroughAPointPair"])
    print("     GQ axiom over all %d non-incident pairs: %s %s"
          % (sum(r["gqAxiomCounts"].values()), r["gqAxiomHolds"],
             r["gqAxiomCounts"]))
    print("     collinearity graph SRG%s" % (tuple(r["collinearitySRG"]),))
    print("  => GQ(2,4): (s+1)(st+1) = 27 points, (t+1)(st+1) = 45 lines")
    print("  and SRG%s is the COMPLEMENT of the Schlaefli graph SRG%s,"
          % (tuple(comp), tuple(schlafli)))
    print("  which is right: two of the 27 lines share a tritangent exactly")
    print("  when they MEET, and each meets 10 of the others.")
    print()
    print("  SO THE TRIANGLE IS ONE OBJECT:")
    print("     27 = the cubic's COORDINATES        = the 27 lines")
    print("     45 = the cubic's MONOMIALS          = the 45 tritangents")
    print("     36 = the cubic's PFAFFIAN SECTIONS  = the 36 double-sixes")
    print("                                           (TOE fdc9f1d75)")
    print()
    print("  NOVELTY: the geometry is classical and already in this corpus")
    print("  (gq24_schlaefli_quadrangle.py, Pass 84). What is offered is that")
    print("  the incidence IS the cubic's term structure -- points are")
    print("  variables, lines are monomials -- checked against all four GQ")
    print("  axioms, plus the observation that all three legs are features of")
    print("  a single polynomial.")

    ok = (r["monomials"] == 45 and r["coordinates"] == 27
          and r["allLinesSizeThree"] and r["allSupportsDistinct"]
          and r["linesPerPoint"] == [5] and r["incidences"] == 135
          and r["maxLinesThroughAPointPair"] == 1 and r["gqAxiomHolds"]
          and r["isSRG"] and r["collinearitySRG"] == comp)

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "schlafli_triangle_one_polynomial.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.schlafli-triangle-one-polynomial.v1",
                "valid": bool(ok),
                "whatWasAlreadyHeld": ("two legs were in place. "
                                       "gq24_schlaefli_quadrangle.py has "
                                       "GQ(2,4) = Q-(5,2) with 27 points and 45 "
                                       "lines and its link to the 27 lines on a "
                                       "cubic surface, citing corpus Pass 84 for "
                                       "PSp(4,3) = PSU(4,2) = W(E6)/Z2. And "
                                       "Theory-of-Everything fdc9f1d75 / "
                                       "8a4933dde proves each of the 36 "
                                       "double-sixes cuts an exact signed "
                                       "Pfaffian section from the 27-coordinate "
                                       "Cartan cubic, with 1de360304 making the "
                                       "36-chain PSp(4,3)-equivariant. So the 36 "
                                       "are SECTIONS and the 27 are COORDINATES; "
                                       "the 45 were the leg with no stated "
                                       "relation to the polynomial"),
                "theAnswer": ("the 45 are its MONOMIALS. N(A,B,C) = det A + "
                              "det B + det C - tr(ABC) has 18 determinant terms "
                              "and 27 trace terms, 45 in all, each a product of "
                              "three distinct coordinates with all supports "
                              "distinct"),
                "checks": r,
                "schlafliGraph": schlafli,
                "complementOfSchlafli": comp,
                "theTriangleIsOneObject": {
                    "27": "the cubic's coordinates = the 27 lines",
                    "45": "the cubic's monomials = the 45 tritangent planes",
                    "36": ("the cubic's Pfaffian sections = the 36 double-sixes "
                           "(Theory-of-Everything fdc9f1d75)"),
                    "reading": ("coordinates, monomials, sections -- given the "
                                "polynomial, all three legs and their incidences "
                                "are readable off it, with nothing imported"),
                },
                "noveltyNotClaimed": ("the geometry is classical and already in "
                                      "this corpus: that the 27 lines and 45 "
                                      "tritangents of a cubic surface form "
                                      "GQ(2,4) is standard, "
                                      "gq24_schlaefli_quadrangle.py already "
                                      "carries GQ(2,4) with those parameters, and "
                                      "Pass 84 already has PSp(4,3) = W(E6)/Z2. "
                                      "What is offered is the REALIZATION -- that "
                                      "this incidence is literally the term "
                                      "structure of the Cartan cubic in the "
                                      "SL(3)^3 coordinates, points being "
                                      "variables and lines being monomials, "
                                      "verified against all four quadrangle "
                                      "axioms rather than asserted -- together "
                                      "with the observation that all three legs "
                                      "are features of one polynomial. A search "
                                      "of both repositories for '45 monomials' "
                                      "and for a monomial/GQ(2,4) identification "
                                      "found nothing, which is weak evidence and "
                                      "is treated as none"),
                "boundary": ("exact and exhaustive over the integers: all 45 "
                             "monomials enumerated from the closed form, all 135 "
                             "incidences, all coordinate pairs, and all 1080 "
                             "non-incident point-line pairs checked for the GQ "
                             "axiom. There is no field here and no q -- the "
                             "monomial structure is a statement about the "
                             "polynomial's shape, not about any F_q realization, "
                             "though 9a202a2's adjoint check gives the same "
                             "polynomial its cubic-norm status over F_q. The "
                             "identification of the 36 sections is QUOTED from "
                             "Theory-of-Everything fdc9f1d75 and not re-derived. "
                             "Nothing here touches tau_2, the rank ceiling, or "
                             "the physical layer"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
