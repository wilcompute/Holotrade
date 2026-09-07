#!/usr/bin/env python3
"""
The instruction cost model, which mentions no geometry at all, reconstructs the
entire Schlafli configuration: 27 lines, 36 double-sixes, 45 tritangent planes.

WHAT THE COST MODEL KNOWS.  Nothing geometric. It is defined by one predicate --
does an element of Sp(4,3) need more transvections than its residue? -- which is
O'Meara's hyperbolic-map condition (3595bd1) and refers only to a bilinear form
and a word length. No cubic surface, no lines, no planes, no E6. Yet running it
out gives all three Schlafli numbers with their classical incidences.

    45  the anomaly set in PSp(4,3)                            (3a0a194)
    27  its maximal ANTICOMMUTING sets, = lines of GQ(4,2)     (605f5e5)
    36  double-sixes among those 27                            (here)

THE THIRD NUMBER, WHICH IS THE TEST.  27 and 45 could be a coincidence of small
integers. 36 cannot, because a double-six is not just a pair of disjoint sixers
-- it needs a bijection a_i <-> b_i with a_i SKEW to b_i and MEETING every other
b_j. That is a rigid condition and it either holds or it does not:

    each line meets 10 and is skew to 16          classical, and it holds
    sixers (6 pairwise skew lines)                72    [classical 72]
    double-six partners per sixer                  1    [classical: exactly 1]
    DOUBLE-SIXES                                  36    [classical 36]
    lines covered by a double-six                 12    [classical 12]

A looser reading -- any two disjoint sixers -- gives 756, so the count is not
robust to getting the definition wrong, and 36 is not something a wrong
construction stumbles into. Every sixer has exactly one partner, which is the
classical statement, and 72/2 = 36.

WHY THIS MATTERS MORE THAN A THIRD MATCHING NUMBER.  The corpus already owns
these objects, from directions that have nothing to do with instruction cost:

  * BT810 identifies the 36 W(3,3) spreads with the 36 DOUBLE-SIXES, and names
    the 45 tritangent planes.
  * The W33-Theory track's Passes 368-371 (analysis/THE_27_FOLD_WAY.md) show
    E6/2E6 splits 1 + 27 + 36, with the 36 nonsingular classes the root pairs
    AND the 36 spreads, and the 27 isotropic classes "the 27 of the cubic
    surface" -- the same 27 on which the order-27 exponent-3 Heisenberg group,
    the single-qutrit Pauli group, acts regularly.
  * 0d8d33e built the 216 carrier states as a principal 6-fibration over those
    36 double-sixes, fibre = Schlafli's six letters.
  * 4952a3b makes the 45 the sentinel code's minimum-weight words.

So 27, 36 and 45 were already the spreads, the root pairs, the carrier's base,
and the code's minimum weight. What is new is that the COST FUNCTION produces
them -- that "which instructions are expensive" is not a separate fact about the
machine but the same configuration, arrived at from a word-length predicate.

AND THE TWO PAULI GROUPS SIT ON THE SAME 27.  The other track's 27 carries an
order-27, exponent-3 extraspecial group: the qutrit Pauli group, acting
regularly. This file's 27 INDEXES order-32 extraspecial 2^{1+4}_- groups, one
per line, qubit-shaped (34f2a84). A 3-group acting on the 27 and a 2-group
indexed by it, on what the counts say is the same 27. Neither track could see
that from its own side.

SCOPE, AND IT MATTERS HERE.  The Schlafli configuration is classical, as is
GQ(4,2) as the (lines, tritangent planes) incidence of a cubic surface and the
27/36/45 counts. All of that is CITED. What is computed here is that the ISA
anomaly set carries it: the meet/skew split, the 72 sixers, the unique-partner
property, and the 36. The identification of THIS 27 with the other track's 27 --
and of these 36 with BT810's spreads -- is by INVARIANTS and by the classical
uniqueness of the configuration, NOT by an explicit equivariant bijection, which
is not built here and is the obvious next thing to build. tau_2 is untouched.
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
    lines = [c for c in cl if len(c) == 5]
    m = len(lines)

    meet = [[0] * m for _ in range(m)]
    for i, j in itertools.combinations(range(m), 2):
        if lines[i] & lines[j]:
            meet[i][j] = meet[j][i] = 1
    skew = [[0 if i == j else 1 - meet[i][j] for j in range(m)]
            for i in range(m)]
    md = {sum(r) for r in meet}
    sd = {sum(r) for r in skew}

    six = []

    def ext(cur, cand):
        if len(cur) == 6:
            six.append(tuple(sorted(cur)))
            return
        for v in list(cand):
            if not cur or v > max(cur):
                ext(cur + [v], [u for u in cand if skew[v][u]])

    ext([], list(range(m)))

    ds, prof = set(), collections.Counter()
    loose = 0
    for A in six:
        partners = 0
        for B in six:
            if set(A) & set(B):
                continue
            loose += 1
            da = [sum(1 for b in B if skew[a][b]) for a in A]
            db = [sum(1 for a in A if skew[a][b]) for b in B]
            if all(d == 1 for d in da) and all(d == 1 for d in db):
                ds.add(frozenset([A, B]))
                partners += 1
        prof[partners] += 1
    cover = collections.Counter(len(set(a) | set(b))
                                for p in ds for a, b in [tuple(p)])

    print("THE COST MODEL RECONSTRUCTS THE CUBIC SURFACE")
    print("=" * 72)
    print("  the cost model mentions no geometry: it is one predicate,")
    print("  'does g need more transvections than its residue'.")
    print()
    print("     45  the anomaly set in PSp(4,3)          %s" % (n == 45))
    print("     27  maximal ANTICOMMUTING sets           %s" % (m == 27))
    print("     36  double-sixes among those 27          %s" % (len(ds) == 36))
    print()
    print("  each line meets %s and is skew to %s   [classical 10 / 16]"
          % (md, sd))
    print("  sixers (6 pairwise skew lines)     %3d   [classical 72]"
          % len(six))
    print("  double-six partners per sixer      %s   [classical: exactly 1]"
          % dict(prof))
    print("  DOUBLE-SIXES                       %3d   [classical 36]"
          % len(ds))
    print("  lines covered by a double-six      %s   [classical 12]"
          % dict(cover))
    print()
    print("  the loose reading -- any two disjoint sixers -- gives %d, so 36"
          % (loose // 2))
    print("  is not a count a wrong construction stumbles into.")
    print()
    print("  ALREADY IN THE CORPUS, from directions unrelated to cost:")
    print("    BT810: the 36 W(3,3) spreads ARE the 36 double-sixes; 45")
    print("           tritangent planes")
    print("    W33-Theory Passes 368-371 (THE_27_FOLD_WAY.md): E6/2E6 splits")
    print("           1+27+36, the 36 are root pairs AND spreads, the 27 are")
    print("           'the 27 of the cubic surface', carrying the order-27")
    print("           exponent-3 qutrit Pauli group regularly")
    print("    0d8d33e: the 216 carrier is a 6-fibration over those 36")
    print("    4952a3b: the 45 are the sentinel code's minimum-weight words")
    print()
    print("  So 27/36/45 were already the spreads, the E6 root pairs, the")
    print("  carrier's base and the code's minimum weight. What is new is that")
    print("  the COST FUNCTION produces them: 'which instructions are")
    print("  expensive' is not a separate fact about the machine.")
    print()
    print("  AND TWO PAULI GROUPS SIT ON THE SAME 27: an order-27 exponent-3")
    print("  QUTRIT Pauli group acting regularly (their track), and order-32")
    print("  extraspecial 2^{1+4}_- QUBIT-shaped groups indexed one per line")
    print("  (34f2a84). Neither track could see that from its own side.")

    ok = (n == 45 and m == 27 and len(six) == 72 and dict(prof) == {1: 72}
          and len(ds) == 36 and dict(cover) == {12: 36}
          and md == {10} and sd == {16} and dia == 5)

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data",
                         "the_cost_model_reconstructs_the_cubic_surface.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.cost-model-is-the-cubic-surface.v1",
                "valid": bool(ok),
                "whatTheCostModelKnows": ("nothing geometric: one predicate, "
                                          "'does g need more transvections than "
                                          "its residue', which is O'Meara's "
                                          "hyperbolic-map condition (3595bd1) "
                                          "and refers only to a bilinear form "
                                          "and a word length -- no cubic "
                                          "surface, no lines, no planes, no E6"),
                "theThreeNumbers": {
                    "tritangentPlanes": n,
                    "lines": m,
                    "doubleSixes": len(ds),
                    "provenance": {
                        "45": "the anomaly set in PSp(4,3) (3a0a194)",
                        "27": ("its maximal ANTICOMMUTING sets = lines of "
                               "GQ(4,2) (605f5e5)"),
                        "36": "double-sixes among those 27 (here)",
                    },
                },
                "theRigidTest": {
                    "meetDegree": sorted(md),
                    "skewDegree": sorted(sd),
                    "sixers": len(six),
                    "partnersPerSixer": {str(k): v for k, v in prof.items()},
                    "doubleSixes": len(ds),
                    "linesCovered": {str(k): v for k, v in cover.items()},
                    "looseReadingGives": loose // 2,
                    "reading": ("a double-six needs a bijection a_i <-> b_i with "
                                "a_i SKEW to b_i and MEETING every other b_j; "
                                "the loose reading (any two disjoint sixers) "
                                "gives %d, so 36 is not a count a wrong "
                                "construction stumbles into, and every sixer "
                                "having exactly one partner is the classical "
                                "statement" % (loose // 2)),
                },
                "alreadyInTheCorpus": [
                    ("BT810: the 36 W(3,3) spreads ARE the 36 double-sixes, and "
                     "the 45 tritangent planes are named there"),
                    ("W33-Theory Passes 368-371, analysis/THE_27_FOLD_WAY.md: "
                     "E6/2E6 splits 1+27+36, the 36 nonsingular classes are the "
                     "root pairs AND the 36 spreads, the 27 isotropic classes "
                     "are 'the 27 of the cubic surface', on which the order-27 "
                     "exponent-3 Heisenberg group -- the single-qutrit Pauli "
                     "group -- acts regularly"),
                    ("0d8d33e: the 216 carrier states are a principal "
                     "6-fibration over those 36 double-sixes, fibre = "
                     "Schlafli's six letters"),
                    ("4952a3b: the 45 are the sentinel code's minimum-weight "
                     "words"),
                ],
                "whatIsNew": ("27, 36 and 45 were already the spreads, the E6 "
                              "root pairs, the carrier's base and the code's "
                              "minimum weight. What is new is that the COST "
                              "FUNCTION produces them -- 'which instructions are "
                              "expensive' is not a separate fact about the "
                              "machine but the same configuration, reached from "
                              "a word-length predicate"),
                "twoPauliGroupsOnOne27": ("the other track's 27 carries an "
                                          "order-27 exponent-3 extraspecial "
                                          "group (qutrit Pauli) acting "
                                          "regularly; this 27 INDEXES order-32 "
                                          "extraspecial 2^{1+4}_- groups, one "
                                          "per line, qubit-shaped (34f2a84). A "
                                          "3-group acting on the 27 and a "
                                          "2-group indexed by it, on what the "
                                          "counts say is the same 27 -- neither "
                                          "track could see that from its own "
                                          "side"),
                "boundary": ("the Schlafli configuration is classical, as is "
                             "GQ(4,2) as the (lines, tritangent planes) "
                             "incidence of a cubic surface and the 27/36/45 "
                             "counts; all CITED. What is computed is that the "
                             "ISA anomaly set carries it: the meet/skew split, "
                             "the 72 sixers, the unique-partner property and the "
                             "36. The identification of THIS 27 with the other "
                             "track's 27, and of these 36 with BT810's spreads, "
                             "is by INVARIANTS and the classical uniqueness of "
                             "the configuration, NOT by an explicit equivariant "
                             "bijection -- that is not built here and is the "
                             "obvious next thing to build. tau_2 is untouched"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
