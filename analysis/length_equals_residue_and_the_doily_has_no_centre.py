#!/usr/bin/env python3
"""
The latency law is really "length = residue", and the doily is the exception
for a mechanical reason: at q = 2 there is no centre to divide out.

WHAT 860714a LEFT UNEXPLAINED.  The transvection Cayley diameter is 2n in six
of seven symplectic groups and 2n + 1 at Sp(4,2). That was measured, and the
self-duality of W(3,2) was offered as the structural company it keeps, but no
mechanism was given. There is one, and it also sharpens the law.

LENGTH VERSUS RESIDUE.  A transvection has residue dim im(g - 1) = 1, so the
transvection length of any g is at least its residue, and the literature ties
the two closely. Computing both for every element, on MATRICES so that residue
is defined at all:

    Sp(4,2), order 720          Sp(4,3), order 51,840
    (res, len) -> count         (res, len) -> count
    (0,0) ->    1               (0,0) ->      1
    (1,1) ->   15               (1,1) ->     80
    (2,2) ->   85               (2,2) ->   1980
    (2,3) ->   15  <- anomaly   (2,3) ->     90  <- anomaly
    (3,3) ->  210               (3,3) ->  16560
    (3,4) ->   90  <- anomaly   (4,4) ->  33128
    (4,4) ->  184               (4,5) ->      1  <- anomaly
    (4,5) ->  120  <- anomaly

So length = residue almost everywhere, with an anomaly set where it is residue
plus one. The anomaly DENSITIES are the whole story:

    Sp(4,2)   225 / 720     = 31.2 %
    Sp(4,3)    91 / 51,840  =  0.18 %        a factor of 178

THE SINGLE WORST ELEMENT OF Sp(4,3) IS -I.  There is exactly one element at
length 5, and it is the centre:

    -I = diag(2,2,2,2) over F3,  residue 4, length 5.

That is the entire gap between the matrix group and the projective one. Sp(4,3)
has matrix diameter 5; -I is central, so it vanishes in PSp(4,3), and the
projective diameter drops to 4 = 2n. The law is a PROJECTIVE law, and it holds
because the one element that breaks it is the one element projectivisation
removes.

AND THAT IS WHY THE DOILY IS DIFFERENT.  At q = 2, -I = I. There is no centre
to divide out, PSp(4,2) = Sp(4,2), and an anomaly set of 31 % cannot be quotiented
away by anything. The exception is not that the doily has a longer worst case
by accident; it is that every other case in the sweep is rescued by its centre
and the doily has none.

    q odd    a small anomaly set, its extreme point is central,
             projectivisation removes it, diameter = 2n
    q = 2    no centre, a 178x denser anomaly set survives,
             diameter = 2n + 1

A CORRECTION TO MY OWN FRAMING.  860714a reported the sweep on the projective
action without saying so, which left "the latency law is 2n" ambiguous between
the matrix and projective groups. On matrices Sp(4,3) is also 5. The law is
about PSp, which is the architecturally right group -- machine states are
projective points -- but the qualifier belongs in the statement.

SCOPE.  Exact and exhaustive: every element of both groups, with residue by
rank(g - I) over the field and length by full BFS. The identification of the
single Sp(4,3) length-5 element as -I is checked by direct comparison. The
claim that q odd always rescues itself this way is NOT established -- it is
verified at q = 3 and consistent with the sweep in 860714a. tau_2 is untouched.
"""

import collections
import itertools
import json
import os
import sys

ROOT = r"C:\Repos\Holotrade"


def study(n, q):
    d = 2 * n

    def mul(A, B):
        return tuple(tuple(sum(A[i][k] * B[k][j] for k in range(d)) % q
                           for j in range(d)) for i in range(d))

    I = tuple(tuple(1 if i == j else 0 for j in range(d)) for i in range(d))

    def form(u, v):
        s = 0
        for i in range(n):
            s += u[i] * v[n + i] - u[n + i] * v[i]
        return s % q

    T = set()
    for vv in itertools.product(range(q), repeat=d):
        if not any(vv):
            continue
        for lam in range(1, q):
            M = tuple(tuple(((1 if i == j else 0)
                             + lam * form(tuple(1 if k == j else 0
                                                for k in range(d)), vv)
                             * vv[i]) % q for j in range(d))
                      for i in range(d))
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

    def rank(A):
        M = [[(A[i][j] - (1 if i == j else 0)) % q for j in range(d)]
             for i in range(d)]
        r = 0
        for c in range(d):
            p = next((i for i in range(r, d) if M[i][c] % q), None)
            if p is None:
                continue
            M[r], M[p] = M[p], M[r]
            iv = pow(M[r][c], -1, q)
            M[r] = [(x * iv) % q for x in M[r]]
            for i in range(d):
                if i != r and M[i][c] % q:
                    f = M[i][c]
                    M[i] = [(M[i][j] - f * M[r][j]) % q for j in range(d)]
            r += 1
        return r

    tab = collections.Counter()
    for A, L in dist.items():
        tab[(rank(A), L)] += 1
    anom = sum(v for k, v in tab.items() if k[1] > k[0])
    far = [A for A, L in dist.items() if L == dia]
    minusI = tuple(tuple((-1 if i == j else 0) % q for j in range(d))
                   for i in range(d))
    return {"n": n, "q": q, "order": len(dist), "transvections": len(T),
            "matrixDiameter": dia,
            "table": {"%d,%d" % k: v for k, v in sorted(tab.items())},
            "anomalies": anom,
            "anomalyPercent": round(100.0 * anom / len(dist), 3),
            "extremeCount": len(far),
            "extremeIsMinusI": len(far) == 1 and far[0] == minusI,
            "hasCentre": minusI != I}


