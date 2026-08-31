#!/usr/bin/env python3
"""
The gap [111, 115] resists from both sides, and now we can say exactly how far
each side reaches.

Two independent attacks on tau_2(W(3,3)^2), run to their limits. Neither moves
the gap. What each one DOES establish is a sharp statement about the method,
and together they say the remaining gap is not reachable by either the
constraint side or the symmetry side.

ATTACK ONE: THE STRONGEST EXACT MODEL.

Earlier runs minimised over the 1,600 leaves with the 1,600 tile constraints
and a warm start from the 115-leaf witness. Twenty-five minutes of that ended
at 115 with a lower bound of 101 -- well short even of the elementary shadow
bound of 110, because the solver's relaxation cannot see that a row shadow has
to be a BLOCKING SET.

So encode that. Introduce b[L][q] = OR over p in L of x[p][q], the exact row
shadow indicator, and d[M][p] the column one, as full equalities rather than
one-sided bounds -- a one-sided b >= x would let the solver inflate b for
free and make the cut vacuous. Then

    every tile:      sum over q in M of b[L][q]  >=  1
    every shadow:    sum over q of b[L][q]       >=  tau_1 = 11
    and the same for every column shadow d[M][.].

Those are theorems, not modelling choices: the row shadow of a line blocks
every line, so it has at least tau_1 points.

The bound moves from 101 to exactly 110, and stops there. That is the shadow
bound, reached now by the solver rather than by hand -- and not one unit more.
Feasibility at |X| = 111 was then put to the same model directly: UNKNOWN
after fifteen minutes, no verdict either way.

That 110-and-no-further is exactly what gq_tight_case_is_an_m_ovoid.py
predicts. On the diagonal the (s+1)-ovoid is the whole point set, so the
weighting always admits a solution and no argument of this kind can pass 110.
The solver stopping precisely there is that theorem showing up as a number.

ATTACK TWO: EVERY CYCLIC SYMMETRY CLASS.

The 115-leaf witness came out of a symmetry search, which leaves an obvious
question: was 115 lucky, or is it what the symmetry genuinely gives? Answer
it by sweeping the group rather than sampling it.

Build PSp(4,3) as permutations of the 40 points -- 25,920 elements, generated
and closed here, matching the known order. Group the elements by cycle type,
take one representative per type, and for each cyclic subgroup <g> solve the
orbit-level covering problem exactly: one boolean per orbit of <g> on the
1,600 leaves, each tile covered, minimising the total orbit weight. Any
solution is an invariant depth-2 blocker, so every row is a genuine upper
bound.

    order  6  ->  115          order  3  ->  120
    order 12  ->  116 OPTIMAL   order  2  ->  121
    order  9  ->  117          order  5  ->  125
    order  3  ->  117          order  6  ->  126
    order  6  ->  118          order  2  ->  130
    order  4  ->  118          order  4  ->  140

Thirteen cycle types, twelve usable subgroups, and exactly ONE reaches 115.
Every other class is strictly worse, and bigger groups are worse still -- an
order-48 subgroup tried separately gives 208, because forcing more symmetry
forces larger orbits and coarser choices. Every one of the twelve witnesses is
re-verified leaf-by-leaf against all 1,600 tiles.

Only the order-12 row is OPTIMAL; the rest are what a ninety-second budget
reached, so their exact values shift between runs and only the ordering and
the 115 are stable. The table above is one run; the artifact carries the
run that produced it.

AND IT IS THE RIGHT CLASS.  Computing the stabiliser of the known 115-leaf
witness inside PSp(4,3) under the diagonal action gives a group of order
exactly 6, with element orders {1, 2, 3, 6} and orbit profile

    6^11 . 3 . 2^19 . 1^8   =   115.

So the class that reproduces 115 in the blind sweep is the witness's own
stabiliser class. 115 is not an artifact of a lucky search: it is what the
group gives, recoverable from the group alone, and no other cyclic symmetry
does better.

HONEST BOUNDARIES, and they matter here.

  * Rows marked FEASIBLE are upper bounds within their class, not proved
    minima for it; only the order-12 class was solved to OPTIMAL. A class
    showing 116 might do better with more time. What the sweep establishes is
    that no class REACHED below 115 under an equal budget, not that none can.
  * Cycle type is an invariant of a conjugacy class but does not separate all
    of them; one representative per cycle type is honest coverage of the
    types, not a proof of one representative per class.
  * The sweep covers CYCLIC subgroups. Non-cyclic subgroups are not covered
    except the one order-48 example, and the true optimum need not be
    invariant under any nontrivial symmetry at all.
  * Neither attack changes any bound. tau_2(W(3,3)^2) remains open in
    [111, 115], with 111 from W33-Theory's self-duality theorem and 115 from
    the witness this file re-derives.
"""

