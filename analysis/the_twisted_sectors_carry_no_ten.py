#!/usr/bin/env python3
"""
THE TWISTED SECTORS CARRY NO TEN: A NORM BUDGET OF 2/15 AGAINST A COSET FLOOR OF
2/9, WHICH COMPLETES THE STANDARD MODEL NO-GO.

a6e1c69 proved the untwisted half: an order-three Wilson line keeps at most one of
Q, u^c, e^c out of each 10. The twisted half was still only measured (ade6ba9:
quark doublets carry no index at any fixed point). This file proves it.

THE BUDGET.  A twisted massless state satisfies P^2/2 + N = 2/3, so |P|^2 = 4/3 at
N = 0 and 2/3 at N = 1/3. Every weight of the 10 (or 10bar) of SU(5) has the same
norm under the Weyl group,
    |w|^2 = |w_3|^2 + |w_2|^2 + (6/5) Y^2 = 2/3 + 1/2 + 1/30 = 6/5,
for each of its pieces Q (Y = 1/6), u^c (Y = -2/3) and e^c (Y = 1). Since
6/5 > 2/3, no N = 1/3 state can carry one. At N = 0 the rest of the charge would
have to satisfy
    |P_rest|^2 = 4/3 - 6/5 = 2/15 = 0.1333...

THE FLOOR.  P_rest includes the whole second E8, where P_2 lies in the coset
E8 + V_f^(2) of the local shift. For a shift with 3V in E8, every coset norm lies in
(2/9)Z, so a NONTRIVIAL coset has minimum norm at least 2/9 = 0.2222... > 2/15.

    Nontrivial second-E8 coset  =>  no twisted massless state carries a ten-weight,
    hence no twisted Q, u^c or e^c.

WHEN COULD THE HYPOTHESIS FAIL?  Only if V_f^(2) lies in E8 itself. Anomaly classes
are additive, class(V + a) = class(V) + class(a) mod 3 because 3V.a is an integer, and
the Wilson-line conditions force class(a^(1)) + class(a^(2)) = 0 mod 3. Here
class(V^(2)) = 2, so a trivial second-E8 shift needs
    V_2 + n_1 a_1^(2) + n_2 a_2^(2)  in  E8,
that is, the class of V_2 must lie in the span of the Wilson-line classes inside
E8/3E8 = F_3^8. That is a codimension-six coincidence, and it does not occur anywhere
in the sample here. Where it did occur one would still need the leftover 2/15 to be
realised inside the first E8, which this file does not analyse: that case is OPEN.

WHAT IS CHECKED.
  1. Over every sampled fixed point, the minimum norm of the second-E8 coset lies in
     {2/9, 4/9, 2/3, 8/9} and is never 0, so the hypothesis holds throughout.
  2. There are no twisted massless states whose SU(5) projection has norm 6/5, i.e.
     no twisted ten-weights at all.
  3. By species: the twisted sectors supply d^c and L, and never Q, u^c or e^c. The
     detector is therefore not blind - it sees the five-plet species it should.
  4. TEETH: the untwisted sector does contain ten-weights of norm 6/5, so the
     6/5 test finds them when they are present.
  5. The lightest twisted colour-triplet weak-doublet has |P|^2 = 2 exactly, a clean
     gap above the massless value 4/3; 2 is the norm of an SU(5) adjoint weight
     ((3,2) with Y = -5/6), which is what the budget leaves available.

THE COMPLETED NO-GO.  Combining with a6e1c69:
  - Q, u^c and e^c can only come from untwisted tens (this file);
  - each untwisted ten donates at most one of them (a6e1c69);
  - this vacuum has n10 = 3 and Q is a multiple of three (ade6ba9, 35eb923).
So three quark doublets exhaust the three tens and force u^c = e^c = 0. The measured
law of bf7ce0a is now derived, and no Wilson-line breaking of the W(3,3)-twist
vacuum completes a Standard Model family.

SCOPE. The budget and floor are arithmetic. The hypothesis (nontrivial second-E8
coset) is verified on every sampled fixed point rather than proved, and the
codimension-six exceptional case is open.
"""

import argparse
import importlib.util
import json
import os
import random

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = 36


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, "analysis", name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


nog = _load("the_w33_vacuum_never_completes_a_standard_model_family")
gut, fam, het = nog.gut, nog.fam, nog.het
from fractions import Fraction as Fr  # noqa: E402

