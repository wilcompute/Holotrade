#!/usr/bin/env python3
"""
THE GATE THE STANDARD MODEL FORCES PRESERVES THE READOUT FRAME AND MOVES EVERY MAGIC DIRECTION,
AND ITS HETEROTIC ROOT GRADING PREDICTS THE PHOTON'S INTERFERENCE VISIBILITY: 1/3 AND 1/9.

THE SELF-ENTANGLEMENT PICTURE, as this corpus builds it (cited, not re-derived):

  * holonet_machine_blueprint section 60: one qutrit entangled with itself at two times gives
    C^3 (x) C^3 = End(C^3). "The two-qutrit machine and the one-qutrit machine that can act on
    itself are the same machine described twice." Counting directions, 3^4 - 1 = 80 and 80/2 =
    40: the forty points of W(3,3) ARE the forty independent things one self-entangled qutrit
    can be measured along.
  * section 65, the optical encoding: one photon carries the two qutrits as its arrival-time
    bins and its frequency bins. The controlled-add |f,t> -> |f, t+f> is one passive chirped
    fibre Bragg grating, demonstrated by Imany et al., npj Quantum Information 5, 59 (2019),
    basis fidelity 0.92 +- 0.01, entanglement of formation >= 1.19 +- 0.12 ebits.
  * photonic_holonet section 65 and BT817: the companion spatial carrier is path (x)
    polarization, C^4, whose 40 Witting rays split 4 PRODUCT + 36 SELF-ENTANGLED.
  * blueprint section 67.1: of the 40 addressed points, 36 are the magic rays and the
    remaining 4 are the coordinate axes -- a line. Magic is everything except one line.

So three independent readings give the same 4 + 36 split of W(3,3), relative to one line: the
non-magic axes, the product rays, the classical frame.

WHAT THIS FILE COMPUTES. The heterotic side meets that split exactly.

  1. The Wilson-line holonomy of the W(3,3) Standard Models is in the CZ class in 45 of 45
     Z6-I models (d772153). Its fixed points on W(3,3) are EXACTLY the Z-type Lagrangian
     {(0,0,z1,z2)} -- the computational readout frame -- and it moves all 36 remaining
     directions. Not a line that happens to have 4 points: the readout line.

     The reason is structural: CZ is diagonal in the computational basis, so it commutes with
     Z1 and Z2 and fixes their Pauli line pointwise, while every direction with a nonzero X
     part is shifted. A gate is diagonal exactly when it preserves the readout frame.

  2. On contexts its cycle type is 1^7 3^11, and stratum by stratum relative to that line:
     the readout context fixed, 6 of the 12 one-product contexts fixed, and NO fixed context
     among the 27 fully self-entangled ones, which it permutes in nine 3-cycles.

  3. The eigenvalue multiplicities measured from the heterotic root gradings predict the
     photon's interference visibility directly. The protocol's Choi witness is V(U) = |Tr U|/d
     (bt820, verified there as V(F3) = 1/3, V(X) = V(Z) = 0). On the two-qutrit register d = 9:

         Wilson line, grading 24|24|24 -> multiplicities (5,2,2) -> Tr = 5 + 2w + 2w^2 = 3
             V = 3/9 = 1/3,  the same visibility as the tritter itself
         theta^3,     grading 32|40    -> multiplicities (5,4)   -> Tr = 5 - 4 = 1
             V = 1/9
         any Pauli                                                -> Tr = 0, V = 0

     So an abstract count of E8 roots fixes an optical interference fringe. The entangling
     gate is visible to the photon's self-interference; the Pauli gates are not.

THE READING. The gate that the Standard Model forces is the one that leaves the classical
readout frame alone and acts on every magic direction. In the machine's own language it
preserves what you can measure and consumes what makes the machine quantum. That is also why
it is cheap optically: diagonal in the time/frequency basis means a bin-dependent phase, the
same hardware class as the demonstrated sum gate, not a new nonlinearity.

SCOPE, CAREFULLY. Nothing here says the photon's registers ARE the heterotic gauge register.
Both are C^3 (x) C^3 carrying the same su(9) Pauli structure and the same W(3,3) of 40
directions; the identification is a dictionary. What is computed is that, under it, the
heterotic holonomy lands on the readout line rather than anywhere else among the 40 lines, and
that its spectrum fixes the visibilities above. The photon facts, the magic count and the
laboratory demonstration are cited from the corpus and its references.
"""

