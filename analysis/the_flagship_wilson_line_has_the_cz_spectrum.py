#!/usr/bin/env python3
"""
THE FLAGSHIP'S WILSON LINE HAS THE CZ SPECTRUM, AND THE STANDARD MODEL'S SU(5) IS ITS
TRIVIAL-PHASE BLOCK.

TOE 422271f78 / 030a44590 read the Wilson line of the recorded W(3,3) Standard Model
SM_20260917_3 (Holotrade 5b3f3ad) on the gauge side and found that it grades the local
A8 = su(9) roots as 24 + 24 + 24, with neutral subalgebra A4 + A1 + A1, so that the SU(9)
holonomy has defining multiplicities 5 + 2 + 2 and is projectively SU(9)-conjugate to the
two-qutrit controlled-Z gate. That was derived on their side from the grading. This file
verifies it from the model's own data, and adds the piece that makes it physical.

VERIFIED HERE, from the flagship's shift and Wilson line directly:

  * the theta^2 local gauge group is su(9): exactly 72 roots survive 2V;
  * the order-three Wilson line grades those 72 roots as exactly 24 | 24 | 24;
  * the counts alone do NOT force the multiplicities: both (5,2,2) and (1,4,4) give 24 neutral
    roots and 24 in each cross-grade. What settles it is the TYPE of the neutral block, computed
    here by decomposing those 24 roots: they form A4 + A1 + A1 (20 + 2 + 2), so the blocks have
    sizes 5, 2, 2. The alternative (1,4,4) would have given A3 + A3;
  * CZ_3 on nine states has eigenvalue omega^{jk}, with multiplicities exactly 5, 2, 2 -- five
    states with jk = 0, two with jk = 1, two with jk = 2. Same spectrum;
  * ALL FOUR SU(5) simple roots that fix the flagship's hypercharge lie in the NEUTRAL block.

THE STATEMENT. The Wilson line that breaks the W(3,3) twist's SU(9) down to the Standard Model
has the spectrum of a two-qutrit controlled-Z gate, and the Standard Model's SU(5) -- the one
carrying GUT-normalised hypercharge, verified in 5b3f3ad -- is precisely that gate's
trivial-phase eigenspace. The 5 of the 5 + 2 + 2 is the SU(5).

This closes the loop opened by 1cde1f1: a qutrit register cannot live in E6, it lives in
sl(9) = su(9) = A8, which is the W(3,3) twist itself; and now the one Wilson line that actually
produces a Standard Model in that setting turns out to be the entangling gate of that register.

PRECISION ABOUT "IS THE CZ GATE". What is established is the SPECTRUM: multiplicities (5,2,2)
of the three cube roots of unity, hence conjugacy to CZ_3 inside SU(9) modulo its centre. Whether
the conjugating map respects the canonical two-qutrit tensor factorisation -- that is, whether
the holonomy is literally a Clifford element for the Pauli grading of sl(9) rather than merely
cospectral with one -- is a finer question and is NOT settled here. The honest claim is
cospectrality plus the SU(5) block identification.

SCOPE. Exact root-system arithmetic on the recorded model, self-contained. The grading reading
is the other track's (422271f78); this is an independent confirmation from the model data plus
the SU(5)-in-the-neutral-block fact.
"""

