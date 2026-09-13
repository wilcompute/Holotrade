#!/usr/bin/env python3
"""
The 90 cost anomalies of Sp(4,3) are the LOCAL CHARGE CONJUGATIONS of two
qutrits -- C on one factor of one of the 45 tensor factorisations -- and the
91st, the centre -I, is global charge conjugation C (x) C.

WHAT IS ALREADY OURS.  the_cost_anomalies_are_the_tritangent_structure.py:
transvection length equals residue in Sp(4,3) except at 91 elements, which are
the 90 involutions acting as -1 on a hyperbolic line L and +1 on L^perp, plus
-I (6bb8975 measured the lengths). Those 90 lines in polarity pairs are BT810's
45 tritangent planes = the 45 octets L u L^perp.
the_optimal_stabilizer_certificates_are_tensor_factorisations.py (feb5154):
an octet is the local Pauli set of a tensor factorisation C^9 = C^3 (x) C^3.

THE PHYSICAL NAME, checked on matrices.  Let C|j> = |-j> on one qutrit. Then
C X C^dag = X^-1 and C Z C^dag = Z^-1, so the two-qutrit unitary C (x) I acts
on Pauli labels (a1,b1,a2,b2) by

    diag(-1, -1, 1, 1),

computed here by conjugating all 80 Pauli matrices, not asserted. That is the
reflection with -1 eigenspace the first factor's hyperbolic line and +1
eigenspace the second's. I (x) C gives diag(1,1,-1,-1) and C (x) C gives -I.

AND IT IS ALL NINETY, not one.  The conjugacy class of diag(-1,-1,1,1) in
Sp(4,3) is computed by closing under generators: its size is 90 = 51840 / 576,
the centraliser being Sp(2,3) x Sp(2,3). Every element of the class is an
involution with a hyperbolic (-1)-eigenspace, so the class IS the anomaly set
of the earlier file. Conjugating C (x) I by a Clifford unitary moves the
factorisation, so

    90 cost anomalies  =  { C on one factor : 45 factorisations x 2 factors },
    the centre -I      =  C (x) C, the same in every factorisation.

WHAT IT MEANS.  In the transvection gate set every Clifford operation costs its
residue -- except charge-conjugating ONE qutrit of some splitting, which costs
one more. The expensive instruction is subsystem charge conjugation, and it is
indexed by exactly the objects (factorisations = octets = tritangent planes)
that carry the certificates and the sentinel code.

SCOPE.  Exact finite computation in Sp(4,3) and with 9x9 matrices. The length
measurement is cited from 6bb8975, not repeated. Nothing is claimed about
physical charge conjugation beyond the qutrit Clifford operator named here.
"""

