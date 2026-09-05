#!/usr/bin/env python3
"""
Two corrections to ae04deb, both of which STRENGTHEN its no-go: at q = 3 the
rank-3 invariant form is degenerate, and the seven classes are not orbits --
the code's weight function separates one of them.

WHY LOOK.  fe3e8fd identified the rank-2 orbit census with the weight enumerator
of the Cardinali-Giuzzi line Symplectic Grassmann code. The same code family is
defined at every rank, so the rank-3 member is a probe of ae04deb's claims that
costs nothing to run. It found two things wrong with how those claims were
phrased.

CORRECTION ONE: AT q = 3 THE RANK-3 INVARIANT FORM IS DEGENERATE.  ae04deb
reported "invariant symmetric forms = 1" at n = 3 for q = 3 and q = 5 and left
it there. The form exists at both, but its rank on ker(omega) is not the same:

    n   q    dim ker(omega)   rank of the induced form   degenerate   q | n
    2   3          5                    5                   no          no
    2   5          5                    5                   no          no
    3   3         14                   13                  YES         YES
    3   5         14                   14                   no          no
    3   7         14                   14                   no          no

The degeneracy is exactly the condition q | n, which at n = 3 singles out q = 3.
So at that prime there is not merely "no orthogonal geometry controlling the
orbits" -- there is no nondegenerate form at all, and the obstruction is
strictly stronger than ae04deb stated. At q = 5 and 7 the form is nondegenerate
and the obstruction is the degree/orbit argument as given. ae04deb's conclusion
is unaffected, because its decisive witnesses were exhibited at BOTH q = 3 and
q = 5 and the q = 5 form is nondegenerate.

CORRECTION TWO: THE SEVEN CLASSES ARE CLASSES, NOT ORBITS.  ae04deb said "seven
classes appear where rank 2 has three", which is true and was worded as classes.
The natural reading is that they are the orbits. They are not. Computing, for
each stratum, the weight of the corresponding codeword:

    n = 2, q = 3, N = 40                 n = 3, q = 3, N = 3640
      (2, zero)  -> 27                     (2, zero) -> 2187
      (4, sq)    -> 30                     (4, zero) -> 2430
      (4, nsq)   -> 24                     (4, sq)   -> 2430
                                           (4, nsq)  -> 2376
      weight IS a function of the          (6, zero) -> 2187 AND 2430
      stratum: one weight each             (6, sq)   -> 2430
                                           (6, nsq)  -> 2457

At rank 2 each stratum carries exactly one weight. At rank 3 the stratum
(bivector rank 6, class zero) carries TWO, so (rank, class) is not a complete
invariant and the true orbit count at rank 3 is at least eight. That again
strengthens the no-go: the rank-3 structure is further from the clean rank-2
trichotomy than "seven classes" suggested.

THE CODE PARAMETERS MATCH AT BOTH RANKS.  Cardinali-Giuzzi give
N = prod (q^{2n-2i}-1)/(q^{i+1}-1) and K = 2n^2-n-1 for k = 2. Building the
line symplectic Grassmann code directly from the totally isotropic lines:

    n = 2, q = 3   N = 40   (CG 40)     K = 5   (CG 5)
    n = 3, q = 3   N = 3640 (CG 3640)   K = 14  (CG 14)

and the rank-2 weight set is exactly {24, 27, 30} exhaustively, with minimum 24
= q^3 - q as their theorem says.

AND A NEGATIVE RESULT WORTH RECORDING.  At rank 3 neither an unbiased direct
sample of 60,000 functionals nor a stratum-based sample of 150,000 found a
codeword of Cardinali-Giuzzi's minimum weight d = q^7 - q^3 = 2160; the smallest
weight seen was 2187 = q^7. Two separate reasons, and both matter. The direct
sample is unbiased but 60,000 of 3^14 is 1.25% of the code, so a small
minimum-weight orbit is easy to miss. The stratum-based sample is WORSE than
that: it indexes functionals by points p through the invariant form, and at
q = 3 that form is degenerate, so it reaches only a 13-dimensional image inside
the 14-dimensional dual and CANNOT see two thirds of the codewords. The
published minimum distance is not in doubt; what is recorded is that this
harness does not reach it, and why.

SCOPE.  The degeneracy table is exact, computed as the rank over GF(q) of the
induced form restricted to ker(omega). The rank-2 weight-by-stratum table is
exhaustive. The rank-3 weight-by-stratum table is from 150,000 samples and is
therefore a LOWER bound on the weights per stratum: a stratum shown with one
weight may carry more, so "at least eight orbits" is a lower bound and the two
weights found in (6, zero) are what makes it strictly greater than seven. No
claim is made about the exact orbit count at rank 3, about the weight enumerator
of the rank-3 code, or about q = 5 and 7 at rank 3, which were not run for
weights. Nothing here revises fe3e8fd's attribution or touches tau_2.
"""

