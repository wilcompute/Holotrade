#!/usr/bin/env python3
"""
BT836's open question, answered: the 11-cell's gluing IS the Paley biplane on
11 points. And a correction to the commit before this one.

THE OPEN ITEM.  BT836 closes with two "Open" bullets. The second reads:

    "chase whether the 11-cell's Petersen-dual gluing (PSL(2,11) on 11 cells)
     is the Paley/biplane structure on 11 already implicit in the Singer Z_13 /
     F42 = Z_7 external clocks (11, 13 twin Ihara/Singer primes)."

It is. Coxeter's own construction says so once the hexad is read arithmetically.

COXETER'S CONSTRUCTION ("A Symmetrical Arrangement of Eleven Hemi-Icosahedra",
Ann. Discrete Math. 20 (1984); the 11-cell is Grunbaum 1976/77, Coxeter
independently 1984): cyclically permute the elements 0..9,t of GF(11) and take
the hexad 02678t. This yields 11 hexads; any two share three elements, forming
a triangle; each hexad contains 10 such triangles, fitting together as the
faces of the hemi-icosahedron {3,5}_5.

THE ARITHMETIC READING, which is the answer.  Mod 11 the quadratic residues
are {1,3,4,5,9} and the non-residues are {2,6,7,8,10}. So

    Coxeter's hexad 02678t  =  {0} u (quadratic NON-residues),
    its complement          =  {1,3,4,5,9}  =  the quadratic RESIDUES.

The 11 cyclic shifts of the hexad are therefore the complements of the 11
translates of the residue set -- and the translates of the quadratic residues
mod 11 are exactly the blocks of the PALEY BIPLANE, the unique 2-(11,5,2)
design. Two blocks meet in 2 points, so two hexads meet in 11 - 2*5 + 2 = 3,
which is precisely Coxeter's triangle condition.

So the 11-cell's gluing is the Paley biplane, not merely analogous to it. The
open item is closed affirmatively.

VERIFIED HERE, all of it, from the hexad up:

  * the 11 hexads pairwise meet in exactly 3;
  * their complements form a 2-(11,5,2) design -- every PAIR of points lies in
    exactly 2 blocks, checked over all 55 pairs;
  * the complement of the base hexad is exactly the quadratic residue set;
  * each hexad's 10 triangles form the hemi-icosahedron {3,5}_5: 10 faces on 6
    vertices, every vertex in 5 faces, every one of the 15 pairs in exactly 2
    faces, skeleton the complete graph K_6.

That last line is Coxeter's claim reconstructed rather than quoted, and it is
the same K_6 that BT836 finds as the hidden 6-set of a W(3,3) spread.

A CORRECTION TO THE PREVIOUS COMMIT.  gc_connection_is_cell_level_only.py
presented the non-embedding of PSL(2,11) and PSL(2,19) in Sp(4,3) as its own
contribution -- "turning 'nobody has found the polytope' into 'no such action
exists'". BT836 already states it, in its Physics/machine reading:

    "The 11-cell/57-cell groups PSL(2,11), PSL(2,19) are not subgroups of
     Sp(4,3) -- the full GC polytopes do not embed. What embeds is their local
     structure (cells), glued by the substrate's own group instead."

So the boundary is theirs. What that file actually contributed is narrower and
should have been stated as such: the one-line divisibility PROOF (11 and 19 do
not divide 51840 = 2^6 . 3^4 . 5, so Lagrange forbids it) where BT836 asserts
the conclusion, plus the independent count mismatch, 36 spreads against 11 and
57 cells. Recorded here rather than silently, since that file's own framing is
now wrong.

WHAT IS ACTUALLY NEW HERE: the identification of Coxeter's hexad as
{0} u non-residues, hence of the 11-cell's gluing as the Paley biplane, which
answers a question BT836 left open by name.

SCOPE.  This is about the 11-cell's internal structure. It does NOT put
PSL(2,11) inside Sp(4,3) -- that remains impossible -- and it does not connect
the biplane to W(3,3). It closes the arithmetic half of BT836's open bullet;
the half about the Singer Z_13 / Z_7 external clocks is untouched.
"""

import itertools
import json
import os
import sys

ROOT = r"C:\Repos\Holotrade"


