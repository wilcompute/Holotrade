#!/usr/bin/env python3
"""
The depth-3 obstruction is 270 isotropic reguli, and they carry GQ(4,2).

WHAT CAME BEFORE, HERE.  the_depth3_obstruction_is_non_isotropy.py found that
each of the 1,080 transversal-free line triples has exactly four transversals
in PG(3,3) and that none of them is totally isotropic -- uniformly, (4, 0),
1,080 times. This asks what those 1,080 actually ARE.

WHAT IS ALREADY OWNED ELSEWHERE, and this result sits on top of it.

  * BT810 (W33-Theory, analysis/bt810_completed_geography_schlafli.py):
    130 = 40 isotropic + 90 hyperbolic; the polarity is fixed-point-free on
    the hyperbolic lines, giving 45 polar pairs; Stab{L, L^perp} has order
    1152, index 45; and the Schlafli dictionary 27 lines / 36 double-sixes /
    40+40 Steiner triads / 45 tritangent planes = hyperbolic polar pairs.
    Each polar pair splits F3^4 = L (+) L^perp into two symplectic planes --
    a TENSOR FACTORIZATION of the two-qutrit system.
  * Pass 2023-2029 (W33-Theory) already states the regulus dichotomy: reguli
    of PG(3,q) with a totally isotropic ruling have EITHER two t.i.
    transversals OR none, by the quadratic character of -det(S), and never
    one. Their work is the two-transversal branch (regular spreads, sigma_S).
    What follows is the OTHER branch -- counted, and identified.
  * BT3769-3786 / BT3795-3812 relate GQ(4,2) to W(3,3) in the opposite
    direction, reconstructing W(3,3) from the 40 plane ovoids of GQ(4,2).
  * That 45 tritangent planes and 27 lines form GQ(4,2) is classical.

THE CENSUS.  Of the C(40,3) = 9,880 triples of W(3,3) lines,

    6,640  are not pairwise skew          (a transversal is forced)
    3,240  are pairwise skew
             2,160  have a totally isotropic transversal
             1,080  have NONE                   <- the obstruction

so the obstruction is exactly one third of the skew triples.

THE IDENTIFICATION.  Every one of the 1,080 sits inside a regulus of PG(3,3)
ALL FOUR of whose lines are totally isotropic, and there are exactly

    270 such all-isotropic reguli,   270 x C(4,3) = 1,080.

The bad triples are precisely the sub-triples of the isotropic reguli. Nothing
is left over and nothing is double counted.

AND THE OPPOSITE REGULUS IS TWO TRITANGENT PLANES.  The four transversals of
each are hyperbolic, and the set of four is CLOSED UNDER THE POLARITY,
touching exactly two of BT810's 45 polar pairs -- in all 1,080 cases. So each
isotropic regulus names an unordered PAIR of tritangent planes, and the
incidence is perfectly uniform: 48 per hyperbolic line, 96 per polar pair.

THE 270 PAIRS ARE A GENERALIZED QUADRANGLE.  Take the 45 polar pairs as
points and join two when some isotropic regulus names both. The map is
injective, so there are 270 edges, and the graph that results is not
arbitrary:

    45 vertices, 270 edges, 12-REGULAR
    maximal cliques: 27, EVERY ONE of size 5 -- nothing else survives
    each vertex in exactly 3 of them, each edge in exactly 1
    GQ axiom verified: a point off a line is collinear with exactly one
    point of it

45 points, 27 lines, 5 points per line, 3 lines per point: GQ(4,2), with the
27 lines recovered as maximal cliques rather than assumed. So the depth-3
obstruction of W(3,3) reconstructs the Schlafli quadrangle edge for edge.

WHAT THIS SAYS.  The reason no single Clifford orbit blocks at depth 3 is not
noise. The failures are indexed by a second generalized quadrangle, the one
belonging to the 27 lines, sitting inside the first. And in measurement terms
the reading of the previous file sharpens: the connecting object of a bad
triple is not a context but a PAIR OF TENSOR FACTORIZATIONS -- an entanglement
structure rather than a measurement.

SCOPE.  The dichotomy is Pass 2029's, the geography is BT810's, and GQ(4,2) on
45 tritangent planes is classical. What is computed here is the count 270, the
exact identification of the depth-3 obstruction with those reguli, the
perp-closure of the opposite regulus onto two polar pairs, and the
reconstruction of the 27 lines as maximal cliques. tau_2 is untouched and
stays open in [111, 115].
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

    def span(a, b):
        S = set()
        for x, y in itertools.product(range(Q), repeat=2):
            if x == y == 0:
                continue
            w = tuple((x * pts[a][k] + y * pts[b][k]) % Q for k in range(4))
            if any(w):
                S.add(idx[nm(w)])
        return tuple(sorted(S))

    alll = sorted({span(a, b) for a, b in itertools.combinations(range(N), 2)
                   if len(span(a, b)) == 4})
    S = [set(L) for L in alll]
    isoflag = [all(form(pts[x], pts[y]) == 0
                   for x, y in itertools.combinations(L, 2)) for L in alll]
    iso = [i for i in range(len(alll)) if isoflag[i]]
    hyp = [i for i in range(len(alll)) if not isoflag[i]]
    lookup = {L: i for i, L in enumerate(alll)}

    def perp(li):
        P = [p for p in range(N)
             if all(form(pts[p], pts[u]) == 0 for u in alll[li])]
        return lookup[tuple(sorted(P))]

    perpmap = {i: perp(i) for i in range(len(alll))}
    polar = sorted({frozenset((i, perpmap[i])) for i in hyp})
    pairid = {}
    for n_, P in enumerate(polar):
        for x in P:
            pairid[x] = n_

    print("THE DEPTH-3 OBSTRUCTION IS A QUADRANGLE")
    print("=" * 72)
    print("  BT810's geography, re-verified: %d lines = %d isotropic + %d"
          % (len(alll), len(iso), len(hyp)))
    print("  hyperbolic; the polarity is fixed-point-free, giving %d polar"
          % len(polar))
    print("  pairs = the 45 tritangent planes. Each polar pair splits")
    print("  F3^4 = L (+) L^perp: a TENSOR FACTORIZATION of the two qutrits.")
    print()

    nonskew, withti, bad = 0, 0, []
    for t in itertools.combinations(iso, 3):
        if (S[t[0]] & S[t[1]]) or (S[t[0]] & S[t[2]]) or (S[t[1]] & S[t[2]]):
            nonskew += 1
            continue
        tr = [m for m in range(len(alll)) if all(S[m] & S[x] for x in t)]
        if any(isoflag[m] for m in tr):
            withti += 1
        else:
            bad.append((t, tr))
    skew = withti + len(bad)
    print("  CENSUS of the C(40,3) = %d line triples:" % (nonskew + skew))
    print("     %5d not pairwise skew (a transversal is forced)" % nonskew)
    print("     %5d pairwise skew: %d with a t.i. transversal, %d WITHOUT"
          % (skew, withti, len(bad)))
    print("     the obstruction is exactly one third of the skew triples: %s"
          % (3 * len(bad) == skew))
    print()

    closed, npairs = collections.Counter(), collections.Counter()
    inc, pinc = collections.Counter(), collections.Counter()
    reguli, allfour, edges = set(), collections.Counter(), {}
    for t, tr in bad:
        closed[frozenset(perpmap[m] for m in tr) == frozenset(tr)] += 1
        npairs[len({pairid[m] for m in tr})] += 1
        for m in tr:
            inc[m] += 1
            pinc[pairid[m]] += 1
        R = frozenset(m for m in range(len(alll))
                      if all(S[m] & S[x] for x in tr))
        allfour[sum(1 for m in R if isoflag[m])] += 1
        reguli.add(R)
        edges[R] = frozenset(pairid[m] for m in tr)
    print("  IDENTIFICATION: every bad triple lies in a regulus whose lines")
    print("  are ALL isotropic (isotropic lines per regulus: %s)"
          % dict(allfour))
    print("     distinct all-isotropic reguli: %d, x C(4,3) = %d, and that is"
          % (len(reguli), 4 * len(reguli)))
    print("     the bad triples exactly: %s" % (4 * len(reguli) == len(bad)))
    print()
    print("  OPPOSITE REGULUS: 4 hyperbolic lines, closed under the polarity")
    print("     perp-closed: %s ; polar pairs touched: %s"
          % (dict(closed), dict(npairs)))
    print("     incidences per hyperbolic line %s (4320/90=48), per pair %s"
          % (sorted(set(inc.values())), sorted(set(pinc.values()))))
    print()

    E = {e for e in edges.values()}
    adj = collections.defaultdict(set)
    for e in E:
        a, b = tuple(e)
        adj[a].add(b)
        adj[b].add(a)
    deg = collections.Counter(len(adj[v]) for v in range(45))

    def cliques(Rr, P, X, out):
        if not P and not X:
            out.append(set(Rr))
            return
        piv = max(P | X, key=lambda u: len(adj[u] & P))
        for v in list(P - adj[piv]):
            cliques(Rr | {v}, P & adj[v], X & adj[v], out)
            P = P - {v}
            X = X | {v}

    out = []
    cliques(set(), set(range(45)), set(), out)
    sizes = collections.Counter(len(c) for c in out)
    k5 = [c for c in out if len(c) == 5]
    percover = collections.Counter(sum(1 for c in k5 if v in c)
                                   for v in range(45))
    edgecov = collections.Counter()
    for c in k5:
        for e in itertools.combinations(sorted(c), 2):
            edgecov[frozenset(e)] += 1
    gqok, bad_ex = True, None
    for c in k5:
        for p in range(45):
            if p in c:
                continue
            if sum(1 for x in c if x in adj[p]) != 1:
                gqok, bad_ex = False, (p, sorted(c))
                break
        if not gqok:
            break

    print("  THE 270 PAIRS ARE A QUADRANGLE. 45 polar pairs as points, joined")
    print("  when an isotropic regulus names both (injective: %s):"
          % (len(E) == len(reguli)))
    print("     %d vertices, %d edges, degree spectrum %s"
          % (45, len(E), dict(deg)))
    print("     maximal cliques: %d, sizes %s -- nothing else survives"
          % (len(out), dict(sizes)))
    print("     lines per point %s ; every edge in exactly one line: %s"
          % (dict(percover),
             set(edgecov.values()) == {1} and len(edgecov) == len(E)))
    print("     GQ axiom (point off a line meets it in exactly one): %s%s"
          % (gqok, "" if gqok else "  %s" % (bad_ex,)))
    print("     => 45 points, 27 lines, 5 per line, 3 per point: GQ(4,2),")
    print("        with the 27 lines RECOVERED as maximal cliques.")
    print()
    print("  So the depth-3 failures are indexed by a second generalized")
    print("  quadrangle -- the one belonging to the 27 lines -- sitting inside")
    print("  the first. The connecting object of a bad triple is not a context")
    print("  but a PAIR OF TENSOR FACTORIZATIONS.")

    ok = (len(bad) == 1080 and len(reguli) == 270 and 3 * len(bad) == skew
          and dict(allfour) == {4: 1080} and dict(closed) == {True: 1080}
          and dict(npairs) == {2: 1080} and set(inc.values()) == {48}
          and set(pinc.values()) == {96} and len(E) == 270
          and dict(deg) == {12: 45} and dict(sizes) == {5: 27}
          and dict(percover) == {3: 45} and gqok)

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data",
                         "the_depth3_obstruction_is_a_quadrangle.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.depth3-obstruction-is-gq42.v1",
                "valid": bool(ok),
                "priorArt": {
                    "BT810": ("W33-Theory: 130 = 40 isotropic + 90 hyperbolic, "
                              "polarity fixed-point-free giving 45 polar pairs "
                              "= the 45 tritangent planes, and the Schlafli "
                              "dictionary 27/36/40/40/45"),
                    "Pass2023_2029": ("W33-Theory: reguli of PG(3,q) with a "
                                      "totally isotropic ruling have either TWO "
                                      "t.i. transversals or NONE, never one, by "
                                      "the quadratic character of -det(S). "
                                      "Their work is the two-transversal "
                                      "branch; this is the other branch, "
                                      "counted and identified"),
                    "BT3769_BT3795": ("W33-Theory: relates GQ(4,2) to W(3,3) in "
                                      "the opposite direction, reconstructing "
                                      "W(3,3) from the 40 plane ovoids of "
                                      "GQ(4,2)"),
                    "classical": ("that the 45 tritangent planes and 27 lines "
                                  "of a cubic surface form GQ(4,2)"),
                },
                "census": {"total": nonskew + skew, "notPairwiseSkew": nonskew,
                           "skew": skew, "skewWithIsotropicTransversal": withti,
                           "skewWithNone": len(bad),
                           "oneThirdOfSkew": 3 * len(bad) == skew},
                "identification": {
                    "allIsotropicReguli": len(reguli),
                    "subTriplesEach": 4,
                    "product": 4 * len(reguli),
                    "exact": 4 * len(reguli) == len(bad),
                    "isotropicLinesPerRegulus": {str(k): v
                                                 for k, v in allfour.items()},
                },
                "oppositeRegulus": {
                    "perpClosed": dict(closed).get(True, 0) == len(bad),
                    "polarPairsTouched": {str(k): v
                                          for k, v in npairs.items()},
                    "incidencesPerHyperbolicLine": sorted(set(inc.values())),
                    "incidencesPerPolarPair": sorted(set(pinc.values())),
                    "reading": ("each isotropic regulus names an unordered PAIR "
                                "of tritangent planes, i.e. a pair of tensor "
                                "factorizations of the two-qutrit system"),
                },
                "quadrangle": {
                    "points": 45,
                    "edges": len(E),
                    "injective": len(E) == len(reguli),
                    "degreeSpectrum": {str(k): v for k, v in deg.items()},
                    "maximalCliques": len(out),
                    "cliqueSizes": {str(k): v for k, v in sizes.items()},
                    "linesPerPoint": {str(k): v for k, v in percover.items()},
                    "everyEdgeInExactlyOneLine": (set(edgecov.values()) == {1}
                                                  and len(edgecov) == len(E)),
                    "gqAxiom": gqok,
                    "isomorphismType": "GQ(4,2)",
                    "linesRecoveredNotAssumed": ("the 27 lines are the maximal "
                                                 "cliques of the obstruction "
                                                 "graph, not an input"),
                },
                "reading": ("no single Clifford orbit blocks at depth 3 because "
                            "the failures are indexed by a second generalized "
                            "quadrangle, the one belonging to the 27 lines, "
                            "sitting inside the first; the connecting object of "
                            "a bad triple is not a measurement context but a "
                            "pair of tensor factorizations"),
                "boundary": ("the dichotomy is Pass 2029's, the geography is "
                             "BT810's, and GQ(4,2) on 45 tritangent planes is "
                             "classical. Computed here: the count 270, the "
                             "identification of the depth-3 obstruction with "
                             "those reguli, the perp-closure onto two polar "
                             "pairs, and the 27 lines as maximal cliques. "
                             "tau_2 is untouched and stays open in [111, 115]"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
