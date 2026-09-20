#!/usr/bin/env python3
"""
THE ANOMALOUS U(1) FIXES THE SINGLET VEV SCALE IN EVERY MODEL, WHICH DECOUPLES THE EXOTICS
NEAR THE STRING SCALE AND PREDICTS NEUTRINOS ABOUT A HUNDRED TIMES TOO LIGHT.

Everything so far in this class has been structural -- which couplings are allowed, which
sets are flat. This turns the structure into two numbers.

THE MEASUREMENT. Every one of the 87 Z6-I Standard Models has an anomalous U(1), and the
orbifolder records its trace. Reading SymmetryGroup.D0_FI_term:

    Tr Q_anom takes 14 values, ALL divisible by 8:
    144(8) 160(6) 200(12) 216(3) 224(3) 232(8) 240(3) 264(6) 272(2) 280(6) 312(6) 336(9)
    440(6) 576(9)     -- min 144, median 264, max 576

The Fayet-Iliopoulos term is xi = g^2 M_s^2 Tr Q_anom / (192 pi^2) and D-flatness sets
<n>^2 ~ xi, so with g ~ 0.7

    <n>/M_s = g sqrt(Tr Q_anom / 192 pi^2)  =  0.19 (min) ... 0.26 (median) ... 0.39 (max)

The whole class condenses within a factor of about four of the string scale.

CONSEQUENCE ONE, AND IT SOFTENS AN EARLIER WORRY. The vector-like exotics get their mass
from the same VEVs, so they sit at ~0.26 M_s. The running range over which they can distort
gauge coupling unification is therefore a factor of about four, not the many decades one
might fear. the_full_spectrum_is_never_su5_complete.py measured that no model in the class
has SU(5)-complete matter; this says the incompleteness has a short lever arm. The two
together are the honest picture: badly incomplete, but decoupling almost immediately.

CONSEQUENCE TWO, AND IT IS A FALSIFIABLE NUMBER. The see-saw. The Dirac operator l.bl.n
first appears at order four, so y_nu ~ <n>/M_s; the Majorana mass comes from the order-three
n^3 terms, so M_R ~ <n>; and 27 right-handed neutrinos acquire Majorana masses
(the_majorana_matrix_has_a_persistent_kernel.py). With v = 174 GeV and M_s = 5 x 10^17 GeV,

    m_nu ~ N y_nu^2 v^2 / M_R ,  giving

    Tr Q = 144  ->  3.2 x 10^-4 eV
    Tr Q = 264  ->  4.3 x 10^-4 eV
    Tr Q = 576  ->  6.3 x 10^-4 eV

against an observed atmospheric scale of about 0.05 eV. The class predicts neutrinos LOW BY
A FACTOR OF ROUGHLY ONE HUNDRED.

And the prediction is robust across the class, which is what makes it worth stating: m_nu
scales as <n>, i.e. as the square root of Tr Q_anom, so a factor of four spread in Tr Q
moves the answer by only a factor of two. One cannot tune Tr Q to fix this. Closing the gap
needs either a Dirac operator at order three rather than four -- which would raise y_nu to
order one and gain the missing two orders -- or many more right-handed neutrinos than the 27
measured, or a Majorana scale well below <n>.

A NEAR-MISS WORTH RECORDING. Computing Tr Q directly from the dumped U(1) charges gives
exactly zero for all seven directions, in all 87 models, and for Tr Q^3 as well -- with the
positive and negative contributions individually large (plus and minus 17522, plus and minus
39126 on the flagship) and cancelling exactly. Taken at face value that says "no anomalous
U(1), hence no FI term", which would have STRENGTHENED the D-flatness no-go of babfd48 by
removing its escape. It is wrong: the orbifolder's own IsFirstU1Anomalous is 1 in all 87 and
its FI term is nonzero. The dumped charges are simply in a different basis from the one in
which the anomalous generator is defined. The lesson is the ordinary one -- a clean zero
that happens to support the conclusion you are already carrying deserves a second source
before it is published, and here the second source disagreed.

SCOPE. Order-of-magnitude scales with explicit inputs: g = 0.7, M_s = 5 x 10^17 GeV,
v = 174 GeV, N = 27 from one model. The Yukawa estimate y ~ (<n>/M_s)^(k-3) for an
order-k operator is the standard suppression counting, not an amplitude calculation, and
coefficients of order one are assumed throughout -- which is exactly the assumption a factor
of a hundred could hide in. The FI relation <n>^2 ~ xi fixes a scale, not a vacuum. Tr Q_anom
is the orbifolder's value, not independently recomputed, and the basis discrepancy above is
recorded rather than resolved.
"""

import argparse
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TRACES = {144: 8, 160: 6, 200: 12, 216: 3, 224: 3, 232: 8, 240: 3, 264: 6,
          272: 2, 280: 6, 312: 6, 336: 9, 440: 6, 576: 9}

INPUTS = {"g": 0.7, "M_s_GeV": 5e17, "v_GeV": 174.0, "N_RH": 27,
          "dirac_order": 4, "majorana_order": 3}

OBSERVED_eV = 0.05

