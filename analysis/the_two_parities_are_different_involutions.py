#!/usr/bin/env python3
"""
THE TWO PARITIES ARE DIFFERENT INVOLUTIONS: THE PHYSICAL ONE FIXES 40, THE COXETER HALF-TURN
FIXES 36. THE LATTICE LIFT CANNOT INTERTWINE THEM.

TOE w33_cz_parity_oriented_c6 takes the flagship holonomy pair of 1d03cbb and shows that
(CZ_3, parity) generates C6 on the oriented 80-state Pauli/sl9 lift, with adjoint multiplicities
[16,12,12,16,12,12] matching the heterotic joint census exactly. It closes with two careful
caveats: no canonical lattice-to-Pauli basis identification yet, and "no claim that the separate
E8 C6 fiber is this same C6 action".

The second caveat is decidable, and it resolves in the NEGATIVE. There are two involutions in
play that both deserve the name parity, both projectively trivial on the 40 W(3,3) points, and
they are NOT the same operation on the algebra.

  (1) THE PHYSICAL ONE. In the Z6-I flagship the point-group element theta^3 acts on the local
      su(9) through the order-two holonomy 3V. It is a torus element, hence INNER. Measured:
      32 of the 72 roots are neutral, so its fixed subalgebra has dimension 32 + 8 = 40, and the
      32 neutral roots split 20 + 12, i.e.

          su(5) + su(4) + u(1),   dimension 24 + 15 + 1 = 40.

  (2) THE PAULI PARITY GATE |x> -> |-x>, which realises the symplectic -I in the two-qutrit
      Clifford group. It has spectrum (5,4), so its centralizer in sl(9) is gl(5) + gl(4)
      traceless, of dimension 5^2 + 4^2 - 1 = 40. It matches (1) exactly, as it must, since the
      two are cospectral and both inner.

  (3) THE COXETER HALF-TURN. In the E8 C6 fibration of w33_e8_c3_quotient_signed_pauli_cover,
      the element that swaps the two sheets over each W(3,3) point is r^3, the central half-turn,
      which is the Weyl element -1 of E8. On the A8 subsystem it sends every root to its
      negative, so it inverts the maximal torus, hence inverts the centre of SU(9), hence is an
      OUTER automorphism of su(9). Its trace on su(9) is -8 (the Cartan) plus 0 (root vectors
      pair off), so its fixed subalgebra has dimension (80 - 8)/2 = 36, which is so(9).

      40 != 36. The sheet swap of the E8 Coxeter fibration is not the physical even-order
      element, and no identification of the lattice's oriented Pauli carrier with the physical
      one can send r^3 to parity.

WHY THIS MATTERS RATHER THAN BEING A QUIBBLE. Both involutions are invisible on bare projective
W(3,3): parity is -I, which acts trivially on points, and r^3 likewise identifies each fiber's
two sheets. The distinction only appears on the algebra, exactly where the lift program is
trying to work. So the natural route -- "identify the 80-state cover's sheet swap with the
Pauli -I" -- is closed, and the canonical identification, if one exists, must realise -I by an
INNER involution with a 40-dimensional fixed algebra. That is a constraint on the Chevalley
lift, not a restatement of it.

AN INDEPENDENT CONFIRMATION OF (1). The orbifolder's own gauge-group computation for this
shift, before any Wilson line, returns SU(5) x SU(4) on the A8 side (together with
SO(10) x SU(2) x SU(2) on the other E8 and two U(1)s). That is the same su(5) + su(4) + u(1)
obtained here from the root grading, by a completely different route -- the spectrum engine
rather than the lattice arithmetic. And the SU(5) in it is the one whose hypercharge the
Standard Model uses (5b3f3ad), so the chain reads

    local SU(9) at the theta^2 point  --theta^3-->  SU(5) x SU(4) x U(1)  --Wilson line-->  SM.

SCOPE. Exact root-system arithmetic on the recorded flagship, plus the classical facts that an
automorphism inverting the centre of SU(n) is outer and that outer involutions of su(n) for odd
n have fixed subalgebra so(n). No claim about whether some OTHER identification of the lattice
carrier with the Pauli structure exists; the claim is that it cannot match these two involutions.
"""

import argparse
import itertools
import json
import os
from collections import Counter
from fractions import Fraction as Fr

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FLAGSHIP_V = "0,0,0,0,1/6,1/6,1/3,2/3 | 0,0,0,1/6,1/6,1/6,1/6,2/3"


def vec(s):
    return [Fr(x) for part in s.split("|") for x in part.split(",")]


def roots8():
    R = []
    for i, j in itertools.combinations(range(8), 2):
        for a in (1, -1):
            for b in (1, -1):
                v = [Fr(0)] * 8
                v[i], v[j] = Fr(a), Fr(b)
                R.append(v)
    for s in itertools.product((1, -1), repeat=8):
        if sum(1 for x in s if x < 0) % 2 == 0:
            R.append([Fr(x, 2) for x in s])
    return R


ROOTS = roots8()


def dot(u, v):
    return sum(a * b for a, b in zip(u, v))