import argparse
import itertools
import json
import os

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = 3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    w = np.exp(2j * np.pi / 3)
    X = np.roll(np.eye(3), 1, axis=0)
    Z = np.diag([w ** j for j in range(3)])
    C = np.zeros((3, 3))
    for j in range(3):
        C[(-j) % 3, j] = 1
    I3 = np.eye(3)

    def pauli(v):
        return np.kron(np.linalg.matrix_power(X, v[0]) @ np.linalg.matrix_power(Z, v[1]),
                       np.linalg.matrix_power(X, v[2]) @ np.linalg.matrix_power(Z, v[3]))

    vecs = [v for v in itertools.product(range(3), repeat=4) if any(v)]
    mats = {v: pauli(v) for v in vecs}

    def label(mat):
        for v, m in mats.items():
            r = np.vdot(m.flatten(), mat.flatten()) / 9
            if abs(abs(r) - 1) < 1e-9:
                return v
        raise AssertionError("not a Pauli")

    def induced(U):
        cols = []
        for e in ((1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)):
            cols.append(label(U @ mats[e] @ U.conj().T))
        S = np.array(cols).T % 3          # column k = image of basis vector k
        # linearity check on every label
        lin = all(label(U @ mats[v] @ U.conj().T) == tuple(int(t) for t in (S @ np.array(v)) % 3)
                  for v in vecs)
        return S, lin

    S_CI, lin1 = induced(np.kron(C, I3))
    S_IC, lin2 = induced(np.kron(I3, C))
    S_CC, lin3 = induced(np.kron(C, C))

    # the symplectic group on labels (a1,b1,a2,b2), form a1 b1' - b1 a1' + a2 b2' - b2 a2'
    J = np.array([[0, 1, 0, 0], [-1, 0, 0, 0], [0, 0, 0, 1], [0, 0, -1, 0]])

    def is_symp(S):
        return np.array_equal((S.T @ J @ S) % 3, J % 3)

    def transvection(v):
        v = np.array(v)
        return np.array([(np.eye(4, dtype=int)[:, k] + (e @ J @ v) * v) % 3
                         for k, e in enumerate(np.eye(4, dtype=int))]).T % 3

    gens = [transvection(v) for v in vecs]
    assert all(is_symp(g) for g in gens)

    def key(S):
        return tuple((S % 3).flatten())

    def inv(S):
        # symplectic inverse: -J S^T J
        return (-(J @ S.T @ J)) % 3

    start = np.diag([2, 2, 1, 1])
    cls = {key(start): start}
    frontier = [start]
    while frontier:
        nxt = []
        for S in frontier:
            for g in gens:
                T = (g @ S @ inv(g)) % 3
                k = key(T)
                if k not in cls:
                    cls[k] = T
                    nxt.append(T)
        frontier = nxt

    def eig_minus_hyperbolic(S):
        # -1 eigenspace of S over F_3 must be a 2-dim subspace on which the form is nondegenerate
        pts = [v for v in itertools.product(range(3), repeat=4) if any(v)
               and tuple(int(t) for t in (S @ np.array(v)) % 3) == tuple((-np.array(v)) % 3)]
        if len(pts) != 8:
            return False
        return any((np.array(u) @ J @ np.array(v)) % 3 for u, v in itertools.combinations(pts, 2))

    involutions = all(np.array_equal((S @ S) % 3, np.eye(4, dtype=int)) for S in cls.values())
    hyperbolic = all(eig_minus_hyperbolic(S) for S in cls.values())
    minus_spaces = set()
    for S in cls.values():
        minus_spaces.add(frozenset(v for v in itertools.product(range(3), repeat=4)
                                   if tuple(int(t) for t in (S @ np.array(v)) % 3) == tuple((-np.array(v)) % 3)))

    print("THE COST ANOMALIES ARE LOCAL CHARGE CONJUGATIONS")
    print("=" * 74)
    print("  C (x) I induces %s  (linear on all 80 labels: %s)" % (S_CI.diagonal().tolist(), lin1))
    print("  I (x) C induces %s  (linear: %s)" % (S_IC.diagonal().tolist(), lin2))
    print("  C (x) C induces %s  (linear: %s)" % (S_CC.diagonal().tolist(), lin3))
    print("  conjugacy class of C (x) I in Sp(4,3): %d elements = 51840/576 = %d" % (len(cls), 51840 // 576))
    print("  all involutions: %s; every (-1)-eigenspace a hyperbolic line: %s; distinct (-1)-spaces: %d"
          % (involutions, hyperbolic, len(minus_spaces)))

    diag_ok = (np.array_equal(S_CI, np.diag([2, 2, 1, 1])) and np.array_equal(S_IC, np.diag([1, 1, 2, 2]))
               and np.array_equal(S_CC, np.diag([2, 2, 2, 2])))
    ok = diag_ok and lin1 and lin2 and lin3 and len(cls) == 90 and involutions and hyperbolic \
        and len(minus_spaces) == 90 and is_symp(S_CI)
    print()
    print("VALID: %s" % ok)

    if args.write:
        assert ok, "checks failed -- refusing to write"
        rec = {
            "schema": "holotrade.cost-anomalies-local-charge-conjugation.v1",
            "valid": True,
            "CtensorIInduces": S_CI.diagonal().tolist(),
            "ItensorCInduces": S_IC.diagonal().tolist(),
            "CtensorCInduces": S_CC.diagonal().tolist(),
            "conjugacyClassSize": len(cls),
            "centraliserOrder": 51840 // len(cls),
            "allInvolutions": involutions,
            "minusEigenspacesHyperbolic": hyperbolic,
            "distinctMinusEigenspaces": len(minus_spaces),
            "priorArt": (
                "the_cost_anomalies_are_the_tritangent_structure.py (90 hyperbolic-line reflections + -I, "
                "lengths from 6bb8975; 45 tritangent planes = 45 octets) and "
                "the_optimal_stabilizer_certificates_are_tensor_factorisations.py (feb5154: octet = tensor "
                "factorisation)."),
            "thePhysicalName": (
                "with C|j> = |-j>, C X C^dag = X^-1 and C Z C^dag = Z^-1, so C (x) I acts on Pauli labels as "
                "diag(-1,-1,1,1), computed by conjugating all 80 Pauli matrices: the reflection in the first "
                "factor's hyperbolic line. I (x) C gives diag(1,1,-1,-1) and C (x) C gives -I."),
            "andItIsAllNinety": (
                "the conjugacy class of diag(-1,-1,1,1) in Sp(4,3) has 90 = 51840/576 elements, all "
                "involutions with a hyperbolic (-1)-eigenspace, 90 distinct eigenspaces: exactly the anomaly "
                "set. So the 90 cost anomalies are C on one factor of one of the 45 factorisations, and the "
                "centre -I is C (x) C."),
            "boundary": (
                "exact finite computation in Sp(4,3) and with 9x9 matrices; the transvection lengths are cited "
                "from 6bb8975 and not repeated; nothing is claimed about physical charge conjugation beyond "
                "the qutrit Clifford operator named here."),
        }
        p = os.path.join(ROOT, "data", "cost_anomalies_local_charge_conjugation.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=2)
        print("written: %s" % p)


if __name__ == "__main__":
    main()
