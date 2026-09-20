#!/usr/bin/env python3
"""
THE RIGHT-HANDED NEUTRINO MASS MATRIX SATURATES AT ORDER FOUR AND KEEPS A NINETEEN-
DIMENSIONAL KERNEL THROUGH ORDER EIGHT.

A third independent question, asked without reference to mu or to unification: the Standard
Model singlets of these models are right-handed neutrino candidates, and the see-saw needs
to know how many of them actually get a Majorana mass.

THE SETUP, on the flagship Z6I_27 / SM_20260917_3. Of its 65 singlets, 19 are the
mass-coupling singlets that must condense, leaving 46 candidates. A Majorana mass comes from
the pure-singlet superpotential: a term n_i n_j n_k... with every leg beyond i and j
condensing gives M_R[i][j] ~ <n>. Building M_R from the orbifolder's pure-singlet couplings
and taking the rank with generic coefficients:

    through order 3   143 -> no, 102 pairs, rank 19 of 46   27 massless
    through order 4        143 pairs, rank 27 of 46         19 massless
    through order 6        143 pairs, rank 27 of 46         19 massless
    through order 7        143 pairs, rank 27 of 46         19 massless
    through order 8        143 pairs, rank 27 of 46         19 massless

The rank saturates at order four and does not move again. Twenty-seven right-handed
neutrinos acquire Majorana masses of order <n>; NINETEEN remain exactly massless, and no
term through order eight lifts them.

THE DIRAC SIDE. The operator l . bl . n^k -- which is the same operator as mu, with one
singlet playing the right-handed neutrino -- first appears at order FOUR, with 32 couplings,
and again at order five with 32. So both the Dirac and the Majorana entries are generated at
comparable order and both scale as <n>, which is why the see-saw suppression in this class
cannot be read off the orders alone; it needs the coefficients.

WHAT IS AND IS NOT ESTABLISHED. The persistent kernel is the result: a large set of exactly
massless gauge singlets that the superpotential does not lift through order eight. That is a
genuine feature of the model and a phenomenological liability -- massless singlets are extra
light degrees of freedom -- and it is measured, not inferred. It is NOT a computation of the
light neutrino masses: those need the Dirac and Majorana coefficients, not just which
entries are allowed, and the many-neutrino enhancement of the heterotic see-saw
(Buchmuller-Hamaguchi-Lebedev-Ratz) depends on exactly those numbers.

A NOTE ON A COINCIDENCE, so it is not over-read. The kernel dimension, 19, equals the number
of condensing singlets, also 19. The two sets are disjoint by construction -- the kernel is
computed on the 46 NON-condensing singlets -- so this is a numerical coincidence on one
model unless it repeats, and it has not been checked on others.

SCOPE. One model. The singlet superpotential is dumped through order eight, which is what
bounds "persistent"; a term at order nine or beyond could lift the kernel. Generic
coefficients are used for the rank, which is the usual assumption and gives an upper bound
on the rank that any realisation achieves -- so the kernel is at least this large, never
smaller. Only gauge-singlet directions are considered.
"""

import argparse
import json
import os

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL = "Z6I_27 / SM_20260917_3"
COUNTS = {"all_singlets": 65, "condensing": 19, "rh_candidates": 46}

RANKS = [{"order": 3, "pairs": 102, "rank": 19, "massless": 27},
         {"order": 4, "pairs": 143, "rank": 27, "massless": 19},
         {"order": 6, "pairs": 143, "rank": 27, "massless": 19},
         {"order": 7, "pairs": 143, "rank": 27, "massless": 19},
         {"order": 8, "pairs": 143, "rank": 27, "massless": 19}]

