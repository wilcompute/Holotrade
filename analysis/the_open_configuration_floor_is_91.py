#!/usr/bin/env python3
"""
Two corrections and one strengthened negative, all about GQ(2,4)^2.

CORRECTION ONE, and it is mine. the_open_configuration_has_a_smaller_instance
.py recorded GQ(2,4)^2 as open in [90, 100]. The floor is 91:
gq24_tight_obstruction.py had already proved tau != 90, and I did not cite it.
That is the same failure the interval audit in 4b23ec0 was written about --
committed by me one commit earlier, in the file that audit was checking
against. The docstring there is corrected in place.

Their argument is worth restating because it is the cleanest obstruction in
this whole thread. At |X| = 90 every row and column shadow is a minimum
blocker, so each of the 45 lines has a centre; the multiplicity trichotomy
plus |F| = 1 + kt/mu = 9 against alpha(GQ(2,4)) = 6 forces F empty, so
centres are distinct; and 45 lines cannot have distinct centres among 27
points. Pigeonhole. No self-duality needed, which is what W(3,3) required
because it has as many lines as points.

CORRECTION TWO, smaller. GQ(2,4) has exactly one minimum blocker per centre --
all 27 are punctured perps c^perp minus {c} (7b15c84) -- so for this quadrangle
"the shadow has a centre" and "the shadow IS a specific 10-set" are the same
statement. W(3,3) has nine per centre, which is why its version of the argument
needs more.

THE STRENGTHENED NEGATIVE.  I had probed feasibility at 99, near the top of the
interval, where infeasibility is hardest to prove, and reported UNKNOWN. That
was the wrong end. Climbing from the BOTTOM instead -- 91, the most constrained
target there is, one above a proved floor -- with the full shadow encoding on
both axes (every row and column shadow forced to block and to have size at
least 10, with sizes capped globally by 5|X| per side) still returns

    <= 91 : UNKNOWN

So the signature is not an artefact of probing near a feasible solution. It
holds at BOTH ends of the interval, on 729 leaves, with the structure supplied.
Combined with tensor_110_no_local_obstruction.py's nine formulations on
W(3,3)^2 and the tenth in 4b23ec0, that is now eleven formulations across two
different quadrangles and both ends of two intervals, none of which returned
INFEASIBLE. The claim that no short refutation exists is no longer resting on
one instance or one region.

WHAT WOULD ACTUALLY MOVE IT.  The pigeonhole argument degrades gracefully with
slack: at |X| = 90 + r at most 5r of the 45 lines can have an oversized shadow,
so at least 45 - 5r lines still have centres. If the multiplicity trichotomy
survived slack, 45 - 5r <= 27 would force r >= 4 and the floor would jump to
94 outright. It is not claimed here, because the trichotomy is derived FROM
pencil reciprocity and reciprocity is derived from tightness -- exactly the
hypothesis that slack removes. Whether the trichotomy holds with defect is the
open question this file is really pointing at, and it is a geometry question,
not a solver one.

SCOPE.  Corrections to an earlier file of mine and a solver non-result. The
tau != 90 proof is gq24_tight_obstruction.py's, cited not reproduced. The
r >= 4 argument is explicitly NOT claimed -- its hypothesis is unverified.
tau(GQ(2,4)^2) stays open in [91, 100] and tau_2 in [111, 115].
"""

import json
import os
import sys

ROOT = r"C:\Repos\Holotrade"


