#!/usr/bin/env python3
"""
Both halves of the parallel track's exterior-square theorem hold at q = 5 and
q = 7 as well as 3. Only the quadrangle is a q = 3 accident.

WHAT WAS BOUNDED.  data/slow_o5_closed_form.json proves that the 45 slow
targets map by c(g) = phat(ker(g-I)) - phat(ker(g+I)) onto exactly the square
nonisotropic orbit of P(W), that the map intertwines every transvection, and
that anticommutation becomes O(5,3) perpendicularity -- with the boundary
"Exact at q=3 for the committed Sp/PSp realization. The exterior-square
construction itself is classical/q-general, but the identification of the cost
orbit with a GQ is q=3-only."

That correctly quarantines the GQ claim, citing 424111b. It leaves the two
substantive halves verified at one prime and described as q-general rather than
shown to be. They are cheap to show.

HALF ONE: THE FORMULA LANDS ON THE SQUARE ORBIT, AT EVERY q TESTED.

    q     hyperbolic lines   distinct images   |square orbit|   exhausts it
    3            90                45               45             yes
    5           650               325              325             yes
    7          2450              1225             1225             yes

Every image lies in W = ker(omega), every one has square Pfaffian, the count
halves exactly (the map identifies a line with its polar, which is the
projectivity under g -> -g), and the images exhaust the orbit rather than
merely landing inside it.

HALF TWO: ANTICOMMUTATION IS PERPENDICULARITY, ON EVERY PAIR.

    q     classes   anticommuting   perpendicular   pairs   agree on all
    3        45          270             270          990       yes
    5       325         9750            9750       52,650       yes
    7      1225      102,900         102,900      749,700       yes

Not merely equal in count: the two relations agree pair by pair, on all
803,340 pairs across the three primes. The correspondence is exact.

SO THE BOUNDARY MOVES, AND SHARPENS.  The exterior-square correspondence -- the
formula, its image, and the anticommutation-perpendicularity dictionary -- is a
FAMILY, holding at every prime tested. The generalized quadrangle is not: the
same graph is SRG(325,60,15,10) at q = 5 and not even strongly regular at q = 7
(424111b). The right statement is that the algebra generalises and the geometry
does not, and the two were previously bounded together at q = 3.

That is the same split this session found on the compiler side: the Weil lift is
q-general (8cdd21f) while the quadrangle is not. Two independent constructions,
the same fault line.

SCOPE.  q = 3, 5, 7 only -- no claim for larger primes, for q even, or for
n > 2. Anomalies are built as reflections (-1 on a nondegenerate line, +1 on its
polar), which 424111b verified are the O'Meara hyperbolic maps at q = 3; at
q = 5 and 7 that identification with the length anomalies is NOT re-verified
here, so what is shown is a theorem about the reflection set, which is what the
formula consumes. Transvection equivariance is the parallel track's check at
q = 3 and is not re-run here. tau_2 is untouched.
"""

import collections
import itertools
import json
import os
import sys

import numpy as np

ROOT = r"C:\Repos\Holotrade"
PAIR = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]


