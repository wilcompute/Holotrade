#!/usr/bin/env python3
"""
Five independent attacks on the gap, and the control that stops one of them
from being over-read.

This file is a search log, not a theorem. It exists because the same searches
keep being worth trying and keep failing in ways that are only informative if
recorded with their calibration attached.

WHAT WAS TRIED, and what each returned.

1. WARM-STARTED CP-SAT on the raw 1,600-leaf model, hinted with the 115-leaf
   witness, 25 minutes. Result 115, lower bound 101.

2. THE STRENGTHENED MODEL. Row and column shadows encoded exactly as
   b[L][q] = OR over p in L of x[p][q] -- as a full equality, since a
   one-sided b >= x lets the solver inflate b for free -- plus the theorem
   that every shadow is a blocking set, so has at least tau_1 = 11 points.
   Then two further valid cuts that the LP relaxation cannot see:

       |H_q| <= (t+1)|C_q|   and its transpose,

   i.e. sum over L of b[L][q] <= 4 * sum over p of x[p][q]. These are the
   inequalities whose equality case defines the tight structure, and their
   aggregate recovers sum_L |B_L| <= 4|X|.

   Bound rises from 101 to exactly 110 -- the shadow bound -- and stops.
   Feasibility at 111: UNKNOWN after fifty minutes. At 114: UNKNOWN after
   twenty-five. No verdict at either end.

3. THE COMPLETE CYCLIC-CLASS SWEEP (tensor_115_resists_from_both_sides.py):
   PSp(4,3) closed to its 25,920 elements, one representative per cycle type,
   orbit-covering solved for each. Exactly one class reaches 115; every other
   is 116 or worse.

4. THE WITNESS'S OWN SUBGROUPS. The witness is invariant under a C6, so it
   also lies in the larger invariant spaces of that C6's subgroups, where a
   better solution could hide without being symmetric enough for the sweep to
   see. The C2 subspace -- 832 orbits, warm-started from the witness itself --
   returned 115 again after seven minutes, in-class bound 106.

5. DEDICATED SIMULATED ANNEALING at fixed size 114: walk 114-leaf sets, drop a
   leaf whose tiles are all doubly covered, add one covering an uncovered
   tile, accept by Metropolis. Three seeds, fifteen minutes each, about 340
   restarts in total. Every run converged to SIX uncovered tiles and none
   reached zero.

AND THE CONTROL, which changes what number 5 means.

Six uncovered out of 1,600, reproduced across three independent seeds, reads
like an obstruction. It is not, or at least this experiment cannot say so. Run
the same annealer from PURE RANDOM starts at sizes where a solution is KNOWN
to exist:

    target 116, random starts, 7 minutes:  best 33 uncovered, never solved
    target 115, random starts, 7 minutes:  best 41 uncovered, never solved

Both are feasible -- 115 by the witness itself, 116 by the order-12 orbit
class -- and the annealer finds neither. So the search is simply not strong
enough from cold, and its 114 result is entirely an artifact of being seeded
with the 115 witness.

What the experiment therefore establishes is narrower and still worth having:
the 115-leaf witness is LOCALLY ISOLATED. Removing one leaf and repairing by
single-swap local moves does not reach a 114-leaf blocker, and gets stuck six
tiles short. It says nothing about whether a 114-leaf blocker exists
elsewhere in the space.

Recording the control rather than the headline, because "three independent
runs all stopped at six" is exactly the shape of a result that gets believed
without one.

WHERE THAT LEAVES THINGS. Five methods, no movement. The constraint side
provably cannot pass 110 -- gq_tight_case_is_an_m_ovoid.py shows the diagonal
always admits the trivial (s+1)-ovoid, so no counting argument of that kind
reaches further -- and the symmetry side has been swept completely over cyclic
subgroups. The remaining possibilities are an asymmetric 114-leaf blocker that
no local search has found, or a proof at 111-114 that is not a counting
argument. tau_2(W(3,3)^2) stays open in [111, 115].
"""

import json
import os
import sys

ROOT = r"C:\Repos\Holotrade"

