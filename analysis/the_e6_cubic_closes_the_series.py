#!/usr/bin/env python3
"""
The open half of c6d1077 closes: the corpus's E6 cubic IS a cubic norm of the
same series as the rank-3 Pfaffian. But the coordinates one corpus file states
for it admit no cubic at all, and the correct model is supplied here.

WHAT WAS LEFT OPEN.  c6d1077 showed the rank-3 symplectic invariant is the
15-dimensional cubic Jordan algebra H_3(H), the A5 member of the Severi series
whose E6 member is the 27, and explicitly did NOT claim that the corpus's gate
cubic is the H_3(O) norm, because how the gate layer defines its cubic had not
been examined. It has now.

WHAT THE CORPUS SAYS.  analysis/w33_cv_universality_cubic.py (Theory-of-
Everything) argues that Lloyd-Braunstein CV universality needs degree 2 plus
degree 3, that the substrate supplies both, and identifies the degree-3 piece as

    "the E6 CARTAN CUBIC on the matter 27 = 3 (x) 3 (x) 3, the epsilon-cubic
     that sl(3,F_3)^3 preserves"

The headline is fine and is not challenged here. The parenthetical realization
is not.

THERE IS NO INVARIANT CUBIC ON 3 (x) 3 (x) 3.  Two independent checks.

First, the natural "epsilon-cubic" -- the contraction of three copies of the
tensor against three epsilon symbols -- VANISHES IDENTICALLY, and for a reason:
exchanging two of the three tensor factors reverses all three epsilons, giving
(-1)^3 = -1, so the expression equals its own negative. Measured: nonzero on
0 of 200 random tensors at each of q = 3, 5, 7, 11, 13.

Second, and decisively, the space of SL(3)^3-invariant cubics on 3 (x) 3 (x) 3
is ZERO. An invariant must have weight zero, which forces each factor's three
indices to be a permutation of {0,1,2}, leaving 36 candidate monomials; imposing
invariance under unipotent generators kills all of them:

    space                 group        weight-0 cubic monomials   invariant cubics
    3 (x) 3      (dim 9)   SL(3)^2              6                        1
    3 (x) 3 (x) 3 (dim 27) SL(3)^3             36                        0

at q = 5, 7, 11. The first row is the POSITIVE CONTROL and its answer is the
determinant -- which is itself the 9-dimensional member H_3(C) of the same
Severi series, so the method finds cubic norms exactly where they exist.

This is consistent with the classical picture: 3 (x) 3 (x) 3 is not the
minuscule 27 at all. It is the graded piece of the E6 ADJOINT under the
Z/3-grading, 78 = 27 + 24 + 27 with 24 = dim sl(3)^3, and the invariants of that
theta-group are classically of degrees 6, 9 and 12 (Vinberg-Elashvili) -- no
cubic, which is what the computation independently shows.

THE CORRECT MODEL, AND IT WORKS AT THE CORPUS'S OWN PRIME.  The minuscule 27
restricts to SL(3)^3 as (3,3bar,1) + (1,3,3bar) + (3bar,1,3), i.e. three copies
of M_3, and on it the E6 Cartan cubic is

    N(A,B,C) = det A + det B + det C - tr(ABC).

That is a genuine cubic norm: with # taken as the gradient of N, which is legal
because N is linear in each of the 27 coordinates,

    q      (x#)# == N(x) x      N nonzero on
    3          200 / 200           132 / 200
    5          200 / 200           163 / 200
    7          200 / 200           164 / 200
   11          200 / 200           185 / 200

exactly, with no scalar correction -- and it holds at q = 3, the substrate's own
prime, where the broken realization gives the zero form.

SO THE SERIES IS COMPLETE, AND VERIFIED BY ONE TEST.  The same adjoint identity
now holds for three members, each checked over finite fields by the same
harness:

    dim   algebra    cubic norm                          group        checked
     9    H_3(C)     det of a 3x3 matrix                 SL(3)^2      unique invariant
    15    H_3(H)     Pfaffian on Lambda^2(F^6)           SL(6)        c6d1077, 300/300
    27    H_3(O)     det A + det B + det C - tr(ABC)     E6           200/200 here

The rank-3 symplectic obstruction and the corpus's gate cubic are the 15- and
27-dimensional members of one series. That is the claim c6d1077 declined to
make, and it is now made.

WHAT THIS DOES AND DOES NOT SAY ABOUT THE CORPUS FILE.  It does not touch the
Lloyd-Braunstein argument, the degree-2 / degree-3 conclusion, or the existence
of the E6 cubic; all of those stand, and the corpus's own 27-36-45 cubic-surface
triangle is about the right 27, whose lines are the weights of the minuscule
representation. What fails is one parenthetical realization in one file: the
27 is not 3 (x) 3 (x) 3 for this purpose, and the "epsilon-cubic that sl(3)^3
preserves" does not exist. That is CLAUDE.md's fourth failure mode exactly -- a
sound file with one ungrounded sentence, which a file-level audit passes and
only reading the sentence catches. The fix is a coordinate change, not a
retraction.

SCOPE.  The invariant-cubic dimensions are computed by imposing invariance on
random group elements and tensors and taking a nullspace over GF(q), so a
nonzero answer is certain but a zero answer is "no invariant survived 400
independent linear conditions on a 36-dimensional space" -- overwhelming but not
a proof, and the 3 (x) 3 control returning exactly 1 is what calibrates it. The
adjoint identity is checked on 200 random elements per prime at q = 3, 5, 7, 11,
so a demonstration rather than a proof, though it is a polynomial identity that
would hold formally. That N(A,B,C) is THE E6 Cartan cubic, and that the theta-
group invariants have degrees 6, 9, 12, are quoted as classical and not
re-derived. No claim is made about gate universality, about the physical layer,
or about tau_2.
"""

