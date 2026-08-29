#!/usr/bin/env python3
"""
The 45 in their 85-point Hermitian module IS the domain of our centre map.

WHAT EACH TRACK HAD.  W33-Theory's commit fd10fd7e2, "Unify W33 and GQ(4,2) in
the 85-point Hermitian module", builds a 40 x 45 incidence B between the 40
points of W(3,3) and 45 antipodal trade-lattice minimum-vector supports, each
of size 8, with row sums 9 and column sums 8, and puts the 40 nonisotropic and
45 isotropic points of PG(3,4) in one equivariant module. Their 45 are defined
lattice-theoretically: they are the pairs of 4-subsets of W(3,3) points sharing
a column signature.

Independently, gq_tight_case_theorem.py here needs a map

    c : the 45 LINES of GQ(2,4)  ->  the 27 POINTS of GQ(2,4),

because at the depth-2 tight size every row shadow is a minimum blocker and
every minimum blocker has a centre. The whole obstruction is a statement about
what that map can be.

THE BRIDGE.  Those two 45-element sets are the same object.

GQ(4,2) is the dual of GQ(2,4): its points are the 45 lines of GQ(2,4),
adjacent when concurrent. Building both graphs from scratch --

    their 45 supports, adjacent when DISJOINT      -> SRG(45, 12, 3, 3)
    GQ(2,4)'s 45 lines, adjacent when CONCURRENT   -> SRG(45, 12, 3, 3)

-- and then matching them vertex by vertex gives an explicit isomorphism,
verified edge-by-edge on all C(45,2) = 990 pairs with zero mismatches. The
parameter agreement alone would have sufficed by the uniqueness of
SRG(45,12,3,3), but an explicit map is cheap and does not depend on quoting a
classification.

Note the sense: their adjacency is DISJOINTNESS of supports and the
quadrangle's is CONCURRENCE of lines. The isomorphism carries one to the
other, so disjoint supports correspond to concurrent lines -- not to disjoint
ones.

WHY IT MATTERS.  The obstruction proved in gq_tight_case_theorem.py says that
at the tight size the multiplicity function of c takes values in {0, 1, 5} and
sums to 5 on every line of GQ(2,4), which forces its support to be an ovoid of
GQ(2,4), and there is none. That is now a statement about a weighting of the
45 objects in THEIR module -- the same 45 that carry their Hermitian form
against W(3,3)'s 40.

So the two tracks are looking at one set from two sides: they have its
Hermitian incidence with W(3,3), we have the constraint that no {0,1,5}-valued
weighting of it can balance. Neither result needs the other, and that is
exactly what makes the identification worth recording rather than asserting a
consequence from it. No claim is made here that either result implies the
other; what is established is that the underlying set is shared, with an
explicit isomorphism to check.
"""

import itertools
import json
import os
import sys
from collections import defaultdict

ROOT = r"C:\Repos\Holotrade"


def w33_geometry():
    def norm(v):
        i = next(k for k, x in enumerate(v) if x % 3)
        z = pow(v[i] % 3, -1, 3)
        return tuple((z * x) % 3 for x in v)

    def form(u, v):
        return (u[0] * v[1] - u[1] * v[0] + u[2] * v[3] - u[3] * v[2]) % 3

    pts = sorted({norm(v) for v in itertools.product(range(3), repeat=4)
                  if any(v)})
    idx = {v: i for i, v in enumerate(pts)}
    lines = set()
    for a, b in itertools.combinations(range(40), 2):
        if form(pts[a], pts[b]):
            continue
        S = set()
        for s, t in itertools.product(range(3), repeat=2):
            if s == t == 0:
                continue
            S.add(idx[norm(tuple((s * pts[a][k] + t * pts[b][k]) % 3
                                 for k in range(4)))])
        if len(S) == 4:
            lines.add(tuple(sorted(S)))
    return pts, sorted(lines)


def their_45():
    """The 45 antipodal supports of W33-Theory's 85-point module."""
    pts, lines = w33_geometry()
    N = [[0] * 40 for _ in range(40)]
    for li, L in enumerate(lines):
        for p in L:
            N[li][p] = 1
    cols = [tuple(N[l][p] for l in range(40)) for p in range(40)]
    sig = defaultdict(list)
    for S in itertools.combinations(range(40), 4):
        z = tuple(sum(cols[p][l] for p in S) for l in range(40))
        sig[z].append(S)
    pairs = sorted(tuple(sorted((tuple(v[0]), tuple(v[1]))))
                   for v in sig.values() if len(v) == 2)
    return [set(u) | set(v) for u, v in pairs]


def gq24():
    def Qf(v):
        return (v[0] * v[1] + v[2] * v[3]
                + v[4] * v[4] + v[4] * v[5] + v[5] * v[5]) % 2

    def Bf(u, v):
        return (Qf([u[i] ^ v[i] for i in range(6)]) ^ Qf(u) ^ Qf(v)) % 2

    P = [v for v in itertools.product([0, 1], repeat=6)
         if any(v) and Qf(v) == 0]
    ix = {v: i for i, v in enumerate(P)}
    LN = set()
    for a, b in itertools.combinations(P, 2):
        if Bf(a, b) == 0:
            c = tuple(a[i] ^ b[i] for i in range(6))
            if any(c) and Qf(c) == 0:
                LN.add(tuple(sorted(ix[x] for x in (a, b, c))))
    return len(P), sorted(LN)


