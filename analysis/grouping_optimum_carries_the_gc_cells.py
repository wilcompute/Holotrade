#!/usr/bin/env python3
"""
Every optimal two-qutrit grouping schedule carries both Grunbaum-Coxeter
cells -- and that is a q = 3 statement, not a law.

WHOSE THEOREM THIS IS.  W33-Theory's BT836 ("The Grunbaum-Coxeter Connection:
Hemi-Dodecahedra Live Inside the Spreads") proves that the cells of the
11-cell and the 57-cell sit inside W(3,3), one in every spread:

  * the 11-cell {3,5,3}_5 has 11 hemi-icosahedral cells, group PSL(2,11);
    the hemi-icosahedron has skeleton K_6;
  * the 57-cell {5,3,5}_5 has 57 hemi-dodecahedral cells, group PSL(2,19);
    the hemi-dodecahedron has skeleton the PETERSEN graph;
  * a spread's stabiliser in PSp(4,3) has order 720 = |S_6|, its icosahedral
    core A_5 splits the 45 line pairs as 15 + 30, and the 15-orbit graph on
    the 10 spread lines is Petersen.

REPRODUCED HERE FROM SCRATCH, every step, because a claim this pretty deserves
an independent build rather than a citation:

    spread found by exact cover: 10 lines covering all 40 points exactly once
    |PSp(4,3)| = 25920
    spread stabiliser order = 720                                  (= |S_6|)
    an A_5 of order 60 inside it
    A_5 orbits on the 45 line pairs: sizes [15, 30]                (Kneser)
    the 15-orbit graph on the 10 lines is PETERSEN                 (networkx)

WHAT IS ADDED: THE GROUPING READING.  the_dual_measurement_question_never_fails
showed that the minimum number of measurement contexts covering all Paulis is
q^n+1 in every case, always OPTIMAL, and always attained by an exact PARTITION
-- that is, by a SPREAD. So the optimal Pauli-grouping schedule is not merely
some spread; a spread is exactly what optimality forces.

Combining that with BT836:

    EVERY optimal two-qutrit measurement-grouping schedule carries the cell of
    the 11-cell (K_6, on the hidden 6-set) and the cell of the 57-cell
    (Petersen, on its own ten settings).

The two exceptional Grunbaum-Coxeter polytopes are not decoration on the
substrate. Their cells are forced by the requirement that the schedule be
optimal.

AND IT IS ANCHORED TO q = 3.  A spread of W(3,q) has q^2+1 lines, and the
Petersen graph has exactly 10 vertices. So the identification needs

    q^2 + 1 = 10,   i.e.   q = 3,

and nothing else:

    q = 2 -> 5 lines,  q = 4 -> 17,  q = 5 -> 26,  q = 7 -> 50,  q = 8 -> 65.

At every other q the optimal grouping schedule still exists and is still a
spread -- that part is general, and proved -- but it carries no Petersen,
because the line count is wrong. The Grunbaum-Coxeter connection is a
qutrit-specific coincidence sitting on top of a general theorem.

That distinction is the reason this file exists rather than a triumphant one.
This project works at q = 3 by default, and it has already been caught once
welding two unrelated invariants together because they agreed at q = 3 (the
two tens, in context_cover_equals_mub_count_iff_q_even.py). The grouping
theorem is general; the polytope reading is not; and the arithmetic that
separates them is one line.

SCOPE.  BT836's theorem is theirs and is reproduced, not extended. What is new
is the fusion with the grouping optimum, and the explicit generality test. No
bound moves.
"""

import collections
import itertools
import json
import os
import random
import sys

try:
    from ortools.sat.python import cp_model
    import networkx as nx
except ImportError:
    sys.exit("needs ortools and networkx")

ROOT = r"C:\Repos\Holotrade"
Q = 3


