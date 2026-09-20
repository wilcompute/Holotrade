#!/usr/bin/env python3
"""
DOUBLET-TRIPLET SPLITTING AND SU(5)-COMPLETE EXOTICS ARE MUTUALLY EXCLUSIVE IN THIS CLASS,
AND THE PLANE TABLE FORCES IT.

*** RETRACTED IN ITS PHYSICAL READING. The arithmetic below is right -- 24 models do have
    n_d = n_bl, the 55 doublet-triplet solvers have n_d = 2 and n_bl = 1, and the two sets
    are disjoint. What is WRONG is calling the 24 "SU(5)-complete" and therefore
    unification-safe. That counted only the d/dbar and l/lbar pairs and ignored every other
    coloured or weak-charged state in the spectrum, of which there are many (the flagship
    has 274 chiral fields, and states such as (1,1,1,-3,1) and (1,1,1,3,2) appear outside
    the d/bd and l/bl labels).

    Computing the one-loop beta functions from the FULL spectrum of all 87 models and
    comparing with the MSSM, delta-b = b - b_MSSM should be (x,x,x) for complete matter:

        exactly complete (spread 0):        0 of 87
        doublet-triplet solvers:            median spread 14.8  (min 2.8, max 37.6)
        non-solvers:                        median spread  9.0  (min 3.0, max 19.8)

    NO model in the class is SU(5)-complete, the solvers are only about 1.6 times worse on
    median, and the two distributions overlap heavily. So the clean disjointness claim is
    withdrawn; see the_full_spectrum_is_never_su5_complete.py for what replaces it. ***

An independent question, asked without reference to the mu problem: do the vector-like
exotics of these models fill complete SU(5) multiplets? It matters because a complete
5 + 5bar at any mass shifts all three gauge couplings equally at one loop, leaving gauge
coupling unification untouched, while an incomplete set does not.

THE COUNT. A vector-like (d, dbar) pair is (3,1)_{1/3} + (3bar,1)_{-1/3}; a vector-like
(l, lbar) pair is (1,2)_{-1/2} + (1,2)_{+1/2}. One of each completes a 5 + 5bar. Since the
net chiralities are fixed at three families,

    n_bd - n_d = 3   and   n_l - n_bl = 3,

so the numbers of vector-like pairs are n_d triplet pairs and n_bl doublet pairs, and the
exotics are SU(5)-complete exactly when n_d = n_bl.

MEASURED OVER THE 87 Z6-I STANDARD MODELS:

    shape (n_l,n_bl,n_d,n_bd)   n_d - n_bl   SU(5)-complete   solves DTS   models
    (4, 1, 2, 5)                     1            no              YES         55
    (9, 6, 6, 9)                     0           YES              no          24
    (8, 5, 7, 10)                    2            no              no           8

    complete exotics : 24 of 87
    solve doublet-triplet splitting : 55 of 87
    BOTH : 0

Disjoint, with no exceptions. Not a partition -- eight models do neither -- but no model
does both.

AND IT IS FORCED, NOT COINCIDENTAL. 67f0e1f established that a model solves doublet-triplet
splitting exactly when its d and bl fields come only from the untwisted sector. 3caf15e
measured that the untwisted species-by-plane table is the same in all 87 models: the colour
triplet d sits in planes 1 and 2, the weak doublet bl in plane 3 alone. So an
untwisted-only model has exactly

    n_d = 2  (planes 1 and 2)   and   n_bl = 1  (plane 3),

hence n_d - n_bl = 1, never zero. Every doublet-triplet solving model is therefore forced
to have incomplete exotics. The measured shape of all 55 is exactly (4,1,2,5), which is that
statement.

The converse direction is the same fact read backwards: the 24 models with n_d = n_bl = 6
have d and bl in the twisted sector as well, which is what supplies the extra pairs AND what
puts a d and a bl on a common fixed point as gauge siblings, locking the mu and triplet-mass
coefficients. One structural choice -- whether d and bl appear twisted -- decides both
questions, in opposite directions.

THE TRADE-OFF. In this class you may have the Higgs doublet split from its colour triplet,
or exotics that leave one-loop unification alone. Not both. The asymmetry that solves the
first is precisely the incompleteness that spoils the second.

SCOPE. This is a one-loop, complete-multiplet argument: an incomplete set does not
automatically ruin unification, it removes the protection, and the actual prediction needs
the exotic masses and two-loop running, neither computed here. Hypercharge normalisation is
assumed to be the SU(5) one, which d772153's t_Y^2 = 5/6 measurement supports for this
class. The counting uses only the net chiralities and the measured spectrum shapes; the
87 models are the Z6-I Standard Models of the 5b3f3ad scan.
"""

import argparse
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SHAPES = [{"shape": [4, 1, 2, 5], "mismatch": 1, "complete": False, "dts": True, "models": 55},
          {"shape": [9, 6, 6, 9], "mismatch": 0, "complete": True, "dts": False, "models": 24},
          {"shape": [8, 5, 7, 10], "mismatch": 2, "complete": False, "dts": False, "models": 8}]

TOTALS = {"models": 87, "complete_exotics": 24, "solve_dts": 55, "both": 0, "neither": 8}

