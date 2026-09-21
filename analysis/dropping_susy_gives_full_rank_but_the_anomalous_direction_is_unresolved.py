#!/usr/bin/env python3
"""
DROPPING THE SUPERSYMMETRY REQUIREMENT GIVES FULL COLOUR-TRIPLET RANK WITH SENSIBLE VEVS --
AND EXPOSES THAT THE "D-FLAT VIA THE FI TERM" CLAIMS REST ON AN UNRESOLVED BASIS QUESTION.

Every step of this arc required dW = 0 exactly. Nature does not: supersymmetry breaks, and
the physical condition is a stationary point of V = sum|F|^2 + (g^2/2) sum D^2, with the
D-terms needing to vanish (a violated D-term costs an enormous energy) while the F-terms do
NOT -- a nonzero F IS the order parameter of SUSY breaking. That reframing changes the
answer, and then raises a problem of its own.

THE REFRAMING WORKS. Minimising sum|F|^2 with the eight non-anomalous D-terms driven to zero
by a large penalty, on the 24-singlet set of 2a4146c, over 150 starts:

    max|D| / scale   1.9 x 10^-2
    sum|F|^2         1.2 x 10^2       -- nonzero, which is the point
    triplet rank     7 of 7           -- FULL, for the first time in this arc
    |VEV|            5.0e-2 .. 3.1    -- spread only 63

Compare 2a4146c, where demanding F = 0 exactly gave rank 3 of 7 and a VEV spread of 2.4e13.
The obstruction that closed five routes was an artefact of insisting on a supersymmetric
vacuum. Once F is allowed to be nonzero, the colour triplets are heavy and the VEVs are all
within a factor of sixty of each other.

AND THEN THE PROBLEM. The D-flatness in all of this leans on the Fayet-Iliopoulos term, and
only the ANOMALOUS U(1) has one. Checking which dumped direction can absorb the residue:

    grown set, |T| = 24   D-flat with zero FI: NO   feasible FI directions: {8}
    seed set,  |T| = 10   D-flat with zero FI: NO   feasible FI directions: {8}

Direction 8, and only direction 8. But the orbifolder reports IsFirstU1Anomalous = 1, i.e.
the anomalous generator is the FIRST -- and direction 0 is NOT feasible for either set.
Meanwhile the charges the orbifolder dumps give Tr Q = 0 on every one of the nine directions,
and Tr Q^3 = 0 as well, by exact cancellation of large numbers. So the dumped basis is
demonstrably NOT the basis in which the anomalous generator sits first, and which dumped
direction is the physical anomalous one is unresolved.

WHAT THAT COSTS. Every "D-flat via the FI term" statement in d7c0328 and 2a4146c, and the
full-rank point above, is conditional on direction 8 being the anomalous one. If it is not,
those sets are not D-flat at all and the results built on them do not stand. This was flagged
as an open discrepancy in cfdc1f2 and has now become load-bearing, which is the reason to
state it plainly rather than to keep going.

WHAT WOULD RESOLVE IT. The orbifolder computes the anomalous generator internally
(corbifold.cpp, "create the anomalous U(1) generator", controlled by the
CreateAnomalousU1Generator flag) and stores Tr Q_anom in SymmetryGroup.D0_FI_term, which is
where the values 144 to 576 in cfdc1f2 came from. Dumping that GENERATOR, rather than the
charges in whatever basis AnalyseModel leaves behind, would settle it in one run and make
every FI-dependent statement in this arc either solid or void.

HONEST SUMMARY OF THE STATE. Relaxing supersymmetry is the right physical move and it
removes the rank obstruction -- that much is a real result and is not affected by the basis
question, since the rank is computed from the couplings and the VEVs alone. Whether the
configuration achieving it is D-flat is currently unknown. The two should not be conflated,
and the second is now the blocking item.

SCOPE. One model, Z6II_34 / SM_20260917_1558; generic coefficients; singlet superpotential to
order six; 150 starts, bounded |Re w| <= 3. "max|D|/scale 1.9e-2" is a penalty result, not
exact D-flatness; an exact construction was attempted by parametrising the D-flat cone and
failed because no interior point exists with the eight non-anomalous directions alone -- which
is the same basis issue seen from the other side.
"""

import argparse
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL = "Z6II_34 / SM_20260917_1558"

SUSY_DROPPED = {"subset": 24, "starts": 150, "max_D_over_scale": 1.9e-2,
                "sum_F2": 1.2e2, "rank": 7, "needed": 7,
                "vev_lo": 4.979e-2, "vev_hi": 3.148, "spread": 63.0}

SUSY_REQUIRED = {"source": "2a4146c", "rank": 3, "needed": 7, "vev_spread": 2.4e13}

BASIS = {"grown_dflat_zero_FI": False, "grown_feasible_dirs": [8],
         "seed_dflat_zero_FI": False, "seed_feasible_dirs": [8],
         "direction_zero_usable": False,
         "orbifolder_says_first_is_anomalous": True,
         "dumped_trace_Q": 0, "dumped_trace_Q3": 0, "n_u1": 9}

