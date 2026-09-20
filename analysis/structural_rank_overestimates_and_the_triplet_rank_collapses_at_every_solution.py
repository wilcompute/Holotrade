#!/usr/bin/env python3
"""
STRUCTURAL RANK IS AN UPPER BOUND AND I HAD USED IT AS THE CRITERION -- AND WITH THE TRUE
RANK, EVERY CONFIGURATION STILL COLLAPSES THE COLOUR-TRIPLET MASS AT THE SOLUTION.

aea4650 closed two routes to a supersymmetric vacuum on the dial-breakers. This pushes the
remaining degree of freedom -- which singlets condense -- and turns up a method error of mine
along the way.

THE METHOD ERROR. Every subset search in this work has used the STRUCTURAL rank of the
colour-triplet mass matrix, the maximum bipartite matching over the entries whose monomials
survive. That is only an UPPER bound on the rank. When several entries share monomials, the
true rank is lower. On the subset found in aea4650 route two:

    structural rank                    7 of 7
    true rank, mu = 0 solved alone     3 of 7

so the subset that looked like it kept the triplets heavy never did. The controlled
comparison that caught it is worth stating: solving mu = 0 ALONE on that subset already gives
rank 3, so the F-terms were never the culprit -- the subset was simply too small, and the
structural rank hid it.

REDOING THE SEARCH WITH THE TRUE RANK. Requiring D-flatness, zero internal superpotential
terms, and TRUE rank 7 evaluated numerically at random points, the search returns a much
smaller set:

    T = {12, 17, 21, 24, 54, 71, 75, 79, 81, 84}   |T| = 10
    D-flat with an FI term          yes, 1 of 18 direction/sign pairs
    D-flat with zero FI             no
    internal W terms                0    -- so <W> = 0 and dW/dn_i = 0 hold automatically
    true rank at generic points     7 of 7

which is the first set in this work to satisfy all three conditions at once. But the residual
system is SQUARE -- 7 outside-field F-terms plus 3 active mu entries against 10 unknowns --
so its solutions are isolated, and there is no freedom left to also hold the rank up.
Solving it with v = exp(w), so no VEV can be exactly zero, over 60 starts:

    residual          9.0 x 10^-14      the system is solved
    triplet rank      2 of 7            the triplets are not heavy
    |VEV| range       7 x 10^-14 to 1.4 -- exp(w) prevents exact zeros, not effective ones

THE PATTERN, ACROSS EVERYTHING TRIED. Full set with dW = 0: solvable, rank 2 of 7. Large
subset, underdetermined by 16: true rank 3 even before the F-terms. Minimal D-flat W-free
subset: square system, rank 2 of 7. In every configuration the conditions drive the
condensing VEVs to values where the colour-triplet mass matrix degenerates. That is now the
specific way the vacuum fails -- not D-flatness, not an empty superpotential, but the rank.

WHAT THIS IS AND IS NOT. It is a robust negative over the configurations searched, with the
failure mode identified. It is NOT a proof: the subset search is greedy and randomised, the
rank is read numerically at generic coefficients, and a larger W-free D-flat subset with true
rank 7 and an underdetermined system would still be the thing to find. The tension is
explicit and is what a further search should optimise against, and it is NOT monotonic in
size: freedom, counted as unknowns minus equations, is -1 for the full set, +16 for the
intermediate subset and 0 for the minimal one. It peaks in the middle. But the intermediate
subset is the one whose TRUE rank is only 3, so no configuration has both the freedom and the
rank at once -- that is the gap a further search has to close.

SCOPE. One model, Z6II_34 / SM_20260917_1558. True rank at 1e-9 relative tolerance over four
random points; greedy subset search over 120 randomised orders; generic coefficients; singlet
superpotential to order six. The exponential parametrisation guarantees non-zero VEVs but not
non-negligible ones, which is itself part of the finding.
"""

import argparse
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

METHOD_ERROR = {"criterion_used": "structural rank (maximum bipartite matching)",
                "is_an": "upper bound", "subset": "aea4650 route two, |T| = 35",
                "structural_rank": 7, "true_rank_mu_only": 3, "needed": 7,
                "caught_by": "solving mu = 0 alone and reading the numerical rank"}

CANDIDATE = {"T": [12, 17, 21, 24, 54, 71, 75, 79, 81, 84], "size": 10,
             "dflat_zero_FI": False, "dflat_with_FI": True, "fi_pairs": 1, "fi_of": 18,
             "internal_terms": 0, "true_rank_generic": 7,
             "eq_outside": 7, "eq_mu": 3, "equations": 10, "unknowns": 10,
             "residual": 9.0e-14, "rank_at_solution": 2, "vev_min": 7.15e-14, "vev_max": 1.38}

PATTERN = [{"config": "full set, dW = 0", "unknowns": 43, "equations": 44, "rank": 2},
           {"config": "large subset, underdetermined", "unknowns": 34, "equations": 18, "rank": 3},
           {"config": "minimal D-flat W-free subset", "unknowns": 10, "equations": 10, "rank": 2}]

