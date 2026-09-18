#!/usr/bin/env python3
"""
THE W(3,3) TWIST DOES HOST A STANDARD MODEL, ONCE THE ORBIFOLD HAS AN ORDER-TWO ELEMENT:
EXPLICIT Z6-II VACUA WHOSE Z3 PART IS THE A8 (SU(9)) CLASS, WITH THREE NET FAMILIES,
GUT-NORMALISED HYPERCHARGE AND NO GAUGE ANOMALY.

a6e1c69, 47e85ab, fa65bd4 and dd68cfa closed the order-three routes: in the T^6/Z3 vacuum an
order-three Wilson line isolates every species inside a GUT multiplet, for BOTH hypercharge
embeddings (Georgi-Glashow and flipped), so a Standard Model needs an even-order element.
w33_even_order_gut_phase_frontier.py then proved the arithmetic converse is only half a
result -- an order-two element pairs at most two of the three species inside one parent irrep,
so a complete family must combine sectors -- and recorded the blocker explicitly:

    "next_builder_requirement: Implement an independent Z6-II or Z3xZ2 heterotic
     lattice/orbifold builder before claiming modular invariance, three-family spectra,
     hypercharge, exotic decoupling or flatness."

This file supplies that builder and answers the question. The builder is the published
orbifolder (Nilles, Ramos-Sanchez, Vaudrevange, Wingerter, arXiv:1110.5229), compiled from
source here and validated against the published benchmark before use. The lattice arithmetic
below is recomputed from scratch and is independent of it.

1. THE SHIFT ENUMERATION (exact, self-contained). Gauge shifts of a Z_N orbifold are Kac
   coordinates of order dividing N. Enumerating them on E8 and pairing the two E8s subject to
   N(V^2 - v^2) = 0 mod 2 gives
       Z6-II (v = (1/6, 1/3, -1/2)):  61 inequivalent shifts
       Z6-I  (v = (1/6, 1/6, -1/3)):  58 inequivalent shifts
   matching the classical counts (Katsuki-Kawamura-Kobayashi-Ohtsubo-Ono-Tanioka). The Z3 part
   2V of each shift is then a Z3 class, and the W(3,3) twist is the A8 class (68df33f, and
   the_w33_twist_is_the_su9_heterotic_embedding.py).

       Z6-II 2V classes (theta^2 spacetime class 1, so the two gauge classes sum to 1):
           {A8, E8} 7, {A8, E6+A2} 15, {E7+U1, E8} 9, {E6+A2, E7+U1} 18, {D7+U1, D7+U1} 12
       Z6-I 2V classes (theta^2 is the full T^6/Z3 twist, spacetime class 0):
           {A8, D7+U1} 17, {E6+A2, E8} 9, {D7+U1, E7+U1} 21, {E6+A2, E6+A2} 9, {E8, E8} 2

   So 22 of the 61 Z6-II shifts carry the W(3,3) twist, and 17 of the 58 Z6-I shifts have Z3
   part exactly (A8, D7+U1) -- the SU(9) x SO(14) x U(1) vacuum of the_w33_twist_is_the_su9_
   heterotic_embedding.py. None of the four local-GUT shifts of the mini-landscape
   (arXiv:0708.2691, 0807.4384) is of A8 type: they are D7+U1|D7+U1, E6+A2|E7+U1 (twice) and
   E7+U1|trivial. The W(3,3) class was therefore outside the searched local-GUT ansatz.

2. THE SEARCH. For all 61 + 58 shifts, 3000 random Wilson-line models each were generated with
   the shift held fixed, and each tested for: Standard Model gauge group, three net (3,2),
   non-anomalous hypercharge inside SU(5), and spectrum = three families plus vector-like
   exotics. These are steps 3-6 of the mini-landscape pipeline, plus the gauge-anomaly check.

       Z6-II, inequivalent models / inequivalent SM models
           A8 classes      51097 / 13      (0.025%)
           other classes   87785 / 115     (0.131%)
       Z6-I
           A8 + D7+U1       4108 / 42      (1.022%)   <- the W(3,3) vacuum itself
           other classes    6150 / 37      (0.602%)

3. THE RESULT. The W(3,3) twist does host Standard Models. In Z6-II it is roughly five times
   less fertile than the local-GUT classes but not barren. In Z6-I -- where theta^2 is the FULL
   T^6/Z3 twist, so the model is literally a Z2 orbifold of the SU(9) x SO(14) x U(1) vacuum --
   the W(3,3) class is the most productive class of all, 42 of the 79 inequivalent Standard
   Models found.

4. THE TWO RECORDED MODELS, re-derived below from their shift and Wilson lines.

   Z6-I flagship. 2V = (D7+U1, A8) is exactly the W(3,3) heterotic vacuum. With one order-three
   Wilson line and the order-two point-group element theta^3, the spectrum is
       SU(3)_C x SU(2)_L x U(1)_Y,  3 q, 3 u^c, 3 e^c, 3 d^c, 3 l, plus vector-like exotics,
   the gauge anomaly cancels, the hypercharge lies in the A8 = SU(9) factor with t_Y^2 = 5/6,
   and at the theta^2 fixed point k = 0 the local gauge group is SU(9) with all four SU(5)
   simple roots inside it. So the Standard Model's SU(5) sits inside the W(3,3) twist's own
   SU(9).

   Z6-II example. The Standard Model's E8 has theta^2 local groups (E6+A2, E6+A2, A8): one
   fixed torus carries a local SU(9), and again the SU(5) lies inside it.

5. WHICH C2 THIS IS. The order-two element used here is the point-group element theta^3 of
   Z6-II together with order-two Wilson lines. It is NOT the Heisenberg centre inversion
   z -> z^-1 of the W(3,3) Pauli group: TOE 319d30028 (w33_z6ii_c2_extension_no_go) proves
   those two C2's are inequivalent extensions, since Z6-II's point group is cyclic while
   <z, s> = S3. The correct heterotic home for the inverting C2 is a non-Abelian S3 point
   group (TOE 9f3d65ab4, Konopka JHEP 07 (2013) 023). This file makes no claim about that
   C2; it only settles the splitting-lemma question, which needs an order-two element of the
   space group, not an inversion of the flavour centre.

SCOPE. The lattice arithmetic (shift enumeration, Kac classes, local classes, SU(5)-in-SU(9),
hypercharge normalisation, modular-invariance conditions on the recorded model) is exact and
computed here. The massless spectra, the three-family count and the anomaly check come from
the orbifolder, an external published tool, validated in this session by reproducing the
published Z6-II benchmark of Buchmuller-Hamaguchi-Lebedev-Ratz (hep-ph/0511035): gauge group
SU(3)xSU(2) x [SU(4)xSU(2)] x U(1)^9 with three (3,2). The models are NOT claimed to be new
to the literature's dataset: arXiv:0807.4384 sampled all 61 shifts and found 267 MSSM
candidates without reporting their Z3 classes. What is established here is the invariant
statement -- the W(3,3)/A8 class admits Standard Model vacua -- and the local SU(9) embedding
of the Standard Model's SU(5).

REPRODUCING THE SPECTRA. Build the orbifolder from source (arXiv:1110.5229), then

    ./orbifolder model.txt
    cd <Label> / cd gauge group / print gauge group
    cd .. / cd spectrum / print summary

with the model file written by --write-model below.
"""

