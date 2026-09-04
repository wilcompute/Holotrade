#!/usr/bin/env python3
"""
The 36 double-sixes of the cost geometry ARE the 36 spreads of W(3,3) -- and
with that the whole Schlafli triple is closed by explicit equivariant maps,
with nothing left resting on matching invariants.

THE LAST LEG.  fe4fb77 derived all three Schlafli numbers from the cost model
and closed by admitting the identifications were "by INVARIANTS and the
classical uniqueness of the configuration, NOT by an explicit equivariant
bijection". Since then the 45 and the 27 have been built explicitly. The 36 was
still outstanding, and both 8982d36 and f04eec3 named it as such: "whether the
36 here are BT810's spreads is still by invariants." This builds it.

    SPREADS of W(3,3)                    36   [10 disjoint lines covering 40]
    DOUBLE-SIXES from the cost geometry  36
    PSp(4,3) transitive on each          yes / yes

    equivariant bijection: 36 double-sixes -> 36 spreads
    bijective                                        yes
    intertwines ALL 80 generators                    yes

The two 36-sets are the same PSp(4,3)-set. BT810 had already identified the 36
spreads with the 36 double-sixes of the cubic surface; what is added here is
that the 36 double-sixes reconstructed FROM THE COST MODEL -- via the skew graph
on its 27 lines, sixers, and the rigid partner condition -- are those same
spreads, equivariantly.

THE TRIPLE, NOW CLOSED.  Every number the cost model produces is tied to an
object this corpus already owned, and every tie is an explicit map checked
against every generator:

    27   the cost quadrangle's LINES
         = the 27 points of W(3,3) opposite a fixed point, one torsor under
           the order-27 exponent-3 qutrit Pauli group            f04eec3
    36   its DOUBLE-SIXES
         = the 36 spreads of W(3,3)                              this file
    45   its POINTS, the expensive instructions
         = the 45 abstract H(3,4) ROM slots                      6b19220
    40   the distinguished COVERS among its 200 ovoids
         = the 40 cheap opcode axes                              8982d36

Four equivariant identifications, no invariant-matching left in the chain. The
cost model is defined by a single predicate -- does an element need more
transvections than its residue -- and it reconstructs, with the corpus's own
group acting correctly throughout, the configuration the corpus had assembled
from blocking sets, spreads, E6 classes and a weight enumerator.

WHAT THAT LICENSES AND WHAT IT DOES NOT.  It licenses treating the cost geometry
and the substrate geometry as one object rather than two that happen to share
counts, which is what the slow-path ROM needs in order to decode. It does NOT
say the cost model discovered anything the corpus lacked: 27, 36 and 45 were
already the spreads, the E6 root pairs, the torsor and the code's minimum
weight. The content is that instruction COST is not an extra fact layered on the
geometry -- it is the geometry, read through a word-length function.

SCOPE.  Exhaustive: the 36 spreads by complete search over the 40 totally
isotropic lines, the 36 double-sixes by the rigid partner condition on sixers,
transitivity by orbit computation, and the bijection verified against every one
of the 80 generators rather than sampled. CITED and not derived: BT810's
identification of the spreads with the double-sixes of the cubic surface, and
the classical Schlafli counts. The ledger above refers to certificates committed
earlier; this file recomputes only its own leg. tau_2 is untouched.
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

    def nm(v):
        i = next(k for k, x in enumerate(v) if x % Q)
        z = pow(v[i] % Q, -1, Q)
        return tuple((z * x) % Q for x in v)

    pts = sorted({nm(v) for v in vecs})
    pidx = {p: i for i, p in enumerate(pts)}

    wl = set()
    for a, b in itertools.combinations(pts, 2):
        if form(a, b) % Q:
            continue
        S = set()
        for x in range(Q):
            for y in range(Q):
                if x == y == 0:
                    continue
                w = tuple((x * a[k] + y * b[k]) % Q for k in range(D))
                if any(w):
                    S.add(nm(w))
        if len(S) == 4 and all(form(u, v) % Q == 0
                               for u, v in itertools.combinations(sorted(S), 2)):
            wl.add(frozenset(pidx[z] for z in S))
    WL = sorted(map(sorted, wl))
    NL = len(WL)

    spreads = []

    def spd(ch, used):
        if len(used) == 40:
            spreads.append(frozenset(ch))
            return
        rem = [p for p in range(40) if p not in used]
        if not rem:
            return
        p = rem[0]
        for k in range(NL):
            if p in WL[k] and not (set(WL[k]) & used):
                spd(ch + [k], used | set(WL[k]))

    spd([], set())

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
    meet = [[0] * M for _ in range(M)]
    for i, j in itertools.combinations(range(M), 2):
        if set(LN[i]) & set(LN[j]):
            meet[i][j] = meet[j][i] = 1
    skew = [[0 if i == j else 1 - meet[i][j] for j in range(M)]
            for i in range(M)]
    six = []

    def ext(cur, cand):
        if len(cur) == 6:
            six.append(tuple(sorted(cur)))
            return
        for v in list(cand):
            if not cur or v > max(cur):
                ext(cur + [v], [u for u in cand if skew[v][u]])

    ext([], list(range(M)))
    ds = set()
    for A in six:
        for B in six:
            if set(A) & set(B):
                continue
            if (all(sum(1 for b in B if skew[a][b]) == 1 for a in A)
                    and all(sum(1 for a in A if skew[a][b]) == 1 for b in B)):
                ds.add(frozenset([A, B]))
    DS = sorted(ds, key=lambda p: sorted(sorted(x) for x in p))

    Li = {frozenset(l): i for i, l in enumerate(LN)}
    idx45 = {}
    for i, g in enumerate(reps):
        idx45[g] = i
        idx45[mul(mI, g)] = i
    WLi = {frozenset(l): i for i, l in enumerate(WL)}
    Sidx = {s: i for i, s in enumerate(spreads)}
    Didx = {d: i for i, d in enumerate(DS)}

    Aacts, Bacts = [], []
    for t in T:
        pp = tuple(pidx[nm(tuple(sum(t[i][k] * pts[j][k] for k in range(D)) % Q
                                 for i in range(D)))] for j in range(40))
        lp = tuple(WLi[frozenset(pp[x] for x in WL[k])] for k in range(NL))
        Bacts.append(tuple(Sidx[frozenset(lp[k] for k in s)] for s in spreads))
        ti = minv(t)
        c45 = tuple(idx45[mul(mul(t, reps[i]), ti)] for i in range(NA))
        l27 = tuple(Li[frozenset(c45[p] for p in LN[j])] for j in range(M))
        Aacts.append(tuple(Didx[frozenset(tuple(sorted(l27[x] for x in half))
                                          for half in d)] for d in DS))

    def transitive(acts, n):
        o, fr2 = {0}, [0]
        while fr2:
            nx = []
            for x in fr2:
                for a in acts:
                    y = a[x]
                    if y not in o:
                        o.add(y)
                        nx.append(y)
            fr2 = nx
        return len(o) == n

    tA = transitive(Aacts, len(DS))
    tB = transitive(Bacts, len(spreads))

    psi = None
    for b0 in range(len(spreads)):
        cand, fr2, good = {0: b0}, [0], True
        while fr2 and good:
            nx = []
            for a in fr2:
                for k in range(len(Aacts)):
                    a2, b2 = Aacts[k][a], Bacts[k][cand[a]]
                    if a2 in cand:
                        if cand[a2] != b2:
                            good = False
                            break
                    else:
                        cand[a2] = b2
                        nx.append(a2)
                if not good:
                    break
            fr2 = nx
        if good and len(cand) == 36 and len(set(cand.values())) == 36:
            psi = cand
            break
    inter = psi is not None and all(
        psi[Aacts[k][a]] == Bacts[k][psi[a]]
        for k in range(len(Aacts)) for a in range(36))

    print("THE SCHLAFLI TRIPLE IS CLOSED")
    print("=" * 72)
    print("  SPREADS of W(3,3)                    %d   [BT810: 36]"
          % len(spreads))
    print("  DOUBLE-SIXES from the cost geometry  %d" % len(DS))
    print("  PSp(4,3) transitive on each          %s / %s" % (tA, tB))
    print()
    print("  equivariant bijection: 36 double-sixes -> 36 spreads")
    print("     bijective                         %s"
          % (psi is not None and len(set(psi.values())) == 36))
    print("     intertwines ALL %d generators      %s" % (len(Aacts), inter))
    print()
    print("  THE TRIPLE, NOW CLOSED -- every tie an explicit map:")
    print("     27  cost-quadrangle LINES   = W(3,3)'s 27 opposite points,")
    print("         one torsor under the qutrit Pauli group        f04eec3")
    print("     36  its DOUBLE-SIXES        = W(3,3)'s 36 spreads  this file")
    print("     45  its POINTS              = the H(3,4) ROM slots 6b19220")
    print("     40  its distinguished COVERS = the cheap opcode axes 8982d36")
    print()
    print("  No invariant-matching left in the chain. The cost model is one")
    print("  predicate -- does an element need more transvections than its")
    print("  residue -- and it reconstructs, with the corpus's own group acting")
    print("  correctly throughout, the configuration the corpus assembled from")
    print("  blocking sets, spreads, E6 classes and a weight enumerator.")
    print()
    print("  It does NOT say the cost model found anything the corpus lacked.")
    print("  27, 36 and 45 were already the spreads, the E6 root pairs, the")
    print("  torsor and the code's minimum weight. The content is that")
    print("  instruction COST is not a fact layered on the geometry -- it IS")
    print("  the geometry, read through a word-length function.")

    ok = (len(spreads) == 36 and len(DS) == 36 and tA and tB and inter
          and NA == 45 and M == 27 and NL == 40 and len(six) == 72)

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "schlafli_triple_closed.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.schlafli-triple-closed.v1",
                "valid": bool(ok),
                "theLastLeg": ("fe4fb77 derived all three Schlafli numbers from "
                               "the cost model and admitted the identifications "
                               "were by INVARIANTS, not explicit equivariant "
                               "bijections. The 45 and 27 were built since; the "
                               "36 was still outstanding, named as such by both "
                               "8982d36 and f04eec3"),
                "theThirtySix": {
                    "spreadsOfW33": len(spreads),
                    "doubleSixesFromCostGeometry": len(DS),
                    "sixers": len(six),
                    "transitiveOnDoubleSixes": tA,
                    "transitiveOnSpreads": tB,
                    "equivariantBijection": bool(inter),
                    "generatorsChecked": len(Aacts),
                    "whatIsAdded": ("BT810 already identified the 36 spreads "
                                    "with the 36 double-sixes of the cubic "
                                    "surface; what is added is that the 36 "
                                    "double-sixes reconstructed FROM THE COST "
                                    "MODEL -- skew graph on its 27 lines, "
                                    "sixers, rigid partner condition -- are "
                                    "those same spreads, equivariantly"),
                },
                "ledger": {
                    "27": {"costObject": "the quadrangle's LINES",
                           "corpusObject": ("the 27 points of W(3,3) opposite a "
                                            "fixed point, one torsor under the "
                                            "order-27 exponent-3 qutrit Pauli "
                                            "group"),
                           "commit": "f04eec3"},
                    "36": {"costObject": "its DOUBLE-SIXES",
                           "corpusObject": "the 36 spreads of W(3,3)",
                           "commit": "this file"},
                    "45": {"costObject": ("its POINTS, the expensive "
                                          "instructions"),
                           "corpusObject": "the 45 abstract H(3,4) ROM slots",
                           "commit": "6b19220"},
                    "40": {"costObject": ("the distinguished COVERS among its "
                                          "200 ovoids"),
                           "corpusObject": "the 40 cheap opcode axes",
                           "commit": "8982d36"},
                },
                "whatItLicenses": ("treating the cost geometry and the substrate "
                                   "geometry as ONE object rather than two that "
                                   "happen to share counts, which is what the "
                                   "slow-path ROM needs in order to decode"),
                "whatItDoesNotSay": ("that the cost model discovered anything "
                                     "the corpus lacked: 27, 36 and 45 were "
                                     "already the spreads, the E6 root pairs, "
                                     "the torsor and the code's minimum weight. "
                                     "The content is that instruction COST is "
                                     "not an extra fact layered on the geometry "
                                     "-- it IS the geometry, read through a "
                                     "word-length function"),
                "boundary": ("exhaustive: the 36 spreads by complete search over "
                             "the 40 totally isotropic lines, the 36 double-"
                             "sixes by the rigid partner condition on sixers, "
                             "transitivity by orbit computation, and the "
                             "bijection verified against every one of the 80 "
                             "generators rather than sampled. CITED not derived: "
                             "BT810's identification of the spreads with the "
                             "double-sixes, and the classical Schlafli counts. "
                             "The ledger refers to certificates committed "
                             "earlier; this file recomputes only its own leg. "
                             "tau_2 is untouched"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
