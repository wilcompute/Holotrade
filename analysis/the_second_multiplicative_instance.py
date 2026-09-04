#!/usr/bin/env python3
"""
Correcting an over-read in 48e1841, and adding the second confirmed
multiplicative instance to the corpus's table: GQ(4,2), tau_2 = 81.

THE OVER-READ.  48e1841 closed with "the OVOID is what prevents compression,
and tau_2 measures what the missing ovoid buys". Read generally that is the
CONVERSE of the corpus's theorem, and data/tensor_multiplicativity_ovoid_defect
.json explicitly marks it unproved:

    theorem          "an ovoid is SUFFICIENT for multiplicativity: delta = 0
                      collapses the shadow lower bound (st+1)*tau_1 onto the
                      product upper bound tau_1^2, so tau_2 = tau_1^2"
    converseProved   false
    converseBoundary "delta > 0 opens a gap between the generic bounds but does
                      not by itself imply tau_2 < tau_1^2"

So the correct statement is one-directional. Having an ovoid FORCES
multiplicativity. Lacking one merely OPENS a gap of width tau_1 * delta between
the two generic bounds -- it does not compel the true value to fall below the
square. What 48e1841 could legitimately say, and what stands, is the INSTANCE:
W(3,3) has delta = 1 and tau_2 <= 115 < 121 = tau_1^2, so W(3,3) in particular
does compress. That is a fact about W(3,3), not a law about defect.

WHAT IS GENUINELY NEW: A SECOND INSTANCE.  That certificate's table had exactly
one confirmed multiplicative row -- GQ(2,2) = W(3,2), at q even -- and one
undecided row, W(3,3). 48e1841 established tau_1(GQ(4,2)) = 9 = st + 1 with 200
ovoids, which is precisely the delta = 0 hypothesis, so the theorem applies and
the row completes itself:

    name             (s,t)   pts  lines  ovoid  tau_1  delta  shadow  product
    GQ(2,2)          (2,2)    15     15      5      5      0      25       25
    W(3,3)           (3,3)    40     40     10     11      1     110      121
    GQ(4,2)  NEW     (4,2)    45     27      9      9      0      81       81

    GQ(4,2):  interval width 0,  tau_2 = 81,  MULTIPLICATIVE

and the certificate's own width formula checks out on it:

    tau_1^2 - (st+1) tau_1 = 81 - 81 = 0 = tau_1 * delta = 9 * 0

WHY THE SECOND INSTANCE IS WORTH HAVING.  With one confirmed row the theorem
had one witness, and that witness was the small self-dual case at even q where a
great many things are degenerate. GQ(4,2) has different parameters, is not
self-dual, and its ovoids are not a classical accident of smallness -- there are
200 of them in two orbits. So the multiplicativity theorem now has a witness
that is not W(3,2), which is the difference between a theorem with an example
and a theorem with a pattern.

IT STILL DOES NOT TOUCH W(3,3).  The undecided row is undecided for the reason
the certificate gives: delta = 1 opens an interval of width tau_1 * delta = 11
between 110 and 121, and the true value sits in [111, 115] inside it. Adding a
delta = 0 instance says nothing about a delta = 1 one. tau_2 remains open.

SCOPE.  tau_1(GQ(4,2)) = 9 and its 200 ovoids are 48e1841 and 8982d36, cited.
The multiplicativity theorem and the width formula are
tensor_multiplicativity_ovoid_defect.json's, cited and APPLIED -- the new row is
a consequence of that theorem plus the delta = 0 input, not an independent
verification of tau_2(GQ(4,2)) = 81 by search. The arithmetic of the row is
recomputed here from the GQ parameters. No claim is made about the converse,
which remains unproved in the corpus and is not attempted here. tau_2 for
W(3,3) is untouched.
"""

import json
import os
import sys

ROOT = r"C:\Repos\Holotrade"


def row(name, s, t, tau1, has_ovoid, note=""):
    pts = (s + 1) * (s * t + 1)
    lines = (t + 1) * (s * t + 1)
    ovoid = s * t + 1
    delta = tau1 - ovoid
    shadow = ovoid * tau1
    prod = tau1 * tau1
    width = prod - shadow
    return {"name": name, "s": s, "t": t, "points": pts, "lines": lines,
            "ovoidSize": ovoid, "tau1": tau1, "ovoidDefect": delta,
            "hasOvoid": has_ovoid, "shadowLower": shadow, "productUpper": prod,
            "intervalWidth": width,
            "widthFormulaHolds": width == tau1 * delta,
            "tau2": prod if delta == 0 else None,
            "multiplicative": True if delta == 0 else None,
            "note": note}