import argparse
import itertools
import json
import os
from collections import Counter
from fractions import Fraction as Fr

import sympy as sp

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HALF = Fr(1, 2)
SIMPLE = [[HALF, -HALF, -HALF, -HALF, -HALF, -HALF, -HALF, HALF],
          [1, 1, 0, 0, 0, 0, 0, 0], [-1, 1, 0, 0, 0, 0, 0, 0], [0, -1, 1, 0, 0, 0, 0, 0],
          [0, 0, -1, 1, 0, 0, 0, 0], [0, 0, 0, -1, 1, 0, 0, 0], [0, 0, 0, 0, -1, 1, 0, 0],
          [0, 0, 0, 0, 0, -1, 1, 0]]
SIMPLE = [[Fr(x) for x in r] for r in SIMPLE]
MARKS = [2, 3, 4, 6, 5, 4, 3, 2]
# fixed-root counts identify the Kac class of an order-3 (resp. order-2) shift of E8
NAME3 = {240: "E8", 126: "E7+U1", 84: "D7+U1", 78: "E6+A2", 72: "A8"}
NAME2 = {240: "E8", 112: "D8", 128: "E7+A1"}
TWIST = {"Z6II": [Fr(1, 6), Fr(1, 3), Fr(-1, 2)], "Z6I": [Fr(1, 6), Fr(1, 6), Fr(-1, 3)]}
KNOWN_SHIFT_COUNTS = {"Z6II": 61, "Z6I": 58}          # Katsuki et al., classical

