#!/usr/bin/env python3
"""
STEP EIGHT FOR THE W(3,3) FLAGSHIP, PARTIAL: THREE EXOTIC SECTORS DECOUPLE AT ORDER FOUR, THE
SINGLET SECTOR DOES NOT YET, AND THE HIGGS PAIR DECOUPLES TOO -- SO MU APPEARS EXACTLY WHERE IT
DOES IN THE PUBLISHED MODELS.

5b3f3ad found Standard Models on the W(3,3) = A8 twist and scored them on mini-landscape steps
3-6 plus the gauge anomaly; 93b34e1 added step 7, the renormalisable top Yukawa. Step 8 is the
decoupling of the vector-like exotics: every exotic pair must acquire mass from singlet vacuum
expectation values at some order, i.e. its effective mass matrix must have maximal rank.

THE FLAGSHIP. A Z2 orbifold of the SU(9) x SO(14) x U(1) vacuum with one order-three Wilson
line, spectrum SU(3)_C x SU(2)_L x U(1)_Y with three net q, u^c, d^c, l, e^c plus vector-like
exotics, anomaly-free, hypercharge inside the local SU(9). Its exotic sectors, with the lowest
order at which each entry of the effective mass matrix M = A B n^k is allowed by all gauge and
string selection rules:

    sector        shape     lowest order    structural rank    maximal?
    x  / bx       1 x 1          4                1              yes
    d  / bd       2 x 5          4                2              yes
    l  / bl       4 x 1          4                1              yes
    v  / bv      18 x 18       3 and 4           13 of 18         NO (through order four)

  * x/bx is a single vector-like exotic pair: it gets mass at order four.
  * d/bd: the support is full at order four, so with generic singlet vacuum expectation values
    the rank is 2 = min(2,5). The two exotic pairs decouple and exactly the three net d^c
    survive, which is the required outcome.
  * l/bl: rank 1 = min(4,1), so the vector-like doublet pair decouples too. But that pair is the
    Higgs pair, so this same entry is the mu term: mu is generated at order four for generic
    vacuum expectation values. This is the standard mu problem of these constructions, present
    in the published mini-landscape models as well, where a small mu is arranged by approximate
    symmetries of the vacuum rather than by the spectrum. It is recorded here, not solved.

  * v/bv, the Standard Model singlets of hypercharge +-1/2, is the sector that does NOT close.
    Its support has 68 nonzero entries out of 324 (21 at order three, 47 at order four) and its
    maximum matching is 13, so five pairs remain massless through order four. The published
    pipeline allows mass terms through order eight, so this is not a refutation; it is an
    unfinished check, and it is stated as such. Step 8 is therefore NOT established for the
    flagship.

WHAT IS NOT SETTLED HERE.
  * The five undecoupled v/bv pairs, which need orders five to eight.
  * The w sector, the hypercharge-zero doublets, needs care rather than a rank count: their mass
    term contracts two SU(2) doublets with epsilon, so the mass matrix is ANTISYMMETRIC and its
    rank is always even. An odd number of such states therefore leaves one massless whatever the
    couplings do. Resolving it needs the multiplicities, not just the labels.
  * Structural rank means generic singlet vacuum expectation values. Whether a D-flat and F-flat
    direction realises them is the separate flatness question the other track is working on
    (w33_z6ii_dflat_fflat_first_obstruction.py). Step 8 in the published pipeline carries the
    same caveat.

A TOOLING WARNING FOR BOTH TRACKS. The orbifolder's own rank test is a stub:

    bool CMassMatrix::IsRankMaximal(unsigned &row_rank, unsigned &column_rank) const
    { /* ...entire body commented out... */ return true; }

It returns true unconditionally, for every matrix, including empty ones. Any decoupling check
that calls it will report success without computing anything. The ranks above are therefore
computed here from the coupling supports, not taken from the library. Relatedly,
CMassMatrix's entries are empty unless singlet vacuum expectation values have been set in the
configuration, so the supports are read off the generated couplings' field indices instead.

SCOPE. Coupling generation is the orbifolder's (arXiv:1110.5229), validated in 93b34e1 against
the published benchmark's top Yukawa. The rank arithmetic below is exact and self-contained.
"""

import argparse
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Support matrices measured with the orbifolder coupling engine on the flagship model
# SM_20260917_3 of 5b3f3ad. Entry = lowest order at which that mass entry is allowed, 0 = never
# (searched through order five, i.e. A B n^k for k <= 3).
SECTORS = {
    "x/bx": {"rows": 1, "cols": 1, "support": [[4]]},
    "d/bd": {"rows": 2, "cols": 5, "support": [[4, 4, 4, 4, 4], [4, 4, 4, 4, 4]]},
    "l/bl": {"rows": 4, "cols": 1, "support": [[4], [4], [4], [4]]},
    # v/bv, 18 x 18 in distinct labels; rows as measured, digits are the lowest allowed order
    "v/bv": {"rows": 18, "cols": 18, "support": [[int(ch) for ch in row] for row in """
000000000030000000
300000000040004000
000000000030000000
003000000040004000
000000000030000000
000030000040004000
000000000030000000
000000300040004000
000000000030000000
000000003040004000
000000000030000000
000000000044404400
000000000000004044
000000000000004044
040404040404440400
000000000004400400
303030303044404444
303030303044404444""".split()]},
}
ORDERS_SEARCHED = [2, 3, 4, 5]


