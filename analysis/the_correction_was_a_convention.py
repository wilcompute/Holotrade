#!/usr/bin/env python3
"""
The correction was never an obstruction. It was my Pauli convention. With the
Weyl-normalised operator the plain Gauss sum is already the canonical section,
and every earlier failure in this thread has the same single cause.

THE QUESTION.  43bbfa1 ended with a correction in closed form,
c = -lam Q(v) with Q(v) = v0 v2 + v1 v3, applied as a Pauli multiplication. Q is
the X-dot-Z overlap -- exactly the quantity that separates the raw product
X^a Z^b from the symmetrised Weyl operator. So: is that correction a fact about
the Clifford group, or an artefact of writing Paulis as raw products?

IT IS AN ARTEFACT.  Put the phase into the operator, D_v = w^{t Q(v)} P_v, and
build the SAME Gauss sum over D_v instead of P_v:

    U_t(v, lam) = (1/sqrt 3) sum_k w^{lam k^2} D_v^k

    t = 0   lands on the section for 32 / 80      (the raw Pauli, 0fb6a0f)
    t = 1   lands on the section for 32 / 80
    t = 2   lands on the section for 80 / 80

At t = 2 the correction is not small, it is ABSENT. No Pauli multiplication, no
table, no closed form to apply -- the natural construction is already canonical.

AND t = 2 IS THE WEYL OPERATOR, BY ITS TWO DEFINING PROPERTIES.

    D_v^k = D_{kv}          t=0: 112/160   t=1: 112/160   t=2: 160/160
    D_v^dag = D_{-v}        t=0:  32/80    t=1:  32/80    t=2:  80/80

Only t = 2 is a genuine displacement operator: powers are displacements along
the same ray, and the adjoint is the opposite displacement. The raw product
X^a Z^b satisfies neither.

WHICH EXPLAINS EVERY FAILURE IN THIS THREAD, WITH ONE CAUSE.

  * 0fb6a0f's lifts were not a section (bf6d67a). They were Gauss sums over the
    WRONG operator.
  * Folding the correction into the sum as a shifted exponent
    w^{lam (j-c)^2} failed. It assumed P_v^c P_v^j = P_v^{c+j}, and P_v^k =
    P_{kv} holds only 112 times in 160. Over D_v it would have been fine.
  * 0c9ac42's table solved at the source instead of the image. A separate slip,
    but it was only needed because the convention forced a correction at all.

One convention choice removes all three.

THE FINAL FORM.

    D_v      =  w^{2 Q(v)} X^{v0} Z^{v2} tensor X^{v1} Z^{v3}
    U(v,lam) =  (1/sqrt 3) sum_{k=0}^{2} w^{lam k^2} D_v^k

and the eighty of these generate the section exactly: order 51,840, no Paulis.
A word from e05515f lifts termwise by this and the product is the canonical
Clifford of the target, with nothing to correct.

SCOPE.  The three t values are compared on the same regenerated section, and the
t = 2 family's group is generated exactly in F_3 with its order and Pauli count
computed. The two Weyl properties are checked on every vector and every power,
not sampled. That t = 2 matches some particular textbook's displacement-operator
convention is NOT claimed -- what is established is that this phase, and not the
raw product, is the one satisfying the two properties and making the lift
canonical. Only n = 2, q = 3. tau_2 is untouched.
"""

import cmath
import itertools
import json
import os
import sys

import numpy as np

ROOT = r"C:\Repos\Holotrade"
P3, D = 3, 4
W = cmath.exp(2j * cmath.pi / P3)


