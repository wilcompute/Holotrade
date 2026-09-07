#!/usr/bin/env python3
"""
The 45 expensive instructions are not a set. Under ANTI-commutation they are
GQ(4,2) -- the dual of the carrier's quadrangle, and the Schlafli configuration
of the cubic surface.

WHERE THIS STARTS.  3a0a194 showed the projective ISA has exactly 45 expensive
instructions, one per minimum-weight codeword. That was a counting statement:
45 objects, matched one-to-one. It left the obvious question unasked -- 45 is
the tritangent count of a cubic surface, whose partner is 27, so if the cost
structure is really Schlafli then the 45 must carry a GEOMETRY and not merely a
cardinality.

THEY DO, AND THE RELATION IS ANTI-COMMUTATION.  Join two of the 45 when their
reflections anticommute, gh = -hg. Then:

    strictly commuting pairs (gh = hg)                        0
    anticommuting pairs                                     270
    remaining pairs                                         720
                                                    C(45,2) = 990

Not one pair of the forty-five commutes. The relation is entirely
anticommutation, which is the Pauli incompatibility relation -- the same one
that makes mutually incompatible Paulis partial ovoids of a symplectic polar
space in this corpus. In PSp the sign disappears, so these are exactly the pairs
that commute PROJECTIVELY, which is why the machine sees them as compatible and
the matrix group does not.

AND THE GRAPH IS A GENERALIZED QUADRANGLE.

    45 vertices, 270 edges, 12-REGULAR
    strongly regular with parameters       (45, 12, 3, 3)
    maximal cliques: 27, EVERY ONE of size 5
    lines per point: 3      flags: 135 = 27 x 5 = 45 x 3
    GQ axiom: a point off a line is collinear with exactly one point of it

45 points, 27 lines, 5 points per line, 3 per point: GQ(4,2) = H(3,4), with the
27 lines recovered as maximal cliques rather than assumed. Its 27 lines are the
27 lines of the cubic surface and its 45 points the 45 tritangent planes, so the
instruction-cost structure is the Schlafli configuration entire, not half of it.

THE GEOMETRIC FORM OF THE RELATION.  Writing L for the hyperbolic line of an
anomaly and L^perp for its polar:

    adjacent  <=>  L n M = empty  AND  L n M^perp = empty

    L meets M only              414 pairs   not adjacent
    L meets M^perp only         306 pairs   not adjacent
    meets neither               270 pairs   ADJACENT

So two expensive instructions are collinear exactly when their polar pairs are
mutually skew. A plausible-looking alternative -- that M is spanned by a point
of L and a point of L^perp -- accounts for ZERO of the 270 and is simply wrong;
it was tested rather than assumed.

WHAT IT MEANS.  GQ(4,2) is the point-line DUAL of GQ(2,4), which is the carrier
geometry this substrate has been running on all along (27 points, 45 lines,
tau_1 = 10, no ovoid). So the machine's cheap structure and its expensive
structure are dual quadrangles: instructions live on W(3,3), states on GQ(2,4),
and the cost irregularity on GQ(2,4)'s dual. The anomaly is not a defect
scattered through the instruction set; it is a second geometry, and it is the
one belonging to the 27 lines.

A CONVERGENCE WORTH NAMING.  a149d0b built GQ(4,2) on these same 45 polar pairs
from a completely different direction -- the depth-3 blocking obstruction, joined
by all-isotropic reguli -- and reported 45 vertices, 270 edges, 12-regular, 27
maximal cliques all of size 5, GQ axiom. Identical invariants, reached from
blocking sets rather than from Cayley-graph lengths. That the same quadrangle
answers "which triples fail to block" and "which instructions cost extra" is the
kind of coincidence this repository exists to notice.

SCOPE.  Exhaustive over all 51,840 elements; the 45 are the anomaly classes of
3a0a194, the relation is tested on matrices, the SRG parameters and the 27 lines
are computed (cliques by Bron-Kerbosch, not assumed), and the GQ axiom is
checked on every point-line pair. GQ(4,2) on 45 tritangent planes is classical,
as is its duality with GQ(2,4); what is computed here is that the ISA's anomaly
set carries it under anticommutation. The identification with a149d0b's graph is
by INVARIANTS only -- both are GQ(4,2) on the 45 polar pairs, but that the
identity map on polar pairs is an isomorphism between them is NOT established
here. tau_2 is untouched.
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

    def act(A, v):
        return tuple(sum(A[i][k] * v[k] for k in range(D)) % Q
                     for i in range(D))

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

    def rk_rows(rows):
        R = [list(x) for x in rows]
        r = 0
        for c in range(D):
            p = next((i for i in range(r, len(R)) if R[i][c] % Q), None)
            if p is None:
                continue
            R[r], R[p] = R[p], R[r]
            iv = pow(R[r][c], -1, Q)
            R[r] = [(x * iv) % Q for x in R[r]]
            for i in range(len(R)):
                if i != r and R[i][c] % Q:
                    f = R[i][c]
                    R[i] = [(R[i][j] - f * R[r][j]) % Q for j in range(D)]
            r += 1
        return r

    def rk(A):
        return rk_rows([tuple((A[i][j] - (1 if i == j else 0)) % Q
                              for j in range(D)) for i in range(D)])

    def nm(v):
        i = next(k for k, x in enumerate(v) if x % Q)
        z = pow(v[i] % Q, -1, Q)
        return tuple((z * x) % Q for x in v)

    def imgline(A):
        M = [[(A[i][j] - (1 if i == j else 0)) % Q for j in range(D)]
             for i in range(D)]
        cols = [tuple(M[i][j] for i in range(D)) for j in range(D)]
        b = []
        for c in cols:
            if rk_rows(b + [c]) == len(b) + 1:
                b.append(c)
        S = set()
        for co in itertools.product(range(Q), repeat=len(b)):
            if not any(co):
                continue
            w = tuple(sum(co[i] * b[i][k] for i in range(len(b))) % Q
                      for k in range(D))
            if any(w):
                S.add(nm(w))
        return frozenset(S)

    def perp_line(L):
        b = sorted(L)[:2]
        return frozenset(nm(v) for v in vecs
                         if all(form(v, x) % Q == 0 for x in b))

    anom90 = [A for A, L in dist.items() if L == 3 and rk(A) == 2]
    reps, seen = [], set()
    for A in anom90:
        k = frozenset([A, mul(mI, A)])
        if k not in seen:
            seen.add(k)
            reps.append(A)
    n = len(reps)
    LL = [imgline(g) for g in reps]
    PP = [perp_line(x) for x in LL]

    comm = anti = 0
    meet_tab = collections.Counter()
    adj = [[0] * n for _ in range(n)]
    for i, j in itertools.combinations(range(n), 2):
        x, y = mul(reps[i], reps[j]), mul(reps[j], reps[i])
        c, a = x == y, x == mul(mI, y)
        comm += c
        anti += a
        mL = len(LL[i] & LL[j]) > 0
        mP = len(LL[i] & PP[j]) > 0
        meet_tab[(mL, mP)] += 1
        if a:
            adj[i][j] = adj[j][i] = 1
    edges = sum(sum(r) for r in adj) // 2
    degs = collections.Counter(sum(r) for r in adj)

    lam, mu = set(), set()
    for i, j in itertools.combinations(range(n), 2):
        cc = sum(1 for x in range(n) if adj[i][x] and adj[j][x])
        (lam if adj[i][j] else mu).add(cc)
    srg = (n, next(iter(degs)), lam.pop() if len(lam) == 1 else None,
           mu.pop() if len(mu) == 1 else None) if len(degs) == 1 else None

    cliques = []

    def bk(R, P, X):
        if not P and not X:
            cliques.append(frozenset(R))
            return
        for v in list(P):
            bk(R | {v}, {u for u in P if adj[v][u]},
               {u for u in X if adj[v][u]})
            P = P - {v}
            X = X | {v}

    bk(set(), set(range(n)), set())
    sizes = collections.Counter(len(c) for c in cliques)
    lines = [c for c in cliques if len(c) == 5]
    per = collections.Counter(sum(1 for L in lines if i in L) for i in range(n))
    gq = all(sum(1 for x in L if adj[p][x]) == 1
             for L in lines for p in range(n) if p not in L)
    flags = sum(len(L) for L in lines)
    # the plausible-but-wrong alternative
    split = sum(1 for i, j in itertools.combinations(range(n), 2)
                if LL[i] & LL[j] and LL[i] & PP[j])

    print("THE EXPENSIVE INSTRUCTIONS FORM A QUADRANGLE")
    print("=" * 72)
    print("  strictly commuting pairs (gh = hg)      %5d" % comm)
    print("  ANTIcommuting pairs (gh = -hg)          %5d" % anti)
    print("  remaining                               %5d"
          % (n * (n - 1) // 2 - comm - anti))
    print("  -> not one pair of the 45 commutes; the relation is entirely")
    print("     anticommutation, the Pauli incompatibility relation. In PSp")
    print("     the sign vanishes, so these are exactly the projectively")
    print("     commuting pairs.")
    print()
    print("  %d vertices, %d edges, degrees %s" % (n, edges, dict(degs)))
    print("  strongly regular:                    %s" % (srg,))
    print("  maximal cliques: %s" % dict(sizes))
    print("  lines per point: %s" % dict(per))
    print("  flags: %d = %d x 5 = %d x 3" % (flags, len(lines), n))
    print("  GQ axiom: %s" % gq)
    print("  -> GQ(4,2) = H(3,4), the 27 lines RECOVERED as maximal cliques")
    print()
    print("  geometric form of the relation:")
    print("     L meets M only         %4d   not adjacent"
          % meet_tab[(True, False)])
    print("     L meets M^perp only    %4d   not adjacent"
          % meet_tab[(False, True)])
    print("     meets neither          %4d   ADJACENT"
          % meet_tab[(False, False)])
    print("     the plausible alternative (M spanned by a point of L and one")
    print("     of L^perp) accounts for %d of the %d -- tested, not assumed."
          % (split, anti))
    print()
    print("  GQ(4,2) is the DUAL of GQ(2,4), the carrier geometry. Cheap")
    print("  structure and expensive structure are dual quadrangles, and the")
    print("  anomaly is the geometry belonging to the 27 lines.")

    ok = (n == 45 and comm == 0 and anti == 270 and edges == 270
          and srg == (45, 12, 3, 3) and dict(sizes) == {5: 27}
          and dict(per) == {3: 45} and gq and flags == 135 and split == 0
          and meet_tab[(False, False)] == 270 and dia == 5)

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data",
                         "the_expensive_instructions_form_a_quadrangle.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.expensive-instructions-quadrangle.v1",
                "valid": bool(ok),
                "whereThisStarts": ("3a0a194 showed the projective ISA has "
                                    "exactly 45 expensive instructions, one per "
                                    "minimum-weight codeword -- a counting "
                                    "statement. 45 is the tritangent count of a "
                                    "cubic surface, whose partner is 27, so if "
                                    "the cost structure is really Schlafli the "
                                    "45 must carry a GEOMETRY, not merely a "
                                    "cardinality"),
                "theRelation": {
                    "stricltyCommuting": comm,
                    "antiCommuting": anti,
                    "remaining": n * (n - 1) // 2 - comm - anti,
                    "totalPairs": n * (n - 1) // 2,
                    "reading": ("not one pair of the 45 commutes; the relation "
                                "is entirely anticommutation, the Pauli "
                                "incompatibility relation -- the same one making "
                                "mutually incompatible Paulis partial ovoids of "
                                "a symplectic polar space in this corpus. In "
                                "PSp the sign vanishes, so these are exactly "
                                "the projectively commuting pairs, which is why "
                                "the machine sees them as compatible and the "
                                "matrix group does not"),
                },
                "quadrangle": {
                    "points": n, "edges": edges,
                    "degrees": dict(degs),
                    "stronglyRegular": list(srg),
                    "maximalCliqueSizes": {str(k): v
                                           for k, v in sizes.items()},
                    "lines": len(lines),
                    "linesPerPoint": {str(k): v for k, v in per.items()},
                    "flags": flags,
                    "gqAxiom": gq,
                    "isomorphismType": "GQ(4,2) = H(3,4)",
                    "linesRecoveredNotAssumed": ("the 27 lines are the maximal "
                                                 "cliques, found by "
                                                 "Bron-Kerbosch, not an input"),
                },
                "geometricForm": {
                    "rule": "adjacent <=> L n M = empty AND L n M^perp = empty",
                    "meetsMOnly": meet_tab[(True, False)],
                    "meetsPolarOnly": meet_tab[(False, True)],
                    "meetsNeither": meet_tab[(False, False)],
                    "refutedAlternative": ("that M is spanned by a point of L "
                                           "and a point of L^perp accounts for "
                                           "%d of the %d -- tested, not assumed"
                                           % (split, anti)),
                },
                "duality": ("GQ(4,2) is the point-line DUAL of GQ(2,4), the "
                            "carrier geometry (27 points, 45 lines, tau_1 = 10, "
                            "no ovoid). Instructions live on W(3,3), states on "
                            "GQ(2,4), and the cost irregularity on GQ(2,4)'s "
                            "dual: the anomaly is not a defect scattered through "
                            "the instruction set, it is a second geometry, the "
                            "one belonging to the 27 lines"),
                "convergence": ("a149d0b built GQ(4,2) on these same 45 polar "
                                "pairs from the depth-3 blocking obstruction, "
                                "joined by all-isotropic reguli, reporting 45 "
                                "vertices, 270 edges, 12-regular, 27 maximal "
                                "cliques all of size 5, GQ axiom. Identical "
                                "invariants from blocking sets rather than "
                                "Cayley-graph lengths: the same quadrangle "
                                "answers 'which triples fail to block' and "
                                "'which instructions cost extra'"),
                "boundary": ("exhaustive over all 51,840 elements; the 45 are "
                             "3a0a194's anomaly classes, the relation is tested "
                             "on matrices, SRG parameters and the 27 lines are "
                             "computed rather than assumed, and the GQ axiom is "
                             "checked on every point-line pair. GQ(4,2) on 45 "
                             "tritangent planes is classical, as is its duality "
                             "with GQ(2,4); what is computed here is that the "
                             "ISA's anomaly set carries it under "
                             "anticommutation. The match with a149d0b is by "
                             "INVARIANTS only -- that the identity map on polar "
                             "pairs is an isomorphism between the two graphs is "
                             "NOT established here. tau_2 is untouched"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
