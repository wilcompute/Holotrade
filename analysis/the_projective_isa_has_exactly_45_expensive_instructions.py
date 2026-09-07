#!/usr/bin/env python3
"""
In the group the architecture actually runs on, the cost anomaly is a perfect
bijection: 45 expensive instructions, 45 minimum-weight codewords, and nothing
else in 25,920 costs more than its residue.

WHY THE GROUP WAS WRONG.  Every cost result so far -- b363f7c, 6bb8975,
3595bd1, e05515f -- was computed in Sp(4,3), and the picture there is 91
anomalies decomposing awkwardly as 90 + 1. But 6bb8975 already established that
the architecturally right group is PSp(4,3): machine states are PROJECTIVE
points, -I acts trivially on them, and the latency law 2n is a projective law.
Nobody then recomputed the cost model there. Doing so collapses the whole
picture.

THE CENTRE IS NOT A SECOND ANOMALY -- IT IS THE POLARITY.  Take the 90
residue-2 anomalies, the reflections that are -1 on a hyperbolic line L and +1
on L^perp. Then:

    -g is also an anomaly, for all 90                        yes
    im(-g - 1) is exactly the POLAR line of im(g - 1)      90 of 90
    classes under g ~ -g                                        45

So multiplying by the centre does not produce a new element of a different kind;
it carries the reflection of L to the reflection of L^perp. On the anomaly set,
-I ACTS AS THE SYMPLECTIC POLARITY. That is why 91 looked like 90 + 1: the +1
was the operator doing the pairing, counted as though it were one of the paired
things.

AND IN PSp THE ANSWER IS EXACTLY 45.

    PSp(4,3): 25,920 elements, 80 opcodes, projective diameter 4

    (projective residue, projective length) -> count
        (0,0)      1
        (1,1)     80
        (2,2)   1980
        (2,3)     45   <- the ONLY anomalies
        (3,3)  12960
        (4,4)  10854

    projective anomalies: 45 of 25,920 = 0.174%

The (4,5) cell is gone -- that was -I, which is the identity here. Every one of
the 45 is anomalous, and they are ALL of the anomalies. There is no residual
mess.

THE BIJECTION.  Those 45 classes are the 45 polar pairs of hyperbolic lines,
which are BT810's 45 tritangent planes, which are the 45 octets L u L^perp,
which are the sentinel code's 45 minimum-weight words (4952a3b). So:

    the projective ISA has exactly one expensive instruction
    per minimum-weight codeword, and no other expensive instruction.

3f93821 guessed at this as "co-location" and had to hedge, because in Sp the
count was 90 against 45 objects, two-to-one, plus an unexplained centre. In PSp
it is one-to-one with nothing left over. The hedge was an artefact of computing
in the wrong group.

WHAT IT MEANS FOR THE MACHINE.  Compiling a gate costs its residue in
transvections -- except for 45 instructions out of 25,920, each of which costs
one extra, and each of which is the reflection in one minimum-weight codeword of
the code the machine uses to protect itself. The error-correcting structure and
the instruction-cost irregularity are not merely correlated; in the projective
group they are the same 45 objects, indexed the same way.

SCOPE.  Exhaustive: all 51,840 matrices reduced onto the 25,920 projective
elements via the action on the 40 points, projective length by full BFS over
that action, projective residue as min(res(g), res(-g)) over the two lifts --
residue is not projectively defined, and that minimum is the choice made here,
stated because a different convention would move the table. The onward chain
from polar pairs to tritangent planes to the code's minimum words is cited prior
art (BT810, 4952a3b), not re-derived. The underlying length law is O'Meara's,
per 3595bd1. tau_2 is untouched.
"""

import collections
import itertools
import json
import os
import sys