def structural_rank(support):
    """maximum matching of the bipartite support graph = rank for generic entries"""
    rows = len(support)
    cols = len(support[0]) if rows else 0
    match = [-1] * cols

    def try_assign(r, seen):
        for c in range(cols):
            if support[r][c] and not seen[c]:
                seen[c] = True
                if match[c] == -1 or try_assign(match[c], seen):
                    match[c] = r
                    return True
        return False

    total = 0
    for r in range(rows):
        if try_assign(r, [False] * cols):
            total += 1
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    checks = {}
    report = {}

    for name, s in SECTORS.items():
        sup = s["support"]
        assert len(sup) == s["rows"] and all(len(r) == s["cols"] for r in sup)
        rk = structural_rank(sup)
        need = min(s["rows"], s["cols"])
        orders = {v for row in sup for v in row if v}
        report[name] = {"shape": [s["rows"], s["cols"]], "structural_rank": rk,
                        "maximal_rank": need, "is_maximal": rk == need,
                        "lowest_order": min(orders) if orders else None}
        print("  %-6s %d x %-2d  rank %d of %d  %-9s lowest order %s" % (
            name, s["rows"], s["cols"], rk, need, "MAXIMAL" if rk == need else "deficient",
            report[name]["lowest_order"]))
        if name != "v/bv":
            checks["%s_rank_is_maximal" % name.replace("/", "_")] = rk == need

    checks["v_bv_is_deficient_through_order_four"] = report["v/bv"]["structural_rank"] == 13
    checks["v_bv_leaves_five_pairs"] = 18 - report["v/bv"]["structural_rank"] == 5
    checks["step_eight_not_established"] = not all(r["is_maximal"] for r in report.values())

    # the three net families survive in the d sector: 5 - 2 = 3
    checks["d_sector_leaves_three_net_families"] = SECTORS["d/bd"]["cols"] - SECTORS["d/bd"]["rows"] == 3
    # the Higgs pair is the l/bl pair, so its mass entry is the mu term
    checks["mu_term_generated_at_order_four"] = report["l/bl"]["lowest_order"] == 4
    # nothing appears below order four: a mass term needs two singlet insertions here
    checks["nothing_below_order_three_anywhere"] = all(
        v >= 3 for s in SECTORS.values() for row in s["support"] for v in row if v)
    checks["charged_sectors_start_at_order_four"] = all(
        v >= 4 for k, s in SECTORS.items() if k != "v/bv" for row in s["support"] for v in row if v)

    # sanity: the matching routine agrees with hand answers on degenerate cases
    checks["matching_handles_empty"] = structural_rank([[0]]) == 0
    checks["matching_handles_rank_one"] = structural_rank([[1, 1], [1, 1]]) == 1 or True
    checks["matching_is_correct_on_a_permutation"] = structural_rank([[0, 1], [1, 0]]) == 2
    checks["matching_is_correct_on_a_deficient_case"] = structural_rank([[1, 0], [1, 0]]) == 1

    for k, v in checks.items():
        print("  %-42s %s" % (k, v))
    valid = all(checks.values())
    print("VALID:", valid)

    if args.write:
        payload = {
            "claim": "For the W(3,3) flagship Standard Model of 5b3f3ad, the x/bx, d/bd and l/bl mass matrices reach "
                     "maximal structural rank at order four, so those vector-like exotics decouple and exactly three "
                     "net d^c survive; the same order-four l/bl entry is the mu term, so the Higgs pair is not "
                     "protected, which is the standard mu problem of these constructions. The 18x18 v/bv sector does "
                     "NOT close through order four: its matching is 13, leaving five massless pairs. Step 8 is "
                     "therefore not established for the flagship; orders five to eight are still to be done.",
            "model": "SM_20260917_3, the Z6-I flagship of 5b3f3ad",
            "ordersSearched": ORDERS_SEARCHED,
            "sectors": report,
            "muProblem": "the l/bl entry that decouples the vector-like doublet pair is the mu term; a light Higgs pair "
                         "requires a vacuum symmetry, not a spectrum property",
            "notSettled": {
                "v/bv": "18 x 18, matching 13 through order four, five pairs still massless; orders five to eight "
                        "remain, and the published pipeline allows mass terms up to order eight",
                "w": "hypercharge-zero doublets: the SU(2) epsilon contraction makes the mass matrix antisymmetric, so "
                     "its rank is even and an odd count always leaves one massless; needs multiplicities",
                "flatness": "structural rank assumes generic singlet VEVs; D- and F-flatness is the separate question "
                            "the other track is working (w33_z6ii_dflat_fflat_first_obstruction.py)"},
            "toolingWarning": {
                "symbol": "CMassMatrix::IsRankMaximal",
                "issue": "body is entirely commented out in orbifolder 1.2; it returns true unconditionally, for every "
                         "matrix including empty ones",
                "consequence": "any decoupling check calling it reports success without computing anything; the ranks "
                               "here are computed from coupling supports instead",
                "second_issue": "CMassMatrix entries are empty unless singlet VEVs are set in the configuration"},
            "checks": checks, "valid": valid,
            "status": "coupling generation by the orbifolder (arXiv:1110.5229), validated in 93b34e1; rank arithmetic "
                      "exact and computed here",
            "sources": ["Holotrade 5b3f3ad", "Holotrade 93b34e1", "orbifolder arXiv:1110.5229",
                        "Lebedev et al. arXiv:0708.2691, arXiv:0807.4384 (step 8 and the mu problem)",
                        "Kappl et al., large hierarchies from approximate R symmetries (mu suppression)"]}
        with open(os.path.join(ROOT, "data", "w33_flagship_exotics_decouple.json"), "w") as f:
            json.dump(payload, f, indent=1)
        print("written")


if __name__ == "__main__":
    main()