import itertools
import json
import os
import random
import sys

import numpy as np
from sympy import GF, Matrix
from sympy.polys.matrices import DomainMatrix

ROOT = r"C:\Repos\Holotrade"
PERM = [(p, (-1) ** sum(1 for i in range(3) for j in range(i + 1, 3)
                        if p[i] > p[j]))
        for p in itertools.permutations(range(3))]


# ---------- the broken realization: epsilon-cubic on 3 (x) 3 (x) 3 ----------

def eps_cubic(T, q):
    tot = 0
    for pi, si in PERM:
        for pj, sj in PERM:
            for pk, sk in PERM:
                tot += (si * sj * sk
                        * T[pi[0]][pj[0]][pk[0]]
                        * T[pi[1]][pj[1]][pk[1]]
                        * T[pi[2]][pj[2]][pk[2]])
    return tot % q


# ---------- invariant-cubic dimension, with a positive control ----------

def sl3_gens(q):
    G = []
    for i in range(3):
        for j in range(3):
            if i != j:
                M = np.eye(3, dtype=np.int64)
                M[i, j] = 1
                G.append(M % q)
    return G


def invariant_cubics(nfac, q, samples=400, seed=0):
    rnd = random.Random(seed)
    perms = list(itertools.permutations(range(3)))
    mons = []
    for rest in itertools.product(perms, repeat=nfac - 1):
        mons.append(tuple(tuple([t] + [rest[f][t] for f in range(nfac - 1)])
                          for t in range(3)))

    def ev(m, T):
        p = 1
        for idx in m:
            p *= T[idx]
        return p

    def act(gs, T):
        U = T
        for f, g in enumerate(gs):
            U = np.moveaxis(np.tensordot(g, U, axes=([1], [f])), 0, f)
        return U % q

    SL = sl3_gens(q)
    rows = []
    for _ in range(samples):
        T = np.array([rnd.randrange(q) for _ in range(3 ** nfac)],
                     dtype=np.int64).reshape((3,) * nfac)
        gs = [SL[rnd.randrange(len(SL))] if rnd.random() < 0.7
              else np.eye(3, dtype=np.int64) for _ in range(nfac)]
        U = act(gs, T)
        rows.append([(ev(m, U) - ev(m, T)) % q for m in mons])
    R = DomainMatrix.from_Matrix(Matrix(rows)).convert_to(GF(q))
    return len(mons), len(R.nullspace().to_Matrix().tolist())