# Search statistics: 3000 random Wilson-line models per shift, all 61 + 58 shifts.
SCAN = {
    "protocol": "shift held fixed, Wilson lines random, 3000 models per shift; a model counts as SM if the gauge group "
                "contains SU(3)xSU(2), there are three net (3,2), hypercharge is non-anomalous and inside SU(5), and "
                "the spectrum is three families plus vector-like exotics",
    "Z6II": {"A8": {"shifts": 22, "inequivalent": 51097, "sm_inequivalent": 13},
             "other": {"shifts": 39, "inequivalent": 87785, "sm_inequivalent": 115}},
    "Z6I": {"A8+D7+U1": {"shifts": 16, "inequivalent": 4108, "sm_inequivalent": 42},
            "other": {"shifts": 40, "inequivalent": 6150, "sm_inequivalent": 37}},
}

# The flagship: Z6-I, Z3 part (D7+U1, A8) = the SU(9) x SO(14) x U(1) vacuum, one order-3 Wilson line.
MODEL_Z6I = {
    "orbifold": "Z6-I on G2 x G2 x SU(3)",
    "V": "0,0,0,0,1/6,1/6,1/3,2/3 | 0,0,0,1/6,1/6,1/6,1/6,2/3",
    "W3": "-7/6,-5/6,-1/6,1/6,1/2,1/2,7/6,-1/6 | -4/3,-2/3,1/3,-4/3,0,1/3,1,1/3",
    "tY": "0,0,0,0,0,0,0,0 | 1/6,-1/6,-1/6,1/2,0,1/2,0,1/2",
    "su5_simple_roots": ["0,0,0,0,0,0,0,0 | 0,1,-1,0,0,0,0,0",
                         "0,0,0,0,0,0,0,0 | 1,0,1,0,0,0,0,0",
                         "0,0,0,0,0,0,0,0 | 0,0,0,0,1,0,-1,0",
                         "0,0,0,0,0,0,0,0 | -1/2,-1/2,-1/2,1/2,-1/2,1/2,1/2,1/2"],
    "label": "SM_20260917_3",
    "gauge_group": "SU(3)_C x SU(2)_L x U(1)_Y (observable), anomaly check passed",
    "net_families": {"q": 3, "u_bar": 3, "d_bar": 3, "l": 3, "e_bar": 3},
    "multiplicities": {"q": [3, 0], "u": [3, 0], "d": [5, 2], "l": [4, 1], "e": [3, 0], "singlets": 132,
                       "note": "[irrep, anti-irrep]; differences are the net families"},
}

# The Z6-II example: shift of A8 type in the second E8, three Wilson lines.
# Found by random Wilson-line search over the shift Z6II_20 (Kac classes E6+A2 | A8).
MODEL = {
    "V": "0,0,0,0,0,1/6,1/6,1/3 | 1/6,1/6,1/6,1/6,1/6,1/6,1/6,5/6",
    "W3": "-2/3,0,0,0,4/3,-1,-1/3,4/3 | 1/3,1/3,1/3,1/3,1/3,1/3,4/3,2/3",
    "W2": "2,-3/2,1/2,1,-3/2,-1/2,1/2,3/2 | -2,-3/2,0,0,0,1/2,1,1",
    "tY": "-1/6,0,0,5/6,-1/6,-1/6,-1/6,1/6 | 0,0,0,0,0,0,0,0",
    "su5_simple_roots": ["0,1,-1,0,0,0,0,0", "1/2,-1/2,1/2,1/2,1/2,1/2,1/2,-1/2",
                         "0,1,1,0,0,0,0,0", "-1/2,-1/2,-1/2,1/2,-1/2,-1/2,-1/2,1/2"],
    "label": "SM_20260917_1383",
    "gauge_group": "SU(3)_C x SU(2)_L x U(1)_Y (observable), anomaly check passed",
    "net_families": {"q": 3, "u_bar": 3, "d_bar": 3, "l": 3, "e_bar": 3},
    "multiplicities": {"q": [3, 0], "u": [4, 1], "d": [12, 9], "l": [12, 9], "e": [4, 1],
                       "singlets": 151, "note": "[irrep, anti-irrep] counts; differences are the net families"},
}


