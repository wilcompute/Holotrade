#!/usr/bin/env python3
"""
The corpus disagrees with itself about the single most-quoted number in it.
Twenty-two files say tau_2 is open in [110, 115], six more quote that
alongside the current figure, and fifty-six say [111, 115].
The second is right, and the reason the first exists is worth recording.

HOW IT HAPPENED, and neither side was careless.

  * Holotrade ran a long campaign against tau_2 = 110 and never closed it.
    tensor_110_no_local_obstruction.py states the outcome plainly: NINE
    formulations, "every one returned UNKNOWN, or was killed before its budget
    expired. Not one returned INFEASIBLE." Files written from inside that
    campaign correctly recorded [110, 115].

  * W33-Theory proved tau_2 != 110 separately, in commit 43049db with
    certificate 1513d61, by the centre argument: at |X| = 110 every row AND
    column shadow is a minimum blocker, hence has a centre, and a minimum
    blocker meets the four lines through its centre twice and every other line
    once. Four Holotrade files already cite that proof by name --
    gq24_tight_obstruction.py, gq_diagonal_theorem.py, gq_tight_case_theorem.py
    and structure_injection_cannot_reprove_110.py, the last of which is
    literally about being unable to REPROVE it locally.

So both records are honest reports of what their own track could see. Only one
of them is current. The cross-track proof supersedes the local non-result, and
the certified interval is

    tau_2(W(3,3)^2) in [111, 115],   110 EXCLUDED.

This file scans the repository and reports which files carry which, so the
disagreement is visible instead of being rediscovered a third time.

WHY IT MATTERS MORE THAN A TYPO.  The whole composition-tax reading of this
thread depends on it. tau*(W) tau(W) = 10 x 11 = 110 is the shadow bound, so
if tau_2 were 110 the tax would be ZERO and W(3,3)^2 would compose for free,
exactly like the ovoid-bearing cases in the tower law. The tax exists precisely
because 110 is excluded. A stale [110, 115] does not weaken a claim by one; it
leaves the central claim of the thread formally unsupported.

AND A TENTH FORMULATION, for the record. With the minimum blockers now
parametrized (c391663), the natural lean model at 111 -- every row and column
shadow forced to block and to have size at least 11, with the shadow sizes
capped globally by 4|X| on each side -- returns UNKNOWN, not INFEASIBLE. The
360-blocker table adds nothing to it: a shadow that blocks every line AND has
size exactly 11 is already one of the 360, so the table is logically redundant
in a feasibility model. The parametrization's value is for enumeration, which
is the other horn of that file's dichotomy.

SCOPE.  The scan is over analysis/, data/ and research/ in this repository. The
proof that 110 is excluded is W33-Theory's, cited not reproduced. The UNKNOWN
at 111 is a solver outcome, not evidence either way. tau_2 stays open in
[111, 115].
"""

import json
import os
import re
import sys

ROOT = r"C:\Repos\Holotrade"
STALE = re.compile(r"\[110,\s*115\]")
CURRENT = re.compile(r"\[111,\s*115\]")


