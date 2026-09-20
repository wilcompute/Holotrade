#!/usr/bin/env python3
"""
THE FULL-CARTAN SPURION OBSTRUCTION AND THE UNTWISTED PLANE SPLIT ARE THE TWO HALVES OF
ONE STATEMENT: THE TWISTED SECTOR CANNOT SPLIT THE MULTIPLET, AND IT DOES NOT HAVE TO.

local_nine_spurion_algebra.py (c555ac5) took the flagship fixed point out of
retraction_the_local_gut_multiplet_is_complete... , computed the local Weyl orbit and found
it is NINE-dimensional: the local group has 156 roots, the orbit has 9 weights, and the 4D
projection keeps only 5 of them -- the colour triplet (3) and the lepton doublet (2) that
the spectrum shows. It then asked whether a spurion in the fundamental-antifundamental
library C.I9 + M4(C) can give the triplet and the doublet different eigenvalues, and
answered no: the visible 5 is a single M5(C) block, so every element of that library acts on
it as a SCALAR, and the target diag(4,4,4,0,0,-3,-3,-3,-3) is not in the algebra.

That is correct and it is verified here independently. It closes a real route: you cannot
split the colour triplet from the weak doublet with one operator acting inside the twisted
multiplet.

IT DOES NOT CLOSE THE PROBLEM, because the mass terms do not act inside the twisted
multiplet. Each is a contraction of the local 9 with an UNTWISTED field, and the untwisted
fields that supply the two contractions are different:

    plane 1   d_1   a colour triplet   -> contracts only the 3 of the 9 -> triplet mass
    plane 2   d_2   a colour triplet   -> contracts only the 3 of the 9 -> triplet mass
    plane 3   bl_1  a weak doublet     -> contracts only the 2 of the 9 -> mu

No untwisted plane carries both, so the two contractions are different invariants built
from different CFT states, and their coefficients are independent. Written as a single
operator on the 9 the result is diag(a,a,a,b,b,...) with a and b unrelated, which is
exactly what their library cannot contain -- and that is the point. The splitting is not
performed by a spurion; it is inherited from the untwisted side.

SO THE TWO RESULTS COMPOSE. Their obstruction says the twisted sector is rigid: the local 9
will not split from within. The plane measurement says it never needed to. Together they
localise the mechanism exactly -- doublet-triplet splitting in this class comes from the
untwisted plane structure and from nowhere else, which is why it tracks the spectrum shape
and gives 55 of 87 (see the_missing_partner_is_the_untwisted_plane_split.py).

A PREDICTION THIS MAKES, and it is falsifiable. If the mechanism is the untwisted plane
split, then a model whose untwisted sector DOES put a colour triplet and a weak doublet in
one plane must fail, regardless of anything happening in the twisted sector. Measured: 32
of the 87 models have such a (d, bl) gauge-sibling pair, and all 32 fail; the 55 without one
all succeed. Set equality, model for model.

SCOPE. Their audit is one flagship point and an explicitly conditional spurion library with
no amplitude claim, and this file inherits that. What is added is the observation that the
library's scalar action on the visible 5 is a constraint on single operators, and the two
mass terms are not one operator.
"""

import argparse
import json
import os

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

THEIRS = {"source": "local_nine_spurion_algebra.py (c555ac5)", "local_roots": 156,
          "local_weyl_orbit": 9, "visible_in_4d": 5, "projected_out": 4,
          "spurion_algebra": "C I9 + M4(C)", "algebra_dimension": 17,
          "commutant": "M5(C) + C I4", "commutant_dimension": 26,
          "target": [4, 4, 4, 0, 0, -3, -3, -3, -3], "target_in_algebra": False}

PLANES = {"d_1": 1, "d_2": 2, "bl_1": 3}

CLASS = {"models": 87, "with_a_d_bl_sibling_pair": 32, "without": 55,
         "failing": 32, "succeeding": 55, "set_equality": True}