def main():
    X1 = np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]], dtype=complex)
    Z1 = np.diag([1, W, W ** 2]).astype(complex)

    def P(v):
        A = np.linalg.matrix_power(X1, v[0]) @ np.linalg.matrix_power(Z1, v[2])
        B = np.linalg.matrix_power(X1, v[1]) @ np.linalg.matrix_power(Z1, v[3])
        return np.kron(A, B)

    def Q(v):
        return (v[0] * v[2] + v[1] * v[3]) % P3

    def Dw(v, t):
        return (W ** ((t * Q(v)) % P3)) * P(v)

    vecs = [v for v in itertools.product(range(P3), repeat=D) if any(v)]
    vi = {v: i for i, v in enumerate(vecs)}
    basis = [(a, b) for a in range(P3) for b in range(P3)]
    bi = {x: i for i, x in enumerate(basis)}

    def encode(U):
        Ud = U.conj().T
        img = {}
        for x in vecs:
            L = U @ P(x) @ Ud
            for y in vecs:
                R = P(y)
                i0 = int(np.argmax(np.abs(R) > 1e-9))
                z = L.flatten()[i0] / R.flatten()[i0]
                if np.allclose(L, z * R, atol=1e-7):
                    img[x] = (y, int(round((cmath.phase(z) % (2 * cmath.pi))
                                           / (2 * cmath.pi / P3))) % P3)
                    break
            else:
                return None
        S = [[0] * D for _ in range(D)]
        for j in range(D):
            e = tuple(1 if k == j else 0 for k in range(D))
            for i in range(D):
                S[i][j] = img[e][0][i]
        return (tuple(map(tuple, S)), tuple(img[x][1] for x in vecs))

    # --- the section
    gens = []
    for M in itertools.product(range(P3), repeat=4):
        if (M[0] * M[3] - M[1] * M[2]) % P3 == 0:
            continue
        U = np.zeros((9, 9), dtype=complex)
        for x in basis:
            y = ((M[0] * x[0] + M[1] * x[1]) % P3,
                 (M[2] * x[0] + M[3] * x[1]) % P3)
            U[bi[y], bi[x]] = 1
        gens.append(U)
    for a in range(P3):
        for b in range(P3):
            for c in range(P3):
                if a == b == c == 0:
                    continue
                gens.append(np.diag(
                    [W ** ((a * x[0] * x[0] + 2 * b * x[0] * x[1]
                            + c * x[1] * x[1]) % P3) for x in basis]
                ).astype(complex))
    F1 = np.array([[W ** (j * k) for k in range(P3)] for j in range(P3)],
                  dtype=complex) / np.sqrt(P3)
    I3 = np.eye(P3, dtype=complex)
    gens += [np.kron(F1, I3), np.kron(I3, F1), np.kron(F1, F1)]
    enc = [e for e in (encode(U) for U in gens) if e is not None]

    def apply(S, x):
        return tuple(sum(S[i][k] * x[k] for k in range(D)) % P3
                     for i in range(D))

    def mul(g1, g2):
        S1, f1 = g1
        S2, f2 = g2
        S = tuple(tuple(sum(S1[i][k] * S2[k][j] for k in range(D)) % P3
                        for j in range(D)) for i in range(D))
        return (S, tuple((f2[vi[x]] + f1[vi[apply(S2, x)]]) % P3 for x in vecs))

    IDS = tuple(tuple(1 if i == j else 0 for j in range(D)) for i in range(D))
    ID = (IDS, tuple([0] * len(vecs)))
    seen, fr = {ID}, [ID]
    while fr:
        nx = []
        for a in fr:
            for g in enc:
                b = mul(g, a)
                if b not in seen:
                    seen.add(b)
                    nx.append(b)
        fr = nx
    sec = {S: f for S, f in seen}

    def nm(v):
        i = next(k for k, x in enumerate(v) if x % P3)
        z = pow(v[i] % P3, -1, P3)
        return tuple((z * x) % P3 for x in v)

    reps = sorted({nm(x) for x in vecs})

    # --- the three conventions
    lands, weyl_pow, weyl_adj = {}, {}, {}
    encs = {}
    for t in range(P3):
        m, e2 = 0, []
        for v in reps:
            for lam in (1, 2):
                U = sum((W ** ((lam * k * k) % P3))
                        * np.linalg.matrix_power(Dw(v, t), k)
                        for k in range(P3)) / np.sqrt(P3)
                e = encode(U)
                if e is None:
                    continue
                e2.append(e)
                if e[1] == sec[e[0]]:
                    m += 1
        lands[t] = m
        encs[t] = e2
        ok = tot = 0
        for v in vecs:
            for k in (1, 2):
                kv = tuple((k * x) % P3 for x in v)
                if not any(kv):
                    continue
                tot += 1
                ok += np.allclose(np.linalg.matrix_power(Dw(v, t), k),
                                  Dw(kv, t), atol=1e-9)
        weyl_pow[t] = (ok, tot)
        weyl_adj[t] = (sum(1 for v in vecs
                           if np.allclose(Dw(v, t).conj().T,
                                          Dw(tuple((-x) % P3 for x in v), t),
                                          atol=1e-9)), len(vecs))

    best = max(lands, key=lambda t: lands[t])
    seen2, fr, capped = {ID}, [ID], False
    while fr and not capped:
        nx = []
        for x in fr:
            for g in encs[best]:
                b = mul(g, x)
                if b not in seen2:
                    seen2.add(b)
                    nx.append(b)
            if len(seen2) > 120000:
                capped = True
                break
        fr = nx
    pl = sum(1 for g in seen2 if g[0] == IDS and any(g[1]))
    is_sec = (not capped and len(seen2) == 51840 and pl == 0)

    print("THE CORRECTION WAS A CONVENTION")
    print("=" * 72)
    print("  D_v = w^{t Q(v)} P_v ,  U_t = (1/sqrt3) sum_k w^{lam k^2} D_v^k")
    print()
    for t in range(P3):
        print("     t=%d  lands on the section  %2d / 80" % (t, lands[t]))
    print("  At t=%d the correction is not small, it is ABSENT." % best)
    print()
    print("  and t=%d is the WEYL operator, by its two defining properties:" % best)
    print("     D_v^k = D_{kv}     " + "  ".join(
        "t=%d: %d/%d" % (t, weyl_pow[t][0], weyl_pow[t][1]) for t in range(P3)))
    print("     D_v^dag = D_{-v}   " + "  ".join(
        "t=%d: %d/%d" % (t, weyl_adj[t][0], weyl_adj[t][1]) for t in range(P3)))
    print()
    print("  WHICH EXPLAINS EVERY FAILURE IN THIS THREAD, WITH ONE CAUSE:")
    print("   * 0fb6a0f's lifts were not a section -- Gauss sums over the")
    print("     WRONG operator.")
    print("   * folding the correction in as w^{lam (j-c)^2} failed -- it")
    print("     assumed P_v^c P_v^j = P_v^{c+j}, and P_v^k = P_{kv} holds only")
    print("     %d of %d times. Over D_v it would have been fine."
          % (weyl_pow[0][0], weyl_pow[0][1]))
    print("   * 0c9ac42 solved at the source not the image -- a separate slip,")
    print("     but only needed because the convention forced a correction.")
    print()
    print("  FINAL FORM:")
    print("     D_v      = w^{2 Q(v)} X^{v0}Z^{v2} tensor X^{v1}Z^{v3}")
    print("     U(v,lam) = (1/sqrt3) sum_k w^{lam k^2} D_v^k")
    print("  the eighty generate: order %d, Paulis %d, IS A SECTION %s"
          % (len(seen2), pl, is_sec))

    ok_all = (lands[2] == 80 and lands[0] == 32 and lands[1] == 32
              and best == 2 and weyl_pow[2] == (160, 160)
              and weyl_adj[2] == (80, 80) and is_sec
              and len(seen) == 51840)

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "correction_was_a_convention.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.correction-was-a-convention.v1",
                "valid": bool(ok_all),
                "theQuestion": ("43bbfa1 ended with c = -lam Q(v) applied as a "
                                "Pauli multiplication; Q is the X-dot-Z overlap, "
                                "exactly what separates the raw product X^a Z^b "
                                "from the symmetrised Weyl operator. Is the "
                                "correction a fact about the Clifford group or "
                                "an artefact of the Pauli convention?"),
                "answer": "an artefact",
                "landsOnSection": {str(t): lands[t] for t in lands},
                "weylProperties": {
                    "powersAreDisplacements": {
                        str(t): "%d/%d" % weyl_pow[t] for t in weyl_pow},
                    "adjointIsOpposite": {
                        str(t): "%d/%d" % weyl_adj[t] for t in weyl_adj},
                    "reading": ("only t = 2 is a genuine displacement operator: "
                                "powers are displacements along the same ray and "
                                "the adjoint is the opposite displacement; the "
                                "raw product X^a Z^b satisfies neither"),
                },
                "explainsEveryFailure": [
                    ("0fb6a0f's lifts were not a section (bf6d67a): Gauss sums "
                     "over the WRONG operator"),
                    ("folding the correction in as w^{lam (j-c)^2} failed: it "
                     "assumed P_v^c P_v^j = P_v^{c+j}, and P_v^k = P_{kv} holds "
                     "only %d of %d times; over D_v it would have been fine"
                     % (weyl_pow[0][0], weyl_pow[0][1])),
                    ("0c9ac42 solved at the source not the image: a separate "
                     "slip, but only needed because the convention forced a "
                     "correction at all"),
                ],
                "finalForm": {
                    "operator": ("D_v = w^{2 Q(v)} X^{v0} Z^{v2} tensor "
                                 "X^{v1} Z^{v3},  Q(v) = v0 v2 + v1 v3"),
                    "lift": "U(v,lam) = (1/sqrt 3) sum_k w^{lam k^2} D_v^k",
                    "noCorrection": True,
                    "groupOrder": len(seen2),
                    "pauliCount": pl,
                    "isASection": bool(is_sec),
                },
                "boundary": ("the three t values are compared on the same "
                             "regenerated section; the t = 2 family's group is "
                             "generated exactly in F_3 with order and Pauli "
                             "count computed. The two Weyl properties are "
                             "checked on every vector and every power, not "
                             "sampled. That t = 2 matches a particular "
                             "textbook's displacement convention is NOT claimed "
                             "-- what is established is that this phase, not the "
                             "raw product, satisfies the two properties and "
                             "makes the lift canonical. Only n = 2, q = 3. "
                             "tau_2 is untouched"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