# ---------- the correct model: E6 Cartan cubic on M3 + M3 + M3 ----------

def det3(M, q):
    return (M[0, 0] * (M[1, 1] * M[2, 2] - M[1, 2] * M[2, 1])
            - M[0, 1] * (M[1, 0] * M[2, 2] - M[1, 2] * M[2, 0])
            + M[0, 2] * (M[1, 0] * M[2, 1] - M[1, 1] * M[2, 0])) % q


def cartan(x, q):
    A, B, C = x
    return (det3(A, q) + det3(B, q) + det3(C, q)
            - int(np.trace(A @ B @ C))) % q


def sharp(x, q):
    base = cartan(x, q)
    out = [np.zeros((3, 3), dtype=np.int64) for _ in range(3)]
    for f in range(3):
        for i in range(3):
            for j in range(3):
                y = [m.copy() for m in x]
                y[f][i, j] = (y[f][i, j] + 1) % q
                out[f][i, j] = (cartan(y, q) - base) % q
    return out


def check_cartan(q, trials=200, seed=1):
    r = random.Random(seed)
    ok = nz = 0
    for _ in range(trials):
        x = [np.array([[r.randrange(q) for _ in range(3)] for _ in range(3)],
                      dtype=np.int64) for _ in range(3)]
        n = cartan(x, q)
        if n % q:
            nz += 1
        SS = sharp(sharp(x, q), q)
        if all(int(SS[f][i, j]) % q == (n * int(x[f][i, j])) % q
               for f in range(3) for i in range(3) for j in range(3)):
            ok += 1
    return {"q": q, "trials": trials, "adjointHeld": ok,
            "adjointExact": ok == trials, "normNonzero": nz,
            "normNotIdenticallyZero": nz > 0}


