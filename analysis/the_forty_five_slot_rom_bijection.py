#!/usr/bin/env python3
"""
The explicit bijection from the 45 real PSp(4,3) expensive instructions to the
45 abstract H(3,4) ROM slots -- the mapping both tracks independently stopped
short of, and which currently makes the slow-path ROM fail closed.

THE GAP, NAMED TWICE.  fe4fb77 closed with "the identification ... is by
INVARIANTS and the classical uniqueness of the configuration, NOT by an explicit
equivariant bijection, which is not built here and is the obvious next thing to
build." The parallel track's slow-path ROM certificate
(w33_slowpath_gq_microcode_rom_summary.json) closed with "the concrete bijection
from the 45 actual PSp anomaly target IDs to these 45 abstract slots is not yet
constructed here; runtime use must fail closed until that mapping is generated
and verified." Same gap, reached from opposite directions, and it is a hard
blocker rather than a nicety: without it the ROM cannot decode a real
instruction.

THE TWO SIDES ARE BUILT INDEPENDENTLY.

    A   the 45 anomaly classes of PSp(4,3): elements whose transvection length
        exceeds their residue, paired under g ~ -g, joined when they
        ANTICOMMUTE (605f5e5)
    B   H(3,4): points of PG(3,4) on the Hermitian variety sum x_i^{q+1} = 0
        with q = 2, which over GF(4) is exactly EVEN WEIGHT -- 18 points of
        weight 2 and 27 of weight 4 -- joined when the line through them lies
        wholly in the variety

Nothing is shared between the constructions: one is a word-length predicate on
matrices over F_3, the other a Hermitian form over F_4.

THE BIJECTION IS FOUND AND VERIFIED.

    A: 45 points, 27 lines, degree 12
    B: 45 points, 27 lines, degree 12
    phi bijective                                          yes
    phi edge-preserving in BOTH directions                  yes
    phi carries each of A's 27 lines to a line of B          yes
    and ONTO all 27 of B's lines                             yes

So the identification is no longer by invariants. It is an explicit table, and
the ROM can decode against it.

IT IS A CHOICE, NOT A CANONICAL MAP, AND THAT MATTERS OPERATIONALLY.  GQ(4,2)
has a large automorphism group, so many bijections work and no one of them is
distinguished. What a ROM needs is not a canonical map but a FIXED one that is
verified -- which is what this emits. Both sides are canonically ORDERED first
(each anomaly class represented by its lexicographically smaller matrix, then
sorted; H(3,4) points sorted as GF(4) tuples) so the table is reproducible from
the certificate rather than dependent on enumeration order. Regenerating with a
different search would give a different valid table; the certificate is the
contract.

WHAT THIS UNBLOCKS.  The parallel track's ROM is 27 banks of 5 entries with
every slow target in exactly 3 banks, and its boot check verifies line size,
target multiplicity, pair uniqueness, SRG parameters and the GQ axiom before
admitting an anomaly catalogue. With this table the catalogue is admissible: a
real PSp target maps to a slot, the slot's three banks are known, and a
corrupted catalogue still fails the incidence check.

SCOPE.  Exhaustive on side A (all 51,840 elements reduced to the 45 classes) and
on side B (all 85 points of PG(3,4)). The isomorphism is found by backtracking
on the collinearity graphs and then INDEPENDENTLY re-verified: bijectivity, edge
preservation in both directions, and image of the line set checked as set
equality, not just containment. The uniqueness of GQ(4,2) is classical and
cited; it is why an isomorphism had to exist, but existence is not what is
delivered here -- the table is. No claim is made that this particular table is
equivariant for any specific group action, only that it is an isomorphism of
incidence geometries. tau_2 is untouched.
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

    # --- side A, canonically ordered
    classes = set()
    for A, L in dist.items():
        if L == 3 and rk(A) == 2:
            classes.add(min(A, mul(mI, A)))
    repsA = sorted(classes)
    NA = len(repsA)
    Aadj = [[0] * NA for _ in range(NA)]
    for i, j in itertools.combinations(range(NA), 2):
        if mul(repsA[i], repsA[j]) == mul(mI, mul(repsA[j], repsA[i])):
            Aadj[i][j] = Aadj[j][i] = 1
    cl = []

    def bk(R, P, X):
        if not P and not X:
            cl.append(frozenset(R))
            return
        for v in list(P):
            bk(R | {v}, {u for u in P if Aadj[v][u]},
               {u for u in X if Aadj[v][u]})
            P = P - {v}
            X = X | {v}

    bk(set(), set(range(NA)), set())
    Alines = sorted(tuple(sorted(c)) for c in cl if len(c) == 5)

    # --- side B, H(3,4) over GF(4), canonically ordered
    MULT = [[0, 0, 0, 0], [0, 1, 2, 3], [0, 2, 3, 1], [0, 3, 1, 2]]
    INV = [0, 1, 3, 2]

    def norm4(w):
        i = next(k for k, x in enumerate(w) if x)
        z = INV[w[i]]
        return tuple(MULT[z][x] for x in w)

    pts4 = sorted({norm4(v) for v in itertools.product(range(4), repeat=4)
                   if any(v)})

    def herm(v):
        return sum(1 for x in v if x) % 2 == 0

    H = sorted(v for v in pts4 if herm(v))
    Hi = {v: i for i, v in enumerate(H)}
    NB = len(H)

    def through(a, b):
        S = set()
        for s in range(4):
            for t in range(4):
                if s == 0 and t == 0:
                    continue
                w = tuple(MULT[s][a[k]] ^ MULT[t][b[k]] for k in range(D))
                if any(w):
                    S.add(norm4(w))
        return frozenset(S)

    Hl = set()
    for a, b in itertools.combinations(H, 2):
        L = through(a, b)
        if len(L) == 5 and all(herm(x) for x in L):
            Hl.add(L)
    Blines = sorted(tuple(sorted(Hi[x] for x in L)) for L in Hl)
    Badj = [[0] * NB for _ in range(NB)]
    for L in Blines:
        for i, j in itertools.combinations(L, 2):
            Badj[i][j] = Badj[j][i] = 1

    # --- isomorphism search
    seen, order = {0}, [0]
    while len(order) < NA:
        grew = False
        for v in list(order):
            for u in range(NA):
                if Aadj[v][u] and u not in seen:
                    seen.add(u)
                    order.append(u)
                    grew = True
        if not grew:
            for u in range(NA):
                if u not in seen:
                    seen.add(u)
                    order.append(u)
                    break
    sol = [None]

    def search(pos, mp, used):
        if sol[0] is not None:
            return
        if pos == NA:
            sol[0] = dict(mp)
            return
        v = order[pos]
        for c in range(NB):
            if c in used:
                continue
            if all(Aadj[v][u] == Badj[c][mp[u]] for u in order[:pos]):
                mp[v] = c
                used.add(c)
                search(pos + 1, mp, used)
                del mp[v]
                used.discard(c)
                if sol[0] is not None:
                    return

    search(0, {}, set())
    phi = sol[0]

    # --- independent re-verification
    bij = phi is not None and len(set(phi.values())) == NA
    edge = bij and all((Aadj[i][j] == 1) == (Badj[phi[i]][phi[j]] == 1)
                       for i, j in itertools.combinations(range(NA), 2))
    Bset = {frozenset(L) for L in Blines}
    img = {frozenset(phi[p] for p in L) for L in Alines} if bij else set()
    lines_ok = bij and img == Bset

    print("THE 45-SLOT ROM BIJECTION")
    print("=" * 72)
    print("  A  PSp(4,3) expensive instructions : %d points, %d lines, deg %s"
          % (NA, len(Alines), {sum(r) for r in Aadj}))
    print("  B  H(3,4) over GF(4)               : %d points, %d lines, deg %s"
          % (NB, len(Blines), {sum(r) for r in Badj}))
    print("     (Hermitian sum x^3 = 0 over GF(4) is exactly EVEN WEIGHT:")
    print("      %d points of weight 2 + %d of weight 4 = %d)"
          % (sum(1 for v in H if sum(1 for x in v if x) == 2),
             sum(1 for v in H if sum(1 for x in v if x) == 4), NB))
    print()
    print("  phi bijective                              %s" % bij)
    print("  phi edge-preserving in BOTH directions     %s" % edge)
    print("  phi carries A's 27 lines ONTO B's 27       %s" % lines_ok)
    print()
    print("  The identification is no longer by invariants: it is a table,")
    print("  and the slow-path ROM can decode against it.")
    print()
    print("  It is a CHOICE, not a canonical map -- GQ(4,2) has a large")
    print("  automorphism group. A ROM does not need a canonical map, it needs")
    print("  a FIXED verified one. Both sides are canonically ordered first so")
    print("  the table reproduces from the certificate, not from search order.")

    ok = bool(bij and edge and lines_ok and NA == 45 and NB == 45
              and len(Alines) == 27 and len(Blines) == 27 and dia == 5)

    if "--write" in sys.argv:
        table = []
        for i in range(NA):
            table.append({
                "slot": phi[i],
                "h34Point": list(H[phi[i]]),
                "spMatrix": [list(row) for row in repsA[i]],
            })
        p = os.path.join(ROOT, "data", "the_45_slot_rom_bijection.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.45-slot-rom-bijection.v1",
                "valid": ok,
                "theGapNamedTwice": ("fe4fb77 closed by saying the "
                                     "identification was by INVARIANTS and not "
                                     "an explicit bijection; the parallel "
                                     "track's slow-path ROM certificate closed "
                                     "by saying the concrete bijection from the "
                                     "45 actual PSp anomaly target IDs to the 45 "
                                     "abstract slots was not constructed and "
                                     "runtime must fail closed until it is. Same "
                                     "gap from opposite directions, and a hard "
                                     "blocker: without it the ROM cannot decode "
                                     "a real instruction"),
                "sideA": {
                    "what": ("the 45 anomaly classes of PSp(4,3) -- elements "
                             "whose transvection length exceeds their residue, "
                             "paired under g ~ -g, joined when they ANTICOMMUTE "
                             "(605f5e5)"),
                    "points": NA, "lines": len(Alines),
                    "degrees": sorted({sum(r) for r in Aadj}),
                },
                "sideB": {
                    "what": ("H(3,4): points of PG(3,4) on the Hermitian "
                             "variety sum x_i^{q+1} = 0 with q = 2, which over "
                             "GF(4) is exactly EVEN WEIGHT; joined when the line "
                             "through them lies wholly in the variety"),
                    "points": NB, "lines": len(Blines),
                    "degrees": sorted({sum(r) for r in Badj}),
                    "weightSplit": {
                        "weight2": sum(1 for v in H
                                       if sum(1 for x in v if x) == 2),
                        "weight4": sum(1 for v in H
                                       if sum(1 for x in v if x) == 4),
                    },
                },
                "independence": ("nothing is shared between the two "
                                 "constructions: one is a word-length predicate "
                                 "on matrices over F_3, the other a Hermitian "
                                 "form over F_4"),
                "verification": {
                    "bijective": bij,
                    "edgePreservingBothDirections": edge,
                    "linesMappedOntoLines": lines_ok,
                    "method": ("found by backtracking on the collinearity "
                               "graphs, then INDEPENDENTLY re-verified: "
                               "bijectivity, edge preservation in both "
                               "directions, and the image of the line set "
                               "checked as SET EQUALITY, not containment"),
                },
                "aChoiceNotCanonical": ("GQ(4,2) has a large automorphism group, "
                                        "so many bijections work and none is "
                                        "distinguished. A ROM does not need a "
                                        "canonical map, it needs a FIXED "
                                        "verified one. Both sides are "
                                        "canonically ORDERED first -- each "
                                        "anomaly class by its lexicographically "
                                        "smaller matrix, H(3,4) points as sorted "
                                        "GF(4) tuples -- so the table reproduces "
                                        "from this certificate rather than from "
                                        "search order. Regenerating with a "
                                        "different search gives a different "
                                        "valid table; THIS certificate is the "
                                        "contract"),
                "whatThisUnblocks": ("the parallel track's ROM is 27 banks of 5 "
                                     "with every slow target in exactly 3 banks, "
                                     "and its boot check verifies line size, "
                                     "target multiplicity, pair uniqueness, SRG "
                                     "parameters and the GQ axiom before "
                                     "admitting an anomaly catalogue. With this "
                                     "table the catalogue is admissible: a real "
                                     "PSp target maps to a slot, the slot's "
                                     "three banks are known, and a corrupted "
                                     "catalogue still fails the incidence check"),
                "linesA": [list(L) for L in Alines],
                "linesB": [list(L) for L in Blines],
                "table": table,
                "boundary": ("exhaustive on side A (all 51,840 elements reduced "
                             "to the 45 classes) and side B (all 85 points of "
                             "PG(3,4)). The uniqueness of GQ(4,2) is classical "
                             "and CITED -- it is why an isomorphism had to "
                             "exist, but existence is not what is delivered "
                             "here, the table is. NO claim that this particular "
                             "table is equivariant for any specific group "
                             "action, only that it is an isomorphism of "
                             "incidence geometries. tau_2 is untouched"),
            }, fh, indent=2)
        print("\n  written: %s  (%d-entry table)"
              % (os.path.relpath(p, ROOT), len(table)))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
