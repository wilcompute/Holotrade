#!/usr/bin/env python3
"""
The 27 lines of the cost quadrangle carry the Schlafli graph, and each one
generates an extraspecial 2-group -- twenty-seven characteristic-TWO Pauli
groups sitting inside a characteristic-three substrate, all sharing one centre.

WHERE THIS STARTS.  605f5e5 showed the 45 expensive instructions form GQ(4,2)
under anticommutation, with 27 lines recovered as maximal cliques. A line is a
set of 5 pairwise ANTICOMMUTING involutions, and 2n + 1 = 5 is exactly the
classical ceiling on a pairwise anticommuting set in a rank-n symplectic space.
So the lines are not incidental: they are maximal anticommuting sets at the
theoretical maximum. That invites three questions nobody asked, and all three
answer cleanly.

(1) THE CEILING IS ATTAINED AND NOTHING EXCEEDS IT.

    maximal anticommuting sets, by size        {5: 27}

Every maximal set has exactly 5 elements -- no 6 exists anywhere among the 45,
and no smaller set is maximal. The bound 2n + 1 is met, uniformly, 27 times.

(2) THE 27 CARRY THE SCHLAFLI GRAPH.  Join two lines when they meet in a point:

    meet graph on the 27          SRG(27, 10, 1, 5)   = GQ(2,4) collinearity
    its complement                SRG(27, 16, 10, 8)  = the SCHLAFLI GRAPH

So the dual quadrangle is not an analogy, it is present on the same data: the
45 points give GQ(4,2), the 27 lines give GQ(2,4), and the complement of the
latter is the Schlafli graph of the 27 lines of a cubic surface. The
instruction-cost structure realises both halves of the configuration and the
graph that sits over them.

The automorphism group of the Schlafli graph is W(E6), of order 51,840 --
classical, and cited rather than recomputed here. That is |Sp(4,3)|, the number
this corpus keeps arriving at from other directions.

(3) EACH LINE GENERATES AN EXTRASPECIAL 2-GROUP.  Take the 5 anticommuting
involutions of a line and close under multiplication:

    order                         32        on all 27 lines
    |centre|                       2
    G' = Z                      true
    |G/Z|                         16, elementary abelian
    involutions                   11
    elements of order 4           20

Order 32 with centre of order 2, derived subgroup equal to the centre, and
elementary abelian quotient of order 16: that is extraspecial 2^{1+4}. The
counts 11 and 20 settle the type -- plus type has 19 involutions and 12 elements
of order 4, minus type has 11 and 20 -- so every one of the 27 is

    2^{1+4}_-  =  D8 o Q8,

the central product, which is the shape of a two-qubit Pauli group. Five
pairwise anticommuting involutions generating an extraspecial 2-group is the
Pauli relation exactly, and it is happening inside Sp(4,3), over F_3.

AND THEY ALL SHARE ONE CENTRE, WHICH IS -I.

    distinct centres across all 27 lines        1
    and it is {I, -I} = Z(Sp(4,3))           true

That is the third job -I has been found doing. 3a0a194 showed it implements the
symplectic polarity on the 45 anomalies, and explains why Sp's count looked like
90 + 1. Here it is the common centre of all 27 extraspecial groups. One central
element organises the polarity, the anomaly count, and every Pauli group in the
picture.

WHAT IS ACTUALLY STRANGE HERE.  This substrate is q = 3. Its instruction set is
qutrit Clifford. Yet its cost anomalies generate 2-GROUPS -- twenty-seven copies
of an extraspecial group of order 32, indexed by the 27 lines of a cubic
surface. The characteristic-two structure is not imported; it arises from the
anticommutation relation among reflections, which is a sign condition and knows
nothing about the field. The qubit shape lives inside the qutrit machine, and
the cost model is where it shows.

SCOPE.  Exhaustive: the 45 are 3a0a194's anomaly classes, cliques by
Bron-Kerbosch, SRG parameters and group orders computed rather than assumed, the
extraspecial type settled by the involution/order-4 census against the standard
classification. What is CITED and not derived here: GQ(4,2)-GQ(2,4) duality; the
Schlafli graph as SRG(27,16,10,8) on the 27 lines of a cubic surface; its
automorphism group being W(E6) of order 51,840; the 2n+1 ceiling on
anticommuting sets; and the involution counts distinguishing 2^{1+4}_+ from
2^{1+4}_-. No claim is made that these 27 groups are Pauli groups of an actual
qubit register -- the isomorphism type is what is established, not a physical
identification. tau_2 is untouched.
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

    anom = [A for A, L in dist.items() if L == 3 and rk(A) == 2]
    reps, seen = [], set()
    for A in anom:
        k = frozenset([A, mul(mI, A)])
        if k not in seen:
            seen.add(k)
            reps.append(A)
    n = len(reps)

    adj = [[0] * n for _ in range(n)]
    for i, j in itertools.combinations(range(n), 2):
        if mul(reps[i], reps[j]) == mul(mI, mul(reps[j], reps[i])):
            adj[i][j] = adj[j][i] = 1

    cl = []

    def bk(R, P, X):
        if not P and not X:
            cl.append(frozenset(R))
            return
        for v in list(P):
            bk(R | {v}, {u for u in P if adj[v][u]},
               {u for u in X if adj[v][u]})
            P = P - {v}
            X = X | {v}

    bk(set(), set(range(n)), set())
    sizes = collections.Counter(len(c) for c in cl)
    lines = [c for c in cl if len(c) == 5]
    m = len(lines)

    def srg(A, N):
        d = {sum(A[i]) for i in range(N)}
        if len(d) != 1:
            return None
        k = d.pop()
        lam, mu = set(), set()
        for i, j in itertools.combinations(range(N), 2):
            c = sum(1 for x in range(N) if A[i][x] and A[j][x])
            (lam if A[i][j] else mu).add(c)
        if len(lam) != 1 or len(mu) != 1:
            return None
        return [N, k, lam.pop(), mu.pop()]

    meet = [[0] * m for _ in range(m)]
    for i, j in itertools.combinations(range(m), 2):
        if lines[i] & lines[j]:
            meet[i][j] = meet[j][i] = 1
    comp = [[0 if i == j else 1 - meet[i][j] for j in range(m)]
            for i in range(m)]
    s_meet, s_comp = srg(meet, m), srg(comp, m)

    def closure(gens):
        S, fr2 = {I}, [I]
        while fr2:
            nx = []
            for a in fr2:
                for g in gens:
                    c = mul(a, g)
                    if c not in S:
                        S.add(c)
                        nx.append(c)
            fr2 = nx
        return S

    census = collections.Counter()
    centres = set()
    for L in lines:
        G = closure([reps[i] for i in L])
        Z = frozenset(g for g in G if all(mul(g, h) == mul(h, g) for h in G))
        Dg = {I}
        inv = {}
        for a in G:
            inv[a] = next(x for x in G if mul(a, x) == I)
        for a in G:
            for b in G:
                Dg.add(mul(mul(a, b), mul(inv[a], inv[b])))
        cos = {frozenset(mul(g, z) for z in Z) for g in G}
        elem = all(mul(g, g) in Z for g in G)
        ninv = sum(1 for g in G if g != I and mul(g, g) == I)
        n4 = sum(1 for g in G
                 if mul(g, g) != I and mul(mul(g, g), mul(g, g)) == I)
        census[(len(G), len(Z), frozenset(Dg) == Z, len(cos), elem,
                ninv, n4)] += 1
        centres.add(Z)
    key = next(iter(census))
    same_centre = len(centres) == 1 and next(iter(centres)) == frozenset(
        [I, mI])

    print("THE 27 LINES ARE PAULI GROUPS")
    print("=" * 72)
    print("  (1) maximal anticommuting sets, by size: %s" % dict(sizes))
    print("      2n+1 = 5 is the ceiling; attained, uniformly, %d times" % m)
    print()
    print("  (2) meet graph on the %d lines      SRG %s" % (m, s_meet))
    print("      -> GQ(2,4) collinearity          %s" % (s_meet == [27, 10, 1, 5]))
    print("      complement                       SRG %s" % s_comp)
    print("      -> the SCHLAFLI graph            %s"
          % (s_comp == [27, 16, 10, 8]))
    print("      Aut(Schlafli) = W(E6), order 51,840 = |Sp(4,3)|  [cited]")
    print()
    print("  (3) group generated by each line's 5 anticommuting involutions:")
    print("      order %d, |Z| %d, G'=Z %s, |G/Z| %d elem-abelian %s"
          % (key[0], key[1], key[2], key[3], key[4]))
    print("      involutions %d, order-4 elements %d" % (key[5], key[6]))
    print("      -> extraspecial 2^{1+4}, and the counts 11/20 give MINUS")
    print("         type: 2^{1+4}_- = D8 o Q8, the two-qubit Pauli shape")
    print("      uniform across all %d lines: %s" % (m, census[key] == m))
    print()
    print("      distinct centres across all %d lines: %d" % (m, len(centres)))
    print("      and it is {I,-I} = Z(Sp(4,3)): %s" % same_centre)
    print()
    print("  -I now has three jobs: it implements the polarity on the 45,")
    print("  it explains why Sp's anomaly count looked like 90 + 1, and it")
    print("  is the common centre of every one of these 27 groups.")
    print()
    print("  The substrate is q = 3, its instruction set is qutrit Clifford,")
    print("  and its cost anomalies generate 2-GROUPS. The characteristic-two")
    print("  structure is not imported: it comes from anticommutation, a sign")
    print("  condition that knows nothing about the field.")

    ok = (dict(sizes) == {5: 27} and m == 27 and n == 45
          and s_meet == [27, 10, 1, 5] and s_comp == [27, 16, 10, 8]
          and key == (32, 2, True, 16, True, 11, 20) and census[key] == 27
          and same_centre and dia == 5)

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "the_27_lines_are_pauli_groups.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.27-lines-are-pauli-groups.v1",
                "valid": bool(ok),
                "whereThisStarts": ("605f5e5 showed the 45 expensive "
                                    "instructions form GQ(4,2) under "
                                    "anticommutation with 27 lines recovered as "
                                    "maximal cliques; a line is 5 pairwise "
                                    "ANTICOMMUTING involutions, and 2n+1 = 5 is "
                                    "the classical ceiling on an anticommuting "
                                    "set in a rank-n symplectic space, so the "
                                    "lines are maximal anticommuting sets at "
                                    "the theoretical maximum"),
                "ceiling": {
                    "maximalSetSizes": {str(k): v for k, v in sizes.items()},
                    "bound": "2n + 1 = 5",
                    "attained": True,
                    "nothingExceedsIt": max(len(c) for c in cl) == 5,
                },
                "theSchlafliGraph": {
                    "lines": m,
                    "meetGraph": s_meet,
                    "isGQ24Collinearity": s_meet == [27, 10, 1, 5],
                    "complement": s_comp,
                    "isSchlafli": s_comp == [27, 16, 10, 8],
                    "reading": ("the dual quadrangle is not an analogy but "
                                "present on the same data: 45 points give "
                                "GQ(4,2), 27 lines give GQ(2,4), and the "
                                "complement of the latter is the Schlafli graph "
                                "of the 27 lines of a cubic surface"),
                    "automorphismGroup": ("Aut(Schlafli) = W(E6) of order "
                                          "51,840 = |Sp(4,3)| -- classical, "
                                          "CITED not recomputed"),
                },
                "extraspecial": {
                    "order": key[0], "centreOrder": key[1],
                    "derivedEqualsCentre": key[2],
                    "quotientOrder": key[3],
                    "quotientElementaryAbelian": key[4],
                    "involutions": key[5], "orderFourElements": key[6],
                    "uniformAcrossAllLines": census[key] == m,
                    "type": "2^{1+4}_- = D8 o Q8",
                    "typeReasoning": ("order 32 with |Z| = 2, G' = Z and G/Z "
                                      "elementary abelian of order 16 is "
                                      "extraspecial 2^{1+4}; plus type has 19 "
                                      "involutions and 12 elements of order 4, "
                                      "minus type 11 and 20, so these are all "
                                      "minus type -- the two-qubit Pauli shape"),
                },
                "oneCentre": {
                    "distinctCentres": len(centres),
                    "isCentreOfSp43": same_centre,
                    "reading": ("-I now has three jobs: it implements the "
                                "symplectic polarity on the 45 anomalies "
                                "(3a0a194), it explains why Sp's anomaly count "
                                "looked like 90 + 1, and it is the common "
                                "centre of every one of these 27 extraspecial "
                                "groups"),
                },
                "whatIsStrange": ("this substrate is q = 3 and its instruction "
                                  "set is qutrit Clifford, yet its cost "
                                  "anomalies generate 2-GROUPS -- 27 copies of "
                                  "an extraspecial group of order 32, indexed by "
                                  "the 27 lines of a cubic surface. The "
                                  "characteristic-two structure is not imported; "
                                  "it comes from anticommutation, a sign "
                                  "condition that knows nothing about the field. "
                                  "The qubit shape lives inside the qutrit "
                                  "machine, and the cost model is where it shows"),
                "boundary": ("exhaustive; the 45 are 3a0a194's anomaly classes, "
                             "cliques by Bron-Kerbosch, SRG parameters and group "
                             "orders computed rather than assumed, extraspecial "
                             "type settled by the involution/order-4 census "
                             "against the standard classification. CITED and not "
                             "derived: GQ(4,2)-GQ(2,4) duality; the Schlafli "
                             "graph as SRG(27,16,10,8) on the 27 lines of a "
                             "cubic surface; Aut(Schlafli) = W(E6) of order "
                             "51,840; the 2n+1 ceiling; and the involution "
                             "counts distinguishing the two extraspecial types. "
                             "NO claim is made that these 27 groups are Pauli "
                             "groups of an actual qubit register -- the "
                             "isomorphism type is what is established, not a "
                             "physical identification. tau_2 is untouched"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
