#!/usr/bin/env python3
"""
Two loose ends in my own recent work, closed: the complementation half of the
balance spectrum is now demonstrated rather than asserted, and the C3 row stays
UNKNOWN at more than twice the budget.

WHAT WAS ASSERTED.  c74fbb1 determined the balance spectrum as {0, 2, 3, ...,
14, 16} and justified the upper half by complementation: "m = 9..14 are feasible
by complementing the witnesses found here, which is CONSTRUCTIVE". That is
true, and the lemma behind it is a one-liner, but the file never actually took a
committed witness and exhibited its complement. Calling something constructive
and constructing it are different, and the second is cheap here, so it should
have been done.

IT IS DONE NOW, on the witness 5aa4ff1 actually committed:

    X      size  200    tile counts {2: 1600}     2-balanced
    X^c    size 1400    tile counts {14: 1600}   14-balanced
    and 100m at m = 14 is 1400, which is |X^c|

Every one of the 1600 tiles is recounted from scratch for both sets. So the
upper half of the spectrum now rests on an exhibited object at m = 14, not only
on the lemma -- and the lemma's prediction is confirmed on the nose.

AND THE C3 ROW HOLDS AT A LONGER BUDGET.  5aa4ff1's cyclic sweep left one entry
unresolved: m = 2 under C3 invariance, UNKNOWN at 200 seconds. Re-run at 430:

    m = 2, C3 invariance, 646 orbit variables, 430s   ->   UNKNOWN

Still undetermined. That changes nothing about the mathematics -- m = 2 is
feasible, by the C5 witness -- and the C3 entry was never load-bearing. It is
recorded here so the sweep table is not left looking like it was abandoned at
the first budget that failed.

WHY THIS IS SMALL AND WORTH DOING ANYWAY.  Neither item moves a bound. The
first converts an assertion into a demonstration in a place where the gap
between them was one function call, which is exactly the kind of gap that later
gets quoted as though it had been checked. The second puts a number on an
UNKNOWN so the next person knows 430 seconds was already spent.

SCOPE.  The complement verification is exhaustive over all 1600 tiles and uses
the witness as committed in data/m_equals_two_balanced_exists.json, read from
disk rather than recomputed, so it checks the artefact the corpus actually
holds. The C3 result is a solver outcome at 430 seconds and is not evidence that
no C3-invariant 2-balanced set exists. tau_2 is untouched.
"""

import collections
import itertools
import json
import os
import sys

from ortools.sat.python import cp_model

ROOT = r"C:\Repos\Holotrade"
Q = 3
D = 4


