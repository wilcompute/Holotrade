#!/usr/bin/env python3
"""
The cheap instruction index and the expensive geometry have exactly DUAL
defects -- and the 40 cheap opcodes ARE the 40 distinguished ovoids of the
expensive geometry, equivariantly.

THE QUESTION NOBODY ASKED OF THE NEW GEOMETRY.  Every major result in this
corpus turns on ovoid-or-not: tau_1, tau_2, the hemisystems, the tower law all
hinge on whether a quadrangle has one. W(3,3) famously does NOT (Thas, odd q),
while it has 36 spreads. 605f5e5 produced a SECOND quadrangle -- GQ(4,2) on the
45 expensive instructions -- and nobody asked it the same question.

THE ANSWER INVERTS.

    W(3,3)   the CHEAP index      36 spreads,   NO ovoid
    GQ(4,2)  the EXPENSIVE set    200 ovoids,   NO spread

Exactly dual defects. The instruction geometry can be partitioned but not
transversally covered; the cost geometry can be transversally covered but not
partitioned. Both counts are computed exhaustively here, and the 200 with its
two orbits is the classical count for H(3,4) (two orbits, 40 and 160, the 40
called PLANE ovoids as sections by the 40 non-tangent planes) -- cited, and
matched exactly.

AND THE SUBSTRATE'S OWN GROUP REALISES THE SPLIT.  PSp(4,3) acts on the 45 by
conjugation, because length and residue are class functions. Its orbits on the
200 ovoids:

    orbit sizes under PSp(4,3) conjugation      40 + 160

which is the literature's split, produced here by the machine's own symmetry
group rather than by the ambient automorphism group of the abstract quadrangle.

THE 40 IS NOT A FREE NUMBER, AND THIS TIME IT IS PROVED.  Fixing one ovoid of
the 40-orbit and computing subdegrees:

    40 distinguished ovoids, suborbits      1 + 12 + 27
    40 points of W(3,3),      suborbits      1 + 12 + 27

Same rank-3 shape -- and 1 + 12 + 27 is exactly the split W33-Theory's
THE_27_FOLD_WAY (Passes 368-371) builds its torsor on, where the 27 opposite
points carry the single-qutrit Pauli group regularly. But matching subdegrees is
only evidence, and fe4fb77 was already criticised in its own boundary for
stopping at invariants. So the map is BUILT:

    equivariant bijection psi: 40 ovoids -> 40 points
    bijective                                        yes
    intertwines ALL 80 generators                    yes

Both actions are transitive, so psi is forced once one value is chosen; the
content is that a consistent choice EXISTS, checked against every generator.
The two 40-sets are therefore the same PSp(4,3)-set, not two sets of equal size
with equal subdegrees.

WHAT IT MEANS FOR THE MACHINE.  An ovoid of GQ(4,2) is 9 expensive instructions
meeting every one of the 27 ROM banks exactly once -- a minimal transversal
cover of the entire slow path. There are 200, and 40 of them are distinguished.
Those 40 are the cheap opcode axes. So:

    every cheap opcode canonically names a 9-element minimal cover
    of the whole 45-instruction slow path.

The fast path indexes the slow path's canonical covers. That is not a design
choice anyone made; it falls out of the cost function. And the absence of a
spread says the complementary move is impossible: the 45 expensive instructions
cannot be partitioned into 9 disjoint banks, so a ROM can cover but never
cleanly split them.

SCOPE.  Exhaustive: 200 ovoids and 0 spreads by complete exact-cover search over
the 45 points and 27 lines; orbits by closure under all 80 conjugation
generators; subdegrees as orbits on ordered pairs. The equivariant bijection is
verified against every generator, not sampled. CITED and not derived: the
classical count of 200 ovoids of H(3,4) in orbits 40 + 160 with the 40 as plane
ovoids; Thas for W(3,3) having no ovoid at odd q; and THE_27_FOLD_WAY for the
1 + 12 + 27 reading. Establishing psi does NOT establish that the 27 appearing
here is the same 27 as that file's -- that remains open and is the next thing to
build. tau_2 is untouched.
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

    def inv(A):
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
    dist, fr, dia = {I: 0}, [I], 0
    while fr:
        nx = []
        for A in fr:
            for M in T:
                C = mul(M, A)
                if C not in dist:
                    dist[C] = dia + 1
                    nx.append(C)
        fr = nx
        if nx:
            dia += 1

    def rk(A):
        M = [[(A[i][j] - (1 if i == j else 0)) % Q for j in range(D)]
             for i in range(D)]
        r = 0
        for c in range(D):
            p = next((i for i in range(r, D) if M[i][c] % Q), None)
            if p is None:
                continue
            M[r], M[p] = M[p], M[r]
            iv = pow(M[r][c], -1, Q)
            M[r] = [(x * iv) % Q for x in M[r]]
            for i in range(D):
                if i != r and M[i][c] % Q:
                    f = M[i][c]
                    M[i] = [(M[i][j] - f * M[r][j]) % Q for j in range(D)]
            r += 1
        return r

    reps = sorted({min(A, mul(mI, A)) for A, L in dist.items()
                   if L == 3 and rk(A) == 2})
    NA = len(reps)
    adj = [[0] * NA for _ in range(NA)]
    for i, j in itertools.combinations(range(NA), 2):
        if mul(reps[i], reps[j]) == mul(mI, mul(reps[j], reps[i])):
            adj[i][j] = adj[j][i] = 1
    cl = []

    def bk(R, P, X):
        if not P and not X:
            cl.append(frozenset(R))
            return
        for v in list(P):
            bk(R | {v}, {u for u in P if adj[v][u]},
               {u for u in X if adj[v][u]})
            P = P - {v}
            X = X | {v}

    bk(set(), set(range(NA)), set())
    L = [sorted(c) for c in cl if len(c) == 5]
    M = len(L)
    lines_of = collections.defaultdict(list)
    for k, ln in enumerate(L):
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
        for p in L[rem[0]]:
            if any(x in cov for x in lines_of[p]):
                continue
            ov(ch + [p], cov | set(lines_of[p]))

    ov([], set())

    spreads = []

    def sp(ch, used):
        if len(ch) == 9:
            if len(used) == NA:
                spreads.append(tuple(ch))
            return
        rem = [p for p in range(NA) if p not in used]
        if not rem:
            return
        for k in lines_of[rem[0]]:
            if any(x in used for x in L[k]):
                continue
            sp(ch + [k], used | set(L[k]))

    sp([], set())

    idx45 = {}
    for i, g in enumerate(reps):
        idx45[g] = i
        idx45[mul(mI, g)] = i
    conj = [tuple(idx45[mul(mul(t, reps[i]), inv(t))] for i in range(NA))
            for t in T]

    seen, orbs = set(), []
    for o in ovoids:
        if o in seen:
            continue
        orb, f2 = {o}, [o]
        while f2:
            nx = []
            for x in f2:
                for g in conj:
                    y = frozenset(g[p] for p in x)
                    if y not in orb:
                        orb.add(y)
                        nx.append(y)
            f2 = nx
        seen |= orb
        orbs.append(orb)
    orbsizes = sorted(len(o) for o in orbs)

    def nm(v):
        i = next(k for k, x in enumerate(v) if x % Q)
        z = pow(v[i] % Q, -1, Q)
        return tuple((z * x) % Q for x in v)

    pts = sorted({nm(v) for v in vecs})
    pidx = {p: i for i, p in enumerate(pts)}
    O40 = sorted([o for o in orbs if len(o) == 40][0], key=lambda s: sorted(s))
    ovi = {o: i for i, o in enumerate(O40)}
    Aacts, Bacts = [], []
    for gi, t in enumerate(T):
        Aacts.append(tuple(ovi[frozenset(conj[gi][p] for p in O40[j])]
                           for j in range(40)))
        Bacts.append(tuple(pidx[nm(tuple(sum(t[i][k] * pts[j][k]
                                             for k in range(D)) % Q
                                         for i in range(D)))]
                           for j in range(40)))

    def subdeg(acts, n):
        out, cov = [], set()
        for b in range(n):
            if b in cov:
                continue
            S, f2 = {(0, b)}, [(0, b)]
            while f2:
                nx = []
                for (x, y) in f2:
                    for p in acts:
                        q = (p[x], p[y])
                        if q not in S:
                            S.add(q)
                            nx.append(q)
                f2 = nx
            blk = {y for (x, y) in S if x == 0}
            out.append(len(blk))
            cov |= blk
        return sorted(out)

    sdA, sdB = subdeg(Aacts, 40), subdeg(Bacts, 40)

    psi = None
    for p0 in range(40):
        cand, f2, good = {0: p0}, [0], True
        while f2 and good:
            nx = []
            for a in f2:
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
            f2 = nx
        if good and len(cand) == 40 and len(set(cand.values())) == 40:
            psi = cand
            break
    inter = psi is not None and all(
        psi[Aacts[k][a]] == Bacts[k][psi[a]]
        for k in range(len(Aacts)) for a in range(40))

    print("THE CHEAP OPCODES ARE THE EXPENSIVE GEOMETRY'S OVOIDS")
    print("=" * 72)
    print("  W(3,3)   the CHEAP index      36 spreads,  NO ovoid  [Thas]")
    print("  GQ(4,2)  the EXPENSIVE set   %3d ovoids,  %d spreads"
          % (len(ovoids), len(spreads)))
    print("  -> exactly DUAL defects: the instruction geometry partitions but")
    print("     cannot be transversally covered; the cost geometry covers but")
    print("     cannot be partitioned.")
    print()
    print("  orbits on the ovoids under PSp(4,3) conjugation: %s" % orbsizes)
    print("     [literature: 200 = 40 + 160, the 40 are PLANE ovoids]")
    print()
    print("  40 distinguished ovoids, suborbits   %s" % sdA)
    print("  40 points of W(3,3),      suborbits   %s" % sdB)
    print("     1+12+27 is THE_27_FOLD_WAY's split (Passes 368-371)")
    print()
    print("  equivariant bijection psi: 40 ovoids -> 40 points")
    print("     bijective                        %s"
          % (psi is not None and len(set(psi.values())) == 40))
    print("     intertwines ALL %d generators     %s" % (len(Aacts), inter))
    print("  -> the same PSp(4,3)-set, not two sets with equal subdegrees.")
    print()
    print("  An ovoid is 9 expensive instructions meeting every one of the 27")
    print("  ROM banks exactly once -- a minimal transversal cover of the whole")
    print("  slow path. So EVERY CHEAP OPCODE CANONICALLY NAMES A 9-ELEMENT")
    print("  MINIMAL COVER of the 45-instruction slow path. And with no spread,")
    print("  the 45 can be covered but never cleanly partitioned.")

    ok = (len(ovoids) == 200 and len(spreads) == 0 and orbsizes == [40, 160]
          and sdA == [1, 12, 27] and sdB == [1, 12, 27] and inter
          and NA == 45 and M == 27 and dia == 5)

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "cheap_opcodes_are_ovoids.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.cheap-opcodes-are-ovoids.v1",
                "valid": bool(ok),
                "theQuestionNobodyAsked": ("every major result in this corpus "
                                           "turns on ovoid-or-not -- tau_1, "
                                           "tau_2, the hemisystems, the tower "
                                           "law -- and W(3,3) has 36 spreads but "
                                           "NO ovoid (Thas, odd q); 605f5e5 "
                                           "produced a SECOND quadrangle on the "
                                           "45 expensive instructions and nobody "
                                           "asked it the same question"),
                "dualDefects": {
                    "cheapIndex": {"geometry": "W(3,3)", "spreads": 36,
                                   "ovoids": 0, "source": "Thas, odd q"},
                    "expensiveSet": {"geometry": "GQ(4,2)",
                                     "ovoids": len(ovoids),
                                     "spreads": len(spreads)},
                    "reading": ("exactly dual defects: the instruction geometry "
                                "partitions but cannot be transversally covered; "
                                "the cost geometry covers but cannot be "
                                "partitioned"),
                },
                "orbitSplit": {
                    "sizes": orbsizes,
                    "byWhat": ("PSp(4,3) acting by CONJUGATION on the 45, valid "
                               "because length and residue are class functions"),
                    "literature": ("classical for H(3,4): 200 ovoids in two "
                                   "orbits 40 + 160, the 40 called PLANE ovoids "
                                   "as sections by the 40 non-tangent planes -- "
                                   "CITED, and matched exactly, but produced "
                                   "here by the machine's own symmetry group"),
                },
                "sameSet": {
                    "subdegreesOvoids": sdA,
                    "subdegreesW33Points": sdB,
                    "equivariantBijection": bool(inter),
                    "generatorsChecked": len(Aacts),
                    "reading": ("1+12+27 is exactly the split W33-Theory's "
                                "THE_27_FOLD_WAY (Passes 368-371) builds its "
                                "torsor on. Matching subdegrees is only "
                                "evidence, so the map is BUILT: both actions are "
                                "transitive so psi is forced once one value is "
                                "chosen, and the content is that a consistent "
                                "choice EXISTS, checked against every generator. "
                                "The two 40-sets are the same PSp(4,3)-set"),
                },
                "machineReading": ("an ovoid of GQ(4,2) is 9 expensive "
                                   "instructions meeting every one of the 27 ROM "
                                   "banks exactly once -- a minimal transversal "
                                   "cover of the whole slow path. 40 of the 200 "
                                   "are distinguished, and those 40 ARE the "
                                   "cheap opcode axes. So every cheap opcode "
                                   "canonically names a 9-element minimal cover "
                                   "of the 45-instruction slow path: the fast "
                                   "path indexes the slow path's canonical "
                                   "covers, and nobody designed that. The "
                                   "absence of a spread says the complementary "
                                   "move is impossible -- the 45 cannot be "
                                   "partitioned into 9 disjoint banks, so a ROM "
                                   "can cover but never cleanly split them"),
                "boundary": ("exhaustive: 200 ovoids and 0 spreads by complete "
                             "exact-cover search; orbits by closure under all 80 "
                             "conjugation generators; subdegrees as orbits on "
                             "ordered pairs; the equivariant bijection verified "
                             "against EVERY generator, not sampled. CITED not "
                             "derived: the classical 200 = 40 + 160 with the 40 "
                             "as plane ovoids; Thas for W(3,3) having no ovoid "
                             "at odd q; THE_27_FOLD_WAY for the 1+12+27 reading. "
                             "Establishing psi does NOT establish that the 27 "
                             "here is the same 27 as that file's -- that remains "
                             "open. tau_2 is untouched"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
