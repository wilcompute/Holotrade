#!/usr/bin/env python3
"""
The compiler's open boundary is a to-do, not a barrier: the qutrit Clifford
group splits over its symplectic quotient, so a symplectic word has a canonical
Clifford lift and there is no cocycle to bookkeep.

THE BOUNDARY I LEFT.  e05515f closed with "it emits SYMPLECTIC transvections:
the Clifford group is their central extension, and the phase bookkeeping needed
to lift a symplectic program to an actual qutrit circuit is NOT done here". That
was honest but uninformative -- it did not say whether the bookkeeping is hard,
easy, or impossible. The W33-Theory track is now lowering those transvections to
a photonic F/CX micro-ISA, so which of the three it is has become the live
question.

IT IS EASY, BECAUSE THE EXTENSION SPLITS.  Building the one-qutrit Clifford
group explicitly as unitaries modulo GLOBAL PHASE, from X, Z, the Fourier gate
and the phase gate:

    Pauli group mod global phase        9
    Clifford group mod global phase   216
    quotient                           24   = |SL(2,3)|

and searching for a complement -- a subgroup of order 24 meeting the Pauli part
only in the identity:

    COMPLEMENT FOUND, order 24, trivial intersection with the Paulis

So the sequence 1 -> P -> C -> Sp -> 1 SPLITS. C is a semidirect product, there
is a homomorphic section Sp -> C, and a product of symplectic transvections
lifts to the product of their canonical Clifford lifts with nothing left over.
No 2-cocycle, no phase table.

THIS IS THE KNOWN ODD-p PICTURE, AND IT IS EXACTLY WHERE QUBITS DIFFER.  The
literature gives the semidirect product Z_p^{2n} : Sp(2n,p) for odd prime p, and
states explicitly that the Clifford group CANNOT be written that way for qubits.
Verified here at n = 1 and cited for general n; the n = 2 section is not
tabulated below.

AND THAT IS THE SAME DICHOTOMY THIS SESSION KEPT FINDING.  q = 2 has been the
exceptional case at every turn: no centre to quotient (6bb8975), the classical
length induction breaking (3595bd1), an anomaly set 178 times denser. The
Clifford extension failing to split at p = 2 while splitting at every odd p is
another instance of the same split, arrived at from the representation side
rather than the geometric one. Recorded as an observation about where the
boundary falls, not as a claim that these are the same theorem.

WHAT THIS CHANGES FOR THE COMPILER.  e05515f's word is a sequence of
transvections realising a target in Sp(4,3). Because a homomorphic section
exists, that word lifts termwise: choose the canonical Clifford for each
transvection once, and the product IS the canonical Clifford of the target. The
remaining work is to TABULATE the section for n = 2 -- eighty unitaries, chosen
once -- which is engineering with a guaranteed answer, not an open problem. The
boundary should be read as "not done" rather than "not known how".

SCOPE.  The splitting is verified EXHAUSTIVELY at n = 1: the Clifford group is
constructed as a complete closure modulo global phase, its order and the Pauli
subgroup's order are checked against the expected 216 and 9, and the complement
is exhibited with its intersection computed. It is NOT verified at n = 2 -- the
two-qutrit Clifford group modulo phase has order 4,199,040 and was not built --
so for the compiler's actual dimension this rests on the cited general odd-p
result. The eighty canonical lifts are NOT produced here. Unitaries are compared
numerically with entries rounded at 1e-6, not in exact cyclotomic arithmetic.
tau_2 is untouched.
"""

import cmath
import json
import os
import random
import sys

import numpy as np

ROOT = r"C:\Repos\Holotrade"
W = cmath.exp(2j * cmath.pi / 3)


def canon(U):
    V = U.flatten()
    i = int(np.argmax(np.abs(V) > 1e-9))
    V = V / V[i]
    return tuple(np.round(V.real, 6) + 1j * np.round(V.imag, 6))


def closure(gens, d=3):
    I = np.eye(d, dtype=complex)
    seen = {canon(I): I}
    fr = [I]
    while fr:
        nx = []
        for A in fr:
            for g in gens:
                B = g @ A
                k = canon(B)
                if k not in seen:
                    seen[k] = B
                    nx.append(B)
        fr = nx
    return seen


