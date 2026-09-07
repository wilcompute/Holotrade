#!/usr/bin/env python3
"""
The cost geometry is a generalized quadrangle only at q = 3. At q = 5 it is
strongly regular but not a quadrangle; at q = 7 it is not even strongly
regular. Everything built on it is a q = 3 phenomenon.

WHY THIS HAD TO BE ASKED.  605f5e5 through 48e1841 built a long chain on one
object: the anticommuting graph on the cost anomalies of PSp(4,3) is GQ(4,2),
carrying the Schlafli configuration, 27 extraspecial 2-groups, 200 ovoids, and a
tower-law base. Every one of those results is at q = 3. This repository's own
rule is that a law with no exceptions on a single sample is not a finding until
the sample is varied, and the variable here is obvious.

THE CONSTRUCTION IS q-GENERAL.  The anomalies are the reflections that act as -1
on a nondegenerate line L and +1 on L^perp -- one per hyperbolic line of
PG(3,q), paired by g ~ -g because -r_L = r_{L^perp}. That is defined for every
odd q, and every reflection built this way is verified O'Meara-hyperbolic. So
the object exists at every odd q and the only question is its shape.

    q    points   hyperbolic lines   reflection classes   degree
    3      40            90                  45             12
    5     156           650                 325             60
    7     400          2450                1225            168

Both counts are exact closed forms across the three: classes = q^2 (q^2 + 1) / 2
and degree = q (q^2 - 1) / 2. The graph is REGULAR at every q tested.

BUT REGULARITY IS ALL THAT SURVIVES.

    q = 3    SRG(45, 12, 3, 3)          and it IS GQ(4,2)
    q = 5    SRG(325, 60, 15, 10)       strongly regular, NOT a quadrangle
    q = 7    168-regular                NOT strongly regular at all

A two-step degradation, not one. At q = 5 the graph is still strongly regular --
so the object does not simply fall apart -- but its parameters fail the GQ
identity: reading s = lambda + 1 = 16 and t = mu - 1 = 9 gives
(s+1)(st+1) = 17 x 145, nowhere near 325. At q = 7 even the strong regularity
goes: lambda and mu are no longer constant.

SO EVERY DOWNSTREAM RESULT IS q = 3 ONLY.  The Schlafli configuration
(fe4fb77, f624d8f), the 27 extraspecial 2^{1+4}_- groups (34f2a84), the 200
ovoids and the dual defect against W(3,3) (8982d36), tau_1 = 9 and the new tower
base (48e1841) -- all of them rest on the graph being GQ(4,2), and it is that
only at q = 3. None of them should be quoted with a "for odd q" attached.

A SECOND, INDEPENDENT ARRIVAL AT THE SAME SPECIALNESS.  The corpus already knows
the quadrangle is a q = 3 coincidence, from a completely different direction:
data/the_quadrangle_is_the_q_equals_three_coincidence.json shows each
all-isotropic regulus names (q+1)/2 polar pairs, which is 2 -- an EDGE -- only at
q = 3, and records isAGraph false from q = 5 on. That is the combinatorial
route, through reguli and blocking. This is the algebraic route, through
anticommutation and word length, and it lands on the same verdict. What it adds
is the shape of the failure: the prior file says the regulus construction stops
being a graph, while this says the anticommuting graph survives as a graph at
every q, is strongly regular at q = 5, and only loses that at q = 7.

SCOPE.  Exact at q = 3, 5, 7: hyperbolic lines enumerated completely, every
reflection checked to be O'Meara-hyperbolic, adjacency computed from the
matrices rather than from a geometric shortcut, and lambda/mu taken over ALL
pairs. The closed forms for the vertex count and degree are read off three data
points and are NOT proved here. No q > 7 is tested, so "not strongly regular for
all q >= 7" is not established -- only that q = 7 is not. tau_2 is untouched.
"""

import collections
import itertools
import json
import os
import sys

import numpy as np

ROOT = r"C:\Repos\Holotrade"


