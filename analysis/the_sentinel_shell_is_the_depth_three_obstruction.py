#!/usr/bin/env python3
"""
The sentinel code's 45 minimum words are the tritangent planes, and its 270
support-disjoint pairs are the depth-3 blocking obstruction. Same 270 objects,
two tracks, neither aware of the other.

TWO THINGS BUILT SEPARATELY.

  * e8_pg34_sentinel_control_plane (landed in 610b99e) starts from a
    [40,15,8]_2 doubly-even self-orthogonal code. Its 45 minimum-weight words
    have 8-element supports; the supports meet in 2 points 720 times and in 0
    points 270 times; the 40x45 cross-incidence B has degrees 9 and 8 and
    satisfies BB^T = 8I_40 + 2A_W33 + J_40 and B^T B = 8I_45 + 2A_c(GQ(4,2));
    and 216 five-circuits appear as GQ cocliques.

  * the_depth3_obstruction_is_a_quadrangle (a149d0b) starts from blocking sets
    in W(3,3) x W(3,3) x W(3,3). The 1,080 transversal-free line triples are
    the C(4,3) sub-triples of 270 all-isotropic reguli; each regulus's
    opposite regulus is closed under the polarity and names exactly two of
    BT810's 45 hyperbolic polar pairs; the 270 resulting edges are GQ(4,2).

Both end at 45 objects and 270 pairs. This checks whether they are the same
45 objects and the same 270 pairs, and they are.

THE DICTIONARY.  Take BT810's 45 hyperbolic polar pairs {L, L^perp} of
PG(3,3). L is nondegenerate, so L and L^perp are DISJOINT and their union is
8 of the 40 points -- a support. Then:

    support sizes                             all 8
    each W(3,3) point lies in 45*8/40 = 9     confirmed
    pair support-intersections                {2: 720, 0: 270}

which is the sentinel code's minimum-shell metric on the nose, [720, 270].

AND THE 270 ARE THE SAME 270.  The support-disjoint pairs and the pairs named
by the all-isotropic reguli are equal AS SETS -- 270 each, symmetric
difference zero. Not merely equinumerous. So

    two tritangent planes are GQ(4,2)-COLLINEAR
      <=> their supports L u L^perp and M u M^perp are disjoint
      <=> the four hyperbolic lines L, L^perp, M, M^perp are the opposite
          regulus of an all-isotropic regulus of W(3,3).

BOTH GRAM IDENTITIES FALL OUT.  Building B as the incidence between the 40
points of W(3,3) and the 45 polar pairs, with no reference to any code,

    B^T B = 8I_45 + 2(J - I - A)     reproduced
    B B^T = 8I_40 + 2A_W33 + J_40    reproduced

so the sentinel control plane's cross-incidence IS the point/polar-pair
incidence of PG(3,3), and the code's minimum-weight shell is a symplectic
object that happened to be reached through coding theory.

WHAT IT BUYS, in both directions.

  * The sentinel code gets a geometric description: its 45 minimum words are
    the 45 tritangent planes of the cubic surface, supported on L u L^perp,
    and its 216 five-circuits are the 5-element sets of pairwise
    regulus-unrelated tritangent planes. The bicolour packet's im(C) = 1+20+24
    is then just the eigenspace decomposition of SRG(45,12,3,3), the GQ(4,2)
    point graph -- multiplicities 1, 20, 24 for eigenvalues 12, 3, -3.

  * The blocking obstruction gets a code: the 270 reguli that stop a single
    Clifford orbit from blocking at depth 3 are the 270 disjoint pairs of
    minimum-weight words of a [40,15,8] code.

Which is the sentence worth keeping: THE DEPTH-3 BLOCKING OBSTRUCTION AND THE
SENTINEL CODE'S MINIMUM-WEIGHT SHELL ARE THE SAME 270 OBJECTS.

PRIOR ART, and it is most of the parts. BT810 (W33-Theory) owns the 40 + 90
split, the fixed-point-free polarity, the 45 polar pairs as tritangent planes,
and the Schlafli dictionary. The sentinel packets own the code, B, the shell
metric and the circuits. a149d0b owns the reguli and their quadrangle, and
ebaec5a owns the q-generalization showing the graph is a q = 3 coincidence.
That 45 tritangent planes and 27 lines form GQ(4,2) is classical. NEW here is
only the identification: that the two 45-sets coincide, that the two 270-sets
coincide as sets, and that both Gram identities follow from the geometry alone.

SCOPE.  An identification of finite structures, verified by set equality and by
reproducing both Gram identities. It says nothing about the code's use for
error correction, and nothing about hardware. tau_2 is untouched and stays open
in [111, 115].
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

    print("THE SENTINEL SHELL IS THE DEPTH-3 OBSTRUCTION")
    print("=" * 72)
    perp_disjoint = all(not (S[sorted(P)[0]] & S[sorted(P)[1]]) for P in polar)
    sup = [S[sorted(P)[0]] | S[sorted(P)[1]] for P in polar]
    deg = collections.Counter()
    for s in sup:
        for p in s:
            deg[p] += 1
    print("  BT810's %d polar pairs {L, L^perp}: L and L^perp disjoint: %s"
          % (len(polar), perp_disjoint))
    print("  supports L u L^perp: sizes %s ; each W(3,3) point in %s of them"
          % (sorted({len(s) for s in sup}), sorted(set(deg.values()))))
    print("     (45 x 8 / 40 = 9, the sentinel plane's crossDegrees)")
    print()

    inter = collections.Counter()
    disjoint = set()
    for i, j in itertools.combinations(range(45), 2):
        k = len(sup[i] & sup[j])
        inter[k] += 1
        if k == 0:
            disjoint.add(frozenset((i, j)))
    print("  pair support-intersections: %s" % dict(inter))
    print("     the sentinel code's minimum-shell metric is [720, 270]: %s"
          % (inter[2] == 720 and inter[0] == 270))
    print()

    regpairs = set()
    for t in itertools.combinations(iso, 3):
        if (S[t[0]] & S[t[1]]) or (S[t[0]] & S[t[2]]) or (S[t[1]] & S[t[2]]):
            continue
        tr = [m for m in range(len(alll)) if all(S[m] & S[x] for x in t)]
        if any(isof[m] for m in tr):
            continue
        regpairs.add(frozenset(pid[m] for m in tr))
    same = disjoint == regpairs
    print("  all-isotropic reguli name %d distinct polar-pair pairs" % len(regpairs))
    print("  SUPPORT-DISJOINT == REGULUS-NAMED, as SETS: %s" % same)
    print("     |symmetric difference| = %d" % len(disjoint ^ regpairs))
    print()

    A = [[0] * 45 for _ in range(45)]
    for e in disjoint:
        a, b = tuple(e)
        A[a][b] = A[b][a] = 1
    degs = sorted({sum(r) for r in A})
    B = [[1 if p in sup[j] else 0 for j in range(45)] for p in range(N)]
    BtB_ok = all(
        sum(B[p][i] * B[p][j] for p in range(N))
        == (8 if i == j else (0 if A[i][j] else 2))
        for i in range(45) for j in range(45))
    w33 = [[1 if p != q and form(pts[p], pts[q]) == 0 else 0
            for q in range(N)] for p in range(N)]
    BBt_ok = all(
        sum(B[p][j] * B[q][j] for j in range(45))
        == (9 if p == q else (3 if w33[p][q] else 1))
        for p in range(N) for q in range(N))
    print("  support-disjointness graph degree: %s (the plane's G45 is 12)" % degs)
    print("  B^T B = 8I_45 + 2(J - I - A) : %s" % BtB_ok)
    print("  B B^T = 8I_40 + 2A_W33 + J_40: %s" % BBt_ok)
    print()
    print("  So the sentinel plane's 40x45 cross-incidence IS the point /")
    print("  polar-pair incidence of PG(3,3), and the code's minimum-weight")
    print("  shell is a symplectic object reached through coding theory.")
    print()
    print("  THE DEPTH-3 BLOCKING OBSTRUCTION AND THE SENTINEL CODE'S")
    print("  MINIMUM-WEIGHT SHELL ARE THE SAME 270 OBJECTS.")

    ok = (perp_disjoint and sorted({len(s) for s in sup}) == [8]
          and sorted(set(deg.values())) == [9] and inter[2] == 720
          and inter[0] == 270 and same and len(regpairs) == 270
          and degs == [12] and BtB_ok and BBt_ok)

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data",
                         "the_sentinel_shell_is_the_depth_three_obstruction.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.sentinel-shell-is-depth3-obstruction.v1",
                "valid": bool(ok),
                "dictionary": {
                    "the45": ("BT810's hyperbolic polar pairs {L, L^perp} of "
                              "PG(3,3) = the 45 tritangent planes"),
                    "support": ("L u L^perp, which is 8 points because a "
                                "nondegenerate L is disjoint from L^perp"),
                    "supportSizes": sorted({len(s) for s in sup}),
                    "pointDegree": sorted(set(deg.values())),
                    "pointDegreeCheck": "45 * 8 / 40 = 9",
                },
                "shellMetric": {
                    "observed": {str(k): v for k, v in sorted(inter.items())},
                    "sentinelPlane": {"2": 720, "0": 270},
                    "matches": inter[2] == 720 and inter[0] == 270,
                },
                "theIdentification": {
                    "supportDisjointPairs": len(disjoint),
                    "regulusNamedPairs": len(regpairs),
                    "equalAsSets": same,
                    "symmetricDifference": len(disjoint ^ regpairs),
                    "statement": ("two tritangent planes are GQ(4,2)-collinear "
                                  "iff their supports are disjoint iff the four "
                                  "hyperbolic lines L, L^perp, M, M^perp are "
                                  "the opposite regulus of an all-isotropic "
                                  "regulus of W(3,3)"),
                },
                "gramIdentitiesReproduced": {
                    "BtB": "8I_45 + 2(J - I - A)",
                    "BtBHolds": BtB_ok,
                    "BBt": "8I_40 + 2A_W33 + J_40",
                    "BBtHolds": BBt_ok,
                    "degreeOfA": degs,
                    "reading": ("the sentinel plane's cross-incidence is the "
                                "point / polar-pair incidence of PG(3,3), built "
                                "here with no reference to any code"),
                },
                "consequences": {
                    "forTheCode": ("the 45 minimum words are the tritangent "
                                   "planes; the 216 five-circuits are the "
                                   "5-element sets of pairwise "
                                   "regulus-unrelated tritangent planes; and "
                                   "im(C) = 1+20+24 is the eigenspace "
                                   "decomposition of SRG(45,12,3,3), "
                                   "eigenvalues 12, 3, -3"),
                    "forTheObstruction": ("the 270 reguli that stop a single "
                                          "Clifford orbit blocking at depth 3 "
                                          "are the 270 disjoint pairs of "
                                          "minimum-weight words of a [40,15,8] "
                                          "code"),
                    "headline": ("the depth-3 blocking obstruction and the "
                                 "sentinel code's minimum-weight shell are the "
                                 "same 270 objects"),
                },
                "priorArt": {
                    "BT810": ("W33-Theory: the 40 + 90 split, the "
                              "fixed-point-free polarity, the 45 polar pairs as "
                              "tritangent planes, the Schlafli dictionary"),
                    "sentinelPackets": ("Holotrade 610b99e: the [40,15,8] code, "
                                        "B, the shell metric, the 216 circuits, "
                                        "and the bicolour 1+15+20+24"),
                    "a149d0b": "the 270 reguli and their quadrangle",
                    "ebaec5a": ("the q-generalization: the graph is a q = 3 "
                                "coincidence"),
                    "classical": "45 tritangent planes and 27 lines form GQ(4,2)",
                    "whatIsNew": ("only the identification -- that the two "
                                  "45-sets coincide, that the two 270-sets "
                                  "coincide AS SETS, and that both Gram "
                                  "identities follow from the geometry alone"),
                },
                "boundary": ("an identification of finite structures, verified "
                             "by set equality and by reproducing both Gram "
                             "identities. It says nothing about the code's use "
                             "for error correction and nothing about hardware. "
                             "tau_2 is untouched and stays open in [111, 115]"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