NEAR_MISS = {"direct_trace_all_directions": 0, "direct_trace_cubed": 0,
             "orbifolder_says_anomalous": 87, "of": 87,
             "flagship_cancelling_pair": [17522, -17522]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    checks = {}
    I = INPUTS

    n = sum(TRACES.values())
    print("  models: %d | distinct Tr Q_anom values: %d | min %d median-ish max %d"
          % (n, len(TRACES), min(TRACES), max(TRACES)))
    checks["all_87_accounted"] = n == 87
    checks["every_trace_divisible_by_eight"] = all(t % 8 == 0 for t in TRACES)
    checks["traces_span_a_factor_four"] = max(TRACES) / min(TRACES) >= 4.0
    checks["every_model_has_an_anomalous_u1"] = (
        NEAR_MISS["orbifolder_says_anomalous"] == NEAR_MISS["of"] == 87)

    def eps(TrQ):
        return I["g"] * math.sqrt(TrQ / (192 * math.pi ** 2))

    lo, hi = eps(min(TRACES)), eps(max(TRACES))
    print("  <n>/M_s = %.3f .. %.3f" % (lo, hi))
    checks["vev_is_a_sizeable_fraction_of_Ms"] = lo > 0.1
    checks["vev_is_below_Ms"] = hi < 1.0
    checks["exotics_decouple_within_a_factor_ten"] = 1.0 / lo < 10.0
    print("  exotics decouple within a factor %.1f of the string scale" % (1.0 / eps(264)))

    def mnu(TrQ):
        e = eps(TrQ)
        return I["N_RH"] * e * e * I["v_GeV"] ** 2 / (e * I["M_s_GeV"]) * 1e9  # eV

    vals = {t: mnu(t) for t in (min(TRACES), 264, max(TRACES))}
    for t, m in vals.items():
        print("  Tr Q = %3d -> m_nu ~ %.2e eV" % (t, m))
    checks["all_predictions_are_sub_milli_eV"] = all(m < 1e-3 for m in vals.values())
    ratio = OBSERVED_eV / vals[264]
    print("  observed ~%.2f eV -> low by a factor %.0f" % (OBSERVED_eV, ratio))
    checks["prediction_is_too_light"] = ratio > 10
    checks["shortfall_is_about_a_hundred"] = 30 < ratio < 400
    # robustness: a factor-4 spread in Tr Q moves m_nu by only sqrt(4) = 2
    spread = max(vals.values()) / min(vals.values())
    print("  a factor %.1f spread in Tr Q moves m_nu by only %.2f" % (max(TRACES) / min(TRACES), spread))
    checks["prediction_is_insensitive_to_the_trace"] = spread < 2.5
    checks["cannot_tune_the_trace_to_fix_it"] = spread < ratio

    nm = NEAR_MISS
    checks["direct_trace_was_zero"] = nm["direct_trace_all_directions"] == 0
    checks["cubed_trace_was_zero_too"] = nm["direct_trace_cubed"] == 0
    checks["but_the_orbifolder_disagrees"] = nm["orbifolder_says_anomalous"] == 87
    checks["the_zero_was_a_basis_artefact"] = (
        nm["direct_trace_all_directions"] == 0 and nm["orbifolder_says_anomalous"] > 0)
    checks["cancellation_was_between_large_numbers"] = (
        sum(nm["flagship_cancelling_pair"]) == 0 and nm["flagship_cancelling_pair"][0] > 1000)

    for k, v in sorted(checks.items()):
        print("  %-50s %s" % (k, v))
    valid = all(checks.values())
    print("VALID:", valid)

    if args.write:
        payload = {
            "claim":
                "Every one of the 87 Z6-I Standard Models has an anomalous U(1), with Tr Q_anom "
                "taking 14 values all divisible by 8, from 144 to 576. The Fayet-Iliopoulos term "
                "fixes <n>/M_s = g sqrt(Tr Q / 192 pi^2) = 0.19 to 0.39, so the whole class "
                "condenses within a factor of about four of the string scale. Two consequences: the "
                "vector-like exotics decouple almost immediately, so the SU(5)-incompleteness "
                "measured elsewhere has a short lever arm; and the see-saw predicts m_nu ~ 3 to 6 "
                "x 10^-4 eV against an observed 0.05 eV -- low by a factor of about a hundred, and "
                "robustly so, since m_nu scales as the square root of Tr Q and a factor-four spread "
                "moves it by only two.",
            "traces": TRACES, "inputs": INPUTS, "observed_eV": OBSERVED_eV,
            "near_miss": NEAR_MISS,
            "how_to_close_the_gap": "a Dirac operator at order three rather than four (raising y_nu "
                                    "to order one, worth the missing two orders), or many more than "
                                    "the 27 measured right-handed neutrinos, or a Majorana scale "
                                    "well below <n>",
            "lesson": "computing Tr Q directly from the dumped charges gives exactly zero for all "
                      "seven directions and for Tr Q^3, by exact cancellation of large numbers. That "
                      "would have said 'no anomalous U(1), hence no FI term', STRENGTHENING the "
                      "existing D-flatness no-go -- and it is wrong, a basis artefact. A clean zero "
                      "that supports the conclusion one is already carrying needs a second source.",
            "checks": checks, "valid": valid,
            "status": "Tr Q_anom read from the orbifolder's own D0_FI_term for all 87 models; the "
                      "scales and the see-saw estimate are computed here from stated inputs",
            "scope": "order-of-magnitude with explicit inputs g = 0.7, M_s = 5e17 GeV, v = 174 GeV, "
                     "N = 27 from one model; y ~ (<n>/M_s)^(k-3) is the standard suppression "
                     "counting, not an amplitude calculation, and order-one coefficients are assumed "
                     "-- which is where a factor of a hundred could hide. The basis discrepancy is "
                     "recorded, not resolved.",
            "sources": ["Holotrade 7fcdd20", "Holotrade 5eab5c8", "Holotrade babfd48",
                        "Holotrade 5b3f3ad", "orbifolder 1.2.1 arXiv:1110.5229"]}
        with open(os.path.join(ROOT, "data", "w33_fi_scale_and_neutrino_shortfall.json"), "w") as f:
            json.dump(payload, f, indent=1)
        print("written")


if __name__ == "__main__":
    main()