import argparse
import itertools
import json
import os
from collections import Counter
from fractions import Fraction as Fr

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# the flagship of 5b3f3ad: Z6-I, Z3 part (D7+U1, A8); the SU(9) side is the second E8
FLAGSHIP = {
    "V": "0,0,0,0,1/6,1/6,1/3,2/3 | 0,0,0,1/6,1/6,1/6,1/6,2/3",
    "W3": "-7/6,-5/6,-1/6,1/6,1/2,1/2,7/6,-1/6 | -4/3,-2/3,1/3,-4/3,0,1/3,1,1/3",
    "su5_simple_roots": ["0,1,-1,0,0,0,0,0", "1,0,1,0,0,0,0,0", "0,0,0,0,1,0,-1,0",
                         "-1/2,-1/2,-1/2,1/2,-1/2,1/2,1/2,1/2"],
    "label": "SM_20260917_3",
}


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    checks = {}

    V, W3 = vec(FLAGSHIP["V"]), vec(FLAGSHIP["W3"])
    su5 = [vec(r) for r in FLAGSHIP["su5_simple_roots"]]
    hi = slice(8, 16)                       # the SU(9) side

    L = [2 * a for a in V[hi]]              # theta^2 local shift at the A8 fixed point
    local = [r for r in ROOTS if dot(r, L).denominator == 1]
    checks["local_group_is_su9"] = len(local) == 72
    print("  theta^2 local group: %d roots = su(9)" % len(local))

    grade = Counter(dot(r, W3[hi]) % 1 for r in local)
    print("  Wilson-line grading: %s" % {str(k): v for k, v in sorted(grade.items())})
    checks["grading_is_24_24_24"] = sorted(grade.values()) == [24, 24, 24] and len(grade) == 3

    neutral = [r for r in local if dot(r, W3[hi]) % 1 == 0]
    checks["neutral_block_has_24_roots"] = len(neutral) == 24

    # the counts alone are ambiguous: (5,2,2) and (1,4,4) both fit
    by_counts = [m for m in itertools.combinations_with_replacement(range(0, 10), 3)
                 if sum(m) == 9 and sum(x * (x - 1) for x in m) == 24
                 and m[0] * m[1] + m[1] * m[2] + m[2] * m[0] == 24]
    print("  multiplicities consistent with the counts alone: %s (ambiguous)" % by_counts)
    checks["counts_alone_are_ambiguous"] = sorted(by_counts) == [(1, 4, 4), (2, 2, 5)]

    # decompose the neutral block into simple factors: that is what settles it
    comps = []
    seen = set()
    for i in range(len(neutral)):
        if i in seen:
            continue
        stack, C = [i], []
        seen.add(i)
        while stack:
            u = stack.pop()
            C.append(neutral[u])
            for j in range(len(neutral)):
                if j not in seen and dot(neutral[u], neutral[j]) != 0:
                    seen.add(j)
                    stack.append(j)
        comps.append(C)
    shape = sorted(len(C) for C in comps)
    print("  neutral block decomposes into components of sizes %s" % shape)
    # a block of size m contributes m(m-1) roots: 20 -> A4 (m=5), 2 -> A1 (m=2)
    blocks = sorted(next(m for m in range(1, 10) if m * (m - 1) == len(C)) for C in comps)
    print("  so the holonomy blocks have sizes %s" % blocks)
    checks["neutral_block_is_A4_plus_A1_plus_A1"] = shape == [2, 2, 20]
    checks["multiplicities_are_5_2_2"] = blocks == [2, 2, 5]

    # CZ_3's own spectrum on nine states
    cz = Counter((j * k) % 3 for j in range(3) for k in range(3))
    print("  CZ_3 eigenvalue multiplicities: %s" % dict(sorted(cz.items())))
    checks["cz_has_the_same_spectrum"] = sorted(cz.values()) == [2, 2, 5]

    inside = [dot(r, W3[hi]) % 1 == 0 for r in su5]
    print("  SU(5) simple roots in the neutral (trivial-phase) block: %s" % inside)
    checks["su5_is_the_trivial_phase_block"] = all(inside)
    checks["su5_roots_are_e8_roots"] = all(dot(r, r) == 2 for r in su5)

    for k, v in checks.items():
        print("  %-44s %s" % (k, v))
    valid = all(checks.values())
    print("VALID:", valid)

    if args.write:
        payload = {
            "claim": "In the recorded W(3,3) Standard Model SM_20260917_3, the theta^2 local gauge group is su(9) and "
                     "the single order-three Wilson line grades its 72 roots exactly 24|24|24. Those counts alone are "
                     "ambiguous - (1,4,4) fits them too - but the neutral block decomposes as A4 + A1 + A1, which "
                     "forces holonomy multiplicities (5,2,2) in the defining 9, exactly the eigenvalue spectrum of the "
                     "two-qutrit controlled-Z gate. All four SU(5) simple roots carrying the model's GUT-normalised "
                     "hypercharge lie in the neutral block, so the Standard Model's SU(5) is that gate's trivial-phase "
                     "eigenspace.",
            "model": FLAGSHIP["label"],
            "grading": {"local_roots": 72, "grades": [24, 24, 24], "neutral": 24,
                        "multiplicities_from_counts_alone": [[1, 4, 4], [2, 2, 5]],
                        "neutral_algebra_computed_here": "A4 + A1 + A1 (20 + 2 + 2)",
                        "forced_multiplicities": [2, 2, 5]},
            "czSpectrum": {"multiplicities": {"0": 5, "1": 2, "2": 2},
                           "reading": "CZ_3 acts as omega^{jk} on the nine states"},
            "su5": "all four simple roots lie in the trivial-phase block",
            "precision": "what is established is cospectrality, hence conjugacy to CZ_3 in SU(9) modulo its centre; "
                         "whether the conjugation respects the canonical two-qutrit tensor factorisation, i.e. whether "
                         "the holonomy is literally Clifford for the Pauli grading of sl(9), is NOT settled here",
            "closesTheLoop": "1cde1f1 showed a qutrit register cannot live in E6 but does live in sl(9) = su(9) = A8, "
                             "the W(3,3) twist; the Wilson line that actually yields a Standard Model there is the "
                             "entangling gate of that register",
            "checks": checks, "valid": valid,
            "status": "exact root-system arithmetic on the recorded model; independent confirmation of the reading in "
                      "TOE 422271f78 / 030a44590, plus the SU(5)-in-the-neutral-block fact",
            "sources": ["TOE 422271f78", "TOE 030a44590", "Holotrade 5b3f3ad", "Holotrade 1cde1f1",
                        "Holotrade 93b34e1", "Holotrade 68df33f"]}
        with open(os.path.join(ROOT, "data", "w33_flagship_wilson_line_cz_spectrum.json"), "w") as f:
            json.dump(payload, f, indent=1)
        print("written")


if __name__ == "__main__":
    main()
