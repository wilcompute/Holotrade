#!/usr/bin/env python3
"""
Depth 3 needs exactly two seeds, the second one is a REPETITION, and the
1,080 turn out not to be the reason.

THE FRONTIER QUESTION.  one_seed_schedule_is_the_commuting_orbit.py proved the
whole two-carrier schedule is the Clifford orbit of a single commuting pair --
480 leaves, one seed, and one is minimal. one_seed_is_a_depth_two_fact.py then
showed no SINGLE orbit blocks at depth 3 and left the obvious question open:
how many are needed? It is two, and both halves of the answer are surprising.

THE EIGHTEEN ORBITS, named by their commuting pattern:

    4320  2 commuting pairs        covers 62400 / 64000   (x3)
    8640  1 commuting pair         covers 59880           (x3)
    8640  pairwise NON-commuting   covers 58800           (x2)
    1080  pairwise NON-commuting   covers 32880           (x2)
     960  cocollinear              covers 27400
     480  two equal, commuting     covers 20800           (x3)
    1080  two equal, non-commuting covers 18840           (x3)
      40  all equal                covers  2440

MINIMUM COVER = 2, searched exactly rather than greedily, and there are
EXACTLY THREE optimal pairs, all of the same shape:

    4320 (2 commuting pairs)  +  480 (two equal, commuting)  =  4800 leaves

THE BLIND SPOT IS POSITIONAL, and it is a theorem.  Each 4,320-orbit is a
PATH: p ~ q ~ r with the single non-commuting pair in a FIXED pair of
positions (i, j), the same for all 4,320 members. Such an orbit misses

    exactly the 1,600 tiles with L_i = L_j,     1600 = 40 x 40,

as a set equality, verified for all three orbits. The proof is one line: if
L_i = L_j then any leaf meeting the tile has both of those coordinates on one
line, so they commute -- and the orbit demands they do not.

And the partner is exactly the repair. The degenerate orbit "two equal,
commuting" with the SAME position pair (i, j) covers all 1,600. That is why
three of the nine possible pairings work and six do not: the positions must
match.

THE CORRECTION, which matters more than the count.  The previous file said the
1,080 transversal-free triples "are exactly what breaks depth 3". That is an
over-read and this refutes it. What the 1,080 break is the COCOLLINEAR orbit,
the naive analogue of depth 2's commuting pairs -- and the cocollinear orbit is
not the good one. The 4,320 path orbit covers

    ALL 40 x 39 x 38 = 59,280 tiles with three distinct lines,

every isotropic-regulus tile among them, and misses only degenerate tiles
where a line repeats. The GQ(4,2) obstruction of the_depth3_obstruction_is_a
_quadrangle.py is real and it is what kills the cocollinear orbit; it is not
what forces the second seed. Degeneracy is.

THE MEASUREMENT READING.  To block depth 3 you must be allowed to measure the
SAME observable on two carriers. A schedule built only of genuinely
three-distinct-observable measurements cannot block, no matter how large --
the 8,640-leaf orbits are twice the size of the path orbit and cover less.
The second seed is A (x) A (x) B with A ~ B: a repetition, not a refinement.

THE FRONTIER, extended by a depth:

    depth 2      1 seed      480 leaves
    depth 3      2 seeds   4,800 leaves     (exactly 3 optimal pairs)

Ten times the leaves for one more seed, and the extra seed buys degeneracy
rather than reach.

SCOPE.  This is over the FULL group Sp(4,3); proper subgroups have more and
smaller orbits and are not swept here. The 1,600-tile theorem is proved in one
direction and verified computationally in the other. tau_2 is untouched and
stays open in [111, 115].
"""

