#!/usr/bin/env python3
"""
The slow path has four spare minimal covers per opcode, and nobody had counted
them: the 200 covers form a 5-to-1 fibration over the 40 cheap opcode axes.

WHERE THIS STARTS.  8982d36 found 200 ovoids of the cost quadrangle in PSp(4,3)
orbits of 40 and 160, and showed the 40 are the cheap opcode axes. The parallel
track then identified those 40 as the Payne covers -- fixing an axis and
Payne-deriving W(3,3) gives 36 inherited lines plus 9 new hyperbolic ones, and
the 9 are exactly a cover (data/slow_path_is_payne_derivative.json). Both pieces
of work use the 40 and neither says anything about the other 160. That is 80% of
the covers, unexamined.

EVERY COVER IS ANCHORED, INCLUDING THE OTHER 160.

    stabiliser orders over the 200        {648: 40, 162: 160}
    W(3,3) points fixed by the stabiliser  {1: 200}

Every single one of the 200 -- not just the plane ovoids -- has a stabiliser
fixing exactly ONE point of W(3,3). So the guess that the other 160 would be
unaddressable is simply false; they are anchored too, just by a smaller group
(162 rather than 648, index 4 inside the point stabiliser).

AND THE FIBRATION IS UNIFORM.

    covers anchored per opcode axis        5, at every one of the 40
    composition                            1 plane + 4 other, at every axis
    the 4 alternates under Stab(axis)      a single orbit
    40 x 5 = 200

So the anchor map is a clean 5-to-1 fibration of the 200 minimal covers onto the
40 opcode axes. Each axis gets one canonical cover -- the Payne one the parallel
track built -- and four alternates, and the four are equivalent under the axis's
own stabiliser, so none of them is distinguished.

WHAT THAT IS, OPERATIONALLY.  A cover is 9 slow targets meeting every one of the
27 ROM banks exactly once. The parallel track's decoder uses the canonical one
per axis. This says there are four more, per axis, of equal standing: 160 spare
minimal covers that the current design does not use. That is redundancy
available for free -- an alternate cover to fall back on if a bank is corrupt,
or four independent covers to cross-check a decode against, with the symmetry
guaranteeing no alternate is worse than another.

THE FIVE IS NOT THE OTHER FIVE, AND THAT MATTERS.  The parallel track has an
F20 Payne FIVE-state atlas built on five pairwise non-collinear slow targets,
where F20 = AGL(1,5) acts on five things transitively. The five here is a
different five: the axis stabiliser acts on its fibre with orbits 1 + 4, NOT
transitively, so no group in sight permutes these five covers as AGL(1,5)
permutes five points. Matching the integers would be exactly the error this
repository keeps paying for. They are two distinct fives.

THE INTERSECTION GEOMETRY.

    |plane n plane|      {1: 540, 3: 240}
    |other n plane|      {0: 1600, 2: 4320, 6: 480}
    |other n other|      computed in full below

Two canonical covers always share 1 or 3 targets and never miss each other
entirely, while an alternate can be disjoint from a canonical one -- 1600 pairs
share nothing at all. So the alternates genuinely reach parts of the slow path
that a given canonical cover does not, which is what makes them useful as
fallbacks rather than as near-duplicates.

SCOPE.  Exhaustive: all 200 covers by complete exact-cover search, orbits and
stabilisers by closure over the full 25,920-element group, anchors by fixed-point
computation on every one of the 200, and the intersection census over all pairs.
The identification of the 40 with the Payne covers is the parallel track's
(slow_path_is_payne_derivative.json), cited not re-derived. No claim is made
that the four alternates have a Payne description -- they are anchored but their
derivation, if any, is not built here. tau_2 is untouched.
"""

import collections
import itertools
import json
import os
import sys

ROOT = r"C:\Repos\Holotrade"
Q = 3
D = 4


