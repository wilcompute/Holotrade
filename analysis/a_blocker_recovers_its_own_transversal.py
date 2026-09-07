#!/usr/bin/env python3
"""
A minimum blocker of W(3,3) recovers the transversal it dropped from the
centres of its nearest neighbours.

WHERE THIS SITS.  the_blocker_transversals_are_the_tetracode.py (64004ce)
computed the pairwise intersection census of the 360 minimum blockers to answer
a question about same-centre pairs, and found the tetracode there. The rest of
that census was left on the table. This reads it.

THE CENSUS IS COMPLETELY REGULAR.  Splitting the 359 other blockers by
|B n B'| gives the same degree sequence at every one of the 360:

    |B n B'|   0    1    2    3    4    5    6    8
    degree    24   48  103   48   72    8   48    8      (sum 359)

Every one of those graphs is connected EXCEPT the one at intersection 5, which
is the same-centre relation and is therefore 40 disjoint copies of K9, one per
centre -- the nine blockers at a centre, minus B itself, which is where the
tetracode came from. The other degree 8, at intersection 8, is the extreme of
the census: the closest two distinct blockers ever get, and unlike the
same-centre class it is connected.

THE THEOREM.  Let B have centre c and let D be the four-point transversal of
the pencil at c that B drops. Then B has exactly EIGHT partners B' with
|B n B'| = 8, and

    the centres of those eight partners are exactly the four points of D,
    two partners per foot.

So the transversal is not merely forced by the far triple -- it is recoverable
from the ambient structure without reference to c's pencil at all: take the
blockers closest to B, read off their centres, and that set IS what B threw
away. The relation is symmetric in the strong sense too: c is among the four
feet dropped by each of the eight partners, so the eight-graph is a symmetric
"I dropped your centre and you dropped mine" relation.

Verified on all 360 blockers, all 8 x 360 incidences, no exceptions.

The intersection-5 graph splitting into 40 cliques of 9 is not an aside: it is
the same-centre characterisation of 64004ce reappearing as a graph statement,
and it is why the intersection-8 graph is the interesting extreme rather than
the intersection-5 one.

AND THE EDGES RESPECT COLLINEARITY.  Every edge of the eight-graph joins
blockers whose centres are COLLINEAR in W(3,3) -- necessarily, since a dropped
foot is a neighbour of c. The eight-graph is 8-regular and connected on 360
vertices, so it links every centre to its neighbours and nothing else.

WHAT IS CITED.  The classification of the 360 as (c,T) and the forced 8+3 split
come from every_minimum_blocker_is_a_point_and_a_triple.py; the count nine per
centre and the 45 octets from the_minimum_blocker_labels_are_octets.py (aa42b38,
6f35762); the foot-collapse selector used to build the blockers and their drops
from the_blocker_triples_are_the_small_orbit.py (4a45d15); the intersection
census itself from the_blocker_transversals_are_the_tetracode.py (64004ce).

SCOPE.  Exhaustive: all 360 blockers, all C(360,2) = 64620 pairs. tau_2 is
untouched and stays open in [111, 115].
"""

import argparse
import collections
import itertools
import json
import os

Q = 3
N = 40
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def geometry():
    def nm(v):
        i = next(k for k, x in enumerate(v) if x % Q)
        z = pow(v[i] % Q, -1, Q)
        return tuple((z * x) % Q for x in v)

    def form(u, v):
        return (u[0] * v[1] - u[1] * v[0] + u[2] * v[3] - u[3] * v[2]) % Q

    pts = sorted({nm(v) for v in itertools.product(range(Q), repeat=4) if any(v)})
    idx = {v: i for i, v in enumerate(pts)}
    lines = set()
    for a, b in itertools.combinations(range(N), 2):
        if form(pts[a], pts[b]):
            continue
        S = set()
        for x in range(Q):
            for y in range(Q):
                if x or y:
                    S.add(idx[nm(tuple((x * pts[a][k] + y * pts[b][k]) % Q
                                       for k in range(4)))])
        if len(S) == 4:
            lines.add(tuple(sorted(S)))
    lines = sorted(lines)
    thru = [[i for i, L in enumerate(lines) if p in L] for p in range(N)]
    adj = [set() for _ in range(N)]
    for L in lines:
        for a in L:
            for b in L:
                if a != b:
                    adj[a].add(b)
    return lines, thru, adj