def main():
    a = study(2, 2)
    b = study(2, 3)
    print("LENGTH EQUALS RESIDUE, AND THE DOILY HAS NO CENTRE")
    print("=" * 72)
    for r in (a, b):
        print("  Sp(4,%d): order %d, %d transvections, matrix diameter %d"
              % (r["q"], r["order"], r["transvections"], r["matrixDiameter"]))
        for k in sorted(r["table"], key=lambda s: tuple(map(int, s.split(",")))):
            res, ln = map(int, k.split(","))
            print("     (res %d, len %d) : %6d%s"
                  % (res, ln, r["table"][k],
                     "   <- anomaly" if ln > res else ""))
        print("     anomalies %d / %d = %s%%"
              % (r["anomalies"], r["order"], r["anomalyPercent"]))
        print()
    print("  anomaly density ratio: %.0fx"
          % (a["anomalyPercent"] / b["anomalyPercent"]))
    print()
    print("  Sp(4,3) has exactly %d element at the extreme, and it IS -I: %s"
          % (b["extremeCount"], b["extremeIsMinusI"]))
    print("  -I is central, so it vanishes in PSp(4,3) and the projective")
    print("  diameter drops to 4 = 2n. The law is a PROJECTIVE law, and it")
    print("  holds because the element that breaks it is the one element")
    print("  projectivisation removes.")
    print()
    print("  At q = 2, -I = I: there is no centre (%s), PSp(4,2) = Sp(4,2),"
          % a["hasCentre"])
    print("  and a %s%% anomaly set cannot be quotiented away by anything."
          % a["anomalyPercent"])
    print("  Every other case in the sweep is rescued by its centre. The doily")
    print("  has none. That is the mechanism 860714a was missing.")

    ok = (a["matrixDiameter"] == 5 and b["matrixDiameter"] == 5
          and b["extremeCount"] == 1 and b["extremeIsMinusI"]
          and not a["hasCentre"] and b["hasCentre"]
          and a["anomalyPercent"] > 30 and b["anomalyPercent"] < 1)

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "length_equals_residue.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.length-equals-residue-doily.v1",
                "valid": bool(ok),
                "whatWasUnexplained": ("860714a measured the transvection "
                                       "diameter as 2n in six of seven cases "
                                       "and 2n+1 at Sp(4,2), offering the "
                                       "self-duality of W(3,2) as company but "
                                       "no mechanism"),
                "lengthVersusResidue": ("a transvection has residue 1, so "
                                        "length >= residue always; computing "
                                        "both on matrices, length = residue "
                                        "almost everywhere with an anomaly set "
                                        "at residue + 1"),
                "cases": [a, b],
                "anomalyDensityRatio": round(a["anomalyPercent"]
                                             / b["anomalyPercent"], 1),
                "theMechanism": {
                    "qOdd": ("a small anomaly set whose extreme point is "
                             "central, removed by projectivisation, leaving "
                             "diameter 2n"),
                    "qTwo": ("-I = I so there is no centre, PSp(4,2) = Sp(4,2), "
                             "and a 178x denser anomaly set survives, leaving "
                             "diameter 2n + 1"),
                    "sp43Extreme": ("exactly one element at length 5 and it is "
                                    "-I = diag(2,2,2,2), residue 4"),
                    "reading": ("the doily is not accidentally worse; every "
                                "other case is rescued by its centre and the "
                                "doily has none"),
                },
                "correctionToMyFraming": ("860714a reported the sweep on the "
                                          "projective action without saying so, "
                                          "leaving 'the latency law is 2n' "
                                          "ambiguous between the matrix and "
                                          "projective groups; on matrices "
                                          "Sp(4,3) is also 5. The law is about "
                                          "PSp, which is the architecturally "
                                          "right group since machine states are "
                                          "projective points, but the qualifier "
                                          "belongs in the statement"),
                "boundary": ("exact and exhaustive over every element of both "
                             "groups, residue by rank(g - I) and length by full "
                             "BFS; the identification of the single Sp(4,3) "
                             "extreme element as -I is by direct comparison. "
                             "The claim that odd q always rescues itself this "
                             "way is NOT established -- verified at q = 3 and "
                             "consistent with the earlier sweep. tau_2 is "
                             "untouched"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