import collections
import itertools
import json
import os
import random
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
    L = len(lines)
    TT = L ** 3
    thru = [[li for li, Ln in enumerate(lines) if p in Ln] for p in range(N)]

    e = [tuple(1 if k == i else 0 for k in range(4)) for i in range(4)]

    def is_sp(A):
        for i, j in itertools.combinations(range(4), 2):
            u = tuple(sum(A[r][k] * e[i][k] for k in range(4)) % Q
                      for r in range(4))
            v = tuple(sum(A[r][k] * e[j][k] for k in range(4)) % Q
                      for r in range(4))
            if form(u, v) != form(e[i], e[j]):
                return False
        return True

    def act(A, v):
        return nm(tuple(sum(A[i][k] * v[k] for k in range(4)) % Q
                        for i in range(4)))

    rng = random.Random(11)
    gens = []
    while len(gens) < 5:
        A = tuple(tuple(rng.randrange(Q) for _ in range(4)) for _ in range(4))
        if is_sp(A):
            gens.append(tuple(idx[act(A, pts[p])] for p in range(N)))

    M = N ** 3
    parent = list(range(M))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for g in gens:
        for v in range(M):
            w = g[v // 1600] * 1600 + g[(v // 40) % 40] * 40 + g[v % 40]
            ra, rb = find(v), find(w)
            if ra != rb:
                parent[ra] = rb
    grouped = collections.defaultdict(list)
    for v in range(M):
        grouped[find(v)].append(v)
    orbs = sorted(grouped.values(), key=len, reverse=True)

    def trip(v):
        return (v // 1600, (v // 40) % 40, v % 40)

    def label(v):
        t = trip(v)
        ne = len(set(t))
        c = sum(1 for a, b in itertools.combinations(t, 2)
                if a != b and form(pts[a], pts[b]) == 0)
        if ne == 1:
            return "all equal"
        if ne == 2:
            return "two equal, %s" % ("commuting" if c else "non-commuting")
        if c == 3:
            return "cocollinear"
        if c == 2:
            return "2 commuting pairs"
        if c == 1:
            return "1 commuting pair"
        return "pairwise NON-commuting"

    def positions(v, want_equal):
        t = trip(v)
        out = set()
        for i, j in itertools.combinations(range(3), 2):
            if want_equal:
                hit = t[i] == t[j]
            else:
                hit = t[i] != t[j] and form(pts[t[i]], pts[t[j]]) != 0
            if hit:
                out.add(frozenset((i, j)))
        return frozenset(out)

    cov = []
    for members in orbs:
        s = bytearray(TT)
        for v in members:
            p_, q_, r_ = trip(v)
            for a in thru[p_]:
                a1 = a * 1600
                for b in thru[q_]:
                    ab = a1 + b * 40
                    for c in thru[r_]:
                        s[ab + c] = 1
        cov.append([len(members), label(members[0]), s, sum(s), members])
    cov.sort(key=lambda t: -t[3])

    print("DEPTH 3 NEEDS TWO SEEDS, AND ONE IS A REPETITION")
    print("=" * 72)
    print("  Sp(4,3) has %d orbits on the %d point-triples; against %d tiles:"
          % (len(orbs), M, TT))
    seen = collections.OrderedDict()
    for sz, nm_, s, k, _ in cov:
        seen.setdefault((sz, nm_, k), 0)
        seen[(sz, nm_, k)] += 1
    for (sz, nm_, k), mult in seen.items():
        print("     %5d  %-24s covers %6d / %d%s"
              % (sz, nm_, k, TT, "   (x%d)" % mult if mult > 1 else ""))
    print()

    best, sols = None, []
    for k in range(1, 5):
        for combo in itertools.combinations(range(len(cov)), k):
            if sum(cov[i][3] for i in combo) < TT:
                continue
            if all(any(cov[i][2][t] for i in combo) for t in range(TT)):
                sols.append(combo)
        if sols:
            best = k
            break
    print("  MINIMUM number of orbits that block depth 3: %s" % best)
    print("  optimal covers found: %d, all of one shape:" % len(sols))
    shapes = {tuple(sorted((cov[i][0], cov[i][1]) for i in c)) for c in sols}
    for sh in shapes:
        print("     %d leaves = %s"
              % (sum(x[0] for x in sh),
                 " + ".join("%d (%s)" % (a, b) for a, b in sh)))
    print()

    print("  THE BLIND SPOT IS POSITIONAL.")
    thm = []
    for sz, nm_, s, k, members in cov:
        if nm_ not in ("2 commuting pairs", "two equal, commuting"):
            continue
        want_eq = nm_.startswith("two equal")
        key = positions(members[0], want_eq)
        same = all(positions(v, want_eq) == key for v in members)
        (i, j) = sorted(tuple(sorted(x)) for x in key)[0]
        pred = {t for t in range(TT) if trip(t)[i] == trip(t)[j]}
        miss = {t for t in range(TT) if not s[t]}
        row = {"orbit": sz, "kind": nm_, "positions": [i, j],
               "samePositionForAll": same, "predictedTiles": len(pred),
               "misses": len(miss),
               "missesExactlyThose": miss == pred,
               "coversAllOfThem": all(s[t] for t in pred)}
        thm.append(row)
        if not want_eq:
            print("     path orbit %d, non-commuting at %s: misses %d, and that"
                  % (sz, (i, j), len(miss)))
            print("        is EXACTLY {tiles with L_%d = L_%d}: %s"
                  % (i, j, miss == pred))
        else:
            print("     degenerate orbit %d, equal at %s: covers all %d of them"
                  % (sz, (i, j), len(pred)))
    print("     1600 = 40 x 40, and the proof is one line: if L_i = L_j then")
    print("     both coordinates lie on one line, so they COMMUTE.")
    print()

    path = cov[0]
    distinct = {t for t in range(TT) if len(set(trip(t))) == 3}
    covdist = all(path[2][t] for t in distinct)
    print("  THE CORRECTION. The path orbit covers ALL %d tiles with three"
          % len(distinct))
    print("  distinct lines (40x39x38): %s -- every isotropic-regulus tile" % covdist)
    print("  among them. So the 1,080 break the COCOLLINEAR orbit, not depth-3")
    print("  blocking. Degeneracy forces the second seed, not GQ(4,2).")
    print()
    print("  FRONTIER:  depth 2   1 seed     480 leaves")
    print("             depth 3   2 seeds  4,800 leaves")
    print("  The extra seed buys degeneracy, not reach: measure the SAME")
    print("  observable on two carriers.")

    ok = (best == 2 and len(sols) == 3 and len(shapes) == 1 and covdist
          and len(distinct) == 59280
          and all(r["samePositionForAll"] for r in thm)
          and all(r["missesExactlyThose"] for r in thm
                  if r["kind"] == "2 commuting pairs")
          and all(r["coversAllOfThem"] for r in thm
                  if r["kind"] == "two equal, commuting"))

    if "--write" in sys.argv:
        p = os.path.join(
            ROOT, "data",
            "depth_three_needs_two_seeds_and_one_is_a_repetition.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.depth3-two-seeds-one-repetition.v1",
                "valid": bool(ok),
                "tiles": TT,
                "orbits": [{"size": sz, "kind": nm_, "covers": k,
                            "multiplicity": mult}
                           for (sz, nm_, k), mult in seen.items()],
                "minimumOrbits": best,
                "optimalCovers": len(sols),
                "optimalShape": [{"size": a, "kind": b}
                                 for a, b in sorted(shapes)[0]],
                "leaves": sum(x[0] for x in sorted(shapes)[0]),
                "whyThreeAndNotNine": ("the position pair of the path orbit's "
                                       "non-commuting pair must match the "
                                       "position pair of the degenerate "
                                       "orbit's equal pair"),
                "positionalTheorem": {
                    "rows": thm,
                    "statement": ("the path orbit whose unique non-commuting "
                                  "pair sits in positions (i,j) misses exactly "
                                  "the 1600 tiles with L_i = L_j"),
                    "count": "1600 = 40 x 40",
                    "proof": ("if L_i = L_j then any leaf meeting the tile has "
                              "both of those coordinates on one line, so they "
                              "commute, and the orbit demands they do not"),
                    "converseVerified": ("set equality checked on all three "
                                         "path orbits"),
                },
                "correction": {
                    "supersedes": "one_seed_is_a_depth_two_fact.py",
                    "wasSaid": ("the 1,080 transversal-free triples are exactly "
                                "what breaks depth 3"),
                    "isTrue": ("they break the COCOLLINEAR orbit, the naive "
                               "analogue of depth 2's commuting pairs"),
                    "isFalse": ("that they force the second seed -- the path "
                                "orbit covers all 59,280 tiles with three "
                                "distinct lines, every isotropic-regulus tile "
                                "among them, and fails only where a line "
                                "repeats"),
                    "distinctLineTiles": len(distinct),
                    "pathOrbitCoversThemAll": covdist,
                },
                "measurementReading": ("to block depth 3 you must be allowed to "
                                       "measure the SAME observable on two "
                                       "carriers; a schedule of only genuinely "
                                       "three-distinct-observable measurements "
                                       "cannot block, however large -- the "
                                       "8,640-leaf orbits are twice the path "
                                       "orbit's size and cover less"),
                "frontier": [
                    {"depth": 2, "seeds": 1, "leaves": 480},
                    {"depth": 3, "seeds": 2, "leaves": 4800},
                ],
                "boundary": ("over the FULL group Sp(4,3); proper subgroups have "
                             "more and smaller orbits and are not swept here. "
                             "tau_2 is untouched and stays open in [111, 115]"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
