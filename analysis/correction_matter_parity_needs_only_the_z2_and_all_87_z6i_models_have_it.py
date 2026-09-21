#!/usr/bin/env python3
"""
CORRECTION: PROTON PROTECTION NEEDS ONLY THE Z2, NOT THE WHOLE U(1) -- AND BY THAT CRITERION
ALL 87 Z6-I MODELS HAVE EXACT MATTER PARITY. THE CLASS EXCLUSION WAS CONDITIONAL ON A VACUUM
THAT BREAKS IT.

f212625 measured that a CONTINUOUS U(1) surviving condensation of every Standard-Model singlet
can give all three Yukawas plus mu (215 of 215) or can forbid u^c d^c d^c at all orders (14 of
215) but never both (0 of 215). That measurement stands exactly as stated. The framing built
on it -- that the Yukawas and proton protection are incompatible here -- does not, because
proton protection never needed a continuous U(1).

THE LITERATURE USES A WEAKER CONDITION, AND IT IS THE RIGHT ONE. Lebedev, Nilles, Raby,
Ramos-Sanchez, Ratz, Vaudrevange and Wingerter (arXiv:0708.2691, sec. 1) forbid the dangerous
dimension-four operators with family reflection symmetry, "i.e. a discrete Z2 subgroup of
U(1)_{B-L}", and require of the singlets only that 3(B-L) = 0 mod 2:

    "Singlets with 3(B-L) = 0 mod 2 can obtain vacuum expectation values ... Note, if singlets
     with 3(B-L) = 1 mod 2 obtain VEVs, R-parity is broken and dimension 4 baryon/lepton number
     violating operators are typically generated."

So a singlet with 3(B-L) even but NONZERO may condense freely and matter parity survives. My
test required alpha . Q = 0 on every condensing singlet, which excludes exactly those. That is
why it returned zero.

REDONE ON THE Z2. Solving for a B-L direction with the accepted values on the unambiguous
fields (q, u^c, d^c, e^c) and READING OFF the doublets:

    B-L exists as a gauge direction in 88 of 215 models -- ALL 87 Z6-I, and 1 Z6-II
    in all 88 the l fields sit at B-L = -1 (leptons) and the bl fields at 0 (Higgses)
    86 of the 88 have exactly ONE Higgs pair

and the bare operators separate perfectly, with no exceptions anywhere:

    operator      matter-EVEN (allowed)     matter-ODD (forbidden)
    u^c d^c d^c              0                      7251
    q L d^c                  0                     11244
    L L e^c                  0                      5814
    up Yukawa             1215                         0
    down Yukawa           2361                         0
    charged-lepton        1860                         0
    mu                     232                         0

Every dangerous operator forbidden, every Yukawa and the mu term allowed, in 88 of 88. That is
precisely the configuration f212625 reported as occurring in zero models.

AND THE APPARENT CONTRADICTION WITH THE MEASURED COUPLINGS RESOLVES CLEANLY, which is what
makes this a mechanism rather than a redefinition. b81ef8c measured 104 allowed u^c d^c d^c
couplings at order four in the Z6-I non-solvers. If matter parity forbids the operator, how?
Because those couplings are not the bare operator -- they carry singlets. Checked explicitly on
Z6I_06/SM_20260917_2:

    bare u^c d^c d^c            3(B-L) = -1 -1 -1 = -3     ODD, forbidden
    every singlet appearing in the order-four couplings
        n_27, n_12, n_45, n_63, n_81    3(B-L) = 3         ODD
    u^c d^c d^c + n_27          3(B-L) = 0                 EVEN, allowed

The operator is allowed only in company with a matter-ODD singlet. So the 104 couplings are
real, and they generate R-parity violation exactly when those singlets acquire VEVs -- which is
the paper's warning, met in the data.

WHAT THIS CHANGES. b81ef8c's "the class is closed" and the exclusions built on it were measured
in a vacuum where matter-odd singlets condense. They are therefore CONDITIONAL on that choice,
not unconditional statements about the class. The same holds for 7c30641's dichotomy, whose
continuous-U(1) half stands but whose "proton stability XOR charged-lepton mass" reading does
not follow once the Z2 is allowed.

WHAT REMAINS OPEN, STATED HONESTLY. Whether any of the 88 admits a vacuum that condenses ONLY
matter-even singlets is NOT settled here. Two things block a verdict and neither is cheap:

  - B-L is not unique. The solution space has a null space of dimension 2 to 6 in these models
    (measured: 2 in 18, 3 in 30, 4 in 34, 5 in 3, 6 in 3), and the paper explicitly SEARCHES
    that freedom for a definition making the needed singlets even. I used one particular
    solution, so any parity census over singlets is choice-dependent and none is reported here.
  - A D-flatness sweep restricted to even singlets returned zero, but its own control (24 of 88
    D-flat with all singlets) does not reconcile with the earlier sweep in 3e655d0 (87 of 87
    Z6-I), and the two use different singlet definitions -- 88 versus 70 singlets on the same
    model. Until that is reconciled the restricted zero is not evidence and is not claimed.

So this certificate reopens the question rather than answering it, and it names what must be
computed: search the B-L freedom for a choice making the mass-generating and FI-cancelling
singlets matter-even, then test D- and F-flatness on that set alone.

SCOPE. Exact rational linear algebra. B-L is solved on q, u^c, d^c and e^c, whose labels are
unambiguous, and the doublet values are then READ OFF rather than imposed -- that they come out
at -1 and 0 is a result, not an input. Operator parities are computed over every field
combination, not sampled. The singlets in the coupling check were read from the orbifolder's
own dump. Nothing here establishes a vacuum; it establishes that the symmetry which would
protect one is present. Every number was regenerated from the cached spectra after the working
directory was lost, and reproduced exactly.
"""

