#!/usr/bin/env python3
"""
FLIPPED SU(5) IS CLOSED TOO: THE W(3,3) VACUUM EXCLUDES BOTH GUT HYPERCHARGE EMBEDDINGS
AT ORDER THREE, SO A STANDARD MODEL NEEDS AN EVEN-ORDER ELEMENT.

a6e1c69, 47e85ab and fa65bd4 closed the Georgi-Glashow route: an order-three Wilson line
breaking SU(5) to the Standard Model keeps at most one of Q, u^c, e^c per ten, and the
twisted sectors carry no ten. Those proofs assume hypercharge lies inside SU(5). Flipped
SU(5) x U(1)_X evades that assumption. Its family is 10_1 + 5bar_-3 + 1_5 with
Y = (X - Y_GG)/5, so the ten holds (Q, d^c, nu^c) and the anti-five (u^c, L). It breaks by a
vector-like 10_H pair, needs no adjoint Higgs, and is the route string models historically
took. This file closes it at order three, in both of the ways it could arise.

(a) A FLIPPED U(1)_X DIRECTLY IN THE THREE-FAMILY SU(5) MODELS. Flipped SU(5) needs a U(1)_X
    with X(family 10) : X(family 5bar) = 1 : -3. In every three-family SU(5) model of the
    vacuum, the family ten and anti-five carry U(1) charge vectors that are PROPORTIONAL
    with ratio -1/2, so every U(1) gives X(5bar) = -X(10)/2 and no U(1)_X can be flipped. The
    ratio is fixed by how the SU(5) sits in SU(9); the flipped ratio comes from
    SO(10) -> SU(5) x U(1) instead.
    Measured: 40 of 40 three-family SU(5) models, ratio -1/2 in all.

(b) FLIPPED SU(5) FROM WILSON-LINE BREAKING OF SO(10). The three-family SO(10) models
    (35eb923) could break to SU(5) x U(1)_X with an extra line. The splitting lemma carries
    over. Inside one SO(10) irrep P.a = k + c X, with k constant. Breaking removes the roots
    in 10_4 + 10bar_-4 (Delta X = +-4), so 4c is not an integer, and order three gives
    4c = +-1/3 mod 1. The X-gaps inside 16 = 10_1 + 5bar_-3 + 1_5 are 4, 4 and 8, i.e.
    4c, 4c and 8c = +-1/3, +-1/3 and +-2/3 mod 1, none integral. So an order-three line keeps
    AT MOST ONE of {10, 5bar, 1} from each sixteen, and a flipped family never descends from
    one.
    Measured: 657 breakings SO(10) -> SU(5) x U(1), and no parent sixteen keeps survivors
    of two SU(5) types. Teeth: with SO(10) unbroken, all 19 sixteens tested stay whole.

THE PRINCIPLE. Across both GUTs and both hypercharge embeddings, the arithmetic is the same.
The family's internal gaps are c times the charges of the broken roots, and at odd order
none is integral. Only an even-order element (t = 1/2) can keep two species together, as
a6e1c69 showed for u^c + e^c. A Standard Model built on the W(3,3) twist therefore needs an
orbifold with an order-two element, such as T^6/Z6-II or Z3 x Z2.

SCOPE. (a) is exact linear algebra on the computed spectra over the sampled parents; (b) is
a lemma plus its verification. Together with the Georgi-Glashow no-go, this covers the two
standard hypercharge embeddings of SU(5)-type unification in the order-three vacuum. It
does not cover non-GUT hypercharges spread across several group factors.
"""

import argparse
import importlib.util
import json
import os
import random
from collections import defaultdict
from fractions import Fraction as Fr

import numpy as np
import sympy as sp

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = 36


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, "analysis", name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


nog = _load("the_w33_vacuum_never_completes_a_standard_model_family")
gut, fam, het = nog.gut, nog.fam, nog.het


