#!/usr/bin/env python3
"""
The optimal way to certify every two-qudit stabilizer state is built on a
TENSOR FACTORISATION. For two qubits it is exactly a Dirac gamma set; for two
qutrits it is three local observables and eight correlations -- and nothing
else is optimal.

PRIOR ART, CITED, NOT RE-DERIVED.
  * w33_blocking_is_pauli_context_covering.py -- a blocking set of W(3,3) is a
    set of Pauli observables meeting every measurement context; tau_1 = 11.
  * context_cover_equals_mub_count_iff_q_even.py -- the cover costs exactly the
    MUB count q^2+1 iff q is even (an ovoid is a perfect context transversal).
  * the_blockers_in_closed_form.py and the octet result (3f93821): the 360
    minimum blockers of W(3,3) are B(c,L) = (Adj(c) minus L^perp) u (L minus
    {c}) with L a hyperbolic line through c.
Neither repository states what an OCTET L u L^perp is physically, nor reads a
blocker as a certificate on STATES, nor checks any of it on state vectors.
That is what this file adds.

THE OPERATIONAL QUESTION.  Call a set S of Pauli observables a CERTIFICATE if
every stabilizer state is an eigenstate of some P in S -- measuring S then
always yields at least one deterministic outcome on any stabilizer state. How
small can S be, and what do the optimal S look like?

COMPUTED FROM STATE VECTORS, not from symplectic coordinates.  The stabilizer
states are generated as the Clifford orbit of |00> under H(x)I, I(x)H, S(x)I,
I(x)S and CSUM, deduplicated up to global phase; "eigenstate of P" is the
numerical test |<psi|P|psi>| = 1. The geometry is never used to produce them.

    d   stabilizer states   classes   fewest certifying   optimal sets
    2          60              15             5                 6
    3         360              40            11               360

THE PHYSICAL READING OF THE OCTET.  A hyperbolic line L is d+1 pairwise
non-commuting Pauli classes whose matrices generate a full matrix algebra
M_d, and its perp L^perp generates the commutant, another M_d, with the two
together spanning all of M_{d^2}. That is precisely a TENSOR FACTORISATION
C^{d^2} = C^d (x) C^d compatible with the Pauli group. The octet L u L^perp is
the set of LOCAL Pauli classes of that factorisation. Counted by the algebra
test here, not by the geometry: 10 factorisations for two qubits, 45 for two
qutrits.

THE STRUCTURE THEOREM, verified by exhaustive enumeration.  Choose a
factorisation, one of its factors, and a local class c on that factor. Take

    the other d local classes on c's factor,  and
    the d^2 - 1 correlated classes  c^j (x) P,  P != I on the other factor.

That is d^2 + d - 1 observables. For d = 2 and d = 3 the sets so built are
EXACTLY the optimal certificates -- the enumeration of all optimal sets and the
construction agree as sets of sets, 6 = 6 and 360 = 360.

  d = 2.  Every optimal certificate is 5 pairwise ANTICOMMUTING Paulis, i.e. a
          set of Dirac gamma matrices generating Cl_5 on C^4. The factorisation
          construction and the Clifford-algebra picture are the same six sets.
  d = 3.  No anticommuting family of the needed size exists (no ovoid), and the
          optimum is instead LOCAL-PLUS-CONDITIONED: a certificate built on a
          factorisation catches 108 of the 360 states with its 3 local
          observables and needs its 8 correlations for the other 252. Every
          Pauli class is local in exactly 9 factorisations -- the 9 minimum
          blockers per point that already carry the tetracode.

WHAT IT MEANS.  Certifying stabilizer states of two qutrits optimally is not a
bag of observables: it is a choice of how to split the pair into two qutrits,
plus one distinguished local direction. The qubit optimum has the same shape and
collapses onto the Clifford algebra behind Dirac spinors.

SCOPE.  Exhaustive at d = 2 and d = 3 (all optimal sets enumerated with a
single CP-SAT worker, since enumerate_all_solutions is complete only then).
The d = 3 statement is the physical reading of a combinatorial classification
this repository already owns; the claim added is the identification of octets
with tensor factorisations, the certificate reading on states, and their
verification with matrices. Nothing is claimed for d >= 5, where the octet
construction still has minimum size (tau_1(W(3,5)) = 29) but is NOT the only
optimum (the_minimality_fence_was_wrong.py). No bound on tau_2 moves here.
"""

