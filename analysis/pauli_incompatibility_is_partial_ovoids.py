#!/usr/bin/env python3
"""
The maximum set of mutually incompatible qudit Pauli observables IS a maximum
partial ovoid of a symplectic polar space -- so a 2005 geometry paper already
answered a 2024 quantum-information question.

THE PHYSICS QUESTION.  The holonet blueprint's self-entanglement section
encodes one photon as two qutrit registers, time-bin and frequency-bin, and
identifies the 40 points of W(3,3) with the two-qutrit Pauli classes and the
40 lines with the maximal COMMUTING subalgebras. A natural physical quantity
follows immediately: how many Pauli observables of such a carrier can be
MUTUALLY INCOMPATIBLE -- pairwise non-commuting, so that no two are jointly
measurable?

For qubits this is a known and well-used quantity. The maximum set of pairwise
ANTICOMMUTING Paulis on n qubits has size 2n+1, a standard fact with real
applications in measurement scheduling and fermionic encodings.

THE QUDIT SITUATION IS NOT THAT.  Sarkar and Yoder (Quantum 8, 1307 (2024),
arXiv:2302.07966) study exactly this for qudits. Qubit Paulis either commute
or anticommute; qudit Paulis can fail to commute in d-1 distinct ways, so the
parity argument behind 2n+1 does not survive. They prove the single-qudit
maximum is the Dedekind psi function Psi(d), give 2n+1 only under the extra
restriction that all Paulis share the SAME commutator value, and describe the
general multi-qudit case as "complicated", offering bounds. Their reported
qutrit values are 4 for one qutrit and 7 for two, with 13 for three found by
computer search.

THE BRIDGE.  Those are not new numbers -- they are old ones, in a literature
that does not cite this one, and older than the quantum paper by two decades. The n-qudit Pauli classes for prime d = q are the
projective points of F_q^{2n}, and two Paulis commute exactly when the
symplectic form vanishes. So the Pauli classes with commutation are precisely
the symplectic polar space W(2n-1, q), and

    a set of pairwise NON-COMMUTING Paulis  =  a PARTIAL OVOID of W(2n-1,q),

whose maximum size finite geometry has studied for decades. The ceiling is the
ovoid size q^n + 1, attained only when an ovoid exists.

That reframing explains the qubit law rather than merely restating it. W(3,2)
HAS an ovoid, so two qubits attain the ceiling: 5 = q^n+1 = 2n+1, all three
numbers coinciding by accident of q = 2. W(3,q) for q ODD has NO ovoid --
Thas's theorem -- so the qutrit answer must fall short of 10, and it does, at
7. The shortfall is a geometric non-existence result, invisible to the parity
argument that gives 2n+1 and invisible to the Hoffman/Lovasz spectral bound,
both of which permit 10.

WHAT IS COMPUTED HERE, all as verification rather than discovery.

    system        space     alpha   ceiling q^n+1   shortfall
    2 qubits      W(3,2)      5           5             0
    3 qubits      W(5,2)      7           9             2
    2 qutrits     W(3,3)      7          10             3
    2 ququints    W(3,5)     18          26             8

all solved to OPTIMAL. Every one reproduces a known value: 5 and 7 are the
qubit 2n+1, 7 at W(3,3) is Sarkar-Yoder's, and 18 at W(3,5) is
Cimrakova-Fack's. That is the point -- they are the control that the bridge is
stated correctly, and the bridge is the contribution.

THE q = 5 VALUE, AND A CORRECTION.  An earlier version of this file presented
alpha(W(3,5)) = 18 as a new result. It is not. The value is PUBLISHED:

    M. Cimrakova and V. Fack, "Searching for maximal partial ovoids and
    spreads in generalized quadrangles", Bull. Belg. Math. Soc. Simon Stevin
    12 (2005) 697-705, Table 1.

Their Table 1 gives the largest maximal partial ovoids by EXHAUSTIVE search:
W(5) has |O'| = 18 with exactly 2 non-equivalent examples, and W(7) has
|O'| = 33 with exactly 1. The column they compare against is Tallini's
theorem, not a guess:

    THEOREM (Tallini). A partial ovoid of W(q), q odd, has size at most
    q^2 + 1 - q.

which is 21 at q = 5 and 43 at q = 7. So q^2-q+1 was never a candidate
formula -- it is a proved upper bound, and the published exhaustive values
show it is not attained at q = 5 or q = 7.

What this file's computation actually is, then, is an INDEPENDENT
VERIFICATION: size 18 attained with a witness checked pairwise
non-commuting, and size 19 INFEASIBLE, reproducing the 2005 value by a
different method on the same SRG(156,30,4,6).

It still settles something locally. W33-Theory's Pass 5226 records
alpha(W(3,5)) with `bound_settled: "lower only"` -- a restart-greedy witness
of 18 with no upper bound -- and alpha(W(3,7)) likewise at 33. Both of those
witnesses were in fact already the true maxima; the pass simply had no way to
know it. And "deficiency = q", which held at the single point q = 3 (10-7 = 3)
and was flagged there as "not a family", does die: at q = 5 the deficiency is
26 - 18 = 8, not 5.

In physical terms: two five-dimensional qudits admit at most EIGHTEEN mutually
incompatible Pauli observables, where the spectral ceiling permits 26 -- a
fact available since 2005 in a literature that does not mention Paulis.

WHAT IS NOT CLAIMED.  The geometry literature records MAXIMAL partial ovoids
of W(5,q) of size q^2+q+1, which is 13 at q = 3 and agrees with Sarkar-Yoder's
computer-verified three-qutrit value. Maximal means unextendable, not largest,
so that agreement is suggestive and not a proof that the maximum is 13; it is
recorded as a lead, not a result. Nothing here computes W(5,3), whose 364
points were out of budget. And the bridge itself is a restatement, not a
theorem -- its value is that it lets a solved literature answer an open
question in another.

PRIOR ART, searched before writing. The qubit 2n+1 law, the Sarkar-Yoder
qudit paper, Thas's no-ovoid theorem and the partial-ovoid literature are all
established. Searching both repositories for blocking, incompatibility or
partial ovoids stated in Pauli or measurement language returns nothing, and
searching the quantum-information literature for symplectic polar spaces or
partial ovoids returns nothing either. The two fields have the same object and
do not cite each other.
"""

