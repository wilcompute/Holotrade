#!/usr/bin/env python3
"""
The Weyl lift is NOT a q = 3 accident: it gives a section at p = 3, 5 and 7,
and the normalising phase is 2^{-1} mod p at every one of them.

WHY ASK.  This session found q = 3 special at every turn -- the cost graph is a
quadrangle only there (424111b), the Schlafli configuration only there, the
doily exceptional in the other direction. c003b33 then found that the Clifford
lift needs no correction over the Weyl operator at q = 3, and explicitly
declined to claim that its phase matched any standard convention. Both of those
are questions about generality, and both are cheap to settle at n = 1.

THE ANSWER IS THAT THE CONSTRUCTION IS A FAMILY.

    p    Weyl t   Pauli   Clifford   quotient        lifts   generate   section
    3      2         9       216       24 = |SL(2,3)|    8       24       yes
    5      3        25      3000      120 = |SL(2,5)|   24      120       yes
    7      4        49     16464      336 = |SL(2,7)|   48      336       yes

At each prime exactly one t makes D_v = w^{t Q(v)} P_v a displacement operator
(powers along the ray, adjoint the opposite), the Gauss sums over it are all
verified to realise their transvections, and they generate a group of order
exactly |SL(2,p)| meeting the Paulis only in the identity. A section, three
times.

AND THE PHASE IS 2^{-1}.  The t values 2, 3, 4 are (p+1)/2, which is 2^{-1} mod
p since 2(p+1)/2 = p+1 = 1. So D_v = w^{2^{-1} Q(v)} P_v -- the standard
tau-normalised displacement operator. c003b33 declined to claim that
correspondence from a single prime; three primes with the same closed form is
enough to state it, and it is stated as a pattern across the three tested, not
as a proof for all p.

SO THE TWO HALVES OF THIS SESSION SPLIT CLEANLY.  The GEOMETRY is a q = 3
coincidence: the anticommutation graph is a generalized quadrangle only at
q = 3, merely strongly regular at 5, and not even that at 7. The COMPILER
construction is not: the displacement normalisation and the Gauss-sum lift work
at every prime tested. One is an accident of small parameters; the other is a
family.

A BUG WORTH RECORDING, THE THIRD OF ITS KIND.  The first run of this reported
Pauli groups of 18, 50 and 98 -- exactly twice 9, 25 and 49 -- and Clifford
orders in the hundreds of thousands. The cause was hashing unitaries by
.tobytes() after rounding: numpy produces -0.0, whose BYTES differ from 0.0
even though the two compare equal, so half the group was counted twice. Adding
0.0 fixes it. This is the third floating-point-hashing failure in this thread
(after the 205,571 artefact and the 120,017 one), each with a different
mechanism and each caught only because an expected integer was known in
advance.

SCOPE.  n = 1 at p = 3, 5, 7, exhaustively: the Clifford group is a complete
closure modulo global phase, orders are checked against p^2 and |SL(2,p)|, every
lift is verified to realise its transvection, and the section claim is order
plus trivial Pauli intersection. n = 2 is verified only at p = 3 (c003b33); the
two-ququint Clifford group was not built. No claim for p beyond 7, for
composite dimensions, or for characteristic 2 -- where the extension does not
split at all. tau_2 is untouched.
"""

import cmath
import itertools
import json
import os
import sys

import numpy as np

ROOT = r"C:\Repos\Holotrade"


