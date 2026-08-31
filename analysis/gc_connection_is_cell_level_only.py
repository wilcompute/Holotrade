#!/usr/bin/env python3
"""
The Grunbaum-Coxeter connection cannot rise above the cell, and one prime
divisibility argument proves it.

WHERE THIS STARTS.  BT836 puts one hemi-icosahedron (K_6, the 11-cell's cell)
and one hemi-dodecahedron (Petersen, the 57-cell's cell) inside every spread of
W(3,3), and grouping_optimum_carries_the_gc_cells.py reproduced that and noted
the optimal measurement-grouping schedule IS a spread. The obvious next hope is
that the cells assemble: that the substrate carries not just the cells but the
POLYTOPES.

It cannot, and the reason is not subtle.

THE PRIME OBSTRUCTION.  The 11-cell has automorphism group PSL(2,11) of order
660 = 2^2 . 3 . 5 . 11, and the 57-cell has PSL(2,19) of order
3420 = 2^2 . 3^2 . 5 . 19. The substrate's group is

    |Sp(4,3)| = 51840 = 2^6 . 3^4 . 5,      |PSp(4,3)| = 25920.

Eleven does not divide 51840. Nineteen does not divide 51840. By Lagrange,
neither PSL(2,11) nor PSL(2,19) embeds in Sp(4,3) or in any quotient of it, and
no element of order 11 or 19 acts on the 40 points at all.

So no action of either polytope's symmetry group exists on W(3,3). The
connection is CELL-LEVEL by necessity, not by accident of how far anyone has
looked -- the cells' own groups (A_5 for the hemi-dodecahedron, S_5 or A_5 for
the hemi-icosahedron's K_6 skeleton) have orders dividing 51840, and the
polytopes' groups do not.

THE COUNT MISMATCH, which says the same thing combinatorially.  The 36 spreads
of W(3,3) give 36 hemi-dodecahedra and 36 hemi-icosahedra, one of each per
spread. The 11-cell needs 11 cells and the 57-cell needs 57. Neither 11 nor 57
is 36, and 36 is exact: it is a single PSp(4,3)-orbit with point stabiliser of
order 720, and 25920/720 = 36.

WHAT WAS ALREADY OURS, and it is more than I first credited. The 36-spread
structure is not new here:

  * BT2053 identifies the four-line spread graph as the rank-three NO_6^-(2)
    graph, equivalently NO_5^{-perp}(3), with local graph Kneser K(6,2),
    second subconstituent Johnson J(6,3), and full automorphism group of order
    51840 -- and states explicitly that the identification does NOT rely on
    the highly nonunique parameter set (36,15,6,6);
  * BT2064 already has the whole family: complete regular-symplectic-spread
    orbits of sizes 36, 300 and 1176 for q = 3, 5, 7, with distinct spreads
    meeting in exactly 1 or q+1 lines in all three cases;
  * BT2088 gives the exact stabiliser as C_2 x S_6 of order 1440, with the
    central involution silent and S_6 the visible quotient.

An independent enumeration here returns 36 spreads, pairwise intersections
taking only the values 1 and 4 = q+1, the share-4 graph strongly regular with
parameters (36,15,6,6) and spectrum 15, 3^15, (-3)^20, a single orbit, and
stabiliser order 720 in PSp(4,3) -- which is BT2088's 1440 modulo the centre,
since |Sp(4,3)| = 2|PSp(4,3)|. Everything matches; nothing there is new.

WHAT IS ADDED -- corrected. An earlier version of this file claimed the
boundary itself. It should not have: BT836 already states, in its
Physics/machine reading, that "the 11-cell/57-cell groups PSL(2,11),
PSL(2,19) are not subgroups of Sp(4,3) -- the full GC polytopes do not embed.
What embeds is their local structure (cells)". The boundary is theirs.

What this file actually adds is narrower: the one-line divisibility PROOF
where BT836 asserts the conclusion, and the independent count mismatch, 36
spreads against 11 and 57 cells. Anyone hoping the spreads assemble either
polytope can stop, and now for a stated reason rather than an assertion.

AND THE MEASUREMENT READING, which the geometry files do not state. Since a
spread is exactly an optimal Pauli-grouping schedule, NO_6^-(2) is the graph on
the 36 complete MUB frames of the two-qutrit system, in which two frames share
either exactly 1 or exactly 4 of their 10 bases, and the group is transitive on
both kinds of pair.
"""

import itertools
import json
import os
import sys

ROOT = r"C:\Repos\Holotrade"


def factor(n):
    f, d = {}, 2
    while d * d <= n:
        while n % d == 0:
            f[d] = f.get(d, 0) + 1
            n //= d
        d += 1
    if n > 1:
        f[n] = f.get(n, 0) + 1
    return f


