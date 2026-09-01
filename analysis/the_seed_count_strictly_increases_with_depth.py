#!/usr/bin/env python3
"""
1, 2, at least 3: the seed count strictly increases with depth, and both jumps
are theorems rather than searches.

WHAT WAS MEASURED.  Depth 2 needs one Clifford orbit (the 480 commuting pairs);
depth 3 needs exactly two (a 4,320 path orbit plus the 480 degenerate orbit that
repairs its positional blind spot). Both of those came from enumeration. This
file replaces the enumeration with proofs, and the proofs then run past the
depths a computer can enumerate.

Everything rests on three facts about an Sp(4,3) orbit O of point n-tuples and
the tiles (L_1, ..., L_n) it must meet:

  (E)  equality and commuting are Sp(4,3)-invariant, so the PATTERN of O --
       which positions are equal, which commute -- is the same at every leaf.
  (C)  two points of one line commute.
  (T)  a GQ has no triangles, so pairwise-collinear distinct points are
       cocollinear; and 1,080 line triples admit no transversal at all
       (the_depth3_obstruction_is_a_quadrangle.py: they are the sub-triples of
       the 270 all-isotropic reguli, and their lines are pairwise disjoint).

THEOREM A.  For every n >= 3, NO single Sp(4,3) orbit blocks the depth-n tiles.

    Proof, three cases on the pattern of O, exhaustive by (E).
      1. Some pair (i, j) is non-commuting in O. Any leaf meeting a tile with
         L_i = L_j puts both coordinates on one line, so by (C) they commute --
         and O forbids that. Every tile with L_i = L_j is missed.
      2. Some pair (i, j) is equal in O. Then p_i = p_j lies in L_i and in
         L_j, so every tile with L_i, L_j disjoint is missed, and W(3,3) has
         disjoint line pairs (27 for each line).
      3. Otherwise all n coordinates are distinct and pairwise commuting. By
         (T) they are cocollinear, on one line M. Take a tile whose first three
         lines are a transversal-free triple: M would meet all three, and none
         exists.                                                            []

At n = 2 case 3 does not close -- two points are always cocollinear and any two
lines DO have a transversal -- which is exactly why depth 2 has its one seed.
The theorem begins where the third point does.

THEOREM B.  For every n >= 4, TWO orbits do not suffice either.

    Proof. Suppose O_a, O_b cover everything. The tile (L, L, ..., L) forces
    all coordinates of some leaf onto one line, so by (C) one of them -- say
    O_a -- has a pattern that is all commuting-or-equal. By Theorem A case 3
    O_a is not blocking, so it is not all-DISTINCT-and-commuting either; and
    O_b, which must cover what O_a misses, is not all commuting-or-equal, so it
    has a non-commuting pair (i, j).

    Now build one witness. Choose a transversal-free triple (L, L_k, L_l) --
    its three lines are pairwise disjoint -- and the tile with L_i = L_j = L,
    the two remaining positions carrying L_k and L_l, and any lines elsewhere.

      * O_b misses it by case 1: L_i = L_j.
      * O_a misses it too. A leaf of O_a has p_i in L, p_k in L_k, p_l in L_l.
        The three lines are pairwise disjoint, so those three points are
        pairwise distinct, and O_a's pattern makes them pairwise commuting.
        By (T) they lie on one line, which then meets L, L_k and L_l -- a
        transversal of a transversal-free triple.                           []

    n >= 4 is needed: at n = 3 the repeated pair uses two of the three
    positions and only ONE is left for the bad triple, which needs two. And
    indeed two orbits DO suffice at depth 3.

SO THE COUNTS ARE  1, 2, >= 3  at depths 2, 3, 4, and the two jumps have
different causes. The first is degeneracy -- depth 3 must be allowed to repeat
an observable. The second is the transversal-free triples, i.e. GQ(4,2): at
depth 4 there is finally room to put a repeated line and a bad triple in the
same tile, and no pair of orbits survives that.

That also settles the standing of the 1,080. They are not what forces the
second seed (the path orbit covers every tile with distinct lines). They are
what forces the THIRD.

WHAT IS VERIFIED BELOW.  The finite ingredients, and the witness explicitly:
for each of the six position pairs at depth 4 a witness tile is built and all
4^4 = 256 of its leaves are enumerated, confirming that none is all
commuting-or-equal and that every one has the (i, j) pair commuting or equal.
Both orbits therefore miss it, with no appeal to the proof.

SCOPE.  Lower bounds only, over the full group Sp(4,3). Whether three orbits
SUFFICE at depth 4 is open here -- the depth-4 coverage computation was not
run. Proper subgroups are not swept. tau_2 is untouched and stays open in
[111, 115].
"""

