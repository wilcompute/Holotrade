#!/usr/bin/env python3
"""
The architecture has a cost model, and its natural instruction set is optimal
in a way the spine asserted and nobody had checked.

WHAT AN OPCODE IS.  8f2921e settled it: an opcode is well-typed exactly when it
is equivariant, so opcodes ARE elements of PSp(4,3). That makes two
architectural quantities computable, and neither had been computed:

    GROUP DIAMETER   worst-case program realising ANY transformation
                     = diameter of the Cayley graph on 25,920 elements
    STATE DIAMETER   worst-case program ROUTING one state to another
                     = diameter of the Schreier graph on the machine states

THE TRADEOFF CURVE, from random generating sets that generate the whole group,
best of many trials:

    opcodes   group diameter   state diameter (40)   state diameter (216)
       2            11                  6                    7
       3             8                  4                    5
       4             7                  3                    -

So two opcodes suffice -- PSp(4,3) is simple and 2-generated, so universality
never needs more -- but the worst-case program is eleven long. Adding
instructions buys length back with sharply diminishing returns.

AND THE SUBSTRATE HAS A BETTER ANSWER THAN ANY RANDOM SET.  The symplectic
TRANSVECTIONS, T(v, lam) : x -> x + lam <x,v> v, are the architecturally
natural instructions -- one per point of W(3,3), 80 in all as 40 inverse pairs.
They generate PSp(4,3) exactly, and:

    Cayley diameter with the full transvection set     4
    address-transfer diameter on the 40 points         2
    carrier-state diameter on the 216                  2

Four instructions realise ANY transformation, and TWO route any state to any
other. Against the best two-opcode set's 11 and 7, that is not a marginal
improvement; it is a different regime, bought with 40 opcodes instead of 2.

THE SPINE'S CLAIM IS CONFIRMED.  The canonical architecture spine asserts that
"all address transfers require zero, one, or two rank-one symplectic
transvections". That is exactly a diameter-2 statement about the transvection
Schreier graph, and it comes out at 2 -- on the 40 points and, newly, on the
216 carrier states as well. The assertion was carried as architecture; it is
now a computed fact, and it extends to the carrier.

WHERE THE LITERATURE SITS.  Diameter bounds for Cayley graphs of classical
groups are known precisely for generating sets CONTAINING A TRANSVECTION, of
the form (log|G|)^c -- so the architecturally natural ISA is exactly the case
the theory covers. No exact diameter for PSp(4,3) appears in the accessible
literature, so the 4 and the 2 here are computed values rather than lookups.

THE ARCHITECTURAL READING.  The instruction set is not a design decision either.
One opcode per point of W(3,3), forty of them, is the set that makes routing
diameter two and universality diameter four; the minimum-instruction machine is
two opcodes and pays eleven. Both ends of that curve are derived, and the
substrate's own preferred point sits at the transvections.

SCOPE.  The transvection numbers are exact -- full BFS over the whole group and
over every state. The random-set numbers are the best found over many trials
and are therefore UPPER bounds on the optimal diameter at each instruction
count, not proven minima. Nothing here is a claim about fabricated hardware or
about instruction latency; the diameters count opcodes, not cycles.
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
SCRATCH = (r"C:\Users\wiljd\AppData\Local\Temp\claude"
           r"\c--Repos-Theory-of-Everything"
           r"\593b31ce-ce26-4c6b-9e86-0847c6c879fd\scratchpad")


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
    ident = tuple(range(N))

    def transvection(vv, lam):
        out = []
        for p in range(N):
            x = pts[p]
            c = (lam * form(x, vv)) % Q
            out.append(idx[nm(tuple((x[k] + c * vv[k]) % Q
                                    for k in range(4)))])
        return tuple(out)

    T = sorted({t for p in range(N) for lam in (1, 2)
                if (t := transvection(pts[p], lam)) != ident})

    def closure(gens):
        S, fr = {ident}, [ident]
        while fr:
            nx = []
            for a in fr:
                for g in gens:
                    c = tuple(a[g[i]] for i in range(N))
                    if c not in S:
                        S.add(c)
                        nx.append(c)
            fr = nx
        return S

    Gsize = len(closure(T))

    def diam_group(gens):
        dist, fr, d = {ident: 0}, [ident], 0
        while fr:
            nx = []
            for a in fr:
                for g in gens:
                    c = tuple(a[g[i]] for i in range(N))
                    if c not in dist:
                        dist[c] = d + 1
                        nx.append(c)
            fr = nx
            if nx:
                d += 1
        return max(dist.values()), len(dist)

    def diam_states(perms, n):
        worst = 0
        for s0 in range(n):
            dist, fr, d = {s0: 0}, [s0], 0
            while fr:
                nx = []
                for s in fr:
                    for p in perms:
                        t = p[s]
                        if t not in dist:
                            dist[t] = d + 1
                            nx.append(t)
                fr = nx
                if nx:
                    d += 1
            if len(dist) < n:
                return None
            worst = max(worst, max(dist.values()))
        return worst

    raw = open(os.path.join(SCRATCH, "circuits.txt")).read().strip().split("\n")
    circuits = [tuple(int(v) - 1 for v in c.split(","))
                for c in raw[0].split("|")[1].split(";")]
    supports = [tuple(int(v) - 1 for v in s.split(","))
                for s in raw[1].split("|")[1].split(";")]
    supset = {frozenset(s): i for i, s in enumerate(supports)}
    cidx = {frozenset(c): i for i, c in enumerate(circuits)}

    def on216(g):
        h = tuple(supset[frozenset(g[p] for p in s)] for s in supports)
        return tuple(cidx[frozenset(h[v] for v in c)] for c in circuits)

    tg, reach = diam_group(T)
    t40 = diam_states(T, N)
    t216 = diam_states([on216(g) for g in T], 216)

    def inv(a):
        o = [0] * N
        for i in range(N):
            o[a[i]] = i
        return tuple(o)

    rng = random.Random(7)
    pool = []
    while len(pool) < 300:
        A = tuple(tuple(rng.randrange(Q) for _ in range(4))
                  for _ in range(4))
        ok = True
        for i, j in itertools.combinations(range(4), 2):
            ei = tuple(1 if k == i else 0 for k in range(4))
            ej = tuple(1 if k == j else 0 for k in range(4))
            u = tuple(sum(A[r][k] * ei[k] for k in range(4)) % Q
                      for r in range(4))
            v = tuple(sum(A[r][k] * ej[k] for k in range(4)) % Q
                      for r in range(4))
            if form(u, v) != form(ei, ej):
                ok = False
                break
        if ok:
            pool.append(tuple(idx[nm(tuple(sum(A[i][k] * pts[p][k]
                                               for k in range(4)) % Q
                                           for i in range(4)))]
                              for p in range(N)))

    curve = []
    for k in (2, 3, 4):
        best = None
        for _ in range(60):
            gens = rng.sample(pool, k)
            if len(closure(gens)) != Gsize:
                continue
            gd, _ = diam_group(list(gens) + [inv(g) for g in gens])
            if best is not None and gd > best["groupDiameter"]:
                continue
            P = list(gens) + [inv(g) for g in gens]
            best = {"opcodes": k, "groupDiameter": gd,
                    "stateDiameter40": diam_states(P, N),
                    "stateDiameter216": diam_states(
                        [on216(g) for g in P], 216)}
        if best:
            curve.append(best)

    print("THE ISA COST MODEL AND THE TRANSVECTION OPTIMUM")
    print("=" * 72)
    print("  an opcode is an equivariant permutation, i.e. an element of")
    print("  PSp(4,3) -- so both diameters are architectural quantities.")
    print()
    print("  opcodes   group diam   state diam (40)   state diam (216)")
    for r in curve:
        print("    %2d          %2d              %s                 %s"
              % (r["opcodes"], r["groupDiameter"],
                 r["stateDiameter40"], r["stateDiameter216"]))
    print()
    print("  TRANSVECTIONS: %d of them (40 inverse pairs, one per point),"
          % len(T))
    print("  generating a group of order %d (= PSp(4,3): %s)"
          % (Gsize, Gsize == 25920))
    print("     Cayley diameter                        %d" % tg)
    print("     address-transfer diameter on the 40    %d" % t40)
    print("     carrier-state diameter on the 216      %d" % t216)
    print()
    print("  The spine asserts address transfers need 'zero, one, or two")
    print("  rank-one symplectic transvections'. That is a diameter-2 claim:")
    print("  %s -- and it extends to the 216 carrier, also %d."
          % ("CONFIRMED" if t40 <= 2 else "REFUTED", t216))
    print()
    print("  Four opcodes realise ANY transformation and TWO route any state")
    print("  to any other, against the best 2-opcode set's %d and %d. The"
          % (curve[0]["groupDiameter"], curve[0]["stateDiameter216"]))
    print("  instruction set is not a design decision either.")

    ok = (Gsize == 25920 and len(T) == 80 and tg == 4 and t40 == 2
          and t216 == 2 and reach == 25920 and len(curve) >= 2)

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "the_isa_cost_model.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.isa-cost-model-transvections.v1",
                "valid": bool(ok),
                "whatAnOpcodeIs": ("8f2921e: an opcode is well-typed exactly "
                                   "when it is equivariant, so opcodes are "
                                   "elements of PSp(4,3)"),
                "quantities": {
                    "groupDiameter": ("worst-case program realising any "
                                      "transformation"),
                    "stateDiameter": ("worst-case program routing one state to "
                                      "another"),
                },
                "tradeoffCurve": curve,
                "transvections": {
                    "count": len(T),
                    "structure": "40 inverse pairs, one per point of W(3,3)",
                    "generates": Gsize,
                    "isPSp": Gsize == 25920,
                    "cayleyDiameter": tg,
                    "reached": reach,
                    "stateDiameter40": t40,
                    "stateDiameter216": t216,
                },
                "spineClaimConfirmed": {
                    "claim": ("all address transfers require zero, one, or two "
                              "rank-one symplectic transvections"),
                    "isADiameterClaim": True,
                    "measured40": t40,
                    "measured216": t216,
                    "verdict": "CONFIRMED" if t40 <= 2 else "REFUTED",
                    "newPart": ("it extends to the 216 carrier states, not just "
                                "the 40 points"),
                },
                "literature": ("diameter bounds for Cayley graphs of classical "
                               "groups are known precisely for generating sets "
                               "CONTAINING A TRANSVECTION, of the form "
                               "(log|G|)^c, so the architecturally natural ISA "
                               "is exactly the covered case; no exact diameter "
                               "for PSp(4,3) appears in the accessible "
                               "literature, so these are computed values not "
                               "lookups"),
                "reading": ("the instruction set is not a design decision "
                            "either: one opcode per point, forty of them, makes "
                            "routing diameter two and universality diameter "
                            "four, while the minimum-instruction machine is two "
                            "opcodes and pays eleven"),
                "boundary": ("the transvection numbers are exact, from full BFS "
                             "over the group and over every state; the "
                             "random-set numbers are the best found over many "
                             "trials and are UPPER bounds on the optimal "
                             "diameter at each instruction count, not proven "
                             "minima. The diameters count opcodes, not cycles, "
                             "and nothing here is a claim about fabricated "
                             "hardware"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