import collections
import itertools
import json
import os
import random
import sys

import numpy as np
from sympy import GF, Matrix
from sympy.polys.matrices import DomainMatrix

ROOT = r"C:\Repos\Holotrade"


def setup(n, q):
    d = 2 * n
    PR = [(i, j) for i in range(d) for j in range(i + 1, d)]
    J = np.zeros((d, d), dtype=np.int64)
    for i in range(n):
        J[i, n + i] = 1
        J[n + i, i] = q - 1
    M = np.zeros((len(PR), len(PR)), dtype=np.int64)
    for k, (i, j) in enumerate(PR):
        for l, (a, b) in enumerate(PR):
            M[k, l] = (J[i, a] * J[j, b] - J[i, b] * J[j, a]) % q
    w = np.array([J[i, j] for (i, j) in PR], dtype=np.int64) % q
    ns = DomainMatrix.from_Matrix(
        Matrix(w.reshape(1, -1).tolist())).convert_to(GF(q)).nullspace()
    Kb = np.array(ns.to_Matrix().tolist(), dtype=np.int64) % q
    return d, PR, J, M, w, Kb


def degeneracy(n, q):
    d, PR, J, M, w, Kb = setup(n, q)
    R = (Kb @ M @ Kb.T) % q
    rk = DomainMatrix.from_Matrix(Matrix(R.tolist())).convert_to(GF(q)).rank()
    return {"n": n, "q": q, "dimKerOmega": int(Kb.shape[0]),
            "rankOfInducedForm": int(rk),
            "degenerate": int(rk) < int(Kb.shape[0]),
            "qDividesN": n % q == 0}


def build_code(n, q):
    d, PR, J, M, w, Kb = setup(n, q)

    def nm(v):
        i = next(k for k, x in enumerate(v) if x % q)
        z = pow(v[i] % q, -1, q)
        return tuple((z * x) % q for x in v)

    P = sorted({nm(v) for v in itertools.product(range(q), repeat=d) if any(v)})

    def sf(u, v):
        return int(np.array(u) @ J @ np.array(v)) % q

    lines = set()
    for a, b in itertools.combinations(P, 2):
        if sf(a, b) % q:
            continue
        wv = tuple((a[i] * b[j] - a[j] * b[i]) % q for (i, j) in PR)
        if any(wv):
            i = next(k for k, x in enumerate(wv) if x % q)
            z = pow(wv[i] % q, -1, q)
            lines.add(tuple((z * x) % q for x in wv))
    L = sorted(lines)
    return np.array(L, dtype=np.int64).T, Kb, M, PR, J, len(L)


def bivrank(b, d, PR, q):
    A = np.zeros((d, d), dtype=np.int64)
    for k, (i, j) in enumerate(PR):
        A[i, j] = b[k] % q
        A[j, i] = (-b[k]) % q
    r = 0
    for c in range(d):
        p = next((i for i in range(r, d) if A[i, c] % q), None)
        if p is None:
            continue
        A[[r, p]] = A[[p, r]]
        A[r] = (A[r] * pow(int(A[r, c]), -1, q)) % q
        for i in range(d):
            if i != r and A[i, c] % q:
                A[i] = (A[i] - A[i, c] * A[r]) % q
        r += 1
    return r


