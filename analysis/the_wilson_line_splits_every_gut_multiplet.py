#!/usr/bin/env python3
"""
WHY THE FAMILY NEVER COMPLETES: AN ORDER-THREE WILSON LINE KEEPS AT MOST ONE
STANDARD MODEL SPECIES OUT OF EACH GUT MULTIPLET.

bf7ce0a measured a law over 10000 Wilson-line breakings of the W(3,3)-twist vacuum:
whenever quark doublets are chiral, u^c and e^c are vector-like and d^c = L. This
file supplies the mechanism, and it is arithmetic rather than numerical.

THE LEMMA.  Let SU(5) sit in the unbroken gauge group and let a be a Wilson line of
order three that breaks it to SU(3) x SU(2) x U(1)_Y. All weights of one SU(5)
irrep differ by SU(5) roots, so on that irrep

    P . a = k + c Y(P),

with k constant on the irrep (the component of a orthogonal to the SU(5) span) and c
fixed by the component of a along it, which is proportional to the hypercharge
direction because the surviving subgroup is the centraliser of a.

The projection keeps the states with P . a in Z. The X and Y gauge bosons of SU(5)
carry Delta Y = +-5/6 and must be projected out, so 5c/6 is not an integer; and
since 3a lies in the lattice, every root has a . root in (1/3)Z, so

    5c/6 = +-1/3   (mod 1).

Now take the 10 = Q + u^c + e^c, with Y = 1/6, -2/3, 1:
    Q - u^c :  c (1/6 + 2/3) =  5c/6  = +-1/3   (mod 1)
    Q - e^c :  c (1/6 - 1)   = -5c/6  = -+1/3   (mod 1)
    u^c - e^c: c (-2/3 - 1)  = -5c/3  = -+2/3   (mod 1)
None is an integer, so no two of the three can satisfy P . a in Z together: AT MOST
ONE of Q, u^c, e^c survives. The same computation on 5bar = d^c + L, whose
hypercharges differ by 1/3 + 1/2 = 5/6, keeps at most one of d^c and L.

Note where order three enters. The dangerous case would be u^c - e^c, whose gap is
twice the basic one; at order N the gap 2t vanishes mod 1 when t = 1/2, which is
exactly what an order-two Wilson line allows. At order three t = +-1/3 and 2t =
-+2/3, so the third pair survives the argument too. The splitting is a property of
Z_3.

THE COROLLARY.  In this vacuum the SU(5) models carry n10 = n5bar = 3 (35eb923), and
quark doublets have zero index at every fixed point, so they come only from the three
untwisted planes (ade6ba9). Each untwisted 10 can donate at most one species. So
three quark doublets exhaust all three tens, and the untwisted sector then has
nothing left for u^c or e^c. That is precisely the measured law of bf7ce0a, and the
family cannot complete from the untwisted sector at all.

WHAT IS CHECKED HERE.
  1. 5c/6 = +-1/3 (mod 1) on every sampled breaking.
  2. On every parent untwisted SU(5) multiplet with at least two survivors, the
     survivors carry a SINGLE hypercharge: at most one species, as the lemma says.
  3. TEETH: for Wilson lines that do NOT break the SU(5), the same multiplets keep
     several hypercharges. The lemma's conclusion is caused by the breaking, and the
     test is not vacuous.
  4. The corollary directly: in breakings with three chiral untwisted quark doublets,
     the untwisted u^c and e^c indices are exactly zero.
  5. The 5bar splits the same way: no surviving multiplet carries both d^c and L.

SCOPE. The lemma is a proof, and items 1-5 are its verification on this vacuum.
Incomplete multiplets from Wilson lines are classical orbifold-GUT lore
(doublet-triplet splitting; Ibanez-Nilles-Quevedo and later orbifold GUT work). What
is established here is the sharp order-three form - at most ONE species per multiplet,
including the u^c/e^c pair that an order-two line would have kept - and the counting
corollary that closes bf7ce0a's measured law for the untwisted sector.
"""

