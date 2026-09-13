#!/usr/bin/env python3
"""
Two ququints are the first system whose optimal stabilizer certificates come in
TWO kinds: 3,900 built on one tensor factorisation, and 46,800 built on a
commuting PAIR of observables that uses five factorisations at once.

WHAT THIS CONTINUES.  the_optimal_stabilizer_certificates_are_tensor_factorisations.py
showed, from state vectors, that for two qubits and two qutrits every optimal
certificate -- a set of Pauli observables of which every stabilizer state is an
eigenstate of at least one -- is FACTORISATION-CONDITIONED: a factorisation
C^d (x) C^d, a local observable c, the other local classes on c's factor, and the
correlations c^j (x) P. the_q5_tight_case_dies_without_the_centre_property.py
classifies the minimum blockers of W(3,5) exactly: two shapes, with closed
forms, 50,700 in all. This file is the physical reading of that classification,
checked on matrices and state vectors.

THE SECOND KIND, stated physically.  Take two COMMUTING, independent Pauli
observables a and b of two ququints. Exactly five tensor factorisations put a
on one factor and b on the other. Choose two of them. The certificate is

    the 4 products a^i b^j (i, j != 0)              -- the shared context,
    the other 5 local classes on a's factor         -- in each of the chosen two,
    the other 5 local classes on b's factor         -- in each of the other three,

4 + 10 + 15 = 29 observables. There are 156 * 30 ordered pairs (a, b) and
C(5,2) = 10 splits: 46,800 certificates. The factorisation-conditioned kind
gives 156 * 25 = 3,900. Nothing else is optimal (that is the exact
classification in the companion file, transported here through the
commutation dictionary, which this file re-verifies on all pairs).

COMPUTED HERE FROM MATRICES.
  * The 3,900 two-ququint stabilizer states are generated as the Clifford
    orbit of |00> under H, S on each factor and CSUM.
  * The 156 Pauli classes are 25 x 25 matrices; commuting iff the symplectic
    form vanishes, checked on every pair.
  * Factorisations are found as sets of 6 pairwise non-commuting classes
    closed under products whose matrices generate M_5, with the commutant
    generating another M_5 and the two spanning M_25: 325 of them.
  * Both kinds of certificate are BUILT from that algebraic data alone and
    each is checked to certify all 3,900 states. Counts: 3,900 and 46,800,
    all distinct, all of size 29, and the two families are disjoint.
  * Each certificate is also checked to be MINIMAL (removing any observable
    leaves some state uncertified). Minimum size 29 is tau_1(W(3,5)), proved
    OPTIMAL in the_minimality_fence_was_wrong.py and cited, not re-solved.

WHAT IT MEANS.  For qubits and qutrits an optimal certificate needs one way of
splitting the system into two parts. For ququints most optimal certificates
(46,800 of 50,700, over 92 per cent) need five splittings at once, tied
together by one commuting pair. The optimum stops being a property of a single
bipartition exactly where the local dimension first allows the excess to be
spread over two centres.

SCOPE.  The construction, the certification of all states and minimality are
exhaustive computations. Optimality (29) and completeness (no third kind) are
cited from the companion files and not recomputed. d >= 7 is not claimed.
"""

