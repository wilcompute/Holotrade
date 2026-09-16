#!/usr/bin/env python3
"""
THE STANDARD MODEL NO-GO IS CLOSED: THE EXHAUSTIVE CENSUS AND THE TWO THEOREMS AGREE,
TERM BY TERM.

Two tracks reached the same wall from opposite directions on the same day, and this
file checks that they are the same wall.

THE ENUMERATION (the other track). w33_su5_breaking_exhaustive and
w33_su5_sm_chiral_exhaustive exhaust the physical Wilson-class universe E8/3E8 rather
than sampling it: 383940 modular-compatible second Wilson classes breaking the frozen
SU(5) to A2 + A1, of which 127980 carry |Q| = 3. Their chiral census is
    (Q, u^c, d^c, L, e^c) = (3,0,3,3,0)  56160 classes
                            (3,0,0,0,0)  56160
                            (3,0,-3,-3,0) 15660
with u^c = e^c = 0 throughout, a universal twisted contribution of (0,0,-3,-3,0), and
k_Y = 5/3 for every such breaking. No class carries (3,3,3,3,3).

THE PROOFS (this track). a6e1c69 and 47e85ab derive exactly that shape:
  - SPLITTING (a6e1c69): on one SU(5) irrep P.a = k + cY with k constant, and breaking
    forces 5c/6 = +-1/3 mod 1, so the gaps 5c/6, -5c/6 and -5c/3 are all non-integral.
    At most ONE of Q, u^c, e^c survives per ten, and one of d^c, L per anti-five.
  - NO TEN IN THE TWISTED SECTORS (47e85ab): a ten-weight has norm 6/5, a massless
    twisted state has |P|^2 = 4/3, and the remaining 2/15 is below the 2/9 floor of a
    nontrivial E8 coset, which every local shift's second-E8 part is.
  - Hence Q, u^c, e^c are untwisted-only, each untwisted ten donates at most one of
    them, and with n10 = 3 and Q a multiple of three, Q = 3 exhausts the tens and
    forces u^c = e^c = 0.

WHAT THIS FILE CHECKS, against the other track's frozen JSON:
  1. u^c = e^c = 0 in every one of the 127980 classes - the splitting theorem's
     prediction, now confirmed exhaustively rather than on 10^4 samples.
  2. The universal twisted contribution has ZERO in the Q, u^c and e^c slots and is
     nonzero only in d^c and L - exactly "the twisted sectors carry no ten".
  3. d^c = L in every census entry - the anti-five splitting, which permits only one
     of the two per multiplet and pairs them across multiplets.
  4. Every census entry is a multiple of three in Q - ade6ba9's untwisted-plane rule.
  5. The Standard Model vector (3,3,3,3,3) is absent, and the best is three species.
  6. Their k_Y = 5/3 agrees with the canonical hypercharge used in bf7ce0a's controls.

WHY BOTH HALVES MATTER. An exhaustive census says the SM is not there; the theorems
say why, and cover breakings outside the enumerated frame (other GUT factors, other
orders: at any order N, Q is isolated and the anti-five splits, and only even N can
pair u^c with e^c). Neither alone is the result; together the no-go is closed.

SCOPE. The enumeration is the other track's and is cited, not reproduced here. The
theorems are this track's. What is new in this file is only the reconciliation.
"""

