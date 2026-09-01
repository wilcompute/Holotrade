#!/usr/bin/env python3
"""
1, 2, 5. Depth 4 needs five seeds, not three -- the proof that gave three was
sound and loose, and the reduction that made this computable is one line.

THE REDUCTION.  A depth-4 set cover over 40^4 = 2,560,000 tiles is not a small
problem, and it does not need to be solved. Covering is Sp(4,3)-equivariant: a
leaf v covers a tile T if and only if gv covers gT. So whether an ORBIT covers
a tile depends only on the tile's ORBIT, and the ground set collapses

    2,560,000 tiles  ->  270 tile-orbits
    2,560,000 leaves ->  226 leaf-orbits

with the covering relation read off directly: for a tile representative
(L_1, ..., L_4), the leaves that cover it are exactly the 4^4 = 256 points of
its lines, and each one names its orbit. The whole depth-4 question becomes a
226 x 270 set cover, which CP-SAT settles exactly.

THE ANSWER, all three depths solved to OPTIMAL by the same code:

    depth 2      3 leaf-orbits,   3 tile-orbits    1 seed        480 leaves
    depth 3     18 leaf-orbits,  20 tile-orbits    2 seeds     4,800 leaves
    depth 4    226 leaf-orbits, 270 tile-orbits    5 seeds    44,160 leaves

Depths 2 and 3 reproduce the enumerations they replace, which is the check on
the reduction. Depth 4 is new. The leanest minimum cover is

    25920 + 12960 + 4320 + 480 + 480  =  44,160 leaves,

and the best single orbit reaches only 185 of the 270 tile-orbits.

THE PROOF WAS NOT TIGHT, and that is worth recording plainly.
the_seed_count_strictly_increases_with_depth.py proved depth 4 needs at least
THREE, from two witness families: the all-repeated tile (L, L, L, L) and one
tile combining a repeated line with a transversal-free triple. The true answer
is five. The proof is correct and it captures less than half the obstruction --
there are constraints at depth 4 that neither witness family sees.

THE SEQUENCE, AND WHY IT IS NOT A RESULT.  1, 2, 5 is the start of the Bell
numbers (1, 2, 5, 15, 52) and equally the start of the Catalan numbers
(1, 2, 5, 14, 42). Three small integers agree with both. This repo has been
here before -- Pass 1471 and 1476 in W33-Theory record `90 = 90` as a matching
integer that took a full decomposition to refute -- so no formula is claimed
here. The two candidates disagree at depth 5, where Bell says 15 and Catalan
says 14, and depth 5 was NOT computed: 40^5 = 102,400,000 tuples is past what
the orbit enumeration above will hold. Until that is done, 1, 2, 5 is three
data points and nothing more.

WHAT IS SAFE TO SAY.  The seed count grows, and it grows faster than the proof
technique can currently show. The jump from 2 to 5 is the interesting one: at
depth 3 a single degenerate orbit repairs a single positional blind spot, while
at depth 4 the blind spots multiply -- five orbits of sizes 25920, 12960, 4320,
480 and 480, spanning nearly the whole size range, are needed before every tile
class is met.

SCOPE.  Exact and optimal at depths 2, 3, 4 over the full group Sp(4,3).
Depth 5 is not computed and no formula is claimed. Proper subgroups are not
swept. tau_2 is untouched and stays open in [111, 115].
"""

import collections
import itertools
import json
import os
import random
import sys

ROOT = r"C:\Repos\Holotrade"
Q = 3
N = 40


