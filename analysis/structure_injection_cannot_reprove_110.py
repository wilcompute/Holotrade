#!/usr/bin/env python3
"""
Handing the solver the entire local structure still does not reprove 110 --
so the structural-injection route is closed, and the control says why.

THE IDEA, which was the strongest one left.  Every previous model gave the
solver constraints. This one gives it the THEORY. The conservation law
F + D = (t+1)r (tensor_excess_conservation_law.py) says that at |X| = 110 + r
only 4r units of slack exist in total, split between blocker excess and column
dependence. Two consequences are far stronger than any inequality:

  * at most 4r lines can have a non-minimum row shadow, so every other row
    shadow is literally one of the 360 KNOWN minimum blockers of W(3,3) --
    not an arbitrary 40-bit set;
  * at most 4r column classes can be dependent, so every other C_q meets each
    line at most once and has at most alpha = 7 points.

The model states both. A selector picks which of the 360 blockers each minimal
line carries, channelled leaf-by-leaf to x[p][q], with the count of exceptions
bounded by the law. At r = 0 that is maximally rigid: all 40 shadows must be
among the 360, and all 40 column classes must be independent.

THE CONTROL, and it is the whole result.  Before asking this model about 111 --
where nobody knows the answer -- ask it about 110, where the answer is KNOWN.
W33-Theory proved tau_2 != 110 by the self-duality argument, so the correct
verdict is INFEASIBLE.

    |X| = 110, structure injected, 5 minutes   ->  UNKNOWN
    |X| = 110, structure injected, 45 minutes  ->  UNKNOWN

It cannot reprove a theorem we already have, in the most constrained instance
the model admits.

WHY THAT KILLS THE ROUTE.  An UNKNOWN at 111 would then carry no information
whatsoever -- the model returns UNKNOWN on a case it should close. Only an
INFEASIBLE would have meant anything, and the control shows the model cannot
produce one even when the answer is known and the slack is zero. So running
it at 111 is not worth the machine time, and reading anything into its silence
would be an error.

WHAT IT SHARPENS.  tensor_110_no_local_obstruction.py established that nine
formulations returned UNKNOWN rather than INFEASIBLE, and concluded that any
refutation of the tight case had to be GLOBAL. That prediction was borne out
when the refutation arrived as a self-duality argument.

This is the same conclusion one level stronger. It is no longer that solvers
had not been given enough. They have now been given everything the theory
knows about the tight case -- the exact identity of every row shadow, the
independence of every column class -- and a solver still cannot close an
instance whose answer is a published theorem. The self-duality step was not
one route among several; it is doing work no amount of local structure
substitutes for.

SCOPE.  A negative result about a method, not about tau_2. It does not move
any bound, and it does not show that no structured encoding could work -- only
that this one, which injects everything the conservation law forces, does not.
tau_2(W(3,3)^2) stays open in [111, 115].
"""

import json
import os
import sys

ROOT = r"C:\Repos\Holotrade"

RUNS = [
    {"target": 110, "r": 0, "slack": 0, "budgetMinutes": 5,
     "status": "UNKNOWN", "knownAnswer": "INFEASIBLE",
     "reprovedKnownAnswer": False},
    {"target": 110, "r": 0, "slack": 0, "budgetMinutes": 45,
     "status": "UNKNOWN", "knownAnswer": "INFEASIBLE",
     "reprovedKnownAnswer": False},
]


def main():
    print("STRUCTURE INJECTION CANNOT REPROVE 110")
    print("=" * 72)
    print("  The model gives the solver the THEORY, not just constraints:")
    print("    * every minimal row shadow must be one of the 360 KNOWN")
    print("      minimum blockers, chosen by a selector and channelled to the")
    print("      leaf variables;")
    print("    * every independent column class meets each line at most once")
    print("      and has at most alpha = 7 points;")
    print("    * the number of exceptions to each is bounded by the")
    print("      conservation law F + D = 4r.")
    print()
    print("  At r = 0 that is maximally rigid -- all 40 shadows among the 360,")
    print("  all 40 column classes independent -- and 110 is KNOWN infeasible")
    print("  by the self-duality theorem. So the model should close it.")
    print()
    for run in RUNS:
        print("     |X| = %d, slack %d, %2d minutes -> %s   (known: %s)"
              % (run["target"], run["slack"], run["budgetMinutes"],
                 run["status"], run["knownAnswer"]))
    print()
    print("  It does not. And an UNKNOWN at 111 would therefore mean nothing,")
    print("  since the model returns UNKNOWN on a case it should close. Only")
    print("  an INFEASIBLE would have carried information, and the control")
    print("  shows it cannot produce one. The route is closed.")
    print()
    print("  This sharpens the no-local-obstruction result by one level. It is")
    print("  not that solvers had not been given enough -- they have now been")
    print("  handed the exact identity of every row shadow and the")
    print("  independence of every column class, and still cannot close an")
    print("  instance whose answer is a published theorem.")

    ok = all(not r["reprovedKnownAnswer"] for r in RUNS)
    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data",
                         "structure_injection_cannot_reprove_110.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.structure-injection-control.v1",
                "valid": True,
                "isNegativeMethodResult": True,
                "model": ("selector forcing each minimal row shadow to be one "
                          "of the 360 known minimum blockers, channelled to "
                          "the leaf variables, plus per-column independence "
                          "indicators, with exception counts bounded by "
                          "F + D = 4r"),
                "runs": RUNS,
                "controlFailed": bool(ok),
                "whyRouteIsClosed": ("the model cannot reprove the known "
                                     "infeasibility at 110 in its most "
                                     "constrained instance, so an UNKNOWN at "
                                     "111 would carry no information and only "
                                     "an INFEASIBLE would -- which it cannot "
                                     "produce"),
                "sharpens": ("tensor_110_no_local_obstruction.py concluded any "
                             "refutation had to be global; this shows solvers "
                             "given the full local structure still cannot "
                             "close an instance whose answer is a theorem"),
                "boundary": ("a negative result about a method, not about "
                             "tau_2; it moves no bound and does not show that "
                             "no structured encoding could work, only that "
                             "this one does not. tau_2 stays open in "
                             "[111, 115]."),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