import argparse
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORDER = ["Q", "uc", "dc", "L", "ec"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    D = os.path.join(ROOT, "data")
    census = json.load(open(os.path.join(D, "w33_su5_sm_chiral_exhaustive.json")))
    breaking = json.load(open(os.path.join(D, "w33_su5_breaking_exhaustive.json")))
    noten = json.load(open(os.path.join(D, "w33_twisted_sectors_carry_no_ten.json")))
    split = json.load(open(os.path.join(D, "w33_wilson_line_splits_gut_multiplets.json")))
    sampled = json.load(open(os.path.join(D, "w33_vacuum_no_standard_model_family.json")))
    checks = {}

    vectors = {k: [int(x) for x in k.strip("()").split(",")] for k in census["chiral_census"]}
    total = sum(census["chiral_census"].values())
    print("  exhaustive classes with |Q| = 3: %d in %d patterns" % (total, len(vectors)))
    for k, v in sorted(census["chiral_census"].items(), key=lambda kv: -kv[1]):
        print("      %-16s %6d classes" % (k, v))
    checks["census_total_matches"] = total == census["models_with_abs_Q_3"] == 127980
    checks["splitting_uc_ec_zero_everywhere"] = all(v[1] == 0 and v[4] == 0 for v in vectors.values())
    checks["fivebar_pairs_dc_with_L"] = all(v[2] == v[3] for v in vectors.values())
    checks["quark_doublets_multiple_of_three"] = all(v[0] % 3 == 0 for v in vectors.values())
    checks["no_standard_model_vector"] = census["standard_model_models"] == 0 and census["best_species_present"] == 3

    tw = census["universal_twisted_contribution"]["(Q,uc,dc,L,ec)"]
    print("  universal twisted contribution:", dict(zip(ORDER, tw)))
    checks["twisted_carries_no_ten_species"] = tw[0] == 0 and tw[1] == 0 and tw[4] == 0
    checks["twisted_carries_only_fiveplet_species"] = (tw[2] != 0 or tw[3] != 0)
    checks["twisted_certificate_agrees"] = (noten["checks"]["no_twisted_ten_species"] and
                                            noten["checks"]["twisted_does_supply_fiveplet_species"])

    # the untwisted remainder, once the universal twisted piece is removed, must be Q-only in the ten slots
    untw = {k: [v[i] - tw[i] for i in range(5)] for k, v in vectors.items()}
    print("  untwisted remainder per pattern:", {k: dict(zip(ORDER, u)) for k, u in untw.items()})
    checks["untwisted_remainder_has_no_uc_or_ec"] = all(u[1] == 0 and u[4] == 0 for u in untw.values())
    checks["untwisted_remainder_Q_is_three"] = all(u[0] == 3 for u in untw.values())

    ky = "5/3" in breaking["headline"] or "k_Y=5/3" in breaking["headline"]
    checks["kY_agrees_with_our_controls"] = ky and abs(sampled["controls"]["control_SU(5)"]["kY"] - 5 / 3) < 1e-9
    checks["splitting_certificate_valid"] = split["valid"] and split["checks"]["one_species_per_multiplet"]
    checks["order_rule_still_general"] = split["measurements"]["byWilsonLineOrder"]["3"] == []

    for k, v in checks.items():
        print("  %-42s %s" % (k, v))
    valid = all(checks.values())
    print("VALID:", valid)
    if args.write:
        payload = {
            "claim": "The other track's exhaustive census over E8/3E8 (127980 net-|3| classes, no Standard Model vector) and "
                     "this track's two theorems (splitting: at most one of Q, u^c, e^c per ten; no ten in the twisted sectors) "
                     "agree term by term. u^c = e^c = 0 in every class, the universal twisted contribution is (0,0,-3,-3,0), "
                     "d^c = L throughout, and the untwisted remainder is Q = 3 with empty u^c and e^c slots.",
            "census": census["chiral_census"], "universalTwisted": dict(zip(ORDER, tw)),
            "untwistedRemainder": {k: dict(zip(ORDER, u)) for k, u in untw.items()},
            "enumeration": {"source": "w33_su5_sm_chiral_exhaustive.json / w33_su5_breaking_exhaustive.json (other track)",
                            "classes": census["models_with_abs_Q_3"],
                            "compatibleSecondWilsonClasses": breaking["universe"]["compatible_second_wilson_classes"]},
            "theorems": {"splitting": "Holotrade a6e1c69", "noTenTwisted": "Holotrade 47e85ab"},
            "checks": checks, "valid": valid,
            "status": "reconciliation: enumeration (other track) and proof (this track) describe the same wall",
            "sources": ["Holotrade ade6ba9", "Holotrade 35eb923", "Holotrade bf7ce0a", "Holotrade a6e1c69", "Holotrade 47e85ab",
                        "other track: w33_su5_breaking_exhaustive, w33_su5_sm_chiral_exhaustive"]}
        with open(os.path.join(D, "w33_standard_model_no_go_closed.json"), "w") as f:
            json.dump(payload, f, indent=1)
        print("written")


if __name__ == "__main__":
    main()