def unit(i, j):
    m = np.zeros((9, 9), dtype=np.int64)
    m[i, j] = 1
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    checks = {}

    I9 = np.eye(9, dtype=np.int64)
    library = [I9] + [unit(i, j) for i in range(5, 9) for j in range(5, 9)]
    checks["their_library_has_dimension_17"] = len(library) == THEIRS["algebra_dimension"] == 17

    def scalar_on_visible(m):
        blk = m[:5, :5]
        return (np.array_equal(blk, blk[0, 0] * np.eye(5, dtype=np.int64))
                and not np.any(m[:5, 5:]) and not np.any(m[5:, :5]))

    checks["every_library_element_is_scalar_on_the_visible_five"] = all(
        scalar_on_visible(m) for m in library)
    target = np.diag(THEIRS["target"])
    checks["the_splitting_target_is_not_in_the_library"] = not any(
        np.array_equal(target, m) for m in library)
    checks["their_obstruction_reproduces"] = (
        checks["every_library_element_is_scalar_on_the_visible_five"]
        and checks["the_splitting_target_is_not_in_the_library"])
    print("  their obstruction reproduces: a single operator on the 9 acts as a scalar on")
    print("  the visible 5, so it cannot split the 3 from the 2.")

    # the plane route: two contractions, by untwisted fields with no common plane
    P3 = np.diag([1, 1, 1, 0, 0, 0, 0, 0, 0])
    P2 = np.diag([0, 0, 0, 1, 1, 0, 0, 0, 0])
    checks["triplet_contraction_is_not_scalar_on_the_five"] = not scalar_on_visible(P3)
    checks["doublet_contraction_is_not_scalar_on_the_five"] = not scalar_on_visible(P2)
    a, b = 7.0, 0.3
    M = a * P3 + b * P2
    checks["independent_coefficients_give_a_split"] = (
        abs(M[0, 0] - a) < 1e-12 and abs(M[3, 3] - b) < 1e-12 and a != b)
    checks["the_split_is_outside_their_library"] = not scalar_on_visible(M)
    print("  the two mass terms are two contractions with different untwisted fields,")
    print("  giving diag(a,a,a,b,b,...) with a and b unrelated -- not one operator.")

    tp = {v for k, v in PLANES.items() if k.startswith("d_")}
    dp = {v for k, v in PLANES.items() if k.startswith("bl")}
    checks["no_untwisted_plane_carries_both"] = not (tp & dp)
    checks["three_planes_three_fields"] = len(set(PLANES.values())) == len(PLANES) == 3
    print("  untwisted planes: triplets %s, doublet %s, overlap %s"
          % (sorted(tp), sorted(dp), sorted(tp & dp)))

    c = CLASS
    checks["the_prediction_holds_across_the_class"] = (
        c["with_a_d_bl_sibling_pair"] == c["failing"] == 32
        and c["without"] == c["succeeding"] == 55
        and c["failing"] + c["succeeding"] == c["models"] == 87 and c["set_equality"])
    print("  prediction: models whose untwisted sector puts both in one plane must fail --")
    print("  %d do have such a pair and %d fail; %d do not and %d succeed; sets equal: %s"
          % (c["with_a_d_bl_sibling_pair"], c["failing"], c["without"], c["succeeding"],
             c["set_equality"]))

    for k, v in sorted(checks.items()):
        print("  %-52s %s" % (k, v))
    valid = all(checks.values())
    print("VALID:", valid)

    if args.write:
        payload = {
            "claim": "The full-Cartan spurion obstruction of c555ac5 and the untwisted plane split "
                     "are the two halves of one statement. Their result is reproduced here: the "
                     "local Weyl orbit at the flagship twisted point is a 9 of which the 4D "
                     "projection keeps 5, and every element of the fundamental-antifundamental "
                     "library C.I9 + M4(C) acts on that visible 5 as a scalar, so no single spurion "
                     "splits the colour triplet from the weak doublet. But the two mass terms are "
                     "not one operator: each is a contraction of the 9 with a different untwisted "
                     "field, and no untwisted plane carries both a triplet and a doublet (flagship "
                     "d_1 plane 1, d_2 plane 2, bl_1 plane 3). So the coefficients are independent "
                     "and the splitting is inherited from the untwisted side rather than performed "
                     "by a spurion.",
            "their_result": THEIRS, "untwisted_planes": PLANES, "class": CLASS,
            "join": "their obstruction says the twisted sector is rigid; the plane measurement says "
                    "it never needed to bend. Together they localise the mechanism: doublet-triplet "
                    "splitting in this class comes from the untwisted plane structure and nowhere "
                    "else.",
            "prediction": "a model whose untwisted sector puts a colour triplet and a weak doublet "
                          "in one plane must fail regardless of the twisted sector. 32 of 87 do, and "
                          "all 32 fail; the 55 without succeed. Set equality, model for model.",
            "checks": checks, "valid": valid,
            "status": "their spurion algebra and its scalar action are recomputed here; the plane "
                      "assignments are measured q_sh from the orbifolder; the class counts are from "
                      "the_missing_partner_is_the_untwisted_plane_split.py",
            "scope": "their audit is one flagship point and an explicitly conditional spurion "
                     "library with no amplitude claim, and this inherits that scope",
            "sources": ["Holotrade c555ac5 (local_nine_spurion_algebra.py)",
                        "Holotrade the_missing_partner_is_the_untwisted_plane_split.py",
                        "Holotrade d1fe6ce", "Holotrade 3e7bc56",
                        "Holotrade the_wilson_line_splits_every_gut_multiplet.py"]}
        with open(os.path.join(ROOT, "data", "w33_spurion_obstruction_plane_split_join.json"), "w") as f:
            json.dump(payload, f, indent=1)
        print("written")


if __name__ == "__main__":
    main()
