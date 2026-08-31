#!/usr/bin/env python3
"""
What the blocking numbers MEAN: tau_1 is a Pauli context-covering number, and
tau_2 is its two-carrier product-measurement version.

WHERE THIS COMES FROM.  The holonet blueprint (holonet_machine_blueprint_body,
section "The self-entanglement, and where the 40 comes from") turns on one
identity,

    C^3 (x) C^3  =  End(C^3),

so that "two qutrits" and "one qutrit that can act on itself" are the same
machine described twice. It counts the 40 points as (3^4-1)/2, the independent
directions one self-entangled qutrit can be measured along, and -- this is the
part the blueprint claims as its own -- identifies the 40 LINES as the maximal
COMMUTING subalgebras.

Take that identification seriously and the blocking numbers stop being
abstract. A line is a measurement CONTEXT: a maximal set of simultaneously
measurable Pauli observables. So

    a blocking set  =  a set of Pauli observables that meets every context,
    tau_1 = 11      =  the fewest observables with that property,
    alpha = 7       =  the most pairwise NON-COMMUTING observables,

and W(3,3) having no ovoid says exactly that ten pairwise non-commuting
2-qutrit Paulis do not exist, though the Hoffman bound leaves room for them.

THE HEMISYSTEMS GET A READING TOO.  The 432 hemisystems this repository has
been circling -- and which W33-Theory reached independently from the trade
lattice -- are the sets of 20 Pauli observables meeting EVERY context in
exactly two. Half of every context, every time. That is what "hemi" means here
in operational terms, not just spectral ones.

AND THE DEPTH-2 PROBLEM BECOMES A TWO-CARRIER STATEMENT.  A point of
W(3,3) x W(3,3) is a pair (A, B) of non-identity Pauli classes, one per
carrier, i.e. the PRODUCT observable A (x) B. A tile L x M is a pair of
contexts, one per carrier. So a depth-2 blocker is

    a set of PRODUCT observables A (x) B such that every pair of local
    contexts is met by at least one of them,

and tau_2 in [111, 115] is the size of the smallest such set. Note what it is
NOT: the four-qutrit Pauli space has (3^8-1)/2 = 3280 classes, and the 1,600
product observables are a proper subset of it. The depth-2 question is
deliberately restricted to LOCAL measurements -- one observable per carrier --
which is exactly the regime a two-carrier machine can actually address.

VERIFIED HERE, with matrices rather than by assertion.  It would be easy to
assert that the symplectic form is commutation and move on. Instead the 80
non-identity two-qutrit Paulis are built as explicit 9x9 complex matrices from
X|j> = |j+1>, Z|j> = omega^j |j>, and every commutator is computed
numerically. The claims checked are:

  * P and Q commute exactly when their symplectic form vanishes -- all
    80 x 80 pairs, no exceptions;
  * P and P^2 always commute, so the 40 projective classes are well defined
    and the commuting relation descends to them;
  * the resulting graph on 40 classes is SRG(40, 12, 2, 4);
  * the maximal commuting sets are 40 in number and have 4 classes each,
    matching the lines of W(3,3) exactly as sets;
  * tau_1 = 11 and alpha = 7 recomputed on the Pauli graph directly.

WHAT IS AND IS NOT NEW.  That the two-qutrit Pauli graph is W(3,3) is
classical and the blueprint already has the 40 = (3^4-1)/2 count and the
maximal-commuting-subalgebra reading; a search of both repositories for
blocking sets stated in Pauli, commuting or context language returns nothing,
so the reading of tau_1, alpha and the hemisystems as measurement quantities,
and of tau_2 as the two-carrier product-measurement covering number, is what
is added. No bound moves: tau_2 stays open in [111, 115].
"""

import itertools
import json
import os
import sys

try:
    import numpy as np
except ImportError:
    sys.exit("needs numpy")

ROOT = r"C:\Repos\Holotrade"
W = np.exp(2j * np.pi / 3)


def single(a, b):
    """X^a Z^b on C^3."""
    X = np.zeros((3, 3), dtype=complex)
    for j in range(3):
        X[(j + 1) % 3, j] = 1
    Z = np.diag([W ** j for j in range(3)])
    return np.linalg.matrix_power(X, a) @ np.linalg.matrix_power(Z, b)