def build(q):
    D = 4

    def form(u, v):
        return (u[0] * v[2] - u[2] * v[0] + u[1] * v[3] - u[3] * v[1]) % q

    def nm(v):
        i = next(k for k, x in enumerate(v) if x % q)
        z = pow(v[i] % q, -1, q)
        return tuple((z * x) % q for x in v)

    pts = sorted({nm(v) for v in itertools.product(range(q), repeat=D)
                  if any(v)})

    def rk_rows(rows):
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

    seen, refl = set(), []
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
        P = [v for v in pts if form(v, a) % q == 0 and form(v, b) % q == 0]
        pb = []
        for v in P:
            if rk_rows(pb + [v]) == len(pb) + 1:
                pb.append(v)
        B = [list(a), list(b)] + [list(x) for x in pb]
        Mb = np.array([[B[j][i] for j in range(D)] for i in range(D)],
                      dtype=np.int64) % q
        Aug = np.concatenate([Mb, np.eye(D, dtype=np.int64)], axis=1)
        r = 0
        for c in range(D):
            p = next(i for i in range(r, D) if Aug[i, c] % q)
            Aug[[r, p]] = Aug[[p, r]]
            Aug[r] = (Aug[r] * pow(int(Aug[r, c]), -1, q)) % q
            for i in range(D):
                if i != r and Aug[i, c] % q:
                    Aug[i] = (Aug[i] - Aug[i, c] * Aug[r]) % q
            r += 1
        Minv = Aug[:, D:] % q
        Dg = np.diag([q - 1, q - 1, 1, 1]).astype(np.int64)
        refl.append((Mb.dot(Dg).dot(Minv)) % q)

    # every reflection must be O'Meara-hyperbolic
    V = np.array([list(v) for v in itertools.product(range(q), repeat=D)
                  if any(v)], dtype=np.int64)
    J = np.array([[0, 0, 1, 0], [0, 0, 0, 1], [-1, 0, 0, 0], [0, -1, 0, 0]],
                 dtype=np.int64)
    allhyp = True
    for Mm in refl:
        W = (V.dot(Mm.T)) % q
        if np.any((np.einsum('ij,jk,ik->i', V, J, W)) % q):
            allhyp = False
            break
    return pts, seen, refl, allhyp