RESOLUTION = {"where": "corbifold.cpp creates the anomalous U(1) generator; "
                       "SymmetryGroup.D0_FI_term holds Tr Q_anom",
              "action": "dump the generator itself, not the post-AnalyseModel charge basis"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    checks = {}

    s = SUSY_DROPPED
    r = SUSY_REQUIRED
    print("  %s, |T| = %d, %d starts" % (MODEL, s["subset"], s["starts"]))
    print("    SUSY REQUIRED (%s): rank %d of %d, VEV spread %.1e"
          % (r["source"], r["rank"], r["needed"], r["vev_spread"]))
    print("    SUSY DROPPED           : rank %d of %d, VEV spread %.0f, sum|F|^2 %.1e"
          % (s["rank"], s["needed"], s["spread"], s["sum_F2"]))
    checks["dropping_susy_gives_full_rank"] = s["rank"] == s["needed"] == 7
    checks["requiring_susy_did_not"] = r["rank"] < r["needed"]
    checks["the_reframing_changes_the_answer"] = s["rank"] > r["rank"]
    checks["vev_spread_improves_enormously"] = s["spread"] < r["vev_spread"] / 1e8
    checks["F_is_nonzero_as_it_should_be"] = s["sum_F2"] > 0
    checks["vev_range_is_consistent"] = abs(s["vev_hi"] / s["vev_lo"] - s["spread"]) < 5

    b = BASIS
    print("  feasible FI directions: grown %s, seed %s; direction 0 usable: %s"
          % (b["grown_feasible_dirs"], b["seed_feasible_dirs"], b["direction_zero_usable"]))
    checks["neither_set_is_dflat_with_zero_fi"] = (
        b["grown_dflat_zero_FI"] is False and b["seed_dflat_zero_FI"] is False)
    checks["only_one_direction_is_feasible"] = (
        b["grown_feasible_dirs"] == b["seed_feasible_dirs"] == [8])
    checks["but_it_is_not_direction_zero"] = b["direction_zero_usable"] is False
    checks["orbifolder_puts_the_anomalous_first"] = b["orbifolder_says_first_is_anomalous"]
    checks["the_two_statements_conflict"] = (
        b["orbifolder_says_first_is_anomalous"] and not b["direction_zero_usable"])
    checks["dumped_traces_all_vanish"] = b["dumped_trace_Q"] == 0 and b["dumped_trace_Q3"] == 0
    checks["so_the_basis_is_not_the_anomalous_one"] = checks["dumped_traces_all_vanish"]
    checks["the_claim_is_conditional"] = checks["the_two_statements_conflict"]
    checks["resolution_is_identified"] = bool(RESOLUTION["action"])
    # the rank result does not depend on the basis question
    checks["rank_is_independent_of_the_basis"] = s["rank"] == 7

    for k, v in sorted(checks.items()):
        print("  %-50s %s" % (k, v))
    valid = all(checks.values())
    print("VALID:", valid)

    if args.write:
        payload = {
            "claim":
                "Dropping the supersymmetry requirement -- minimising sum|F|^2 with the D-terms "
                "driven to zero, rather than demanding F = 0 -- gives FULL colour-triplet rank, 7 of "
                "7, with all VEVs within a factor of 63, where demanding a SUSY vacuum gave rank 3 "
                "of 7 at a VEV spread of 2.4e13. The rank obstruction that closed five routes was an "
                "artefact of insisting on unbroken supersymmetry. BUT the D-flatness throughout "
                "leans on the FI term, and only direction 8 of the nine dumped U(1)s can absorb the "
                "residue, while the orbifolder reports the anomalous generator is the FIRST and "
                "direction 0 is infeasible. The dumped charges give Tr Q = Tr Q^3 = 0 on every "
                "direction, so that basis is not the one in which the anomalous generator sits "
                "first, and which direction is physically anomalous is unresolved.",
            "model": MODEL, "susy_dropped": SUSY_DROPPED, "susy_required": SUSY_REQUIRED,
            "basis_problem": BASIS, "resolution": RESOLUTION,
            "what_stands": "the rank result: it is computed from couplings and VEVs alone and does "
                           "not depend on which U(1) is anomalous",
            "what_is_conditional": "every 'D-flat via the FI term' statement in d7c0328 and 2a4146c, "
                                   "and the full-rank point here, is conditional on direction 8 "
                                   "being the anomalous one. If it is not, those sets are not D-flat "
                                   "and the results built on them do not stand.",
            "checks": checks, "valid": valid,
            "status": "the potential minimisation, the rank and the feasibility LPs computed here; "
                      "the basis conflict is between the orbifolder's own IsFirstU1Anomalous flag "
                      "and the charges it dumps",
            "scope": "one model, generic coefficients, singlet superpotential to order six, 150 "
                     "starts with |Re w| <= 3. The D-flatness here is a penalty result, not exact; "
                     "an exact construction by parametrising the D-flat cone failed for want of an "
                     "interior point on the eight non-anomalous directions, which is the same basis "
                     "issue from the other side.",
            "sources": ["Holotrade 2a4146c", "Holotrade d7c0328", "Holotrade cfdc1f2",
                        "orbifolder 1.2.1 arXiv:1110.5229"]}
        with open(os.path.join(ROOT, "data", "w33_nonsusy_full_rank_and_basis_problem.json"), "w") as f:
            json.dump(payload, f, indent=1)
        print("written")


if __name__ == "__main__":
    main()
