#!/usr/bin/env python3
"""
Their exact 111 three-centre model, run at 90 minutes a case: all three
UNKNOWN. A measurement of the model, not of tau_2.

WHY RUN IT.  the_111_exact_three_centre_leaf_csp.py is the other track's
witness-independent decision model for tau_2 at 111: the variables are the
actual 1,600 leaves, the row and column loads are pinned to the exact
pencil-excess profile, every one of the 1,600 product tiles must be hit, and
the pencil-excess theorem makes the three centre relations -- equal, collinear,
noncollinear -- exhaustive under the diagonal PSp(4,3). Three UNSATs would
prove tau_2 >= 112 and close 111. The script is committed with no certificate
beside it, so the verdict was never taken. This takes it.

THE RUN.  Default budget is 300 s a case. This used 5400 s a case, 8 workers,
--write, on all three cases. Result:

        equal          UNKNOWN   5400 s
        collinear      UNKNOWN   5400 s
        noncollinear   UNKNOWN   5400 s   104,074,035 branches, 421,083 conflicts

and the script's own certifiedTau2Interval comes back [111, 115], which is the
value it emits when no case is SAT and not all are UNSAT. Their own reading
line is the correct one and is quoted rather than softened: "UNKNOWN is no
mathematical evidence."

SO tau_2 IS UNCHANGED AND STAYS OPEN IN [111, 115]. Nothing is proved here
about 111 in either direction.

WHAT THE MEASUREMENT IS WORTH.  Four and a half hours of solver time on the
exhaustive formulation, at eighteen times the model's default budget, does not
close a single centre case. The noncollinear case alone burned 104 million
branches for 421 thousand conflicts without terminating, which is the profile
of a search that is not near closing rather than one that just needs a little
longer. That is a real constraint on the programme: the exact leaf model at
this size is not going to be decided by turning up the clock, and the next
attempt on 111 wants a stronger reduction before the solver sees it -- more
symmetry broken, or the load profile pinned harder, or a theorem.

It also sits beside the four levers already recorded as null on the 114 side:
the clock (36d3b4b), the group (cf9ecf7), the encoding (e3ffec2) and the
transpose (b43588c). The pattern on both sides of the interval is the same --
where a control resolves, the target does not.

SCOPE.  This file asserts nothing mathematical. It records the status, budget,
worker count and search statistics of one run of someone else's model, so that
the next person does not spend the same four and a half hours discovering the
same thing. The model itself is unmodified and uncriticised: it is correct as
written, and would have proved tau_2 >= 112 had it returned three UNSATs.
"""

import argparse
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Recorded from the run: their model, unmodified, --budget 5400 --workers 8.
RUN = {
    "script": "analysis/the_111_exact_three_centre_leaf_csp.py",
    "invocation": "--budget 5400 --workers 8 --write",
    "budgetSecondsPerCase": 5400.0,
    "workers": 8,
    "cases": {
        "equal": {"status": "UNKNOWN", "seconds": 5400.077},
        "collinear": {"status": "UNKNOWN", "seconds": 5400.0},
        "noncollinear": {"status": "UNKNOWN", "seconds": 5400.052,
                         "branches": 104074035, "conflicts": 421083},
    },
    "certifiedTau2Interval": [111, 115],
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    statuses = {k: v["status"] for k, v in RUN["cases"].items()}
    all_unknown = set(statuses.values()) == {"UNKNOWN"}
    any_sat = any(s in ("OPTIMAL", "FEASIBLE") for s in statuses.values())
    all_unsat = set(statuses.values()) == {"UNSAT"}

    print("THE EXACT 111 MODEL DOES NOT CLOSE AT 90 MINUTES A CASE")
    print("=" * 74)
    print("  script : %s" % RUN["script"])
    print("  run    : %s" % RUN["invocation"])
    print()
    for name, row in RUN["cases"].items():
        extra = ""
        if "branches" in row:
            extra = "   %d branches, %d conflicts" % (row["branches"],
                                                      row["conflicts"])
        print("    %-13s %-8s %8.0f s%s"
              % (name, row["status"], row["seconds"], extra))
    print()
    print("  all three UNKNOWN            : %s" % all_unknown)
    print("  any 111 witness found        : %s" % any_sat)
    print("  all three UNSAT (would prove tau_2 >= 112) : %s" % all_unsat)
    print("  script's certified interval  : %s" % RUN["certifiedTau2Interval"])
    print()
    print("  UNKNOWN is no mathematical evidence. tau_2 stays open in [111,115].")

    ok = all_unknown and not any_sat and not all_unsat
    print()
    print("VALID: %s" % ok)

    if args.write:
        assert ok, "the recorded statuses are not all UNKNOWN"
        rec = {
            "schema": "holotrade.exact-111-model-run-record.v1",
            "valid": True,
            "run": RUN,
            "allThreeUnknown": all_unknown,
            "anyWitnessFound": any_sat,
            "allThreeUnsat": all_unsat,
            "tau2Interval": [111, 115],
            "whatWasRun": (
                "the_111_exact_three_centre_leaf_csp.py is the other track's "
                "witness-independent decision model for tau_2 at 111: actual "
                "1,600 leaf variables, row and column loads pinned to the exact "
                "pencil-excess profile, all 1,600 product tiles required to be "
                "hit, and the three centre relations made exhaustive by the "
                "pencil-excess theorem. Three UNSATs would prove tau_2 >= 112. "
                "The script is committed with no certificate beside it, so the "
                "verdict had never been taken."),
            "theVerdict": (
                "all three cases UNKNOWN at 5400 seconds each with 8 workers -- "
                "eighteen times the model's own 300-second default. The script's "
                "certifiedTau2Interval returns [111, 115], the value it emits "
                "when no case is SAT and not all are UNSAT. Their own reading "
                "line is the right one and is not softened here: UNKNOWN is no "
                "mathematical evidence. Nothing is proved about 111 in either "
                "direction."),
            "whatTheMeasurementIsWorth": (
                "four and a half hours on the exhaustive formulation does not "
                "close a single centre case, and the noncollinear case burned "
                "104,074,035 branches for 421,083 conflicts without terminating "
                "-- the profile of a search that is not near closing rather than "
                "one needing a little longer. The exact leaf model at this size "
                "will not be decided by turning up the clock; the next attempt "
                "wants a stronger reduction before the solver sees it, more "
                "symmetry broken or the load profile pinned harder or a theorem. "
                "That saves the next person the same four and a half hours."),
            "itMatchesThePatternOnTheOtherSide": (
                "this sits beside the four levers already null on the 114 side -- "
                "the clock (36d3b4b), the group (cf9ecf7), the encoding (e3ffec2) "
                "and the transpose (b43588c). On both ends of the interval the "
                "pattern is the same: where a control resolves, the target does "
                "not."),
            "boundary": (
                "this file asserts nothing mathematical. It records the status, "
                "budget, worker count and search statistics of ONE run of someone "
                "else's model. The model is unmodified and uncriticised -- it is "
                "correct as written and would have proved tau_2 >= 112 had it "
                "returned three UNSATs. tau_2 stays open in [111, 115]."),
        }
        p = os.path.join(ROOT, "data", "exact_111_model_run_record.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=2)
        print("written: %s" % p)


if __name__ == "__main__":
    main()
