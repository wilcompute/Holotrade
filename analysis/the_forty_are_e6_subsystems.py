#!/usr/bin/env python3
"""
The 40 coordinates of the code are E6 root subsystems: the 3A2 subsystems of
E6, adjacent when they share no root, ARE the point graph of Q(4,3).

WHY LOOK.  Two corpus threads have run side by side all session without
touching. One is geometric: the 40 points of Q(4,3), which are the 40 lines of
W(3,3), the 40 isotropic points of ker(omega), and the 40 coordinates of the
Cardinali-Giuzzi code (fe3e8fd). The other is E6: the 27-36-45 cubic-surface
triangle, |Sp(4,3)| = |W(E6)| = 51840, and the sl(3)^3 that 9a202a2 found
mis-attached to the wrong graded piece. The bridge is a counting observation:
the stabiliser of a 3A2 subsystem in W(E6) is W(A2)^3 : S3 of order
6^3 x 6 = 1296, and 51840 / 1296 = 40.

IT IS NOT A COINCIDENCE.  Building E6 explicitly:

    roots                                        72
    A2 subsystems                               120
    orthogonal triples of them (3A2)             40

and on those 40, declaring two adjacent when they SHARE NO ROOT:

    the graph is SRG(40, 12, 2, 4)
    its complement (share 6 roots) is SRG(40, 27, 18, 18)
    maximal 4-cliques                            40   -- the lines of a GQ(3,3)

WHICH GQ, AND THE DISCRIMINATOR IS THE CORPUS'S OWN.  There are exactly two
generalized quadrangles of order 3, W(3,3) and its dual Q(4,3), and their point
graphs are both SRG(40,12,2,4). They are told apart by ovoids: W(3,3) has none
for odd q, so alpha = 7 (the corpus's own coclique ovoid deficit of 3 from
tensor_multiplicativity_ovoid_defect.json), while Q(4,3) has ovoids and
alpha = q^2+1 = 10. Computing the independence number of the E6 graph exactly
gives

    alpha = 10

so it is Q(4,3), not W(3,3) -- the dual, which is the right answer: the 40
points of Q(4,3) are the 40 LINES of W(3,3), which is exactly what the code's
coordinates are.

AND THE IDENTIFICATION IS EXPLICIT, NOT PARAMETRIC.  Rather than rest on
matching SRG parameters, an isomorphism from the E6 3A2 graph to the point graph
of the parabolic quadric x0x1 + x2x3 + x4^2 was constructed by search and
verified on all 1600 ordered pairs. So the 40 A2+A2+A2 subsystems of E6 ARE the
40 points of Q(4,3), by an exhibited bijection.

WHAT THIS JOINS.  The session's coding and geometry thread and the corpus's E6
thread now meet at the 40. The code whose weight enumerator is the O(5,q) orbit
census has coordinates that are E6 root subsystems; the 45 and 36 of the orbit
partition already matched the 45 tritangents and 36 double-sixes of the Schlafli
configuration, and the 40 was the piece with no E6 meaning. It has one.

AND IT REDEEMS THE INSTINCT 9a202a2 CORRECTED.  That commit showed the corpus
attached its cubic to the wrong object: 3 (x) 3 (x) 3 is the graded piece of the
E6 ADJOINT under the Z/3-grading whose zero part is sl(3)^3, and it carries no
invariant cubic at all. But sl(3)^3 was not the wrong SUBGROUP to be looking at.
A 3A2 subsystem is precisely a choice of that Z/3-grading, and the number of
ways to install one is the 40. So the corpus's instinct to put sl(3)^3 at the
centre was right; what was wrong was which graded piece carries the cubic. The
cubic lives on the minuscule 27; the 40 is what sl(3)^3 itself counts.

NOVELTY IS NOT CLAIMED.  W(E6) = U4(2):2 = PSp(4,3).2 is a classical
isomorphism, 3A2 is a standard subsystem of E6, and the classification of
generalized quadrangles of order 3 into W(3,3) and Q(4,3) is Payne-Thas. Given
those, a rank-3 action of W(E6) on 40 objects matching Q(4,3) is the kind of
thing that is very likely known to specialists; a search turned up the
ingredients (W(E6) = U4(2):2, the 3A2 fundamental roots, rank-3 permutation
groups) but not this statement in this form, which is weak evidence and is not
treated as any. What is offered is the VERIFICATION and the corpus-local bridge,
not the mathematics.

SCOPE.  Everything here is exact and exhaustive at the single object E6 over the
integers: all 72 roots, all 120 A2 subsystems, all 40 triples, all 780 vertex
pairs, all 1600 ordered pairs under the exhibited isomorphism, and an exact
branch-and-bound independence number. There is no q parameter and nothing
generalises -- this is a statement about E6 and Q(4,3), full stop. The
discriminator alpha = 7 for W(3,3) is QUOTED from the corpus, not re-derived
here. Nothing about tau_2, the Jordan series, or the rank ceiling changes.
"""