def analyse(q):
    pts, hyp, refl, allhyp = build(q)
    keys = {}
    for Mm in refl:
        a = tuple(Mm.flatten())
        b = tuple(((-Mm) % q).flatten())
        keys[min(a, b)] = True
    C = np.array([np.array(k, dtype=np.int64).reshape(4, 4)
                  for k in sorted(keys)])
    n = len(C)
    GH = np.einsum('aij,bjk->abik', C, C) % q
    HG = np.transpose(GH, (1, 0, 2, 3))
    A = np.all(GH == ((-HG) % q), axis=(2, 3)).astype(np.int64)
    np.fill_diagonal(A, 0)
    degs = sorted(set(A.sum(axis=1).tolist()))
    A2 = A.dot(A)
    off = ~np.eye(n, dtype=bool)
    lam = sorted(set(A2[A == 1].tolist()))
    mu = sorted(set(A2[(A == 0) & off].tolist()))
    srg = None
    if len(degs) == 1 and len(lam) == 1 and len(mu) == 1:
        srg = [n, degs[0], lam[0], mu[0]]
    isgq = False
    if srg:
        N, k, l, m = srg
        s, t = l + 1, m - 1
        isgq = (N == (s + 1) * (s * t + 1) and k == s * (t + 1))
    return {"q": q, "points": len(pts), "hyperbolicLines": len(hyp),
            "classes": n, "degrees": degs,
            "everyReflectionIsHyperbolic": bool(allhyp),
            "lambdaValues": lam, "muValues": mu,
            "stronglyRegular": srg, "isGQ": bool(isgq),
            "classesClosedForm": q * q * (q * q + 1) // 2,
            "degreeClosedForm": q * (q * q - 1) // 2}


def main():
    rows = [analyse(q) for q in (3, 5, 7)]

    print("THE COST QUADRANGLE IS q = 3 ONLY")
    print("=" * 72)
    print("  the construction is q-general: reflections -1 on a nondegenerate")
    print("  line, +1 on its polar, one per hyperbolic line of PG(3,q),")
    print("  paired by g ~ -g. All verified O'Meara-hyperbolic.")
    print()
    print("   q   points   hyp lines   classes   degree   closed forms match")
    for r in rows:
        print("  %2d    %4d       %5d     %5d    %5d      %s / %s"
              % (r["q"], r["points"], r["hyperbolicLines"], r["classes"],
                 r["degrees"][0],
                 r["classes"] == r["classesClosedForm"],
                 r["degrees"][0] == r["degreeClosedForm"]))
    print("  classes = q^2(q^2+1)/2 ; degree = q(q^2-1)/2 ; REGULAR at every q")
    print()
    for r in rows:
        if r["stronglyRegular"]:
            print("  q = %d   SRG%s   %s"
                  % (r["q"], tuple(r["stronglyRegular"]),
                     "and it IS GQ(4,2)" if r["isGQ"]
                     else "strongly regular, NOT a quadrangle"))
        else:
            print("  q = %d   %d-regular, NOT strongly regular"
                  % (r["q"], r["degrees"][0]))
            print("          lambda takes %d values %s"
                  % (len(r["lambdaValues"]), r["lambdaValues"][:6]))
            print("          mu     takes %d values %s"
                  % (len(r["muValues"]), r["muValues"][:6]))
    print()
    print("  A TWO-STEP degradation: quadrangle -> merely strongly regular ->")
    print("  not even that. So every downstream result -- the Schlafli triple,")
    print("  the 27 extraspecial 2-groups, the 200 ovoids and the dual defect,")
    print("  tau_1 = 9 and the new tower base -- is q = 3 ONLY, and none of")
    print("  them should be quoted with a 'for odd q' attached.")
    print()
    print("  SECOND ARRIVAL: the corpus already knows the quadrangle is a q = 3")
    print("  coincidence, from the REGULUS side -- each all-isotropic regulus")
    print("  names (q+1)/2 polar pairs, an EDGE only at q = 3. That is the")
    print("  combinatorial route; this is the algebraic one, and it adds the")
    print("  SHAPE of the failure the prior file does not record.")

    ok = (rows[0]["isGQ"] and rows[0]["stronglyRegular"] == [45, 12, 3, 3]
          and rows[1]["stronglyRegular"] == [325, 60, 15, 10]
          and not rows[1]["isGQ"] and rows[2]["stronglyRegular"] is None
          and all(len(r["degrees"]) == 1 for r in rows)
          and all(r["classes"] == r["classesClosedForm"] for r in rows)
          and all(r["degrees"][0] == r["degreeClosedForm"] for r in rows)
          and all(r["everyReflectionIsHyperbolic"] for r in rows))

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "cost_quadrangle_is_q3_only.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.cost-quadrangle-q3-only.v1",
                "valid": bool(ok),
                "whyAsked": ("605f5e5 through 48e1841 built a long chain on one "
                             "object at q = 3; this repository's rule is that a "
                             "law with no exceptions on a single sample is not a "
                             "finding until the sample is varied"),
                "constructionIsQGeneral": ("the anomalies are the reflections -1 "
                                           "on a nondegenerate line L and +1 on "
                                           "L^perp, one per hyperbolic line of "
                                           "PG(3,q), paired by g ~ -g because "
                                           "-r_L = r_{L^perp}; defined for every "
                                           "odd q, and every reflection built "
                                           "this way is verified "
                                           "O'Meara-hyperbolic"),
                "rows": rows,
                "closedForms": {
                    "classes": "q^2 (q^2 + 1) / 2",
                    "degree": "q (q^2 - 1) / 2",
                    "note": ("read off three data points, NOT proved here; the "
                             "graph is REGULAR at every q tested"),
                },
                "twoStepDegradation": {
                    "q3": "SRG(45,12,3,3) and it IS GQ(4,2)",
                    "q5": ("SRG(325,60,15,10) -- strongly regular but NOT a "
                           "quadrangle: s = lambda+1 = 16, t = mu-1 = 9 gives "
                           "(s+1)(st+1) = 17 x 145, nowhere near 325"),
                    "q7": "168-regular but NOT strongly regular at all",
                    "reading": ("a two-step degradation, not one: the object "
                                "does not simply fall apart at q = 5, it stays "
                                "strongly regular and only fails the quadrangle "
                                "identity; strong regularity itself goes at "
                                "q = 7"),
                },
                "everythingDownstreamIsQ3Only": ("the Schlafli configuration "
                                                 "(fe4fb77, f624d8f), the 27 "
                                                 "extraspecial 2^{1+4}_- groups "
                                                 "(34f2a84), the 200 ovoids and "
                                                 "the dual defect against W(3,3) "
                                                 "(8982d36), and tau_1 = 9 with "
                                                 "the new tower base (48e1841) "
                                                 "all rest on the graph being "
                                                 "GQ(4,2), which holds only at "
                                                 "q = 3; none should be quoted "
                                                 "with a 'for odd q' attached"),
                "secondIndependentArrival": ("the corpus already knows the "
                                             "quadrangle is a q = 3 coincidence "
                                             "from the REGULUS side -- "
                                             "the_quadrangle_is_the_q_equals_"
                                             "three_coincidence.json shows each "
                                             "all-isotropic regulus names "
                                             "(q+1)/2 polar pairs, an EDGE only "
                                             "at q = 3, and records isAGraph "
                                             "false from q = 5 on. That is the "
                                             "combinatorial route; this is the "
                                             "algebraic route through "
                                             "anticommutation and word length, "
                                             "reaching the same verdict and "
                                             "adding the SHAPE of the failure "
                                             "the prior file does not record"),
                "boundary": ("exact at q = 3, 5, 7: hyperbolic lines enumerated "
                             "completely, every reflection checked to be "
                             "O'Meara-hyperbolic, adjacency computed from the "
                             "matrices rather than a geometric shortcut, and "
                             "lambda/mu taken over ALL pairs. The closed forms "
                             "are read off three data points and NOT proved. No "
                             "q > 7 is tested, so 'not strongly regular for all "
                             "q >= 7' is NOT established -- only that q = 7 is "
                             "not. tau_2 is untouched"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