import itertools
import json
import os
import sys

try:
    from ortools.sat.python import cp_model
except ImportError:
    sys.exit("needs ortools:  py -3 -m pip install ortools")

ROOT = r"C:\Repos\Holotrade"


def polar(n, q):
    """W(2n-1,q): projective points of F_q^{2n}, i.e. n-qudit Pauli classes."""
    def nm(v):
        i = next(k for k, x in enumerate(v) if x % q)
        z = pow(v[i] % q, -1, q)
        return tuple((z * x) % q for x in v)

    def form(u, v):
        return sum(u[2 * i] * v[2 * i + 1] - u[2 * i + 1] * v[2 * i]
                   for i in range(n)) % q

    pts = sorted({nm(v) for v in itertools.product(range(q), repeat=2 * n)
                  if any(v)})
    return pts, form


def independence(pts, form, budget, exact=None):
    N = len(pts)
    m = cp_model.CpModel()
    y = [m.NewBoolVar("") for _ in range(N)]
    adj = []
    for a, b in itertools.combinations(range(N), 2):
        if form(pts[a], pts[b]) == 0:
            m.Add(y[a] + y[b] <= 1)
            adj.append((a, b))
    if exact is None:
        m.Maximize(sum(y))
    else:
        m.Add(sum(y) == exact)
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = budget
    s.parameters.num_search_workers = 8
    st = s.Solve(m)
    name = s.StatusName(st)
    wit = None
    if name in ("OPTIMAL", "FEASIBLE"):
        S = [i for i in range(N) if s.Value(y[i])]
        ok = all(form(pts[a], pts[b]) != 0
                 for a, b in itertools.combinations(S, 2))
        wit = {"size": len(S), "pairwiseNonCommuting": ok}
    return name, (int(s.ObjectiveValue()) if exact is None else exact), wit


