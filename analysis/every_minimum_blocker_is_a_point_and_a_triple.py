#!/usr/bin/env python3
"""
Every minimum blocker of W(3,3) is a point and a triple. All 360 of them,
exhaustively, with the rest of the eleven points forced.

WHY THIS IS THE RIGHT OBJECT.  tensor_110_no_local_obstruction.py's verdict on
tau_2 is that every local invariant closes, so the answer needs either an
exhaustive search or a non-local idea. An exhaustive search over the tight case
needs each of the 40 line-shadows to be a minimum blocker, and until now a
shadow was an 11-subset of 40 points constrained only by a list of derived
properties. This replaces that with two small numbers.

THE COUNT FIRST, because it forces most of the structure.  A minimum blocker B
has 11 points and meets the four lines through its centre c twice each. If c
were IN B those four lines would account for 1 + 4 = 5 points and the remaining
six would have to cover the other 36 lines with only 6 x 4 = 24 incidences.
Impossible. So c is not in B. The four pencil lines then contribute 8 points and
3 are left over, necessarily among the 27 points not collinear with c.

Verified on all 360: centre in B, 0 times; the (near, far) split is (8, 3),
360 times.

THE THEOREM, exhaustive over the complete enumeration (OPTIMAL).

  1. B has a unique centre c, and c is NOT in B.
  2. B n c^perp is the 12 neighbours of c minus a TRANSVERSAL of the pencil --
     one excluded point on each of the four lines through c. Verified: the
     excluded set has exactly 4 distinct points, 360 times.
  3. B \\ c^perp is 3 points that are PAIRWISE NON-COLLINEAR -- a partial ovoid
     of size 3 among the 27 far points. Verified: 0 collinear pairs, 360 times,
     and never three on a line.
  4. The 9 blockers sharing a centre have far-triples that PARTITION the 27 far
     points: 9 x 3 = 27, every point covered once, pairwise intersections all
     empty.
  5. (c, far triple) DETERMINES B: 360 distinct keys for 360 blockers, no
     collisions. The eight near points are forced by the three far ones.

So the minimum blockers are exactly

    { (c, T) : c a point, T a block of the canonical 9-block partition
               of the 27 points far from c },        360 = 40 x 9,

and nothing else has to be stored. The near part is not a choice.

WHAT THE 27 ARE.  The far points of c carry an 8-regular graph with lambda = 1
and mu in {0, 3} -- so it is NOT strongly regular, unlike almost everything
else in this thread. Every edge lies in exactly one triangle, giving 36
triangles, four through each point: a (27_4, 36_3) configuration. The 9
far-triples are 9 of its 945 three-cocliques, and the partition singles them
out.

WHAT IT BUYS.  A tight-case shadow assignment was 40 choices of an 11-subset of
40 points. It is now 40 choices from 360, each a pair (centre, block index in
1..9), with the consistency conditions expressible directly in those terms.
That is the reduction an exhaustive attack needs, and it is the first time the
blockers have been parametrized rather than merely counted and characterized.

SEARCHED THE LITERATURE and found no classification of W(3,3)'s minimum
blockers. The nearby published work is on blocking sets in generalised
quadrangles and polar spaces and on minimum weights of the codes of generalised
polygons; none of it gives this parametrization.

SCOPE.  Exhaustive over the complete enumeration, which returned OPTIMAL, so
these are properties of ALL 360 and not a sample. The (27_4, 36_3) reading is
a description of one far-graph, checked at one centre and transitive by the
group. tau_2 is untouched and stays open in [111, 115].
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
    thru = [[li for li, L in enumerate(lines) if p in L] for p in range(N)]
    nb = [{y for li in thru[p] for y in lines[li]} - {p} for p in range(N)]

    m = cp_model.CpModel()
    x = [m.NewBoolVar("") for _ in range(N)]
    for L in lines:
        m.AddBoolOr([x[p] for p in L])
    m.Add(sum(x) == 11)
    got = []

    class C(cp_model.CpSolverSolutionCallback):
        def __init__(s, v):
            super().__init__()
            s.v = v

        def on_solution_callback(s):
            got.append(frozenset(i for i in range(N) if s.Value(s.v[i])))

    sv = cp_model.CpSolver()
    sv.parameters.enumerate_all_solutions = True
    sv.parameters.max_time_in_seconds = 900
    status = sv.StatusName(sv.Solve(m, C(x)))

    print("EVERY MINIMUM BLOCKER IS A POINT AND A TRIPLE")
    print("=" * 72)
    print("  enumeration: %s, %d minimum blockers" % (status, len(got)))

    bycentre = collections.defaultdict(list)
    cin, split, excl, faredge, farline = 0, collections.Counter(), \
        collections.Counter(), collections.Counter(), 0
    for B in got:
        dbl = [li for li, L in enumerate(lines) if len(B & set(L)) == 2]
        c = next(p for p in range(N) if set(dbl) == set(thru[p]))
        bycentre[c].append(B)
        if c in B:
            cin += 1
        far = sorted(B - nb[c] - {c})
        split[(len(B & nb[c]), len(far))] += 1
        excl[len({next(p for p in lines[li] if p != c and p not in B)
                  for li in thru[c]})] += 1
        faredge[sum(1 for u, v in itertools.combinations(far, 2)
                    if form(pts[u], pts[v]) == 0)] += 1
        if any(set(far) <= set(L) for L in lines):
            farline += 1
    print("  1. centre in B: %d of %d" % (cin, len(got)))
    print("  2. (near, far) split: %s ; excluded transversal sizes: %s"
          % (dict(split), dict(excl)))
    print("  3. collinear pairs among the 3 far points: %s ; all on a line: %d"
          % (dict(faredge), farline))
    perc = sorted({len(v) for v in bycentre.values()})
    part = 0
    for c, Bs in bycentre.items():
        tris = [frozenset(B - nb[c] - {c}) for B in Bs]
        if (len(set().union(*tris)) == 27
                and all(not (a & b)
                        for a, b in itertools.combinations(tris, 2))):
            part += 1
    print("  4. blockers per centre %s ; far-triples partition the 27 far"
          " points at %d of %d centres" % (perc, part, len(bycentre)))
    keys = {}
    collide = 0
    for c, Bs in bycentre.items():
        for B in Bs:
            k = (c, frozenset(B - nb[c] - {c}))
            if k in keys and keys[k] != B:
                collide += 1
            keys[k] = B
    print("  5. (centre, far triple) determines B: %s -- %d keys, %d blockers"
          % (collide == 0, len(keys), len(got)))
    print()

    c0 = sorted(bycentre)[0]
    far = sorted(set(range(N)) - nb[c0] - {c0})
    fi = {p: i for i, p in enumerate(far)}
    A = [[0] * 27 for _ in range(27)]
    for u, v in itertools.combinations(far, 2):
        if form(pts[u], pts[v]) == 0:
            A[fi[u]][fi[v]] = A[fi[v]][fi[u]] = 1
    deg = sorted({sum(r) for r in A})
    lam, mu = set(), set()
    for u, v in itertools.combinations(range(27), 2):
        common = sum(1 for w in range(27) if A[u][w] and A[v][w])
        (lam if A[u][v] else mu).add(common)
    tri = sum(1 for u, v, w in itertools.combinations(range(27), 3)
              if A[u][v] and A[u][w] and A[v][w])
    coc = sum(1 for t in itertools.combinations(far, 3)
              if all(form(pts[u], pts[v]) != 0
                     for u, v in itertools.combinations(t, 2)))
    print("  THE 27 FAR POINTS: %s-regular, lambda %s, mu %s -> NOT strongly"
          % (deg, sorted(lam), sorted(mu)))
    print("  regular. Every edge in one triangle, %d triangles, %d per point:"
          % (tri, tri * 3 // 27))
    print("  a (27_4, %d_3) configuration. The 9 far-triples are 9 of its %d"
          % (tri, coc))
    print("  three-cocliques.")
    print()
    print("  => minimum blockers = { (c, T) : T a block of the canonical")
    print("     9-block partition of c's 27 far points }, 360 = 40 x 9,")
    print("     with the eight near points FORCED. A tight-case shadow is now")
    print("     a pair, not an 11-subset.")

    ok = (status == "OPTIMAL" and len(got) == 360 and cin == 0
          and dict(split) == {(8, 3): 360} and dict(excl) == {4: 360}
          and dict(faredge) == {0: 360} and farline == 0
          and perc == [9] and part == 40 and collide == 0
          and len(keys) == 360 and deg == [8] and sorted(lam) == [1]
          and sorted(mu) == [0, 3])

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data",
                         "every_minimum_blocker_is_a_point_and_a_triple.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.minimum-blocker-parametrization.v1",
                "valid": bool(ok),
                "enumeration": {"status": status, "count": len(got),
                                "exhaustive": status == "OPTIMAL"},
                "theorem": {
                    "centreNotInB": cin == 0,
                    "whyCentreIsExcluded": ("if c were in B the four pencil "
                                            "lines would use 1 + 4 = 5 points "
                                            "and the remaining six could cover "
                                            "only 6 x 4 = 24 of the other 36 "
                                            "lines"),
                    "nearFarSplit": {str(k): v for k, v in split.items()},
                    "excludedTransversalSizes": {str(k): v
                                                 for k, v in excl.items()},
                    "farCollinearPairs": {str(k): v
                                          for k, v in faredge.items()},
                    "farTripleOnALine": farline,
                    "blockersPerCentre": perc,
                    "farTriplesPartitionTheFar": part,
                    "centres": len(bycentre),
                    "keyDeterminesBlocker": collide == 0,
                    "distinctKeys": len(keys),
                },
                "parametrization": ("minimum blockers = {(c, T) : c a point, T "
                                    "a block of the canonical 9-block partition "
                                    "of the 27 points far from c}, 360 = 40 x 9, "
                                    "with the eight near points forced"),
                "theFarGraph": {
                    "vertices": 27, "degree": deg, "lambda": sorted(lam),
                    "mu": sorted(mu), "stronglyRegular": False,
                    "triangles": tri, "trianglesPerPoint": tri * 3 // 27,
                    "configuration": "(27_4, %d_3)" % tri,
                    "threeCocliques": coc,
                    "note": ("not strongly regular, unlike almost everything "
                             "else in this thread; mu takes two values"),
                },
                "whatItBuys": ("a tight-case shadow assignment was 40 choices "
                               "of an 11-subset of 40 points and is now 40 "
                               "choices from 360, each a pair (centre, block "
                               "index in 1..9), with consistency conditions "
                               "expressible in those terms -- the reduction an "
                               "exhaustive attack needs"),
                "literature": ("searched and found no classification of "
                               "W(3,3)'s minimum blockers; the nearby published "
                               "work is on blocking sets in generalised "
                               "quadrangles and polar spaces and on minimum "
                               "weights of the codes of generalised polygons"),
                "boundary": ("exhaustive over the complete enumeration, which "
                             "returned OPTIMAL, so these are properties of all "
                             "360 and not a sample; the (27_4, 36_3) reading is "
                             "checked at one centre and transitive by the group. "
                             "tau_2 is untouched and stays open in [111, 115]"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