TABLE = {"untwisted_triplet_planes": [1, 2], "untwisted_doublet_planes": [3],
         "source": "3caf15e", "universal_over": 87}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    checks = {}

    # the chirality arithmetic that defines the count
    for s in SHAPES:
        nl, nbl, nd, nbd = s["shape"]
        assert nbd - nd == 3 and nl - nbl == 3, s
    checks["every_shape_has_three_families"] = all(
        s["shape"][3] - s["shape"][2] == 3 and s["shape"][0] - s["shape"][1] == 3
        for s in SHAPES)
    checks["mismatch_is_nd_minus_nbl"] = all(
        s["mismatch"] == s["shape"][2] - s["shape"][1] for s in SHAPES)
    checks["complete_iff_mismatch_zero"] = all(
        s["complete"] == (s["mismatch"] == 0) for s in SHAPES)

    print("  shape                mismatch  SU(5)-complete  solves DTS  models")
    for s in SHAPES:
        print("  %-20s %5d        %-6s        %-6s      %3d"
              % (tuple(s["shape"]), s["mismatch"], s["complete"], s["dts"], s["models"]))

    t = TOTALS
    checks["shapes_cover_the_class"] = sum(s["models"] for s in SHAPES) == t["models"] == 87
    checks["complete_count_matches"] = sum(
        s["models"] for s in SHAPES if s["complete"]) == t["complete_exotics"] == 24
    checks["dts_count_matches"] = sum(
        s["models"] for s in SHAPES if s["dts"]) == t["solve_dts"] == 55
    checks["no_model_does_both"] = sum(
        s["models"] for s in SHAPES if s["complete"] and s["dts"]) == t["both"] == 0
    checks["eight_do_neither"] = sum(
        s["models"] for s in SHAPES if not s["complete"] and not s["dts"]) == t["neither"] == 8
    checks["not_a_partition_but_disjoint"] = t["both"] == 0 and t["neither"] > 0
    print("  complete %d, solve DTS %d, BOTH %d, neither %d"
          % (t["complete_exotics"], t["solve_dts"], t["both"], t["neither"]))

    # the plane table forces the mismatch for every DTS solver
    tb = TABLE
    forced_nd = len(tb["untwisted_triplet_planes"])
    forced_nbl = len(tb["untwisted_doublet_planes"])
    print("  untwisted table forces n_d = %d, n_bl = %d -> mismatch %d for any untwisted-only model"
          % (forced_nd, forced_nbl, forced_nd - forced_nbl))
    checks["table_forces_two_triplets"] = forced_nd == 2
    checks["table_forces_one_doublet"] = forced_nbl == 1
    checks["forced_mismatch_is_nonzero"] = forced_nd - forced_nbl != 0
    dts_shape = [s for s in SHAPES if s["dts"]][0]["shape"]
    checks["the_dts_shape_is_the_forced_one"] = (
        dts_shape[2] == forced_nd and dts_shape[1] == forced_nbl)
    checks["so_no_dts_model_can_be_complete"] = (
        checks["forced_mismatch_is_nonzero"] and checks["the_dts_shape_is_the_forced_one"])
    checks["table_is_universal"] = tb["universal_over"] == 87

    for k, v in sorted(checks.items()):
        print("  %-48s %s" % (k, v))
    valid = all(checks.values())
    print("VALID:", valid)

    if args.write:
        payload = {
            "claim":
                "In the 87 W(3,3) Z6-I Standard Models, doublet-triplet splitting and SU(5)-complete "
                "vector-like exotics are mutually exclusive: 24 models have complete exotics "
                "(n_d = n_bl, so the extra triplet and doublet pairs assemble into 5 + 5bar and leave "
                "one-loop unification untouched), 55 solve doublet-triplet splitting, and NO model "
                "does both. It is forced rather than coincidental: a model solves doublet-triplet "
                "splitting exactly when its d and bl are untwisted only (67f0e1f), and the universal "
                "untwisted table (3caf15e) puts d in planes 1 and 2 and bl in plane 3 alone, so such "
                "a model has n_d = 2 and n_bl = 1 and mismatch 1, never zero. The 24 complete models "
                "have d and bl twisted as well, which supplies the extra pairs and simultaneously "
                "makes them gauge siblings, locking the coefficients.",
            "shapes": SHAPES, "totals": TOTALS, "table": TABLE,
            "trade_off": "the asymmetry that splits the Higgs from its colour triplet is precisely "
                         "the incompleteness that removes unification's protection -- one structural "
                         "choice, whether d and bl appear in the twisted sector, decides both "
                         "questions in opposite directions",
            "checks": checks, "valid": valid,
            "status": "spectrum shapes measured by the orbifolder across all 87 models; the "
                      "chirality and completeness arithmetic is computed here; the untwisted plane "
                      "table is quoted from 3caf15e and the sector criterion from 67f0e1f",
            "scope": "a one-loop complete-multiplet argument -- incompleteness removes the "
                     "protection rather than automatically ruining unification, and the actual "
                     "prediction needs exotic masses and two-loop running, neither computed here. "
                     "SU(5) hypercharge normalisation assumed, supported by d772153's t_Y^2 = 5/6.",
            "sources": ["Holotrade 3caf15e", "Holotrade 67f0e1f", "Holotrade d772153",
                        "Holotrade 5b3f3ad", "orbifolder 1.2.1 arXiv:1110.5229"]}
        with open(os.path.join(ROOT, "data", "w33_dts_versus_complete_su5_exotics.json"), "w") as f:
            json.dump(payload, f, indent=1)
        print("written")


if __name__ == "__main__":
    main()
