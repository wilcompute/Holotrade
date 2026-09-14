#!/usr/bin/env python3
"""
AUDIT: W33-Theory's PAPER_SECTION5_DELTA_CP.tex (Pass 136) is internally
inconsistent and contradicts the main paper. It is orphaned (no manuscript
inputs it), so this records the defect rather than retracting a live claim.

WHAT THE SECTION CLAIMS.  "delta_CP = pi/2 as F3 Wilson-line holonomy" for the
LEPTONIC (PMNS) phase: the loop holonomy is g^3 = (-1)^3 = -1, "which
corresponds to a phase flip e^{i delta_CP} = e^{i pi/2} = i". It then checks
the value with "the Jarlskog invariant ... J = (9/40)(1/25)(1/260) sin delta_CP
... which at delta_CP = pi/2 gives J = 3.054e-5, consistent with PDG
(3.08 +- 0.13)e-5".

THREE DEFECTS, EACH CHECKED EXACTLY HERE.
  1. The holonomy -1 is e^{i pi}, not e^{i pi/2}. With the stated Z2-valued
     holonomy the only phases available are 0 and pi, and a CP phase of pi is
     CP-conserving.
  2. (9/40)(1/25)(1/260) are the substrate's CKM (quark) moduli |V_us|, |V_cb|,
     |V_ub| (w33_paper_body.tex, "CP Violation"; BT919). The product is the CKM
     Jarlskog, not the PMNS one, and the PDG value quoted is the quark J.
  3. At sin delta = 1 that product is 9/260000 = 3.4615e-5, NOT 3.054e-5. The
     printed 3.054e-5 is 27/884000, the main paper's CKM value with
     sin delta = 15/17. So the section quotes a number that requires
     sin delta = 15/17 while asserting delta = pi/2.

AND THE CONFLICT.  The main paper (w33_paper_body.tex) and BT919 give the CKM
phase via sin delta = (mu^2-1)/(mu^2+1) = 15/17 (delta = 61.93 or 118.07
degrees). The orphaned section's delta = pi/2 is presented as leptonic but is
checked against quark data, so it neither confirms nor supplies a PMNS phase.

A SECOND, SMALLER ITEM.  scripts/w33_cubic_invariant.py's docstring equates
"the 36 internal triangles of H27" with "the 36 lines on the cubic surface". A
cubic surface has 27 lines; 36 counts double-sixes (equivalently positive E6
roots). Label error in an exploratory script; no certified number depends on it.

SCOPE.  Exact rational arithmetic on the quoted numbers and a check that no TeX
file inputs the section. Nothing about the physical value of any CP phase is
asserted.
"""

import argparse
import json
import os
import re
from fractions import Fraction as F

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOE = r"C:\Repos\Theory of Everything"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    product = F(9, 40) * F(1, 25) * F(1, 260)
    at_sin_one = product
    at_15_17 = product * F(15, 17)
    printed = 3.054e-5
    sec = os.path.join(TOE, "PAPER_SECTION5_DELTA_CP.tex")
    text = open(sec, encoding="utf-8").read() if os.path.exists(sec) else ""
    quotes_pi2 = "e^{i\\pi/2} = i" in text and "3.054" in text and "9}{40}" in text
    orphan = True
    if os.path.isdir(TOE):
        for dirpath, dirs, files in os.walk(TOE):
            dirs[:] = [d for d in dirs if d not in (".git", ".venv", "node_modules", "__pycache__", ".claude")]
            for fn in files:
                if fn.endswith(".tex"):
                    try:
                        t = open(os.path.join(dirpath, fn), encoding="utf-8", errors="ignore").read()
                    except OSError:
                        continue
                    if re.search(r"\\(input|include)\{[^}]*PAPER_SECTION5_DELTA_CP", t):
                        orphan = False
    cubic = os.path.join(TOE, "scripts", "w33_cubic_invariant.py")
    cubic_text = open(cubic, encoding="utf-8").read() if os.path.exists(cubic) else ""
    cubic_mislabel = "36 internal triangles of H27 = the 36 lines on the cubic surface" in cubic_text

    print("AUDIT: THE ORPHANED DELTA_CP SECTION")
    print("=" * 74)
    print("  CKM moduli product (9/40)(1/25)(1/260) = %s = %.4e" % (product, float(product)))
    print("  at sin delta = 1     : %.4e   (the section prints 3.054e-5)" % float(at_sin_one))
    print("  at sin delta = 15/17 : %s = %.4e   (the main paper's CKM value)" % (at_15_17, float(at_15_17)))
    print("  section quotes pi/2 phase and the 3.054e-5 check: %s; inputs found: %s" % (quotes_pi2, not orphan))
    print("  cubic-invariant docstring mislabel present: %s" % cubic_mislabel)
    ok = (at_15_17 == F(27, 884000) and abs(float(at_15_17) - printed) < 5e-9
          and abs(float(at_sin_one) - printed) > 3e-6 and quotes_pi2 and orphan and cubic_mislabel)
    print()
    print("VALID: %s" % ok)
    if args.write:
        assert ok, "checks failed -- refusing to write"
        rec = {
            "schema": "holotrade.audit-delta-cp-section.v1",
            "valid": True,
            "target": "W33-Theory PAPER_SECTION5_DELTA_CP.tex (Pass 136)",
            "orphaned": orphan,
            "ckmProduct": str(product),
            "jarlskogAtSinOne": float(at_sin_one),
            "jarlskogAtFifteenSeventeenths": str(at_15_17),
            "printedValue": printed,
            "defects": [
                "holonomy -1 is e^{i pi}, not e^{i pi/2}; a Z2 holonomy yields only 0 or pi, and pi conserves CP",
                "the check uses the substrate's CKM (quark) moduli and the quark PDG J for a claimed PMNS phase",
                "at sin delta = 1 the product is 9/260000 = 3.4615e-5, not the printed 3.054e-5, which equals 27/884000 "
                "and needs sin delta = 15/17",
            ],
            "conflict": "main paper and BT919 give sin delta_CKM = 15/17; the orphaned section asserts pi/2",
            "secondary": ("scripts/w33_cubic_invariant.py docstring equates 36 internal triangles with '36 lines on the "
                          "cubic surface'; a cubic surface has 27 lines, 36 counts double-sixes"),
            "boundary": "exact arithmetic on quoted numbers; no physical CP phase is asserted",
        }
        p = os.path.join(ROOT, "data", "audit_delta_cp_section.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=2)
        print("written: %s" % p)


if __name__ == "__main__":
    main()