import itertools
import json
import os
import sys

import numpy as np

ROOT = r"C:\Repos\Holotrade"


def e6_roots():
    R = []
    for i in range(5):
        for j in range(i + 1, 5):
            for si in (2, -2):
                for sj in (2, -2):
                    v = [0] * 8
                    v[i] = si
                    v[j] = sj
                    R.append(tuple(v))
    for nu in itertools.product((0, 1), repeat=5):
        if sum(nu) % 2:
            continue
        for s in (1, -1):
            v = [0] * 8
            for i in range(5):
                v[i] = s * ((-1) ** nu[i])
            v[5] = -s
            v[6] = -s
            v[7] = s
            R.append(tuple(v))
    return sorted(set(R))


def dot(a, b):
    return sum(x * y for x, y in zip(a, b)) // 4


def build():
    R = e6_roots()
    Ri = set(R)
    A2 = set()
    for a, b in itertools.combinations(R, 2):
        if dot(a, b) == -1:
            c = tuple(x + y for x, y in zip(a, b))
            if c in Ri:
                A2.add(frozenset([a, b, c] + [tuple(-x for x in z)
                                              for z in (a, b, c)]))
    A2 = sorted(A2, key=lambda s: sorted(s))

    def orth(S, T):
        return all(dot(a, b) == 0 for a in S for b in T)

    triples = [t for t in itertools.combinations(range(len(A2)), 3)
               if orth(A2[t[0]], A2[t[1]]) and orth(A2[t[0]], A2[t[2]])
               and orth(A2[t[1]], A2[t[2]])]
    T = [frozenset().union(*[A2[x] for x in t]) for t in triples]
    n = len(T)
    G = np.zeros((n, n), dtype=np.int64)
    shared = {}
    for a in range(n):
        for b in range(n):
            if a != b:
                s = len(T[a] & T[b])
                shared[s] = shared.get(s, 0) + 1
                if s == 0:
                    G[a, b] = 1
    return len(R), len(A2), n, G, shared


def quadric_graph(q=3):
    rows = []
    for i in range(5):
        for m in range(q ** (4 - i)):
            v = [0] * i + [1]
            x = m
            for _ in range(4 - i):
                v.append(x % q)
                x //= q
            rows.append(v)
    P = np.array(rows, dtype=np.int64)
    Qv = (P[:, 0] * P[:, 1] + P[:, 2] * P[:, 3] + P[:, 4] ** 2) % q
    iso = P[Qv == 0]
    M = np.array([[0, 1, 0, 0, 0], [1, 0, 0, 0, 0], [0, 0, 0, 1, 0],
                  [0, 0, 1, 0, 0], [0, 0, 0, 0, 2]], dtype=np.int64)
    m = len(iso)
    G = np.zeros((m, m), dtype=np.int64)
    for a in range(m):
        for b in range(m):
            if a != b and (iso[a] @ M @ iso[b]) % q == 0:
                G[a, b] = 1
    return G


