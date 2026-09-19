#!/usr/bin/env python3
"""
THE ENTANGLING GATE FIXES THE PHOTON'S PRODUCT CONTEXT AND STIRS ITS FULLY SELF-ENTANGLED
SECTOR WITHOUT A SINGLE FIXED POINT.

TWO CARRIERS, ONE GEOMETRY. W(3,3) is realised twice in this corpus, on different Hilbert
spaces:

  * BT817, the self-entangled photon atlas (cited, not re-derived): ONE photon, self-entangled across its own degrees
    of freedom, path (x) polarization = C^2 (x) C^2 = C^4. Its 40 Witting rays have
    orthogonality graph SRG(40,12,2,4) = W(3,3), the 40 orthonormal tetrads are the lines, and
    the rays stratify as 4 PRODUCT + 36 SELF-ENTANGLED, with contexts splitting 1 + 12 + 27.

  * The heterotic gauge register: TWO QUTRITS, C^3 (x) C^3 = C^9, whose Pauli algebra is
    su(9) = A8 = the W(3,3) twist of E8 (68df33f, Holotrade 1cde1f1). This is where the
    Standard Models of 5b3f3ad live, inside a local SU(9).

The two share the geometry W(3,3) and its group PSp(4,3). They do NOT share a state space, and
nothing here says the photon is the gauge register.

WHAT IS PROVED HERE.

  1. The photon's 1 + 12 + 27 context stratification is not extra structure: it is exactly the
     decomposition of the generalised quadrangle GQ(3,3) relative to ONE LINE. Every point lies
     on 4 lines, so a chosen line L0 has 12 lines meeting it in a point and 27 disjoint from it,
     and 1 + 12 + 27 = 40. Verified below. This makes BT817's remark precise -- "choosing how to
     split the photon into two qubits IS choosing a parabolic vacuum" -- as: choosing the split
     is choosing a line, the all-product context; the 12 one-product contexts are the lines
     meeting it, and the 27 fully entangled contexts are the lines disjoint from it.

  2. The gate the Standard Model forces is of exactly the type that stabilises such a line. The
     Wilson-line holonomy of the W(3,3) Standard Models is in the CZ class in 45 of 45 Z6-I
     models (d772153). CZ acts on the 40 points with cycle type 1^4 3^12, and its FOUR FIXED
     POINTS FORM A LINE. So in the photon dictionary it fixes an all-product context pointwise.

  3. Its action on the three strata, relative to that line:

         the all-product context (1)          fixed
         one-product contexts   (12)          6 fixed, 6 in two 3-cycles
         fully entangled        (27)          NO fixed context, nine 3-cycles

     The entangling gate is trivial on the unentangled rays, partial on the partially entangled
     contexts, and acts FREELY on the fully self-entangled sector. Its total line cycle type is
     1^7 3^11, which is where the seven fixed contexts come from: one product, six one-product,
     none fully entangled.

WHAT THIS DOES NOT CLAIM. Sp(4,3) is transitive on the 40 lines, with line stabiliser of order
51840/40 = 1296, so "the CZ-fixed line can be identified with the product context" is a
compatibility statement, not a derivation. The content is that BOTH distinguished four-sets are
lines -- neither is forced to be -- and that once identified, the stratum-by-stratum action is
the exact one above, which is not a matter of choice.

HOW IT READS FOR EVERYTHING ELSE. The same geometric datum, a distinguished line of W(3,3), is
read on the photonic side as "which of my rays are unentangled" and on the gauge side as "what
my entangling holonomy leaves alone". Self-entanglement of a single photon and the entangling
Wilson line of the heterotic model are two readings of one line. That is also why the parity
element is invisible here: it is -I, which acts trivially on all 40 points (e2390de), so the
entanglement stratification cannot see it at all -- it only appears on the oriented 80-state
lift.

SCOPE. The Witting/SRG/4+36 facts are BT817's, cited not re-derived; the ray-shape check below
is a consistency check on the stratification, not a reconstruction of the Witting configuration.
The geometry and the CZ action are computed here exactly.
"""