def study(q):
    D = 4

    def mul(A, B):
        return tuple(tuple(sum(A[i][k] * B[k][j] for k in range(D)) % q
                           for j in range(D)) for i in range(D))

    def form(u, v):
        return (u[0] * v[2] - u[2] * v[0] + u[1] * v[3] - u[3] * v[1]) % q

    def nm(v):
        i = next(k for k, x in enumerate(v) if x % q)
        z = pow(v[i] % q, -1, q)
        return tuple((z * x) % q for x in v)

    pts = sorted({nm(v) for v in itertools.product(range(q), repeat=D)
                  if any(v)})

    def rk(rows):
        R = [list(x) for x in rows]
        r = 0
        for c in range(D):
            p = next((i for i in range(r, len(R)) if R[i][c] % q), None)
            if p is None:
                continue
            R[r], R[p] = R[p], R[r]
            iv = pow(R[r][c], -1, q)
            R[r] = [(x * iv) % q for x in R[r]]
            for i in range(len(R)):
                if i != r and R[i][c] % q:
                    f = R[i][c]
                    R[i] = [(R[i][j] - f * R[r][j]) % q for j in range(D)]
            r += 1
        return r

    def wedge(u, v):
        return tuple((u[i] * v[j] - u[j] * v[i]) % q for (i, j) in PAIR)

    def phat(u, v):
        w = wedge(u, v)
        iv = pow(form(u, v) % q, -1, q)
        return tuple((iv * x) % q for x in w)

    def Qf(b):
        return (b[0] * b[5] - b[1] * b[4] + b[2] * b[3]) % q

    def inW(b):
        return (b[1] + b[4]) % q == 0

    def nm6(b):
        i = next(k for k, x in enumerate(b) if x % q)
        z = pow(b[i] % q, -1, q)
        return tuple((z * x) % q for x in b)

    sq = {(x * x) % q for x in range(1, q)}
    P6 = sorted({nm6(b) for b in itertools.product(range(q), repeat=6)
                 if any(b) and inW(b)})
    SQ = {b for b in P6 if Qf(b) % q in sq}

    seen, items, imgs, allW = set(), [], [], True
    for a, b in itertools.combinations(pts, 2):
        if form(a, b) % q == 0:
            continue
        S = set()
        for x in range(q):
            for y in range(q):
                if x == y == 0:
                    continue
                w = tuple((x * a[k] + y * b[k]) % q for k in range(D))
                if any(w):
                    S.add(nm(w))
        S = frozenset(S)
        if S in seen:
            continue
        seen.add(S)
        Pp = [v for v in pts if form(v, a) % q == 0 and form(v, b) % q == 0]
        pb = []
        for v in Pp:
            if rk(pb + [v]) == len(pb) + 1:
                pb.append(v)
        c = tuple((phat(pb[0], pb[1])[k] - phat(a, b)[k]) % q for k in range(6))
        if not inW(c) or not any(c):
            allW = False
        imgs.append(nm6(c))
        B = [list(a), list(b)] + [list(x) for x in pb]
        M = np.array([[B[j][i] for j in range(D)] for i in range(D)],
                     dtype=np.int64) % q
        Aug = np.concatenate([M, np.eye(D, dtype=np.int64)], axis=1)
        r = 0
        for c2 in range(D):
            p = next(i for i in range(r, D) if Aug[i, c2] % q)
            Aug[[r, p]] = Aug[[p, r]]
            Aug[r] = (Aug[r] * pow(int(Aug[r, c2]), -1, q)) % q
            for i in range(D):
                if i != r and Aug[i, c2] % q:
                    Aug[i] = (Aug[i] - Aug[i, c2] * Aug[r]) % q
            r += 1
        Dg = np.diag([q - 1, q - 1, 1, 1]).astype(np.int64)
        g = (M.dot(Dg).dot(Aug[:, D:] % q)) % q
        items.append((tuple(map(tuple, g.tolist())), nm6(c)))

    reps = {}
    for g, c in items:
        key = min(g, tuple(tuple((-x) % q for x in row) for row in g))
        reps[key] = (g, c)
    L = list(reps.values())
    n = len(L)

    def Bf(u, v):
        s = tuple((u[i] + v[i]) % q for i in range(6))
        return (Qf(s) - Qf(u) - Qf(v)) % q

    anti = perp = agree = 0
    tot = n * (n - 1) // 2
    for i, j in itertools.combinations(range(n), 2):
        gi, ci = L[i]
        gj, cj = L[j]
        A = mul(gi, gj) == tuple(tuple((-x) % q for x in row)
                                 for row in mul(gj, gi))
        Pq = Bf(ci, cj) % q == 0
        anti += A
        perp += Pq
        agree += (A == Pq)

    return {"q": q, "hyperbolicLines": len(seen),
            "distinctImages": len(set(imgs)), "squareOrbit": len(SQ),
            "allInW": bool(allW), "exhaustsOrbit": set(imgs) == SQ,
            "classes": n, "anticommuting": anti, "perpendicular": perp,
            "pairs": tot, "agreeOnAllPairs": agree == tot}