def srg(G):
    n = G.shape[0]
    deg = sorted(set(G.sum(1).tolist()))
    CN = G @ G
    iu = np.triu_indices(n, 1)
    e = G[iu].astype(bool)
    c = CN[iu]
    lam = sorted(set(c[e].tolist()))
    mu = sorted(set(c[~e].tolist()))
    return (len(deg) == 1 and len(lam) == 1 and len(mu) == 1,
            [n, deg[0], lam[0] if lam else None, mu[0] if mu else None])


def independence(G):
    n = G.shape[0]
    adj = [set(np.nonzero(G[i])[0].tolist()) for i in range(n)]
    best = [0]

    def expand(R, P):
        if not P:
            best[0] = max(best[0], len(R))
            return
        if len(R) + len(P) <= best[0]:
            return
        v = P[0]
        expand(R | {v}, [u for u in P if u != v and u not in adj[v]])
        expand(R, [u for u in P if u != v])

    sys.setrecursionlimit(10000)
    expand(set(), list(range(n)))
    return best[0]


def find_iso(G1, G2):
    n = G1.shape[0]
    a1 = [set(np.nonzero(G1[i])[0].tolist()) for i in range(n)]
    a2 = [set(np.nonzero(G2[i])[0].tolist()) for i in range(n)]

    def search(mapping, used):
        if len(mapping) == n:
            return dict(mapping)
        v = max((x for x in range(n) if x not in mapping),
                key=lambda x: len(a1[x] & set(mapping)))
        for w in range(n):
            if w in used:
                continue
            if any(u in mapping and mapping[u] not in a2[w] for u in a1[v]):
                continue
            if any(u in mapping and u not in a1[v] and mapping[u] in a2[w]
                   for u in range(n)):
                continue
            mapping[v] = w
            used.add(w)
            r = search(mapping, used)
            if r is not None:
                return r
            del mapping[v]
            used.discard(w)
        return None

    return search({}, set())