def blockers_at(c, lines, thru):
    """(blocker, dropped transversal) for the nine blockers with centre c."""
    perp = {y for i in thru[c] for y in lines[i]}
    far = sorted(set(range(N)) - perp)
    pencil = [[p for p in lines[i] if p != c] for i in thru[c]]
    edges = set()
    for L in lines:
        for x in itertools.combinations(sorted(set(L) & set(far)), 2):
            edges.add(frozenset(x))
    out = []
    for T in itertools.combinations(far, 3):
        if any(frozenset(x) in edges for x in itertools.combinations(T, 2)):
            continue
        feet = collections.Counter()
        for i in {i for p in T for i in thru[p]}:
            feet[[y for y in lines[i] if y in perp][0]] += 1
        if sorted(feet.values()) != [3, 3, 3, 3]:
            continue
        near = [p for L in pencil for p in L if p not in set(feet)]
        B = frozenset(near) | frozenset(T)
        assert len(B) == 11 and all(B & set(L) for L in lines)
        out.append((B, frozenset(feet)))
    return out


def components(n, nbr):
    seen, out = set(), []
    for v0 in range(n):
        if v0 in seen:
            continue
        comp, stack = {v0}, [v0]
        seen.add(v0)
        while stack:
            v = stack.pop()
            for w in nbr[v]:
                if w not in seen:
                    seen.add(w)
                    comp.add(w)
                    stack.append(w)
        out.append(len(comp))
    return sorted(out)