def main():
    r = random.Random(7)
    epsz = []
    for q in (3, 5, 7, 11, 13):
        nz = 0
        for _ in range(200):
            T = [[[r.randrange(q) for _ in range(3)] for _ in range(3)]
                 for _ in range(3)]
            if eps_cubic(T, q) % q:
                nz += 1
        epsz.append({"q": q, "trials": 200, "nonzero": nz,
                     "identicallyZero": nz == 0})

    inv = []
    for q in (5, 7, 11):
        n2, d2 = invariant_cubics(2, q)
        n3, d3 = invariant_cubics(3, q)
        inv.append({"q": q,
                    "control_3x3": {"monomials": n2, "invariantCubics": d2},
                    "test_3x3x3": {"monomials": n3, "invariantCubics": d3},
                    "controlIsOne": d2 == 1, "testIsZero": d3 == 0})

    cart = [check_cartan(q) for q in (3, 5, 7, 11)]

    print("THE E6 CUBIC CLOSES THE SERIES")
    print("=" * 72)
    print("  c6d1077 declined to claim the corpus's gate cubic is the H_3(O)")
    print("  norm, because the gate layer's definition had not been examined.")
    print()
    print("  w33_cv_universality_cubic.py calls it 'the E6 CARTAN CUBIC on the")
    print("  matter 27 = 3 (x) 3 (x) 3, the epsilon-cubic that sl(3,F_3)^3")
    print("  preserves'. The headline is fine; that realization is not.")
    print()
    print("  (1) the natural epsilon-cubic VANISHES IDENTICALLY -- exchanging")
    print("      two tensor factors reverses all three epsilons, (-1)^3 = -1:")
    for e in epsz:
        print("        q=%2d  nonzero on %d/200" % (e["q"], e["nonzero"]))
    print()
    print("  (2) and there is NO invariant cubic on 3 (x) 3 (x) 3 at all:")
    print("        q    control 3(x)3: monomials/invariants   test 3(x)3(x)3")
    for i in inv:
        print("       %2d          %d / %d  (expect 1 = det)         %2d / %d"
              % (i["q"], i["control_3x3"]["monomials"],
                 i["control_3x3"]["invariantCubics"],
                 i["test_3x3x3"]["monomials"],
                 i["test_3x3x3"]["invariantCubics"]))
    print("      the control's answer IS the determinant, itself the 9-dim")
    print("      member H_3(C) of the same series -- so the method finds cubic")
    print("      norms exactly where they exist. 3(x)3(x)3 is the graded piece")
    print("      of the E6 ADJOINT (78 = 27+24+27), whose theta-group")
    print("      invariants are classically of degrees 6, 9, 12: no cubic.")
    print()
    print("  THE CORRECT MODEL. The minuscule 27 restricts to SL(3)^3 as three")
    print("  copies of M_3, and there the Cartan cubic is")
    print("      N(A,B,C) = det A + det B + det C - tr(ABC),")
    print("  a genuine cubic norm:")
    print("        q     (x#)# == N(x)x      N nonzero on")
    for c in cart:
        print("       %2d        %3d / %3d           %3d / %3d"
              % (c["q"], c["adjointHeld"], c["trials"],
                 c["normNonzero"], c["trials"]))
    print("  exactly, no scalar correction, INCLUDING AT q = 3 -- the")
    print("  substrate's own prime, where the broken realization is the zero")
    print("  form.")
    print()
    print("  SO THE SERIES IS COMPLETE, ONE TEST FOR THREE MEMBERS:")
    print("     dim 9   H_3(C)   det(3x3)                        unique invariant")
    print("     dim 15  H_3(H)   Pfaffian on Lambda^2(F^6)       c6d1077 300/300")
    print("     dim 27  H_3(O)   detA+detB+detC-tr(ABC)          200/200 here")
    print("  The rank-3 symplectic obstruction and the corpus's gate cubic are")
    print("  the 15- and 27-dimensional members of one series.")
    print()
    print("  This does NOT touch Lloyd-Braunstein, the degree-2/degree-3")
    print("  conclusion, or the existence of the E6 cubic. One parenthetical")
    print("  realization in one file is wrong; the fix is a coordinate change,")
    print("  not a retraction. CLAUDE.md failure mode four exactly.")

    ok = (all(e["identicallyZero"] for e in epsz)
          and all(i["controlIsOne"] and i["testIsZero"] for i in inv)
          and all(c["adjointExact"] and c["normNotIdenticallyZero"]
                  for c in cart)
          and any(c["q"] == 3 and c["adjointExact"] for c in cart))

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "e6_cubic_closes_the_series.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.e6-cubic-closes-series.v1",
                "valid": bool(ok),
                "whatWasLeftOpen": ("c6d1077 showed the rank-3 symplectic "
                                    "invariant is the 15-dimensional cubic "
                                    "Jordan algebra H_3(H) and explicitly did NOT "
                                    "claim the corpus's gate cubic is the H_3(O) "
                                    "norm, because how the gate layer defines its "
                                    "cubic had not been examined"),
                "whatTheCorpusSays": ("analysis/w33_cv_universality_cubic.py "
                                      "identifies the degree-3 piece as 'the E6 "
                                      "CARTAN CUBIC on the matter 27 = 3 (x) 3 "
                                      "(x) 3, the epsilon-cubic that sl(3,F_3)^3 "
                                      "preserves'. The headline -- Lloyd-"
                                      "Braunstein needs degree 2 plus degree 3 "
                                      "and the substrate supplies both -- is fine "
                                      "and is NOT challenged. The parenthetical "
                                      "realization is"),
                "epsilonCubicVanishes": epsz,
                "whyItVanishes": ("exchanging two of the three tensor factors "
                                  "reverses all three epsilon symbols, giving "
                                  "(-1)^3 = -1, so the contraction equals its own "
                                  "negative and is identically zero"),
                "invariantCubicDimensions": inv,
                "theControl": ("3 (x) 3 under SL(3)^2 returns exactly ONE "
                               "invariant cubic, the determinant, which is itself "
                               "the 9-dimensional member H_3(C) of the same "
                               "Severi series -- so the method finds cubic norms "
                               "exactly where they exist, and the zero for "
                               "3 (x) 3 (x) 3 is calibrated"),
                "whichTwentySeven": ("3 (x) 3 (x) 3 is not the minuscule 27: it "
                                     "is the graded piece of the E6 ADJOINT under "
                                     "the Z/3-grading, 78 = 27 + 24 + 27 with "
                                     "24 = dim sl(3)^3, and the invariants of "
                                     "that theta-group are classically of degrees "
                                     "6, 9 and 12 (Vinberg-Elashvili) -- no "
                                     "cubic, which the computation independently "
                                     "shows"),
                "theCorrectModel": ("the minuscule 27 restricts to SL(3)^3 as "
                                    "(3,3bar,1) + (1,3,3bar) + (3bar,1,3), three "
                                    "copies of M_3, and there the E6 Cartan cubic "
                                    "is N(A,B,C) = det A + det B + det C - "
                                    "tr(ABC), which satisfies the cubic-norm "
                                    "adjoint identity exactly with no scalar "
                                    "correction, INCLUDING at q = 3 where the "
                                    "broken realization is the zero form"),
                "cartanChecks": cart,
                "theSeriesIsComplete": {
                    "9": "H_3(C), det of a 3x3 matrix, SL(3)^2, unique invariant",
                    "15": ("H_3(H), Pfaffian on Lambda^2(F^6), SL(6), c6d1077 "
                           "300/300"),
                    "27": ("H_3(O), det A + det B + det C - tr(ABC), E6, 200/200 "
                           "here"),
                    "reading": ("the rank-3 symplectic obstruction and the "
                                "corpus's gate cubic are the 15- and "
                                "27-dimensional members of ONE series; this is "
                                "the claim c6d1077 declined to make, and it is "
                                "now made"),
                },
                "whatThisDoesNotSay": ("it does not touch the Lloyd-Braunstein "
                                       "argument, the degree-2/degree-3 "
                                       "conclusion, or the existence of the E6 "
                                       "cubic -- all stand, and the corpus's own "
                                       "27-36-45 cubic-surface triangle is about "
                                       "the right 27, whose lines are the weights "
                                       "of the minuscule representation. What "
                                       "fails is ONE parenthetical realization in "
                                       "ONE file. That is CLAUDE.md's fourth "
                                       "failure mode exactly -- a sound file with "
                                       "one ungrounded sentence, which a "
                                       "file-level audit passes and only reading "
                                       "the sentence catches. The fix is a "
                                       "coordinate change, not a retraction"),
                "boundary": ("the invariant-cubic dimensions are computed by "
                             "imposing invariance on random group elements and "
                             "tensors and taking a nullspace over GF(q), so a "
                             "nonzero answer is certain but a ZERO answer is 'no "
                             "invariant survived 400 independent linear "
                             "conditions on a 36-dimensional space' -- "
                             "overwhelming but not a proof, with the 3 (x) 3 "
                             "control returning exactly 1 as the calibration. The "
                             "adjoint identity is checked on 200 random elements "
                             "per prime at q = 3, 5, 7, 11, a demonstration "
                             "rather than a proof, though it is a polynomial "
                             "identity that would hold formally. That N(A,B,C) is "
                             "THE E6 Cartan cubic, and that the theta-group "
                             "invariants have degrees 6, 9, 12, are quoted as "
                             "classical and not re-derived. No claim is made "
                             "about gate universality, the physical layer, or "
                             "tau_2"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
