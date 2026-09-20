#!/usr/bin/env python3
"""
THE FLAGSHIP'S ORDER-THREE WILSON LINE SITS IN THE THIRD GEOMETRIC PAIR -- ANSWERING THE
AMBIGUITY b4fa45c MADE EXPLICIT, FROM THE FILE THE SCAN ACTUALLY FED TO THE ORBIFOLDER.

w33_flagship_orbifolder_model.py (b4fa45c) notes that the historical analysis froze V and
W3 but not which of the three geometric pair slots W3 occupied, and offers --pair 01, 23
or 45; a5d42fd and 8937573 then set up a replay to decide it by exhaustion.

It does not have to be decided by exhaustion. The 5b3f3ad scan generated these models and
kept the orbifolder input files, so the slot is recorded, not inferred. The flagship model
file, label SM_20260917_3 in the Z6I_27 shift block, is reproduced verbatim below. In the
eight-row "Shifts and Wilsonlines" block -- two gauge shifts then six Wilson lines -- the
nonzero rows are the seventh and eighth, i.e. zero-based indices 6 and 7, which is exactly
the (6, 7) that b4fa45c maps to

    --pair 45

So the third pair carries it, and the replay needs one candidate rather than three (or six
with the geometry choice). The other two placements are not the recorded flagship.

WHAT THIS DOES AND DOES NOT SETTLE. It settles which input file produced the frozen
flagship spectrum, because that file is the input. It does not independently confirm that
the file is the physically intended model -- if the scan itself put W3 in the wrong slot,
this records the same mistake faithfully. The replay of a5d42fd is still worth running as
an external check against published orbifolder 1.2.1; what changes is that it can pin the
candidate first and use the others as controls, which is the cheaper experiment.

The geometry is likewise recorded rather than discovered: Geometry_Z6-I_G2xG2xSU3.txt.
"""

import argparse
import json
import os
from fractions import Fraction as F

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The orbifolder input file for the flagship, verbatim from the 5b3f3ad scan
# (sm/Z6I_27.txt, first model block).
MODEL_FILE = """begin model
Label:SM_20260917_3
SpaceGroup:Geometry/Geometry_Z6-I_G2xG2xSU3.txt
Lattice:E8xE8
Shifts and Wilsonlines:
    0,     0,     0,     0,   1/6,   1/6,   1/3,   2/3,     0,     0,     0,   1/6,   1/6,   1/6,   1/6,   2/3
    0,     0,     0,     0,     0,     0,     0,     0,     0,     0,     0,     0,     0,     0,     0,     0
    0,     0,     0,     0,     0,     0,     0,     0,     0,     0,     0,     0,     0,     0,     0,     0
    0,     0,     0,     0,     0,     0,     0,     0,     0,     0,     0,     0,     0,     0,     0,     0
    0,     0,     0,     0,     0,     0,     0,     0,     0,     0,     0,     0,     0,     0,     0,     0
    0,     0,     0,     0,     0,     0,     0,     0,     0,     0,     0,     0,     0,     0,     0,     0
 -7/6,  -5/6,  -1/6,   1/6,   1/2,   1/2,   7/6,  -1/6,  -4/3,  -2/3,   1/3,  -4/3,     0,   1/3,     1,   1/3
 -7/6,  -5/6,  -1/6,   1/6,   1/2,   1/2,   7/6,  -1/6,  -4/3,  -2/3,   1/3,  -4/3,     0,   1/3,     1,   1/3
end model
"""

# the frozen record, as carried in 5b3f3ad / d772153
FROZEN_V = "0,0,0,0,1/6,1/6,1/3,2/3,0,0,0,1/6,1/6,1/6,1/6,2/3"
FROZEN_W3 = "-7/6,-5/6,-1/6,1/6,1/2,1/2,7/6,-1/6,-4/3,-2/3,1/3,-4/3,0,1/3,1,1/3"

# b4fa45c's mapping from --pair to the two zero-based row indices it fills
PAIR_ROWS = {"01": (2, 3), "23": (4, 5), "45": (6, 7)}


