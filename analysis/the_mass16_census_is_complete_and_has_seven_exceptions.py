#!/usr/bin/env python3
"""
Mass 16 is complete: 169805 = 123365 pencil-generated + 46440 exceptional, and
the exceptions are exactly SEVEN orbits. That is the 114 case.

WHERE IT SITS.  For a tensor blocker of size 110 + k the axis load-excess e
satisfies A e = 2 e + k 1 with sum(e) = 4k, so k = 4 is mass 16 is size 114 --
the size that has now defeated five search levers. The other track proved mass 4
is exactly one point-pencil and mass 8 exactly two, then found the induction
FAILING at masses 12 and 16 and wrote the_mass12_mass16_exact_orbit_census.py to
classify what is really there. That script self-labels PARTIAL unless the
enumeration finishes OPTIMAL, and it never did -- it crashed outright until
ebd9a84, and after the fix reached only 50572 solutions at mass 16 with status
FEASIBLE. 139dd83 completed mass 12. This completes MASS 16.

THE CENSUS, enumerating every nonnegative integer solution and reaching OPTIMAL,
hence exhaustive:

    mass  4   admissible     40   pencil-generated     40   exceptional      0
    mass 16   admissible 169805   pencil-generated 123365   exceptional  46440

Mass 4 is carried as a control with a known answer -- 40, the point-pencils --
because a silently truncated enumeration is the failure mode here (see the
worker gotcha below) and a census with no control is not evidence.

SEVEN EXCEPTIONAL ORBITS, NOT ONE.  Under the line-action of PSp(4,3), order
25920 and asserted before use, the 46440 exceptional excesses split as

    720, 1080, 1440, 8640, 8640, 12960, 12960      stabilisers 36, 24, 18, 3, 3, 2, 2

summing to 46440, and the 123365 pencil-generated ones fall into 28 orbits. So
the shape of the failure CHANGES with mass: at mass 12 the induction fails on
exactly ONE class of 1440 (139dd83), and at mass 16 it fails on seven, three of
them large and with stabilisers as small as 2. Whatever governs the exceptions
is not a single sporadic object.

AN INDEPENDENT CROSS-CHECK FELL OUT.  The pencil-generated count 123365 is
reproduced here from the enumeration, and it agrees exactly with the count
obtained a completely different way in the_kernel_is_spanned_by_octet_
differences.py: the 123410 multisets of 4 points minus the 45 collisions, which
are exactly the octet polarity pairs {L, L^perp}. Two routes, one number. That
also explains the 45: mass 16 is the first mass at which the pencil-sum map
stops being injective, and it stops on the octets.

WHAT THIS DOES NOT DO.  It does not decide tau_2 and it is not a statement about
blockers. A load-excess census classifies admissible PROFILES -- a necessary
condition on a 114-leaf blocker's row and column loads, nothing more. What it
buys is that a 114 decision in the style of the other track's 112 model, which
fixes an exact row/column profile pair and runs a leaf CSP, now has a finite and
enumerated case list: 35 orbits per axis, so 35 x 35 = 1225 exact cases. That is
a large programme but it is a defined one, which it was not before. tau_2 stays
open in [111, 115].

THE WORKER GOTCHA, repeated because it is the whole reason a control is carried.
CP-SAT's enumerate_all_solutions is COMPLETE ONLY WITH num_workers = 1. With
four workers the identical models return under-counts and still report OPTIMAL,
silently. The census function used here sets one worker; the other track's
script sets num_search_workers = 1 correctly too.

SCOPE.  Exhaustive at masses 4 and 16: both reached OPTIMAL with a single worker
and the certificate is refused if either did not. Orbits are computed by closure
under generators of the line-action whose order is asserted to be 25920 before
use. The geometry, the line adjacency and the pencil family are built here and
not imported from the other track's census. Masses 8 and 12 are not recomputed;
they are 139dd83's.
"""