def main():
    rows = [study(q) for q in (3, 5, 7)]

    print("THE EXTERIOR-SQUARE THEOREM IS q-GENERAL")
    print("=" * 72)
    print("  slow_o5_closed_form.json bounds both halves at q = 3 and calls")
    print("  the construction 'classical/q-general'. Showing it.")
    print()
    print("  HALF ONE -- the formula lands on the square orbit:")
    print("     q    hyp lines   images   |square orbit|   exhausts")
    for r in rows:
        print("    %2d      %5d    %5d          %5d       %s"
              % (r["q"], r["hyperbolicLines"], r["distinctImages"],
                 r["squareOrbit"], r["exhaustsOrbit"]))
    print("     every image in W: %s" % all(r["allInW"] for r in rows))
    print()
    print("  HALF TWO -- anticommutation IS perpendicularity:")
    print("     q   classes   anticomm   perp      pairs   agree on all")
    for r in rows:
        print("    %2d     %5d     %6d %6d   %8d       %s"
              % (r["q"], r["classes"], r["anticommuting"], r["perpendicular"],
                 r["pairs"], r["agreeOnAllPairs"]))
    print("     not merely equal counts -- they agree PAIR BY PAIR, on all")
    print("     %d pairs across the three primes."
          % sum(r["pairs"] for r in rows))
    print()
    print("  SO THE BOUNDARY MOVES AND SHARPENS. The exterior-square")
    print("  correspondence is a FAMILY. The generalized quadrangle is not:")
    print("  SRG(325,60,15,10) at q=5, not even strongly regular at q=7")
    print("  (424111b). The algebra generalises; the geometry does not.")
    print()
    print("  Same split this session found on the compiler side -- the Weil")
    print("  lift is q-general (8cdd21f) while the quadrangle is not. Two")
    print("  independent constructions, the same fault line.")

    ok = (all(r["exhaustsOrbit"] for r in rows)
          and all(r["allInW"] for r in rows)
          and all(r["agreeOnAllPairs"] for r in rows)
          and all(r["distinctImages"] == r["squareOrbit"] for r in rows)
          and all(r["anticommuting"] == r["perpendicular"] for r in rows))

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "exterior_square_is_q_general.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.exterior-square-q-general.v1",
                "valid": bool(ok),
                "whatWasBounded": ("slow_o5_closed_form.json proves the formula "
                                   "and the anticommutation dictionary at q = 3 "
                                   "and calls the construction "
                                   "'classical/q-general' while correctly "
                                   "quarantining the GQ claim as q = 3 only; the "
                                   "two substantive halves were verified at one "
                                   "prime and described as general rather than "
                                   "shown to be"),
                "citesVerbatim": {
                    "source": "data/slow_o5_closed_form.json (commit d61cdb2)",
                    "theorem": ("The executable 45 slow targets map by an "
                                "explicit basis-independent exterior-square "
                                "formula onto exactly the square nonisotropic "
                                "orbit of P(W). The map intertwines every "
                                "transvection and turns slow-target "
                                "anticommutation into O(5,3) perpendicularity. "
                                "No graph-isomorphism search is required."),
                    "boundary": ("Exact at q=3 for the committed Sp/PSp "
                                 "realization. The exterior-square construction "
                                 "itself is classical/q-general, but the "
                                 "identification of the cost orbit with a GQ is "
                                 "q=3-only and no q-general GQ claim is made."),
                    "formula": ("c(g)=phat(ker(g-I))-phat(ker(g+I)), "
                                "phat(span(a,b))=(a wedge b)/<a,b>"),
                    "Q": "b_01 b_23 - b_02 b_13 + b_03 b_12",
                    "omegaCoordinateLaw": "b_02+b_13=0",
                    "theirCheckThisReproduces":
                        "anticommutation_equals_O5_perpendicularity_all_990_pairs",
                    "conventionsAreTheirs": ("Q and the omega law here are their "
                                             "expressions verbatim, and their 990 "
                                             "is exactly the q = 3 row below, so "
                                             "this is an independent reproduction "
                                             "before it is an extension"),
                },
                "rows": rows,
                "halfOne": ("the formula c(g) = phat(ker(g-I)) - phat(ker(g+I)) "
                            "sends every reflection into W, the image count "
                            "halves exactly (a line and its polar share an "
                            "image, which is the projectivity under g -> -g), "
                            "and the images EXHAUST the square nonisotropic "
                            "orbit rather than merely landing inside it, at "
                            "q = 3, 5 and 7"),
                "halfTwo": ("anticommutation and O(5,q) perpendicularity agree "
                            "PAIR BY PAIR -- not merely in count -- on all %d "
                            "pairs across the three primes"
                            % sum(r["pairs"] for r in rows)),
                "theBoundaryMoves": ("the exterior-square correspondence is a "
                                     "FAMILY, holding at every prime tested; the "
                                     "generalized quadrangle is not, being "
                                     "SRG(325,60,15,10) at q = 5 and not even "
                                     "strongly regular at q = 7 (424111b). The "
                                     "algebra generalises and the geometry does "
                                     "not, and the two were previously bounded "
                                     "together at q = 3"),
                "sameFaultLineAsTheCompiler": ("the Weil lift is q-general "
                                               "(8cdd21f) while the quadrangle "
                                               "is not; two independent "
                                               "constructions, the same split"),
                "boundary": ("q = 3, 5, 7 only -- no claim for larger primes, "
                             "for q even, or for n > 2. Anomalies are built as "
                             "reflections (-1 on a nondegenerate line, +1 on its "
                             "polar), which 424111b verified are the O'Meara "
                             "hyperbolic maps at q = 3; at q = 5 and 7 that "
                             "identification with the LENGTH anomalies is NOT "
                             "re-verified here, so what is shown is a theorem "
                             "about the reflection set, which is what the "
                             "formula consumes. Transvection equivariance is the "
                             "parallel track's check at q = 3 and is not re-run "
                             "here. tau_2 is untouched"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