def srg_parameters(A, n):
    deg = {sum(r) for r in A}
    lam, mu = set(), set()
    for i, j in itertools.combinations(range(n), 2):
        c = sum(1 for k in range(n) if A[i][k] and A[j][k])
        (lam if A[i][j] else mu).add(c)
    return sorted(deg), sorted(lam), sorted(mu)


def main():
    sup = their_45()
    npts, lns = gq24()
    n = 45

    AG = [[0] * n for _ in range(n)]
    for i, j in itertools.combinations(range(n), 2):
        if not (sup[i] & sup[j]):
            AG[i][j] = AG[j][i] = 1
    DG = [[0] * n for _ in range(n)]
    for i, j in itertools.combinations(range(n), 2):
        if set(lns[i]) & set(lns[j]):
            DG[i][j] = DG[j][i] = 1

    pa = srg_parameters(AG, n)
    pd = srg_parameters(DG, n)

    try:
        import networkx as nx
    except ImportError:
        sys.exit("needs networkx:  py -3 -m pip install networkx")
    GA = nx.Graph((i, j) for i in range(n) for j in range(i + 1, n) if AG[i][j])
    GD = nx.Graph((i, j) for i in range(n) for j in range(i + 1, n) if DG[i][j])
    gm = nx.algorithms.isomorphism.GraphMatcher(GA, GD)
    iso = gm.is_isomorphic()
    mism, mapping = None, None
    if iso:
        mapping = gm.mapping
        mism = sum(1 for i in range(n) for j in range(i + 1, n)
                   if AG[i][j] != DG[mapping[i]][mapping[j]])

    print("THE 45 IS SHARED")
    print("=" * 70)
    print("  their 45 supports: %d objects, each of size %s"
          % (len(sup), sorted({len(s) for s in sup})))
    print("  GQ(2,4): %d points, %d lines" % (npts, len(lns)))
    print()
    print("  their 45, adjacent when supports DISJOINT     : SRG(45, %d, %s, %s)"
          % (pa[0][0], pa[1][0], pa[2][0]))
    print("  GQ(2,4) lines, adjacent when CONCURRENT       : SRG(45, %d, %s, %s)"
          % (pd[0][0], pd[1][0], pd[2][0]))
    print("  (this is the collinearity graph of GQ(4,2), the dual of GQ(2,4))")
    print()
    print("  explicit isomorphism found: %s" % iso)
    if iso:
        print("  verified edge-by-edge on all %d pairs, mismatches: %d"
              % (n * (n - 1) // 2, mism))
        print("  sample of the map: %s" % sorted(mapping.items())[:6])
    print()
    print("  So the domain of the centre map c : 45 lines -> 27 points, whose")
    print("  impossibility is the content of gq_tight_case_theorem.py, is the")
    print("  same 45 that carries their Hermitian incidence against W(3,3)'s")
    print("  40 in the 85-point module (commit fd10fd7e2).")
    print()
    print("  Recorded as a shared object, not as an implication: neither")
    print("  result needs the other, which is what makes the identification")
    print("  worth writing down.")

    ok = bool(iso and mism == 0 and pa == pd
              and pa[0] == [12] and pa[1] == [3] and pa[2] == [3])

    if "--write" in sys.argv:
        out = os.path.join(ROOT, "data", "gq42_bridge_to_85_point_module.json")
        with open(out, "w") as fh:
            json.dump({
                "schema": "holotrade.gq42-bridge-85-point-module.v1",
                "valid": ok,
                "claim": ("W33-Theory's 45 antipodal trade-lattice supports are "
                          "the 45 points of GQ(4,2), equivalently the 45 lines "
                          "of GQ(2,4)"),
                "theirSide": {
                    "commit": "fd10fd7e2",
                    "title": "Unify W33 and GQ(4,2) in the 85-point Hermitian module",
                    "objects": len(sup),
                    "supportSize": sorted({len(s) for s in sup}),
                    "adjacency": "supports disjoint",
                    "srg": {"degree": pa[0], "lambda": pa[1], "mu": pa[2]},
                },
                "ourSide": {
                    "objects": len(lns),
                    "adjacency": "lines concurrent (GQ(4,2) collinearity)",
                    "srg": {"degree": pd[0], "lambda": pd[1], "mu": pd[2]},
                    "role": ("domain of the centre map c : 45 lines -> 27 "
                             "points in gq_tight_case_theorem.py"),
                },
                "isomorphic": bool(iso),
                "pairsChecked": n * (n - 1) // 2,
                "mismatches": mism,
                "senseOfTheMap": ("their DISJOINTNESS corresponds to the "
                                  "quadrangle's CONCURRENCE, not to disjoint "
                                  "lines"),
                "notClaimed": ("no implication in either direction. Their "
                               "Hermitian incidence and our weighting "
                               "obstruction are independent results about one "
                               "set."),
                "boundary": ("SRG(45,12,3,3) is unique, so the parameters alone "
                             "would settle this; the explicit isomorphism is "
                             "recorded so the identification does not rest on "
                             "quoting a classification."),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(out, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