import argparse
import itertools
import json
import os

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = 5


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    D = d * d
    w = np.exp(2j * np.pi / d)
    X = np.roll(np.eye(d), 1, axis=0)
    Z = np.diag([w ** j for j in range(d)])
    H = np.array([[w ** (j * k) for k in range(d)] for j in range(d)]) / np.sqrt(d)
    S = np.diag([w ** (j * (j - 1) // 2) for j in range(d)])
    I = np.eye(d)
    CSUM = np.zeros((D, D))
    for a in range(d):
        for b in range(d):
            CSUM[a * d + (a + b) % d, a * d + b] = 1
    gates = [np.kron(H, I), np.kron(I, H), np.kron(S, I), np.kron(I, S), CSUM]

    def key(v):
        k = np.flatnonzero(np.abs(v) > 1e-9)[0]
        v = v * np.conj(v[k]) / abs(v[k])
        return tuple(np.round(v.real, 6)) + tuple(np.round(v.imag, 6))

    start = np.zeros(D, complex)
    start[0] = 1
    seen = {key(start): start}
    frontier = [start]
    while frontier:
        nxt = []
        for v in frontier:
            for g in gates:
                u = g @ v
                k = key(u)
                if k not in seen:
                    seen[k] = u
                    nxt.append(u)
        frontier = nxt
    states = np.array(list(seen.values()))
    nS = len(states)

    vecs = [v for v in itertools.product(range(d), repeat=4) if any(v)]
    classes = sorted({min(tuple((k * c) % d for c in v) for k in range(1, d)) for v in vecs})
    nC = len(classes)
    cid = {c: i for i, c in enumerate(classes)}

    def canon(v):
        return cid[min(tuple((k * c) % d for c in v) for k in range(1, d))]

    def pauli(v):
        return np.kron(np.linalg.matrix_power(X, v[0]) @ np.linalg.matrix_power(Z, v[1]),
                       np.linalg.matrix_power(X, v[2]) @ np.linalg.matrix_power(Z, v[3]))

    M = [pauli(c) for c in classes]

    def sform(u, v):
        return (u[0] * v[1] - u[1] * v[0] + u[2] * v[3] - u[3] * v[2]) % d

    comm = np.array([[np.allclose(A @ B, B @ A) for B in M] for A in M])
    form_ok = all(comm[i][j] == (sform(classes[i], classes[j]) == 0)
                  for i in range(nC) for j in range(nC))
    eig = np.array([[abs(np.vdot(s, A @ s)) > 1 - 1e-6 for A in M] for s in states])
    contexts = {tuple(np.flatnonzero(r)) for r in eig}

    # products of classes are read off the MATRICES: a Pauli matrix is a phased permutation, so
    # its support pattern and phase ratios identify it up to a global phase
    def mkey(mat):
        rows = np.argmax(np.abs(mat), axis=0)
        ref = mat[rows[0], 0]
        ph = np.round(np.angle(mat[rows, np.arange(D)] / ref) * d / (2 * np.pi)).astype(int) % d
        return tuple(rows) + tuple(ph)

    POW = {}
    for j in range(nC):
        for kk in range(1, d):
            POW[mkey(np.linalg.matrix_power(M[j], kk))] = j
    assert len(POW) == nC * (d - 1), "class powers must be distinguishable"

    def class_of(mat):
        return POW[mkey(mat)]

    PW = [[np.linalg.matrix_power(M[j], k) for k in range(d)] for j in range(nC)]

    def closure(i, j):
        return frozenset(class_of(PW[i][s] @ PW[j][t])
                         for s in range(d) for t in range(d) if s or t)

    def alg_dim(idxs):
        mats = [np.eye(D)] + [np.linalg.matrix_power(M[i], k) for i in idxs for k in range(1, d)]
        return int(np.linalg.matrix_rank(np.array([m.flatten() for m in mats]), tol=1e-8))

    hyper = set()
    done = set()
    for i in range(nC):
        for j in range(i + 1, nC):
            if not comm[i][j] and (i, j) not in done:
                L = closure(i, j)
                hyper.add(L)
                done.update(itertools.combinations(sorted(L), 2))
    facts = {}
    for L in hyper:
        Lp = frozenset(j for j in range(nC) if all(comm[j][a] for a in L))
        ok = (len(L) == d + 1 and len(Lp) == d + 1
              and not any(comm[a][b] for a, b in itertools.combinations(sorted(L), 2))
              and alg_dim(sorted(L)) == D and alg_dim(sorted(Lp)) == D)
        if ok:
            facts[L] = Lp
    # a single spot check that factors span M_25 together
    L0 = next(iter(facts))
    both = [np.linalg.matrix_power(M[i], k) @ np.linalg.matrix_power(M[j], kk)
            for i in L0 for j in facts[L0] for k in range(1, d) for kk in range(1, d)]
    both += [np.linalg.matrix_power(M[i], k) for i in list(L0) + list(facts[L0]) for k in range(1, d)]
    both += [np.eye(D)]
    span_ok = int(np.linalg.matrix_rank(np.array([m.flatten() for m in both]), tol=1e-8)) == D * D
    unordered = {frozenset((L, facts[L])) for L in facts}

    kind1 = set()
    for L, Lp in facts.items():
        for c in L:
            corr = {class_of(np.linalg.matrix_power(M[c], k1) @ np.linalg.matrix_power(M[o], k2))
                    for o in Lp for k1 in range(1, d) for k2 in range(1, d)}
            kind1.add(frozenset(set(L) - {c}) | frozenset(corr))

    kind2 = set()
    for a in range(nC):
        for b in range(nC):
            if a == b or not comm[a][b]:
                continue
            ctx = closure(a, b)
            sep = [L for L in facts if a in L and b in facts[L]]
            assert len(sep) == d, len(sep)
            for chosen in itertools.combinations(range(d), 2):
                B = set(ctx) - {a, b}
                for t, L in enumerate(sep):
                    B |= (set(L) - {a}) if t in chosen else (set(facts[L]) - {b})
                kind2.add(frozenset(B))

    def certifies(B):
        return bool(eig[:, sorted(B)].any(axis=1).all())

    E = eig.astype(np.int32)

    def minimal(B):
        cols = sorted(B)
        cover = E[:, cols].sum(axis=1)
        return all(not ((cover - E[:, j]) > 0).all() for j in cols)

    all1 = all(len(B) == 29 and certifies(B) for B in kind1)
    all2 = all(len(B) == 29 and certifies(B) for B in kind2)
    min1 = all(minimal(B) for B in kind1)
    min2 = all(minimal(B) for B in kind2)

    print("THE QUQUINT CERTIFICATES HAVE A SECOND KIND")
    print("=" * 74)
    print("  stabilizer states (Clifford orbit): %d   Pauli classes: %d   contexts: %d"
          % (nS, nC, len(contexts)))
    print("  commutation == symplectic form on all pairs: %s" % form_ok)
    print("  algebra-checked factorisations: %d ordered, %d unordered; factors span M_25: %s"
          % (len(facts), len(unordered), span_ok))
    print("  kind 1 (one factorisation):  %d certificates, all size 29 and certifying: %s, minimal: %s"
          % (len(kind1), all1, min1))
    print("  kind 2 (commuting pair):     %d certificates, all size 29 and certifying: %s, minimal: %s"
          % (len(kind2), all2, min2))
    print("  families disjoint: %s   total %d" % (not (kind1 & kind2), len(kind1 | kind2)))

    ok = (nS == 3900 and nC == 156 and len(contexts) == 156 and form_ok
          and len(facts) == 650 and len(unordered) == 325 and span_ok
          and len(kind1) == 3900 and len(kind2) == 46800 and not (kind1 & kind2)
          and all1 and all2 and min1 and min2)
    print()
    print("VALID: %s" % ok)

    if args.write:
        assert ok, "checks failed -- refusing to write"
        rec = {
            "schema": "holotrade.ququint-certificates-second-kind.v1",
            "valid": True,
            "stabilizerStates": nS, "pauliClasses": nC, "contexts": len(contexts),
            "commutationEqualsForm": form_ok,
            "factorisationsOrdered": len(facts), "factorisationsUnordered": len(unordered),
            "factorsSpanFullAlgebra": span_ok,
            "kindOneCount": len(kind1), "kindTwoCount": len(kind2), "total": len(kind1 | kind2),
            "familiesDisjoint": not (kind1 & kind2),
            "allCertifyAllStates": all1 and all2, "allMinimal": min1 and min2,
            "certificateSize": 29,
            "theSecondKind": (
                "take two COMMUTING independent Pauli observables a and b; exactly five tensor "
                "factorisations put a on one factor and b on the other; choose two of them. The "
                "certificate is the 4 products a^i b^j, the other 5 local classes on a's factor in each "
                "of the chosen two, and the other 5 local classes on b's factor in each of the other "
                "three: 4 + 10 + 15 = 29. 156 * 30 ordered pairs times C(5,2) = 10 splits gives 46,800."),
            "whatItMeans": (
                "for qubits and qutrits an optimal certificate needs one bipartition; for ququints "
                "46,800 of the 50,700 optimal certificates need five bipartitions tied together by one "
                "commuting pair."),
            "citedNotRecomputed": (
                "minimum size 29 = tau_1(W(3,5)) from the_minimality_fence_was_wrong.py; completeness "
                "(no third kind) from the_q5_tight_case_dies_without_the_centre_property.py."),
            "boundary": (
                "construction, certification of all 3,900 states and minimality are exhaustive; "
                "optimality and completeness are cited. d >= 7 is not claimed."),
        }
        p = os.path.join(ROOT, "data", "ququint_certificates_second_kind.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=2)
        print("written: %s" % p)


if __name__ == "__main__":
    main()