def build(q):
    def nm(v):
        i = next(k for k, x in enumerate(v) if x % q)
        z = pow(v[i] % q, -1, q)
        return tuple((z * x) % q for x in v)

    def form(u, v):
        return (u[0] * v[1] - u[1] * v[0] + u[2] * v[3] - u[3] * v[2]) % q

    pts = sorted({nm(v) for v in itertools.product(range(q), repeat=4)
                  if any(v)})
    idx = {v: i for i, v in enumerate(pts)}
    lines = set()
    for a, b in itertools.combinations(range(len(pts)), 2):
        if form(pts[a], pts[b]):
            continue
        S = set()
        for x, y in itertools.product(range(q), repeat=2):
            if x == y == 0:
                continue
            S.add(idx[nm(tuple((x * pts[a][k] + y * pts[b][k]) % q
                               for k in range(4)))])
        if len(S) == q + 1:
            lines.add(tuple(sorted(S)))
    return pts, idx, sorted(lines), form, nm


def main():
    print("THE GROUPING OPTIMUM CARRIES BOTH GRUNBAUM-COXETER CELLS")
    print("=" * 72)
    print("  A spread of W(3,q) has q^2+1 lines; Petersen has 10 vertices.")
    sizes = {}
    for q in (2, 3, 4, 5, 7, 8):
        sizes[q] = q * q + 1
        print("     q=%d -> %-3d lines  %s"
              % (q, q * q + 1, "MATCH" if q * q + 1 == 10 else ""))
    print()

    pts, idx, lines, form, nm = build(Q)
    N = len(pts)
    m = cp_model.CpModel()
    y = [m.NewBoolVar("") for _ in lines]
    for p in range(N):
        m.Add(sum(y[i] for i, L in enumerate(lines) if p in L) == 1)
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = 60.0
    s.parameters.num_search_workers = 8
    st = s.Solve(m)
    spread = [lines[i] for i in range(len(lines)) if s.Value(y[i])]
    cover = collections.Counter(p for L in spread for p in L)
    exact = sorted(cover.values()) == [1] * N

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

    rng = random.Random(7)
    gens = []
    while len(gens) < 6:
        A = tuple(tuple(rng.randrange(Q) for _ in range(4)) for _ in range(4))
        if is_sp(A):
            gens.append(tuple(idx[act(A, pts[p])] for p in range(N)))

    def comp(f, g):
        return tuple(f[g[i]] for i in range(N))

    E = tuple(range(N))
    G, fr = {E}, [E]
    while fr:
        nx2 = []
        for g in fr:
            for p in gens:
                h = comp(p, g)
                if h not in G:
                    G.add(h)
                    nx2.append(h)
        fr = nx2

    sp = {tuple(sorted(L)) for L in spread}
    stab = [g for g in G
            if {tuple(sorted(g[p] for p in L)) for L in spread} == sp]

    def order_of(g):
        c, o = g, 1
        while c != E:
            c = comp(c, g)
            o += 1
        return o

    A5 = None
    cand = [g for g in stab if order_of(g) in (2, 3, 5)]
    rng.shuffle(cand)
    for a, b in itertools.combinations(cand[:40], 2):
        S, fr2, ok = {E}, [E], True
        while fr2 and ok:
            nx3 = []
            for g in fr2:
                for p in (a, b):
                    h = comp(p, g)
                    if h not in S:
                        S.add(h)
                        nx3.append(h)
                        if len(S) > 60:
                            ok = False
                            break
                if not ok:
                    break
            fr2 = nx3
        if ok and len(S) == 60:
            A5 = S
            break

    orbit_sizes, petersen = None, None
    if A5:
        seen, orbs = set(), []
        for pr in itertools.combinations(range(len(spread)), 2):
            if pr in seen:
                continue
            L1, L2 = spread[pr[0]], spread[pr[1]]
            ob = set()
            for g in A5:
                i1 = next(i for i, L in enumerate(spread)
                          if tuple(sorted(g[p] for p in L1)) == tuple(sorted(L)))
                i2 = next(i for i, L in enumerate(spread)
                          if tuple(sorted(g[p] for p in L2)) == tuple(sorted(L)))
                ob.add(tuple(sorted((i1, i2))))
            seen |= ob
            orbs.append(sorted(ob))
        orbit_sizes = sorted(len(o) for o in orbs)
        for o in orbs:
            if len(o) == 15:
                g15 = nx.Graph()
                g15.add_nodes_from(range(10))
                g15.add_edges_from(o)
                petersen = nx.is_isomorphic(g15, nx.petersen_graph())

    print("  reproducing BT836 from scratch:")
    print("     spread: %d lines, covers all %d points exactly once: %s"
          % (len(spread), N, exact))
    print("     |PSp(4,3)| = %d" % len(G))
    print("     spread stabiliser order = %d  (= |S_6|: %s)"
          % (len(stab), len(stab) == 720))
    print("     A_5 of order 60 inside it: %s" % (A5 is not None))
    print("     A_5 orbits on the %d line pairs: %s"
          % (len(spread) * (len(spread) - 1) // 2, orbit_sizes))
    print("     the 15-orbit graph on the 10 lines is PETERSEN: %s" % petersen)
    print()
    print("  THE GROUPING READING. The minimum context cover is q^n+1 always,")
    print("  always OPTIMAL, and always an exact PARTITION -- a spread. So a")
    print("  spread is what optimality FORCES, not a choice. Hence every")
    print("  optimal two-qutrit grouping schedule carries K_6 (the 11-cell's")
    print("  cell, on the hidden 6-set) and Petersen (the 57-cell's cell).")
    print()
    print("  AND IT IS q = 3 ONLY. Petersen needs 10 vertices and a spread has")
    print("  q^2+1 lines, so the identification needs q = 3. At every other q")
    print("  the optimal schedule is still a spread -- general, and proved --")
    print("  but carries no Petersen. General theorem, qutrit-specific reading.")

    ok = (exact and len(G) == 25920 and len(stab) == 720
          and A5 is not None and orbit_sizes == [15, 30] and petersen is True)

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data",
                         "grouping_optimum_carries_the_gc_cells.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.gc-cells-in-grouping-optimum.v1",
                "valid": bool(ok),
                "theoremIsTheirs": ("W33-Theory BT836, 'The Grunbaum-Coxeter "
                                    "Connection: Hemi-Dodecahedra Live Inside "
                                    "the Spreads'"),
                "reproduced": {
                    "spreadLines": len(spread), "coversExactlyOnce": exact,
                    "groupOrder": len(G),
                    "spreadStabiliserOrder": len(stab),
                    "stabiliserIsS6Order": len(stab) == 720,
                    "a5Found": A5 is not None,
                    "a5OrbitsOnLinePairs": orbit_sizes,
                    "fifteenOrbitIsPetersen": petersen,
                },
                "cells": {
                    "11-cell": {"cells": 11, "group": "PSL(2,11)",
                                "cellSkeleton": "K_6"},
                    "57-cell": {"cells": 57, "group": "PSL(2,19)",
                                "cellSkeleton": "Petersen"},
                },
                "groupingReading": ("the minimum context cover is q^n+1 always, "
                                    "always OPTIMAL and always an exact "
                                    "partition, so a spread is what optimality "
                                    "forces; hence every optimal two-qutrit "
                                    "grouping schedule carries both cells"),
                "anchoredToQ3": {
                    "reason": ("a spread of W(3,q) has q^2+1 lines and Petersen "
                               "has 10 vertices, so the identification needs "
                               "q^2+1 = 10, i.e. q = 3"),
                    "spreadSizes": sizes,
                    "generalPart": ("the optimal schedule is a spread at every "
                                    "q -- that is proved and general"),
                    "specificPart": ("the Petersen/K_6 reading exists only at "
                                     "q = 3"),
                },
                "whyStated": ("this project works at q = 3 by default and has "
                              "already been caught welding two invariants "
                              "together because they agreed there"),
                "boundary": ("BT836's theorem is reproduced, not extended; the "
                             "fusion with the grouping optimum and the "
                             "generality test are what is added. No bound "
                             "moves."),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