def main():
    X = np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]], dtype=complex)
    Z = np.diag([1, W, W ** 2]).astype(complex)
    F = np.array([[W ** (j * k) for k in range(3)] for j in range(3)],
                 dtype=complex) / np.sqrt(3)
    S = np.diag([1, 1, W]).astype(complex)

    P = closure([X, Z])
    C = closure([X, Z, F, S])
    Pk = set(P)
    quotient = len(C) // len(P)

    keys = list(C)
    rnd = random.Random(3)
    found, tries = None, 0
    for _ in range(20000):
        a, b = rnd.sample(keys, 2)
        H = set(closure([C[a], C[b]]))
        tries += 1
        if len(H) == quotient and len(H & Pk) == 1:
            found = H
            break

    print("THE PHASE LIFT HAS NO OBSTRUCTION")
    print("=" * 72)
    print("  e05515f left the phase bookkeeping undone without saying whether")
    print("  it is hard, easy, or impossible. It is easy.")
    print()
    print("  one-qutrit groups modulo GLOBAL PHASE:")
    print("     Pauli                %4d   [expect 9]" % len(P))
    print("     Clifford             %4d   [expect 216]" % len(C))
    print("     quotient C/P         %4d   [= |SL(2,3)| = 24]" % quotient)
    print()
    print("  searched %d generated subgroups for a complement" % tries)
    if found:
        print("     COMPLEMENT FOUND: order %d, Pauli intersection %d"
              % (len(found), len(found & Pk)))
        print("     -> 1 -> P -> C -> Sp -> 1 SPLITS; C is a semidirect")
        print("        product and there is a homomorphic section Sp -> C.")
    print()
    print("  So a product of symplectic transvections lifts to the product of")
    print("  their canonical Clifford lifts with NOTHING left over: no")
    print("  2-cocycle, no phase table.")
    print()
    print("  This is the known odd-p picture -- Z_p^2n : Sp(2n,p) -- and the")
    print("  literature states explicitly that QUBITS are the case where the")
    print("  Clifford group is NOT such a semidirect product. Verified here at")
    print("  n = 1; cited for general n; the n = 2 section is not tabulated.")
    print()
    print("  Same dichotomy this session kept finding: q = 2 has no centre to")
    print("  quotient (6bb8975), breaks the classical length induction")
    print("  (3595bd1), and carries a 178x denser anomaly set. The Clifford")
    print("  extension failing to split at p = 2 is another instance, reached")
    print("  from representation theory rather than geometry. An observation")
    print("  about where the boundary falls, not a claim of one theorem.")
    print()
    print("  FOR THE COMPILER: e05515f's word lifts TERMWISE. Choose the")
    print("  canonical Clifford for each of the eighty transvections once and")
    print("  the product is the canonical Clifford of the target. What remains")
    print("  is tabulation -- engineering with a guaranteed answer -- so the")
    print("  boundary reads 'not done', not 'not known how'.")

    ok = (len(P) == 9 and len(C) == 216 and quotient == 24
          and found is not None and len(found) == 24
          and len(found & Pk) == 1)

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "phase_lift_has_no_obstruction.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.phase-lift-no-obstruction.v1",
                "valid": bool(ok),
                "theBoundaryLeft": ("e05515f closed with 'the phase bookkeeping "
                                    "needed to lift a symplectic program to an "
                                    "actual qutrit circuit is NOT done here' -- "
                                    "honest but uninformative, since it did not "
                                    "say whether the bookkeeping is hard, easy "
                                    "or impossible; the W33-Theory track is now "
                                    "lowering those transvections to a photonic "
                                    "F/CX micro-ISA, so which it is has become "
                                    "the live question"),
                "oneQutritGroups": {
                    "pauliModGlobalPhase": len(P),
                    "cliffordModGlobalPhase": len(C),
                    "quotient": quotient,
                    "quotientIs": "|SL(2,3)| = 24",
                },
                "splitting": {
                    "subgroupsSearched": tries,
                    "complementOrder": len(found) if found else None,
                    "pauliIntersection": len(found & Pk) if found else None,
                    "splits": bool(found),
                    "consequence": ("1 -> P -> C -> Sp -> 1 splits, C is a "
                                    "semidirect product, and a product of "
                                    "symplectic transvections lifts to the "
                                    "product of their canonical Clifford lifts "
                                    "with nothing left over -- no 2-cocycle, no "
                                    "phase table"),
                },
                "literature": ("the semidirect product Z_p^{2n} : Sp(2n,p) for "
                               "odd prime p is the known picture, and the "
                               "literature states explicitly that QUBITS are the "
                               "case where the Clifford group is NOT such a "
                               "semidirect product; verified here at n = 1, "
                               "cited for general n"),
                "sameDichotomyAsTheSession": ("q = 2 has been the exceptional "
                                              "case throughout: no centre to "
                                              "quotient (6bb8975), the classical "
                                              "length induction breaking "
                                              "(3595bd1), a 178x denser anomaly "
                                              "set. The Clifford extension "
                                              "failing to split at p = 2 while "
                                              "splitting at odd p is another "
                                              "instance, reached from "
                                              "representation theory rather than "
                                              "geometry. Recorded as an "
                                              "OBSERVATION about where the "
                                              "boundary falls, not a claim that "
                                              "these are the same theorem"),
                "whatItChangesForTheCompiler": ("e05515f's word lifts TERMWISE: "
                                                "choose the canonical Clifford "
                                                "for each of the eighty "
                                                "transvections once, and the "
                                                "product is the canonical "
                                                "Clifford of the target. The "
                                                "remaining work is TABULATION "
                                                "for n = 2 -- engineering with a "
                                                "guaranteed answer, not an open "
                                                "problem -- so the boundary "
                                                "reads 'not done' rather than "
                                                "'not known how'"),
                "boundary": ("the splitting is verified EXHAUSTIVELY at n = 1: "
                             "the Clifford group is a complete closure modulo "
                             "global phase, its order and the Pauli subgroup's "
                             "order are checked against 216 and 9, and the "
                             "complement is exhibited with its intersection "
                             "computed. It is NOT verified at n = 2 -- the "
                             "two-qutrit Clifford group modulo phase has order "
                             "4,199,040 and was not built -- so for the "
                             "compiler's actual dimension this rests on the "
                             "cited general odd-p result. The eighty canonical "
                             "lifts are NOT produced here. Unitaries are "
                             "compared numerically at 1e-6, not in exact "
                             "cyclotomic arithmetic. tau_2 is untouched"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