import argparse
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
    checks["w33_has_40_points"] = len(pts) == 40
    checks["w33_has_40_lines"] = len(lines) == 40
    checks["gq33_each_point_on_four_lines"] = all(
        sum(1 for L in lines if p in L) == 4 for p in pts)

    # CZ on points: 1^4 3^12, fixed points form a line
    cp = cycle_type(CZ, pts)
    fixed = frozenset(p for p in pts if CZ(p) == p)
    print("  CZ on the 40 points: %s" % cp)
    checks["cz_point_type_is_1_4_3_12"] = cp == {1: 4, 3: 12}
    checks["cz_fixed_points_form_a_line"] = fixed in set(lines)
    print("  CZ fixed points: %d, and they form a line: %s" % (len(fixed), fixed in set(lines)))

    # the 1 + 12 + 27 stratification relative to that line is pure geometry
    L0 = fixed
    meet = [L for L in lines if L != L0 and len(L & L0) == 1]
    disj = [L for L in lines if L != L0 and len(L & L0) == 0]
    print("  relative to that line: 1 + %d meeting + %d disjoint = %d" % (
        len(meet), len(disj), 1 + len(meet) + len(disj)))
    checks["strata_are_1_12_27"] = (len(meet), len(disj)) == (12, 27)
    checks["strata_exhaust_the_lines"] = 1 + len(meet) + len(disj) == 40

    # CZ on lines, and stratum by stratum
    def CZline(L):
        return frozenset(CZ(p) for p in L)

    cl = cycle_type(CZline, lines)
    print("  CZ on the 40 contexts: %s" % cl)
    checks["cz_line_type_is_1_7_3_11"] = cl == {1: 7, 3: 11}
    checks["cz_preserves_each_stratum"] = all(CZline(L) in meet for L in meet) and \
        all(CZline(L) in disj for L in disj) and CZline(L0) == L0
    t_meet = cycle_type(CZline, meet)
    t_disj = cycle_type(CZline, disj)
    print("  one-product stratum (12): %s      fully entangled stratum (27): %s" % (t_meet, t_disj))
    checks["six_of_the_twelve_are_fixed"] = t_meet == {1: 6, 3: 2}
    checks["no_fully_entangled_context_is_fixed"] = t_disj == {3: 9}
    checks["seven_fixed_lines_split_1_plus_6"] = 1 + t_meet.get(1, 0) == cl.get(1, 0) == 7

    # transitivity caveat, as arithmetic
    checks["line_stabiliser_order_1296"] = 51840 // 40 == 1296

    # The photon-side facts (40 Witting rays, SRG(40,12,2,4), 4 product + 36 self-entangled,
    # contexts 1+12+27) are BT817's certified results and are CITED, not re-derived here. This
    # file adds only what it computes: that 1+12+27 is the line decomposition of GQ(3,3), and
    # the CZ action on it. No vacuous restatement of BT817's counts is recorded as a check.

    for k, v in checks.items():
        print("  %-46s %s" % (k, v))
    valid = all(checks.values())
    print("VALID:", valid)

    if args.write:
        payload = {
            "claim": "The photon's 1+12+27 context stratification (BT817) is exactly the GQ(3,3) decomposition relative "
                     "to one line: the all-product context is a line L0, the 12 one-product contexts are the lines "
                     "meeting it, the 27 fully entangled contexts are the lines disjoint from it. The CZ class that the "
                     "heterotic Standard Model forces (d772153) has cycle type 1^4 3^12 on points with its four fixed "
                     "points forming a line, so it fixes such a product context pointwise; on contexts its type is "
                     "1^7 3^11, distributed as the product context fixed, 6 of the 12 one-product contexts fixed, and "
                     "NO fixed context among the 27 fully self-entangled ones, which it permutes in nine 3-cycles.",
            "twoCarriers": {
                "photon": "one photon self-entangled across path (x) polarization, C^4, 40 Witting rays, "
                          "4 product + 36 self-entangled (BT817)",
                "gauge_register": "two qutrits, C^9, Pauli algebra su(9) = A8 = the W(3,3) twist, where the Standard "
                                  "Models of 5b3f3ad live",
                "shared": "the geometry W(3,3) and its group PSp(4,3) -- NOT a state space"},
            "stratification_is_geometry": {"line": 1, "meeting": 12, "disjoint": 27,
                                           "reason": "in GQ(3,3) every point lies on 4 lines"},
            "cz_action": {"points": {"1": 4, "3": 12}, "fixed_points_form_a_line": True,
                          "lines": {"1": 7, "3": 11},
                          "by_stratum": {"all_product": "fixed", "one_product_12": {"fixed": 6, "3cycles": 2},
                                         "fully_entangled_27": {"fixed": 0, "3cycles": 9}}},
            "caveat": "Sp(4,3) is transitive on the 40 lines with stabiliser 1296, so identifying the CZ-fixed line "
                      "with the product context is a compatibility statement; the content is that both distinguished "
                      "four-sets ARE lines, and that the stratum-by-stratum action is then forced",
            "parity_note": "the parity element is -I, which acts trivially on all 40 points, so the entanglement "
                           "stratification cannot see it; it only appears on the oriented 80-state lift (e2390de)",
            "checks": checks, "valid": valid,
            "status": "geometry and CZ action computed exactly here; the Witting/SRG/4+36 facts are BT817's, cited",
            "sources": ["TOE analysis/BT817_self_entangled_photon_atlas.md", "Holotrade d772153", "Holotrade 1cde1f1",
                        "Holotrade 5b3f3ad", "Holotrade e2390de", "Holotrade 68df33f"]}
        with open(os.path.join(ROOT, "data", "w33_entangling_gate_fixes_product_context.json"), "w") as f:
            json.dump(payload, f, indent=1)
        print("written")


if __name__ == "__main__":
    main()