def study(p):
    w = cmath.exp(2j * cmath.pi / p)
    X = np.zeros((p, p), dtype=complex)
    for j in range(p):
        X[(j + 1) % p, j] = 1
    Z = np.diag([w ** j for j in range(p)]).astype(complex)

    def P(v):
        return (np.linalg.matrix_power(X, v[0])
                @ np.linalg.matrix_power(Z, v[1]))

    def Q(v):
        return (v[0] * v[1]) % p

    def form(u, v):
        return (u[0] * v[1] - u[1] * v[0]) % p

    vecs = [v for v in itertools.product(range(p), repeat=2) if any(v)]

    good = []
    for t in range(p):
        def Dv(v, t=t):
            return (w ** ((t * Q(v)) % p)) * P(v)
        okp = all(np.allclose(np.linalg.matrix_power(Dv(v), k),
                              Dv(tuple((k * x) % p for x in v)), atol=1e-9)
                  for v in vecs for k in range(1, p)
                  if any((k * x) % p for x in v))
        oka = all(np.allclose(Dv(v).conj().T,
                              Dv(tuple((-x) % p for x in v)), atol=1e-9)
                  for v in vecs)
        if okp and oka:
            good.append(t)
    t = good[0]

    def D(v):
        return (w ** ((t * Q(v)) % p)) * P(v)

    def canon(U):
        V = U.flatten()
        i = int(np.argmax(np.abs(V) > 1e-9))
        V = V / V[i]
        # "+ 0.0" kills -0.0, whose bytes differ from 0.0 though they compare
        # equal; without it every group order came out doubled.
        return tuple((round(z.real, 6) + 0.0, round(z.imag, 6) + 0.0)
                     for z in V)

    def closure(gs):
        I = np.eye(p, dtype=complex)
        seen = {canon(I): I}
        fr = [I]
        while fr:
            nx = []
            for A in fr:
                for g in gs:
                    B = g @ A
                    k = canon(B)
                    if k not in seen:
                        seen[k] = B
                        nx.append(B)
            fr = nx
        return seen

    Pg = closure([P((1, 0)), P((0, 1))])
    F = np.array([[w ** (j * k) for k in range(p)] for j in range(p)],
                 dtype=complex) / np.sqrt(p)
    S = np.diag([w ** ((j * j) % p) for j in range(p)]).astype(complex)
    C = closure([P((1, 0)), P((0, 1)), F, S])
    sl = len(C) // len(Pg)

    def nm(v):
        i = next(k for k, x in enumerate(v) if x % p)
        z = pow(v[i] % p, -1, p)
        return tuple((z * x) % p for x in v)

    lifts, verified = [], 0
    for v in sorted({nm(x) for x in vecs}):
        for lam in range(1, p):
            a = (-pow(2 * lam, -1, p)) % p
            U = sum((w ** ((a * k * k) % p))
                    * np.linalg.matrix_power(D(v), k)
                    for k in range(p)) / np.sqrt(p)
            ok = True
            for x in vecs:
                tx = tuple((x[k] + lam * form(x, v) * v[k]) % p
                           for k in range(2))
                L = U @ P(x) @ U.conj().T
                R = P(tx)
                i0 = int(np.argmax(np.abs(R) > 1e-9))
                if not np.allclose(L, (L.flatten()[i0] / R.flatten()[i0]) * R,
                                   atol=1e-7):
                    ok = False
                    break
            verified += ok
            if ok:
                lifts.append(U)
    H = closure(lifts)
    inter = len(set(H) & set(Pg))
    return {"p": p, "weylT": good, "t": t, "tIsHalfInverse": t == pow(2, -1, p),
            "pauli": len(Pg), "clifford": len(C), "quotient": sl,
            "expectedQuotient": (p * p - 1) * p,
            "lifts": len(lifts), "verified": verified,
            "generated": len(H), "pauliIntersection": inter,
            "isASection": len(H) == sl and inter == 1}