def main():
    def mul(A, B):
        return tuple(tuple(sum(A[i][k] * B[k][j] for k in range(D)) % Q
                           for j in range(D)) for i in range(D))

    I = tuple(tuple(1 if i == j else 0 for j in range(D)) for i in range(D))
    mI = tuple(tuple((-1 if i == j else 0) % Q for j in range(D))
               for i in range(D))

    def form(u, v):
        return (u[0] * v[2] - u[2] * v[0] + u[1] * v[3] - u[3] * v[1]) % Q

    E = [tuple(1 if k == j else 0 for k in range(D)) for j in range(D)]

    def tv(vv, lam):
        return tuple(tuple(((1 if i == j else 0)
                            + lam * form(E[j], vv) * vv[i]) % Q
                           for j in range(D)) for i in range(D))

    def minv(A):
        Aug = [[A[i][j] for j in range(D)]
               + [1 if i == j else 0 for j in range(D)] for i in range(D)]
        r = 0
        for c in range(D):
            p = next((i for i in range(r, D) if Aug[i][c] % Q), None)
            Aug[r], Aug[p] = Aug[p], Aug[r]
            iv = pow(Aug[r][c], -1, Q)
            Aug[r] = [(x * iv) % Q for x in Aug[r]]
            for i in range(D):
                if i != r and Aug[i][c] % Q:
                    f = Aug[i][c]
                    Aug[i] = [(Aug[i][j] - f * Aug[r][j]) % Q
                              for j in range(2 * D)]
            r += 1
        return tuple(tuple(Aug[i][D + j] for j in range(D)) for i in range(D))

    vecs = [v for v in itertools.product(range(Q), repeat=D) if any(v)]
    T = sorted({tv(v, l) for v in vecs for l in (1, 2)} - {I})
    dist, fr, d0 = {I: 0}, [I], 0
    while fr:
        nx = []
        for A in fr:
            for M2 in T:
                C = mul(M2, A)
                if C not in dist:
                    dist[C] = d0 + 1
                    nx.append(C)
        fr = nx
        if nx:
            d0 += 1

    def rk(A):
        M2 = [[(A[i][j] - (1 if i == j else 0)) % Q for j in range(D)]
              for i in range(D)]
        r = 0
        for c in range(D):
            p = next((i for i in range(r, D) if M2[i][c] % Q), None)
            if p is None:
                continue
            M2[r], M2[p] = M2[p], M2[r]
            iv = pow(M2[r][c], -1, Q)
            M2[r] = [(x * iv) % Q for x in M2[r]]
            for i in range(D):
                if i != r and M2[i][c] % Q:
                    f = M2[i][c]
                    M2[i] = [(M2[i][j] - f * M2[r][j]) % Q for j in range(D)]
            r += 1
        return r

    reps = sorted({min(A, mul(mI, A)) for A, Lg in dist.items()
                   if Lg == 3 and rk(A) == 2})
    NA = len(reps)
    adjm = [[0] * NA for _ in range(NA)]
    for i, j in itertools.combinations(range(NA), 2):
        if mul(reps[i], reps[j]) == mul(mI, mul(reps[j], reps[i])):
            adjm[i][j] = adjm[j][i] = 1
    cl = []

    def bk(R, P, X):
        if not P and not X:
            cl.append(frozenset(R))
            return
        for v in list(P):
            bk(R | {v}, {u for u in P if adjm[v][u]},
               {u for u in X if adjm[v][u]})
            P = P - {v}
            X = X | {v}

    bk(set(), set(range(NA)), set())
    LN = [sorted(c) for c in cl if len(c) == 5]
    M = len(LN)
    lines_of = collections.defaultdict(list)
    for k, ln in enumerate(LN):
        for p in ln:
            lines_of[p].append(k)

    ovoids = []

    def ov(ch, cov):
        if len(ch) == 9:
            if len(cov) == M:
                ovoids.append(frozenset(ch))
            return
        rem = [k for k in range(M) if k not in cov]
        if not rem:
            return
        for p in LN[rem[0]]:
            if any(x in cov for x in lines_of[p]):
                continue
            ov(ch + [p], cov | set(lines_of[p]))

    ov([], set())

    def nm(v):
        i = next(k for k, x in enumerate(v) if x % Q)
        z = pow(v[i] % Q, -1, Q)
        return tuple((z * x) % Q for x in v)

    pts = sorted({nm(v) for v in vecs})
    pidx = {p: i for i, p in enumerate(pts)}
    idx45 = {}
    for i, g in enumerate(reps):
        idx45[g] = i
        idx45[mul(mI, g)] = i
    seenm, fr = {I}, [I]
    while fr:
        nx = []
        for A in fr:
            for t in T:
                B = mul(t, A)
                if B not in seenm:
                    seenm.add(B)
                    nx.append(B)
        fr = nx
    G = {}
    for A in seenm:
        a40 = tuple(pidx[nm(tuple(sum(A[i][k] * p[k] for k in range(D)) % Q
                                  for i in range(D)))] for p in pts)
        Ai = minv(A)
        a45 = tuple(idx45[mul(mul(A, reps[i]), Ai)] for i in range(NA))
        G[(a40, a45)] = True
    Gl = list(G)

    seenx, orbs = set(), []
    for o in ovoids:
        if o in seenx:
            continue
        orb, f2 = {o}, [o]
        while f2:
            nx = []
            for x in f2:
                for k in Gl:
                    y = frozenset(k[1][p] for p in x)
                    if y not in orb:
                        orb.add(y)
                        nx.append(y)
            f2 = nx
        seenx |= orb
        orbs.append(orb)
    O40 = next((o for o in orbs if len(o) == 40), set())
    O160 = next((o for o in orbs if len(o) == 160), set())

    stabsz, fixn, anchor, kind = collections.Counter(), collections.Counter(), {}, {}
    for o in ovoids:
        S = [k for k in Gl if frozenset(k[1][p] for p in o) == o]
        F = [p for p in range(40) if all(k[0][p] == p for k in S)]
        stabsz[len(S)] += 1
        fixn[len(F)] += 1
        if len(F) == 1:
            anchor[o] = F[0]
        kind[o] = "plane" if o in O40 else "other"

    per = collections.defaultdict(collections.Counter)
    for o, p in anchor.items():
        per[p][kind[o]] += 1
    prof = collections.Counter(tuple(sorted(v.items())) for v in per.values())
    tot = collections.Counter(sum(v.values()) for v in per.values())

    p0 = sorted(per)[0]
    alts = [o for o, p in anchor.items() if p == p0 and kind[o] == "other"]
    S0 = [k for k in Gl if k[0][p0] == p0]
    orb, f2 = {alts[0]}, [alts[0]]
    while f2:
        nx = []
        for x in f2:
            for k in S0:
                y = frozenset(k[1][q] for q in x)
                if y not in orb:
                    orb.add(y)
                    nx.append(y)
        f2 = nx
    alts_one_orbit = len(orb) == len(alts)
    stab_orbits_on_fibre = sorted(
        [1, len(orb)]) if alts_one_orbit else None

    ipp = collections.Counter()
    for a, b in itertools.combinations(sorted(O40, key=sorted), 2):
        ipp[len(a & b)] += 1
    iop = collections.Counter()
    for a in O160:
        for b in O40:
            iop[len(a & b)] += 1
    ioo = collections.Counter()
    for a, b in itertools.combinations(sorted(O160, key=sorted), 2):
        ioo[len(a & b)] += 1

    print("EVERY OPCODE AXIS ANCHORS FIVE COVERS")
    print("=" * 72)
    print("  stabiliser orders over the 200 covers   %s" % dict(stabsz))
    print("  W(3,3) points fixed by the stabiliser   %s" % dict(fixn))
    print("  -> EVERY cover is anchored at a unique axis, the other 160 too;")
    print("     the guess that they would be unaddressable is false.")
    print()
    print("  covers anchored per opcode axis         %s" % dict(tot))
    print("  composition at every axis               %s" % dict(prof))
    print("  the 4 alternates under Stab(axis)       one orbit: %s"
          % alts_one_orbit)
    print("  40 x 5 = %d" % (40 * 5))
    print()
    print("  |plane n plane|   %s" % dict(sorted(ipp.items())))
    print("  |other n plane|   %s" % dict(sorted(iop.items())))
    print("  |other n other|   %s" % dict(sorted(ioo.items())))
    print("  -> two canonical covers always share 1 or 3 and never miss each")
    print("     other; an alternate CAN be disjoint from a canonical one")
    print("     (%d pairs share nothing), so the alternates reach parts of the"
          % iop[0])
    print("     slow path a given canonical cover does not.")
    print()
    print("  THE FIVE IS NOT THE F20 FIVE: the axis stabiliser acts on its")
    print("  fibre with orbits 1 + 4, NOT transitively, so nothing here")
    print("  permutes these five as AGL(1,5) permutes five points. Matching")
    print("  the integers would be the error this repo keeps paying for.")

    ok = (len(ovoids) == 200 and dict(stabsz) == {648: 40, 162: 160}
          and dict(fixn) == {1: 200} and dict(tot) == {5: 40}
          and len(per) == 40 and alts_one_orbit and len(alts) == 4
          and dict(ipp) == {1: 540, 3: 240} and NA == 45 and M == 27)

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "opcode_axis_anchors_five_covers.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.opcode-axis-anchors-five-covers.v1",
                "valid": bool(ok),
                "whereThisStarts": ("8982d36 found 200 covers in orbits 40 and "
                                    "160 and showed the 40 are the cheap opcode "
                                    "axes; the parallel track identified those "
                                    "40 as the Payne covers "
                                    "(slow_path_is_payne_derivative.json). Both "
                                    "use the 40; neither says anything about the "
                                    "other 160 -- 80% of the covers, unexamined"),
                "everyCoverIsAnchored": {
                    "stabiliserOrders": {str(k): v for k, v in stabsz.items()},
                    "pointsFixedByStabiliser": {str(k): v
                                                for k, v in fixn.items()},
                    "reading": ("every one of the 200, not just the plane "
                                "ovoids, has a stabiliser fixing exactly ONE "
                                "point of W(3,3); the guess that the other 160 "
                                "would be unaddressable is false -- they are "
                                "anchored by a smaller group, 162 against 648, "
                                "index 4 in the point stabiliser"),
                },
                "fibration": {
                    "coversPerAxis": {str(k): v for k, v in tot.items()},
                    "composition": "1 plane + 4 other, at every one of the 40",
                    "alternatesFormOneOrbit": alts_one_orbit,
                    "stabOrbitsOnFibre": stab_orbits_on_fibre,
                    "total": 40 * 5,
                    "reading": ("a clean 5-to-1 fibration of the 200 minimal "
                                "covers onto the 40 opcode axes: one canonical "
                                "cover (the Payne one) plus four alternates, "
                                "equivalent under the axis's own stabiliser so "
                                "none is distinguished"),
                },
                "operationalReading": ("a cover is 9 slow targets meeting every "
                                       "one of the 27 ROM banks exactly once. "
                                       "The decoder uses the canonical one per "
                                       "axis; there are four more per axis of "
                                       "equal standing -- 160 spare minimal "
                                       "covers the current design does not use. "
                                       "Free redundancy: an alternate to fall "
                                       "back on if a bank is corrupt, or four "
                                       "independent covers to cross-check a "
                                       "decode against, with the symmetry "
                                       "guaranteeing no alternate is worse"),
                "thisFiveIsNotTheF20Five": ("the parallel track has an F20 Payne "
                                            "FIVE-state atlas where F20 = "
                                            "AGL(1,5) acts transitively on five "
                                            "things. The five here is different: "
                                            "the axis stabiliser acts on its "
                                            "fibre with orbits 1 + 4, NOT "
                                            "transitively, so nothing permutes "
                                            "these five as AGL(1,5) permutes "
                                            "five points. Matching the integers "
                                            "would be exactly the error this "
                                            "repository keeps paying for -- they "
                                            "are two distinct fives"),
                "intersections": {
                    "planeWithPlane": {str(k): v for k, v in sorted(ipp.items())},
                    "otherWithPlane": {str(k): v for k, v in sorted(iop.items())},
                    "otherWithOther": {str(k): v for k, v in sorted(ioo.items())},
                    "reading": ("two canonical covers always share 1 or 3 "
                                "targets and never miss each other entirely, "
                                "while an alternate CAN be disjoint from a "
                                "canonical one, so the alternates genuinely "
                                "reach parts of the slow path a given canonical "
                                "cover does not -- which is what makes them "
                                "fallbacks rather than near-duplicates"),
                },
                "boundary": ("exhaustive: all 200 covers by complete exact-cover "
                             "search, orbits and stabilisers by closure over the "
                             "full 25,920-element group, anchors by fixed-point "
                             "computation on every one of the 200, and the "
                             "intersection census over ALL pairs. The "
                             "identification of the 40 with the Payne covers is "
                             "the parallel track's, cited not re-derived. NO "
                             "claim that the four alternates have a Payne "
                             "description -- they are anchored, but their "
                             "derivation, if any, is not built here. tau_2 is "
                             "untouched"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