import argparse
import importlib.util
import json
import os
import random
from fractions import Fraction as Fr

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
SPECIES = {Fr(1, 6): "Q", Fr(-2, 3): "uc", Fr(1, 3): "dc", Fr(-1, 2): "L", Fr(1): "ec"}


def multiplets(states, roots):
    key = {tuple(s): i for i, s in enumerate(states)}
    seen, out = set(), []
    for i in range(len(states)):
        if i in seen:
            continue
        stack, comp = [i], []
        seen.add(i)
        while stack:
            k = stack.pop()
            comp.append(k)
            for r in roots:
                j = key.get(tuple(states[k] + r))
                if j is not None and j not in seen:
                    seen.add(j)
                    stack.append(j)
        out.append([states[k] for k in comp])
    return out


def untwisted(B, V, a1):
    d = B.R16 @ V
    return B.R16[((B.R16 @ a1) % S == 0) & ((d % S) == 12)]


def c_of(a2, parent, y):
    basis = np.array(parent, float)
    _, sv, vt = np.linalg.svd(basis)
    Bs = vt[:int(np.sum(sv > 1e-8))]
    a_par = Bs.T @ (Bs @ a2.astype(float))
    brk = next(r for r in parent if abs(float(r @ y)) > 1e-9)
    return float(brk @ a_par) / float(brk @ y)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--budget", type=int, default=4000)
    args = ap.parse_args()
    B = fam.Builder()
    V = np.concatenate([B.shift(72, 1), B.shift(84, 2)])
    rng = random.Random(20260915)
    ps = nog.three_family_parents(B, V, rng, "A4", 4)
    print("  three-family SU(5) parents:", len(ps))
    checks, out = {}, {}

    cvals, tested, multi_y, byrep, corollary, corollary_fail = {}, 0, 0, {}, 0, 0
    fivebar_tested = fivebar_both = 0
    breakings = 0
    for _ in range(args.budget):
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
        breakings += 1
        t = round((c_of(a2, c5, y) * 5 / 6) % 1, 6)
        cvals[t] = cvals.get(t, 0) + 1
        seen_species = {}
        for M in multiplets(list(untwisted(B, V, a1)), list(c5)):
            surv = [P for P in M if int(P @ a2) % S == 0]
            Ys = {Fr(int(round(float(P @ y) / S * 6)), 6) for P in surv}
            if len(M) == 5 and len(surv) >= 2:                  # a 5bar (or 5): d^c versus L
                fivebar_tested += 1
                fivebar_both += len({SPECIES.get(v) for v in Ys} & {"dc", "L"}) > 1
            if len(surv) >= 2:
                tested += 1
                multi_y += len(Ys) > 1
            for v in Ys:
                if v in SPECIES:
                    seen_species[SPECIES[v]] = seen_species.get(SPECIES[v], 0) + len(
                        [P for P in surv if Fr(int(round(float(P @ y) / S * 6)), 6) == v])
        # the corollary, on the untwisted sector alone
        res = nog.sm_content(B, V, [a1, a2], c5, a2s[0], a1s[0])
        if res is None:
            continue
        untw_only = seen_species
        if untw_only.get("Q", 0) >= 6:                           # three (3,2)s = 6 weights
            corollary += 1
            if untw_only.get("uc", 0) or untw_only.get("ec", 0):
                corollary_fail += 1
    print("  breakings sampled: %d" % breakings)
    print("  (5c/6 mod 1) values:", dict(sorted(cvals.items())))
    print("  untwisted multiplets with >=2 survivors: %d, carrying more than one hypercharge: %d" % (tested, multi_y))
    print("  five-plets with >=2 survivors: %d, carrying both d^c and L: %d" % (fivebar_tested, fivebar_both))
    print("  breakings whose untwisted sector holds three quark doublets: %d, of which also hold u^c or e^c: %d" % (
        corollary, corollary_fail))
    checks["c_is_plus_minus_one_third"] = bool(cvals) and set(cvals) <= {round(1 / 3, 6), round(2 / 3, 6)}
    checks["one_species_per_multiplet"] = tested > 2000 and multi_y == 0
    checks["fivebar_never_keeps_both"] = fivebar_both == 0
    checks["corollary_no_uc_or_ec_beside_three_Q"] = corollary > 0 and corollary_fail == 0

    # TEETH: a Wilson line that leaves SU(5) unbroken keeps several hypercharges per multiplet
    a1, c5 = ps[0]
    sr, A, info = gut.diagram(c5)
    p = info["path"]
    aa, bb, dd = sr[p[0]], sr[p[1]], sr[p[3]]
    y0 = nog.hypercharge(c5, [aa, bb, aa + bb, -aa, -bb, -(aa + bb)], [dd, -dd])
    Ms = multiplets(list(untwisted(B, V, a1)), list(c5))
    whole = multi = trials = 0
    rng2 = random.Random(99)
    while trials < 25:
        a2 = B.line(rng2, V, [a1])
        inside = [r for r in nog.gauge(B, V, [a1, a2]) if tuple(r) in {tuple(x) for x in c5}]
        if len(inside) != len(c5):
            continue
        trials += 1
        for M in Ms:
            surv = [P for P in M if int(P @ a2) % S == 0]
            if len(surv) < 2:
                continue
            whole += 1
            multi += len({Fr(int(round(float(P @ y0) / S * 6)), 6) for P in surv}) > 1
    print("  teeth: unbroken-SU(5) lines %d, multiplets with >=2 survivors %d, with several hypercharges %d" % (
        trials, whole, multi))
    checks["teeth_unbroken_keeps_several_species"] = whole > 0 and multi == whole
    out = {"multipletSizes": sorted({len(M) for M in Ms}), "cValues": {str(k): v for k, v in sorted(cvals.items())},
           "multipletsTested": tested, "multipletsWithSeveralHypercharges": multi_y,
           "fivebarTested": fivebar_tested, "fivebarWithBoth": fivebar_both,
           "corollaryCases": corollary, "corollaryFailures": corollary_fail,
           "teeth": {"unbrokenLines": trials, "multiplets": whole, "withSeveralHypercharges": multi}}
    for k, v in checks.items():
        print("  %-42s %s" % (k, v))
    valid = all(checks.values())
    print("VALID:", valid)
    if args.write:
        payload = {"claim": "An order-three Wilson line breaking SU(5) to the Standard Model keeps at most one of Q, u^c, e^c "
                            "from each 10 and at most one of d^c, L from each 5bar, because 5c/6 = +-1/3 mod 1 makes all three "
                            "pairwise hypercharge gaps non-integral. With n10 = 3 and quark doublets confined to the three "
                            "untwisted planes, three quark doublets exhaust the tens, so the untwisted sector can hold no u^c "
                            "or e^c: this is the mechanism behind the measured law of bf7ce0a.",
                   "lemma": "P.a = k + cY on an SU(5) irrep; breaking forces 5c/6 = +-1/3 (mod 1); the gaps 5c/6, -5c/6 and "
                            "-5c/3 are then all non-integral, so at most one species per multiplet survives.",
                   "orderThreeIsEssential": "at order two the gap 2t vanishes for t = 1/2, so u^c and e^c would survive together",
                   "measurements": out, "checks": checks, "valid": valid,
                   "status": "lemma proved arithmetically; items verified on this vacuum",
                   "sources": ["Holotrade fbd2c5f", "Holotrade ade6ba9", "Holotrade 35eb923", "Holotrade bf7ce0a",
                               "classical orbifold-GUT doublet-triplet splitting"]}
        with open(os.path.join(ROOT, "data", "w33_wilson_line_splits_gut_multiplets.json"), "w") as f:
            json.dump(payload, f, indent=1)
        print("written")


if __name__ == "__main__":
    main()
