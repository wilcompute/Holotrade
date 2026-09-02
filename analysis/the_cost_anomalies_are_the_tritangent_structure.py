#!/usr/bin/env python3
"""
The ISA's cost anomalies and the code's minimum-weight structure are the same
ninety objects.

WHERE THIS STARTS.  6bb8975 found that transvection length equals residue
almost everywhere in Sp(4,3), with exactly 91 exceptions: 90 at (residue 2,
length 3) and one at (residue 4, length 5), the latter being the centre -I.
The centre was identified. The 90 were counted and left unnamed.

90 IS NOT A FREE NUMBER IN THIS CORPUS.  PG(3,3) has 130 lines splitting into
40 isotropic and 90 HYPERBOLIC, and the 90 hyperbolic lines are the thread this
whole architecture runs on: in polarity pairs they give BT810's 45 tritangent
planes, which are the 45 octets L u L^perp, which are the sentinel code's 45
minimum-weight words (4952a3b), which carry GQ(4,2), the 270 isotropic reguli,
and the depth-3 blocking obstruction. So 90 = 90 is either a matching integer
or a bridge, and this repository's rule is to build the map.

THE MAP IS g -> im(g - 1), AND IT IS A BIJECTION.

    residue-2 length-3 anomalies                       90
    of those, involutions                              90  (all)
    whose image is a HYPERBOLIC line                    90  (all)
    distinct image lines                               90
    image set equals the 90 hyperbolic lines exactly  yes

Each anomaly is the involution acting as -1 on its hyperbolic line and fixing
the perpendicular line pointwise, and every hyperbolic line carries exactly one
of them. So the anomaly set decomposes completely:

    91 anomalies  =  90 hyperbolic-line reflections  +  the centre -I.

WHAT THAT MEANS FOR THE ARCHITECTURE.  An operation costs residue-many
transvections -- except when it is a hyperbolic-line reflection, which costs one
extra, and except for the centre, which is free projectively. The expensive
instructions are not scattered. They are indexed by exactly the objects that
carry the error-correcting structure: the same 90 lines whose octets are the
[40,15,8] code's minimum words.

The cost anomaly is CO-LOCATED with the code. That is not something the ISA
work and the code work could have predicted about each other -- they were built
from a Cayley graph and from a weight enumerator respectively -- and it says the
substrate spends its extra instruction exactly where it keeps its minimum
distance.

AND IT EXPLAINS THE ISOTROPIC/HYPERBOLIC SPLIT ONE LEVEL DOWN.  The 40
isotropic lines are where the transvections themselves live -- one per point,
generating everything at residue 1. The 90 hyperbolic lines are where the
reflections live, and those are precisely the residue-2 elements that cannot be
done in two. The 130 lines of PG(3,3) split into the cheap generators and the
expensive anomalies, and nothing else.

SCOPE.  Exhaustive over all 51,840 elements of Sp(4,3): length by full BFS,
residue by rank(g - I), image by column space, hyperbolicity by the form. The
bijection is set equality, not a count match. The onward chain -- hyperbolic
lines to tritangent planes to the sentinel code -- is prior art cited from
BT810 and 4952a3b, not re-derived. No claim is made for other q. tau_2 is
untouched.
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

    def form(u, v):
        return (u[0] * v[2] - u[2] * v[0] + u[1] * v[3] - u[3] * v[1]) % Q

    E = [tuple(1 if k == j else 0 for k in range(D)) for j in range(D)]

    T = set()
    for vv in itertools.product(range(Q), repeat=D):
        if not any(vv):
            continue
        for lam in range(1, Q):
            M = tuple(tuple(((1 if i == j else 0)
                             + lam * form(E[j], vv) * vv[i]) % Q
                            for j in range(D)) for i in range(D))
            if M != I:
                T.add(M)
    T = sorted(T)
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

    def rref_rank(rows):
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

    def image(A):
        M = [[(A[i][j] - (1 if i == j else 0)) % Q for j in range(D)]
             for i in range(D)]
        cols = [tuple(M[i][j] for i in range(D)) for j in range(D)]
        basis = []
        for c in cols:
            if rref_rank(basis + [c]) == len(basis) + 1:
                basis.append(c)
        return basis

    def nm(v):
        i = next(k for k, x in enumerate(v) if x % Q)
        z = pow(v[i] % Q, -1, Q)
        return tuple((z * x) % Q for x in v)

    def span_pts(basis):
        S = set()
        for coef in itertools.product(range(Q), repeat=len(basis)):
            if not any(coef):
                continue
            w = tuple(sum(coef[i] * basis[i][k] for i in range(len(basis))) % Q
                      for k in range(D))
            if any(w):
                S.add(nm(w))
        return frozenset(S)

    pts = sorted({nm(v) for v in itertools.product(range(Q), repeat=D)
                  if any(v)})
    lines = set()
    for a, b in itertools.combinations(pts, 2):
        S = set()
        for x in range(Q):
            for y in range(Q):
                if x == y == 0:
                    continue
                w = tuple((x * a[k] + y * b[k]) % Q for k in range(D))
                if any(w):
                    S.add(nm(w))
        if len(S) == 4:
            lines.add(frozenset(S))
    hyp = {L for L in lines
           if any(form(u, v) % Q
                  for u, v in itertools.combinations(sorted(L), 2))}

    anom = [A for A, L in dist.items()
            if L == 3 and len(image(A)) == 2]
    invol = sum(1 for A in anom if mul(A, A) == I)
    imgs = [span_pts(image(A)) for A in anom]
    inhyp = sum(1 for L in imgs if L in hyp)
    distinct = set(imgs)
    # does each act as -1 on its line and fix the perp pointwise?
    minus_on_line = 0
    for A in anom:
        b = image(A)
        ok = all(tuple(sum(A[i][k] * v[k] for k in range(D)) % Q
                       for i in range(D)) == tuple((-v[k]) % Q
                                                   for k in range(D))
                 for v in b)
        if ok:
            minus_on_line += 1
    centre = [A for A, L in dist.items() if L == 5]

    print("THE COST ANOMALIES ARE THE TRITANGENT STRUCTURE")
    print("=" * 72)
    print("  PG(3,3): %d lines = %d isotropic + %d hyperbolic"
          % (len(lines), len(lines) - len(hyp), len(hyp)))
    print()
    print("  residue-2 length-3 anomalies              %d" % len(anom))
    print("  of those, involutions                     %d" % invol)
    print("  acting as -1 on their own image           %d" % minus_on_line)
    print("  whose image is a HYPERBOLIC line          %d" % inhyp)
    print("  distinct image lines                      %d" % len(distinct))
    print("  image set equals the 90 hyperbolic lines: %s"
          % (distinct == hyp))
    print()
    print("  plus the centre: %d element at length 5" % len(centre))
    print("  => 91 anomalies = 90 hyperbolic-line reflections + -I")
    print()
    print("  Those 90 lines, in polarity pairs, are BT810's 45 tritangent")
    print("  planes = the 45 octets L u L^perp = the sentinel code's 45")
    print("  minimum-weight words (4952a3b), carrying GQ(4,2), the 270")
    print("  isotropic reguli, and the depth-3 obstruction.")
    print()
    print("  So the ISA spends its extra instruction exactly where the code")
    print("  keeps its minimum distance. The 130 lines of PG(3,3) split into")
    print("  the cheap generators (40 isotropic, one transvection each) and")
    print("  the expensive anomalies (90 hyperbolic), and nothing else.")

    ok = (len(anom) == 90 and invol == 90 and inhyp == 90
          and len(distinct) == 90 and distinct == hyp
          and minus_on_line == 90 and len(centre) == 1
          and len(hyp) == 90 and len(lines) == 130)

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data",
                         "the_cost_anomalies_are_the_tritangents.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.cost-anomalies-are-tritangents.v1",
                "valid": bool(ok),
                "whereThisStarts": ("6bb8975 found 91 transvection-length "
                                    "anomalies in Sp(4,3) -- 90 at (residue 2, "
                                    "length 3) and one at (4,5) which is the "
                                    "centre; the centre was identified and the "
                                    "90 were counted and left unnamed"),
                "whyNinetyIsNotFree": ("PG(3,3) has 130 lines splitting 40 "
                                       "isotropic + 90 hyperbolic, and the 90 "
                                       "hyperbolic lines in polarity pairs give "
                                       "BT810's 45 tritangent planes = the 45 "
                                       "octets = the sentinel code's 45 "
                                       "minimum-weight words (4952a3b), "
                                       "carrying GQ(4,2), the 270 isotropic "
                                       "reguli and the depth-3 obstruction"),
                "theMap": {
                    "definition": "g -> im(g - 1)",
                    "anomalies": len(anom),
                    "involutions": invol,
                    "actAsMinusOneOnTheirImage": minus_on_line,
                    "imageIsHyperbolic": inhyp,
                    "distinctImages": len(distinct),
                    "bijectionOntoTheNinety": distinct == hyp,
                },
                "decomposition": {
                    "total": len(anom) + len(centre),
                    "hyperbolicReflections": len(anom),
                    "centre": len(centre),
                    "statement": ("91 anomalies = 90 hyperbolic-line "
                                  "reflections + -I"),
                },
                "pg33Split": {
                    "lines": len(lines),
                    "isotropic": len(lines) - len(hyp),
                    "hyperbolic": len(hyp),
                    "reading": ("the isotropic lines are where the "
                                "transvections live, one per point at residue "
                                "1; the hyperbolic lines are where the "
                                "reflections live, the residue-2 elements that "
                                "cannot be done in two. The 130 split into the "
                                "cheap generators and the expensive anomalies "
                                "and nothing else"),
                },
                "architecturalReading": ("an operation costs residue-many "
                                         "transvections except when it is a "
                                         "hyperbolic-line reflection, which "
                                         "costs one extra, and except for the "
                                         "centre, which is free projectively; "
                                         "the expensive instructions are "
                                         "indexed by exactly the objects "
                                         "carrying the error-correcting "
                                         "structure, so the cost anomaly is "
                                         "CO-LOCATED with the code -- something "
                                         "neither the Cayley-graph work nor the "
                                         "weight-enumerator work could have "
                                         "predicted about the other"),
                "boundary": ("exhaustive over all 51,840 elements of Sp(4,3): "
                             "length by full BFS, residue by rank(g-I), image "
                             "by column space, hyperbolicity by the form; the "
                             "bijection is set equality, not a count match. The "
                             "onward chain from hyperbolic lines to tritangent "
                             "planes to the sentinel code is prior art cited "
                             "from BT810 and 4952a3b, not re-derived. No claim "
                             "for other q. tau_2 is untouched"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
