#!/usr/bin/env python3
"""
The monomials-are-GQ-lines identification is PUBLISHED. ea2ff88's novelty hedge
is withdrawn, the literature is cited, and the series is recorded as verified
rather than found.

WHAT WAS COMPUTED.  The squarefree cubic Jordan norms, taking coordinates as
points and monomial supports as lines, give generalized quadrangles -- and
exactly the complete list of those with three points per line:

    algebra    dim   norm          monomials   result
    H3(R)        6   det symmetric      -       NOT squarefree, a coordinate
                                                appears squared, so there is no
                                                incidence structure at all
    H3(C)        9   det of a 3x3       6       GQ(2,1), the grid
    H3(H)       15   Pf of a 6x6       15       GQ(2,2), the doily
    H3(O)       27   Cartan cubic      45       GQ(2,4)

each verified against all four quadrangle axioms -- constant line size, constant
lines per point, no point pair on two lines, and the GQ axiom on every
non-incident point-line pair (36, 180 and 1080 pairs respectively). Generalized
quadrangles of order (2,t) exist only for t = 1, 2, 4, so the three squarefree
norms realize all of them, one each.

IT IS PUBLISHED, AND ea2ff88 SHOULD HAVE SAID SO.  Two independent sources.

Levay, Saniga and Vrana, "Black Hole Entropy and Finite Geometry"
(arXiv:0903.0541), state the 27-dimensional case outright: "The 27 charges
correspond to the points and the 45 terms in the entropy formula to the lines
of GQ(2,4)." The E6 Cartan cubic IS the D=5 entropy formula, so those 45 terms
are its 45 monomials. The same abstract continues: "Different truncations with
15, 11 and 9 charges are represented by three distinguished subconfigurations
of GQ(2,4) ... these are the 'doily' (i.e. GQ(2,2)) with 15, the 'perp-set' of
a point with 11, and the 'grid' (i.e. GQ(2,1)) with 9 points, respectively." So
the 15 and the 9 are published too, and in the same paper.

And the general statement is older still: "Generalized Quadrangles and Cubic
Forms" (Communications in Algebra 29(10), 2001) characterises when a pair of
cubic forms satisfies the adjoint identities -- exactly the identity 9a202a2 and
c6d1077 verified -- in terms of the associated incidence structure being a star
or a generalized quadrangle with determined parameters. That is not a
coincidence to be noticed; it is a theorem, and it runs both ways.

THE HEDGE IS WITHDRAWN.  ea2ff88 recorded that "a search of both repositories
for '45 monomials' and for a monomial/GQ(2,4) identification found nothing,
which is weak evidence and is treated as none". The hedge was correctly worded
and the corpus search was accurate, but the framing still invited a reading of
novelty, and that reading is wrong. The identification is in the literature, the
whole three-member series is in the literature, and the general theorem behind
it is in the literature. Nothing mathematical in ea2ff88 or here is new.

WHAT IS ACTUALLY WORTH KEEPING.  Three things, none of them a discovery.
First, the computation: all four GQ axioms checked exhaustively for all three
algebras, which is a verification the cited papers do not need to supply and
this corpus can now rely on. Second, the citation itself -- the corpus has been
building on the E6 cubic, the doily and GQ(2,4) for a long time without pointing
at Levay-Saniga-Vrana, and that literature is squarely relevant to a quantum
information corpus, being the black-hole/qubit correspondence. Third, the
negative on H3(R): the series starts at dimension 9 because the symmetric
determinant is not squarefree, which is the reason there is no GQ(2,0) member to
look for.

SCOPE.  Exact and exhaustive over the integers for all three algebras: every
monomial enumerated from the closed form, every incidence, every point pair and
every non-incident point-line pair. No field and no q -- this is about the
shape of the polynomials. That GQs of order (2,t) exist only for t = 1, 2, 4 is
quoted as classical (Payne-Thas) and not re-derived. The prior-art statements
are quoted from the abstract of arXiv:0903.0541 and from the title and summary
of the Communications in Algebra paper; the full texts were not read, so the
attribution is to what those sources state, and if either goes further this file
understates them rather than the reverse. Nothing here touches tau_2, the rank
ceiling, or the physical layer.
"""

import collections
import itertools
import json
import os
import sys

ROOT = r"C:\Repos\Holotrade"