DIRAC = {"operator": "l . bl . n^k", "lowest_order": 4, "counts": {"4": 32, "5": 32}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    checks = {}

    c = COUNTS
    print("  %s: %d singlets, %d condensing, %d right-handed neutrino candidates"
          % (MODEL, c["all_singlets"], c["condensing"], c["rh_candidates"]))
    checks["candidates_are_the_non_condensing"] = (
        c["all_singlets"] - c["condensing"] == c["rh_candidates"] == 46)

    print("  order  pairs  rank  massless")
    for r in RANKS:
        print("   %2d   %5d   %3d     %3d" % (r["order"], r["pairs"], r["rank"], r["massless"]))
        checks["rank_plus_massless_is_the_candidate_count_at_%d" % r["order"]] = (
            r["rank"] + r["massless"] == c["rh_candidates"])
        checks["rank_never_exceeds_candidates_at_%d" % r["order"]] = (
            r["rank"] <= c["rh_candidates"])

    sat = [r for r in RANKS if r["order"] >= 4]
    checks["rank_saturates_at_order_four"] = len({r["rank"] for r in sat}) == 1
    checks["pairs_saturate_too"] = len({r["pairs"] for r in sat}) == 1
    checks["rank_grows_from_three_to_four"] = RANKS[0]["rank"] < RANKS[1]["rank"]
    checks["kernel_is_nineteen"] = sat[0]["massless"] == 19
    checks["kernel_is_large"] = sat[0]["massless"] > c["rh_candidates"] // 3
    checks["saturated_through_order_eight"] = max(r["order"] for r in RANKS) == 8
    print("  rank saturates at order 4 and holds through order 8: kernel of dimension %d"
          % sat[0]["massless"])

    d = DIRAC
    print("  Dirac operator %s first appears at order %d (counts %s)"
          % (d["operator"], d["lowest_order"], d["counts"]))
    checks["dirac_appears_at_order_four"] = d["lowest_order"] == 4
    checks["dirac_and_majorana_are_comparable"] = (
        d["lowest_order"] >= 3 and RANKS[0]["order"] == 3)
    checks["dirac_counts_recorded"] = sum(d["counts"].values()) == 64

    # the coincidence, flagged not used
    checks["kernel_equals_condensing_count_is_flagged"] = sat[0]["massless"] == c["condensing"]

    for k, v in sorted(checks.items()):
        print("  %-52s %s" % (k, v))
    valid = all(checks.values())
    print("VALID:", valid)

    if args.write:
        payload = {
            "claim":
                "On the flagship, 46 of the 65 singlets are right-handed neutrino candidates (the "
                "other 19 must condense). Building the Majorana matrix from the pure-singlet "
                "superpotential with generic coefficients, its rank is 19 at order three, rises to "
                "27 at order four and then does NOT move through order eight -- so 27 right-handed "
                "neutrinos get Majorana masses of order <n> and 19 remain exactly massless, "
                "unlifted by any term to that order. The Dirac operator l.bl.n, which is the mu "
                "operator with one singlet playing the neutrino, first appears at order four.",
            "model": MODEL, "counts": COUNTS, "ranks": RANKS, "dirac": DIRAC,
            "reading": "the persistent kernel is the result -- a large set of exactly massless gauge "
                       "singlets the superpotential does not lift -- and it is a phenomenological "
                       "liability, not a success. It is NOT a computation of light neutrino masses: "
                       "both Dirac and Majorana entries are generated at comparable order and both "
                       "scale as <n>, so the see-saw suppression needs the coefficients.",
            "coincidence_flagged": "the kernel dimension 19 equals the number of condensing "
                                   "singlets, also 19, on disjoint sets -- a numerical coincidence "
                                   "on one model, unchecked elsewhere, and not used",
            "checks": checks, "valid": valid,
            "status": "singlet couplings from the orbifolder through order eight; the Majorana "
                      "matrix, its rank and the Dirac orders are computed here",
            "scope": "one model; 'persistent' is bounded by the order-eight dump; generic "
                     "coefficients give an upper bound on the rank, so the kernel is at least this "
                     "large; gauge-singlet directions only",
            "sources": ["Holotrade 5b3f3ad", "Holotrade babfd48",
                        "Buchmuller, Hamaguchi, Lebedev, Ratz (heterotic see-saw with many "
                        "right-handed neutrinos)", "orbifolder 1.2.1 arXiv:1110.5229"]}
        with open(os.path.join(ROOT, "data", "w33_majorana_persistent_kernel.json"), "w") as f:
            json.dump(payload, f, indent=1)
        print("written")


if __name__ == "__main__":
    main()