def main():
    rows = [study(p) for p in (3, 5, 7)]

    print("THE WEYL LIFT IS q-GENERAL")
    print("=" * 72)
    print("  this session found q = 3 special at every turn, and c003b33")
    print("  declined to claim its phase matched a standard convention.")
    print("  Both are cheap to settle at n = 1.")
    print()
    print("   p   t   Pauli  Clifford  quotient   lifts  generate  section")
    for r in rows:
        print("  %2d   %d   %5d  %8d  %8d   %5d  %8d  %s"
              % (r["p"], r["t"], r["pauli"], r["clifford"], r["quotient"],
                 r["lifts"], r["generated"], r["isASection"]))
    print()
    print("  quotient = |SL(2,p)| = (p^2-1)p : %s"
          % all(r["quotient"] == r["expectedQuotient"] for r in rows))
    print("  every lift verified to realise its transvection: %s"
          % all(r["verified"] == r["lifts"] for r in rows))
    print("  exactly one t works at each p: %s"
          % all(len(r["weylT"]) == 1 for r in rows))
    print()
    print("  AND THE PHASE IS 2^{-1}: t = %s = (p+1)/2 = 2^{-1} mod p : %s"
          % ([r["t"] for r in rows],
             all(r["tIsHalfInverse"] for r in rows)))
    print("  so D_v = w^{2^{-1} Q(v)} P_v, the tau-normalised displacement")
    print("  operator. c003b33 declined that from one prime; three with the")
    print("  same closed form is enough to state it -- as a pattern across the")
    print("  three tested, not a proof for all p.")
    print()
    print("  SO THE TWO HALVES OF THIS SESSION SPLIT CLEANLY. The GEOMETRY is")
    print("  a q = 3 coincidence -- a quadrangle only at 3, merely strongly")
    print("  regular at 5, not even that at 7 (424111b). The COMPILER")
    print("  construction is not: it works at every prime tested. One is an")
    print("  accident of small parameters; the other is a family.")

    ok = (all(r["isASection"] for r in rows)
          and all(r["quotient"] == r["expectedQuotient"] for r in rows)
          and all(r["verified"] == r["lifts"] for r in rows)
          and all(r["tIsHalfInverse"] for r in rows)
          and all(len(r["weylT"]) == 1 for r in rows))

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "weyl_lift_is_q_general.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.weyl-lift-q-general.v1",
                "valid": bool(ok),
                "whyAsk": ("this session found q = 3 special at every turn, and "
                           "c003b33 explicitly declined to claim its phase "
                           "matched a standard convention; both are questions "
                           "about generality and both are cheap at n = 1"),
                "rows": rows,
                "theAnswer": ("the construction is a FAMILY: at each prime "
                              "exactly one t makes D_v a displacement operator, "
                              "every Gauss sum over it is verified to realise "
                              "its transvection, and they generate a group of "
                              "order exactly |SL(2,p)| meeting the Paulis only "
                              "in the identity"),
                "thePhaseIsHalfInverse": ("t = 2, 3, 4 at p = 3, 5, 7 is "
                                          "(p+1)/2 = 2^{-1} mod p, so "
                                          "D_v = w^{2^{-1} Q(v)} P_v is the "
                                          "tau-normalised displacement operator; "
                                          "c003b33 declined this from one prime, "
                                          "and three with the same closed form "
                                          "is enough to state it as a PATTERN "
                                          "across the three tested, not a proof "
                                          "for all p"),
                "theSessionSplitsCleanly": ("the GEOMETRY is a q = 3 coincidence "
                                            "-- the anticommutation graph is a "
                                            "generalized quadrangle only at "
                                            "q = 3, merely strongly regular at "
                                            "5, not even that at 7 (424111b). "
                                            "The COMPILER construction is not: "
                                            "the displacement normalisation and "
                                            "the Gauss-sum lift work at every "
                                            "prime tested. One is an accident of "
                                            "small parameters, the other a "
                                            "family"),
                "aBugWorthRecording": ("the first run reported Pauli groups of "
                                       "18, 50 and 98 -- exactly twice 9, 25 and "
                                       "49 -- because unitaries were hashed by "
                                       ".tobytes() after rounding, and numpy "
                                       "produces -0.0 whose BYTES differ from "
                                       "0.0 though they compare equal, so half "
                                       "the group was counted twice. Adding 0.0 "
                                       "fixes it. Third floating-point-hashing "
                                       "failure in this thread, after the "
                                       "205,571 and 120,017 artefacts, each with "
                                       "a different mechanism and each caught "
                                       "only because an expected integer was "
                                       "known in advance"),
                "boundary": ("n = 1 at p = 3, 5, 7 exhaustively: the Clifford "
                             "group is a complete closure modulo global phase, "
                             "orders checked against p^2 and |SL(2,p)|, every "
                             "lift verified to realise its transvection, and the "
                             "section claim is order plus trivial Pauli "
                             "intersection. n = 2 is verified only at p = 3 "
                             "(c003b33); the two-ququint Clifford group was NOT "
                             "built. No claim for p beyond 7, for composite "
                             "dimensions, or for characteristic 2 -- where the "
                             "extension does not split at all. tau_2 is "
                             "untouched"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