def connected(n, nbr):
    seen, stack = {0}, [0]
    while stack:
        v = stack.pop()
        for w in nbr[v]:
            if w not in seen:
                seen.add(w)
                stack.append(w)
    return len(seen) == n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    lines, thru, adj = geometry()
    triples = [(c, B, D) for c in range(N)
               for B, D in blockers_at(c, lines, thru)]
    assert len(triples) == 360
    C = [c for c, _, _ in triples]
    S = [B for _, B, _ in triples]
    D = [d for _, _, d in triples]

    inter = [[len(S[i] & S[j]) if i != j else -1 for j in range(360)]
             for i in range(360)]

    degrees = {}
    conn = {}
    comps = {}
    for k in [0, 1, 2, 3, 4, 5, 6, 8]:
        degs = {sum(1 for j in range(360) if inter[i][j] == k)
                for i in range(360)}
        degrees[k] = sorted(degs)
        nbr = [[j for j in range(360) if inter[i][j] == k] for i in range(360)]
        conn[k] = connected(360, nbr)
        comps[k] = components(360, nbr)
    regular = all(len(v) == 1 for v in degrees.values())
    degseq = {k: degrees[k][0] for k in degrees}
    assert sum(degseq.values()) == 359

    eight_ok = True
    pairs_ok = True
    drop_ok = True
    sym_ok = True
    collinear_ok = True
    for i in range(360):
        nb = [j for j in range(360) if inter[i][j] == 8]
        if len(nb) != 8:
            eight_ok = False
        cs = collections.Counter(C[j] for j in nb)
        if sorted(cs.values()) != [2, 2, 2, 2]:
            pairs_ok = False
        if set(cs) != set(D[i]):
            drop_ok = False
        for j in nb:
            if C[i] not in D[j]:
                sym_ok = False
            if C[j] not in adj[C[i]]:
                collinear_ok = False

    # the intersection-5 graph is the same-centre relation, so it is NOT
    # connected: it is 40 disjoint K9s. Everything else is connected.
    five_is_forty_k9s = (comps[5] == sorted([9] * 40)
                         and degseq[5] == 8
                         and all(conn[k] for k in conn if k != 5))
    ok = (regular and five_is_forty_k9s and eight_ok and pairs_ok
          and drop_ok and sym_ok and collinear_ok)

    print("W(3,3): 360 minimum blockers")
    print()
    print("THE INTERSECTION CENSUS IS COMPLETELY REGULAR")
    print("   |B n B'| : " + "".join("%6d" % k for k in sorted(degseq)))
    print("     degree : " + "".join("%6d" % degseq[k] for k in sorted(degseq)))
    print("  connected : " + "".join("%6s" % ("yes" if conn[k] else "NO")
                                     for k in sorted(degseq)))
    print("  every graph regular: %s   degrees sum to %d = 359"
          % (regular, sum(degseq.values())))
    print("  the intersection-5 graph is 40 disjoint K9s (one per centre): %s"
          % (comps[5] == sorted([9] * 40)))
    print("  every OTHER intersection graph is connected: %s"
          % all(conn[k] for k in conn if k != 5))
    print("  degree 8 at intersection 5 is the same-centre class -- the")
    print("  tetracode. Degree 8 at intersection 8 is the extreme of the census.")
    print()
    print("THE EIGHT-GRAPH THEOREM")
    print("  every blocker has exactly 8 partners at intersection 8 : %s" % eight_ok)
    print("  they fall 2-2-2-2 over four centres                    : %s" % pairs_ok)
    print("  AND THOSE FOUR CENTRES ARE THE FEET IT DROPPED         : %s" % drop_ok)
    print("  symmetric -- each partner dropped this blocker's centre: %s" % sym_ok)
    print("  every edge joins blockers with COLLINEAR centres       : %s" % collinear_ok)
    print()
    print("  so a blocker recovers the transversal it threw away from the")
    print("  centres of the blockers nearest to it, without reference to its")
    print("  own pencil.")
    print()
    print("VALID: %s" % ok)

    if args.write:
        assert ok, "checks failed -- refusing to write"
        rec = {
            "schema": "holotrade.blocker-eight-graph.v1",
            "valid": True,
            "minimumBlockers": 360,
            "pairsExamined": 360 * 359 // 2,
            "degreeByIntersection": {str(k): degseq[k] for k in sorted(degseq)},
            "degreesSumTo359": True,
            "everyGraphIsRegular": True,
            "connectedByIntersection": {str(k): conn[k] for k in sorted(conn)},
            "everyGraphConnectedExceptFive": True,
            "intersectionFiveIsFortyDisjointK9": True,
            "componentCountByIntersection":
                {str(k): len(comps[k]) for k in sorted(comps)},
            "eightPartnersEach": True,
            "partnersSplitTwoPerCentre": True,
            "partnerCentresAreTheDroppedFeet": True,
            "relationIsSymmetric": True,
            "edgesJoinCollinearCentres": True,
            "theTheorem": (
                "let B be a minimum blocker with centre c and let D be the "
                "four-point pencil transversal B drops. Then B has exactly EIGHT "
                "partners B' with |B n B'| = 8, and the centres of those eight "
                "are exactly the four points of D, two partners per foot. So the "
                "dropped transversal is recoverable from the ambient structure "
                "without reference to the pencil at c: take the blockers closest "
                "to B and read off their centres. The relation is symmetric -- c "
                "is among the four feet dropped by each partner -- so the "
                "eight-graph is an 'I dropped your centre and you dropped mine' "
                "relation, 8-regular and connected on 360 vertices."),
            "theCensusIsRegular": (
                "splitting the other 359 blockers by |B n B'| gives the SAME "
                "degree sequence at every one of the 360, and each resulting "
                "graph is connected: 24, 48, 103, 48, 72, 8, 48, 8 at "
                "intersections 0, 1, 2, 3, 4, 5, 6, 8 respectively, summing to "
                "359. Intersection 7 does not occur. Every one of those graphs is "
                "CONNECTED except the one at intersection 5, which is the "
                "same-centre relation and is therefore 40 disjoint copies of K9, "
                "one per centre -- the same-centre characterisation reappearing "
                "as a graph statement. The degree 8 at "
                "intersection 5 is the same-centre class, which is where the "
                "tetracode lives; the degree 8 at intersection 8 is the extreme "
                "of the census, the closest two distinct blockers ever get."),
            "priorArtCited": (
                "the (c,T) classification and the 8+3 split from "
                "every_minimum_blocker_is_a_point_and_a_triple.py; the count "
                "nine per centre and the 45 octets from "
                "the_minimum_blocker_labels_are_octets.py (aa42b38, 6f35762); "
                "the foot-collapse selector used to build the blockers and their "
                "drops from the_blocker_triples_are_the_small_orbit.py "
                "(4a45d15); the intersection census from "
                "the_blocker_transversals_are_the_tetracode.py (64004ce)."),
            "boundary": (
                "exhaustive over all 360 blockers and all 64620 pairs, with the "
                "eight-graph claims checked at every blocker and every one of "
                "the 2880 directed incidences rather than sampled. Connectivity "
                "is computed, not assumed. Nothing here has a q parameter: the "
                "octet construction is minimum only at q = 3, so none of this "
                "generalises off q = 3 and none is claimed to. tau_2 is "
                "untouched and stays open in [111, 115]."),
        }
        p = os.path.join(ROOT, "data", "blocker_eight_graph.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=2)
        print("written: %s" % p)


if __name__ == "__main__":
    main()