def gq_check(npts, lines):
    lines = [frozenset(l) for l in lines]
    sizes = sorted({len(l) for l in lines})
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
    ax = collections.Counter()
    for l in lines:
        for p in range(npts):
            if p in l:
                continue
            ax[sum(1 for x in l if x in coll[p])] += 1
    perpoint = sorted(set(rep.values()))
    ok = (len(sizes) == 1 and len(perpoint) == 1
          and (max(pair.values()) if pair else 0) <= 1 and set(ax) == {1})
    s = sizes[0] - 1 if len(sizes) == 1 else None
    t = perpoint[0] - 1 if len(perpoint) == 1 else None
    return {"points": npts, "lines": len(lines), "lineSizes": sizes,
            "linesPerPoint": perpoint,
            "maxLinesPerPointPair": max(pair.values()) if pair else 0,
            "gqAxiomPairs": sum(ax.values()),
            "gqAxiomAllOne": set(ax) == {1},
            "isGQ": ok, "s": s, "t": t,
            "pointsFormula": (s + 1) * (s * t + 1) if ok else None,
            "linesFormula": (t + 1) * (s * t + 1) if ok else None}


def main():
    # H3(R): det of a SYMMETRIC 3x3 -- squares appear, so no 3-set supports
    sym, k = {}, 0
    for i in range(3):
        for j in range(i, 3):
            sym[(i, j)] = k
            sym[(j, i)] = k
            k += 1
    symterms = {tuple(sorted(sym[(r, p[r])] for r in range(3)))
                for p in itertools.permutations(range(3))}
    squarefree6 = all(len(set(t)) == 3 for t in symterms)

    ent = {(i, j): 3 * i + j for i in range(3) for j in range(3)}
    L9 = [frozenset(ent[(r, p[r])] for r in range(3))
          for p in itertools.permutations(range(3))]

    duad, k = {}, 0
    for i in range(6):
        for j in range(i + 1, 6):
            duad[(i, j)] = k
            k += 1

    def matchings(rem):
        if not rem:
            yield []
            return
        a = rem[0]
        for x in range(1, len(rem)):
            b = rem[x]
            for m in matchings(rem[1:x] + rem[x + 1:]):
                yield [(a, b)] + m

    L15 = [frozenset(duad[p] for p in m) for m in matchings(list(range(6)))]

    coords = [(f, i, j) for f in range(3) for i in range(3) for j in range(3)]
    ci = {c: n for n, c in enumerate(coords)}
    L45 = []
    for f in range(3):
        for p in itertools.permutations(range(3)):
            L45.append(frozenset(ci[(f, r, p[r])] for r in range(3)))
    for i in range(3):
        for j in range(3):
            for k2 in range(3):
                L45.append(frozenset({ci[(0, i, j)], ci[(1, j, k2)],
                                      ci[(2, k2, i)]}))

    rows = [
        {"algebra": "H3(C)", "dim": 9, "norm": "det of a 3x3",
         **gq_check(9, L9)},
        {"algebra": "H3(H)", "dim": 15, "norm": "Pf of a 6x6",
         **gq_check(15, L15)},
        {"algebra": "H3(O)", "dim": 27, "norm": "E6 Cartan cubic",
         **gq_check(27, L45)},
    ]

    print("THE JORDAN / GQ SERIES IS PUBLISHED")
    print("=" * 72)
    print("  H3(R) dim 6, det of a symmetric 3x3: squarefree = %s" % squarefree6)
    print("     a coordinate appears SQUARED, so there is no incidence")
    print("     structure and the series starts at dimension 9.")
    print()
    print("  algebra  dim  norm              monomials  ->  GQ      axioms")
    for r in rows:
        print("  %-7s %3d  %-16s %6d     ->  GQ(%d,%d)  %d pairs, all 1: %s"
              % (r["algebra"], r["dim"], r["norm"], r["lines"], r["s"], r["t"],
                 r["gqAxiomPairs"], r["gqAxiomAllOne"]))
    print("  GQs of order (2,t) exist only for t = 1, 2, 4, so the three")
    print("  squarefree norms realize ALL of them, one each.")
    print()
    print("  AND IT IS PUBLISHED. Levay-Saniga-Vrana, arXiv:0903.0541:")
    print("     'The 27 charges correspond to the points and the 45 terms in")
    print("      the entropy formula to the lines of GQ(2,4).'")
    print("     and the 15 and 9 truncations are named there as the doily")
    print("     GQ(2,2) and the grid GQ(2,1). The general theorem is older:")
    print("     'Generalized Quadrangles and Cubic Forms', Comm. Algebra 29(10)")
    print("     (2001), characterises the adjoint identities in terms of the")
    print("     incidence structure being a star or a GQ.")
    print()
    print("  SO ea2ff88's NOVELTY HEDGE IS WITHDRAWN. Its corpus search was")
    print("  accurate and its wording was hedged, but the framing invited a")
    print("  reading of novelty and that reading is wrong. Nothing")
    print("  mathematical there or here is new.")

    ok = (not squarefree6
          and all(r["isGQ"] for r in rows)
          and [(r["s"], r["t"]) for r in rows] == [(2, 1), (2, 2), (2, 4)]
          and all(r["pointsFormula"] == r["points"] for r in rows)
          and all(r["linesFormula"] == r["lines"] for r in rows))

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "jordan_gq_series_is_published.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.jordan-gq-series-published.v1",
                "valid": bool(ok),
                "rows": rows,
                "h3rIsNotSquarefree": not squarefree6,
                "whyTheSeriesStartsAtNine": ("the determinant of a SYMMETRIC 3x3 "
                                             "is not squarefree -- a coordinate "
                                             "appears squared -- so its terms are "
                                             "not 3-sets and there is no "
                                             "incidence structure at all. That is "
                                             "why there is no GQ(2,0) member to "
                                             "look for"),
                "theCompleteList": ("generalized quadrangles of order (2,t) exist "
                                    "only for t = 1, 2, 4, so the three "
                                    "squarefree cubic Jordan norms realize ALL of "
                                    "them, one each: det3 -> GQ(2,1) the grid, "
                                    "Pf6 -> GQ(2,2) the doily, Cartan -> GQ(2,4)"),
                "priorArt": {
                    "levaySanigaVrana": ("'Black Hole Entropy and Finite "
                                         "Geometry', arXiv:0903.0541, states it "
                                         "outright: 'The 27 charges correspond to "
                                         "the points and the 45 terms in the "
                                         "entropy formula to the lines of "
                                         "GQ(2,4).' The E6 Cartan cubic IS the "
                                         "D=5 entropy formula, so those 45 terms "
                                         "are its monomials. The same abstract "
                                         "names the 15 and 9 truncations as the "
                                         "doily GQ(2,2) and the grid GQ(2,1), so "
                                         "the whole three-member series is there"),
                    "generalizedQuadranglesAndCubicForms": ("Communications in "
                                                            "Algebra 29(10) "
                                                            "(2001) characterises "
                                                            "when a pair of cubic "
                                                            "forms satisfies the "
                                                            "adjoint identities -- "
                                                            "exactly the identity "
                                                            "c6d1077 and 9a202a2 "
                                                            "verified -- in terms "
                                                            "of the associated "
                                                            "incidence structure "
                                                            "being a star or a "
                                                            "generalized "
                                                            "quadrangle with "
                                                            "determined "
                                                            "parameters. The "
                                                            "connection is a "
                                                            "theorem, and it runs "
                                                            "both ways"),
                },
                "theHedgeIsWithdrawn": ("ea2ff88 recorded that a search of both "
                                        "repositories for '45 monomials' and for "
                                        "a monomial/GQ(2,4) identification found "
                                        "nothing, 'which is weak evidence and is "
                                        "treated as none'. The hedge was correctly "
                                        "worded and the corpus search was "
                                        "accurate, but the framing still invited a "
                                        "reading of novelty and that reading is "
                                        "WRONG. The identification is published, "
                                        "the whole series is published, and the "
                                        "general theorem behind it is published. "
                                        "Nothing mathematical in ea2ff88 or here "
                                        "is new"),
                "whatIsWorthKeeping": ("three things, none a discovery. The "
                                       "COMPUTATION: all four GQ axioms checked "
                                       "exhaustively for all three algebras, which "
                                       "the cited papers have no need to supply "
                                       "and this corpus can now rely on. The "
                                       "CITATION: the corpus has been building on "
                                       "the E6 cubic, the doily and GQ(2,4) for a "
                                       "long time without pointing at "
                                       "Levay-Saniga-Vrana, and that literature -- "
                                       "the black-hole/qubit correspondence -- is "
                                       "squarely relevant to a quantum information "
                                       "corpus. And the NEGATIVE on H3(R), which "
                                       "explains why the series starts at "
                                       "dimension 9"),
                "boundary": ("exact and exhaustive over the integers for all three "
                             "algebras: every monomial from the closed form, every "
                             "incidence, every point pair, every non-incident "
                             "point-line pair. No field and no q -- this is about "
                             "the shape of the polynomials. That GQs of order "
                             "(2,t) exist only for t = 1,2,4 is quoted as "
                             "classical (Payne-Thas). The prior-art statements are "
                             "quoted from the ABSTRACT of arXiv:0903.0541 and from "
                             "the title and summary of the Communications in "
                             "Algebra paper; the full texts were NOT read, so the "
                             "attribution is to what those sources state, and if "
                             "either goes further this file understates them "
                             "rather than the reverse. Nothing here touches tau_2, "
                             "the rank ceiling, or the physical layer"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