def weights_by_stratum(n, q, samples, seed=3):
    G, Kb, M, PR, J, N = build_code(n, q)
    d = 2 * n
    sq = {(x * x) % q for x in range(1, q)}
    w = np.array([J[i, j] for (i, j) in PR], dtype=np.int64) % q
    rnd = random.Random(seed)
    out = collections.defaultdict(set)
    cnt = collections.Counter()
    GT = G.T
    exhaustive = q ** Kb.shape[0] <= 30000
    if exhaustive:
        it = (np.array(c, dtype=np.int64) @ Kb % q
              for c in itertools.product(range(q), repeat=Kb.shape[0]))
    else:
        it = (np.array([rnd.randrange(q) for _ in PR], dtype=np.int64)
              for _ in range(samples))
    for b in it:
        if not b.any() or (b * w).sum() % q:
            continue
        Qv = int(b @ M @ b) % q
        cls = "zero" if Qv == 0 else ("square" if Qv in sq else "nonsquare")
        r = bivrank(b, d, PR, q)
        out[(r, cls)].add(int(np.count_nonzero((GT @ (M @ b)) % q)))
        cnt[(r, cls)] += 1
    return N, out, cnt, exhaustive


def main():
    deg = [degeneracy(n, q) for (n, q) in
           [(2, 3), (2, 5), (3, 3), (3, 5), (3, 7)]]

    strata = {}
    for (n, q) in [(2, 3), (3, 3)]:
        N, out, cnt, ex = weights_by_stratum(n, q, 150000)
        strata["%d,%d" % (n, q)] = {
            "N": N, "exhaustive": ex,
            "byStratum": {"%d,%s" % k: sorted(v) for k, v in sorted(out.items())},
            "counts": {"%d,%s" % k: v for k, v in sorted(cnt.items())},
            "weightIsFunctionOfStratum": all(len(v) == 1 for v in out.values()),
            "distinctWeights": sorted({x for v in out.values() for x in v}),
            "cgN": None, "cgK": 2 * n * n - n - 1,
            "cgD": q ** (4 * n - 5) - q ** (2 * n - 3),
        }
        num = 1
        for i in range(2):
            num = num * (q ** (2 * n - 2 * i) - 1) // (q ** (i + 1) - 1)
        strata["%d,%d" % (n, q)]["cgN"] = num
        strata["%d,%d" % (n, q)]["matchesCGlength"] = (N == num)

    print("THE RANK-THREE STRATA ARE NOT ORBITS")
    print("=" * 72)
    print("  Two corrections to ae04deb, both of which STRENGTHEN its no-go.")
    print()
    print("  ONE: at q = 3 the rank-3 invariant form is DEGENERATE.")
    print("    n  q   dim ker(omega)  rank of form  degenerate  q | n")
    for r in deg:
        print("    %d %2d        %3d           %3d        %-5s      %s"
              % (r["n"], r["q"], r["dimKerOmega"], r["rankOfInducedForm"],
                 r["degenerate"], r["qDividesN"]))
    print("  The degeneracy is exactly q | n, which at n = 3 singles out q = 3.")
    print("  So there the obstruction is STRONGER than stated: not merely no")
    print("  orthogonal geometry controlling the orbits, but no nondegenerate")
    print("  form at all. ae04deb's conclusion is unaffected -- its witnesses")
    print("  were exhibited at q = 5 too, where the form is nondegenerate.")
    print()
    print("  TWO: the seven classes are CLASSES, not orbits.")
    for k in sorted(strata):
        s = strata[k]
        print("    n,q = %s  N = %d (CG %d, match %s)  %s"
              % (k, s["N"], s["cgN"], s["matchesCGlength"],
                 "EXHAUSTIVE" if s["exhaustive"] else "sampled"))
        for st, ws in s["byStratum"].items():
            print("        stratum (%s) -> weights %s" % (st, ws))
        print("        weight is a function of the stratum: %s"
              % s["weightIsFunctionOfStratum"])
    print("  At rank 2 each stratum carries exactly one weight. At rank 3 the")
    print("  stratum (6, zero) carries TWO, so (rank, class) is not a complete")
    print("  invariant and there are AT LEAST EIGHT orbits at rank 3.")
    print()
    print("  AND A NEGATIVE WORTH RECORDING: neither an unbiased direct sample")
    print("  of 60,000 functionals nor this 150,000-sample stratum pass found")
    print("  a codeword of CG's minimum weight q^7 - q^3 = 2160; the smallest")
    print("  seen was 2187 = q^7. The direct sample is unbiased but covers")
    print("  1.25 percent of the code. This stratum pass is WORSE: it")
    print("  functionals through the invariant form, which at q = 3 is")
    print("  degenerate, so it reaches only a 13-dimensional image inside the")
    print("  14-dimensional dual and cannot see two thirds of the codewords.")
    print("  The published minimum distance is not in doubt; what is recorded")
    print("  is that this harness does not reach it, and why.")

    r2 = strata["2,3"]
    r3 = strata["3,3"]
    ok = (r2["exhaustive"] and r2["weightIsFunctionOfStratum"]
          and r2["distinctWeights"] == [24, 27, 30]
          and r2["matchesCGlength"] and r3["matchesCGlength"]
          and not r3["weightIsFunctionOfStratum"]
          and len(r3["byStratum"]) == 7
          and any(len(v) > 1 for v in r3["byStratum"].values())
          and [d["degenerate"] for d in deg] == [False, False, True, False, False]
          and all(d["degenerate"] == d["qDividesN"] for d in deg))

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "rank_three_strata_are_not_orbits.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.rank-three-strata-not-orbits.v1",
                "valid": bool(ok),
                "whyLook": ("fe3e8fd identified the rank-2 orbit census with the "
                            "weight enumerator of the Cardinali-Giuzzi line "
                            "Symplectic Grassmann code; the same family is "
                            "defined at every rank, so the rank-3 member is a "
                            "free probe of ae04deb's claims, and it found two "
                            "things wrong with how they were phrased"),
                "correctionOne": ("ae04deb reported 'invariant symmetric forms = "
                                  "1' at n = 3 for q = 3 and 5 and left it there. "
                                  "The form exists at both, but at q = 3 its rank "
                                  "on ker(omega) is 13 of 14 -- DEGENERATE -- and "
                                  "the condition is exactly q | n, which at n = 3 "
                                  "singles out q = 3. So there the obstruction is "
                                  "STRICTLY STRONGER than stated: not merely no "
                                  "orthogonal geometry controlling the orbits, "
                                  "but no nondegenerate form at all. ae04deb's "
                                  "conclusion is unaffected because its decisive "
                                  "witnesses were exhibited at q = 5 as well, "
                                  "where the form is nondegenerate"),
                "degeneracyTable": deg,
                "correctionTwo": ("ae04deb said 'seven classes appear where rank "
                                  "2 has three', which is true and was worded as "
                                  "classes; the natural reading is that they are "
                                  "the orbits, and they are not. Computing the "
                                  "codeword weight for each stratum, at rank 2 "
                                  "every stratum carries exactly one weight, but "
                                  "at rank 3 the stratum (bivector rank 6, class "
                                  "zero) carries TWO. So (rank, class) is not a "
                                  "complete invariant and the true orbit count at "
                                  "rank 3 is AT LEAST EIGHT -- which again "
                                  "strengthens the no-go, the rank-3 structure "
                                  "being further from the rank-2 trichotomy than "
                                  "seven classes suggested"),
                "strata": strata,
                "theNegativeWorthRecording": ("at rank 3 neither an unbiased "
                                              "direct sample of 60,000 "
                                              "functionals nor a 150,000-sample "
                                              "stratum pass found a codeword of "
                                              "Cardinali-Giuzzi's minimum weight "
                                              "q^7 - q^3 = 2160; the smallest "
                                              "seen was 2187 = q^7. The direct "
                                              "sample is unbiased but covers only "
                                              "1.25% of 3^14. The stratum pass is "
                                              "WORSE: it indexes functionals by "
                                              "points through the invariant form, "
                                              "which at q = 3 is degenerate, so "
                                              "it reaches only a 13-dimensional "
                                              "image inside the 14-dimensional "
                                              "dual and CANNOT see two thirds of "
                                              "the codewords. The published "
                                              "minimum distance is not in doubt; "
                                              "what is recorded is that this "
                                              "harness does not reach it, and "
                                              "why"),
                "boundary": ("the degeneracy table is EXACT, computed as the rank "
                             "over GF(q) of the induced form restricted to "
                             "ker(omega). The rank-2 weight-by-stratum table is "
                             "EXHAUSTIVE. The rank-3 table is from 150,000 "
                             "samples and is therefore a LOWER bound on the "
                             "weights per stratum: a stratum shown with one "
                             "weight may carry more, so 'at least eight orbits' "
                             "is a lower bound, and the two weights found in "
                             "(6, zero) are what makes it strictly greater than "
                             "seven. No claim is made about the exact orbit count "
                             "at rank 3, about the weight enumerator of the "
                             "rank-3 code, or about q = 5 and 7 at rank 3, which "
                             "were not run for weights. Nothing here revises "
                             "fe3e8fd's attribution or touches tau_2"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