def main():
    from ortools.sat.python import cp_model

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
    pg = []
    while len(pg) < 5:
        A = tuple(tuple(rng.randrange(Q) for _ in range(4)) for _ in range(4))
        if is_sp(A):
            pg.append(tuple(idx[act(A, pts[p])] for p in range(N)))
    lg = [tuple(lidx[tuple(sorted(g[p] for p in L))] for L in lines)
          for g in pg]

    def orbits(gens, depth):
        M = N ** depth
        lab = [-1] * M
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
                for g in gens:
                    w, x, mul = 0, v, 1
                    for _ in range(depth):
                        w += g[x % N] * mul
                        mul *= N
                        x //= N
                    if lab[w] < 0:
                        lab[w] = oid
                        stack.append(w)
        return lab, reps

    print("1, 2, 5 -- AND THE PROOF WAS NOT TIGHT")
    print("=" * 72)
    print("  Covering is Sp(4,3)-equivariant, so whether an ORBIT covers a tile")
    print("  depends only on the tile's ORBIT. The ground set collapses and")
    print("  depth 4 becomes a small exact problem instead of a 2,560,000 one.")
    print()

    rows = []
    for depth in (2, 3, 4):
        plab, preps = orbits(pg, depth)
        llab, lreps = orbits(lg, depth)
        nt = len(lreps)
        pw = [N ** i for i in range(depth)]

        def digits(v):
            o = []
            for _ in range(depth):
                o.append(v % N)
                v //= N
            return o

        covers = collections.defaultdict(set)
        for ti, T in enumerate(lreps):
            for leaf in itertools.product(*[lines[x] for x in digits(T)]):
                covers[plab[sum(leaf[i] * pw[i] for i in range(depth))]].add(ti)
        osz = collections.Counter(plab)
        ids = sorted(covers)

        m = cp_model.CpModel()
        x = {o: m.NewBoolVar("o%d" % o) for o in ids}
        for t in range(nt):
            m.AddBoolOr([x[o] for o in ids if t in covers[o]])
        m.Minimize(sum(x.values()))
        s = cp_model.CpSolver()
        s.parameters.max_time_in_seconds = 600
        st = s.Solve(m)
        k = sum(1 for o in ids if s.Value(x[o]))

        m2 = cp_model.CpModel()
        y = {o: m2.NewBoolVar("y%d" % o) for o in ids}
        for t in range(nt):
            m2.AddBoolOr([y[o] for o in ids if t in covers[o]])
        m2.Add(sum(y.values()) == k)
        m2.Minimize(sum(osz[o] * y[o] for o in ids))
        s2 = cp_model.CpSolver()
        s2.parameters.max_time_in_seconds = 600
        st2 = s2.Solve(m2)
        chosen = [o for o in ids if s2.Value(y[o])]
        best1 = max(len(covers[o]) for o in ids)

        rows.append({
            "depth": depth, "tiles": N ** depth,
            "leafOrbits": len(preps), "tileOrbits": nt,
            "minimumSeeds": k, "status": s.StatusName(st),
            "leanestLeaves": sum(osz[o] for o in chosen),
            "leanestStatus": s2.StatusName(st2),
            "orbitSizes": sorted(osz[o] for o in chosen),
            "bestSingleOrbitTileOrbits": best1,
        })
        print("  depth %d: %9d tiles -> %3d tile-orbits, %3d leaf-orbits"
              % (depth, N ** depth, nt, len(preps)))
        print("           MINIMUM %d seeds (%s), leanest %d leaves (%s)"
              % (k, s.StatusName(st), sum(osz[o] for o in chosen),
                 s2.StatusName(st2)))
        print("           sizes %s ; best single orbit reaches %d/%d"
              % (sorted(osz[o] for o in chosen), best1, nt))
    print()

    seq = [r["minimumSeeds"] for r in rows]
    bell = [1, 2, 5, 15, 52]
    catalan = [1, 2, 5, 14, 42]
    print("  THE SEQUENCE IS %s -- and that is NOT a result." % seq)
    print("  Bell    starts %s" % bell[:len(seq)])
    print("  Catalan starts %s" % catalan[:len(seq)])
    print("  Three small integers agree with both. W33-Theory's Passes 1471")
    print("  and 1476 record '90 = 90' as a matching integer that needed a")
    print("  full decomposition to refute, so no formula is claimed. The two")
    print("  disagree at depth 5 (15 vs 14) and depth 5 was NOT computed:")
    print("  40^5 = 102,400,000 tuples is past this enumeration.")
    print()
    print("  AND THE PROOF WAS NOT TIGHT. The earlier witness argument proved")
    print("  depth 4 needs >= 3, from two witness families. The truth is 5, so")
    print("  it captures less than half the obstruction. Correct, and loose.")

    ok = (seq == [1, 2, 5]
          and all(r["status"] == "OPTIMAL" for r in rows)
          and all(r["leanestStatus"] == "OPTIMAL" for r in rows)
          and rows[0]["leanestLeaves"] == 480
          and rows[1]["leanestLeaves"] == 4800
          and rows[2]["tileOrbits"] == 270 and rows[2]["leafOrbits"] == 226)

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data",
                         "one_two_five_and_the_proof_was_not_tight.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.one-two-five-depth-seeds.v1",
                "valid": bool(ok),
                "reduction": ("covering is Sp(4,3)-equivariant, so whether an "
                              "orbit covers a tile depends only on the tile's "
                              "orbit; the ground set collapses from 40^n tiles "
                              "to the tile-orbits and the covering relation is "
                              "read off the 4^n points of a representative's "
                              "lines"),
                "rows": rows,
                "sequence": seq,
                "sequenceIsNotAResult": {
                    "bell": bell,
                    "catalan": catalan,
                    "why": ("three small integers agree with both; W33-Theory "
                            "Passes 1471 and 1476 record '90 = 90' as a "
                            "matching integer that needed a full decomposition "
                            "to refute"),
                    "theyDisagreeAt": {"depth": 5, "bell": 15, "catalan": 14},
                    "depth5NotComputed": ("40^5 = 102,400,000 tuples is past "
                                          "this orbit enumeration"),
                },
                "proofWasNotTight": {
                    "file": "the_seed_count_strictly_increases_with_depth.py",
                    "proved": 3,
                    "truth": 5,
                    "reading": ("the witness argument is correct and captures "
                                "less than half the obstruction -- there are "
                                "depth-4 constraints neither witness family "
                                "sees"),
                },
                "boundary": ("exact and optimal at depths 2, 3, 4 over the full "
                             "group Sp(4,3). Depth 5 is not computed and no "
                             "formula is claimed. Proper subgroups are not "
                             "swept. tau_2 is untouched and stays open in "
                             "[111, 115]"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