import itertools
import json
import os
import sys

ROOT = r"C:\Repos\Holotrade"
Q = 3
N = 40


def main():
    def nm(v):
        i = next(k for k, x in enumerate(v) if x % Q)
        z = pow(v[i] % Q, -1, Q)
        return tuple((z * x) % Q for x in v)

    def form(u, v):
        return (u[0] * v[1] - u[1] * v[0] + u[2] * v[3] - u[3] * v[2]) % Q

    pts = sorted({nm(v) for v in itertools.product(range(Q), repeat=4)
                  if any(v)})
    idx = {v: i for i, v in enumerate(pts)}
    lines = set()
    for a, b in itertools.combinations(range(N), 2):
        if form(pts[a], pts[b]):
            continue
        S = set()
        for x, y in itertools.product(range(Q), repeat=2):
            if x == y == 0:
                continue
            S.add(idx[nm(tuple((x * pts[a][k] + y * pts[b][k]) % Q
                               for k in range(4)))])
        if len(S) == 4:
            lines.add(tuple(sorted(S)))
    lines = sorted(lines)
    LS = [set(L) for L in lines]

    print("THE SEED COUNT STRICTLY INCREASES WITH DEPTH")
    print("=" * 72)

    # (C) two points of one line commute
    C = all(form(pts[a], pts[b]) == 0 for L in lines
            for a, b in itertools.combinations(L, 2))
    # case 2's ingredient: disjoint line pairs exist, 27 per line
    disj = {sum(1 for M in LS if not (M & L)) for L in LS}
    # (T) transversal-free triples, and their pairwise disjointness
    bad = []
    for t in itertools.combinations(range(len(lines)), 3):
        if any(LS[m] & LS[t[0]] and LS[m] & LS[t[1]] and LS[m] & LS[t[2]]
               for m in range(len(lines))):
            continue
        bad.append(t)
    bad_disjoint = all(not (LS[t[0]] & LS[t[1]]) and not (LS[t[0]] & LS[t[2]])
                       and not (LS[t[1]] & LS[t[2]]) for t in bad)
    # no triangles: pairwise collinear distinct points are cocollinear
    notri = True
    for a, b, c in itertools.combinations(range(N), 3):
        if (form(pts[a], pts[b]) == 0 and form(pts[a], pts[c]) == 0
                and form(pts[b], pts[c]) == 0):
            if not any({a, b, c} <= L for L in LS):
                notri = False
                break

    print("  INGREDIENTS")
    print("     (C) two points of one line commute: %s" % C)
    print("     (T) no triangles -- pairwise collinear distinct points are")
    print("         cocollinear: %s" % notri)
    print("     (T) transversal-free line triples: %d, all pairwise disjoint: %s"
          % (len(bad), bad_disjoint))
    print("     case 2: disjoint lines per line: %s" % sorted(disj))
    print()

    print("  THEOREM A. For n >= 3 no single orbit blocks, by three cases:")
    print("     1. a non-commuting pair (i,j) misses every tile with L_i = L_j")
    print("     2. an equal pair (i,j) misses every tile with L_i, L_j disjoint")
    print("     3. all distinct and commuting => cocollinear => needs a")
    print("        transversal of a transversal-free triple")
    print("     At n = 2 case 3 does not close: two points are always")
    print("     cocollinear and two lines always have a transversal. That is")
    print("     exactly why depth 2 has one seed.")
    print()

    # THEOREM B's witness, made explicit at depth 4
    L0, Lk, Ll = bad[0]
    rows = []
    for (i, j) in itertools.combinations(range(4), 2):
        rest = [x for x in range(4) if x not in (i, j)]
        tile = [None] * 4
        tile[i] = tile[j] = L0
        tile[rest[0]], tile[rest[1]] = Lk, Ll
        allcomm, ijsafe = 0, 0
        for leaf in itertools.product(*[sorted(LS[x]) for x in tile]):
            ok = all(a == b or form(pts[a], pts[b]) == 0
                     for a, b in itertools.combinations(leaf, 2))
            if ok:
                allcomm += 1
            if leaf[i] == leaf[j] or form(pts[leaf[i]], pts[leaf[j]]) == 0:
                ijsafe += 1
        rows.append({"positions": [i, j], "tile": tile, "leaves": 256,
                     "allCommutingOrEqualLeaves": allcomm,
                     "leavesWithIJCommutingOrEqual": ijsafe})
        print("  WITNESS at depth 4, repeated pair %s: of 256 leaves, %d are"
              % ((i, j), allcomm))
        print("     all commuting-or-equal (so O_a misses), and %d/256 have"
              % ijsafe)
        print("     positions %s commuting or equal (so O_b misses)." % ((i, j),))
    witness_ok = all(r["allCommutingOrEqualLeaves"] == 0
                     and r["leavesWithIJCommutingOrEqual"] == 256
                     for r in rows)
    print()
    print("  every witness kills BOTH orbits: %s" % witness_ok)
    print()
    print("  COUNTS:  depth 2 -> 1 seed    depth 3 -> 2    depth 4 -> >= 3")
    print("  The jumps have different causes: degeneracy first, then the")
    print("  transversal-free triples. So the 1,080 do not force the second")
    print("  seed -- they force the THIRD.")

    ok = (C and notri and len(bad) == 1080 and bad_disjoint and disj == {27}
          and witness_ok)

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data",
                         "the_seed_count_strictly_increases_with_depth.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.seed-count-increases-with-depth.v1",
                "valid": bool(ok),
                "ingredients": {
                    "twoPointsOfALineCommute": C,
                    "noTriangles": notri,
                    "transversalFreeTriples": len(bad),
                    "transversalFreeTriplesArePairwiseDisjoint": bad_disjoint,
                    "disjointLinesPerLine": sorted(disj),
                    "patternIsAnOrbitInvariant": ("equality and commuting are "
                                                  "Sp(4,3)-invariant"),
                },
                "theoremA": {
                    "statement": ("for every n >= 3 no single Sp(4,3) orbit "
                                  "blocks the depth-n tiles"),
                    "cases": [
                        "a non-commuting pair (i,j) misses every tile with "
                        "L_i = L_j, since two points of one line commute",
                        "an equal pair (i,j) misses every tile with L_i and "
                        "L_j disjoint",
                        "all distinct and pairwise commuting forces "
                        "cocollinearity, which needs a transversal of a "
                        "transversal-free triple",
                    ],
                    "whyNotAtN2": ("two points are always cocollinear and two "
                                   "lines always have a transversal, so case 3 "
                                   "does not close -- which is why depth 2 has "
                                   "one seed"),
                },
                "theoremB": {
                    "statement": ("for every n >= 4 two orbits do not suffice"),
                    "proof": ("the tile (L,...,L) forces one orbit to be all "
                              "commuting-or-equal; the other must then have a "
                              "non-commuting pair (i,j); the tile with "
                              "L_i = L_j = L and a transversal-free triple "
                              "(L, L_k, L_l) in two further positions defeats "
                              "both"),
                    "whyNotAtN3": ("the repeated pair uses two of the three "
                                   "positions and the bad triple needs two "
                                   "more; and two orbits do suffice at depth 3"),
                    "witnesses": rows,
                    "everyWitnessKillsBoth": witness_ok,
                },
                "counts": [
                    {"depth": 2, "seeds": 1, "status": "exact"},
                    {"depth": 3, "seeds": 2, "status": "exact"},
                    {"depth": 4, "seeds": 3, "status": "lower bound"},
                ],
                "standingOfThe1080": ("they are not what forces the second seed "
                                      "-- the depth-3 path orbit covers every "
                                      "tile with distinct lines -- they are "
                                      "what forces the third"),
                "boundary": ("lower bounds only, over the full group Sp(4,3). "
                             "Whether three orbits SUFFICE at depth 4 is open "
                             "here; the depth-4 coverage computation was not "
                             "run. Proper subgroups are not swept. tau_2 is "
                             "untouched and stays open in [111, 115]"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