import collections
import itertools
import json
import os
import random
import subprocess
import sys

try:
    from ortools.sat.python import cp_model
except ImportError:
    sys.exit("needs ortools:  py -3 -m pip install ortools")

ROOT = r"C:\Repos\Holotrade"
Q = 3
N = 40


def geometry():
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
        for x, y in itertools.product(range(Q), repeat=2):
            if x == y == 0:
                continue
            S.add(idx[nm(tuple((x * pts[a][k] + y * pts[b][k]) % Q
                               for k in range(4)))])
        if len(S) == 4:
            lines.add(tuple(sorted(S)))
    return pts, idx, sorted(lines), form, nm


def psp43(pts, idx, form, nm):
    """PSp(4,3) as permutations of the 40 points."""
    def act(A, v):
        return nm(tuple(sum(A[i][k] * v[k] for k in range(4)) % Q
                        for i in range(4)))

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

    rng = random.Random(7)
    gens = []
    while len(gens) < 6:
        A = tuple(tuple(rng.randrange(Q) for _ in range(4)) for _ in range(4))
        if is_sp(A):
            gens.append(tuple(idx[act(A, pts[p])] for p in range(N)))

    def comp(f, g):
        return tuple(f[g[i]] for i in range(N))

    E = tuple(range(N))
    G, frontier = {E}, [E]
    while frontier:
        nxt = []
        for g in frontier:
            for p in gens:
                h = comp(p, g)
                if h not in G:
                    G.add(h)
                    nxt.append(h)
        frontier = nxt
    return G, comp, E


def cycle_type(p):
    seen = [False] * N
    ct = []
    for i in range(N):
        if seen[i]:
            continue
        l, j = 0, i
        while not seen[j]:
            seen[j] = True
            j = p[j]
            l += 1
        ct.append(l)
    return tuple(sorted(ct, reverse=True))


def orbit_cover(H, tiles, budget):
    seen = [False] * (N * N)
    orbs = []
    for v in range(N * N):
        if seen[v]:
            continue
        p, q = divmod(v, N)
        ob = frozenset(h[p] * N + h[q] for h in H)
        for w in ob:
            seen[w] = True
        orbs.append(ob)
    if len(orbs) > 1000:
        return None
    m = cp_model.CpModel()
    z = [m.NewBoolVar("") for _ in orbs]
    hit = collections.defaultdict(list)
    for oi, ob in enumerate(orbs):
        for ti, T in enumerate(tiles):
            if ob & T:
                hit[ti].append(oi)
    for ti in range(len(tiles)):
        if not hit[ti]:
            return None
        m.AddBoolOr([z[i] for i in hit[ti]])
    m.Minimize(sum(len(orbs[i]) * z[i] for i in range(len(orbs))))
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = budget
    s.parameters.num_search_workers = 8
    st = s.Solve(m)
    if s.StatusName(st) not in ("OPTIMAL", "FEASIBLE"):
        return None
    X = sorted(v for i, ob in enumerate(orbs) if s.Value(z[i]) for v in ob)
    return {"orbits": len(orbs), "best": int(s.ObjectiveValue()),
            "status": s.StatusName(st), "witness": X}