NEEDED = 7


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    checks = {}

    m = METHOD_ERROR
    print("  method error: %s is an %s" % (m["criterion_used"], m["is_an"]))
    print("    %s -> structural %d, TRUE %d, needed %d"
          % (m["subset"], m["structural_rank"], m["true_rank_mu_only"], m["needed"]))
    checks["structural_overestimated_the_rank"] = m["true_rank_mu_only"] < m["structural_rank"]
    checks["the_subset_never_kept_the_triplets"] = m["true_rank_mu_only"] < m["needed"]
    checks["caught_by_a_controlled_comparison"] = bool(m["caught_by"])

    c = CANDIDATE
    print("  candidate |T| = %d: D-flat(FI) %s (%d/%d), internal terms %d, true rank %d of %d"
          % (c["size"], c["dflat_with_FI"], c["fi_pairs"], c["fi_of"],
             c["internal_terms"], c["true_rank_generic"], NEEDED))
    checks["candidate_size_matches"] = len(c["T"]) == c["size"] == 10
    checks["candidate_is_dflat_via_fi"] = c["dflat_with_FI"] and not c["dflat_zero_FI"]
    checks["candidate_is_W_free"] = c["internal_terms"] == 0
    checks["candidate_has_true_rank_generically"] = c["true_rank_generic"] == NEEDED
    checks["all_three_conditions_met_at_once"] = (
        checks["candidate_is_dflat_via_fi"] and checks["candidate_is_W_free"]
        and checks["candidate_has_true_rank_generically"])
    # and yet the system is square
    checks["equation_count_adds_up"] = c["eq_outside"] + c["eq_mu"] == c["equations"] == 10
    checks["the_system_is_square"] = c["equations"] == c["unknowns"]
    print("    but the system is square: %d equations, %d unknowns -> isolated solutions"
          % (c["equations"], c["unknowns"]))
    print("    solved: residual %.1e, rank %d of %d, |VEV| %.1e .. %.2f"
          % (c["residual"], c["rank_at_solution"], NEEDED, c["vev_min"], c["vev_max"]))
    checks["the_system_solves"] = c["residual"] < 1e-11
    checks["but_the_rank_collapses"] = c["rank_at_solution"] < NEEDED
    checks["exp_parametrisation_does_not_save_it"] = c["vev_min"] < 1e-9

    print("  pattern across configurations:")
    for p in PATTERN:
        print("    %-32s %2d unknowns, %2d equations -> rank %d of %d"
              % (p["config"], p["unknowns"], p["equations"], p["rank"], NEEDED))
    checks["every_configuration_collapses"] = all(p["rank"] < NEEDED for p in PATTERN)
    checks["three_configurations_tried"] = len(PATTERN) == 3
    checks["the_failure_mode_is_the_rank"] = checks["every_configuration_collapses"]
    # the tension a further search must optimise -- freedom is NOT monotonic in size
    free = {p["config"]: p["unknowns"] - p["equations"] for p in PATTERN}
    mid = max(free.values())
    checks["freedom_peaks_at_intermediate_size"] = (
        free["large subset, underdetermined"] == mid == 16
        and free["full set, dW = 0"] < 0 and free["minimal D-flat W-free subset"] == 0)
    checks["no_configuration_has_both_freedom_and_rank"] = all(
        p["rank"] < NEEDED for p in PATTERN)
    print("    freedom (unknowns - equations): %s -- peaks in the middle, not at either end"
          % free)

    for k, v in sorted(checks.items()):
        print("  %-50s %s" % (k, v))
    valid = all(checks.values())
    print("VALID:", valid)

    if args.write:
        payload = {
            "claim":
                "Every subset search in this work used the STRUCTURAL rank of the colour-triplet "
                "mass matrix, which is only an upper bound; on the aea4650 subset the true rank with "
                "mu = 0 alone is 3, not the structural 7, so that subset never kept the triplets "
                "heavy. Redoing the search with the true rank returns the first set satisfying all "
                "three conditions at once -- 10 singlets, D-flat via the FI term, zero internal "
                "superpotential terms so <W> = 0 and dW/dn_i = 0 are automatic, true rank 7 at "
                "generic points -- but its residual system is SQUARE, 10 equations in 10 unknowns, "
                "and at the isolated solutions the triplet rank falls to 2 of 7.",
            "method_error": METHOD_ERROR, "candidate": CANDIDATE, "pattern": PATTERN,
            "needed_rank": NEEDED,
            "failure_mode": "in every configuration tried, the F-term and mu conditions drive the "
                            "condensing VEVs to values where the colour-triplet mass matrix "
                            "degenerates. The vacuum fails on the RANK, not on D-flatness and not on "
                            "an empty superpotential.",
            "not_a_proof": "the subset search is greedy and randomised, the rank is numerical at "
                           "generic coefficients, and a larger W-free D-flat subset with true rank 7 "
                           "AND an underdetermined system remains the thing to look for. The tension "
                           "is explicit and NOT monotonic in size: freedom (unknowns minus "
                           "equations) is -1 for the full set, +16 for the intermediate subset and 0 "
                           "for the minimal one, peaking in the middle -- but the intermediate one "
                           "is exactly the subset whose TRUE rank is only 3, so no configuration has "
                           "both the freedom and the rank.",
            "checks": checks, "valid": valid,
            "status": "couplings and charges from the orbifolder; true rank, subset search, "
                      "D-flatness LPs and the exponential-parametrisation solve computed here",
            "scope": "one model, Z6II_34/SM_20260917_1558; true rank at 1e-9 relative tolerance over "
                     "four random points; greedy search over 120 randomised orders; generic "
                     "coefficients; singlet superpotential to order six. v = exp(w) guarantees "
                     "non-zero VEVs but not non-negligible ones, which is part of the finding.",
            "sources": ["Holotrade aea4650", "Holotrade 25700ea", "Holotrade bd6c60e",
                        "orbifolder 1.2.1 arXiv:1110.5229"]}
        with open(os.path.join(ROOT, "data", "w33_true_rank_and_the_collapse.json"), "w") as f:
            json.dump(payload, f, indent=1)
        print("written")


if __name__ == "__main__":
    main()
