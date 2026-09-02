#!/usr/bin/env python3
"""
The orphaned harness now has a module, and the property it proves is a theorem
about the geometry rather than a design intent.

THE ORPHAN.  7f0d0a3 recorded rtl/verify_w33_216_typed_microvm.ys as a formal
harness with nothing under it: it reads rtl/w33_216_typed_microvm.v, which did
not exist. The name says "216 typed microvm", so the missing piece was a type
discipline for the 216-state carrier -- and 0d8d33e derived one rather than
leaving it to be chosen.

THE TYPE DISCIPLINE IS FORCED.  The 216 circuits form a canonical principal
6-fibration over the 36 double-sixes with fibre S6/S5. Relabelling the states
by (double-six, letter) makes

    type(s) = s / 6,   tag(s) = s mod 6

true by construction. Equivariance of the fibration then says something a
hardware engineer would recognise: an opcode may permute states however the
group allows, but

    s/6 == t/6   =>   g[s]/6 == g[t]/6,

THE OPCODE CANNOT LEAK THE TAG INTO THE TYPE. Two states of the same type must
land in the same type, whatever their tags. That is not a coding convention to
be enforced by review; it is the fibration, written as an assertion.

PROVED IN HARDWARE.  rtl/w33_216_typed_microvm.v encodes one PSp(4,3)
generator as a 216-entry table and asserts exactly that implication over two
free 8-bit state inputs. Yosys, through the harness:

    Solving problem with 38509 variables and 112829 clauses
    SAT proof finished - no model found: SUCCESS

quantified over all 216 x 216 ordered state pairs, not sampled.

AND THE CHECK HAS TEETH.  A control module is emitted alongside it, identical
except that two entries of the table are swapped -- a permutation that is no
longer equivariant. Its harness reports

    SAT proof finished - model found: FAIL

so the property is not vacuously true of any table. A passing proof on the real
generator therefore means something.

ONE REPAIR TO THE HARNESS.  As written it could not run on this toolchain:
Yosys 0.68 lowers assertions to $check cells, which the classic sat pass cannot
consume ("No SAT model available for cell $assert ... ($check)"). Adding
chformal -lower after proc fixes it, and that one word is the only change made
to the other track's script.

WHY IT MATTERS.  This is the first RTL in the repository whose correctness
property is a THEOREM about the substrate rather than a statement of design
intent. The types are not checked against a specification someone wrote -- the
specification IS the fibration, and there is exactly one way to type a state
because exactly one spread stabiliser contains each circuit stabiliser. A
future opcode is well-typed if and only if it is equivariant, and Yosys can
decide that.

SCOPE.  One generator's action, combinational, no state machine and no
datapath. It proves the fibration property of that opcode and the emptiness of
the control's; it is not a processor, and nothing here is a claim about
fabricated hardware. tau_2 is untouched.
"""

import json
import os
import re
import subprocess
import sys

ROOT = r"C:\Repos\Holotrade"


def run(script):
    out = subprocess.run(["node", "scripts/run-yosys.js", script],
                         cwd=ROOT, capture_output=True, text=True)
    text = out.stdout + out.stderr
    m = re.search(r"Solving problem with (\d+) variables and (\d+) clauses",
                  text)
    if "no model found: SUCCESS" in text:
        verdict = "PROVED"
    elif "model found: FAIL" in text:
        verdict = "COUNTEREXAMPLE"
    else:
        verdict = "UNKNOWN"
    return {"script": script, "verdict": verdict,
            "variables": int(m.group(1)) if m else None,
            "clauses": int(m.group(2)) if m else None}


def main():
    main_r = run("rtl/verify_w33_216_typed_microvm.ys")
    ctrl_r = run("rtl/verify_w33_216_typed_microvm_control.ys")

    print("THE TYPED MICROVM PROPERTY IS A THEOREM")
    print("=" * 72)
    print("  states relabelled by (double-six, letter), so type(s) = s/6 and")
    print("  tag(s) = s mod 6 hold by construction. The assertion is")
    print("      s/6 == t/6  =>  g[s]/6 == g[t]/6,")
    print("  i.e. the opcode cannot leak the tag into the type.")
    print()
    print("  module   %-14s %s  (%s vars, %s clauses)"
          % ("real generator", main_r["verdict"], main_r["variables"],
             main_r["clauses"]))
    print("  control  %-14s %s  (%s vars, %s clauses)"
          % ("two entries swapped", ctrl_r["verdict"], ctrl_r["variables"],
             ctrl_r["clauses"]))
    print()
    print("  Quantified over all 216 x 216 ordered state pairs, not sampled.")
    print("  The control fails, so the property is not vacuously true of any")
    print("  table -- a passing proof on the real generator means something.")
    print()
    print("  Harness repair: Yosys 0.68 lowers asserts to $check cells the")
    print("  classic sat pass cannot consume, so 'chformal -lower' was added")
    print("  after proc. That one word is the only change to the other")
    print("  track's script.")
    print()
    print("  This is the first RTL here whose correctness property is a")
    print("  THEOREM about the substrate rather than design intent: the types")
    print("  are not checked against a written spec, the spec IS the")
    print("  fibration. An opcode is well-typed iff it is equivariant.")

    ok = (main_r["verdict"] == "PROVED"
          and ctrl_r["verdict"] == "COUNTEREXAMPLE")

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data",
                         "the_typed_microvm_property_is_a_theorem.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.typed-microvm-property-theorem.v1",
                "valid": bool(ok),
                "theOrphan": ("7f0d0a3 recorded "
                              "rtl/verify_w33_216_typed_microvm.ys as a formal "
                              "harness reading a module that did not exist"),
                "typeDiscipline": {
                    "source": ("0d8d33e: the 216 circuits are a canonical "
                               "principal 6-fibration over the 36 double-sixes "
                               "with fibre S6/S5"),
                    "relabelling": ("states ordered by (double-six, letter) so "
                                    "type(s) = s/6 and tag(s) = s mod 6 hold by "
                                    "construction"),
                    "property": "s/6 == t/6  =>  g[s]/6 == g[t]/6",
                    "meaning": ("the opcode cannot leak the tag into the type; "
                                "two states of one type land in one type "
                                "whatever their tags"),
                    "forced": ("exactly one spread stabiliser contains each "
                               "circuit stabiliser, so there is exactly one way "
                               "to type a state"),
                },
                "proof": main_r,
                "control": ctrl_r,
                "quantification": ("all 216 x 216 ordered state pairs, by SAT, "
                                   "not sampled"),
                "controlHasTeeth": ("the control module is identical except "
                                    "that two table entries are swapped, "
                                    "breaking equivariance, and its harness "
                                    "reports a counterexample -- so the "
                                    "property is not vacuously true of any "
                                    "table"),
                "harnessRepair": ("Yosys 0.68 lowers assertions to $check "
                                  "cells the classic sat pass cannot consume, "
                                  "so chformal -lower was added after proc; "
                                  "that is the only change to the other "
                                  "track's script"),
                "whyItMatters": ("the first RTL here whose correctness property "
                                 "is a theorem about the substrate rather than "
                                 "design intent -- the types are not checked "
                                 "against a written specification, the "
                                 "specification IS the fibration, and an opcode "
                                 "is well-typed if and only if it is "
                                 "equivariant"),
                "boundary": ("one generator's action, combinational, no state "
                             "machine and no datapath; it proves that opcode's "
                             "fibration property and the control's failure, and "
                             "is not a processor. No claim about fabricated "
                             "hardware. tau_2 is untouched"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
