#!/usr/bin/env python3
"""
THE EXOTIC MASS RANK IS SET BY WHERE THE SINGLETS CONDENSE, NOT BY GENERIC COUPLINGS:
SYMMETRIC VACUA GIVE RANK ONE, AND RANK NINE NEEDS EACH TWISTED SINGLET SPREAD OVER
SEVERAL FIXED POINTS WITH UNEQUAL VEVS.

Reads and checks the other track's exotic-decoupling chain for the frozen SU(5)
three-family witness:
    6871d80  w33_exotic_sextic_nonic_completion      (selection rules, "structural rank 9")
    ae76a54  w33_exotic_worldsheet_instanton_kernel  (positive classical kernels)
    4fdf7b0  w33_exotic_benchmark_mass_matrix        (Vandermonde C_rc = (r+1)^c, rank 9)
    6ee5e7b  w33_su5_singlet_flat_directions         (16 quartic flat rays)
    add6a87  w33_su5_fi_degree12_flatness            (FI pairs, degree-12 cube)

WHAT HOLDS UP (credited).
  - Their counts are right: 2 sextic and 40 nonic gauge-charge solutions per anti-five
    type, reproduced here.
  - Every sextic channel uses singlets that DO receive VEVs in their flat/FI vacuum:
    untwisted pairs (0,1) and (2,3) - exactly the two FI-cancelling bilinears - and
    twisted types 0..3. The chain is consistent at the level of momentum types.

A REPRODUCIBILITY BUG.  The committed w33_exotic_sextic_nonic_completion.py does not
run. Its nonic loop appends the whole list of index tuples,
    for ui in u5.get(need, []): nsol.append((ti, ui))
where the sextic loop two blocks above correctly iterates `for tt in ti`, so the
nonic block raises TypeError. The committed JSON also lacks the `massless_spectrum`
and `details` keys the code writes, so it was produced by a different version of the
file. With the one-line fix the published counts reproduce exactly (checked below).

THE GAP.  The rank-nine claim rests on replacing the coefficient matrix by the
Vandermonde C_rc = (r+1)^c and arguing that the rank<9 locus is a proper subvariety
of coupling space. But the rows are not independent parameters. They are the nine
degenerate fixed points f in Z_3^2 of the two tori without a Wilson line, and every
ingredient - the space-group rule f + g + g' = 0, the Rule-4 coincidence filter, and
the classical kernels K_S / K_D - is invariant under translating all fixed points
together. The column data (anti-five type, untwisted plane, CFT and untwisted-VEV
coefficients) carry no fixed-point label. So

    M(f, c) = sum_{s} A_{s}(f) B_{s}(c),   A_s(f) = sum_{g + g' = -f} v_t(g) v_t'(g') K(f,g,g'),

and each anti-five type uses ONE twisted singlet pair (t,t') in both its sextic and
nonic channels, so only four pairs occur. The rank is therefore controlled by the
fixed-point profile v_t(g) of the twisted singlet VEVs, which none of the certificates
specify.

TWO BOUNDS (proved, then verified).
  A. TRANSLATION-INVARIANT VEVs => RANK 1. If v_t(g + h) = v_t(g) for all h, then
     M(f + h, c) = M(f, c): all nine rows coincide.
  B. EACH TYPE AT A SINGLE FIXED POINT => RANK <= 4. A_s is then supported on the one
     point f = -(g_t + g_t'), and there are four pairs.

WHAT IS MEASURED.
  - Translation-invariant, single-point and the diagonal line {(b,b)} - the placement
    the degree-12 cube of add6a87 uses - all give rank 1.
  - Rank 9 is reachable, but only when each of the four twisted types sits on at least
    two fixed points, and reliably only from about four, with unequal values.

CONSEQUENCE. "Generic rank 9" is not a statement about generic couplings; it is a
condition on the vacuum. In every symmetric vacuum eight of the nine exotic
five-plets stay massless at this order. Decoupling the exotics requires showing that
the D- and F-flat vacuum spreads each twisted singlet over several fixed points with
unequal VEVs - which the D-terms permit (all nine copies carry identical gauge
charges) but which F-terms at the relevant order may lift. That is the open problem
this front actually has.

SCOPE. The two bounds are proofs. The support-size table is a measurement over random
placements with generic nonzero column coefficients, i.e. an upper bound on what any
realisation can achieve.
"""

import argparse
import contextlib
import importlib.util
import io
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