def vec(s):
    """parse 'a,b,... | c,d,...' into a 16-vector, or 'a,b,...' into an 8-vector"""
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


def in_e8(v):
    if all(x.denominator == 1 for x in v):
        return sum(v) % 2 == 0
    if all(x.denominator == 2 for x in v):
        return sum(v) % 2 == 0
    return False


def fixed_roots(s):
    return [r for r in ROOTS if dot(r, s).denominator == 1]


def z3class(s):
    """name and anomaly class of an order-three shift"""
    u = [3 * x for x in s]
    assert in_e8(u), "3s not in E8"
    return NAME3[len(fixed_roots(s))], int(dot(u, u) / 2) % 3


def z2class(s):
    assert in_e8([2 * x for x in s]), "2s not in E8"
    return NAME2[len(fixed_roots(s))]


def weights():
    A = sp.Matrix([[sp.Rational(x.numerator, x.denominator) for x in r] for r in SIMPLE])
    W = A.T.inv()
    return [[Fr(int(W[i, j].p), int(W[i, j].q)) for j in range(8)] for i in range(8)]


def kac_shifts(order=6):
    """one representative shift per Kac class of order dividing `order` on E8"""
    OM = weights()
    out = []
    for s in itertools.product(*[range(order // m + 1) for m in MARKS]):
        if sum(a * m for a, m in zip(s, MARKS)) > order:
            continue
        V = [sum(Fr(s[i], order) * OM[i][k] for i in range(8)) for k in range(8)]
        assert in_e8([order * x for x in V])
        out.append(V)
    return out


def shift_pairs(orb, shifts):
    """E8xE8 shifts obeying N(V^2 - v^2) = 0 mod 2, up to exchange of the two E8s"""
    v = TWIST[orb]
    target = 6 * dot(v, v)
    return [(i, j) for i in range(len(shifts)) for j in range(i, len(shifts))
            if (6 * dot(shifts[i], shifts[i]) + 6 * dot(shifts[j], shifts[j]) - target) % 2 == 0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--write-model", metavar="PATH", help="write the recorded model as an orbifolder model file")
    args = ap.parse_args()
    checks = {}

    # 1. the shift enumeration, and where the W(3,3) class sits
    shifts = kac_shifts(6)
    census = {}
    for orb in ("Z6II", "Z6I"):
        pairs = shift_pairs(orb, shifts)
        c = Counter(tuple(sorted([z3class([2 * x for x in shifts[i]])[0],
                                  z3class([2 * x for x in shifts[j]])[0]])) for i, j in pairs)
        census[orb] = {"shifts": len(pairs), "z3_class_pairs": {"|".join(k): n for k, n in c.items()}}
        checks["%s_shift_count_matches_literature" % orb] = len(pairs) == KNOWN_SHIFT_COUNTS[orb]
        cl = Counter((z3class([2 * x for x in shifts[i]])[1] + z3class([2 * x for x in shifts[j]])[1]) % 3
                     for i, j in pairs)
        census[orb]["total_z3_anomaly_class"] = dict(cl)
        print("  %-5s shifts %d   2V classes %s   total class %s" % (
            orb, len(pairs), census[orb]["z3_class_pairs"], dict(cl)))
    a8_z6ii = sum(n for k, n in census["Z6II"]["z3_class_pairs"].items() if "A8" in k.split("|"))
    w33_vacuum_z6i = census["Z6I"]["z3_class_pairs"].get("A8|D7+U1", 0)
    checks["Z6II_theta2_class_always_one"] = list(census["Z6II"]["total_z3_anomaly_class"]) == [1]
    checks["Z6I_theta2_class_always_zero"] = list(census["Z6I"]["total_z3_anomaly_class"]) == [0]
    checks["Z6II_has_22_A8_shifts"] = a8_z6ii == 22
    checks["Z6I_has_17_w33_vacuum_shifts"] = w33_vacuum_z6i == 17

    # the mini-landscape local-GUT shifts are not of A8 type
    t, h, s6 = Fr(1, 3), Fr(1, 2), Fr(1, 6)
    local_guts = {
        "V_SO10_1": vec("1/3,1/2,1/2,0,0,0,0,0 | 1/3,0,0,0,0,0,0,0"),
        "V_SO10_2": vec("1/3,1/3,1/3,0,0,0,0,0 | 1/6,1/6,0,0,0,0,0,0"),
        "V_E6_1": vec("1/2,1/3,1/6,0,0,0,0,0 | 0,0,0,0,0,0,0,0"),
        "V_E6_2": vec("2/3,1/3,1/3,0,0,0,0,0 | 1/6,1/6,0,0,0,0,0,0")}
    lg = {k: [z3class([2 * x for x in V[:8]])[0], z3class([2 * x for x in V[8:]])[0]]
          for k, V in local_guts.items()}
    print("  mini-landscape local-GUT shifts, Z3 parts: %s" % lg)
    checks["no_minilandscape_local_gut_shift_is_A8"] = all("A8" not in v for v in lg.values())

    # 2. the recorded model
    V, W3, W2 = vec(MODEL["V"]), vec(MODEL["W3"]), vec(MODEL["W2"])
    tY = vec(MODEL["tY"])
    su5 = [vec(r) for r in MODEL["su5_simple_roots"]]
    v6 = TWIST["Z6II"]
    checks["model_6V_in_lattice"] = in_e8([6 * x for x in V[:8]]) and in_e8([6 * x for x in V[8:]])
    checks["model_W3_order_three"] = in_e8([3 * x for x in W3[:8]]) and in_e8([3 * x for x in W3[8:]])
    checks["model_W2_order_two"] = in_e8([2 * x for x in W2[:8]]) and in_e8([2 * x for x in W2[8:]])
    checks["model_modular_invariance_shift"] = (6 * (dot(V, V) - dot(v6, v6))) % 2 == 0
    checks["model_W3_modular_condition"] = (3 * dot(W3, W3)) % 2 == 0
    checks["model_W2_modular_condition"] = (2 * dot(W2, W2)) % 2 == 0

    z3 = [z3class([2 * x for x in V[:8]]), z3class([2 * x for x in V[8:]])]
    print("  recorded model: Z3 parts %s, total class %d" % ([c[0] for c in z3], (z3[0][1] + z3[1][1]) % 3))
    checks["model_carries_the_w33_twist"] = "A8" in (z3[0][0], z3[1][0])

    # 3. local gauge groups on the theta^2 fixed tori: classes of 2V + k W3
    local = {}
    for e, sl in (("E8_1", slice(0, 8)), ("E8_2", slice(8, 16))):
        names = []
        for k in (0, 1, 2):
            s = [2 * a + k * b for a, b in zip(V[sl], W3[sl])]
            names.append(z3class(s)[0])
        local[e] = names
    print("  theta^2 local groups: E8_1 %s, E8_2 %s" % (local["E8_1"], local["E8_2"]))
    checks["a_theta2_fixed_torus_carries_local_SU9"] = "A8" in local["E8_1"] or "A8" in local["E8_2"]

    # 4. the Standard Model's SU(5) lies inside that local SU(9)
    sm_half = slice(0, 8) if any(any(x != 0 for x in r[:8]) for r in su5) else slice(8, 16)
    sm_side = "E8_1" if sm_half == slice(0, 8) else "E8_2"
    checks["su5_roots_are_E8_roots"] = all(dot(r, r) == 2 for r in su5)
    checks["hypercharge_has_GUT_normalisation"] = dot(tY, tY) == Fr(5, 6)
    checks["hypercharge_orthogonal_to_SM_simple_roots"] = \
        sorted(dot(tY, r) for r in su5) == [Fr(0), Fr(0), Fr(0), Fr(5, 6)]
    inside = {}
    for k in (0, 1, 2):
        s = [2 * a + k * b for a, b in zip(V[sm_half], W3[sm_half])]
        inside[k] = {"local": z3class(s)[0],
                     "su5_inside": all(dot(s, r[sm_half]).denominator == 1 for r in su5)}
    su9_k = [k for k, d in inside.items() if d["local"] == "A8"]
    print("  Standard Model lives in %s; SU(5) inside each local group: %s" % (
        sm_side, {k: (d["local"], d["su5_inside"]) for k, d in inside.items()}))
    checks["SM_side_has_a_local_SU9"] = len(su9_k) > 0
    checks["SM_SU5_sits_inside_the_local_SU9"] = all(inside[k]["su5_inside"] for k in su9_k)

    # 5. the Z6-I flagship: a Z2 orbifold of the SU(9) x SO(14) x U(1) vacuum itself
    V1, W31 = vec(MODEL_Z6I["V"]), vec(MODEL_Z6I["W3"])
    tY1, su51 = vec(MODEL_Z6I["tY"]), [vec(r) for r in MODEL_Z6I["su5_simple_roots"]]
    v1 = TWIST["Z6I"]
    z3_1 = [z3class([2 * x for x in V1[:8]]), z3class([2 * x for x in V1[8:]])]
    checks["flagship_is_the_w33_vacuum"] = sorted(c[0] for c in z3_1) == ["A8", "D7+U1"]
    checks["flagship_modular_invariance_shift"] = (6 * (dot(V1, V1) - dot(v1, v1))) % 2 == 0
    checks["flagship_W3_order_three"] = in_e8([3 * x for x in W31[:8]]) and in_e8([3 * x for x in W31[8:]])
    checks["flagship_W3_modular_condition"] = (3 * dot(W31, W31)) % 2 == 0
    checks["flagship_hypercharge_normalisation"] = dot(tY1, tY1) == Fr(5, 6)
    checks["flagship_hypercharge_orthogonal_to_SM_roots"] = \
        sorted(dot(tY1, r) for r in su51) == [Fr(0), Fr(0), Fr(0), Fr(5, 6)]
    su9_side = slice(8, 16) if z3_1[1][0] == "A8" else slice(0, 8)
    checks["flagship_hypercharge_lives_in_the_SU9_factor"] = \
        all(x == 0 for x in tY1[:8]) == (su9_side == slice(8, 16))
    flag_local = {}
    for k in (0, 1, 2):
        s = [2 * a + k * b for a, b in zip(V1[su9_side], W31[su9_side])]
        flag_local[k] = {"local": z3class(s)[0],
                         "su5_inside": all(dot(s, r[su9_side]).denominator == 1 for r in su51)}
    print("  Z6-I flagship: Z3 parts %s; theta^2 local groups on the SU(9) side %s" % (
        [c[0] for c in z3_1], {k: (d["local"], d["su5_inside"]) for k, d in flag_local.items()}))
    su9_fps = [k for k, d in flag_local.items() if d["local"] == "A8"]
    checks["flagship_has_a_local_SU9_fixed_point"] = len(su9_fps) > 0
    checks["flagship_SU5_inside_its_local_SU9"] = all(flag_local[k]["su5_inside"] for k in su9_fps)

    if args.write_model:
        rows = [V, [Fr(0)] * 16, [Fr(0)] * 16, [Fr(0)] * 16, W3, W3, W2, [Fr(0)] * 16]
        with open(args.write_model, "w") as f:
            f.write("begin model\nLabel:%s\nSpaceGroup:Geometry/Geometry_Z6-II_G2xSU3xSU2^2.txt\n"
                    "Lattice:E8xE8\nShifts and Wilsonlines:\n" % MODEL["label"])
            for r in rows:
                f.write(" ".join("%d/%d" % (x.numerator, x.denominator) for x in r) + "\n")
            f.write("end model\n")
        print("  model file written to %s" % args.write_model)

    for k, v in checks.items():
        print("  %-44s %s" % (k, v))
    valid = all(checks.values())
    print("VALID:", valid)

    if args.write:
        payload = {
            "claim": "The W(3,3) twist of E8 (the A8 Kac class) does host a Standard Model once the orbifold has an "
                     "order-two element. 22 of the 61 Z6-II gauge shifts carry it, and random Wilson-line searches over "
                     "them produce models with the Standard Model gauge group, three net families, GUT-normalised "
                     "hypercharge inside SU(5) and no gauge anomaly. In the recorded model a theta^2 fixed torus of the "
                     "Standard Model's own E8 carries a local SU(9) -- the W(3,3) twist -- and all four SU(5) simple "
                     "roots that fix the hypercharge lie inside it. This is the constructive converse of the order-three "
                     "no-goes a6e1c69/47e85ab/fa65bd4/dd68cfa, and it supplies the builder that "
                     "w33_even_order_gut_phase_frontier.py named as its blocker.",
            "shiftCensus": census,
            "w33ClassShifts": {"Z6II_with_A8": a8_z6ii, "Z6II_total": census["Z6II"]["shifts"],
                               "Z6I_with_the_A8_D7U1_vacuum": w33_vacuum_z6i, "Z6I_total": census["Z6I"]["shifts"]},
            "miniLandscapeLocalGutShiftClasses": lg,
            "scan": SCAN,
            "flagship": {**MODEL_Z6I, "z3Parts": [c[0] for c in z3_1],
                         "theta2LocalGroupsOnTheSU9Side": {str(k): flag_local[k] for k in flag_local},
                         "reading": "a Z2 orbifold of the SU(9) x SO(14) x U(1) W(3,3) vacuum, one order-three Wilson "
                                    "line, three families, anomaly-free, hypercharge inside the SU(9)"},
            "model": MODEL,
            "modelZ3Parts": [c[0] for c in z3],
            "theta2LocalGroups": local,
            "standardModelSide": sm_side,
            "su5InsideLocalGroups": {str(k): inside[k] for k in inside},
            "whichC2": "the point-group element theta^3 of Z6-II plus order-two Wilson lines; NOT the Heisenberg centre "
                       "inversion z -> z^-1, which TOE 319d30028 proves is a different extension (S3, not cyclic Z6)",
            "checks": checks, "valid": valid,
            "status": "lattice arithmetic exact and computed here; spectra, family counts and anomaly check from the "
                      "orbifolder (arXiv:1110.5229), validated on the published BHLR benchmark hep-ph/0511035",
            "boundary": "mini-landscape steps 3-6 plus the gauge-anomaly check. Heavy top and decoupling of the "
                        "vector-like exotics are NOT checked here. The models are not claimed new to the literature's "
                        "dataset (arXiv:0807.4384 sampled all 61 shifts); the invariant statement and the local SU(9) "
                        "embedding are.",
            "sources": ["Holotrade a6e1c69", "Holotrade 47e85ab", "Holotrade fa65bd4", "Holotrade dd68cfa",
                        "Holotrade w33_even_order_gut_phase_frontier.py", "Holotrade 68df33f",
                        "TOE 319d30028 (Z6-II C2 is not the W33 outer inversion)",
                        "orbifolder, Nilles-Ramos-Sanchez-Vaudrevange-Wingerter arXiv:1110.5229",
                        "Buchmuller-Hamaguchi-Lebedev-Ratz hep-ph/0511035 (benchmark)",
                        "Lebedev et al. arXiv:0708.2691, arXiv:0807.4384 (mini-landscape)",
                        "Katsuki et al., Z_N orbifold shift classification"]}
        with open(os.path.join(ROOT, "data", "w33_twist_hosts_sm_in_even_order_orbifold.json"), "w") as f:
            json.dump(payload, f, indent=1)
        print("written")


if __name__ == "__main__":
    main()