def main():
    prior = os.path.join(ROOT, "data",
                         "tensor_multiplicativity_ovoid_defect.json")
    with open(prior) as fh:
        P = json.load(fh)
    converse_open = (P.get("converseProved") is False)

    rows = [
        row("GQ(2,2) = W(3,2), q even", 2, 2, 5, True,
            "the corpus's single confirmed row"),
        row("W(3,3), q odd -- no ovoid (Thas)", 3, 3, 11, False,
            "undecided; true value in [111,115] inside the width-11 interval"),
        row("GQ(4,2), the cost quadrangle", 4, 2, 9, True,
            "NEW: tau_1 = 9 = st+1 with 200 ovoids (48e1841, 8982d36)"),
    ]
    new = rows[-1]

    print("THE SECOND MULTIPLICATIVE INSTANCE")
    print("=" * 72)
    print("  CORRECTION to 48e1841, which said 'the OVOID is what prevents")
    print("  compression'. Read generally that is the CONVERSE, and the corpus")
    print("  marks it unproved:")
    print("     converseProved   %s" % P.get("converseProved"))
    print("     converseBoundary %s" % P.get("converseBoundary"))
    print()
    print("  The theorem is one-directional: having an ovoid FORCES")
    print("  multiplicativity; lacking one merely OPENS a gap of width")
    print("  tau_1 * delta. What stands from 48e1841 is the INSTANCE -- W(3,3)")
    print("  has delta = 1 and tau_2 <= 115 < 121, so W(3,3) in particular")
    print("  compresses. A fact about W(3,3), not a law about defect.")
    print()
    print("  name                        (s,t)  pts  lin  ov  t1  d  shad  prod")
    for r in rows:
        print("  %-26s (%d,%d) %4d %4d %3d %3d %2d %5d %5d"
              % (r["name"][:26], r["s"], r["t"], r["points"], r["lines"],
                 r["ovoidSize"], r["tau1"], r["ovoidDefect"],
                 r["shadowLower"], r["productUpper"]))
    print()
    print("  NEW ROW: GQ(4,2) has delta = %d, so the theorem applies:"
          % new["ovoidDefect"])
    print("     interval width %d, tau_2 = %d, MULTIPLICATIVE"
          % (new["intervalWidth"], new["tau2"]))
    print("     width formula tau_1^2 - (st+1)tau_1 = tau_1 * delta: %s"
          % new["widthFormulaHolds"])
    print()
    print("  The table had ONE confirmed multiplicative row, and it was the")
    print("  small self-dual case at even q where much is degenerate. GQ(4,2)")
    print("  has different parameters, is not self-dual, and its ovoids are no")
    print("  accident of smallness -- 200 of them in two orbits. The theorem")
    print("  now has a witness that is not W(3,2).")
    print()
    print("  It still says NOTHING about W(3,3): delta = 1 opens an interval of")
    print("  width tau_1 * delta = %d between %d and %d, and the true value sits"
          % (rows[1]["intervalWidth"], rows[1]["shadowLower"],
             rows[1]["productUpper"]))
    print("  in [111,115] inside it. Adding a delta = 0 instance decides no")
    print("  delta = 1 one. tau_2 remains open.")

    ok = (converse_open and all(r["widthFormulaHolds"] for r in rows)
          and new["ovoidDefect"] == 0 and new["tau2"] == 81
          and new["points"] == 45 and new["lines"] == 27
          and rows[1]["intervalWidth"] == 11
          and rows[1]["shadowLower"] == 110 and rows[1]["productUpper"] == 121)

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "second_multiplicative_instance.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.second-multiplicative-instance.v1",
                "valid": bool(ok),
                "correction": {
                    "of": "48e1841",
                    "whatItSaid": ("'the OVOID is what prevents compression, and "
                                   "tau_2 measures what the missing ovoid buys'"),
                    "whyItIsAnOverRead": ("read generally that is the CONVERSE of "
                                          "the corpus's theorem, and "
                                          "tensor_multiplicativity_ovoid_defect"
                                          ".json marks it unproved: "
                                          "converseProved = false, and delta > 0 "
                                          "'does not by itself imply "
                                          "tau_2 < tau_1^2'"),
                    "whatStands": ("the INSTANCE -- W(3,3) has delta = 1 and "
                                   "tau_2 <= 115 < 121 = tau_1^2, so W(3,3) in "
                                   "particular compresses; that is a fact about "
                                   "W(3,3), not a law about defect"),
                    "correctStatement": ("having an ovoid FORCES "
                                         "multiplicativity; lacking one merely "
                                         "OPENS a gap of width tau_1 * delta "
                                         "between the two generic bounds"),
                },
                "priorTheorem": {
                    "statement": P.get("theorem"),
                    "converseProved": P.get("converseProved"),
                    "converseBoundary": P.get("converseBoundary"),
                    "widthFormula": P.get("widthFormula"),
                    "source": "data/tensor_multiplicativity_ovoid_defect.json",
                },
                "table": rows,
                "newRow": new,
                "whyItMatters": ("the certificate's table had exactly ONE "
                                 "confirmed multiplicative row, GQ(2,2) = "
                                 "W(3,2), the small self-dual case at even q "
                                 "where a great deal is degenerate. GQ(4,2) has "
                                 "different parameters, is not self-dual, and "
                                 "its ovoids are not an accident of smallness -- "
                                 "200 of them in two orbits. The theorem now has "
                                 "a witness that is not W(3,2), which is the "
                                 "difference between a theorem with an example "
                                 "and a theorem with a pattern"),
                "itDoesNotTouchW33": ("the undecided row stays undecided for the "
                                      "reason the certificate gives: delta = 1 "
                                      "opens an interval of width tau_1 * delta "
                                      "= 11 between 110 and 121, with the true "
                                      "value in [111,115] inside it. Adding a "
                                      "delta = 0 instance decides no delta = 1 "
                                      "one"),
                "boundary": ("tau_1(GQ(4,2)) = 9 and its 200 ovoids are 48e1841 "
                             "and 8982d36, cited. The multiplicativity theorem "
                             "and width formula are the prior certificate's, "
                             "cited and APPLIED -- the new row is a consequence "
                             "of that theorem plus the delta = 0 input, NOT an "
                             "independent verification of tau_2(GQ(4,2)) = 81 by "
                             "search. The row arithmetic is recomputed here from "
                             "the GQ parameters. No claim about the converse, "
                             "which remains unproved in the corpus and is not "
                             "attempted here. tau_2 for W(3,3) is untouched"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
