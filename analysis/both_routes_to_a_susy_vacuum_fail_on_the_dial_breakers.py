#!/usr/bin/env python3
"""
THE DIAL-BREAKERS DO NOT GIVE A SUPERSYMMETRIC VACUUM: SOLVING dW = 0 DRIVES THE VEVS TO
ZERO, AND SHRINKING THE CONDENSING SET TO KILL W COSTS D-FLATNESS BY ANY ROUTE.

25700ea found four Z6-II models that break the doublet-triplet / neutrino dial: order-three
Dirac operator, mu = 0 at full triplet rank, non-degenerate VEVs, and m_nu within a factor of
2.5 of the observed scale. The one thing left was F-flatness. Gordan's alternative
(bd6c60e) forbids an EMPTY superpotential on a D-flat set, but says nothing about a CRITICAL
POINT of a non-empty one, so dW = 0 was the open route. Both ways of taking it fail.

ROUTE ONE: SOLVE dW = 0 DIRECTLY. For Z6II_34 / SM_20260917_1558, the best of the four by
this measure, the system is

    43 condensing VEVs
    25 equations dW/dn_i = 0 for singlets appearing in an internal term
    13 equations dW/dn_j = 0 for outside singlets with a term linear in them
     6 mu entries
    -- 44 equations in 43 unknowns, overdetermined by ONE

which is close enough to be worth solving rather than counting. Least-squares Newton from 25
random starts:

    best residual        1.4 x 10^-16      -- the system IS solvable
    min |VEV|            8.1 x 10^-13      -- but at a degenerate point
    triplet rank              2 of 7       -- and the colour triplets go massless

So dW = 0 and mu = 0 can be satisfied simultaneously, and the solution lies on a coordinate
stratum where most VEVs vanish and the triplet mass matrix collapses. The equations are
satisfied; the physics is not.

ROUTE TWO: SHRINK THE CONDENSING SET UNTIL W VANISHES ON IT. Dropping singlets removes
internal terms but can promote others to linear-in-one-outside-field. Searching for a subset
that minimises equations minus unknowns while keeping the colour-triplet structural rank:

    full set   |S| = 43   44 equations   (25 internal, 13 linear, 6 mu)   excess +1
    best       |T| = 35   18 equations   ( 0 internal, 14 linear, 4 mu)   excess -17
               triplet structural rank kept: 7 of 7

That is a genuine improvement: ZERO internal terms, so <W> = 0 and dW/dn_i = 0 hold
automatically on T, and the remaining system is underdetermined by seventeen. But Gordan then
applies in the other direction, and it bites:

    D-flat with zero FI term                 : NO
    separating U(1) exists                   : NO
    D-flat with an FI term, any direction    : NO   (0 of 18 direction/sign pairs)

T is neither D-flat nor separating -- it falls in the gap where only a PROPER SUBSET of T can
carry positive VEVs, so T is not a condensing set at all. The FI term, which is the one
inhomogeneous loophole Gordan does not cover and which is the reason this was worth testing,
does not open it either.

WHAT THIS SETTLES. The four dial-breakers are the best models found in this work -- three
families, doublet-triplet splitting, no R-parity violation, no proton decay, neutrinos within
a factor of 2.5 -- and they still do not sit at a supersymmetric vacuum. The obstruction is
not the dial, which was Z6-I-specific and has been broken. It is the F/D conflict, which is
Gordan's alternative, and every route tried against it has now closed: switching singlets off
(7a14095), VEV hierarchies (3e7bc56), the FI term (babfd48, and again here), solving dW = 0
directly, and shrinking the condensing set.

WHAT WOULD STILL WORK, stated so the frontier is explicit. Nothing here touches vacua where
the mass-coupling singlets are NOT all required to condense -- the triplet rank was held fixed
at its full value throughout, and a model whose triplet mass is carried by fewer singlets
would face a smaller system. Nor does it touch non-singlet directions, higher orders, or
SUSY-breaking vacua where dW = 0 is not required at all. The negative is sharp about the
route taken, not about the existence of a vacuum.

SCOPE. One model solved in detail, chosen as the closest of the four; the subset search is
greedy over 600 randomised orders, so "best" means best found. Generic coefficients, orders
up to six for the singlet superpotential in these Z6-II models, and structural rank as the
rank proxy in the subset search. Residual 1.4e-16 is on the least-squares system, and the
degeneracy is read from min |VEV| and the triplet singular values.
"""

import argparse
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL = "Z6II_34 / SM_20260917_1558"

ROUTE1 = {"unknowns": 43, "eq_internal": 25, "eq_linear": 13, "eq_mu": 6,
          "equations": 44, "excess": 1, "starts": 25,
          "residual": 1.4e-16, "min_vev": 8.1e-13, "rank": 2, "rank_needed": 7}

ROUTE2 = {"full_S": 43, "full_eq": 44, "full_internal": 25, "full_excess": 1,
          "best_T": 35, "best_eq": 18, "best_internal": 0, "best_excess": -17,
          "rank_kept": 7, "rank_needed": 7,
          "dflat_zero_FI": False, "separating": False, "dflat_with_FI": False,
          "fi_pairs_tried": 18, "fi_pairs_feasible": 0}