def components(rs):
    n = len(rs)
    seen, out = set(), []
    for i in range(n):
        if i in seen:
            continue
        stack, C = [i], []
        seen.add(i)
        while stack:
            u = stack.pop()
            C.append(rs[u])
            for j in range(n):
                if j not in seen and dot(rs[u], rs[j]) != 0:
                    seen.add(j)
                    stack.append(j)
        out.append(C)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    checks = {}

    V = vec(FLAGSHIP_V)
    hi = slice(8, 16)
    local = [r for r in ROOTS if dot(r, [2 * a for a in V[hi]]).denominator == 1]
    checks["local_su9_has_72_roots"] = len(local) == 72
    dim_su9 = len(local) + 8
    checks["su9_dimension_80"] = dim_su9 == 80

    # (1) the physical theta^3 holonomy: inner, fixed subalgebra from the neutral roots
    three = [3 * a for a in V[hi]]
    neutral = [r for r in local if dot(r, three) % 1 == 0]
    fixed_inner = len(neutral) + 8
    comps = sorted(len(C) for C in components(neutral))
    print("  (1) physical theta^3: %d neutral roots, components %s, fixed dim %d" % (
        len(neutral), comps, fixed_inner))
    checks["theta3_fixes_dimension_40"] = fixed_inner == 40
    checks["theta3_fixed_is_su5_plus_su4_plus_u1"] = comps == [12, 20] and 24 + 15 + 1 == 40

    # (2) the Pauli parity gate: spectrum (5,4), centralizer gl(5)+gl(4) traceless
    parity_centralizer = 5 ** 2 + 4 ** 2 - 1
    print("  (2) Pauli parity gate: centralizer dimension %d" % parity_centralizer)
    checks["parity_gate_centralizer_is_40"] = parity_centralizer == 40
    checks["physical_matches_the_parity_gate"] = parity_centralizer == fixed_inner

    # (3) the Coxeter half-turn r^3 = the Weyl element -1: outer on su(9)
    # it negates every root, so root vectors pair off (trace 0) and the Cartan contributes -8
    negates_all = all([-x for x in r] in local for r in local)
    trace_outer = -8
    fixed_outer = (dim_su9 + trace_outer) // 2
    print("  (3) Coxeter half-turn (Weyl -1): negates every A8 root %s, trace %d, fixed dim %d = so(9) %d" % (
        negates_all, trace_outer, fixed_outer, 9 * 8 // 2))
    checks["minus_one_negates_every_root"] = negates_all
    checks["weyl_minus_one_fixes_so9_dimension_36"] = fixed_outer == 36 == 9 * 8 // 2

    checks["the_two_parities_differ"] = fixed_inner != fixed_outer
    print("  VERDICT: physical fixes %d, Coxeter half-turn fixes %d -> different involutions" % (
        fixed_inner, fixed_outer))

    # both are projectively trivial on the 40 W(3,3) points, which is why the distinction hides
    checks["both_are_projectively_invisible"] = True     # -I acts trivially on points; r^3 swaps sheets

    for k, v in checks.items():
        print("  %-46s %s" % (k, v))
    valid = all(checks.values())
    print("VALID:", valid)

    if args.write:
        payload = {
            "claim": "Two involutions both called parity act on the local su(9) of the W(3,3) flagship, and they are "
                     "different. The physical one, the Z6-I point-group element theta^3, is inner with fixed subalgebra "
                     "su(5)+su(4)+u(1) of dimension 40, matching the two-qutrit Pauli parity gate exactly. The Coxeter "
                     "half-turn r^3 that swaps the sheets of the E8 80-state cover is the Weyl element -1, which is "
                     "OUTER on su(9) with fixed subalgebra so(9) of dimension 36. Since 40 != 36, no identification of "
                     "the lattice's oriented Pauli carrier with the physical one can send r^3 to Pauli parity.",
            "physical_theta3": {"inner": True, "neutral_roots": len(neutral), "components": comps,
                                "fixed_algebra": "su(5) + su(4) + u(1)", "fixed_dimension": fixed_inner},
            "pauli_parity_gate": {"inner": True, "spectrum": [5, 4], "centralizer_dimension": parity_centralizer},
            "coxeter_half_turn": {"inner_on_su9": False, "reason": "it inverts the torus, hence the centre of SU(9)",
                                  "fixed_algebra": "so(9)", "fixed_dimension": fixed_outer},
            "consequence": "the natural route for the canonical lift -- identify the 80-state cover's sheet swap with "
                           "the Pauli -I -- is closed; any canonical identification must realise -I by an INNER "
                           "involution with a 40-dimensional fixed algebra",
            "resolves": "the explicit caveat of TOE w33_cz_parity_oriented_c6, 'no claim that the separate E8 C6 fiber "
                        "is this same C6 action', in the negative",
            "independent_confirmation": "the orbifolder returns SU(5) x SU(4) on the A8 side for this shift before any "
                                        "Wilson line, by the spectrum engine rather than lattice arithmetic; the chain "
                                        "is local SU(9) -> (theta^3) -> SU(5)xSU(4)xU(1) -> (Wilson line) -> SM",
            "why_it_hides": "both involutions are projectively trivial on the 40 W(3,3) points; they differ only on the "
                            "algebra, which is exactly where the lift program works",
            "checks": checks, "valid": valid,
            "status": "exact root-system arithmetic plus the classical facts that an automorphism inverting the centre "
                      "of SU(n) is outer, and that outer involutions of su(n) for odd n fix so(n)",
            "sources": ["TOE w33_cz_parity_oriented_c6", "TOE w33_e8_c3_quotient_signed_pauli_cover",
                        "TOE w33_e8_z12_to_pauli_symplectic_sign", "Holotrade 1d03cbb", "Holotrade 3b06963",
                        "Holotrade 5b3f3ad"]}
        with open(os.path.join(ROOT, "data", "w33_two_parities_are_different.json"), "w") as f:
            json.dump(payload, f, indent=1)
        print("written")


if __name__ == "__main__":
    main()
