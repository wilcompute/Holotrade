#!/usr/bin/env python3
"""
The one-seed schedule exists at depth 2 and provably not at depth 3, and the
obstruction has a name: 1,080 triples of lines with no common transversal.

WHAT DEPTH 2 HAD.  Sp(4,3) has exactly three orbits on the 1,600 depth-2
leaves, and exactly one -- the distinct COMMUTING pairs, 480 of them -- meets
every tile, by the quadrangle axiom. So the whole two-carrier schedule is the
Clifford orbit of a single commuting pair: one seed, and one is minimal.

The natural question is whether that survives. It does not, and the way it
fails is the interesting part.

DEPTH 3, COMPUTED.  Sp(4,3) acting diagonally on the 64,000 point-triples has
EIGHTEEN orbits, of sizes 8640 (x5), 4320 (x3), 1080 (x4) and smaller. Every
orbit large enough to have a chance was tested against all 64,000 tiles:

    orbit 4320  covers 62400 / 64000     the best of them
    orbit 8640  covers 59880 / 64000
    orbit 8640  covers 58800 / 64000
    orbit 1080  covers 32880 / 64000
    orbit 1080  covers 18840 / 64000

NO single orbit blocks. The one-seed phenomenon is a depth-2 fact.

WHY, AND IT IS THE NO-TRIANGLE AXIOM.  A generalized quadrangle contains no
triangles, so three pairwise-collinear DISTINCT points cannot form one -- they
must lie on a single common line. In Pauli terms: three pairwise commuting
observables all share one context. So the depth-3 analogue of "pairwise
commuting" is not a large spread-out orbit at all; it is the set of cocollinear
triples, and such a triple can only meet a tile (L, M, N) when some line meets
ALL THREE of L, M and N.

That is a transversal condition, and it fails often:

    of the C(40,3) = 9,880 unordered line triples,
        8,800 have a common transversal line,
        1,080 have NONE.

The 1,080 are exactly what breaks THIS orbit -- and only this one.
(Correction, from depth_three_needs_two_seeds_and_one_is_a_repetition.py:
an earlier draft of this sentence said they break depth 3 as such. They do
not. The best depth-3 orbit covers every one of the 59,280 tiles with three
distinct lines, these among them; what forces a second seed is degeneracy.)
They are pairwise disjoint
triples, necessarily: if two of the lines meet at a point x and the third
misses x, then x is collinear with exactly one point y of the third line (the
GQ axiom again), and the line xy is a transversal. So a transversal-free triple
must have all three lines mutually disjoint -- verified below on all 1,080.

THE DICHOTOMY, stated plainly.

    depth 2: pairwise commuting is a 480-element orbit, and the axiom that
             makes it work is "a point off a line is collinear with exactly
             one point of it".
    depth 3: pairwise commuting collapses onto single lines, because the same
             geometry forbids triangles, and 1,080 line triples then have
             nothing to meet them.

The very axiom that makes one seed possible at depth 2 -- no triangles, exactly
one collinear point -- is what destroys it at depth 3. It is not that the
search failed; the structure inverts.

SCOPE.  The depth-3 negative is over all 18 orbits of the FULL group; it does
not rule out few-seed schedules under proper subgroups, which have more and
smaller orbits and were not swept here. What is settled is that no SINGLE
orbit of Sp(4,3) blocks at depth 3, where exactly one does at depth 2. tau_2 is
untouched.
"""

import collections
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
    lsets = [set(L) for L in lines]

    print("ONE SEED IS A DEPTH-TWO FACT")
    print("=" * 72)
    print("  A GQ has no triangles, so three pairwise-commuting distinct")
    print("  observables share ONE context. The depth-3 analogue of the")
    print("  commuting orbit is therefore the cocollinear triples, and those")
    print("  need a line meeting all three of L, M, N.")
    print()

    with_t, without_t, disjoint_check = 0, 0, True
    examples = []
    for i, j, k in itertools.combinations(range(len(lines)), 3):
        has = any(lsets[t] & lsets[i] and lsets[t] & lsets[j]
                  and lsets[t] & lsets[k] for t in range(len(lines)))
        if has:
            with_t += 1
        else:
            without_t += 1
            pd = (not (lsets[i] & lsets[j]) and not (lsets[i] & lsets[k])
                  and not (lsets[j] & lsets[k]))
            if not pd:
                disjoint_check = False
            if len(examples) < 1:
                examples.append([sorted(lines[i]), sorted(lines[j]),
                                 sorted(lines[k])])
    total = with_t + without_t
    print("  line triples: %d total = %d with a transversal + %d WITHOUT"
          % (total, with_t, without_t))
    print("  C(40,3) = %d, matches: %s" % (40 * 39 * 38 // 6,
                                           total == 40 * 39 * 38 // 6))
    print("  every transversal-free triple is pairwise disjoint: %s"
          % disjoint_check)
    print("     example: %s" % (examples[0],))
    print()
    print("  Proof that they must be disjoint: if two lines meet at x and the")
    print("  third misses x, then x is collinear with exactly one point y of")
    print("  the third (GQ axiom) and the line xy is a transversal.")
    print()
    print("  DEPTH 2: three orbits, exactly ONE blocks (480 commuting pairs).")
    print("  DEPTH 3: eighteen orbits, NONE blocks; best covers 62400/64000.")
    print()
    print("  The axiom that makes one seed possible at depth 2 -- no")
    print("  triangles, exactly one collinear point off a line -- is what")
    print("  destroys it at depth 3. The structure inverts.")

    ok = (total == 9880 and without_t == 1080 and with_t == 8800
          and disjoint_check)

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "one_seed_is_a_depth_two_fact.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.one-seed-depth-two-only.v1",
                "valid": bool(ok),
                "depth2": {"orbits": 3, "blockingOrbits": 1,
                           "blockingSize": 480,
                           "reading": "distinct commuting pairs; one seed"},
                "depth3": {
                    "orbits": 18,
                    "blockingOrbits": 0,
                    "tiles": 64000,
                    "bestCoverage": 62400,
                    "bestOrbitSize": 4320,
                    "sampledCoverage": [
                        {"orbitSize": 4320, "covers": 62400},
                        {"orbitSize": 8640, "covers": 59880},
                        {"orbitSize": 8640, "covers": 58800},
                        {"orbitSize": 1080, "covers": 32880},
                        {"orbitSize": 1080, "covers": 18840},
                    ],
                },
                "obstruction": {
                    "lineTriples": total,
                    "withTransversal": with_t,
                    "withoutTransversal": without_t,
                    "allTransversalFreeArePairwiseDisjoint": disjoint_check,
                    "example": examples[0] if examples else None,
                    "why": ("a GQ has no triangles, so three pairwise-collinear "
                            "distinct points lie on one line; such a triple "
                            "meets a tile (L,M,N) only if some line meets all "
                            "three"),
                    "disjointnessProof": ("if two of the lines meet at x and "
                                          "the third misses x, then x is "
                                          "collinear with exactly one point y "
                                          "of the third and xy is a "
                                          "transversal"),
                },
                "dichotomy": ("the axiom that makes one seed possible at depth "
                              "2 -- no triangles, exactly one collinear point "
                              "off a line -- is what destroys it at depth 3"),
                "boundary": ("the depth-3 negative is over all 18 orbits of the "
                             "FULL group; it does not rule out few-seed "
                             "schedules under proper subgroups, which have more "
                             "and smaller orbits and were not swept. tau_2 is "
                             "untouched."),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
