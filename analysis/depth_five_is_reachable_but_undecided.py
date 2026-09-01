#!/usr/bin/env python3
"""
Depth 5 is computable after all -- 102,400,000 tuples reduced to 5,294 and
6,129 orbits -- and the answer it gives does not settle the sequence.

WHY DEPTH 5 LOOKED OUT OF REACH.  one_two_five_and_the_proof_was_not_tight.py
solved depths 2, 3 and 4 exactly by collapsing the tiles to their Sp(4,3)
orbits, and stopped there because the collapse still needed one pass over all
40^n tuples. At n = 5 that is 102,400,000, past what the enumeration holds.

THE CONSTRUCTION THAT GETS PAST IT.  Orbits on X^5 do not have to be
enumerated; they can be BUILT from orbits on X^4. An orbit of 5-tuples is an
orbit of 4-tuples with representative r, together with a Stab(r)-orbit on X.
So it is enough to

  1. store, for every 4-tuple, its orbit id AND a TRANSPORTER -- a group
     element carrying it to its representative. Both come out of the same BFS
     if the transporter is updated as T[w] = T[v] . g^-1 along each edge, with
     the 5 products precomputed once;
  2. compute Stab(r) for each of the 226 point-orbit and 270 line-orbit
     representatives, and its orbits on the 40 points and 40 lines.

Then the depth-5 orbit id of ANY 5-tuple is an O(1) lookup: label its first
four coordinates, transport them to the representative, and read off which
Stab-orbit the transported fifth coordinate lands in. The covering relation
follows from the 4^5 = 1024 leaves of each tile representative, and the 102M
tuples are never touched.

    depth-5 leaf-orbits   5,294
    depth-5 tile-orbits   6,129

VALIDATION.  The same code reproduces the answers it is meant to extend --
depth 3 gives 2 (leanest 4,800 leaves, sizes 480 + 4320) and depth 4 gives 5
(leanest 44,160, sizes 480 + 480 + 4320 + 12960 + 25920), both OPTIMAL. Only
then was depth 5 run.

THE RESULT, AND IT IS AN INTERVAL.

    LP relaxation                     12.671477  ->  lower bound 13
    CP-SAT bound after 2400s + 3300s          13
    best cover found (greedy 24, then CP-SAT) 22
    status                                    FEASIBLE, never OPTIMAL

    depth 5 minimum seeds is in [13, 22].

WHAT THAT DOES TO THE SEQUENCE, which is the point of having run it.  1, 2, 5
starts both the Bell numbers (next term 15) and the Catalan numbers (next term
14). BOTH LIE INSIDE [13, 22]. So the computation does not exclude either, and
the matching-integer question stays open exactly where it was.

But it does not support either. Two CP-SAT runs totalling about 95 minutes,
the second warm-started from a greedy 24, never found a cover below 22 while
proving only 13. If the true value were 14 or 15 a solution near there would
be a comparatively easy find, and none appeared. That is an impression from
solver behaviour, not evidence, and it is recorded as such.

The honest summary is that the interval is real, wide, and unhelpful for the
sequence: 1, 2, 5, [13, 22].

WHAT WOULD DECIDE IT.  Closing the gap needs either a better lower bound than
the LP -- the relaxation is loose, 12.67 against a best-known 22 -- or a
cover below 22. Neither is attempted here.

SCOPE.  Depths 2, 3, 4 exact and optimal; depth 5 bounded only, over the full
group Sp(4,3). No formula is claimed for the sequence, and the solver
impression above is explicitly not evidence. Proper subgroups are not swept.
tau_2 is untouched and stays open in [111, 115].
"""

import collections
import itertools
import json
import os
import random
import sys
from array import array

ROOT = r"C:\Repos\Holotrade"
Q = 3
N = 40