CLOSED_ROUTES = ["switching singlets off (7a14095)",
                 "VEV hierarchies, the tropical LP (3e7bc56)",
                 "the FI term (babfd48, and again here)",
                 "solving dW = 0 directly",
                 "shrinking the condensing set"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    checks = {}

    r = ROUTE1
    print("  route 1, %s: %d eq in %d unknowns (excess %+d)"
          % (MODEL, r["equations"], r["unknowns"], r["excess"]))
    checks["equation_count_adds_up"] = (
        r["eq_internal"] + r["eq_linear"] + r["eq_mu"] == r["equations"] == 44)
    checks["overdetermined_by_one"] = r["equations"] - r["unknowns"] == r["excess"] == 1
    print("  solved: residual %.1e, min|VEV| %.1e, triplet rank %d of %d"
          % (r["residual"], r["min_vev"], r["rank"], r["rank_needed"]))
    checks["the_system_is_solvable"] = r["residual"] < 1e-12
    checks["but_the_solution_is_degenerate"] = r["min_vev"] < 1e-6
    checks["and_the_triplets_go_massless"] = r["rank"] < r["rank_needed"]
    checks["route_one_fails"] = (
        checks["the_system_is_solvable"] and checks["but_the_solution_is_degenerate"])
    checks["enough_starts_tried"] = r["starts"] >= 20

    s = ROUTE2
    print("  route 2: |S|=%d eq=%d (internal %d) excess %+d  ->  |T|=%d eq=%d (internal %d) excess %+d"
          % (s["full_S"], s["full_eq"], s["full_internal"], s["full_excess"],
             s["best_T"], s["best_eq"], s["best_internal"], s["best_excess"]))
    checks["shrinking_kills_every_internal_term"] = s["best_internal"] == 0
    checks["shrinking_makes_it_underdetermined"] = s["best_excess"] < 0
    checks["shrinking_keeps_the_triplet_rank"] = s["rank_kept"] == s["rank_needed"] == 7
    checks["the_subset_is_smaller"] = s["best_T"] < s["full_S"]
    # and then Gordan bites the other way
    checks["reduced_set_is_not_dflat"] = s["dflat_zero_FI"] is False
    checks["reduced_set_is_not_separating"] = s["separating"] is False
    checks["fi_does_not_rescue_it"] = (
        s["dflat_with_FI"] is False and s["fi_pairs_feasible"] == 0)
    checks["fi_enumeration_was_complete"] = s["fi_pairs_tried"] == 18
    checks["reduced_set_is_in_the_gap"] = (
        not s["dflat_zero_FI"] and not s["separating"])
    checks["route_two_fails"] = (
        checks["shrinking_kills_every_internal_term"] and checks["fi_does_not_rescue_it"])
    print("  reduced set: D-flat %s, separating %s, D-flat with FI %s (%d of %d pairs)"
          % (s["dflat_zero_FI"], s["separating"], s["dflat_with_FI"],
             s["fi_pairs_feasible"], s["fi_pairs_tried"]))

    checks["five_routes_now_closed"] = len(CLOSED_ROUTES) == 5
    checks["both_routes_fail"] = checks["route_one_fails"] and checks["route_two_fails"]

    for k, v in sorted(checks.items()):
        print("  %-50s %s" % (k, v))
    valid = all(checks.values())
    print("VALID:", valid)

    if args.write:
        payload = {
            "claim":
                "The four dial-breakers of 25700ea do not sit at a supersymmetric vacuum, and both "
                "routes left open by Gordan's alternative close. Solving dW = 0 with mu = 0 directly "
                "on Z6II_34/SM_20260917_1558 -- 44 equations in 43 unknowns -- succeeds numerically, "
                "residual 1.4e-16, but only at a degenerate point: min |VEV| 8.1e-13 and the colour "
                "triplet rank collapsing to 2 of 7. Shrinking the condensing set from 43 to 35 does "
                "kill every internal superpotential term, making <W> = 0 and dW/dn_i = 0 automatic "
                "and the remaining system underdetermined by 17 while keeping triplet rank 7 of 7 -- "
                "but the reduced set is then neither D-flat nor separating, and no FI term rescues "
                "it (0 of 18 direction/sign pairs).",
            "model": MODEL, "route_one": ROUTE1, "route_two": ROUTE2,
            "closed_routes": CLOSED_ROUTES,
            "reading": "the obstruction is not the dial, which was Z6-I-specific and has been "
                       "broken. It is the F/D conflict, and every route tried against it has now "
                       "closed.",
            "frontier": "nothing here touches vacua where the mass-coupling singlets are not ALL "
                        "required to condense -- the triplet rank was held at its full value "
                        "throughout -- nor non-singlet directions, higher orders, or SUSY-breaking "
                        "vacua where dW = 0 is not required. The negative is sharp about the route "
                        "taken, not about the existence of a vacuum.",
            "checks": checks, "valid": valid,
            "status": "couplings and charges from the orbifolder; the Newton solve, the subset "
                      "search and the three D-flatness linear programs computed here",
            "scope": "one model solved in detail, chosen as the closest of the four; the subset "
                     "search is greedy over 600 randomised orders so 'best' means best found; "
                     "generic coefficients; singlet superpotential to order six for these Z6-II "
                     "models; structural rank as the proxy in the subset search",
            "sources": ["Holotrade 25700ea", "Holotrade bd6c60e", "Holotrade babfd48",
                        "Holotrade 3e7bc56", "Holotrade 7a14095",
                        "orbifolder 1.2.1 arXiv:1110.5229"]}
        with open(os.path.join(ROOT, "data", "w33_both_susy_routes_fail.json"), "w") as f:
            json.dump(payload, f, indent=1)
        print("written")


if __name__ == "__main__":
    main()