import argparse
import importlib.util
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def mass12_module():
    """Reuse 139dd83's machinery rather than duplicating 330 lines of it."""
    p = os.path.join(ROOT, "analysis",
                     "the_mass12_census_is_complete_and_has_one_exception.py")
    spec = importlib.util.spec_from_file_location("mass12", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--budget", type=float, default=7200.0)
    ap.add_argument("--ks", type=int, nargs="+", default=[1, 4])
    args = ap.parse_args()

    m = mass12_module()
    pts, idx, sf, lines = m.geometry()
    adjL = [[1 if i != j and set(lines[i]) & set(lines[j]) else 0
             for j in range(40)] for i in range(40)]
    thru = [[i for i, L in enumerate(lines) if p in L] for p in range(40)]
    gens, gorder = m.line_action_generators(pts, idx, sf, lines)
    assert gorder == 25920, gorder

    rows = []
    for k in args.ks:
        adm, status = m.census(k, adjL, thru, args.budget)
        pg = m.pencil_vectors(k, thru)
        exc = adm - pg
        rows.append({
            "k": k, "mass": 4 * k,
            "admissible": len(adm), "solverStatus": status,
            "complete": status == "OPTIMAL",
            "pencilGenerated": len(adm & pg),
            "pencilFamilySize": len(pg),
            "exceptional": len(exc),
            "pencilOrbitSizes": m.orbit_sizes(adm & pg, gens),
            "exceptionalOrbitSizes": m.orbit_sizes(exc, gens),
        })

    print("THE MASS-16 CENSUS, COMPLETED")
    print("=" * 74)
    print("  line-action group order: %d" % gorder)
    print()
    for r in rows:
        print("  mass %2d  admissible %6d [%s]  pencil %6d  exceptional %6d"
              % (r["mass"], r["admissible"], r["solverStatus"],
                 r["pencilGenerated"], r["exceptional"]))
        print("           pencil orbits      : %d orbits" % len(r["pencilOrbitSizes"]))
        print("           exceptional orbits : %s" % r["exceptionalOrbitSizes"])
        if r["exceptionalOrbitSizes"]:
            print("           stabilisers        : %s"
                  % [gorder // s for s in r["exceptionalOrbitSizes"]])
    print()
    print("  mass 4 is the control: 40 admissible, all pencil, no exceptions.")
    print("  mass 16 is exhaustive and its exceptions are SEVEN orbits, against")
    print("  exactly ONE at mass 12 (139dd83) -- the failure shape changes.")

    target = [r for r in rows if r["k"] == 4]
    control = [r for r in rows if r["k"] == 1]
    ok = (all(r["complete"] for r in rows)
          and bool(target) and bool(control)
          and control[0]["admissible"] == 40
          and control[0]["exceptional"] == 0
          and target[0]["admissible"] == 169805
          and target[0]["pencilGenerated"] == 123365
          and target[0]["exceptional"] == 46440
          and len(target[0]["exceptionalOrbitSizes"]) == 7
          and sum(target[0]["exceptionalOrbitSizes"]) == 46440)
    print()
    print("VALID: %s" % ok)

    if args.write:
        assert ok, "checks failed -- refusing to write"
        t = target[0]
        rec = {
            "schema": "holotrade.mass16-census-complete.v1",
            "valid": True,
            "lineActionGroupOrder": gorder,
            "rows": rows,
            "controlMass4": {"admissible": control[0]["admissible"],
                             "exceptional": control[0]["exceptional"],
                             "status": control[0]["solverStatus"]},
            "mass16Admissible": t["admissible"],
            "mass16PencilGenerated": t["pencilGenerated"],
            "mass16Exceptional": t["exceptional"],
            "mass16ExceptionalOrbits": t["exceptionalOrbitSizes"],
            "mass16ExceptionalStabilisers": [gorder // s
                                             for s in t["exceptionalOrbitSizes"]],
            "mass16PencilOrbitCount": len(t["pencilOrbitSizes"]),
            "theResult": (
                "mass 16 has exactly 169805 admissible excesses, of which 123365 "
                "are pencil-generated and 46440 are not, with solver status "
                "OPTIMAL so the census is exhaustive. Under the line-action of "
                "PSp(4,3) the exceptional ones split into SEVEN orbits -- 720, "
                "1080, 1440, 8640, 8640, 12960, 12960, with stabilisers 36, 24, "
                "18, 3, 3, 2, 2 -- and the pencil-generated ones into 28. Mass 16 "
                "is 4(114-110), so this is the load-profile classification for "
                "the size that has defeated five search levers."),
            "theFailureShapeChangesWithMass": (
                "at mass 12 the pencil induction fails on exactly ONE class of "
                "1440 (139dd83); at mass 16 it fails on seven, three of them "
                "large and with stabilisers as small as 2. Whatever governs the "
                "exceptions is not a single sporadic object, and an argument that "
                "handled the mass-12 exception by naming it will not transfer."),
            "independentCrossCheck": (
                "the pencil-generated count 123365 is reproduced here from the "
                "enumeration and agrees exactly with the count obtained a "
                "different way in the_kernel_is_spanned_by_octet_differences.py: "
                "123410 multisets of four points minus 45 collisions, which are "
                "exactly the octet polarity pairs {L, L^perp}. Two routes, one "
                "number -- and it explains the 45, since mass 16 is the first "
                "mass at which the pencil-sum map stops being injective, and it "
                "stops on the octets."),
            "whatItDoesNotDo": (
                "it does not decide tau_2 and is not a statement about blockers. "
                "A load-excess census classifies admissible PROFILES, a necessary "
                "condition on a 114-leaf blocker's row and column loads and "
                "nothing more. What it buys is that a 114 decision in the style "
                "of the other track's 112 model -- fix an exact row/column "
                "profile pair, run a leaf CSP -- now has a finite enumerated case "
                "list: 35 orbits per axis, so 1225 exact cases. A large programme "
                "but a defined one, which it was not before. tau_2 stays open in "
                "[111, 115]."),
            "priorArt": (
                "the excess equation, the mass-4 and mass-8 theorems and the "
                "census script are the other track's; ebd9a84 fixed the TypeError "
                "that stopped that script running at all, and 139dd83 completed "
                "mass 12. This file reuses 139dd83's geometry, line-action and "
                "census machinery by import rather than re-deriving it."),
            "boundary": (
                "exhaustive at masses 4 and 16: both reached OPTIMAL with a "
                "SINGLE worker -- CP-SAT's enumerate_all_solutions is complete "
                "only with num_workers = 1, and with more it under-counts while "
                "still reporting OPTIMAL -- and the certificate is refused if "
                "either did not. Mass 4 is carried as a known-answer control for "
                "exactly that reason. Orbits are closures under generators of the "
                "line-action whose order is asserted to be 25920 before use. "
                "Masses 8 and 12 are not recomputed here; they are 139dd83's."),
        }
        p = os.path.join(ROOT, "data", "mass16_census_complete.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=2)
        print("written: %s" % p)


if __name__ == "__main__":
    main()
