#!/usr/bin/env python3
"""
Eight independent attacks on the gap, and the control that stops one of
them from being over-read.

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

6. ROW-WEIGHTING LOCAL SEARCH, the standard method that actually works on set
   cover: every tile carries a weight, cost is the total weight of uncovered
   tiles, and weights of still-uncovered tiles are raised when the search
   stalls so the landscape deforms until it escapes. It failed its own
   calibration -- from cold it could not reach even 121, where B x B is an
   explicit solution -- so nothing it says about 114 counts either. Recorded
   so the next attempt does not rebuild it.

7a. NON-CYCLIC SYMMETRY, which closes a boundary this file had left open.
   tensor_115_resists_from_both_sides.py swept every CYCLIC class of PSp(4,3)
   and said so -- non-cyclic subgroups have different orbits, so a better
   blocker could have hidden in one without any cyclic model seeing it.

   Random pairs of Sp(4,3) elements almost always generate a large subgroup,
   so a naive sweep found exactly one usable class. COMMUTING pairs generate
   abelian groups of order at most ord(g)*ord(h), which lands reliably in the
   range where the orbit model stays solvable. Building the full 25,920-element
   group, taking centralisers of the 4,895 elements of order 2 to 4, and
   sweeping the resulting subgroups gave 512 pairs and nine distinct
   non-cyclic classes of orders 4, 8, 9 and 24.

   Best over all of them: 116, from a group of order 9. None reached 115, let
   alone beat it. So the witness's cyclic C6 remains the only symmetry of any
   kind found that attains the optimum.

7. LNS WITH EXACT SUB-SOLVES, which is the one that carries weight. Freeze a
   random subset of the 115-leaf witness, let CP-SAT choose everything else
   optimally, repeat with a fresh frozen set each round. Every neighbourhood
   is explored by an exact solver rather than by a heuristic, and the frozen
   set changes constantly, so the walk passes through asymmetric
   configurations no orbit model can express.

       freeing 25-55 leaves:   3,336 rounds, zero improvements
       freeing 60-110 leaves:      94 rounds, zero improvements

   The second row is the calibration built into the method. Freeing 110 of
   115 leaves and re-optimising exactly is very nearly a fresh solve of the
   whole problem, and it returns 115 every time. This is not a heuristic
   failing to find something; it is an exact solver, run 3,430 times on
   overlapping neighbourhoods, never finding a 114.

   One honest limit: each sub-solve has a 25-second budget, so a round that
   finds nothing has not PROVED its neighbourhood empty. Failure means "did
   not find a 114 here in 25 seconds", not "no 114 exists here".

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

WHERE THAT LEAVES THINGS. Eight methods, no movement. The constraint side
provably cannot pass 110 -- gq_tight_case_is_an_m_ovoid.py shows the diagonal
always admits the trivial (s+1)-ovoid, so no counting argument of that kind
reaches further -- and the symmetry side has now been swept over cyclic AND non-cyclic classes,
with only the witness's own C6 reaching 115. The remaining possibilities are an
asymmetric 114-leaf blocker that no local search has found, or a proof at
111-114 that is not a counting argument. tau_2(W(3,3)^2) stays open in
[111, 115].
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
    {"method": "row-weighting local search, cold starts",
     "budgetMinutes": 20, "result": "failed its own calibration at 121",
     "lowerBound": None, "verdict": "no solution found"},
    {"method": "LNS with exact CP-SAT sub-solves, small neighbourhoods "
               "(25-55 of 115 leaves freed)",
     "budgetMinutes": 25, "result": "3336 rounds, 0 improvements, final 115",
     "lowerBound": None, "verdict": "no improvement"},
    {"method": "LNS with exact CP-SAT sub-solves, large neighbourhoods "
               "(60-110 of 115 leaves freed)",
     "budgetMinutes": 25, "result": "94 rounds, 0 improvements, final 115",
     "lowerBound": None, "verdict": "no improvement"},
    {"method": "NON-CYCLIC symmetry classes from commuting pairs "
               "(orders 4, 8, 9, 24)",
     "budgetMinutes": 20,
     "result": "512 pairs, 9 distinct classes, best 116",
     "lowerBound": None, "verdict": "no improvement"},
]

CONTROL = [
    {"target": 116, "starts": "pure random", "budgetMinutes": 7,
     "knownFeasible": True, "bestUncovered": 33, "solved": False},
    {"target": 115, "starts": "pure random", "budgetMinutes": 7,
     "knownFeasible": True, "bestUncovered": 41, "solved": False},
]


def main():
    print("EIGHT ATTACKS ON THE GAP, AND ONE CONTROL")
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
    print("  What survives: the witness is LOCALLY ISOLATED, and 3,430 exact")
    print("  LNS rounds -- including 94 that re-optimised 60 to 110 of the")
    print("  115 leaves -- never found a 114 either. Each sub-solve had a")
    print("  25-second budget, so no neighbourhood is PROVED empty.")
    print()
    print("  Eight methods, no movement. The constraint side provably cannot")
    print("  pass 110; the symmetry side is now swept over cyclic AND")
    print("  non-cyclic classes, and only the witness's own C6 reaches 115.")
    print("  What remains is an asymmetric witness no local search has found,")
    print("  or a proof that is not a counting argument.")

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
                "nonCyclicGapClosed": ("the cyclic sweep's stated boundary is "
                                       "now covered: 9 non-cyclic classes of "
                                       "orders 4, 8, 9 and 24, best 116"),
                "whatSurvives": ("the 115-leaf witness is locally isolated: "
                                 "removing one leaf and repairing by single "
                                 "swaps stalls six tiles short of 114; and "
                                 "3,430 LNS rounds with exact CP-SAT "
                                 "sub-solves, including 94 that re-optimised "
                                 "60 to 110 of the 115 leaves, never found a "
                                 "114"),
                "lnsCaveat": ("each LNS sub-solve had a 25-second budget, so a "
                              "round finding nothing has not proved its "
                              "neighbourhood empty"),
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