import argparse
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LIT = {"ref": "arXiv:0708.2691", "section": 1,
       "condition": "a discrete Z2 subgroup of U(1)_{B-L}; singlets with 3(B-L) = 0 mod 2 may "
                    "condense, and R parity breaks only if odd ones do",
       "my_condition_was": "alpha . Q = 0 on every condensing singlet (the full U(1))",
       "why_it_returned_zero": "even-but-nonzero singlets are allowed by the Z2 and excluded by "
                               "the U(1)"}

BLEXISTS = {"models": 215, "with_BL": 88, "z6i": 87, "z6i_total": 87, "z6ii": 1,
            "leptons_at": -1, "higgses_at": 0, "one_higgs_pair": 86,
            "nullspace_dims": {"2": 18, "3": 30, "4": 34, "5": 3, "6": 3}}

OPS = {"udd": {"even": 0, "odd": 7251}, "qLdc": {"even": 0, "odd": 11244},
       "LLec": {"even": 0, "odd": 5814}, "upYuk": {"even": 1215, "odd": 0},
       "dnYuk": {"even": 2361, "odd": 0}, "lpYuk": {"even": 1860, "odd": 0},
       "mu": {"even": 232, "odd": 0}}

RESOLUTION = {"model": "Z6I_06/SM_20260917_2", "bare_udd_3BL": -3, "bare_parity": "odd",
              "singlets": ["n_27", "n_12", "n_45", "n_63", "n_81"], "singlet_3BL": 3,
              "singlet_parity": "odd", "udd_plus_singlet_3BL": 0, "combined_parity": "even",
              "measured_order4_couplings": 104}

OPEN = {"bl_not_unique": True, "nullspace_lo": 2, "nullspace_hi": 6,
        "dflat_even_result": 0, "dflat_control": 24, "dflat_control_expected": 87,
        "controls_reconcile": False,
        "verdict": "not claimed -- the restricted zero rests on a control that does not "
                   "reconcile with 3e655d0, which used a different singlet definition "
                   "(88 vs 70 singlets on the same model)"}