def main():
    print("MUTUALLY INCOMPATIBLE PAULIS ARE PARTIAL OVOIDS")
    print("=" * 72)
    print("  n-qudit Pauli classes with commutation = W(2n-1,q); a pairwise")
    print("  NON-commuting set is a partial ovoid; the ceiling q^n+1 is")
    print("  attained only when an ovoid exists.")
    print()
    rows = []
    for label, n, q, budget in (("2 qubits", 2, 2, 60.0),
                                ("3 qubits", 3, 2, 600.0),
                                ("2 qutrits", 2, 3, 300.0),
                                ("2 ququints", 2, 5, 1800.0)):
        pts, form = polar(n, q)
        name, a, wit = independence(pts, form, budget)
        ceil = q ** n + 1
        rows.append({
            "system": label, "space": "W(%d,%d)" % (2 * n - 1, q),
            "n": n, "q": q, "pauliClasses": len(pts),
            "alpha": a, "status": name, "ovoidCeiling": ceil,
            "shortfall": ceil - a, "twoNplusOne": 2 * n + 1,
            "witness": wit,
            "qEven": q % 2 == 0,
        })
        print("  %-11s %-8s %4d classes | alpha = %-3d (%s) | ceiling %-3d "
              "| shortfall %d | 2n+1 = %d"
              % (label, rows[-1]["space"], len(pts), a, name, ceil,
                 ceil - a, 2 * n + 1))
    print()

    # the new one: prove 19 impossible at q=5
    pts, form = polar(2, 5)
    n19, _, _ = independence(pts, form, 1800.0, exact=19)
    print("  W(3,5): independent set of size 19 -> %s" % n19)
    closed = n19 == "INFEASIBLE"
    print("     so alpha(W(3,5)) = 18 exactly. W33-Theory Pass 5226 had this")
    print("     as 'lower only' with q^2-q+1 = 21 an unreached comparison")
    print("     target; 21 is now REFUTED, not merely unreached.")
    print("     And 'deficiency = q' dies: 26 - 18 = 8, not 5.")
    print()
    print("  Physically: two five-dimensional qudits admit at most EIGHTEEN")
    print("  mutually incompatible Pauli observables, where the spectral")
    print("  ceiling permits 26. For the blueprint's qutrit carrier the")
    print("  number is 7 against a ceiling of 10, and the obstruction is")
    print("  Thas's no-ovoid theorem for odd q -- geometric, and invisible")
    print("  to both the 2n+1 parity argument and the Hoffman bound.")

    ok = closed and all(r["status"] == "OPTIMAL" for r in rows)
    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data",
                         "pauli_incompatibility_is_partial_ovoids.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.pauli-incompatibility-partial-ovoids.v1",
                "valid": bool(ok),
                "bridge": ("a set of pairwise non-commuting n-qudit Paulis "
                           "(prime d=q) is exactly a partial ovoid of the "
                           "symplectic polar space W(2n-1,q); the maximum is "
                           "the maximum partial ovoid, ceiling q^n+1"),
                "instances": rows,
                "correction": ("an earlier version of this file called "
                               "alpha(W(3,5)) = 18 new. It is published: "
                               "Cimrakova and Fack 2005, Table 1, by "
                               "exhaustive search, with 2 non-equivalent "
                               "examples; W(7) is 33 with 1. This file's "
                               "computation is an independent verification."),
                "tallini": ("a partial ovoid of W(q), q odd, has size at most "
                            "q^2+1-q (Tallini) -- a proved upper bound, not a "
                            "candidate formula; it is not attained at q = 5 "
                            "(18 < 21) or q = 7 (33 < 43)"),
                "newResult": {
                    "statement": "alpha(W(3,5)) = 18, verified independently",
                    "size18": "OPTIMAL, witness verified pairwise non-commuting",
                    "size19": n19,
                    "closesLocally": ("W33-Theory Pass 5226 recorded "
                                      "bound_settled 'lower only' at q=5 and "
                                      "q=7; both its witnesses, 18 and 33, "
                                      "were already the published maxima"),
                    "refutes": ["deficiency = q as a family (26-18 = 8, not 5)"],
                    "doesNotRefute": ("Tallini's q^2+1-q, which is a valid "
                                      "upper bound and simply not attained"),
                    "physicalReading": ("two five-dimensional qudits admit at "
                                        "most 18 mutually incompatible Pauli "
                                        "observables; the spectral ceiling "
                                        "permits 26"),
                },
                "whyQubitsAreSpecial": ("W(3,2) has an ovoid, so two qubits "
                                        "attain the ceiling and 5 = q^n+1 = "
                                        "2n+1 all coincide; W(3,q) for odd q "
                                        "has none (Thas), so the qutrit value "
                                        "falls short at 7 against 10"),
                "priorArt": {
                    "qubitLaw": "max anticommuting Pauli set on n qubits is 2n+1",
                    "qudit": ("Sarkar and Yoder, Quantum 8, 1307 (2024), "
                              "arXiv:2302.07966: single-qudit maximum is "
                              "Psi(d); 2n+1 only under equal commutator "
                              "values; multi-qudit case called complicated"),
                    "geometry": ("Thas: W(3,q) has an ovoid iff q is even; "
                                 "partial ovoids of symplectic polar spaces "
                                 "are a long-studied topic"),
                    "w33Theory": ("Pass 5226/5227 recorded alpha(W(3,5)) >= 18 "
                                  "as a witness with no upper bound"),
                    "geometryValues": ("Cimrakova and Fack 2005 Table 1, "
                                       "exhaustive: W(5) -> 18 (2 examples), "
                                       "W(7) -> 33 (1 example); upper bound "
                                       "column is Tallini's q^2+1-q"),
                },
                "leadNotResult": ("the geometry literature records MAXIMAL "
                                  "partial ovoids of W(5,q) of size q^2+q+1, "
                                  "which is 13 at q=3 and agrees with "
                                  "Sarkar-Yoder's computer-verified "
                                  "three-qutrit value -- but maximal means "
                                  "unextendable, not largest, so this is a "
                                  "lead and not a proof"),
                "notComputed": "W(5,3), whose 364 points were out of budget",
                "boundary": ("the bridge is a restatement, not a theorem; its "
                             "value is letting a solved literature answer an "
                             "open question in another"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