def main():
    stale, current, both = [], [], []
    for sub in ("analysis", "data", "research"):
        d = os.path.join(ROOT, sub)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if not fn.endswith((".py", ".json", ".md")):
                continue
            p = os.path.join(d, fn)
            try:
                with open(p, encoding="utf-8", errors="ignore") as fh:
                    t = fh.read()
            except OSError:
                continue
            s, c = bool(STALE.search(t)), bool(CURRENT.search(t))
            rel = "%s/%s" % (sub, fn)
            if s and c:
                both.append(rel)
            elif s:
                stale.append(rel)
            elif c:
                current.append(rel)

    print("THE tau_2 INTERVAL IS [111, 115], AND THE CORPUS DISAGREES")
    print("=" * 72)
    print("  files asserting the SUPERSEDED [110, 115] only : %d" % len(stale))
    print("  files asserting the CURRENT    [111, 115] only : %d" % len(current))
    print("  files carrying BOTH (quoting prior art)        : %d" % len(both))
    print()
    print("  the stale ones:")
    for f in stale:
        print("     %s" % f)
    print()
    print("  RESOLUTION. W33-Theory proved tau_2 != 110 in commit 43049db")
    print("  (certificate 1513d61) by the centre argument, and four Holotrade")
    print("  files already cite it: gq24_tight_obstruction.py,")
    print("  gq_diagonal_theorem.py, gq_tight_case_theorem.py, and")
    print("  structure_injection_cannot_reprove_110.py -- the last of which is")
    print("  about being unable to REPROVE it locally. Holotrade's own nine")
    print("  formulations never returned INFEASIBLE at 110, which is why files")
    print("  written from inside that campaign kept [110, 115]. Both records")
    print("  are honest; only one is current.")
    print()
    print("  WHY IT MATTERS. tau*(W) tau(W) = 10 x 11 = 110 is the shadow")
    print("  bound, so if tau_2 were 110 the composition tax would be ZERO and")
    print("  W(3,3)^2 would compose for free like the ovoid-bearing cases in")
    print("  the tower law. The tax exists precisely because 110 is excluded.")
    print()
    print("  A TENTH FORMULATION, for the record: the lean model at 111 --")
    print("  every row and column shadow forced to block and to have size >= 11,")
    print("  with shadow sizes capped globally by 4|X| per side -- returns")
    print("  UNKNOWN. The 360-blocker table adds nothing, since a shadow that")
    print("  blocks and has size exactly 11 IS one of the 360.")

    ok = len(stale) > 0 and len(current) > 0

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data",
                         "the_tau2_interval_is_111_not_110.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.tau2-interval-reconciliation.v1",
                "valid": bool(ok),
                "certifiedInterval": [111, 115],
                "excluded": 110,
                "scan": {"staleOnly": stale, "currentOnly": current,
                         "both": both,
                         "staleCount": len(stale),
                         "currentCount": len(current),
                         "bothCount": len(both)},
                "resolution": {
                    "proof": ("W33-Theory commit 43049db, certificate 1513d61, "
                              "by the centre argument: at |X| = 110 every row "
                              "and column shadow is a minimum blocker, hence "
                              "has a centre, and a minimum blocker meets the "
                              "four lines through its centre twice and every "
                              "other line once"),
                    "citedInHolotradeBy": [
                        "gq24_tight_obstruction.py",
                        "gq_diagonal_theorem.py",
                        "gq_tight_case_theorem.py",
                        "structure_injection_cannot_reprove_110.py",
                    ],
                    "whyTheStaleFilesExist": ("Holotrade's own nine "
                                              "formulations against 110 never "
                                              "returned INFEASIBLE, as "
                                              "tensor_110_no_local_obstruction"
                                              ".py records, so files written "
                                              "from inside that campaign "
                                              "correctly reported [110, 115]"),
                    "verdict": ("both records are honest reports of what their "
                                "own track could see; the cross-track proof "
                                "supersedes the local non-result"),
                },
                "whyItMatters": ("tau*(W) tau(W) = 10 x 11 = 110 is the shadow "
                                 "bound, so if tau_2 were 110 the composition "
                                 "tax would be zero and W(3,3)^2 would compose "
                                 "for free like the ovoid-bearing cases in the "
                                 "tower law; the tax exists precisely because "
                                 "110 is excluded, so a stale interval leaves "
                                 "the thread's central claim unsupported rather "
                                 "than merely off by one"),
                "tenthFormulation": {
                    "model": ("every row and column shadow forced to block and "
                              "to have size at least 11, with shadow sizes "
                              "capped globally by 4|X| on each side"),
                    "target": 111,
                    "result": "UNKNOWN",
                    "tableIsRedundant": ("a shadow that blocks every line and "
                                         "has size exactly 11 is already one of "
                                         "the 360, so the parametrization adds "
                                         "nothing to a feasibility model -- its "
                                         "value is for enumeration, the other "
                                         "horn of the dichotomy"),
                },
                "boundary": ("the scan covers analysis/, data/ and research/ in "
                             "this repository; the proof that 110 is excluded "
                             "is W33-Theory's, cited not reproduced; the "
                             "UNKNOWN at 111 is a solver outcome and not "
                             "evidence either way. tau_2 stays open in "
                             "[111, 115]"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
