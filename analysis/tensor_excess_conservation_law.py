#!/usr/bin/env python3
"""
One conservation law governs every depth-2 blocker: blocker excess plus column
dependence equals (t+1) times the distance above the shadow bound.

THE LAW.  Let Q be a GQ(s,t) with blocking number tau_1, and let X be any
depth-2 blocker with

    |X| = (st+1) tau_1 + r,

so r is how far X sits above the shadow bound. Write B_L for the row shadow of
line L, C_q for the column class of point q, and H_q for the set of lines
meeting C_q. Define

    F = sum over lines of (|B_L| - tau_1)        the BLOCKER EXCESS
    D = sum over points of ((t+1)|C_q| - |H_q|)  the COLUMN DEPENDENCE

Both are nonnegative -- every row shadow is a blocking set, and a set of c
points meets at most (t+1)c lines. Then

    F + D = (t+1) * r.                                              (LAW)

PROOF, in three lines.  Both sides of sum_L |B_L| = sum_q |H_q| count pairs
(L, q) with q in B_L. The left side is (#lines) tau_1 + F. The right side is
(t+1)|X| - D. Since (#lines) tau_1 = (t+1)(st+1) tau_1 = (t+1) times the
shadow bound, substituting |X| = shadow + r and cancelling gives the law. []

WHAT IT REPLACES.  At r = 0 both terms are nonnegative and sum to zero, so
F = D = 0: EVERY row shadow is a minimum blocker and EVERY column class is
independent. That is the entire tight-case setup, which
gq_tight_case_theorem.py derives through a chain of inequalities, obtained
here by cancelling one identity.

COLLISIONS ARE NOT A THIRD QUANTITY.  It is tempting to track
G = sum over tiles of (|X cap (L x M)| - |B_L cap M|), the number of times a
tile holds two leaves sharing a column. But for a fixed line L and point q,
if C_q meets L in k points then each of the t+1 lines M through q sees k
leaves where the shadow sees one, so

    G = (t+1) * D,

and the "second law" 4F + G = 16r for W(3,3) is just four times the first.
Recording that here because it looked like an independent constraint and is
not; two conservation laws would have been worth more than one, and only one
is real.

THE COROLLARY WORTH HAVING.  Since F and D are nonnegative and sum to
(t+1)r, each is at most (t+1)r. F counts excess one unit at a time, so

    at least (#lines) - (t+1)r row shadows are MINIMUM blockers,
    at least (#points) - (t+1)r column classes are INDEPENDENT.

For W(3,3) at |X| = 110 + r that is at least 40 - 4r of each. So any blocker
within a few leaves of the bound still has most of the tight-case structure
intact -- most rows still carry a centre, most columns are still partial
ovoids -- which is exactly the foothold a proof at r = 1 would need, and it
comes free from the law.

VERIFIED ON TWO BLOCKERS, both by recomputing every term from the leaf set:

  * the 115-leaf symmetric witness, r = 5: F = 10, D = 10, sum 20 = 4r;
    G = 40 = 4D; 33 of 40 row shadows minimum and 33 of 40 column classes
    independent, against the guaranteed 40 - 20 = 20 of each.
  * the product blocker B x B, r = 11: the law is checked there too, on a
    blocker built by an entirely different construction.

The witness's anatomy is worth recording on its own. Its row shadows are
33 of size 11, four of size 12 and three of size 13; its column classes run
{1: 9, 2: 3, 3: 18, 4: 9, 10: 1}. That single class of size 10 cannot be
independent, since alpha(W(3,3)) = 7 -- so the optimum is not a near-tight
configuration with a few defects, it carries one genuinely large dependent
column.

SCOPE.  The law is exact and holds for every GQ and every depth-2 blocker; it
is an identity, not a bound, and by itself it excludes nothing. It does not
move tau_2, which stays open in [111, 115].
"""

import collections
import itertools
import json
import os
import subprocess
import sys

ROOT = r"C:\Repos\Holotrade"
Q = 3
N = 40


def geometry():
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
        for x, y in itertools.product(range(Q), repeat=2):
            if x == y == 0:
                continue
            S.add(idx[nm(tuple((x * pts[a][k] + y * pts[b][k]) % Q
                               for k in range(4)))])
        if len(S) == 4:
            lines.add(tuple(sorted(S)))
    return sorted(lines)