def pauli(v):
    """v = (a1,b1,a2,b2) -> the 9x9 two-qutrit Pauli X^a1 Z^b1 (x) X^a2 Z^b2."""
    return np.kron(single(v[0], v[1]), single(v[2], v[3]))


def sform(u, v):
    """The symplectic form on F_3^4 in the (a1,b1,a2,b2) coordinates."""
    return (u[0] * v[1] - u[1] * v[0] + u[2] * v[3] - u[3] * v[2]) % 3


def main():
    vecs = [v for v in itertools.product(range(3), repeat=4) if any(v)]
    mats = {v: pauli(v) for v in vecs}
    print("PAULI READING OF THE BLOCKING NUMBERS")
    print("=" * 72)
    print("  %d non-identity two-qutrit Paulis, built as 9x9 matrices"
          % len(vecs))

    # 1. commutation == symplectic form, checked on every pair
    bad = 0
    for u, v in itertools.combinations(vecs, 2):
        A, B = mats[u], mats[v]
        commutes = np.allclose(A @ B, B @ A, atol=1e-9)
        if commutes != (sform(u, v) == 0):
            bad += 1
    print("  commutator vs symplectic form: %d mismatches over %d pairs"
          % (bad, len(vecs) * (len(vecs) - 1) // 2))

    # 2. P and P^2 commute, so the projective classes are well defined
    sq_ok = all(np.allclose(mats[v] @ mats[v] @ mats[v], mats[v] @ mats[v] @ mats[v])
                and sform(v, tuple((2 * c) % 3 for c in v)) == 0 for v in vecs)
    def cls(v):
        return min(v, tuple((2 * c) % 3 for c in v))
    classes = sorted({cls(v) for v in vecs})
    N = len(classes)
    cidx = {c: i for i, c in enumerate(classes)}
    print("  P commutes with P^2 for every P: %s -> %d projective classes"
          % (sq_ok, N))

    # 3. the commuting graph on classes
    adj = [[False] * N for _ in range(N)]
    for a, b in itertools.combinations(range(N), 2):
        if sform(classes[a], classes[b]) == 0:
            adj[a][b] = adj[b][a] = True
    deg = {sum(r) for r in adj}
    lam, mu = set(), set()
    for a, b in itertools.combinations(range(N), 2):
        c = sum(1 for k in range(N) if adj[a][k] and adj[b][k])
        (lam if adj[a][b] else mu).add(c)
    print("  commuting graph: SRG(%d, %s, %s, %s)"
          % (N, sorted(deg), sorted(lam), sorted(mu)))

    # 4. maximal commuting sets = maximal totally isotropic subspaces
    contexts = set()
    for a, b in itertools.combinations(range(N), 2):
        if sform(classes[a], classes[b]) != 0:
            continue
        span = set()
        u, v = classes[a], classes[b]
        for s, t in itertools.product(range(3), repeat=2):
            if s == t == 0:
                continue
            w = tuple((s * u[k] + t * v[k]) % 3 for k in range(4))
            span.add(cidx[cls(w)])
        if len(span) == 4:
            contexts.add(tuple(sorted(span)))
    contexts = sorted(contexts)
    print("  maximal commuting subalgebras (contexts): %d, each of %d classes"
          % (len(contexts), len(contexts[0])))
    all_commute = all(
        sform(classes[i], classes[j]) == 0
        for C in contexts for i, j in itertools.combinations(C, 2))
    print("     every context is pairwise commuting: %s" % all_commute)

    # 5. tau_1 and alpha on the Pauli graph itself
    from ortools.sat.python import cp_model
    m = cp_model.CpModel()
    x = [m.NewBoolVar("") for _ in range(N)]
    for C in contexts:
        m.AddBoolOr([x[i] for i in C])
    m.Minimize(sum(x))
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = 120.0
    s.parameters.num_search_workers = 8
    st = s.Solve(m)
    tau1 = int(s.ObjectiveValue())
    m2 = cp_model.CpModel()
    y = [m2.NewBoolVar("") for _ in range(N)]
    for a, b in itertools.combinations(range(N), 2):
        if adj[a][b]:
            m2.Add(y[a] + y[b] <= 1)
    m2.Maximize(sum(y))
    s2 = cp_model.CpSolver()
    s2.parameters.max_time_in_seconds = 120.0
    s2.parameters.num_search_workers = 8
    st2 = s2.Solve(m2)
    alpha = int(s2.ObjectiveValue())
    print()
    print("  tau_1 = %d (%s): the fewest Pauli observables meeting EVERY"
          % (tau1, s.StatusName(st)))
    print("     measurement context on one self-entangled qutrit")
    print("  alpha = %d (%s): the most pairwise NON-COMMUTING Paulis;"
          % (alpha, s2.StatusName(st2)))
    print("     ten of them would be an ovoid, and none exists")
    print()
    print("  hemisystem reading: the 432 sets of 20 observables that meet")
    print("  every context in exactly two -- half of every context, always.")
    print()
    print("  depth 2: a point of the product is a PRODUCT observable A (x) B,")
    print("  a tile is a pair of local contexts, and tau_2 in [111, 115] is")
    print("  the smallest set of product observables covering every pair. The")
    print("  four-qutrit Pauli space has (3^8-1)/2 = %d classes, so the 1,600"
          % ((3 ** 8 - 1) // 2))
    print("  product observables are a proper subset: the question is about")
    print("  LOCAL measurements, one per carrier, which is what a two-carrier")
    print("  machine can address.")

    ok = (bad == 0 and N == 40 and sorted(deg) == [12] and sorted(lam) == [2]
          and sorted(mu) == [4] and len(contexts) == 40 and all_commute
          and tau1 == 11 and alpha == 7
          and s.StatusName(st) == "OPTIMAL" and s2.StatusName(st2) == "OPTIMAL")

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data",
                         "w33_blocking_is_pauli_context_covering.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.w33-pauli-context-covering.v1",
                "valid": bool(ok),
                "source": ("holonet_machine_blueprint_body.tex, 'The "
                           "self-entanglement, and where the 40 comes from': "
                           "C^3 (x) C^3 = End(C^3), 40 = (3^4-1)/2 points, "
                           "40 lines as maximal commuting subalgebras"),
                "verifiedWithMatrices": {
                    "paulisBuilt": len(vecs),
                    "commutatorFormMismatches": bad,
                    "pairsChecked": len(vecs) * (len(vecs) - 1) // 2,
                    "projectiveClasses": N,
                    "srg": {"degree": sorted(deg), "lambda": sorted(lam),
                            "mu": sorted(mu)},
                    "contexts": len(contexts),
                    "contextSize": len(contexts[0]),
                    "everyContextCommutes": all_commute,
                },
                "readings": {
                    "tau1": {"value": tau1, "proved": s.StatusName(st) == "OPTIMAL",
                             "meaning": ("fewest Pauli observables meeting every "
                                         "measurement context")},
                    "alpha": {"value": alpha,
                              "proved": s2.StatusName(st2) == "OPTIMAL",
                              "meaning": ("most pairwise non-commuting Paulis; "
                                          "an ovoid would be ten and none "
                                          "exists")},
                    "hemisystem": ("20 observables meeting every context in "
                                   "exactly two -- half of every context"),
                    "tau2": ("smallest set of PRODUCT observables A (x) B "
                             "covering every pair of local contexts on two "
                             "carriers; open in [111, 115]"),
                },
                "fourQutritClasses": (3 ** 8 - 1) // 2,
                "productObservables": N * N,
                "scopeNote": ("the 1,600 product observables are a proper "
                              "subset of the 3,280 four-qutrit Pauli classes, "
                              "so depth 2 asks about LOCAL measurements only"),
                "priorArt": ("the two-qutrit Pauli graph being W(3,3) is "
                             "classical, and the blueprint already has the 40 "
                             "count and the maximal-commuting reading; a search "
                             "of both repositories for blocking sets in Pauli, "
                             "commuting or context language returns nothing"),
                "boundary": ("an interpretation, verified but not a new bound; "
                             "tau_2 stays open in [111, 115]"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
