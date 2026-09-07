#!/usr/bin/env python3
"""
tau_1 of the cost quadrangle is 9 -- defect zero -- so it is a new base for the
tower law, the smallest yet, and every difficulty in composing the machine is
confined to the fast-path factors.

WHY ASK.  8982d36 proved the cost quadrangle GQ(4,2) has 200 ovoids while
W(3,3) has none: dual defects. d9a9c59's splitting theorem says an OVOID-BEARING
factor peels off exactly -- "if Q1 has an ovoid then tau(Q1 x R) = tau_1 * tau(R)
for arbitrary R". Those two results have not been put together, and nothing in
the corpus computes tau_1 for GQ(4,2).

tau_1(GQ(4,2)) = 9, AND THE BOUND IS PURE COUNTING.

    45 points, 27 lines, 3 lines per point, 5 points per line
    a blocker needs at least 27/3 = 9 points
    a 9-point blocker exists

So tau_1 = 9 = st + 1, the ovoid bound, attained. DEFECT ZERO -- and the
witnesses are forced to be ovoids: a 9-set covering 27 lines with each point on
exactly 3 has no slack anywhere, so it meets every line exactly once.

    minimum blocking sets of size 9        200
    of those that are ovoids               200
    every minimum blocker is an ovoid      yes

The 200 minimum blockers and the 200 ovoids are the same 200 objects, which is
what "defect zero" means concretely.

THE FOUR QUADRANGLES OF THIS CORPUS, AND A CLEAN DICHOTOMY.

    geometry            (s,t)   st+1   tau_1   defect   ovoid   tower base
    W(3,3)              (3,3)     10     11       1      no        --
    dual of W(3,3)      (3,3)     10     10       0      yes       10
    GQ(2,4)             (2,4)      9     10       1      no        --
    GQ(4,2)  the cost   (4,2)      9      9       0      yes        9

    defect 0  <=>  has an ovoid  <=>  tau_1 = st+1  <=>  tower law applies

and in EACH dual pair exactly one member bears an ovoid: W(3,3) does not but its
dual does (its ovoids are W's 36 spreads); GQ(2,4) does not but its dual GQ(4,2)
does. The dual defect of 8982d36, restated as blocking numbers.

A NEW TOWER BASE, THE SMALLEST YET.  d9a9c59's law was applied with base 10, the
dual of W(3,3). GQ(4,2) gives a second base, and a smaller one:

    tau(GQ(4,2)^m x R) = 9^m * tau(R)     for arbitrary R, any m
    tau(GQ(4,2)^m) = 9^m                  exactly, at every depth

WHERE THE DIFFICULTY ACTUALLY LIVES.  Combining with the tower law's existing
form, every factor with an ovoid peels off exactly and only the W-factors
resist:

    tau(GQ(4,2)^m x Wdual^j x W^k) = 9^m * 10^j * tau(W^k)

with tau(W^0) = 1, tau(W^1) = 11 exact, and tau(W^2) open in [111, 115]. So an
arbitrarily deep tower is exactly solved except for its W-factors, and the whole
open problem sits at k >= 2.

AND IT SAYS WHAT tau_2 IS MEASURING.  For an ovoid-bearing factor the product
does not compress: 9^2 = 81 exactly. For W(3,3) it does -- tau_1^2 = 121 but
tau_2 <= 115, so the product is strictly cheaper than the square. The ovoid is
what PREVENTS compression, and tau_2 is measuring how much the missing ovoid
buys: between 6 and 10 off the square.

ARCHITECTURALLY.  Composing slow paths is free: the expensive-instruction
geometry tiles to any depth at exactly 9 per level. Composing fast paths is the
open problem. The part of the machine that costs extra per instruction is the
part that costs nothing to scale, and vice versa.

SCOPE.  tau_1 = 9 is exact: the lower bound is the counting bound and the upper
is an explicit witness, and the enumeration of all 200 minimum blockers is
complete. The splitting theorem is d9a9c59's, cited and applied, not re-proved
here; its own boundary note that tau(W^k) for k >= 2 is untouched applies
unchanged. tau_1 values for W(3,3), its dual and GQ(2,4) are corpus values
(tensor_blocking_structure.json, gq24_schlaefli_quadrangle.json,
the_tower_law_one_ovoid_splits_any_depth.json), cited not recomputed. tau_2 is
untouched.
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
    LNS = [sorted(c) for c in cl if len(c) == 5]
    M = len(LNS)
    lines_of = collections.defaultdict(list)
    for k, ln in enumerate(LNS):
        for p in ln:
            lines_of[p].append(k)
    ppl = {len(l) for l in LNS}
    lpp = {len(v) for v in lines_of.values()}
    bound = -(-M // max(lpp))

    def exists(k, chosen, covered):
        if len(covered) == M:
            return list(chosen)
        if len(chosen) == k:
            return None
        rem = [x for x in range(M) if x not in covered]
        for p in LNS[rem[0]]:
            r = exists(k, chosen + [p], covered | set(lines_of[p]))
            if r:
                return r
        return None

    tau1, witness = None, None
    for k in range(1, 12):
        w = exists(k, [], set())
        if w:
            tau1, witness = k, w
            break

    blockers = []

    def allmin(chosen, covered):
        if len(covered) == M:
            if len(chosen) == tau1:
                blockers.append(frozenset(chosen))
            return
        if len(chosen) == tau1:
            return
        rem = [x for x in range(M) if x not in covered]
        for p in LNS[rem[0]]:
            allmin(chosen + [p], covered | set(lines_of[p]))

    allmin([], set())
    B = set(blockers)
    ovo = [b for b in B if all(len(b & set(l)) == 1 for l in LNS)]

    print("THE COST QUADRANGLE IS A NEW TOWER-LAW BASE")
    print("=" * 72)
    print("  GQ(4,2): %d points, %d lines, %s lines/point, %s points/line"
          % (NA, M, lpp, ppl))
    print("  counting bound: a blocker needs >= %d/%d = %d points"
          % (M, max(lpp), bound))
    print("  a %d-point blocker exists          -> tau_1 = %d = st+1, DEFECT 0"
          % (tau1, tau1))
    print()
    print("  minimum blocking sets of size %d   %d" % (tau1, len(B)))
    print("  of those that are ovoids          %d" % len(ovo))
    print("  every minimum blocker is an ovoid %s" % (len(ovo) == len(B)))
    print()
    print("  geometry            (s,t)   st+1  tau_1  defect  ovoid  base")
    print("  W(3,3)              (3,3)     10     11      1     no    --")
    print("  dual of W(3,3)      (3,3)     10     10      0    yes    10")
    print("  GQ(2,4)             (2,4)      9     10      1     no    --")
    print("  GQ(4,2)  the cost   (4,2)      9      %d      %d    yes     %d"
          % (tau1, tau1 - 9, tau1))
    print("  -> defect 0 <=> ovoid <=> tau_1 = st+1 <=> tower law applies,")
    print("     and in EACH dual pair exactly one member bears an ovoid.")
    print()
    print("  NEW BASE (d9a9c59's splitting theorem, applied):")
    print("     tau(GQ(4,2)^m x R) = %d^m * tau(R)   for arbitrary R"
          % tau1)
    print("     tau(GQ(4,2)^m)     = %d^m            exactly, every depth"
          % tau1)
    print()
    print("     tau(GQ(4,2)^m x Wdual^j x W^k) = %d^m * 10^j * tau(W^k)" % tau1)
    print("     with tau(W^1) = 11 exact and tau(W^2) open in [111,115]:")
    print("     an arbitrarily deep tower is solved EXCEPT its W-factors.")
    print()
    print("  AND IT SAYS WHAT tau_2 MEASURES: an ovoid-bearing factor does not")
    print("  compress (9^2 = 81 exactly), while W(3,3) does -- 11^2 = 121 but")
    print("  tau_2 <= 115. The ovoid PREVENTS compression, and tau_2 measures")
    print("  what the missing ovoid buys: between 6 and 10 off the square.")

    ok = (NA == 45 and M == 27 and lpp == {3} and ppl == {5} and bound == 9
          and tau1 == 9 and len(B) == 200 and len(ovo) == 200 and d0 == 5)

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "cost_quadrangle_tower_base.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.cost-quadrangle-tower-base.v1",
                "valid": bool(ok),
                "whyAsk": ("8982d36 proved GQ(4,2) has 200 ovoids while W(3,3) "
                           "has none; d9a9c59's splitting theorem says an "
                           "ovoid-bearing factor peels off exactly. The two have "
                           "not been put together, and nothing in the corpus "
                           "computes tau_1 for GQ(4,2)"),
                "tau1": {
                    "value": tau1,
                    "points": NA, "lines": M,
                    "linesPerPoint": sorted(lpp),
                    "pointsPerLine": sorted(ppl),
                    "countingBound": bound,
                    "witness": sorted(witness),
                    "defect": tau1 - 9,
                    "reading": ("the lower bound is pure counting -- 27 lines, 3 "
                                "lines per point, so at least 9 points -- and a "
                                "9-point blocker exists, so tau_1 = 9 = st+1 "
                                "with DEFECT ZERO"),
                },
                "minimumBlockersAreOvoids": {
                    "minimumBlockers": len(B),
                    "ovoids": len(ovo),
                    "identical": len(ovo) == len(B),
                    "why": ("a 9-set covering 27 lines with each point on "
                            "exactly 3 has no slack anywhere, so it meets every "
                            "line exactly once; the 200 minimum blockers and the "
                            "200 ovoids are the same 200 objects, which is what "
                            "defect zero means concretely"),
                },
                "fourQuadrangles": [
                    {"geometry": "W(3,3)", "st": [3, 3], "stPlus1": 10,
                     "tau1": 11, "defect": 1, "ovoid": False,
                     "towerBase": None, "source": "corpus"},
                    {"geometry": "dual of W(3,3)", "st": [3, 3], "stPlus1": 10,
                     "tau1": 10, "defect": 0, "ovoid": True,
                     "towerBase": 10, "source": "corpus (d9a9c59)"},
                    {"geometry": "GQ(2,4)", "st": [2, 4], "stPlus1": 9,
                     "tau1": 10, "defect": 1, "ovoid": False,
                     "towerBase": None, "source": "corpus"},
                    {"geometry": "GQ(4,2) the cost quadrangle", "st": [4, 2],
                     "stPlus1": 9, "tau1": tau1, "defect": tau1 - 9,
                     "ovoid": True, "towerBase": tau1, "source": "here"},
                ],
                "dichotomy": ("defect 0 <=> has an ovoid <=> tau_1 = st+1 <=> "
                              "the tower law applies; and in EACH dual pair "
                              "exactly one member bears an ovoid -- W(3,3) does "
                              "not but its dual does (its ovoids are W's 36 "
                              "spreads), GQ(2,4) does not but GQ(4,2) does. The "
                              "dual defect of 8982d36 restated as blocking "
                              "numbers"),
                "newTowerBase": {
                    "law": "tau(GQ(4,2)^m x R) = 9^m * tau(R), arbitrary R",
                    "pure": "tau(GQ(4,2)^m) = 9^m exactly, at every depth",
                    "combined": ("tau(GQ(4,2)^m x Wdual^j x W^k) = 9^m * 10^j * "
                                 "tau(W^k), with tau(W^1) = 11 exact and "
                                 "tau(W^2) open in [111,115]: an arbitrarily "
                                 "deep tower is solved EXCEPT its W-factors"),
                    "smallestYet": ("d9a9c59 applied the law with base 10, the "
                                    "dual of W(3,3); this is a second base and a "
                                    "smaller one"),
                },
                "whatTau2Measures": ("an ovoid-bearing factor does not compress "
                                     "-- 9^2 = 81 exactly -- while W(3,3) does: "
                                     "tau_1^2 = 121 but tau_2 <= 115, so the "
                                     "product is strictly cheaper than the "
                                     "square. The ovoid is what PREVENTS "
                                     "compression, and tau_2 measures what the "
                                     "missing ovoid buys: between 6 and 10 off "
                                     "the square"),
                "architecturally": ("composing slow paths is free -- the "
                                    "expensive-instruction geometry tiles to any "
                                    "depth at exactly 9 per level -- while "
                                    "composing fast paths is the open problem. "
                                    "The part of the machine that costs extra "
                                    "per instruction is the part that costs "
                                    "nothing to scale, and vice versa"),
                "boundary": ("tau_1 = 9 is exact: lower bound by counting, upper "
                             "by explicit witness, and the enumeration of all 200 "
                             "minimum blockers is complete. The splitting theorem "
                             "is d9a9c59's, CITED and applied, not re-proved, and "
                             "its own note that tau(W^k) for k >= 2 is untouched "
                             "applies unchanged. tau_1 for W(3,3), its dual and "
                             "GQ(2,4) are corpus values, cited not recomputed. "
                             "tau_2 is untouched"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
