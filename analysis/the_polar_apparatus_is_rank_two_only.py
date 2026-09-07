#!/usr/bin/env python3
"""
The whole polar-incidence apparatus is rank-two only, and the obstruction is
that the Pfaffian on Lambda^2(F^2n) has DEGREE n. At n = 3 it is a cubic and
the quadratic form stops controlling the orbits.

WHY ASK.  64e6406, ba74506, c9e6be7 and aa42b38 all run on one mechanism: the
five-space W = ker(omega) inside Lambda^2(F_q^4) carries an Sp-invariant
quadratic form whose three orbits on P(W) are the 40 isotropic, 45 square and 36
nonsquare points, and every result -- the exterior-square map, the 24/15 tight
frames, the octets, the blocker labels -- is built on that partition. The
architecture track works at Sp(6,2) and Sp(8,2). So: does the mechanism lift?

THE FIRST GUESS WAS WRONG, AND INSTRUCTIVELY.  The natural conjecture is that
rank 3 has no invariant form at all. It does. Solving g^T M g = M over the whole
generated group gives a one-dimensional space of invariant symmetric bilinear
forms on ker(omega) at BOTH ranks:

    Sp(4,q)  dim ker(omega) =  5   invariant symmetric forms = 1
    Sp(6,q)  dim ker(omega) = 14   invariant symmetric forms = 1

(the rank-2 answer being 1 is the positive control: it is the Pfaffian, and a
wrong generating set would have returned a larger space). The form at rank 3 is
the one induced by the symplectic form itself,
<a^b, c^d> = <a,c><b,d> - <a,d><b,c>, and it exists at every rank. So the
obstruction is not the absence of a quadratic form.

THE OBSTRUCTION IS THE DEGREE OF THE PFAFFIAN.  Lambda^{2n}(V) is
one-dimensional, so b^n is a scalar and the Pfaffian is a form of DEGREE n on
Lambda^2(V). At n = 2 it is QUADRATIC -- and a quadratic invariant is exactly an
orthogonal geometry, which is why Sp(4,q) lands on O(5,q) at all. At n = 3 it is
CUBIC, and a cubic hypersurface in PG(13,q) is not a quadric. Degree 2 happens
once.

WHAT THAT DOES TO THE ORBITS.  Stratify P(ker omega) by two invariants: the rank
of the bivector as an alternating form, and the class of the invariant quadratic
form (zero / square / nonsquare).

    n = 2, exhaustively over all of ker(omega):
        classes realised   (2,zero), (4,square), (4,nonsquare)      3
        rank is a FUNCTION of the Q-class                          yes

    n = 3:
        classes realised   (2,zero), (4,zero), (4,sq), (4,nsq),
                           (6,zero), (6,sq), (6,nsq)                7
        rank is a function of the Q-class                           NO

At n = 2 the rank stratification and the quadratic form carry the SAME
information -- rank 2 is exactly Q = 0 (decomposable bivectors, the lines of
PG(3,q), i.e. the 40 W33 lines) and rank 4 is exactly Q =/= 0, split by square
nonzero class into 45 and 36. That coincidence is the 40/45/36 partition. At n = 3 they
are independent: Q = 0 contains ranks 2, 4 AND 6, and each nonzero class
contains ranks 4 and 6. Explicit witness pairs are recorded in the certificate
-- same Q-class, different rank -- so this is a demonstration, not a statistic.

A LABEL-CONVENTION WARNING, RECORDED RATHER THAN SMOOTHED OVER.  The
square/nonsquare NAMES above follow the induced form used here, which differs
from the Pfaffian used in ba74506 and c9e6be7 by a scalar whose square class
varies with q and with the sign convention in J. So the two names SWAP between
files: at q = 3 and 5 the q^2(q^2+1)/2 orbit is called "nonsquare" here and
"square" there, while at q = 7 they agree. The partition is identical either
way, and the certificate states it convention-free as

    (q+1)(q^2+1)  /  q^2(q^2+1)/2  /  q^2(q^2-1)/2
    40/45/36        156/325/300      400/1225/1176

which is checked against those closed forms at every q. Nothing here or earlier
depends on which orbit gets which name, but an unexplained swap between
certificates is exactly the kind of convention artefact that cost this session a
wrong correction table earlier, so it is named.

AND THE GROUP ORDERS SAY THE SAME THING.  At n = 2, |Sp(4,q)| = |SO(5,q)|, so
the map onto the orthogonal group can be, and is, surjective, and Witt's theorem
then makes the Sp-orbits equal to the orthogonal ones. At n = 3, Sp(6) has
dimension 21 sitting inside SO(14) of dimension 91; the image is a tiny subgroup
and its orbits are strictly finer than the quadric's. There is no rank-3 analogue
of "the three orbits", so there is nothing for D, C, the octets or the (c,m)
labels to be defined on.

SO THE PROGRAMME HAS A CEILING, AND IT IS EXACTLY B2 = C2.  Every q-general
result this session established is general in q and rigid in RANK. That is worth
stating precisely, because the natural next move -- push the polar machinery to
Sp(6,q) for the architecture track -- cannot work, and now fails for a reason
rather than for lack of effort.

ONE THING WORTH FLAGGING, NOT CLAIMING.  The corpus's architecture layer already
carries a degree-2 / degree-3 split: "gates = deg-2 symplectic + deg-3 E6 cubic".
Here the same split appears as the degree of the Pfaffian, quadratic at rank 2
and cubic at rank 3. Whether those two degree-3 objects are the same cubic is NOT
investigated here and no identification is asserted; it is recorded as a question
because the coincidence of degree is the kind of thing this corpus has twice
found to be substantive and twice found to be nothing.

SCOPE.  The invariant-form dimensions are computed at q = 3, 5, 7 for n = 2 and
q = 3, 5 for n = 3, against a generated group (basis transvections plus random
ones); the rank-2 value of 1 is the control that the generating set is adequate,
and a deficient set would inflate, never deflate, the answer. The n = 2 orbit
table is EXHAUSTIVE over ker(omega). The n = 3 table is from sampling, but the
claim that rank is not a function of Q-class is carried by explicit witness pairs
that are exhibited and re-verified, not by the sample. Group dimensions are quoted
as classical. Nothing here concerns q even, n > 3, or tau_2, and nothing here
retracts any earlier result: they are all still q-general, which is a different
axis from rank.
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


def setup(n, q):
    d = 2 * n
    PR = [(i, j) for i in range(d) for j in range(i + 1, d)]
    J = np.zeros((d, d), dtype=np.int64)
    for i in range(n):
        J[i, n + i] = 1
        J[n + i, i] = q - 1
    w = np.array([J[i, j] for (i, j) in PR], dtype=np.int64) % q
    G = np.zeros((len(PR), len(PR)), dtype=np.int64)
    for k, (i, j) in enumerate(PR):
        for l, (a, b) in enumerate(PR):
            G[k, l] = (J[i, a] * J[j, b] - J[i, b] * J[j, a]) % q
    return d, PR, J, w, G


def bivrank(b, d, PR, q):
    M = np.zeros((d, d), dtype=np.int64)
    for k, (i, j) in enumerate(PR):
        M[i, j] = b[k] % q
        M[j, i] = (-b[k]) % q
    A = M % q
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


def qclass(b, G, q):
    sq = {(x * x) % q for x in range(1, q)}
    v = int(b @ G @ b) % q
    return "zero" if v == 0 else ("square" if v in sq else "nonsquare")


def invariant_forms(n, q, ngen=6, seed=0):
    d, PR, J, w, _ = setup(n, q)
    rnd = random.Random(seed)
    vs = [np.eye(d, dtype=np.int64)[i] for i in range(d)]
    vs += [np.array([rnd.randrange(q) for _ in range(d)], dtype=np.int64)
           for _ in range(ngen)]
    gens = [(np.eye(d, dtype=np.int64) - np.outer(v, (J @ v))) % q
            for v in vs if v.any()]

    def wedge(g):
        idx = {p: k for k, p in enumerate(PR)}
        A = np.zeros((len(PR), len(PR)), dtype=np.int64)
        for c, (i, j) in enumerate(PR):
            gi, gj = g[:, i], g[:, j]
            for (a, b) in PR:
                A[idx[(a, b)], c] = (gi[a] * gj[b] - gi[b] * gj[a]) % q
        return A % q

    ns = DomainMatrix.from_Matrix(
        Matrix(w.reshape(1, -1).tolist())).convert_to(GF(q)).nullspace()
    Kb = np.array(ns.to_Matrix().tolist(), dtype=np.int64) % q
    dk = Kb.shape[0]
    KT = DomainMatrix.from_Matrix(Matrix(Kb.T.tolist())).convert_to(GF(q))
    restricted = []
    for g in gens:
        img = (Kb @ wedge(g).T) % q
        sol = []
        for r in img:
            b = DomainMatrix.from_Matrix(
                Matrix(r.reshape(-1, 1).tolist())).convert_to(GF(q))
            sol.append([int(t) % q for t in KT._solve(b)[0].to_Matrix()])
        restricted.append(np.array(sol, dtype=np.int64) % q)

    pairs = [(i, j) for i in range(dk) for j in range(i, dk)]
    pidx = {p: k for k, p in enumerate(pairs)}
    rows = []
    for C in restricted:
        for (a, b) in pairs:
            row = [0] * len(pairs)
            for i in range(dk):
                for j in range(dk):
                    coef = (C[i, a] * C[j, b]) % q
                    if not coef:
                        continue
                    key = (i, j) if i <= j else (j, i)
                    row[pidx[key]] = (row[pidx[key]] + coef) % q
            row[pidx[(a, b)]] = (row[pidx[(a, b)]] - 1) % q
            rows.append(row)
    R = DomainMatrix.from_Matrix(Matrix(rows)).convert_to(GF(q))
    return dk, len(R.nullspace().to_Matrix().tolist())


def orbits_exhaustive(n, q):
    d, PR, J, w, G = setup(n, q)
    ns = DomainMatrix.from_Matrix(
        Matrix(w.reshape(1, -1).tolist())).convert_to(GF(q)).nullspace()
    Kb = np.array(ns.to_Matrix().tolist(), dtype=np.int64) % q
    cls = {}
    for coeffs in itertools.product(range(q), repeat=Kb.shape[0]):
        b = (np.array(coeffs, dtype=np.int64) @ Kb) % q
        if not b.any():
            continue
        cls.setdefault((bivrank(b, d, PR, q), qclass(b, G, q)), 0)
        cls[(bivrank(b, d, PR, q), qclass(b, G, q))] += 1
    return cls


def orbits_sampled(n, q, samples, seed=0):
    d, PR, J, w, G = setup(n, q)
    rnd = random.Random(seed)
    cls, wit = {}, {}
    for _ in range(samples):
        b = np.array([rnd.randrange(q) for _ in PR], dtype=np.int64)
        if not b.any() or (b * w).sum() % q:
            continue
        k = (bivrank(b, d, PR, q), qclass(b, G, q))
        cls[k] = cls.get(k, 0) + 1
        wit.setdefault(k, [int(x) for x in b])
    return cls, wit


def main():
    forms = []
    for (n, q) in [(2, 3), (2, 5), (2, 7), (3, 3), (3, 5)]:
        dk, dim = invariant_forms(n, q)
        forms.append({"n": n, "q": q, "dimKerOmega": dk,
                      "invariantSymmetricForms": dim,
                      "pfaffianDegree": n,
                      "lambdaTopIsOneDimensional": True})

    ex = {}
    for q in (3, 5, 7):
        c = orbits_exhaustive(2, q)
        ex[q] = {"%d,%s" % k: v for k, v in sorted(c.items())}

    sa, witnesses = {}, {}
    for q in (3, 5):
        c, w = orbits_sampled(3, q, 400000)
        sa[q] = {"%d,%s" % k: v for k, v in sorted(c.items())}
        witnesses[q] = w

    # decisive witnesses: same Q-class, different bivector rank, re-verified
    proof = {}
    for q in (3, 5):
        d, PR, J, w, G = setup(3, q)
        byq = {}
        for (r, cl), b in witnesses[q].items():
            byq.setdefault(cl, {})[r] = b
        pick = {}
        for cl, rs in byq.items():
            if len(rs) >= 2:
                a, bb = sorted(rs)[0], sorted(rs)[-1]
                va, vb = np.array(rs[a]), np.array(rs[bb])
                pick[cl] = {
                    "rankA": a, "vectorA": rs[a],
                    "rankB": bb, "vectorB": rs[bb],
                    "recheckRankA": bivrank(va, d, PR, q),
                    "recheckRankB": bivrank(vb, d, PR, q),
                    "recheckClassA": qclass(va, G, q),
                    "recheckClassB": qclass(vb, G, q),
                    "sameQclass": qclass(va, G, q) == qclass(vb, G, q),
                    "differentRank": bivrank(va, d, PR, q) != bivrank(vb, d, PR, q),
                }
        proof[q] = pick

    def rankIsFunctionOfQ(table):
        byq = {}
        for k in table:
            r, cl = k.split(",")
            byq.setdefault(cl, set()).add(int(r))
        return all(len(v) == 1 for v in byq.values())

    n2ok = all(rankIsFunctionOfQ(ex[q]) for q in ex)
    n3ok = all(not rankIsFunctionOfQ(sa[q]) for q in sa)

    print("THE POLAR APPARATUS IS RANK-TWO ONLY")
    print("=" * 72)
    print("  Everything from 64e6406 to aa42b38 runs on one mechanism: the")
    print("  five-space ker(omega) in Lambda^2(F_q^4) carries an invariant")
    print("  QUADRATIC form whose three orbits are 40/45/36. Does it lift?")
    print()
    print("  The first guess -- no invariant form at rank 3 -- is WRONG:")
    print("     n  q   dim ker(omega)   invariant symmetric forms")
    for f in forms:
        print("     %d %2d        %3d                  %d"
              % (f["n"], f["q"], f["dimKerOmega"],
                 f["invariantSymmetricForms"]))
    print("  (the rank-2 value 1 is the control -- a bad generating set would")
    print("  INFLATE this, never deflate it). The rank-3 form is the one")
    print("  induced by <,> and exists at every rank.")
    print()
    print("  THE OBSTRUCTION IS THE PFAFFIAN'S DEGREE. Lambda^{2n} is one-")
    print("  dimensional, so the Pfaffian is a form of DEGREE n on Lambda^2.")
    print("  n = 2 -> QUADRATIC -> an orthogonal geometry -> O(5,q).")
    print("  n = 3 -> CUBIC -> a cubic hypersurface, not a quadric.")
    print("  Degree 2 happens once.")
    print()
    print("  Stratify by (bivector rank, Q-class):")
    for q in ex:
        print("     n=2 q=%d EXHAUSTIVE: %s" % (q, sorted(ex[q])))
    for q in sa:
        print("     n=3 q=%d sampled:    %s" % (q, sorted(sa[q])))
    print("     rank is a function of the Q-class at n=2: %s" % n2ok)
    print("     rank is a function of the Q-class at n=3: %s" % (not n3ok))
    print()
    print("  At n = 2 rank 2 IS Q = 0 (the decomposable bivectors -- the lines")
    print("  of PG(3,q), i.e. the 40 W33 lines) and rank 4 IS Q =/= 0, split")
    print("  45/36 by square class. That coincidence is the whole partition.")
    print("  At n = 3 they are independent, and the witnesses below are")
    print("  explicit pairs with the SAME Q-class and DIFFERENT rank:")
    for q in proof:
        for cl, w in sorted(proof[q].items()):
            print("     q=%d  Q-class %-9s ranks %d and %d   verified %s"
                  % (q, cl, w["rankA"], w["rankB"],
                     w["sameQclass"] and w["differentRank"]))
    print()
    print("  So there is no rank-3 analogue of 'the three orbits', and hence")
    print("  nothing for D, C, the octets or the (c,m) labels to live on.")
    print("  The programme's ceiling is exactly B2 = C2.")

    sizesOK = all(
        sorted([ex[q]["2,zero"] // (q - 1),
                ex[q]["4,square"] // (q - 1),
                ex[q]["4,nonsquare"] // (q - 1)])
        == sorted([(q + 1) * (q * q + 1), q * q * (q * q + 1) // 2,
                   q * q * (q * q - 1) // 2])
        for q in ex)
    print()
    print("  LABEL CONVENTION: the square/nonsquare NAMES here follow the")
    print("  induced form <a^b,c^d>, which differs from ba74506's Pfaffian by")
    print("  a scalar whose square class varies with q, so the two names swap")
    print("  between files at q = 3 and 5 and agree at q = 7. The PARTITION is")
    print("  identical -- sizes match (q+1)(q^2+1) / q^2(q^2+1)/2 /")
    print("  q^2(q^2-1)/2 at every q: %s" % sizesOK)

    ok = (sizesOK and n2ok and n3ok
          and all(f["invariantSymmetricForms"] == 1 for f in forms)
          and all(len(ex[q]) == 3 for q in ex)
          and all(len(sa[q]) == 7 for q in sa)
          and all(w["sameQclass"] and w["differentRank"]
                  for q in proof for w in proof[q].values())
          and len(proof[3]) >= 2 and len(proof[5]) >= 2)

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "polar_apparatus_rank_two_only.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.polar-apparatus-rank-two-only.v1",
                "valid": bool(ok),
                "whyAsk": ("64e6406, ba74506, c9e6be7 and aa42b38 all run on one "
                           "mechanism -- the five-space ker(omega) in "
                           "Lambda^2(F_q^4) carrying an Sp-invariant QUADRATIC "
                           "form whose three orbits on P(W) are the 40 isotropic, "
                           "45 square and 36 nonsquare points -- and the "
                           "architecture track works at Sp(6,2) and Sp(8,2), so "
                           "whether the mechanism lifts in RANK is the load-"
                           "bearing question"),
                "theFirstGuessWasWrong": ("the natural conjecture, that rank 3 "
                                          "has no invariant form at all, is "
                                          "FALSE: the space of invariant "
                                          "symmetric bilinear forms on ker(omega) "
                                          "is one-dimensional at BOTH ranks. The "
                                          "rank-3 form is the one induced by the "
                                          "symplectic form, <a^b,c^d> = "
                                          "<a,c><b,d> - <a,d><b,c>, and it exists "
                                          "at every rank. The obstruction is not "
                                          "the absence of a quadratic form"),
                "invariantForms": forms,
                "theObstruction": ("Lambda^{2n}(V) is one-dimensional, so b^n is "
                                   "a scalar and the Pfaffian is a form of DEGREE "
                                   "n on Lambda^2(V). At n = 2 it is QUADRATIC, "
                                   "and a quadratic invariant is exactly an "
                                   "orthogonal geometry -- which is why Sp(4,q) "
                                   "lands on O(5,q) at all. At n = 3 it is CUBIC, "
                                   "and a cubic hypersurface in PG(13,q) is not a "
                                   "quadric. Degree 2 happens once"),
                "orbitsExhaustiveRank2": ex,
                "orbitsSampledRank3": sa,
                "orbitSizesRank2Projective": {
                    str(q): {"isotropic": ex[q]["2,zero"] // (q - 1),
                             "big": max(ex[q]["4,square"],
                                        ex[q]["4,nonsquare"]) // (q - 1),
                             "small": min(ex[q]["4,square"],
                                          ex[q]["4,nonsquare"]) // (q - 1),
                             "closedForms": [(q + 1) * (q * q + 1),
                                             q * q * (q * q + 1) // 2,
                                             q * q * (q * q - 1) // 2]}
                    for q in ex},
                "aLabelConventionWarning": ("the square/nonsquare NAMES in "
                                            "orbitsExhaustiveRank2 follow the "
                                            "induced form <a^b,c^d> = "
                                            "<a,c><b,d> - <a,d><b,c> used here, "
                                            "which differs from the Pfaffian used "
                                            "in ba74506 and c9e6be7 by a scalar "
                                            "whose square class varies with q and "
                                            "with the sign convention in J. So "
                                            "the two NAMES swap between files -- "
                                            "at q = 3 and 5 the q^2(q^2+1)/2 "
                                            "orbit is labelled 'nonsquare' here "
                                            "and 'square' there, while at q = 7 "
                                            "they agree. The PARTITION is "
                                            "identical either way, and "
                                            "orbitSizesRank2Projective states it "
                                            "convention-free as "
                                            "(q+1)(q^2+1) / q^2(q^2+1)/2 / "
                                            "q^2(q^2-1)/2 = 40/45/36, "
                                            "156/325/300, 400/1225/1176. Nothing "
                                            "in this file or the earlier ones "
                                            "depends on which orbit gets which "
                                            "name, but the flip is recorded "
                                            "because an unexplained swap between "
                                            "certificates is exactly the kind of "
                                            "convention artefact that cost this "
                                            "session a wrong correction table "
                                            "earlier"),
                "rankIsFunctionOfQclass": {"n2": n2ok, "n3": not n3ok},
                "whatThatDoesToTheOrbits": ("at n = 2 the rank stratification and "
                                            "the quadratic form carry the SAME "
                                            "information: rank 2 is exactly "
                                            "Q = 0, the decomposable bivectors, "
                                            "i.e. the lines of PG(3,q) and so the "
                                            "40 W33 lines; rank 4 is exactly "
                                            "Q =/= 0, split 45/36 by square "
                                            "class. That coincidence IS the "
                                            "40/45/36 partition. At n = 3 they "
                                            "are independent -- Q = 0 contains "
                                            "ranks 2, 4 AND 6, and each nonzero "
                                            "class contains ranks 4 and 6 -- so "
                                            "seven classes appear where rank 2 "
                                            "has three"),
                "decisiveWitnesses": proof,
                "groupOrdersSayTheSame": ("at n = 2, |Sp(4,q)| = |SO(5,q)|, so the "
                                          "map onto the orthogonal group can be "
                                          "and is surjective and Witt's theorem "
                                          "makes the Sp-orbits equal to the "
                                          "orthogonal ones; at n = 3, Sp(6) has "
                                          "dimension 21 inside SO(14) of "
                                          "dimension 91, the image is a tiny "
                                          "subgroup, and its orbits are strictly "
                                          "finer than the quadric's"),
                "theCeilingIsB2equalsC2": ("every q-general result this session "
                                           "established is general in q and RIGID "
                                           "IN RANK; the natural next move, "
                                           "pushing the polar machinery to "
                                           "Sp(6,q) for the architecture track, "
                                           "cannot work, and now fails for a "
                                           "reason rather than for lack of "
                                           "effort"),
                "flaggedNotClaimed": ("the corpus's architecture layer already "
                                      "carries a degree-2 / degree-3 split -- "
                                      "'gates = deg-2 symplectic + deg-3 E6 "
                                      "cubic' -- and here the same split appears "
                                      "as the degree of the Pfaffian, quadratic "
                                      "at rank 2 and cubic at rank 3. Whether "
                                      "those two degree-3 objects are the SAME "
                                      "cubic is NOT investigated and no "
                                      "identification is asserted; it is recorded "
                                      "as a question, because a coincidence of "
                                      "degree is the kind of thing this corpus "
                                      "has twice found substantive and twice "
                                      "found to be nothing"),
                "boundary": ("invariant-form dimensions are computed at q = 3,5,7 "
                             "for n = 2 and q = 3,5 for n = 3 against a GENERATED "
                             "group (basis transvections plus random ones); the "
                             "rank-2 value of 1 is the control that the "
                             "generating set is adequate, and a deficient set "
                             "would inflate, never deflate, the answer. The n = 2 "
                             "orbit table is EXHAUSTIVE over ker(omega); the "
                             "n = 3 table is SAMPLED, but the claim that rank is "
                             "not a function of Q-class is carried by the "
                             "explicit witness pairs, which are exhibited and "
                             "re-verified, not by the sample. Group dimensions "
                             "are quoted as classical. Nothing here concerns q "
                             "even, n > 3, or tau_2, and nothing here retracts "
                             "any earlier result: those are q-general, which is a "
                             "different axis from rank"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