ROOT = r"C:\Repos\Holotrade"
Q = 3
D = 4
NP = 40


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

    # (1) the centre acts as the polarity on the anomaly set
    anom90 = [A for A, L in dist.items() if L == 3 and rk(A) == 2]
    closed = all(mul(mI, A) in anom90 for A in anom90)
    polar_ok = sum(1 for A in anom90
                   if imgline(mul(mI, A)) == perp_line(imgline(A)))
    classes = {frozenset([A, mul(mI, A)]) for A in anom90}

    # (2) the projective cost model
    pts = sorted({nm(v) for v in vecs})
    idx = {v: i for i, v in enumerate(pts)}

    def perm(A):
        return tuple(idx[nm(act(A, pts[p]))] for p in range(NP))

    ident = tuple(range(NP))
    Pgens = sorted({perm(M) for M in T})
    pd, fr, pdia = {ident: 0}, [ident], 0
    while fr:
        nx = []
        for a in fr:
            for g in Pgens:
                c = tuple(a[g[i]] for i in range(NP))
                if c not in pd:
                    pd[c] = pdia + 1
                    nx.append(c)
        fr = nx
        if nx:
            pdia += 1

    tab = collections.Counter()
    seen = {}
    for A in dist:
        p = perm(A)
        if p in seen:
            continue
        seen[p] = (min(rk(A), rk(mul(mI, A))), pd[p])
        tab[seen[p]] += 1
    panom = sum(v for k, v in tab.items() if k[1] > k[0])
    ref = {perm(A) for A in anom90}
    all_ref_anom = all(seen[p][1] > seen[p][0] for p in ref)
    anom_set = {p for p in seen if seen[p][1] > seen[p][0]}

    print("THE PROJECTIVE ISA HAS EXACTLY 45 EXPENSIVE INSTRUCTIONS")
    print("=" * 72)
    print("  the centre is not a second anomaly -- it is the POLARITY:")
    print("     -g is also an anomaly, for all 90:            %s" % closed)
    print("     im(-g-1) is the POLAR line of im(g-1):     %d of %d"
          % (polar_ok, len(anom90)))
    print("     classes under g ~ -g:                         %d" % len(classes))
    print()
    print("  PSp(4,3): %d elements, %d opcodes, projective diameter %d"
          % (len(pd), len(Pgens), pdia))
    print("     (projective residue, projective length) -> count")
    for k in sorted(tab):
        print("        %s : %6d%s"
              % (k, tab[k], "   <- the ONLY anomalies" if k[1] > k[0] else ""))
    print("     projective anomalies: %d of %d = %.3f%%"
          % (panom, len(pd), 100.0 * panom / len(pd)))
    print()
    print("     the 90 reflections give %d distinct PSp elements" % len(ref))
    print("     all of them anomalous:                        %s" % all_ref_anom)
    print("     and they are ALL the anomalies:               %s"
          % (ref == anom_set))
    print()
    print("  Those 45 classes are the 45 polar pairs = BT810's 45 tritangent")
    print("  planes = the 45 octets = the sentinel code's 45 minimum-weight")
    print("  words. So the projective ISA has exactly ONE expensive")
    print("  instruction per minimum-weight codeword, and no other.")
    print()
    print("  3f93821 hedged this as 'co-location' because in Sp the count was")
    print("  90 against 45 objects, two-to-one, plus an unexplained centre.")
    print("  The hedge was an artefact of computing in the wrong group.")

    ok = (closed and polar_ok == 90 and len(anom90) == 90
          and len(classes) == 45 and len(pd) == 25920 and len(Pgens) == 80
          and pdia == 4 and panom == 45 and len(ref) == 45
          and all_ref_anom and ref == anom_set
          and tab[(2, 3)] == 45 and dia == 5)

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "the_projective_isa_45.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.projective-isa-45-expensive.v1",
                "valid": bool(ok),
                "whyTheGroupWasWrong": ("every cost result so far -- b363f7c, "
                                        "6bb8975, 3595bd1, e05515f -- was "
                                        "computed in Sp(4,3), where the picture "
                                        "is 91 anomalies decomposing awkwardly "
                                        "as 90 + 1; but 6bb8975 already "
                                        "established that PSp(4,3) is the "
                                        "architecturally right group, since "
                                        "machine states are projective points "
                                        "and -I acts trivially on them, and "
                                        "nobody recomputed the cost model there"),
                "centreIsThePolarity": {
                    "anomalySetClosedUnderNegation": closed,
                    "imageOfNegatedIsPolarLine": polar_ok,
                    "outOf": len(anom90),
                    "classes": len(classes),
                    "reading": ("multiplying by the centre carries the "
                                "reflection of L to the reflection of L^perp, "
                                "so on the anomaly set -I ACTS AS THE "
                                "SYMPLECTIC POLARITY; 91 looked like 90 + 1 "
                                "only because the operator doing the pairing "
                                "was counted as one of the paired things"),
                },
                "projectiveCostModel": {
                    "order": len(pd),
                    "opcodes": len(Pgens),
                    "diameter": pdia,
                    "matrixDiameter": dia,
                    "table": {"%d,%d" % k: v for k, v in sorted(tab.items())},
                    "anomalies": panom,
                    "anomalyPercent": round(100.0 * panom / len(pd), 3),
                    "residueConvention": ("residue is NOT projectively defined; "
                                          "min(res(g), res(-g)) over the two "
                                          "lifts is the choice made here, and a "
                                          "different convention would move the "
                                          "table"),
                },
                "theBijection": {
                    "expensiveInstructions": panom,
                    "minimumWeightCodewords": 45,
                    "reflectionsAreAllAnomalies": bool(ref == anom_set),
                    "statement": ("the projective ISA has exactly one expensive "
                                  "instruction per minimum-weight codeword, and "
                                  "no other expensive instruction"),
                    "chain": ("45 polar pairs of hyperbolic lines = BT810's 45 "
                              "tritangent planes = the 45 octets L u L^perp = "
                              "the sentinel code's 45 minimum-weight words "
                              "(4952a3b) -- cited prior art, not re-derived"),
                },
                "supersedesTheHedge": ("3f93821 called this 'co-location' and "
                                       "had to hedge because in Sp the count was "
                                       "90 against 45 objects, two-to-one, plus "
                                       "an unexplained centre; in PSp it is "
                                       "one-to-one with nothing left over, so "
                                       "the hedge was an artefact of computing "
                                       "in the wrong group"),
                "readingForTheMachine": ("compiling a gate costs its residue in "
                                         "transvections except for 45 "
                                         "instructions out of 25,920, each "
                                         "costing one extra, and each being the "
                                         "reflection in one minimum-weight "
                                         "codeword of the code the machine uses "
                                         "to protect itself; the "
                                         "error-correcting structure and the "
                                         "instruction-cost irregularity are the "
                                         "same 45 objects, indexed the same way"),
                "boundary": ("exhaustive: all 51,840 matrices reduced onto the "
                             "25,920 projective elements via the action on the "
                             "40 points, projective length by full BFS over that "
                             "action, projective residue as min over the two "
                             "lifts. The chain from polar pairs to tritangent "
                             "planes to minimum words is cited prior art "
                             "(BT810, 4952a3b). The underlying length law is "
                             "O'Meara's per 3595bd1. tau_2 is untouched"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