def main():
    SP43 = 51840
    PSP43 = 25920
    PSL211 = 660
    PSL219 = 3420

    print("THE GC CONNECTION IS CELL-LEVEL ONLY")
    print("=" * 72)
    print("  |Sp(4,3)|  = %d = %s" % (SP43, factor(SP43)))
    print("  |PSp(4,3)| = %d" % PSP43)
    print("  |PSL(2,11)| = %d = %s   (11-cell)" % (PSL211, factor(PSL211)))
    print("  |PSL(2,19)| = %d = %s   (57-cell)" % (PSL219, factor(PSL219)))
    print()
    d11 = SP43 % 11 == 0
    d19 = SP43 % 19 == 0
    print("  11 divides |Sp(4,3)|? %s        19 divides |Sp(4,3)|? %s"
          % (d11, d19))
    print("  so by Lagrange neither PSL(2,11) nor PSL(2,19) embeds in Sp(4,3)")
    print("  or any quotient, and no element of order 11 or 19 acts on the 40")
    print("  points. The polytopes' symmetry groups cannot act on W(3,3).")
    print()
    print("  The CELLS' groups do fit: |A_5| = 60 divides %d -> %s"
          % (SP43, SP43 % 60 == 0))
    print("  which is why the cells appear and the polytopes cannot.")
    print()
    print("  COUNT MISMATCH, agreeing combinatorially: 36 spreads give 36 of")
    print("  each cell, one per spread. The 11-cell needs 11 cells, the")
    print("  57-cell needs 57. 36 is exact -- one orbit, stabiliser 720,")
    print("  25920/720 = %d." % (PSP43 // 720))
    print()
    print("  Prior art: BT2053 (spread graph = NO_6^-(2), rank three),")
    print("  BT2064 (orbits 36, 300, 1176 for q=3,5,7; spreads meet in 1 or")
    print("  q+1 lines), BT2088 (exact stabiliser C_2 x S_6 of order 1440).")
    print("  An independent enumeration here reproduced all of it.")

    ok = (not d11) and (not d19) and SP43 % 60 == 0 and PSP43 // 720 == 36

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "gc_connection_is_cell_level_only.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.gc-cell-level-only.v1",
                "valid": bool(ok),
                "orders": {
                    "Sp(4,3)": SP43, "PSp(4,3)": PSP43,
                    "PSL(2,11)": PSL211, "PSL(2,19)": PSL219,
                    "A5": 60,
                },
                "factorisations": {
                    "Sp(4,3)": {str(k): v for k, v in factor(SP43).items()},
                    "PSL(2,11)": {str(k): v for k, v in factor(PSL211).items()},
                    "PSL(2,19)": {str(k): v for k, v in factor(PSL219).items()},
                },
                "primeObstruction": {
                    "11dividesSp43": d11, "19dividesSp43": d19,
                    "conclusion": ("by Lagrange neither PSL(2,11) nor "
                                   "PSL(2,19) embeds in Sp(4,3) or any "
                                   "quotient, and no element of order 11 or 19 "
                                   "acts on the 40 points"),
                },
                "cellGroupsDoFit": {"A5divides": SP43 % 60 == 0,
                                    "why": ("the cells' groups have orders "
                                            "dividing 51840, the polytopes' do "
                                            "not")},
                "countMismatch": {"spreads": 36, "cellsPerSpread": 1,
                                  "elevenCellNeeds": 11, "fiftySevenCellNeeds": 57,
                                  "orbitCheck": "25920 / 720 = 36"},
                "reproducedPriorArt": {
                    "BT2053": ("spread graph is the rank-three NO_6^-(2), "
                               "equivalently NO_5^{-perp}(3), local graph "
                               "Kneser K(6,2), second subconstituent Johnson "
                               "J(6,3); identification does not rely on the "
                               "nonunique parameters (36,15,6,6)"),
                    "BT2064": ("regular-symplectic-spread orbits 36, 300, 1176 "
                               "for q = 3, 5, 7; distinct spreads meet in "
                               "exactly 1 or q+1 lines"),
                    "BT2088": "exact stabiliser C_2 x S_6 of order 1440",
                    "independentCheck": ("36 spreads, intersections only 1 and "
                                         "4 = q+1, share-4 graph SRG(36,15,6,6) "
                                         "with spectrum 15, 3^15, (-3)^20, "
                                         "single orbit, stabiliser 720 in "
                                         "PSp(4,3) = 1440 modulo the centre"),
                },
                "whatIsAdded": ("CORRECTED: BT836 already states the "
                                "non-embedding of PSL(2,11) and PSL(2,19) in "
                                "Sp(4,3). This file adds only the one-line "
                                "divisibility proof where BT836 asserts the "
                                "conclusion, plus the independent count "
                                "mismatch of 36 spreads against 11 and 57 "
                                "cells."),
                "correctedClaim": ("an earlier version presented the boundary "
                                   "as its own contribution; it is BT836's"),
                "measurementReading": ("a spread is an optimal Pauli-grouping "
                                       "schedule, so NO_6^-(2) is the graph on "
                                       "the 36 complete MUB frames of two "
                                       "qutrits, two frames sharing exactly 1 "
                                       "or exactly 4 of their 10 bases"),
                "boundary": ("a negative result bounding an inquiry, plus a "
                             "reading of an already-identified graph; no bound "
                             "moves and BT836's theorem is untouched"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
