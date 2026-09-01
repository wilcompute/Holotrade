#!/usr/bin/env python3
"""
W(3,3) and GQ(2,4) are not dual -- their orders forbid it -- but GQ(2,4) lives
inside W(3,3) as its 27 octet-factors, and the two are geometries for one group.

WHY THE QUESTION.  the_tax_tracks_blocker_richness_not_deficiency.py compared
W(3,3) with GQ(2,4) as though they were independent quadrangles that happened
to share a deficiency. Conventionally they are: W(3,3) is GQ(3,3) with dual
Q(4,3), GQ(2,4) is Q(5,2) with dual GQ(4,2), and (3,3) is not (2,4). No
isomorphism, no duality.

BUT THEY SHARE A GROUP.  PSp(4,3) = PSU(4,2) is a classical exceptional
isomorphism, so Aut(W(3,3)) and Aut(GQ(2,4)) are the same W(E6) of order
51,840. Verified here rather than quoted: PSp(4,3), built as permutations of
W(3,3)'s 40 points and of order 25,920, induces an action on the 27 that is
FAITHFUL (image order 25,920), TRANSITIVE, and of RANK 3.

AND THE 27 ARE MADE OF W(3,3).  Prior art first. The 45 induced K(4,4)
"octets" of W(3,3), and their 45-point strongly regular overlap geometry, are
W33-Theory's (BT766, recorded in BT1536). 4952a3b identified those octets with
BT810's polar-pair supports L u L^perp, and the identification is forced: L
and L^perp are orthogonal so every point of one is collinear with every point
of the other, while a hyperbolic line's four points are pairwise
non-collinear. Complete bipartite on 4 + 4. Same object, two names.

WHAT IS NEW is what the 27 LINES of GQ(4,2) do to those octets. Each is a
5-clique of them, and its five supports turn out to be pairwise disjoint and
to cover everything:

    5 x 8 = 40 = |W(3,3)|,   verified on all 27 of 27.

So each line of GQ(4,2) -- equivalently each POINT of GQ(2,4) -- is a
PARTITION of W(3,3)'s forty vertices into five vertex-disjoint induced
K(4,4)'s. A K(4,4)-FACTOR.

AND COLLINEARITY IS BLOCK-SHARING.  Two octet-factors share zero or one
blocks, never more:

    share exactly one block   135 pairs   = GQ(2,4)'s 45 lines x C(3,2)
    share none                216 pairs   = 27 x 16 / 2, its non-collinear count

Both exact. So the whole of GQ(2,4) is recovered:

    GQ(2,4) = the 27 K(4,4)-factors of W(3,3),
              two of them collinear exactly when they share a block.

THREE GEOMETRIES, ONE GROUP, ONE SPACE.  PG(3,3) has 130 lines, splitting 40
isotropic + 90 hyperbolic. The 40 are W(3,3) = GQ(3,3). The 90, paired by the
polarity, are the 45 points of GQ(4,2). The 27 factors are the points of
GQ(2,4). Orders (3,3), (4,2) and (2,4) -- three quadrangles, one W(E6), one
ambient projective space. And 40 + 45 = 85 is exactly the sentinel control
plane's carrier.

WHAT IT DOES TO THE TAX RESULT.  It makes the earlier comparison sharper, not
weaker. The 27-versus-360 blocker gap is not a comparison between unrelated
objects that happen to share a deficiency of 1; it is a comparison between two
realizations of the SAME group on the SAME space, differing precisely in where
they sit in the t-versus-s trichotomy. One group, two geometries, and the
composition tax appears in exactly one of them.

SCOPE.  The 45 octets and their overlap geometry are prior art; PSp(4,3) =
PSU(4,2) is classical; the octet/polar-pair identification is 4952a3b's. New
here: that each of the 27 lines is a K(4,4)-factor of W(3,3), the
block-sharing collinearity criterion, and the faithful rank-3 action verified
on the 27. Searched for prior art on the factors and found none. tau_2 is
untouched and stays open in [111, 115].
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

    def span(a, b):
        S = set()
        for x in range(Q):
            for y in range(Q):
                if x == y == 0:
                    continue
                w = tuple((x * pts[a][k] + y * pts[b][k]) % Q for k in range(4))
                if any(w):
                    S.add(idx[nm(w)])
        return tuple(sorted(S))

    alll = sorted({span(a, b) for a, b in itertools.combinations(range(N), 2)
                   if len(span(a, b)) == 4})
    S = [set(L) for L in alll]
    isof = [all(form(pts[x], pts[y]) == 0
                for x, y in itertools.combinations(L, 2)) for L in alll]
    iso = [i for i in range(len(alll)) if isof[i]]
    hyp = [i for i in range(len(alll)) if not isof[i]]
    lut = {L: i for i, L in enumerate(alll)}

    def perp(li):
        return lut[tuple(sorted(p for p in range(N)
                                if all(form(pts[p], pts[u]) == 0
                                       for u in alll[li])))]

    pm = {i: perp(i) for i in range(len(alll))}
    polar = sorted({frozenset((i, pm[i])) for i in hyp}, key=sorted)
    pid = {}
    for n_, P in enumerate(polar):
        for x in P:
            pid[x] = n_
    sup = [S[sorted(P)[0]] | S[sorted(P)[1]] for P in polar]

    edges = set()
    for t in itertools.combinations(iso, 3):
        if (S[t[0]] & S[t[1]]) or (S[t[0]] & S[t[2]]) or (S[t[1]] & S[t[2]]):
            continue
        tr = [m for m in range(len(alll)) if all(S[m] & S[x] for x in t)]
        if any(isof[m] for m in tr):
            continue
        edges.add(frozenset(pid[m] for m in tr))
    adj = collections.defaultdict(set)
    for e in edges:
        a, b = tuple(e)
        adj[a].add(b)
        adj[b].add(a)
    out = []

    def cl(R, P, X):
        if not P and not X:
            out.append(frozenset(R))
            return
        piv = max(P | X, key=lambda u: len(adj[u] & P))
        for v in list(P - adj[piv]):
            cl(R | {v}, P & adj[v], X & adj[v])
            P = P - {v}
            X = X | {v}

    cl(set(), set(range(45)), set())
    K5 = [c for c in out if len(c) == 5]

    print("GQ(2,4) LIVES INSIDE W(3,3) AS ITS OCTET-FACTORS")
    print("=" * 72)
    # the octets ARE induced K(4,4)s
    k44 = 0
    for v, P in enumerate(polar):
        a, b = sorted(P)
        A, B = sorted(S[a]), sorted(S[b])
        cross = all(form(pts[x], pts[y]) == 0 for x in A for y in B)
        inside = all(form(pts[x], pts[y]) != 0
                     for X in (A, B)
                     for x, y in itertools.combinations(X, 2))
        if cross and inside:
            k44 += 1
    print("  the %d polar-pair supports are induced K(4,4) octets: %d of %d"
          % (len(polar), k44, len(polar)))
    print("     L is orthogonal to L^perp so the cross pairs are all")
    print("     collinear, and a hyperbolic line's 4 points are pairwise not.")
    print()

    factors, cover = 0, collections.Counter()
    for C in K5:
        blocks = [sup[v] for v in C]
        tot = set().union(*blocks)
        disj = all(not (blocks[i] & blocks[j])
                   for i, j in itertools.combinations(range(5), 2))
        cover[(len(tot), disj)] += 1
        if disj and len(tot) == N:
            factors += 1
    print("  EACH of GQ(4,2)'s %d lines is a K(4,4)-FACTOR of W(3,3):" % len(K5))
    print("     (covered points, pairwise disjoint) -> %s" % dict(cover))
    print("     5 x 8 = %d = |W(3,3)| ; genuine factors: %d of %d"
          % (5 * 8, factors, len(K5)))
    print()

    share = collections.Counter()
    for A, B in itertools.combinations(range(len(K5)), 2):
        share[len(K5[A] & K5[B])] += 1
    print("  blocks shared by two factors: %s" % dict(share))
    print("     one block: %d = 45 lines x C(3,2) = %d  -> COLLINEAR"
          % (share[1], 45 * 3))
    print("     none:      %d = 27 x 16 / 2 = %d      -> non-collinear"
          % (share[0], 27 * 16 // 2))
    print("     never more than one: %s" % (set(share) == {0, 1}))
    print()

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
    gp = []
    while len(gp) < 3:
        A = tuple(tuple(rng.randrange(Q) for _ in range(4)) for _ in range(4))
        if is_sp(A):
            gp.append(tuple(idx[act(A, pts[p])] for p in range(N)))
    ident = tuple(range(N))
    G, seen, fr = [ident], {ident}, [ident]
    while fr:
        nx = []
        for a in fr:
            for g in gp:
                c = tuple(a[g[i]] for i in range(N))
                if c not in seen:
                    seen.add(c)
                    G.append(c)
                    nx.append(c)
        fr = nx
    lineimg = {tuple(sorted(alll[i])): i for i in range(len(alll))}
    k5idx = {c: i for i, c in enumerate(K5)}

    def on27(g):
        h = [0] * 45
        for v, P in enumerate(polar):
            a = sorted(P)[0]
            h[v] = pid[lineimg[tuple(sorted(g[p] for p in alll[a]))]]
        return tuple(k5idx[frozenset(h[v] for v in K5[i])] for i in range(27))

    imgs = {on27(g) for g in G}
    gens27 = [on27(g) for g in gp]
    lab, oid = {}, 0
    for i in range(27):
        for j in range(27):
            if (i, j) in lab:
                continue
            stack = [(i, j)]
            lab[(i, j)] = oid
            while stack:
                a, b = stack.pop()
                for h in gens27:
                    w = (h[a], h[b])
                    if w not in lab:
                        lab[w] = oid
                        stack.append(w)
            oid += 1
    seen27 = {0}
    fr = [0]
    while fr:
        nx = []
        for v in fr:
            for h in gens27:
                if h[v] not in seen27:
                    seen27.add(h[v])
                    nx.append(h[v])
        fr = nx
    print("  PSp(4,3) on 40 points: order %d. Induced on the 27:" % len(G))
    print("     faithful: %s (image order %d) ; transitive: %s ; rank %d"
          % (len(imgs) == len(G), len(imgs), len(seen27) == 27, oid))
    print("     PSp(4,3) = PSU(4,2) is why W(3,3) and GQ(2,4) share W(E6).")
    print()
    print("  => GQ(2,4) = the 27 K(4,4)-factors of W(3,3), two collinear")
    print("     exactly when they share a block.")
    print()
    print("  PG(3,3)'s 130 lines = 40 isotropic + 90 hyperbolic. The 40 are")
    print("  W(3,3) = GQ(3,3); the 90 in polarity pairs are GQ(4,2)'s 45")
    print("  points; the 27 factors are GQ(2,4)'s. Three quadrangles, one")
    print("  W(E6), one ambient space -- and 40 + 45 = 85 is the sentinel")
    print("  control plane's carrier.")

    ok = (k44 == 45 and factors == 27 and set(share) == {0, 1}
          and share[1] == 135 and share[0] == 216
          and len(G) == 25920 and len(imgs) == 25920
          and len(seen27) == 27 and oid == 3)

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data",
                         "gq24_lives_inside_w33_as_its_octet_factors.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.gq24-inside-w33-octet-factors.v1",
                "valid": bool(ok),
                "notConventionallyDual": ("W(3,3) is GQ(3,3) with dual Q(4,3); "
                                          "GQ(2,4) is Q(5,2) with dual GQ(4,2); "
                                          "(3,3) is not (2,4)"),
                "sameGroup": {
                    "fact": "PSp(4,3) = PSU(4,2), a classical isomorphism",
                    "orderOnPoints": len(G),
                    "inducedOn27Faithful": len(imgs) == len(G),
                    "imageOrder": len(imgs),
                    "transitive": len(seen27) == 27,
                    "rank": oid,
                    "autOrder": 51840,
                },
                "octetsAreK44": {"count": k44, "of": len(polar),
                                 "priorArt": ("the 45 induced K(4,4) octets and "
                                              "their 45-point overlap geometry "
                                              "are W33-Theory's BT766, recorded "
                                              "in BT1536"),
                                 "identification": ("4952a3b matched them with "
                                                    "BT810's polar-pair supports "
                                                    "L u L^perp")},
                "octetFactors": {
                    "count": factors, "of": len(K5),
                    "blocksEach": 5, "blockSize": 8,
                    "covers": 5 * 8,
                    "statement": ("each of GQ(4,2)'s 27 lines partitions "
                                  "W(3,3)'s 40 vertices into five vertex-"
                                  "disjoint induced K(4,4)s"),
                },
                "collinearityIsBlockSharing": {
                    "sharedBlockCounts": {str(k): v
                                          for k, v in sorted(share.items())},
                    "neverMoreThanOne": set(share) == {0, 1},
                    "shareOne": share[1], "expectedCollinear": 45 * 3,
                    "shareNone": share[0], "expectedNonCollinear": 27 * 16 // 2,
                },
                "theStatement": ("GQ(2,4) = the 27 K(4,4)-factors of W(3,3), "
                                 "two collinear exactly when they share a "
                                 "block"),
                "threeGeometriesOneGroup": ("PG(3,3)'s 130 lines are 40 "
                                            "isotropic + 90 hyperbolic; the 40 "
                                            "are W(3,3) = GQ(3,3), the 90 in "
                                            "polarity pairs are GQ(4,2)'s 45 "
                                            "points, and the 27 factors are "
                                            "GQ(2,4)'s -- orders (3,3), (4,2) "
                                            "and (2,4) for one W(E6) in one "
                                            "ambient space, with 40 + 45 = 85 "
                                            "the sentinel control plane's "
                                            "carrier"),
                "effectOnTheTaxResult": ("it makes the earlier comparison "
                                         "sharper: the 27-versus-360 blocker "
                                         "gap is not between unrelated objects "
                                         "sharing a deficiency, but between two "
                                         "realizations of the same group on the "
                                         "same space, differing only in where "
                                         "they sit in the t-versus-s "
                                         "trichotomy"),
                "boundary": ("the 45 octets and their overlap geometry are "
                             "prior art; PSp(4,3) = PSU(4,2) is classical; the "
                             "octet/polar-pair identification is 4952a3b's. New "
                             "here: that each of the 27 lines is a K(4,4)-factor, "
                             "the block-sharing collinearity criterion, and the "
                             "faithful rank-3 action on the 27. tau_2 is "
                             "untouched and stays open in [111, 115]"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