SPEC = {(True, True, Fr(1, 6)): "Q", (True, True, Fr(-1, 6)): "Qbar",
        (True, False, Fr(-2, 3)): "uc", (True, False, Fr(2, 3)): "ucbar",
        (True, False, Fr(1, 3)): "dc", (True, False, Fr(-1, 3)): "dcbar",
        (False, True, Fr(-1, 2)): "L", (False, True, Fr(1, 2)): "Lbar",
        (False, False, Fr(1)): "ec", (False, False, Fr(-1)): "ecbar"}
TEN = {"Q", "Qbar", "uc", "ucbar", "ec", "ecbar"}


def anomaly_class(z):
    return int(z @ z // 8) % 3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--models", type=int, default=250)
    args = ap.parse_args()
    B = fam.Builder()
    V = np.concatenate([B.shift(72, 1), B.shift(84, 2)])
    rng = random.Random(20260916)
    ps = nog.three_family_parents(B, V, rng, "A4", 4)
    checks = {}
    print("  gauge shift classes: first E8 %d, second E8 %d" % (anomaly_class(V[:8]), anomaly_class(V[8:])))

    minsecond, models, fixedpoints = {}, 0, 0
    ten_twisted = ten_untwisted = 0
    species = {"untwisted": {}, "twisted": {}}
    lightest = {}
    trivial_second = 0
    wilson_classes = {}
    while models < args.models:
        a1, c5 = ps[rng.randrange(len(ps))]
        a2 = B.line(rng, V, [a1])
        pset = {tuple(x) for x in c5}
        inside = np.array([r for r in nog.gauge(B, V, [a1, a2]) if tuple(r) in pset], dtype=np.int64)
        if not len(inside):
            continue
        comps = het.root_components(inside)
        a2s = [x for x in comps if fam.cname(x) == "A2"]
        a1s = [x for x in comps if fam.cname(x) == "A1"]
        if len(a2s) != 1 or not a1s or len(a2s) + len(a1s) != len(comps):
            continue
        y = nog.hypercharge(c5, a2s[0], a1s[0])
        if y is None:
            continue
        models += 1
        for a in (a1, a2):
            k = (anomaly_class(a[:8]), anomaly_class(a[8:]))
            wilson_classes[k] = wilson_classes.get(k, 0) + 1
        basis = np.array(c5, float)
        _, sv, vt = np.linalg.svd(basis)
        Bs = vt[:int(np.sum(sv > 1e-8))]
        srs = list(gut.diagram(np.array(a2s[0]))[0]) + list(gut.diagram(np.array(a1s[0]))[0])

        def classify(P, m, bucket):
            L = np.stack([P @ a for a in srs], axis=1) // S
            Ys = (P @ y) / S
            for row, yy in zip(L, Ys):
                lab = tuple(int(t) for t in row)
                nm = SPEC.get(((lab[0] - lab[1]) % 3 != 0, lab[2] % 2 != 0, Fr(int(round(yy * 6)), 6)))
                if nm:
                    species[bucket][nm] = species[bucket].get(nm, 0) + m

        _, untw, fps = B.model(V, [a1, a2])
        classify(untw, 3, "untwisted")
        proj_u = np.sum((untw.astype(float) @ Bs.T) ** 2, axis=1) / S
        ten_untwisted += int(np.sum(np.abs(proj_u - 6 / 5) < 1e-6))
        for ns, st in fps.items():
            if ns[2] != 0:
                continue
            fixedpoints += 1
            Vf = V + ns[0] * a1 + ns[1] * a2
            V2 = Vf[8:] - B.cvp6(Vf[8:])
            m2 = float(np.min(np.sum((B.lam6 + V2) ** 2, axis=1))) / S
            minsecond[round(m2, 4)] = minsecond.get(round(m2, 4), 0) + 1
            trivial_second += m2 < 1e-9
            for P, m in st:
                if not len(P):
                    continue
                classify(P, m, "twisted")
                proj = np.sum((P.astype(float) @ Bs.T) ** 2, axis=1) / S
                ten_twisted += int(np.sum(np.abs(proj - 6 / 5) < 1e-6))
            # lightest twisted colour-triplet weak-doublet, massless or not
            W1, h1 = B.coset(Vf[:8])
            W2, h2 = B.coset(Vf[8:])
            lo = None
            for i in range(len(W1)):
                sel = np.nonzero(h1[i] + h2 <= 90)[0]
                if not len(sel):
                    continue
                P = np.hstack([np.repeat(W1[i][None, :], len(sel), axis=0), W2[sel]])
                L = np.stack([P @ a for a in srs], axis=1) // S
                nrm = (h1[i] + h2[sel]) / float(S)
                for row, nn in zip(L, nrm):
                    lab = tuple(int(t) for t in row)
                    if (lab[0] - lab[1]) % 3 != 0 and lab[2] % 2 != 0 and (lo is None or nn < lo):
                        lo = nn
            if lo is not None:
                lightest[round(float(lo), 4)] = lightest.get(round(float(lo), 4), 0) + 1

    print("  models %d, fixed points %d" % (models, fixedpoints))
    print("  Wilson-line classes (first, second):", dict(sorted(wilson_classes.items())))
    print("  minimum norm of the second-E8 coset:", dict(sorted(minsecond.items())), " trivial:", trivial_second)
    print("  ten-weights (SU(5) projection of norm 6/5): untwisted %d, twisted %d" % (ten_untwisted, ten_twisted))
    print("  species, untwisted:", dict(sorted(species["untwisted"].items())))
    print("  species, twisted:  ", dict(sorted(species["twisted"].items())))
    print("  lightest twisted colour-triplet weak-doublet |P|^2:", dict(sorted(lightest.items())))
    checks["second_e8_coset_never_trivial"] = trivial_second == 0 and fixedpoints > 500
    checks["coset_floor_above_budget"] = min(minsecond) > 4 / 3 - 6 / 5
    checks["no_twisted_ten_weights"] = ten_twisted == 0
    checks["teeth_untwisted_has_ten_weights"] = ten_untwisted > 0
    checks["no_twisted_ten_species"] = all(species["twisted"].get(s, 0) == 0 for s in TEN)
    checks["twisted_does_supply_fiveplet_species"] = sum(species["twisted"].get(s, 0) for s in ("dc", "dcbar", "L", "Lbar")) > 0
    checks["lightest_twisted_doublet_is_two"] = set(lightest) == {2.0}
    for k, v in checks.items():
        print("  %-42s %s" % (k, v))
    valid = all(checks.values())
    print("VALID:", valid)
    if args.write:
        payload = {
            "claim": "Twisted massless states of the W(3,3)-twist vacuum carry no weight of the SU(5) ten: a ten-weight has "
                     "norm 6/5, massless twisted states have |P|^2 = 4/3, and the leftover 2/15 is below the 2/9 floor of any "
                     "nontrivial E8 coset, which is what the second-E8 part of every local shift is. Hence Q, u^c and e^c are "
                     "untwisted-only, which with a6e1c69 (at most one species per untwisted ten) and n10 = 3 completes the "
                     "Standard Model no-go of bf7ce0a.",
            "budget": {"tenWeightNorm": "6/5", "masslessTwisted": "4/3", "leftover": "2/15", "cosetFloor": "2/9"},
            "measurements": {"models": models, "fixedPoints": fixedpoints,
                             "minSecondE8CosetNorm": {str(k): v for k, v in sorted(minsecond.items())},
                             "trivialSecondE8": trivial_second,
                             "tenWeightsUntwisted": ten_untwisted, "tenWeightsTwisted": ten_twisted,
                             "speciesUntwisted": species["untwisted"], "speciesTwisted": species["twisted"],
                             "lightestTwistedDoublet": {str(k): v for k, v in sorted(lightest.items())},
                             "wilsonClasses": {str(k): v for k, v in sorted(wilson_classes.items())}},
            "openCase": "a trivial second-E8 local shift needs class(V_2) in the span of the Wilson-line classes inside "
                        "E8/3E8 = F_3^8, a codimension-six coincidence absent from this sample and not analysed here",
            "checks": checks, "valid": valid,
            "status": "budget and floor are arithmetic; the hypothesis is verified on every sampled fixed point",
            "sources": ["Holotrade ade6ba9", "Holotrade 35eb923", "Holotrade bf7ce0a", "Holotrade ed1eaca", "Holotrade a6e1c69"]}
        with open(os.path.join(ROOT, "data", "w33_twisted_sectors_carry_no_ten.json"), "w") as f:
            json.dump(payload, f, indent=1)
        print("written")


if __name__ == "__main__":
    main()