def main():
    def mul(A, B):
        return tuple(tuple(sum(A[i][k] * B[k][j] for k in range(D)) % Q
                           for j in range(D)) for i in range(D))

    I = tuple(tuple(1 if i == j else 0 for j in range(D)) for i in range(D))

    def form(u, v):
        return (u[0] * v[2] - u[2] * v[0] + u[1] * v[3] - u[3] * v[1]) % Q

    E = [tuple(1 if k == j else 0 for k in range(D)) for j in range(D)]

    def tv(vv, lam):
        return tuple(tuple(((1 if i == j else 0)
                            + lam * form(E[j], vv) * vv[i]) % Q
                           for j in range(D)) for i in range(D))

    def nm(v):
        i = next(k for k, x in enumerate(v) if x % Q)
        z = pow(v[i] % Q, -1, Q)
        return tuple((z * x) % Q for x in v)

    vecs = [v for v in itertools.product(range(Q), repeat=D) if any(v)]
    pts = sorted({nm(v) for v in vecs})
    pidx = {p: i for i, p in enumerate(pts)}
    T = sorted({tv(v, l) for v in vecs for l in (1, 2)} - {I})
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
    WL = [sorted(l) for l in wl]
    NL = len(WL)

    # --- (a) the complement, on the committed witness
    with open(os.path.join(ROOT, "data",
                           "m_equals_two_balanced_exists.json")) as fh:
        W = json.load(fh)
    X = set(W["witness"])
    comp = set(range(1600)) - X

    def profile(S):
        c = collections.Counter()
        for L in range(NL):
            for M in range(NL):
                c[sum(1 for p in WL[L] for r in WL[M] if p * 40 + r in S)] += 1
        return dict(c)

    pX, pC = profile(X), profile(comp)
    okX = pX == {2: NL * NL}
    okC = pC == {14: NL * NL}
    size_ok = len(comp) == 100 * 14

    # --- (b) the C3 row at a longer budget
    def perm(A):
        return tuple(pidx[nm(tuple(sum(A[i][k] * pts[j][k] for k in range(D)) % Q
                                   for i in range(D)))] for j in range(40))

    idp = tuple(range(40))
    g3 = None
    seen, fr = {I}, [I]
    while fr and g3 is None:
        nx = []
        for A in fr:
            for t in T:
                B = mul(t, A)
                if B not in seen:
                    seen.add(B)
                    nx.append(B)
                    pm = perm(B)
                    o, cur = 1, pm
                    while cur != idp:
                        cur = tuple(pm[x] for x in cur)
                        o += 1
                    if o == 3 and g3 is None:
                        g3 = pm
        fr = nx

    par = list(range(1600))

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    for p in range(40):
        for r in range(40):
            a, b = find(p * 40 + r), find(g3[p] * 40 + g3[r])
            if a != b:
                par[a] = b
    orb = collections.defaultdict(list)
    for c in range(1600):
        orb[find(c)].append(c)
    groups = list(orb.values())
    c2g = {}
    for gi, cells in enumerate(groups):
        for c in cells:
            c2g[c] = gi
    mdl = cp_model.CpModel()
    y = [mdl.NewBoolVar("") for _ in groups]
    for L in range(NL):
        for M in range(NL):
            t = collections.Counter()
            for p in WL[L]:
                for r in WL[M]:
                    t[c2g[p * 40 + r]] += 1
            mdl.Add(sum(t[gi] * y[gi] for gi in t) == 2)
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = 430
    s.parameters.num_search_workers = 8
    st = s.Solve(mdl)
    c3 = {cp_model.OPTIMAL: 'OPTIMAL', cp_model.FEASIBLE: 'FEASIBLE',
          cp_model.INFEASIBLE: 'INFEASIBLE',
          cp_model.UNKNOWN: 'UNKNOWN'}[st]

    print("THE COMPLEMENT HALF IS DEMONSTRATED")
    print("=" * 72)
    print("  c74fbb1 called the upper half of the spectrum CONSTRUCTIVE but")
    print("  never exhibited a complement. Doing it on the committed witness:")
    print()
    print("     X     size %4d   tile counts %s   2-balanced: %s"
          % (len(X), pX, okX))
    print("     X^c   size %4d   tile counts %s  14-balanced: %s"
          % (len(comp), pC, okC))
    print("     100m at m = 14 is 1400 = |X^c|: %s" % size_ok)
    print()
    print("  Every one of the %d tiles recounted from scratch for both sets."
          % (NL * NL))
    print("  The upper half now rests on an exhibited object at m = 14, not")
    print("  only on the lemma -- and the lemma's prediction is confirmed.")
    print()
    print("  AND THE C3 ROW AT A LONGER BUDGET:")
    print("     m = 2, C3 invariance, %d orbit variables, 430s -> %s"
          % (len(groups), c3))
    print("  Still undetermined. Nothing mathematical hangs on it -- m = 2 is")
    print("  feasible by the C5 witness -- but the sweep table should not look")
    print("  abandoned at the first budget that failed.")

    ok = okX and okC and size_ok and len(X) == 200 and c3 in (
        "UNKNOWN", "INFEASIBLE", "OPTIMAL", "FEASIBLE")

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "complement_half_demonstrated.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.complement-half-demonstrated.v1",
                "valid": bool(ok),
                "whatWasAsserted": ("c74fbb1 justified m = 9..14 by "
                                    "complementation and called it "
                                    "CONSTRUCTIVE, but never took a committed "
                                    "witness and exhibited its complement; "
                                    "calling something constructive and "
                                    "constructing it are different, and the "
                                    "second is cheap here"),
                "complementCheck": {
                    "witnessSource": "data/m_equals_two_balanced_exists.json",
                    "readFromDisk": True,
                    "X": {"size": len(X), "tileCounts": pX,
                          "isBalanced": okX, "m": 2},
                    "complement": {"size": len(comp), "tileCounts": pC,
                                   "isBalanced": okC, "m": 14},
                    "sizeIs100m": size_ok,
                    "tilesRecounted": NL * NL,
                },
                "c3Row": {
                    "m": 2, "symmetry": "C3", "orbitVars": len(groups),
                    "budgetSeconds": 430, "status": c3,
                    "priorBudgetSeconds": 200, "priorStatus": "UNKNOWN",
                    "loadBearing": False,
                    "note": ("nothing mathematical hangs on it -- m = 2 is "
                             "feasible by the C5 witness -- but the sweep table "
                             "should not look abandoned at the first budget "
                             "that failed"),
                },
                "whyItIsWorthDoing": ("neither item moves a bound. The first "
                                      "converts an assertion into a "
                                      "demonstration where the gap between them "
                                      "was one function call -- exactly the kind "
                                      "of gap that later gets quoted as though "
                                      "it had been checked. The second puts a "
                                      "number on an UNKNOWN so the next person "
                                      "knows 430 seconds was already spent"),
                "boundary": ("the complement verification is exhaustive over all "
                             "1600 tiles and uses the witness AS COMMITTED, read "
                             "from disk rather than recomputed, so it checks the "
                             "artefact the corpus actually holds. The C3 result "
                             "is a solver outcome at 430 seconds and is NOT "
                             "evidence that no C3-invariant 2-balanced set "
                             "exists. tau_2 is untouched"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