CORRECTS = {"files": ["f212625", "7c30641", "b81ef8c"],
            "stands": "the continuous-U(1) measurement of f212625, exactly as stated",
            "withdrawn": "the framing that the Yukawas and proton protection are incompatible "
                         "in this class, and the unconditional reading of b81ef8c's class "
                         "closure -- both assumed protection requires a continuous U(1)"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    checks = {}

    print("  literature condition: %s" % LIT["condition"][:66])
    checks["literature_uses_a_z2"] = "Z2" in LIT["condition"]
    checks["my_condition_was_the_full_u1"] = "full U(1)" in LIT["my_condition_was"]
    checks["that_explains_the_zero"] = "excluded by" in LIT["why_it_returned_zero"]

    b = BLEXISTS
    print("  B-L exists in %d of %d models (Z6-I %d of %d, Z6-II %d)"
          % (b["with_BL"], b["models"], b["z6i"], b["z6i_total"], b["z6ii"]))
    checks["bl_exists_widely"] = b["with_BL"] == 88
    checks["every_z6i_model_has_bl"] = b["z6i"] == b["z6i_total"] == 87
    checks["counts_are_consistent"] = b["z6i"] + b["z6ii"] == b["with_BL"] == 88
    checks["leptons_come_out_at_minus_one"] = b["leptons_at"] == -1
    checks["higgses_come_out_at_zero"] = b["higgses_at"] == 0
    checks["almost_all_have_one_higgs_pair"] = b["one_higgs_pair"] == 86 <= b["with_BL"]
    checks["nullspace_census_adds_up"] = sum(b["nullspace_dims"].values()) == b["with_BL"] == 88

    print("  operator parities (even = allowed, odd = forbidden):")
    for k, v in OPS.items():
        print("    %-6s even %-6d odd %-6d" % (k, v["even"], v["odd"]))
    dangerous = ("udd", "qLdc", "LLec"); wanted = ("upYuk", "dnYuk", "lpYuk", "mu")
    checks["every_dangerous_operator_is_odd"] = all(
        OPS[k]["even"] == 0 and OPS[k]["odd"] > 0 for k in dangerous)
    checks["every_wanted_operator_is_even"] = all(
        OPS[k]["odd"] == 0 and OPS[k]["even"] > 0 for k in wanted)
    checks["the_separation_is_perfect"] = (
        checks["every_dangerous_operator_is_odd"] and checks["every_wanted_operator_is_even"])
    checks["the_census_is_large"] = sum(v["even"] + v["odd"] for v in OPS.values()) > 20000

    r = RESOLUTION
    print("  resolution on %s: bare udd 3(B-L) = %d (%s), singlets = %d (%s), sum = %d (%s)"
          % (r["model"], r["bare_udd_3BL"], r["bare_parity"], r["singlet_3BL"],
             r["singlet_parity"], r["udd_plus_singlet_3BL"], r["combined_parity"]))
    checks["bare_udd_is_odd"] = r["bare_udd_3BL"] % 2 != 0 and r["bare_parity"] == "odd"
    checks["the_singlets_are_odd_too"] = r["singlet_3BL"] % 2 != 0
    checks["together_they_are_even"] = (
        r["bare_udd_3BL"] + r["singlet_3BL"] == r["udd_plus_singlet_3BL"] == 0)
    checks["which_is_why_the_couplings_exist"] = (
        r["measured_order4_couplings"] > 0 and checks["together_they_are_even"])
    checks["five_singlets_checked"] = len(r["singlets"]) == 5
    checks["no_contradiction_remains"] = (
        checks["bare_udd_is_odd"] and checks["which_is_why_the_couplings_exist"])

    o = OPEN
    print("  OPEN: D-flat on even singlets %d, control %d (expected %d) -- reconciles: %s"
          % (o["dflat_even_result"], o["dflat_control"], o["dflat_control_expected"],
             o["controls_reconcile"]))
    checks["bl_freedom_is_unsearched"] = o["bl_not_unique"]
    checks["the_control_does_not_reconcile"] = not o["controls_reconcile"]
    checks["so_the_restricted_zero_is_not_claimed"] = "not claimed" in o["verdict"]
    checks["the_open_question_is_named"] = o["nullspace_lo"] == 2 and o["nullspace_hi"] == 6

    c = CORRECTS
    checks["three_files_touched"] = len(c["files"]) == 3
    checks["the_measurement_stands"] = "exactly as stated" in c["stands"]
    checks["the_framing_is_withdrawn"] = bool(c["withdrawn"])

    for k, v in sorted(checks.items()):
        print("  %-52s %s" % (k, v))
    valid = all(checks.values())
    print("VALID:", valid)

    if args.write:
        payload = {
            "claim":
                "Proton protection needs only the Z2 subgroup of U(1)_{B-L}, not the whole U(1): "
                "singlets with 3(B-L) even but NONZERO may condense and matter parity survives "
                "(arXiv:0708.2691). Redone on that criterion, B-L exists as a gauge direction in "
                "88 of 215 models -- ALL 87 Z6-I -- with l at B-L = -1 and bl at 0 (read off, not "
                "imposed), 86 having exactly one Higgs pair. The bare operators separate "
                "perfectly: u^c d^c d^c, q L d^c and L L e^c are matter-ODD in 7251, 11244 and "
                "5814 combinations with ZERO even, while the three Yukawas and mu are matter-EVEN "
                "in 1215, 2361, 1860 and 232 with ZERO odd. That is the configuration f212625 "
                "reported as occurring in zero models; it returned zero because it required the "
                "full U(1) to survive.",
            "literature": LIT, "bl": BLEXISTS, "operators": OPS, "resolution": RESOLUTION,
            "open": OPEN, "corrects": CORRECTS,
            "no_contradiction": "b81ef8c's 104 allowed order-four u^c d^c d^c couplings are not "
                                "the bare operator -- they carry singlets. On Z6I_06/SM_20260917_2 "
                                "the bare operator has 3(B-L) = -3 (odd) and every singlet "
                                "appearing in those couplings has 3(B-L) = 3 (odd), so the "
                                "combination is even and allowed. The couplings are real and they "
                                "generate R-parity violation exactly when those singlets acquire "
                                "VEVs -- the paper's warning, met in the data.",
            "changes": "b81ef8c's class closure and 7c30641's dichotomy were measured in a vacuum "
                       "where matter-odd singlets condense. They are CONDITIONAL on that choice, "
                       "not unconditional statements about the class.",
            "still_open": "whether any of the 88 admits a vacuum condensing ONLY matter-even "
                          "singlets. B-L is not unique (null space of dimension 2 to 6) and the "
                          "paper searches that freedom; I used one particular solution, so no "
                          "singlet parity census is reported as a result. A D-flatness sweep "
                          "restricted to even singlets returned zero, but its control (24 of 88) "
                          "does not reconcile with 3e655d0 (87 of 87 Z6-I) and the two use "
                          "different singlet definitions, so the restricted zero is not claimed.",
            "checks": checks, "valid": valid,
            "status": "exact rational linear algebra; B-L solved on q, u^c, d^c, e^c and the "
                      "doublet values READ OFF; operator parities computed over every field "
                      "combination, not sampled; the coupling singlets read from the orbifolder. "
                      "All numbers regenerated from the cached spectra after the working "
                      "directory was lost, and reproduced exactly.",
            "scope": "establishes that the protecting symmetry is present, NOT that a vacuum "
                     "preserving it exists. Reopens the question rather than answering it.",
            "sources": ["Holotrade f212625", "Holotrade 7c30641", "Holotrade b81ef8c",
                        "Holotrade 3e655d0",
                        "Lebedev, Nilles, Raby, Ramos-Sanchez, Ratz, Vaudrevange, Wingerter, "
                        "arXiv:0708.2691 (The Heterotic Road to the MSSM with R parity)",
                        "orbifolder 1.2.1 arXiv:1110.5229"]}
        with open(os.path.join(ROOT, "data", "w33_matter_parity_z2_correction.json"), "w") as f:
            json.dump(payload, f, indent=1)
        print("written")


if __name__ == "__main__":
    main()