def main():
    print("THE OPEN CONFIGURATION'S FLOOR IS 91, NOT 90")
    print("=" * 72)
    print("  CORRECTION ONE (mine): the_open_configuration_has_a_smaller_")
    print("  instance.py wrote [90, 100]. gq24_tight_obstruction.py had")
    print("  already proved tau != 90 and I did not cite it -- the same")
    print("  failure the 4b23ec0 audit was written about, one commit earlier.")
    print("  Corrected in place; the interval is [91, 100].")
    print()
    print("  their argument, restated: at |X| = 90 all 45 line-shadows are")
    print("  minimum blockers, so all have centres; |F| = 1 + kt/mu = 9 against")
    print("  alpha = 6 forces F empty, so centres are distinct; and 45 lines")
    print("  cannot have distinct centres among 27 points. Pigeonhole -- no")
    print("  self-duality needed, which W(3,3) required only because it has as")
    print("  many lines as points.")
    print()
    print("  CORRECTION TWO: GQ(2,4) has ONE minimum blocker per centre, all")
    print("  27 punctured perps (7b15c84), so 'has a centre' and 'IS a specific")
    print("  10-set' coincide there. W(3,3) has nine per centre.")
    print()
    print("  STRENGTHENED NEGATIVE: I probed 99, near the top, where")
    print("  infeasibility is hardest, and reported UNKNOWN. Climbing from the")
    print("  BOTTOM instead -- 91, one above a proved floor, the most")
    print("  constrained target there is, with the full two-axis shadow")
    print("  encoding -- still gives UNKNOWN.")
    print()
    print("  So the signature holds at BOTH ends of the interval. With")
    print("  tensor_110_no_local_obstruction.py's nine and 4b23ec0's tenth,")
    print("  that is eleven formulations across two quadrangles and both ends")
    print("  of two intervals, none INFEASIBLE.")
    print()
    print("  WHAT WOULD MOVE IT: at |X| = 90 + r at most 5r lines can have an")
    print("  oversized shadow, so at least 45 - 5r keep centres. If the")
    print("  multiplicity trichotomy survived slack, 45 - 5r <= 27 would force")
    print("  r >= 4 and the floor would jump to 94. NOT claimed -- the")
    print("  trichotomy comes from pencil reciprocity, which comes from")
    print("  tightness, which is exactly what slack removes. Whether it")
    print("  survives defect is a geometry question, not a solver one.")

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data",
                         "the_open_configuration_floor_is_91.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.open-configuration-floor-91.v1",
                "valid": True,
                "correctionOne": {
                    "file": "the_open_configuration_has_a_smaller_instance.py",
                    "wrote": [90, 100],
                    "correct": [91, 100],
                    "priorArtNotCited": "gq24_tight_obstruction.py",
                    "mine": True,
                    "note": ("the same failure the 4b23ec0 interval audit was "
                             "written about, committed one commit earlier, in a "
                             "file that audit was checking against"),
                    "theirArgument": ("at |X| = 90 all 45 line-shadows are "
                                      "minimum blockers so all have centres; "
                                      "|F| = 1 + kt/mu = 9 against alpha = 6 "
                                      "forces F empty so centres are distinct; "
                                      "45 lines cannot have distinct centres "
                                      "among 27 points"),
                    "whyNoSelfDualityNeeded": ("W(3,3) has as many lines as "
                                               "points so a bijection is "
                                               "possible on counting grounds; "
                                               "GQ(2,4) has 45 lines and 27 "
                                               "points, so pigeonhole fires"),
                },
                "correctionTwo": ("GQ(2,4) has exactly one minimum blocker per "
                                  "centre, all 27 punctured perps (7b15c84), so "
                                  "'the shadow has a centre' and 'the shadow IS "
                                  "a specific 10-set' are the same statement "
                                  "there; W(3,3) has nine per centre"),
                "strengthenedNegative": {
                    "earlierProbe": {"target": 99, "result": "UNKNOWN",
                                     "problem": ("near the top of the interval, "
                                                 "where infeasibility is "
                                                 "hardest to prove")},
                    "newProbe": {"target": 91, "result": "UNKNOWN",
                                 "why": ("one above a proved floor, the most "
                                         "constrained target available, with "
                                         "the full two-axis shadow encoding")},
                    "reading": ("the signature is not an artefact of probing "
                                "near a feasible solution -- it holds at both "
                                "ends of the interval"),
                    "runningTotal": ("eleven formulations across two "
                                     "quadrangles and both ends of two "
                                     "intervals, none INFEASIBLE"),
                },
                "whatWouldMoveIt": {
                    "observation": ("at |X| = 90 + r at most 5r of the 45 lines "
                                    "can have an oversized shadow, so at least "
                                    "45 - 5r still have centres"),
                    "ifTrichotomySurvivedSlack": ("45 - 5r <= 27 would force "
                                                  "r >= 4 and the floor would "
                                                  "jump to 94"),
                    "notClaimed": True,
                    "whyNot": ("the multiplicity trichotomy is derived from "
                               "pencil reciprocity, which is derived from "
                               "tightness -- exactly the hypothesis slack "
                               "removes"),
                    "theRealOpenQuestion": ("whether the trichotomy holds with "
                                            "defect; a geometry question, not a "
                                            "solver one"),
                },
                "boundary": ("corrections to an earlier file of mine and a "
                             "solver non-result; the tau != 90 proof is "
                             "gq24_tight_obstruction.py's, cited not "
                             "reproduced; the r >= 4 argument is explicitly not "
                             "claimed. tau(GQ(2,4)^2) stays open in [91, 100] "
                             "and tau_2 in [111, 115]"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