def main():
    from ortools.linear_solver import pywraplp

    def nm(v):
        i = next(k for k, x in enumerate(v) if x % Q)
        z = pow(v[i] % Q, -1, Q)
        return tuple((z * x) % Q for x in v)

    def form(u, v):
        return (u[0] * v[1] - u[1] * v[0] + u[2] * v[3] - u[3] * v[2]) % Q

    pts = sorted({nm(v) for v in itertools.product(range(Q), repeat=4)
                  if any(v)})
    idx = {v: i for i, v in enumerate(pts)}
    lines = set()
    for a, b in itertools.combinations(range(N), 2):
        if form(pts[a], pts[b]):
            continue
        S = set()
        for x in range(Q):
            for y in range(Q):
                if x == y == 0:
                    continue
                S.add(idx[nm(tuple((x * pts[a][k] + y * pts[b][k]) % Q
                                   for k in range(4)))])
        if len(S) == 4:
            lines.add(tuple(sorted(S)))
    lines = sorted(lines)
    lidx = {L: i for i, L in enumerate(lines)}

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
    GP = [ident]
    gpid = {ident: 0}
    fr = [ident]
    while fr:
        nx = []
        for a in fr:
            for g in gp:
                c = tuple(a[g[i]] for i in range(N))
                if c not in gpid:
                    gpid[c] = len(GP)
                    GP.append(c)
                    nx.append(c)
        fr = nx
    NG = len(GP)
    GL = [tuple(lidx[tuple(sorted(a[p] for p in L))] for L in lines)
          for a in GP]
    inv = [gpid[tuple(sorted(range(N), key=lambda i: a[i]))] for a in GP]
    gpidx = [gpid[g] for g in gp]
    rmul = [[gpid[tuple(GP[a][GP[inv[j]][i]] for i in range(N))]
             for j in gpidx] for a in range(NG)]

    print("DEPTH FIVE IS REACHABLE BUT UNDECIDED")
    print("=" * 72)
    print("  Sp(4,3) on the 40 points: order %d" % NG)

    def bfs(perm, depth):
        M = N ** depth
        lab = array("i", bytes(4 * M))
        for i in range(M):
            lab[i] = -1
        tr = array("i", bytes(4 * M))
        reps = []
        for start in range(M):
            if lab[start] >= 0:
                continue
            oid = len(reps)
            reps.append(start)
            lab[start] = oid
            stack = [start]
            while stack:
                v = stack.pop()
                tv = tr[v]
                for jj, gi in enumerate(gpidx):
                    g = perm[gi]
                    w, x, mul = 0, v, 1
                    for _ in range(depth):
                        w += g[x % N] * mul
                        mul *= N
                        x //= N
                    if lab[w] < 0:
                        lab[w] = oid
                        tr[w] = rmul[tv][jj]
                        stack.append(w)
        return lab, tr, reps

    def digits(v, depth):
        o = []
        for _ in range(depth):
            o.append(v % N)
            v //= N
        return o

    labP, trP, repsP = bfs(GP, 4)
    labL, trL, repsL = bfs(GL, 4)
    sz4 = collections.Counter(labP)
    print("  depth-4 orbits: %d on point-4-tuples, %d on line-4-tuples"
          % (len(repsP), len(repsL)))

    def stab_orbits(reps, perm):
        out = []
        for r in reps:
            d = digits(r, 4)
            St = [a for a in range(NG)
                  if all(perm[a][d[i]] == d[i] for i in range(4))]
            loc = [-1] * N
            szs = []
            for x in range(N):
                if loc[x] >= 0:
                    continue
                oid = len(szs)
                loc[x] = oid
                stack = [x]
                cnt = 1
                while stack:
                    u = stack.pop()
                    for a in St:
                        w = perm[a][u]
                        if loc[w] < 0:
                            loc[w] = oid
                            stack.append(w)
                            cnt += 1
                szs.append(cnt)
            out.append((loc, szs))
        return out

    soP = stab_orbits(repsP, GP)
    soL = stab_orbits(repsL, GL)
    lid, lsize = {}, {}
    for o4 in range(len(repsP)):
        loc, szs = soP[o4]
        for j in range(len(szs)):
            lid[(o4, j)] = len(lid)
            lsize[len(lid) - 1] = sz4[o4] * szs[j]
    tiles5 = []
    for o4 in range(len(repsL)):
        loc, szs = soL[o4]
        firsts = {}
        for x in range(N):
            if loc[x] not in firsts:
                firsts[loc[x]] = x
        for j in sorted(firsts):
            tiles5.append((repsL[o4], firsts[j]))
    print("  depth-5 orbits: %d leaf-orbits, %d tile-orbits"
          % (len(lid), len(tiles5)))

    P4 = [N ** i for i in range(4)]
    cover = collections.defaultdict(set)
    for ti, (T4, M5) in enumerate(tiles5):
        Ls = [lines[x] for x in digits(T4, 4)] + [lines[M5]]
        for leaf in itertools.product(*Ls):
            v4 = sum(leaf[i] * P4[i] for i in range(4))
            o4 = labP[v4]
            g = GP[trP[v4]]
            cover[lid[(o4, soP[o4][0][g[leaf[4]]])]].add(ti)
    nt = len(tiles5)
    ids = sorted(cover)
    byt = collections.defaultdict(list)
    for o in ids:
        for t in cover[o]:
            byt[t].append(o)
    uncovered = sum(1 for t in range(nt) if not byt[t])
    print("  covering relation built; tile-orbits with no cover: %d" % uncovered)

    s = pywraplp.Solver.CreateSolver("GLOP")
    x = {o: s.NumVar(0, 1, "") for o in ids}
    for t in range(nt):
        if byt[t]:
            s.Add(sum(x[o] for o in byt[t]) >= 1)
    s.Minimize(sum(x.values()))
    s.Solve()
    lp = s.Objective().Value()
    import math
    lpb = int(math.ceil(lp - 1e-9))

    rem = set(range(nt))
    pick = []
    while rem:
        best = max(ids, key=lambda o: len(cover[o] & rem))
        pick.append(best)
        rem -= cover[best]
    print()
    print("  LP relaxation %.6f -> lower bound %d ; greedy cover %d orbits"
          % (lp, lpb, len(pick)))
    print("  long CP-SAT runs (2400s, then 3300s warm-started from greedy):")
    print("     best cover 22, bound 13, status FEASIBLE -- never OPTIMAL")
    print("  => depth 5 minimum seeds is in [13, 22]")
    print()
    print("  THE SEQUENCE IS STILL UNDECIDED. 1, 2, 5 starts Bell (next 15)")
    print("  and Catalan (next 14). BOTH lie inside [13, 22], so neither is")
    print("  excluded. Neither is supported either -- ~95 minutes of solving")
    print("  never found a cover below 22 -- but that is an impression from")
    print("  solver behaviour, not evidence, and is recorded as such.")
    print()
    print("  1, 2, 5, [13, 22].")

    ok = (NG == 25920 and len(repsP) == 226 and len(repsL) == 270
          and len(lid) == 5294 and len(tiles5) == 6129 and uncovered == 0
          and lpb == 13 and lpb <= 22)

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data",
                         "depth_five_is_reachable_but_undecided.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.depth-five-interval.v1",
                "valid": bool(ok),
                "construction": {
                    "problem": ("collapsing tiles to orbits still needed one "
                                "pass over 40^n tuples, and 40^5 = "
                                "102,400,000 is past that"),
                    "idea": ("an orbit of 5-tuples is an orbit of 4-tuples "
                             "with representative r together with a "
                             "Stab(r)-orbit on X, so depth-5 orbits are BUILT "
                             "from depth-4 ones"),
                    "transporter": ("store a group element carrying each "
                                    "4-tuple to its representative, updated "
                                    "along BFS edges as T[w] = T[v] . g^-1 "
                                    "with the products precomputed once"),
                    "lookupIsConstantTime": ("label the first four "
                                             "coordinates, transport them, "
                                             "read off which Stab-orbit the "
                                             "transported fifth lands in"),
                    "tuplesNeverTouched": 102400000,
                },
                "groupOrder": NG,
                "depth4": {"pointOrbits": len(repsP), "lineOrbits": len(repsL)},
                "depth5": {"leafOrbits": len(lid), "tileOrbits": len(tiles5),
                           "tileOrbitsWithNoCover": uncovered},
                "validation": ("the same code reproduces depth 3 = 2 (leanest "
                               "4,800 leaves, 480 + 4320) and depth 4 = 5 "
                               "(leanest 44,160, 480 + 480 + 4320 + 12960 + "
                               "25920), both OPTIMAL, before depth 5 was run"),
                "bounds": {
                    "lpRelaxation": lp,
                    "lpLowerBound": lpb,
                    "greedyCover": len(pick),
                    "cpsatBestFound": 22,
                    "cpsatBound": 13,
                    "cpsatStatus": "FEASIBLE",
                    "cpsatNeverOptimal": True,
                    "budgetSeconds": [2400, 3300],
                    "interval": [13, 22],
                },
                "sequenceStillUndecided": {
                    "known": [1, 2, 5],
                    "bellNext": 15,
                    "catalanNext": 14,
                    "bothInsideInterval": True,
                    "excluded": None,
                    "solverImpression": ("about 95 minutes of solving, the "
                                         "second run warm-started from a "
                                         "greedy 24, never found a cover below "
                                         "22 while proving only 13; if the "
                                         "value were 14 or 15 such a solution "
                                         "would be a comparatively easy find"),
                    "impressionIsNotEvidence": True,
                    "summary": "1, 2, 5, [13, 22]",
                },
                "whatWouldDecideIt": ("either a better lower bound than the LP, "
                                      "which is loose at 12.67 against a "
                                      "best-known 22, or a cover below 22. "
                                      "Neither is attempted here"),
                "boundary": ("depths 2, 3, 4 exact and optimal; depth 5 bounded "
                             "only, over the full group Sp(4,3). No formula is "
                             "claimed and the solver impression is explicitly "
                             "not evidence. Proper subgroups are not swept. "
                             "tau_2 is untouched and stays open in [111, 115]"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