def main():
    nroots, nA2, n, G1, shared = build()
    G2 = quadric_graph(3)
    ok1, p1 = srg(G1)
    comp = 1 - G1 - np.eye(n, dtype=np.int64)
    ok2, p2 = srg(comp)
    alpha = independence(G1)
    cliques = sum(1 for c in itertools.combinations(range(n), 4)
                  if all(G1[x, y] for x, y in itertools.combinations(c, 2)))
    m = find_iso(G1, G2)
    verified = m is not None and all(
        G1[a, b] == G2[m[a], m[b]] for a in range(n) for b in range(n))

    print("THE FORTY ARE E6 SUBSYSTEMS")
    print("=" * 72)
    print("  |W(E6)| = 51840 and the stabiliser of a 3A2 subsystem is")
    print("  W(A2)^3 : S3 of order 6^3 x 6 = 1296, so 51840/1296 = 40.")
    print()
    print("    E6 roots                       %3d" % nroots)
    print("    A2 subsystems                  %3d" % nA2)
    print("    orthogonal triples (3A2)       %3d" % n)
    print("    shared-root profile            %s" % dict(sorted(shared.items())))
    print()
    print("  Adjacent when they SHARE NO ROOT:")
    print("    SRG%s  : %s" % (tuple(p1), ok1))
    print("    complement SRG%s : %s" % (tuple(p2), ok2))
    print("    maximal 4-cliques              %3d   (the lines of a GQ(3,3))"
          % cliques)
    print()
    print("  WHICH GQ? There are exactly two of order 3, W(3,3) and its dual")
    print("  Q(4,3), both with this point-graph parameter set. Ovoids tell")
    print("  them apart: alpha(W(3,3)) = 7 (no ovoid, the corpus's own")
    print("  coclique deficit 3) and alpha(Q(4,3)) = q^2+1 = 10.")
    print("    independence number of the E6 graph = %d  ->  %s"
          % (alpha, "Q(4,3)" if alpha == 10 else "NOT Q(4,3)"))
    print("  which is the right answer: the 40 points of Q(4,3) are the 40")
    print("  LINES of W(3,3), and those are the code's coordinates.")
    print()
    print("  AND EXPLICITLY, NOT PARAMETRICALLY: an isomorphism to the point")
    print("  graph of x0x1+x2x3+x4^2 was found and checked on all %d ordered"
          % (n * n))
    print("  pairs: %s" % verified)
    print()
    print("  SO THE THREADS MEET AT THE 40. The 45 and 36 of the orbit")
    print("  partition already matched the 45 tritangents and 36 double-sixes;")
    print("  the 40 was the piece with no E6 meaning, and it has one.")
    print()
    print("  AND IT REDEEMS THE INSTINCT 9a202a2 CORRECTED: a 3A2 subsystem IS")
    print("  a choice of the Z/3-grading whose zero part is sl(3)^3, so putting")
    print("  sl(3)^3 at the centre was right -- what was wrong was which graded")
    print("  piece carries the cubic. The cubic lives on the minuscule 27; the")
    print("  40 is what sl(3)^3 itself counts.")
    print()
    print("  AND GAP CARRIES THE GROUP SIDE (w33_e6_3a2_forty.g): the action")
    print("  is FAITHFUL, transitive, rank 3 with subdegrees 1+12+27, point")
    print("  stabiliser exactly 1296 = |W(A2)^3:S3|, and StructureDescription")
    print("  names the image 'O(5,3) : C2' -- the quadric's own automorphism")
    print("  group. The 40 are Q(4,3)'s points as a G-SET, not just a graph.")
    print()
    print("  NOVELTY NOT CLAIMED: W(E6) = U4(2):2 = PSp(4,3).2 is classical,")
    print("  3A2 is a standard subsystem, and GQs of order 3 are classified")
    print("  (Payne-Thas). Only the verification and the bridge are offered.")

    ok = (nroots == 72 and nA2 == 120 and n == 40 and ok1 and ok2
          and p1 == [40, 12, 2, 4] and p2 == [40, 27, 18, 18]
          and alpha == 10 and cliques == 40 and verified)

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "forty_are_e6_subsystems.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.forty-are-e6-subsystems.v1",
                "valid": bool(ok),
                "whyLook": ("two corpus threads ran side by side all session "
                            "without touching: the 40 points of Q(4,3) -- the 40 "
                            "lines of W(3,3), the 40 isotropic points of "
                            "ker(omega), the 40 coordinates of the "
                            "Cardinali-Giuzzi code (fe3e8fd) -- and the E6 "
                            "thread, with its 27-36-45 triangle, "
                            "|Sp(4,3)| = |W(E6)| = 51840, and the sl(3)^3 that "
                            "9a202a2 found mis-attached. The bridge is a count: "
                            "the stabiliser of a 3A2 subsystem in W(E6) is "
                            "W(A2)^3 : S3 of order 6^3 x 6 = 1296, and "
                            "51840/1296 = 40"),
                "counts": {"roots": nroots, "A2subsystems": nA2,
                           "threeA2subsystems": n,
                           "sharedRootProfile": {str(k): v
                                                 for k, v in sorted(shared.items())}},
                "graph": {"adjacency": "share no root",
                          "srg": p1, "isSRG": ok1,
                          "complementSrg": p2, "complementIsSRG": ok2,
                          "maximalFourCliques": cliques},
                "whichGQ": ("there are exactly two generalized quadrangles of "
                            "order 3, W(3,3) and its dual Q(4,3), and both point "
                            "graphs are SRG(40,12,2,4); ovoids tell them apart, "
                            "alpha(W(3,3)) = 7 because W(3,q) has no ovoid for "
                            "odd q (the corpus's own coclique ovoid deficit of 3) "
                            "against alpha(Q(4,3)) = q^2+1 = 10"),
                "independenceNumber": alpha,
                "identifiedAs": "Q(4,3)" if alpha == 10 else "unresolved",
                "whyThatIsTheRightAnswer": ("the 40 points of Q(4,3) are the 40 "
                                            "LINES of W(3,3), and those are "
                                            "exactly the coordinates of the code "
                                            "whose weight enumerator is the "
                                            "O(5,q) orbit census"),
                "explicitIsomorphism": {
                    "constructed": m is not None,
                    "verifiedOnOrderedPairs": n * n,
                    "verified": bool(verified),
                    "note": ("the identification does NOT rest on matching SRG "
                             "parameters: a bijection to the point graph of "
                             "x0x1 + x2x3 + x4^2 was exhibited and checked on "
                             "every ordered pair"),
                },
                "whatThisJoins": ("the session's coding and geometry thread and "
                                  "the corpus's E6 thread now meet at the 40: the "
                                  "45 and 36 of the orbit partition already "
                                  "matched the 45 tritangents and 36 double-sixes "
                                  "of the Schlafli configuration, and the 40 was "
                                  "the piece with no E6 meaning. It has one"),
                "itRedeemsTheInstinct": ("9a202a2 showed the corpus attached its "
                                         "cubic to the wrong object -- "
                                         "3 (x) 3 (x) 3 is the graded piece of the "
                                         "E6 ADJOINT under the Z/3-grading whose "
                                         "zero part is sl(3)^3, and carries no "
                                         "invariant cubic. But sl(3)^3 was not the "
                                         "wrong SUBGROUP: a 3A2 subsystem is "
                                         "precisely a choice of that grading, and "
                                         "the number of ways to install one is the "
                                         "40. The instinct was right; the graded "
                                         "piece was wrong. The cubic lives on the "
                                         "minuscule 27; the 40 is what sl(3)^3 "
                                         "itself counts"),
                "gapCompanion": ("analysis/w33_e6_3a2_forty.g verifies the GROUP "
                                "side, which this file cannot reach: the action "
                                "of W(E6) on the 40 is FAITHFUL (kernel 1), "
                                "transitive, of rank 3 with subdegrees "
                                "1 + 12 + 27, its point stabiliser is exactly "
                                "1296 = 6^3 * 6 = |W(A2)^3 : S3|, and GAP's "
                                "StructureDescription names the image "
                                "'O(5,3) : C2' -- the automorphism group of the "
                                "parabolic quadric itself, with |P|/2 = "
                                "|PSp(4,3)| = 25920. So the 40 are the points of "
                                "Q(4,3) as a G-SET and not merely as a graph. It "
                                "emits data/e6_3a2_forty_gap.json and fails "
                                "closed on all fourteen checks"),
                "noveltyNotClaimed": ("W(E6) = U4(2):2 = PSp(4,3).2 is a classical "
                                      "isomorphism, 3A2 is a standard subsystem of "
                                      "E6, and the classification of generalized "
                                      "quadrangles of order 3 into W(3,3) and "
                                      "Q(4,3) is Payne-Thas. Given those, a rank-3 "
                                      "action of W(E6) on 40 objects matching "
                                      "Q(4,3) is very likely known to specialists; "
                                      "a search turned up the ingredients but not "
                                      "this statement in this form, which is weak "
                                      "evidence and is not treated as any. What is "
                                      "offered is the VERIFICATION and the "
                                      "corpus-local bridge, not the mathematics"),
                "boundary": ("everything is exact and exhaustive at the single "
                             "object E6 over the integers: all 72 roots, all 120 "
                             "A2 subsystems, all 40 triples, all 780 vertex pairs, "
                             "all 1600 ordered pairs under the exhibited "
                             "isomorphism, and an exact branch-and-bound "
                             "independence number. There is no q parameter and "
                             "nothing generalises -- this is a statement about E6 "
                             "and Q(4,3), full stop. The discriminator alpha = 7 "
                             "for W(3,3) is QUOTED from the corpus, not re-derived. "
                             "Nothing about tau_2, the Jordan series, or the rank "
                             "ceiling changes"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