def main():
    n = 11
    base = frozenset({0, 2, 6, 7, 8, 10})          # Coxeter's 02678t
    hexads = [frozenset((x + i) % n for x in base) for i in range(n)]
    QR = sorted({(x * x) % n for x in range(1, n)})
    QNR = sorted(set(range(1, n)) - set(QR))

    print("THE 11-CELL'S GLUING IS THE PALEY BIPLANE")
    print("=" * 72)
    print("  Coxeter's hexad 02678t  = %s" % sorted(base))
    print("  quadratic residues      = %s" % QR)
    print("  non-residues            = %s" % QNR)
    print("  {0} u non-residues      = %s   MATCH: %s"
          % (sorted([0] + QNR), sorted(base) == sorted([0] + QNR)))
    comp0 = sorted(set(range(n)) - base)
    print("  complement of the hexad = %s   == residues: %s"
          % (comp0, comp0 == QR))
    print()

    pair_int = {len(a & b) for a, b in itertools.combinations(hexads, 2)}
    blocks = [frozenset(set(range(n)) - h) for h in hexads]
    blk_int = {len(a & b) for a, b in itertools.combinations(blocks, 2)}
    pair_cov = {}
    for p, q in itertools.combinations(range(n), 2):
        pair_cov[(p, q)] = sum(1 for B in blocks if p in B and q in B)
    lam = set(pair_cov.values())
    print("  11 hexads, pairwise intersections: %s" % sorted(pair_int))
    print("  11 complements of size %s, pairwise intersections: %s"
          % (sorted({len(b) for b in blocks}), sorted(blk_int)))
    print("  every pair of points lies in exactly %s blocks (over all %d pairs)"
          % (sorted(lam), len(pair_cov)))
    biplane = (sorted(lam) == [2] and sorted({len(b) for b in blocks}) == [5]
               and sorted(blk_int) == [2])
    print("  -> the complements form the 2-(11,5,2) PALEY BIPLANE: %s" % biplane)
    print()

    # each hexad's 10 triangles form the hemi-icosahedron {3,5}_5
    h0 = hexads[0]
    tris = [tuple(sorted(h0 & h)) for h in hexads if h != h0]
    verts = sorted(h0)
    vdeg = {v: sum(1 for t in tris if v in t) for v in verts}
    edges = {}
    for t in tris:
        for e in itertools.combinations(sorted(t), 2):
            edges[e] = edges.get(e, 0) + 1
    k6 = len(edges) == 15 and all(v == 2 for v in edges.values())
    hemi = (len(tris) == 10 and all(len(t) == 3 for t in tris)
            and len(verts) == 6 and set(vdeg.values()) == {5} and k6)
    print("  base hexad's triangles: %d, each of size %s"
          % (len(tris), sorted({len(t) for t in tris})))
    print("     vertices %d, every vertex in %s triangles"
          % (len(verts), sorted(set(vdeg.values()))))
    print("     distinct edges %d, each in %s triangles"
          % (len(edges), sorted(set(edges.values()))))
    print("     skeleton is K_6 (all 15 pairs, each in exactly 2 faces): %s" % k6)
    print("  -> the 10 triangles form the hemi-icosahedron {3,5}_5: %s" % hemi)
    print()
    print("  So the 11-cell's gluing IS the Paley biplane on 11 points, which")
    print("  answers the second Open bullet of BT836 affirmatively.")
    print()
    print("  CORRECTION: the previous commit presented the non-embedding of")
    print("  PSL(2,11) and PSL(2,19) in Sp(4,3) as its own boundary. BT836")
    print("  already states it. That file's real contribution is the")
    print("  divisibility proof and the count mismatch, not the boundary.")

    ok = biplane and hemi and sorted(pair_int) == [3] and comp0 == QR

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data",
                         "eleven_cell_gluing_is_the_paley_biplane.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.eleven-cell-paley-biplane.v1",
                "valid": bool(ok),
                "answersOpenItem": ("BT836's second Open bullet: whether the "
                                    "11-cell's gluing is the Paley/biplane "
                                    "structure on 11. It is."),
                "coxeter": {
                    "source": ("H.S.M. Coxeter, 'A Symmetrical Arrangement of "
                               "Eleven Hemi-Icosahedra', Ann. Discrete Math. "
                               "20 (1984); polytope due to Grunbaum 1976/77"),
                    "hexad": sorted(base),
                    "construction": ("cyclically permute GF(11) and take the "
                                     "hexad 02678t; any two of the 11 share a "
                                     "triangle, and each hexad's 10 triangles "
                                     "form the hemi-icosahedron {3,5}_5"),
                },
                "arithmeticReading": {
                    "quadraticResidues": QR,
                    "nonResidues": QNR,
                    "hexadIsZeroPlusNonResidues": sorted(base) == sorted([0] + QNR),
                    "complementIsResidues": comp0 == QR,
                    "why": ("the 11 hexads are complements of the 11 translates "
                            "of the residue set, and those translates are the "
                            "blocks of the Paley biplane"),
                },
                "verified": {
                    "hexadPairIntersections": sorted(pair_int),
                    "blockSizes": sorted({len(b) for b in blocks}),
                    "blockPairIntersections": sorted(blk_int),
                    "pairsCovered": len(pair_cov),
                    "everyPairInBlocks": sorted(lam),
                    "isBiplane_2_11_5_2": biplane,
                    "triangles": len(tris),
                    "vertices": len(verts),
                    "vertexDegrees": sorted(set(vdeg.values())),
                    "distinctEdges": len(edges),
                    "edgeMultiplicities": sorted(set(edges.values())),
                    "skeletonIsK6": k6,
                    "isHemiIcosahedron": hemi,
                },
                "correctionToPreviousCommit": (
                    "gc_connection_is_cell_level_only.py presented the "
                    "non-embedding of PSL(2,11) and PSL(2,19) in Sp(4,3) as "
                    "its own boundary. BT836 already states it in its "
                    "Physics/machine reading. That file's actual contribution "
                    "is the one-line divisibility proof and the count "
                    "mismatch, not the boundary itself."),
                "boundary": ("this is about the 11-cell's internal structure. "
                             "It does NOT place PSL(2,11) inside Sp(4,3), "
                             "which remains impossible, and it does not "
                             "connect the biplane to W(3,3). BT836's Singer "
                             "Z_13 / Z_7 clock half is untouched."),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