def anatomy(X, lines, tau1=11, t_plus_1=4, shadow=110):
    """Recompute every term of the law from the leaf set alone."""
    lsets = [set(L) for L in lines]
    B = [set(q for (p, q) in X if p in L) for L in lsets]
    Dm = [set(p for (p, q) in X if q in M) for M in lsets]
    C = [set(p for (p, q) in X if q == j) for j in range(N)]
    H = [sum(1 for L in lsets if any(p in L for p in C[j])) for j in range(N)]
    F = sum(len(s) - tau1 for s in B)
    D = sum(t_plus_1 * len(C[j]) - H[j] for j in range(N))
    G = 0
    for li, L in enumerate(lsets):
        for M in lsets:
            tile = sum(1 for (p, q) in X if p in L and q in M)
            G += tile - len(B[li] & M)
    r = len(X) - shadow
    return {
        "size": len(X), "r": r,
        "F": F, "D": D, "FplusD": F + D, "lawTarget": t_plus_1 * r,
        "lawHolds": F + D == t_plus_1 * r,
        "G": G, "GequalsTPlus1D": G == t_plus_1 * D,
        "rowShadowSizes": dict(collections.Counter(len(s) for s in B)),
        "colShadowSizes": dict(collections.Counter(len(s) for s in Dm)),
        "columnClassSizes": dict(collections.Counter(len(c) for c in C)),
        "minimumRowShadows": sum(1 for s in B if len(s) == tau1),
        "independentColumnClasses": sum(1 for j in range(N)
                                        if t_plus_1 * len(C[j]) == H[j]),
        "guaranteedMinimumRows": max(0, len(lines) - t_plus_1 * r),
        "guaranteedIndependentColumns": max(0, N - t_plus_1 * r),
    }


def main():
    lines = geometry()
    out = subprocess.run(
        ["node", "-e", "global.window=global;"
         "const T=require('./js/tensor-sharding.js');"
         "process.stdout.write(JSON.stringify({w:T.SYMMETRIC_WITNESS,"
         "b:T.BLOCKER}));"],
        cwd=ROOT, capture_output=True, text=True)
    d = json.loads(out.stdout)
    W = [(v // N, v % N) for v in d["w"]]
    B0 = d["b"]
    PROD = [(p, q) for p in B0 for q in B0]

    print("THE EXCESS CONSERVATION LAW")
    print("=" * 72)
    print("  F + D = (t+1) r, where F is blocker excess, D column dependence,")
    print("  and r the distance above the shadow bound. Both sides count the")
    print("  pairs (L,q) with q in B_L, once as rows and once as columns.")
    print()
    rows = []
    for name, X in (("115-leaf symmetric witness", W),
                    ("product blocker B x B", PROD)):
        a = anatomy(X, lines)
        a["name"] = name
        rows.append(a)
        print("  %s: |X| = %d, r = %d" % (name, a["size"], a["r"]))
        print("     F = %-3d D = %-3d  F + D = %-3d  vs (t+1)r = %-3d  -> %s"
              % (a["F"], a["D"], a["FplusD"], a["lawTarget"], a["lawHolds"]))
        print("     G = %-4d = (t+1) D ? %s   (so G is not independent)"
              % (a["G"], a["GequalsTPlus1D"]))
        print("     row shadow sizes %s" % a["rowShadowSizes"])
        print("     column class sizes %s" % a["columnClassSizes"])
        print("     minimum row shadows %d (guaranteed >= %d); independent "
              "column classes %d (guaranteed >= %d)"
              % (a["minimumRowShadows"], a["guaranteedMinimumRows"],
                 a["independentColumnClasses"],
                 a["guaranteedIndependentColumns"]))
        print()

    print("  At r = 0 both terms vanish, giving the whole tight-case setup --")
    print("  every row shadow minimum, every column class independent -- by")
    print("  cancelling one identity instead of chaining inequalities.")
    print()
    print("  The witness carries a column class of size 10, which cannot be")
    print("  independent since alpha(W(3,3)) = 7. The optimum is not a")
    print("  near-tight configuration with small defects.")

    ok = all(a["lawHolds"] and a["GequalsTPlus1D"] for a in rows)
    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "tensor_excess_conservation_law.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.tensor-excess-conservation.v1",
                "valid": bool(ok),
                "law": "F + D = (t+1) r",
                "definitions": {
                    "F": "sum over lines of (|B_L| - tau_1), blocker excess",
                    "D": "sum over points of ((t+1)|C_q| - |H_q|), dependence",
                    "r": "|X| - (st+1) tau_1, distance above the shadow bound",
                },
                "proof": ("sum_L |B_L| = sum_q |H_q|, both counting pairs "
                          "(L,q) with q in B_L; the left is #lines*tau_1 + F "
                          "and the right is (t+1)|X| - D"),
                "collisionsNotIndependent": ("G = (t+1) D exactly, so the "
                                             "apparent second law 4F + G = 16r "
                                             "is four times the first"),
                "corollary": ("at least #lines - (t+1)r row shadows are "
                              "minimum and at least #points - (t+1)r column "
                              "classes are independent"),
                "instances": rows,
                "tightCase": ("at r = 0 the law forces F = D = 0, recovering "
                              "the entire tight-case structure in one step"),
                "boundary": ("an identity, not a bound; it excludes nothing on "
                             "its own and does not move tau_2, open in "
                             "[111, 115]"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