def enumerate_channels(sex):
    """the other track's enumeration, with the nonic loop fixed; returns pair data and counts."""
    parent = json.load(open(os.path.join(ROOT, "data", "w33_vacuum_three_family_gut.json")))
    line = np.array(parent["examples"]["su5_three_families"]["lines"][0], dtype=np.int64)
    fam, gut = sex.fam, sex.gut
    B = fam.Builder()
    V = np.concatenate([B.shift(72, 1), B.shift(84, 2)])
    gauge, untw, fps = B.model(V, [line])
    comps = fam.het.root_components(gauge)
    A4 = next(C for C in comps if fam.cname(C) == "A4" and np.any(C[:, :8]))
    sr = np.array(gut.diagram(A4)[0], dtype=np.int64)
    L5b, L5 = (0, 0, 0, 1), (0, 0, 1, 0)
    UC = sex.multiplets(untw, A4)
    bars = [C for C in UC if len(C) == 5 and sex.highest(C, sr) == L5b]
    US = [C[0] for C in UC if len(C) == 1]
    TC = {n1: [c for P, m in fps[(n1, 0, 0)] for c in sex.multiplets(P, A4)] for n1 in range(3)}
    five = next(C for C in TC[0] if len(C) == 5 and sex.highest(C, sr) == L5)
    TS = [(n1, C[0]) for n1 in range(3) for C in TC[n1] if len(C) == 1]
    Ds = []
    for Cb in bars:
        ds = {tuple((a + b).tolist()) for a in five for b in Cb
              if all(x + y == 0 for x, y in zip(a @ sr.T // S, b @ sr.T // S))}
        assert len(ds) == 1
        Ds.append(np.array(next(iter(ds)), dtype=np.int64))
    tvec = [x[1] for x in TS]
    t2, u2, u5 = sex.multiset_sums(tvec, 2), sex.multiset_sums(US, 2), sex.multiset_sums(US, 5)
    out = []
    for D in Ds:
        sext, non = set(), set()
        for st, ti in t2.items():
            need = sex.keyv(-D - np.array(st, dtype=np.int64))
            for ui in u2.get(need, []):
                for tt in ti:
                    sext.add((tuple(sorted(tt)), tuple(sorted(ui))))
            for ui in u5.get(need, []):
                for tt in ti:                                  # the fix: iterate, as the sextic loop does
                    non.add((tuple(sorted(tt)), tuple(sorted(ui))))
        out.append({"sextic": sorted(sext), "nonic": sorted(non)})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    checks, report = {}, {}
    sex = _load("w33_exotic_sextic_nonic_completion")
    flat = _load("w33_su5_singlet_flat_directions")
    ker = _load("w33_exotic_worldsheet_instanton_kernel")

    # 1. the committed script does not run, and its JSON is not its output
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            sex.main(write=False)
        crashed, err = False, ""
    except TypeError as e:
        crashed, err = True, str(e)
    committed = json.load(open(os.path.join(ROOT, "data", "w33_exotic_sextic_nonic_completion.json")))
    src = open(os.path.join(ROOT, "analysis", "w33_exotic_sextic_nonic_completion.py")).read()
    missing = [k for k in ("massless_spectrum", "details") if ("'%s'" % k) in src and k not in json.dumps(committed)]
    print("  committed sextic/nonic script crashes: %s (%s)" % (crashed, err))
    print("  keys written by the code but absent from the committed JSON:", missing)
    report["bug"] = {"committedScriptCrashes": crashed, "error": err, "jsonMissingKeysTheCodeWrites": missing,
                     "line": "for ui in u5.get(need,[]):nsol.append((ti,ui))",
                     "fix": "for ui in u5.get(need,[]):\n    for tt in ti: nsol.append((tt,ui))"}

    # 2. with the fix, their counts reproduce
    ch = enumerate_channels(sex)
    sext_counts = [len(c["sextic"]) for c in ch]
    non_counts = [len(c["nonic"]) for c in ch]
    print("  fixed enumeration: sextic solutions per anti-five type %s, nonic %s" % (sext_counts, non_counts))
    checks["their_counts_reproduce_with_fix"] = sext_counts == [2, 2, 2, 2] and non_counts == [40, 40, 40, 40]

    # 3. consistency credit: sextic singlets are exactly the ones the flat/FI vacuum gives VEVs
    with contextlib.redirect_stdout(io.StringIO()):
        fo = flat.main(write=False)
    U_vev = {i for r in fo["directions"] for k, i in r["support"] if k == "U"}
    T_vev = {i for r in fo["directions"] for k, i in r["support"] if k != "U"}
    alive = all(set(u) <= U_vev and set(t) <= T_vev for c in ch for t, u in c["sextic"])
    pairs = {}
    for j, c in enumerate(ch):
        tp = {t for t, _ in c["sextic"]} | {t for t, _ in c["nonic"]}
        pairs[j] = sorted(tp)
    one_pair_each = all(len(v) == 1 for v in pairs.values())
    print("  every sextic channel uses VEVd singlets: %s   twisted pair per anti-five type: %s" % (alive, pairs))
    checks["sextic_channels_use_vacuum_singlets"] = alive
    checks["one_twisted_pair_per_antifive_type"] = one_pair_each
    PAIRS = {j: v[0] for j, v in pairs.items()}
    types = sorted({t for p in PAIRS.values() for t in p})

    # 4. the mass matrix as a function of the fixed-point VEV profile
    KS, KD = ker.KS(1.0), ker.KD(1.0)
    FP = [(a, b) for a in range(3) for b in range(3)]

    def row_fn(f, pair, plane, v):
        t, u = pair
        tot = 0.0
        for g in FP:
            gp = ((-f[0] - g[0]) % 3, (-f[1] - g[1]) % 3)
            co = [f[i] == g[i] == gp[i] for i in range(2)]
            if plane in (2, 3) and co[plane - 2]:
                continue                                      # Rule 4 for the sextic columns
            k = 1.0
            for i in range(2):
                k *= KS if co[i] else KD
            tot += v[t][g] * v[u][gp] * k
        return tot

    def mass(v, seed):
        rr = random.Random(seed)
        cols = [rr.uniform(0.5, 2.0) * np.array([row_fn(f, PAIRS[j], plane, v) for f in FP])
                for j in range(4) for plane in (2, 3, 1)]
        return np.array(cols).T                               # 9 rows x 12 columns

    def rank(v, seeds=4):
        return sorted({int(np.linalg.matrix_rank(mass(v, s), tol=1e-9)) for s in range(seeds)})

    rng = random.Random(20260916)
    named = {
        "translation_invariant": {t: {g: 1.0 for g in FP} for t in types},
        "single_point_origin": {t: {g: float(g == (0, 0)) for g in FP} for t in types},
        "diagonal_line_of_the_degree12_cube": {t: {g: float(g[0] == g[1]) for g in FP} for t in types},
        "generic_all_points": {t: {g: rng.uniform(0.2, 1.5) for g in FP} for t in types},
    }
    named_ranks = {k: rank(v) for k, v in named.items()}
    for k, v in named_ranks.items():
        print("  %-40s rank %s" % (k, v))
    checks["A_translation_invariant_rank_one"] = named_ranks["translation_invariant"] == [1]
    checks["symmetric_placements_rank_one"] = named_ranks["single_point_origin"] == [1] and \
        named_ranks["diagonal_line_of_the_degree12_cube"] == [1]
    checks["generic_profile_reaches_rank_nine"] = named_ranks["generic_all_points"] == [9]

    # bound B and the support-size table
    table = {}
    for k in range(1, 10):
        hist = {}
        for trial in range(200):
            v = {}
            for t in types:
                sup = rng.sample(FP, k)
                v[t] = {g: (rng.uniform(0.3, 1.5) if g in sup else 0.0) for g in FP}
            r = int(np.linalg.matrix_rank(mass(v, trial), tol=1e-9))
            hist[r] = hist.get(r, 0) + 1
        table[k] = {"maxRank": max(hist), "fractionRank9": round(hist.get(9, 0) / 200, 3),
                    "histogram": {str(a): b for a, b in sorted(hist.items())}}
        print("  VEVs on k=%d fixed points per type: max rank %d, fraction reaching 9: %.2f" % (
            k, table[k]["maxRank"], table[k]["fractionRank9"]))
    checks["B_single_point_rank_at_most_four"] = table[1]["maxRank"] <= 4
    checks["rank_nine_needs_spread"] = table[1]["fractionRank9"] == 0 and table[4]["fractionRank9"] == 1.0

    for k, v in checks.items():
        print("  %-42s %s" % (k, v))
    valid = all(checks.values())
    print("VALID:", valid)
    if args.write:
        payload = {
            "claim": "The exotic mass matrix of the frozen SU(5) witness factorises through the nine degenerate fixed points: "
                     "M(f,c) = sum_s A_s(f) B_s(c), with one twisted singlet pair per anti-five type. Every ingredient is "
                     "translation-invariant on Z_3^2, so translation-invariant VEVs give rank 1 and single-fixed-point VEVs give "
                     "rank <= 4; the diagonal placement used for the degree-12 cube also gives rank 1. Rank 9 requires each twisted "
                     "singlet to be spread over several fixed points with unequal VEVs - a condition on the vacuum, not a generic "
                     "property of the couplings.",
            "credited": {"countsReproduce": checks["their_counts_reproduce_with_fix"],
                         "sexticChannelsUseVacuumSinglets": alive,
                         "untwistedPairsAreTheFIBilinears": True},
            "reproducibilityBug": report["bug"],
            "twistedPairPerAntifiveType": {str(k): list(v) for k, v in PAIRS.items()},
            "rankByNamedProfile": named_ranks, "rankBySupportSize": table,
            "checks": checks, "valid": valid,
            "status": "bounds A and B are proofs; the support-size table measures what generic realisations can reach",
            "sources": ["Holotrade 6871d80", "Holotrade ae76a54", "Holotrade 4fdf7b0", "Holotrade 6ee5e7b", "Holotrade add6a87",
                        "Kobayashi-Parameswaran-Ramos-Sanchez-Zavala arXiv:1107.2137 (Rules 4/5)"]}
        with open(os.path.join(ROOT, "data", "w33_exotic_mass_rank_by_condensate.json"), "w") as f:
            json.dump(payload, f, indent=1)
        print("written")


if __name__ == "__main__":
    main()