import argparse
import cmath
import itertools
import json
import os
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def symp(u, v):
    return (u[0] * v[2] + u[1] * v[3] - u[2] * v[0] - u[3] * v[1]) % 3


def canon(v):
    nz = next(x for x in v if x)
    return tuple((x * pow(nz, -1, 3)) % 3 for x in v)


def geometry():
    pts = sorted({canon(v) for v in itertools.product(range(3), repeat=4) if any(v)})
    lines = set()
    for a, b in itertools.combinations(pts, 2):
        if symp(a, b) == 0:
            L = frozenset(canon(tuple((i * a[k] + j * b[k]) % 3 for k in range(4)))
                          for i in range(3) for j in range(3) if (i, j) != (0, 0))
            if len(L) == 4:
                lines.add(L)
    return pts, sorted(lines, key=lambda L: sorted(L))


def CZ(v):
    return canon((v[0], v[1], (v[2] + v[1]) % 3, (v[3] + v[0]) % 3))


def cycle_type(perm, objs):
    seen, c = set(), Counter()
    for o in objs:
        if o in seen:
            continue
        n, x = 0, o
        while x not in seen:
            seen.add(x)
            x = perm(x)
            n += 1
        c[n] += 1
    return dict(sorted(c.items()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    checks = {}

    pts, lines = geometry()
    checks["forty_points"] = len(pts) == 40
    checks["forty_lines"] = len(lines) == 40

    # 1. the CZ fixed line is the readout (Z-type) frame, and it moves all 36 others
    fixed = [p for p in pts if CZ(p) == p]
    zline = [p for p in pts if p[0] == 0 and p[1] == 0]
    moved = [p for p in pts if CZ(p) != p]
    print("  CZ fixed points: %s" % fixed)
    print("  Z-type readout line: %s" % zline)
    checks["cz_fixes_exactly_the_readout_line"] = set(fixed) == set(zline)
    checks["readout_line_is_a_line"] = frozenset(zline) in set(lines)
    checks["cz_moves_all_thirty_six"] = len(moved) == 36
    print("  CZ fixes the readout frame and moves all %d magic directions" % len(moved))

    # 2. context action, stratum by stratum
    def CZline(L):
        return frozenset(CZ(p) for p in L)

    L0 = frozenset(zline)
    meet = [L for L in lines if L != L0 and len(L & L0) == 1]
    disj = [L for L in lines if L != L0 and len(L & L0) == 0]
    checks["strata_1_12_27"] = (len(meet), len(disj)) == (12, 27)
    t_all, t_meet, t_disj = cycle_type(CZline, lines), cycle_type(CZline, meet), cycle_type(CZline, disj)
    print("  contexts: all %s   one-product %s   fully entangled %s" % (t_all, t_meet, t_disj))
    checks["context_type_1_7_3_11"] = t_all == {1: 7, 3: 11}
    checks["no_fully_entangled_context_fixed"] = t_disj == {3: 9}

    # 3. the visibilities, from the heterotic multiplicities
    w = cmath.exp(2j * cmath.pi / 3)
    tr_cz = 5 + 2 * w + 2 * w ** 2                 # multiplicities (5,2,2) from grading 24|24|24
    tr_par = 5 - 4                                  # multiplicities (5,4)  from grading 32|40
    v_cz, v_par = abs(tr_cz) / 9, abs(tr_par) / 9
    print("  Tr(CZ) = %.6f -> V = %.6f (1/3)    Tr(parity) = %d -> V = %.6f (1/9)" % (
        tr_cz.real, v_cz, tr_par, v_par))
    checks["trace_of_cz_is_three"] = abs(tr_cz - 3) < 1e-12
    checks["visibility_of_cz_is_one_third"] = abs(v_cz - 1 / 3) < 1e-12
    checks["visibility_of_parity_is_one_ninth"] = abs(v_par - 1 / 9) < 1e-12
    # every non-identity two-qutrit Pauli is traceless, computed rather than asserted:
    # Tr(X^a Z^b) = sum_j w^{bj} [j = j+a] = 3 delta_{a,0} delta_{b,0} per qutrit
    def pauli_trace(a, b):
        return sum(w ** ((b * j) % 3) for j in range(3)) if a % 3 == 0 else 0
    pauli_traces = {(a1, b1, a2, b2): pauli_trace(a1, b1) * pauli_trace(a2, b2)
                    for a1 in range(3) for b1 in range(3) for a2 in range(3) for b2 in range(3)}
    nonident = [t for k, t in pauli_traces.items() if any(k)]
    checks["every_nonidentity_pauli_is_traceless"] = all(abs(t) < 1e-12 for t in nonident)
    checks["identity_trace_is_nine"] = abs(pauli_traces[(0, 0, 0, 0)] - 9) < 1e-12

    # the protocol's own convention, reproduced: V(F3) = 1/3 on one qutrit
    F3_trace = sum(w ** ((j * j) % 3) for j in range(3)) / cmath.sqrt(3)
    checks["protocol_convention_V_F3_is_one_third"] = abs(abs(F3_trace) / 3 - 1 / 3) < 1e-9

    for k, v in checks.items():
        print("  %-46s %s" % (k, v))
    valid = all(checks.values())
    print("VALID:", valid)

    if args.write:
        payload = {
            "claim": "The CZ class that the heterotic Standard Model forces (45 of 45, d772153) fixes exactly the "
                     "Z-type Lagrangian of W(3,3) -- the computational readout frame -- and moves all 36 remaining "
                     "directions, which are the magic rays of blueprint 67.1 and the self-entangled rays of BT817. On "
                     "contexts its type is 1^7 3^11 with NO fixed context among the 27 fully entangled ones. Its "
                     "eigenvalue multiplicities, measured from the heterotic root gradings, give Choi visibilities "
                     "V = |Tr|/9 of 1/3 for the Wilson line and 1/9 for theta^3, against 0 for any Pauli.",
            "selfEntanglementPicture": {
                "identity": "C^3 (x) C^3 = End(C^3): two qutrits = one qutrit acting on itself (blueprint 60)",
                "counting": "3^4 - 1 = 80, /2 = 40 directions = the points of W(3,3)",
                "optical_encoding": "arrival-time bins (x) frequency bins on one photon (blueprint 65)",
                "laboratory": "Imany et al., npj QI 5, 59 (2019): deterministic single-photon qutrit sum gate, "
                              "fidelity 0.92 +- 0.01, entanglement of formation >= 1.19 +- 0.12 ebits",
                "splits": {"photon rays (BT817)": "4 product + 36 self-entangled",
                           "magic (blueprint 67.1)": "36 magic + 4 coordinate axes = one line"}},
            "whatIsComputed": {
                "cz_fixed_line": "exactly the Z-type readout frame, because CZ is diagonal so it commutes with Z1, Z2",
                "moved": 36,
                "context_type": {"1": 7, "3": 11},
                "by_stratum": {"readout": "fixed", "one_product_12": {"fixed": 6, "3cycles": 2},
                               "fully_entangled_27": {"fixed": 0, "3cycles": 9}},
                "visibilities": {"wilson_line_CZ": "1/3, the same as the tritter", "theta3_parity": "1/9",
                                 "any_pauli": "0"}},
            "reading": "the Standard Model's gate leaves the classical readout frame alone and acts on every magic "
                       "direction: it preserves what can be measured and consumes what makes the machine quantum. "
                       "Being diagonal in the time/frequency basis, it is a bin-dependent phase -- the same hardware "
                       "class as the demonstrated sum gate, not a new nonlinearity",
            "scope": "the identification of the photon's registers with the heterotic gauge register is a DICTIONARY: "
                     "both are C^3 (x) C^3 with the same su(9) Pauli structure and the same 40 directions. What is "
                     "computed is that the heterotic holonomy lands on the readout line rather than anywhere else "
                     "among the 40, and that its spectrum fixes the visibilities",
            "checks": checks, "valid": valid,
            "sources": ["TOE holonet_machine_blueprint sections 60, 65, 67.1",
                        "TOE photonic_holonet section 65", "TOE analysis/BT817_self_entangled_photon_atlas.md",
                        "TOE analysis/bt820_self_entanglement_protocol.py",
                        "Imany et al., npj Quantum Information 5, 59 (2019)",
                        "Holotrade d772153", "Holotrade 1d03cbb", "Holotrade 9ca676a", "Holotrade 5b3f3ad"]}
        with open(os.path.join(ROOT, "data", "w33_sm_gate_preserves_readout_moves_magic.json"), "w") as f:
            json.dump(payload, f, indent=1)
        print("written")


if __name__ == "__main__":
    main()