def components(Ps, roots):
    key = {tuple(x): i for i, x in enumerate(Ps)}
    seen, out = set(), []
    for i in range(len(Ps)):
        if i in seen:
            continue
        stack, comp = [i], []
        seen.add(i)
        while stack:
            k = stack.pop()
            comp.append(Ps[k])
            for r in roots:
                j = key.get(tuple(Ps[k] + r))
                if j is not None and j not in seen:
                    seen.add(j)
                    stack.append(j)
        out.append(comp)
    return out


def su5_family_charges(B, V, a1, c5):
    """U(1) charge vectors of the SU(5) tens and five-type multiplets, by orientation."""
    gauge, untw, fps = B.model(V, [a1])
    T = [np.array([Fr(int(x.p), int(x.q)) for x in v]) for v in sp.Matrix(gauge.tolist()).nullspace()]
    states = [(P, 3) for P in untw]
    for ns, st in fps.items():
        if ns[1] == 0 and ns[2] == 0:
            for Ps, m in st:
                states += [(P, m * 9) for P in Ps]
    sr, _, info = gut.diagram(c5)
    simple = [sr[i] for i in info["path"]]
    bucket = defaultdict(list)
    for P, m in states:
        bucket[m].append(P)
    tens, fives = defaultdict(int), defaultdict(int)
    for m, Ps in bucket.items():
        for comp in components(Ps, list(gauge)):
            labs = {tuple(int(x) for x in (np.array([P @ a for a in simple]) // S)) for P in comp}
            n = len(labs)
            if n not in (5, 10):
                continue
            hw = next(tuple(l) for l in labs if all(x >= 0 for x in l))
            q = tuple(sum(Fr(int(x), 6) * t for x, t in zip(comp[0], tv)) for tv in T)
            (tens if n == 10 else fives)[(hw, q)] += m * (len(comp) // n)
    return tens, fives


def majority(d):
    orient = defaultdict(int)
    for (hw, q), m in d.items():
        orient[hw] += m
    top = max(orient.values())
    return [q for (hw, q), m in d.items() if orient[hw] == top]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--parents", type=int, default=40)
    args = ap.parse_args()
    checks = {}
    B = fam.Builder()
    V = np.concatenate([B.shift(72, 1), B.shift(84, 2)])

    # (a) direct flipped U(1)_X
    rng = random.Random(20260917)
    ps = nog.three_family_parents(B, V, rng, "A4", args.parents)
    ratios = defaultdict(int)
    flippable = 0
    for a1, c5 in ps:
        tens, fives = su5_family_charges(B, V, a1, c5)
        ok = False
        for q10 in majority(tens):
            for q5 in majority(fives):
                if sp.Matrix([list(q10), list(q5)]).rank() == 2:
                    ratios["independent"] += 1
                    ok = True
                else:
                    lam = next(Fr(b) / Fr(a) for a, b in zip(q10, q5) if a != 0)
                    ratios[str(lam)] += 1
                    ok = ok or lam == -3
        flippable += ok
    print("  (a) three-family SU(5) models: %d, admitting a flipped U(1)_X: %d, 5bar/10 charge relations %s" % (
        len(ps), flippable, dict(ratios)))
    checks["a_no_flipped_U1X"] = len(ps) == args.parents and flippable == 0
    checks["a_ratio_minus_half_universal"] = set(ratios) == {"-1/2"}

    # (b) SO(10) -> SU(5) x U(1) by a Wilson line
    parents10 = []
    while len(parents10) < 6:
        a = B.line(rng, V, [])
        ok = ((B.R16 @ V) % S == 0) & ((B.R16 @ a) % S == 0)
        comps = het.root_components(B.R16[ok])
        if not any(fam.cname(c) == "D5" for c in comps):
            continue
        _, st = gut.model_states(B, V, [a])
        for c in comps:
            if fam.cname(c) == "D5" and abs(gut.family_indices(c, st)["n16"]) == 3:
                parents10.append((a, c))
                break
    breakings = tested = viol = teeth_n = teeth_whole = 0
    d = B.R16 @ V
    for _ in range(6000):
        a1, c10 = parents10[rng.randrange(len(parents10))]
        a2 = B.line(rng, V, [a1])
        pset = {tuple(x) for x in c10}
        ok = (d % S == 0) & ((B.R16 @ a1) % S == 0) & ((B.R16 @ a2) % S == 0)
        inside = [r for r in B.R16[ok] if tuple(r) in pset]
        untw = B.R16[((B.R16 @ a1) % S == 0) & ((d % S) == 12)]
        sixteens = [m for m in components(list(untw), list(c10)) if len(m) == 16]
        if len(inside) == len(c10):
            teeth_n += len(sixteens)
            teeth_whole += sum(1 for M in sixteens if sorted(len(x) for x in components(M, list(c10))) == [16])
            continue
        if not inside or sorted(fam.cname(c) for c in het.root_components(np.array(inside))) != ["A4"]:
            continue
        breakings += 1
        for M in sixteens:
            surv = [P for P in M if int(P @ a2) % S == 0]
            if surv:
                tested += 1
                viol += len({len(c) for c in components(surv, inside)}) > 1
    print("  (b) SO(10) -> SU(5)xU(1) breakings %d, sixteens with survivors %d, carrying two SU(5) types %d; "
          "teeth: %d of %d unbroken sixteens whole" % (breakings, tested, viol, teeth_whole, teeth_n))
    checks["b_lemma_arithmetic"] = all((Fr(g) * Fr(1, 3) / 4).denominator != 1 for g in (4, 8)) and \
        all(((Fr(g, 4) * t) % 1) != 0 for g in (4, 4, 8) for t in (Fr(1, 3), Fr(2, 3)))
    checks["b_no_sixteen_keeps_two_types"] = breakings > 100 and viol == 0
    checks["b_teeth_unbroken_whole"] = teeth_n > 0 and teeth_whole == teeth_n

    for k, v in checks.items():
        print("  %-36s %s" % (k, v))
    valid = all(checks.values())
    print("VALID:", valid)
    if args.write:
        payload = {
            "claim": "Flipped SU(5) x U(1)_X is closed at order three in the W(3,3) vacuum. Directly, the family ten and "
                     "anti-five carry proportional U(1) charges with ratio -1/2 in every three-family SU(5) model, so no "
                     "U(1)_X has the flipped ratio -3. Via SO(10) breaking, the X-gaps 4, 4, 8 inside a sixteen are all "
                     "non-integral multiples of 4c = +-1/3, so an order-three line keeps at most one of {10, 5bar, 1} per "
                     "sixteen. With the Georgi-Glashow no-go, both SU(5) hypercharge embeddings are excluded at order "
                     "three; a Standard Model on the W(3,3) twist needs an even-order element.",
            "a": {"models": len(ps), "flippable": flippable, "ratios": dict(ratios)},
            "b": {"breakings": breakings, "sixteens": tested, "violations": viol, "teethWhole": [teeth_whole, teeth_n],
                  "lemma": "P.a = k + cX; broken roots Delta X = +-4 => 4c = +-1/3 mod 1; gaps 4c, 4c, 8c all non-integral"},
            "principle": "odd order isolates every species inside a GUT multiplet; only order two (t = 1/2) can pair",
            "checks": checks, "valid": valid,
            "status": "(a) exact on sampled parents; (b) lemma plus verification",
            "sources": ["Holotrade a6e1c69", "Holotrade 47e85ab", "Holotrade fa65bd4", "Holotrade 35eb923",
                        "Antoniadis-Ellis-Hagelin-Nanopoulos flipped SU(5) string models (context)"]}
        with open(os.path.join(ROOT, "data", "w33_flipped_su5_closed_order3.json"), "w") as f:
            json.dump(payload, f, indent=1)
        print("written")


if __name__ == "__main__":
    main()