import argparse
import itertools
import json
import os

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(d):
    from ortools.sat.python import cp_model

    D = d * d
    w = np.exp(2j * np.pi / d)
    X = np.roll(np.eye(d), 1, axis=0)
    Z = np.diag([w ** j for j in range(d)])
    if d == 2:
        H = np.array([[1, 1], [1, -1]]) / np.sqrt(2)
        S = np.diag([1, 1j])
    else:
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
    states = list(seen.values())
    nS = len(states)

    def pauli(v):
        return np.kron(np.linalg.matrix_power(X, v[0]) @ np.linalg.matrix_power(Z, v[1]),
                       np.linalg.matrix_power(X, v[2]) @ np.linalg.matrix_power(Z, v[3]))

    vecs = [v for v in itertools.product(range(d), repeat=4) if any(v)]
    classes = sorted({min(tuple((k * c) % d for c in v) for k in range(1, d))
                      for v in vecs})
    nC = len(classes)
    M = [pauli(c) for c in classes]
    comm = [[bool(np.allclose(A @ B, B @ A)) for B in M] for A in M]
    eig = np.array([[abs(np.vdot(s, A @ s)) > 1 - 1e-6 for A in M] for s in states])
    contexts = {tuple(np.flatnonzero(r)) for r in eig}

    m = cp_model.CpModel()
    x = [m.NewBoolVar("") for _ in range(nC)]
    for r in eig:
        m.AddBoolOr([x[j] for j in np.flatnonzero(r)])
    m.Minimize(sum(x))
    sv = cp_model.CpSolver()
    sv.parameters.num_workers = 8
    st = sv.Solve(m)
    tau = int(sv.ObjectiveValue())
    tau_status = sv.StatusName(st)

    m2 = cp_model.CpModel()
    x2 = [m2.NewBoolVar("") for _ in range(nC)]
    for r in eig:
        m2.AddBoolOr([x2[j] for j in np.flatnonzero(r)])
    m2.Add(sum(x2) == tau)
    sols = []

    class CB(cp_model.CpSolverSolutionCallback):
        def __init__(self):
            cp_model.CpSolverSolutionCallback.__init__(self)

        def on_solution_callback(self):
            sols.append(frozenset(j for j in range(nC) if self.Value(x2[j])))

    sv2 = cp_model.CpSolver()
    sv2.parameters.num_workers = 1
    sv2.parameters.enumerate_all_solutions = True
    enum_status = sv2.StatusName(sv2.Solve(m2, CB()))
    optimal = set(sols)

    def alg_dim(idxs):
        mats = [np.eye(D)] + [np.linalg.matrix_power(M[i], k)
                              for i in idxs for k in range(1, d)]
        prods = [A @ B for A in mats for B in mats]
        return int(np.linalg.matrix_rank(np.array([p.flatten() for p in prods]), tol=1e-8))

    facts = set()
    for L in itertools.combinations(range(nC), d + 1):
        if any(comm[a][b] for a, b in itertools.combinations(L, 2)):
            continue
        if alg_dim(L) != d * d:
            continue
        Lp = tuple(j for j in range(nC) if all(comm[j][a] for a in L))
        if len(Lp) != d + 1 or alg_dim(Lp) != d * d or alg_dim(L + Lp) != D * D:
            continue
        facts.add(tuple(sorted((L, Lp))))

    def class_of(mat):
        return next(j for j in range(nC) for kk in range(1, d)
                    if abs(np.trace(np.linalg.matrix_power(M[j], kk).conj().T @ mat)) > 1e-6)

    built = {}
    for L, Lp in facts:
        for side, other in ((L, Lp), (Lp, L)):
            for c in side:
                corr = {class_of(np.linalg.matrix_power(M[c], k1) @ np.linalg.matrix_power(M[o], k2))
                        for o in other for k1 in range(1, d) for k2 in range(1, d)}
                B = frozenset(set(side) - {c}) | frozenset(corr)
                built.setdefault(B, (L, Lp, c))
    certifies = all(all(any(eig[s][j] for j in B) for s in range(nS)) for B in built)

    rec = {"d": d, "stabilizerStates": nS, "expectedStates": D * (d + 1) * (d * d + 1),
           "pauliClasses": nC, "contexts": len(contexts),
           "eigenclassesPerState": sorted({int(v) for v in eig.sum(1)}),
           "fewestCertifying": tau, "fewestStatus": tau_status,
           "optimalSets": len(optimal), "enumerationStatus": enum_status,
           "factorisations": len(facts), "constructedSets": len(built),
           "constructedSizes": sorted({len(b) for b in built}),
           "constructedCertifyAll": certifies,
           "constructedEqualsOptimal": set(built) == optimal}
    if d == 2:
        rec["optimalSetsPairwiseAnticommute"] = all(
            all(np.allclose(M[a] @ M[b], -M[b] @ M[a]) for a, b in itertools.combinations(sorted(B), 2))
            for B in optimal)
    else:
        B, (L, Lp, c) = next(iter(built.items()))
        loc = set(L if c in L else Lp) - {c}
        rec["statesCertifiedByLocals"] = int(sum(1 for s in range(nS) if any(eig[s][j] for j in loc)))
        rec["statesNeedingCorrelations"] = nS - rec["statesCertifiedByLocals"]
        rec["factorisationsPerClass"] = sorted({sum(1 for (a, b) in facts if cc in a or cc in b)
                                                for cc in range(nC)})
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    r2, r3 = run(2), run(3)
    print("THE OPTIMAL STABILIZER CERTIFICATES ARE TENSOR FACTORISATIONS")
    print("=" * 74)
    for r in (r2, r3):
        print("  d=%d: %d stabilizer states (Clifford orbit, expected %d), %d classes, %d contexts"
              % (r["d"], r["stabilizerStates"], r["expectedStates"], r["pauliClasses"], r["contexts"]))
        print("        fewest certifying observables %d [%s]; optimal sets %d [%s]"
              % (r["fewestCertifying"], r["fewestStatus"], r["optimalSets"], r["enumerationStatus"]))
        print("        algebra-checked factorisations %d; construction gives %d sets of size %s"
              % (r["factorisations"], r["constructedSets"], r["constructedSizes"]))
        print("        construction certifies all: %s   construction == all optima: %s"
              % (r["constructedCertifyAll"], r["constructedEqualsOptimal"]))
    print("  qubits: every optimum is 5 pairwise anticommuting Paulis: %s"
          % r2["optimalSetsPairwiseAnticommute"])
    print("  qutrits: %d states caught by the 3 locals, %d need the 8 correlations;"
          " each class is local in %s factorisations"
          % (r3["statesCertifiedByLocals"], r3["statesNeedingCorrelations"], r3["factorisationsPerClass"]))

    ok = (r2["stabilizerStates"] == 60 and r3["stabilizerStates"] == 360
          and r2["fewestCertifying"] == 5 and r3["fewestCertifying"] == 11
          and r2["fewestStatus"] == r3["fewestStatus"] == "OPTIMAL"
          and r2["enumerationStatus"] == r3["enumerationStatus"] == "OPTIMAL"
          and r2["optimalSets"] == 6 and r3["optimalSets"] == 360
          and r2["factorisations"] == 10 and r3["factorisations"] == 45
          and r2["constructedEqualsOptimal"] and r3["constructedEqualsOptimal"]
          and r2["constructedCertifyAll"] and r3["constructedCertifyAll"]
          and r2["optimalSetsPairwiseAnticommute"]
          and r3["statesCertifiedByLocals"] == 108 and r3["factorisationsPerClass"] == [9])
    print()
    print("VALID: %s" % ok)

    if args.write:
        assert ok, "checks failed -- refusing to write"
        rec = {
            "schema": "holotrade.optimal-stabilizer-certificates.v1",
            "valid": True,
            "qubits": r2,
            "qutrits": r3,
            "priorArt": (
                "w33_blocking_is_pauli_context_covering.py (blocking set = observables "
                "meeting every context, tau_1 = 11); context_cover_equals_mub_count_iff_q_even.py "
                "(cover = MUB count iff q even); the_blockers_in_closed_form.py and 3f93821 "
                "(the 360 minimum blockers are B(c,L)). Cited, not re-derived."),
            "theQuestion": (
                "a set S of Pauli observables is a CERTIFICATE if every stabilizer state is an "
                "eigenstate of some P in S, so measuring S always yields a deterministic outcome "
                "on any stabilizer state. How small can S be and what do the optimal S look like?"),
            "computedFromStateVectors": (
                "stabilizer states are generated as the Clifford orbit of |00> under H(x)I, "
                "I(x)H, S(x)I, I(x)S and CSUM and deduplicated up to phase; eigenstate means "
                "|<psi|P|psi>| = 1 numerically. The symplectic geometry is never used to "
                "produce them."),
            "theOctetIsATensorFactorisation": (
                "a hyperbolic line L is d+1 pairwise non-commuting Pauli classes generating a "
                "full matrix algebra M_d; L^perp generates the commutant, another M_d, and "
                "together they span M_{d^2}. That is a tensor factorisation C^{d^2} = "
                "C^d (x) C^d compatible with the Pauli group, and the octet L u L^perp is its set "
                "of LOCAL classes. Counted by the algebra test: 10 for two qubits, 45 for two "
                "qutrits."),
            "theStructureTheorem": (
                "choose a factorisation, a factor and a local class c on it; take the other d "
                "local classes on that factor and the d^2-1 correlated classes c^j (x) P with "
                "P != I on the other factor. For d = 2 and d = 3 these are EXACTLY the optimal "
                "certificates: 6 = 6 and 360 = 360 as sets of sets."),
            "qubitsAreDiracSets": (
                "every optimal two-qubit certificate is 5 pairwise ANTICOMMUTING Paulis, a set "
                "of Dirac gamma matrices generating Cl_5 on C^4; the factorisation construction "
                "and the Clifford-algebra picture give the same six sets."),
            "qutritsAreLocalPlusConditioned": (
                "no such anticommuting family exists for two qutrits (no ovoid); the optimum is "
                "local-plus-conditioned: one certificate catches 108 of the 360 states with its "
                "3 local observables and needs its 8 correlations for the other 252. Every "
                "Pauli class is local in exactly 9 factorisations -- the 9 minimum blockers per "
                "point that carry the tetracode."),
            "boundary": (
                "exhaustive at d = 2 and d = 3, all optimal sets enumerated with num_workers = 1. "
                "The d = 3 classification is combinatorially already ours; what is added is the "
                "identification of octets with tensor factorisations, the certificate reading "
                "on states, and verification with matrices. Nothing is claimed for d >= 5, where "
                "the octet construction is minimum but not the only optimum. No bound on tau_2 "
                "moves."),
        }
        p = os.path.join(ROOT, "data", "optimal_stabilizer_certificates.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=2)
        print("written: %s" % p)


if __name__ == "__main__":
    main()
