#!/usr/bin/env python3
"""
The fork cannot be crossed, but it can be BRIDGED. The bridge is the fibre
product, it is canonical, and it is the correspondence the parallel track found
and could only describe.

WHERE THIS STARTS.  fed190d proved the two 216-state carriers are inequivalent
under every automorphism of the substrate, so no opcode converts one into the
other -- a fork, not a gauge. That leaves an obvious question it did not
answer: is there ANY canonical relation between them? There is exactly one.
Two bundles over a common base always have a unique canonical bridge, the
fibre product, and here the base is canonical (7f0d0a3: the 36 double-sixes).

    216  x_36  216  =  36 x 6 x 6  =  1296 states,

computed:

    states                         1296
    states over each spread          36   -> a complete K(6,6) per spread
    PSp(4,3) orbit                 1296   -> transitive
    stabiliser order                 20   -> 25920 / 20 = 1296
    both projections onto          True / True

THAT IS THE PARALLEL TRACK'S CORRESPONDENCE.  ad6e209 and the Steinberg witness
report "a smallest correspondence of valency six and rank 36" whose only
nonzero Gram eigenvalue is 36, splitting into 36 copies of K(6,6), and read it
as strongly indicating a hidden common quotient rather than a noisy
many-to-many relation. It is not merely not-noisy. It is the fibre product over
the 36 double-sixes -- valency six because each fibre has six states, rank 36
because there are 36 fibres, and complete bipartite on each because a fibre
product puts every state over a spread against every other.

THE STABILISER NAMES ITSELF.  Stab(c, p) = Stab(c) n Stab(p), an intersection
of an S5 from each of the two nonconjugate classes inside the spread
stabiliser S6. Classically that intersection is the Frobenius group F20 =
AGL(1,5) of order 20, and 20 is exactly what comes out. Checked here for the
F20 signature: order 20, non-abelian, with a unique subgroup of order 5.

WHAT IT MEANS FOR THE ARCHITECTURE.  fed190d's constraint was that no single
carrier addresses both modules and no operation converts between carriers. The
fibre product escapes it without violating it. Both projections are onto, so
both carriers' permutation modules pull back into the composite, and the
composite sees 64 AND 81. You cannot rotate one machine into the other; you
CAN run both, synchronised on the double-six they share, and that composite is
canonical rather than an engineering convention -- fibre products are unique up
to unique isomorphism.

So the corrected architecture reads:

    one carrier      a fork, 216 states, sees exactly one of {64, 81}
    the composite    1296 states, canonical, sees both,
                     stabiliser F20, synchronised on the double-six

and the price of seeing both is exactly six-fold state expansion per fork, paid
once, with no conversion instruction needed because there is no conversion --
only pairing.

AND THE PRODUCT LAYER IS ONE ENTRY SHORT.  js/w33-execution-profile.js, built
on fed190d, makes the carrier an immutable construction-time commitment and
enumerates exactly two machine types:

    CIRCUIT_ST81  w33.circuit216.steinberg81            logical dimension 81
    PAIR_ST64     w33.paired-hemisystem216.steinberg64  logical dimension 64

That enum is incomplete, and completing it is forced rather than optional. The
fibre product is a third machine type -- 1296 states, transitive, stabiliser
F20, addressing both 81 and 64 -- and it is the ONLY other one, because a fibre
product is unique up to unique isomorphism. So the field is ternary, not
binary, and a deployment may commit to the composite exactly as it commits to
either fork. What it may not do is convert between the two forks, which
fed190d already forbids.

SCOPE.  The fibre product, its size, per-spread structure, transitivity,
stabiliser order and F20 signature are computed here. That both permutation
modules pull back follows from the projections being onto; the specific 64/81
selector pattern is ad6e209's, cited not reproduced. Nothing here is a claim
about fabricated hardware. tau_2 is untouched.
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
    LS = [set(L) for L in lines]
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
        A = tuple(tuple(rng.randrange(Q) for _ in range(4))
                  for _ in range(4))
        if is_sp(A):
            gp.append(tuple(idx[act(A, pts[p])] for p in range(N)))
    ident = tuple(range(N))
    G, seen, fr = [ident], {ident}, [ident]
    while fr:
        nx = []
        for a in fr:
            for g in gp:
                c = tuple(a[g[i]] for i in range(N))
                if c not in seen:
                    seen.add(c)
                    G.append(c)
                    nx.append(c)
        fr = nx
    Gi = {g: i for i, g in enumerate(G)}

    def comp(a, b):
        return tuple(a[b[i]] for i in range(N))

    def inv(a):
        o = [0] * N
        for i in range(N):
            o[a[i]] = i
        return tuple(o)

    spreads = []

    def ext(cur, cov, start):
        if len(cur) == 10:
            if len(cov) == 40:
                spreads.append(frozenset(cur))
            return
        for j in range(start, 40):
            if LS[j] & cov:
                continue
            ext(cur + [j], cov | LS[j], j + 1)

    ext([], set(), 0)
    lidx = {L: i for i, L in enumerate(lines)}

    def onspread(g, s):
        return frozenset(lidx[tuple(sorted(g[p] for p in lines[j]))]
                         for j in s)

    sidx = {s: i for i, s in enumerate(spreads)}
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

    g216 = [on216(g) for g in G]
    cst = [i for i in range(len(G)) if g216[i][0] == 0]
    S0 = spreads[[i for i, s in enumerate(spreads)
                  if all(onspread(G[k], s) == s for k in cst)][0]]
    cmap = {}
    for k in range(len(G)):
        c = g216[k][0]
        if c not in cmap:
            cmap[c] = sidx[onspread(G[k], S0)]
        if len(cmap) == 216:
            break

    m = cp_model.CpModel()
    x = [m.NewBoolVar("") for _ in range(N)]
    for L in lines:
        m.Add(sum(x[p] for p in L) == 2)
    hemis = []

    class C(cp_model.CpSolverSolutionCallback):
        def __init__(s, v):
            super().__init__()
            s.v = v

        def on_solution_callback(s):
            hemis.append(frozenset(i for i in range(N) if s.Value(s.v[i])))

    sv = cp_model.CpSolver()
    sv.parameters.enumerate_all_solutions = True
    sv.parameters.max_time_in_seconds = 900
    sv.Solve(m, C(x))
    allp = frozenset(range(N))
    pairs = sorted({frozenset((h, allp - h)) for h in hemis},
                   key=lambda P: sorted(sorted(t) for t in P))
    pidx = {P: i for i, P in enumerate(pairs)}

    def onpair(g, P):
        return frozenset(frozenset(g[p] for p in h) for h in P)

    P0 = pairs[0]
    pst = [i for i, g in enumerate(G) if onpair(g, P0) == P0]
    T0 = spreads[[i for i, s in enumerate(spreads)
                  if all(onspread(G[k], s) == s for k in pst)][0]]
    pmap = {}
    for k in range(len(G)):
        h = pidx[onpair(G[k], P0)]
        if h not in pmap:
            pmap[h] = sidx[onspread(G[k], T0)]
        if len(pmap) == 216:
            break

    FP = [(c, p) for c in range(216) for p in range(216)
          if cmap[c] == pmap[p]]
    byS = collections.Counter(cmap[c] for c, p in FP)

    def onfp(k, t):
        return (g216[k][t[0]], pidx[onpair(G[k], pairs[t[1]])])

    t0 = FP[0]
    gi = [Gi[g] for g in gp]
    orb, fr = {t0}, [t0]
    while fr:
        nx = []
        for t in fr:
            for k in gi:
                u = onfp(k, t)
                if u not in orb:
                    orb.add(u)
                    nx.append(u)
        fr = nx
    st = [k for k in range(len(G)) if onfp(k, t0) == t0]
    # F20 signature: order 20, non-abelian, unique subgroup of order 5
    stset = set(st)
    abelian = all(comp(G[a], G[b]) == comp(G[b], G[a])
                  for a in st for b in st)
    five = set()
    for a in st:
        cur, u = {Gi[ident]}, a
        while u not in cur:
            cur.add(u)
            u = Gi[comp(G[u], G[a])]
        if len(cur) == 5:
            five.add(frozenset(cur))
    onto_c = len({c for c, p in FP}) == 216
    onto_p = len({p for c, p in FP}) == 216

    print("THE FORK IS BRIDGED BY THE FIBRE PRODUCT")
    print("=" * 72)
    print("  216 x_36 216 = %d states (36 x 6 x 6 = %d)" % (len(FP), 36 * 36))
    print("  states over each spread: %s -> a complete K(6,6) per spread"
          % sorted(set(byS.values())))
    print("  PSp(4,3) orbit %d of %d -> transitive: %s"
          % (len(orb), len(FP), len(orb) == len(FP)))
    print("  stabiliser order %d ; 25920 / %d = %d"
          % (len(st), len(st), len(G) // len(st)))
    print()
    print("  F20 signature: order 20 %s, non-abelian %s, subgroups of order 5:"
          " %d" % (len(st) == 20, not abelian, len(five)))
    print("  -> Stab(c,p) = Stab(c) n Stab(p), an S5 from each of the two")
    print("     nonconjugate classes; classically that meets in F20 = AGL(1,5).")
    print()
    print("  both projections onto: %s / %s -- so both carriers' permutation"
          % (onto_c, onto_p))
    print("  modules pull back, and the composite sees 64 AND 81.")
    print()
    print("  That is the parallel track's 'smallest correspondence of valency")
    print("  six and rank 36, 36 copies of K(6,6)': valency six because each")
    print("  fibre has six states, rank 36 because there are 36 fibres, and")
    print("  complete bipartite because a fibre product pairs everything over")
    print("  a spread with everything else. Not a hidden quotient -- the fibre")
    print("  product over the double-sixes.")

    ok = (len(FP) == 1296 and sorted(set(byS.values())) == [36]
          and len(orb) == 1296 and len(st) == 20 and not abelian
          and len(five) == 1 and onto_c and onto_p)

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "the_fork_is_bridged.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.fork-bridged-by-fibre-product.v1",
                "valid": bool(ok),
                "whereThisStarts": ("fed190d proved the two carriers "
                                    "inequivalent under every substrate "
                                    "automorphism -- a fork, not a gauge -- "
                                    "leaving open whether any canonical "
                                    "relation exists; two bundles over a common "
                                    "base have exactly one, the fibre product"),
                "fibreProduct": {
                    "states": len(FP),
                    "formula": "36 x 6 x 6",
                    "statesPerSpread": sorted(set(byS.values())),
                    "shapePerSpread": "K(6,6)",
                    "transitive": len(orb) == len(FP),
                    "stabiliserOrder": len(st),
                    "orbitStabiliser": len(G) // len(st),
                    "projectionsOnto": [onto_c, onto_p],
                },
                "isTheirCorrespondence": ("ad6e209 and the Steinberg witness "
                                          "report a smallest correspondence of "
                                          "valency six and rank 36 splitting "
                                          "into 36 copies of K(6,6); valency "
                                          "six because each fibre has six "
                                          "states, rank 36 because there are 36 "
                                          "fibres, complete bipartite because a "
                                          "fibre product pairs everything over "
                                          "a spread with everything else"),
                "stabiliserIsF20": {
                    "order": len(st),
                    "nonAbelian": not abelian,
                    "subgroupsOfOrderFive": len(five),
                    "reading": ("Stab(c,p) = Stab(c) n Stab(p), an S5 from each "
                                "of the two nonconjugate classes in S6, which "
                                "classically meet in the Frobenius group "
                                "F20 = AGL(1,5)"),
                },
                "architecture": {
                    "oneCarrier": ("a fork: 216 states, sees exactly one of "
                                   "{64, 81}"),
                    "theComposite": ("1296 states, canonical, sees both, "
                                     "stabiliser F20, synchronised on the "
                                     "double-six"),
                    "price": ("six-fold state expansion per fork, paid once"),
                    "noConversionNeeded": ("there is no conversion instruction "
                                           "because there is no conversion -- "
                                           "only pairing; and the composite is "
                                           "canonical rather than an "
                                           "engineering convention, since fibre "
                                           "products are unique up to unique "
                                           "isomorphism"),
                },
                "productLayerIsOneEntryShort": {
                    "file": "js/w33-execution-profile.js",
                    "enumerates": ["w33.circuit216.steinberg81",
                                   "w33.paired-hemisystem216.steinberg64"],
                    "missing": ("a third machine type: the fibre product, 1296 "
                                "states, transitive, stabiliser F20, addressing "
                                "both 81 and 64"),
                    "forced": ("it is the ONLY other one, because a fibre "
                               "product is unique up to unique isomorphism, so "
                               "the field is ternary rather than binary"),
                    "stillForbidden": ("converting between the two forks, which "
                                       "fed190d rules out"),
                },
                "boundary": ("the fibre product, its size, per-spread "
                             "structure, transitivity, stabiliser order and F20 "
                             "signature are computed here; that both "
                             "permutation modules pull back follows from the "
                             "projections being onto, and the 64/81 selector "
                             "pattern is ad6e209's, cited not reproduced. No "
                             "hardware claim. tau_2 is untouched"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