def rows_of(text):
    body = text.split("Shifts and Wilsonlines:\n")[1].split("end model")[0]
    out = []
    for line in body.strip().splitlines():
        out.append(tuple(F(x.strip()) for x in line.split(",")))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    checks = {}

    rows = rows_of(MODEL_FILE)
    print("  rows in the shift/Wilson block: %d" % len(rows))
    checks["block_has_eight_rows"] = len(rows) == 8
    checks["every_row_has_sixteen_entries"] = all(len(r) == 16 for r in rows)

    zero = tuple(F(0) for _ in range(16))
    nonzero = [i for i, r in enumerate(rows) if r != zero]
    print("  nonzero rows (zero-based): %s" % nonzero)
    checks["exactly_three_nonzero_rows"] = len(nonzero) == 3
    checks["row_zero_is_the_shift"] = nonzero[0] == 0

    wl = [i for i in nonzero if i != 0]
    print("  Wilson-line rows: %s" % wl)
    checks["two_wilson_rows"] = len(wl) == 2
    checks["the_two_wilson_rows_are_equal"] = rows[wl[0]] == rows[wl[1]]

    pair = [p for p, ij in PAIR_ROWS.items() if tuple(sorted(wl)) == ij]
    print("  matching --pair slot: %s" % pair)
    checks["matches_exactly_one_pair_slot"] = len(pair) == 1
    checks["the_slot_is_45"] = pair == ["45"]
    checks["not_the_other_two_slots"] = tuple(sorted(wl)) not in (PAIR_ROWS["01"], PAIR_ROWS["23"])

    fv = tuple(F(x) for x in FROZEN_V.split(","))
    fw = tuple(F(x) for x in FROZEN_W3.split(","))
    checks["shift_matches_the_frozen_record"] = rows[0] == fv
    checks["wilson_line_matches_the_frozen_record"] = rows[wl[0]] == fw
    print("  V and W3 both match the frozen record: %s"
          % (rows[0] == fv and rows[wl[0]] == fw))

    # the Wilson line is of order three: 3 W3 must lie in the E8 x E8 lattice.
    # E8 = { x in Z^8 or x in (Z+1/2)^8, with sum(x) even } -- the half-integral
    # spinor class is part of it, so "integral" is the wrong test.
    def in_e8(h):
        allint = all(x.denominator == 1 for x in h)
        allhalf = all(x.denominator == 2 for x in h)
        return (allint or allhalf) and sum(h) % 2 == 0

    three = tuple(3 * x for x in fw)
    h1, h2 = three[:8], three[8:]
    checks["three_W3_first_half_in_E8"] = in_e8(h1)
    checks["three_W3_second_half_in_E8"] = in_e8(h2)
    checks["the_wilson_line_has_order_three"] = in_e8(h1) and in_e8(h2)
    # and it is genuinely order three, not order one: W3 itself is not in the lattice
    checks["W3_itself_is_not_in_the_lattice"] = not (in_e8(fw[:8]) and in_e8(fw[8:]))
    print("  3*W3 in E8xE8: %s (first half %s class, sum %s; second half %s class, sum %s)"
          % (in_e8(h1) and in_e8(h2),
             "spinor" if all(x.denominator == 2 for x in h1) else "root", sum(h1),
             "spinor" if all(x.denominator == 2 for x in h2) else "root", sum(h2)))

    checks["geometry_is_recorded"] = "Geometry_Z6-I_G2xG2xSU3.txt" in MODEL_FILE

    for k, v in sorted(checks.items()):
        print("  %-46s %s" % (k, v))
    valid = all(checks.values())
    print("VALID:", valid)

    if args.write:
        payload = {
            "claim": "The flagship SM_20260917_3's order-three Wilson line occupies the third "
                     "geometric pair, b4fa45c's --pair 45 (zero-based rows 6 and 7 of the eight-row "
                     "shift/Wilson block). This is read off the orbifolder input file the 5b3f3ad "
                     "scan actually used, not inferred, so the replay of a5d42fd/8937573 can pin one "
                     "candidate and use the other two as controls instead of exhausting three.",
            "pair": "45", "wilson_rows_zero_based": [6, 7],
            "geometry": "Geometry/Geometry_Z6-I_G2xG2xSU3.txt",
            "model_file": MODEL_FILE,
            "V": FROZEN_V, "W3": FROZEN_W3,
            "scope": "this records which input file produced the frozen spectrum, because it is that "
                     "input file; it does not independently verify that the scan chose the intended "
                     "slot, so the external orbifolder 1.2.1 replay is still worth running",
            "checks": checks, "valid": valid,
            "status": "the model file is quoted verbatim from the scan; the row, slot, lattice and "
                      "order-three arithmetic are computed here",
            "sources": ["Holotrade b4fa45c", "Holotrade a5d42fd", "Holotrade 8937573",
                        "Holotrade 5b3f3ad", "Holotrade d772153", "orbifolder 1.2.1 arXiv:1110.5229"]}
        with open(os.path.join(ROOT, "data", "w33_flagship_wilson_line_pair_slot.json"), "w") as f:
            json.dump(payload, f, indent=1)
        print("written")


if __name__ == "__main__":
    main()