ATTEMPTS = [
    {"method": "warm-started CP-SAT on the raw model",
     "budgetMinutes": 25, "result": "115", "lowerBound": 101,
     "verdict": "no improvement"},
    {"method": "strengthened model, feasibility at 111",
     "budgetMinutes": 50, "result": "UNKNOWN", "lowerBound": 110,
     "verdict": "no verdict"},
    {"method": "strengthened model, feasibility at 114",
     "budgetMinutes": 25, "result": "UNKNOWN", "lowerBound": 110,
     "verdict": "no verdict"},
    {"method": "complete cyclic conjugacy-class sweep",
     "budgetMinutes": 18, "result": "115 by exactly one class of order 6",
     "lowerBound": None, "verdict": "no improvement"},
    {"method": "C2 subspace of the witness's own stabiliser",
     "budgetMinutes": 7, "result": "115", "lowerBound": 106,
     "verdict": "no improvement"},
    {"method": "simulated annealing at fixed size 114, seeded by the witness",
     "budgetMinutes": 45, "result": "best 6 uncovered of 1600, never 0",
     "lowerBound": None, "verdict": "no solution found"},
]

CONTROL = [
    {"target": 116, "starts": "pure random", "budgetMinutes": 7,
     "knownFeasible": True, "bestUncovered": 33, "solved": False},
    {"target": 115, "starts": "pure random", "budgetMinutes": 7,
     "knownFeasible": True, "bestUncovered": 41, "solved": False},
]


def main():
    print("FIVE ATTACKS ON THE GAP, AND ONE CONTROL")
    print("=" * 72)
    for a in ATTEMPTS:
        print("  %-52s %s" % (a["method"], a["result"]))
        if a["lowerBound"] is not None:
            print("     %d min, lower bound %d" % (a["budgetMinutes"], a["lowerBound"]))
        else:
            print("     %d min" % a["budgetMinutes"])
    print()
    print("  THE CONTROL. Annealing at 114 stopping at six uncovered tiles,")
    print("  reproduced across three seeds, reads like an obstruction. Run the")
    print("  same annealer from pure random starts at sizes KNOWN feasible:")
    for c in CONTROL:
        print("     target %d (feasible: %s), random starts, %d min -> best %d "
              "uncovered, solved %s"
              % (c["target"], c["knownFeasible"], c["budgetMinutes"],
                 c["bestUncovered"], c["solved"]))
    print()
    print("  It finds NEITHER, though 115 is attained by the witness and 116")
    print("  by the order-12 orbit class. The annealer is not strong enough")
    print("  from cold, so its 114 result is an artifact of being seeded with")
    print("  the witness.")
    print()
    print("  What survives: the 115-leaf witness is LOCALLY ISOLATED --")
    print("  removing a leaf and repairing by single swaps does not reach 114")
    print("  and stalls six tiles short. Nothing is established about whether")
    print("  a 114-leaf blocker exists elsewhere.")
    print()
    print("  Five methods, no movement. The constraint side provably cannot")
    print("  pass 110, and the symmetry side is swept out over cyclic")
    print("  subgroups. What remains is an asymmetric witness no local search")
    print("  has found, or a proof that is not a counting argument.")

    ok = all(not c["solved"] and c["knownFeasible"] for c in CONTROL)
    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "tensor_114_search_log_with_control.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.tensor-114-search-log.v1",
                "valid": True,
                "isSearchLogNotTheorem": True,
                "attempts": ATTEMPTS,
                "control": CONTROL,
                "controlInvalidatesAnnealingEvidence": bool(ok),
                "whatSurvives": ("the 115-leaf witness is locally isolated: "
                                 "removing one leaf and repairing by single "
                                 "swaps stalls six tiles short of 114"),
                "whatIsNotEstablished": ("that a 114-leaf blocker does not "
                                         "exist; the annealer cannot find 115 "
                                         "or 116 from cold either, so its "
                                         "failure at 114 carries no weight as "
                                         "an infeasibility argument"),
                "newCutsUsed": ("|H_q| <= (t+1)|C_q| and its transpose, "
                                "invisible to the LP relaxation; their "
                                "aggregate is sum_L |B_L| <= (t+1)|X|"),
                "constraintSideCeiling": ("110, and provably so: the diagonal "
                                          "always admits the trivial "
                                          "(s+1)-ovoid, so no counting "
                                          "argument of that kind passes it"),
                "frontier": {"interval": [111, 115]},
                "boundary": ("a log of failed searches with its control; it "
                             "proves nothing and moves nothing"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