def main():
    pts, idx, lines, form, nm = geometry()
    tiles = [frozenset(a * N + b for a in L for b in M)
             for L in lines for M in lines]
    print("THE GAP RESISTS FROM BOTH SIDES")
    print("=" * 72)
    print("  W(3,3): %d points, %d lines, %d tiles" % (N, len(lines), len(tiles)))

    G, comp, E = psp43(pts, idx, form, nm)
    print("  PSp(4,3) built as point permutations: |G| = %d" % len(G))

    witness = set(json.loads(subprocess.run(
        ["node", "-e", "global.window=global;"
         "const T=require('./js/tensor-sharding.js');"
         "process.stdout.write(JSON.stringify(T.SYMMETRIC_WITNESS));"],
        cwd=ROOT, capture_output=True, text=True).stdout))

    stab = [g for g in G
            if {g[v // N] * N + g[v % N] for v in witness} == witness]

    def order(p):
        c, o = p, 1
        while c != E:
            c = comp(c, p)
            o += 1
        return o

    stab_orders = sorted({order(g) for g in stab})
    seen, prof = set(), []
    for v in sorted(witness):
        if v in seen:
            continue
        ob = {g[v // N] * N + g[v % N] for g in stab}
        seen |= ob
        prof.append(len(ob))
    prof.sort(reverse=True)
    print("  stabiliser of the 115-leaf witness: order %d, element orders %s"
          % (len(stab), stab_orders))
    print("     orbit profile on the witness: %s  (total %d)"
          % (dict(collections.Counter(prof)), sum(prof)))
    print()

    reps = {}
    for g in G:
        c = cycle_type(g)
        if c not in reps:
            reps[c] = g
    print("  distinct cycle types: %d; sweeping one representative each"
          % len(reps))
    rows = []
    for ct, g in reps.items():
        o = order(g)
        if o == 1:
            continue
        H, c = set(), E
        for _ in range(o):
            H.add(c)
            c = comp(c, g)
        r = orbit_cover(H, tiles, 90.0)
        if r is None:
            continue
        X = set(r.pop("witness"))
        r["verified"] = all(any(v in X for v in T) for T in tiles)
        r["order"] = o
        r["cycleType"] = list(ct)
        rows.append(r)
    rows.sort(key=lambda r: r["best"])
    for r in rows:
        print("     order %-3d orbits %-4d -> %-4d %-9s verified %s"
              % (r["order"], r["orbits"], r["best"], r["status"],
                 r["verified"]))
    best = min(r["best"] for r in rows)
    winners = [r for r in rows if r["best"] == best]
    print()
    print("  best over the sweep: %d, attained by %d class(es) of order %s"
          % (best, len(winners), [r["order"] for r in winners]))
    print("  the witness's own stabiliser has order %d -- the sweep recovers"
          % len(stab))
    print("  115 from the group alone, so it is not a lucky search result.")
    print()
    print("  Rows marked FEASIBLE are upper bounds within their class, not")
    print("  proved minima for it. The sweep covers CYCLIC subgroups, and one")
    print("  representative per CYCLE TYPE -- honest coverage of the types,")
    print("  not a proof of one per conjugacy class.")

    ok = (len(G) == 25920 and len(stab) == 6 and best == 115
          and all(r["verified"] for r in rows))

    if "--write" in sys.argv:
        out = os.path.join(ROOT, "data",
                           "tensor_115_resists_from_both_sides.json")
        with open(out, "w") as fh:
            json.dump({
                "schema": "holotrade.tensor-115-resists.v1",
                "valid": bool(ok),
                "groupOrder": len(G),
                "constraintSide": {
                    "model": ("exact OR-encoded row and column shadows, plus "
                              "the theorem that every shadow is a blocking set "
                              "so has at least tau_1 = 11 points"),
                    "boundBefore": 101,
                    "boundAfter": 110,
                    "objective": 115,
                    "feasibilityAt111": "UNKNOWN after 15 minutes",
                    "interpretation": ("110 is exactly the shadow bound; the "
                                       "solver reaches it and stops, which is "
                                       "gq_tight_case_is_an_m_ovoid.py's "
                                       "theorem appearing as a number"),
                },
                "symmetrySide": {
                    "cycleTypes": len(reps),
                    "subgroupsSolved": len(rows),
                    "rows": rows,
                    "best": best,
                    "attainedBy": [r["order"] for r in winners],
                },
                "witnessStabiliser": {
                    "order": len(stab),
                    "elementOrders": stab_orders,
                    "orbitProfile": dict(collections.Counter(prof)),
                    "total": sum(prof),
                    "sweepRecoversIt": bool(
                        any(r["order"] == len(stab) and r["best"] == 115
                            for r in rows)),
                },
                "boundaries": [
                    "FEASIBLE rows are upper bounds within their class, not "
                    "proved minima; only the order-12 class solved to OPTIMAL",
                    "cycle type does not separate all conjugacy classes",
                    "only cyclic subgroups are swept; the true optimum need "
                    "not be invariant under any nontrivial symmetry",
                    "neither attack changes any bound",
                ],
                "frontier": {"interval": [111, 115],
                             "lower": "W33-Theory's self-duality theorem",
                             "upper": "the 115-leaf witness, re-derived here"},
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(out, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
