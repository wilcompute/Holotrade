#!/usr/bin/env python3
"""
Six of the seven exceptional mass-16 orbits are the mass-12 exception plus a
pencil. Exactly ONE orbit, of size 1080, is new at mass 16.

WHAT WAS LEFT OPEN.  3aa3ad6 completed the mass-16 census -- 169805 admissible
axis load-excesses, 123365 pencil-generated, 46440 exceptional in seven orbits
of sizes 720, 1080, 1440, 8640, 8640, 12960 and 12960. A census counts; it does
not explain. Mass 8 has no exceptions at all and mass 12 has exactly one
exceptional orbit, of size 1440 (139dd83), so the obvious question is whether
the mass-16 exceptions are built from the mass-12 one or are new objects.

THE ANSWER, and it is almost entirely the former.  Adding a single point-pencil
to each of the 1440 mass-12 exceptional excesses gives 48240 distinct vectors.
Intersecting with the mass-16 exceptional set:

    mass-16 exceptional          46440
      inherited  = (mass-12 exceptional) + pencil     45360    97.7%
      new at mass 16                                   1080     2.3%

and under the line-action of PSp(4,3), order 25920 and asserted before use, the
split is exactly along orbits:

    inherited   720, 1440, 8640, 8640, 12960, 12960     six orbits, 45360
    new         1080                                    ONE orbit,  stabiliser 24

So "seven exceptional orbits" overstates how much is going on at mass 16. There
is ONE inherited class, propagating from mass 12 into six orbits, and ONE
genuinely new object.

AND ADDING A PENCIL CAN REPAIR PENCIL-GENERATION.  Of the 48240 vectors of the
form (mass-12 exceptional) + pencil, 2880 are PENCIL-GENERATED at mass 16 --
that is, an excess with no nonnegative pencil preimage acquires one when a
pencil is added. That is the octet collision doing visible work: mass 16 is the
first mass at which the pencil-sum map fails to be injective, and it fails
exactly on the 45 octet polarity pairs {L, L^perp}
(the_kernel_is_spanned_by_octet_differences.py). The same degeneracy that makes
the encoding ambiguous at mass 16 is what lets an exception become
pencil-generated one pencil later.

WHY IT MATTERS FOR THE PROGRAMME.  An argument that dispatches the mass-12
exception does most of the mass-16 work for free -- six orbits out of seven,
45360 of 46440 profiles. The residue is a single orbit of 1080 with stabiliser
24, which is a small enough object to be attacked directly. That is a very
different situation from seven unrelated sporadic classes, which is what the
census alone suggested and what 3aa3ad6 explicitly warned might be the case.

WHAT IT DOES NOT DO.  It says nothing about tau_2 and nothing about blockers.
These are admissible load PROFILES: a necessary condition on the row and column
loads of a 114-leaf blocker, not a claim that any of them is realised by one.
tau_2 stays open in [111, 115].

SCOPE.  Both censuses reach OPTIMAL with a single worker -- CP-SAT's
enumerate_all_solutions is complete only with num_workers = 1 -- and the
certificate is refused if either does not. The inherited/new split is a set
computation over the full 46440, not a sample, and the orbit decomposition is a
closure under generators of the line-action. Masses 4 and 8 are not recomputed
here; the mass-12 census is 139dd83's and the mass-16 census is 3aa3ad6's, both
re-run rather than read from their certificates so the split is computed from
the same objects it describes.
"""

import argparse
import importlib.util
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def mass12_module():
    p = os.path.join(ROOT, "analysis",
                     "the_mass12_census_is_complete_and_has_one_exception.py")
    spec = importlib.util.spec_from_file_location("mass12", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--budget12", type=float, default=3600.0)
    ap.add_argument("--budget16", type=float, default=7200.0)
    args = ap.parse_args()

    m = mass12_module()
    pts, idx, sf, lines = m.geometry()
    adjL = [[1 if i != j and set(lines[i]) & set(lines[j]) else 0
             for j in range(40)] for i in range(40)]
    thru = [[i for i, L in enumerate(lines) if p in L] for p in range(40)]
    gens, gorder = m.line_action_generators(pts, idx, sf, lines)
    assert gorder == 25920, gorder

    def pencil(c):
        v = [0] * 40
        for i in thru[c]:
            v[i] = 1
        return tuple(v)

    a12, s12 = m.census(3, adjL, thru, args.budget12)
    a16, s16 = m.census(4, adjL, thru, args.budget16)
    exc12 = a12 - m.pencil_vectors(3, thru)
    pg16 = m.pencil_vectors(4, thru)
    exc16 = a16 - pg16

    shifted = set()
    for e in exc12:
        for c in range(40):
            p = pencil(c)
            shifted.add(tuple(e[i] + p[i] for i in range(40)))

    inherited = exc16 & shifted
    new = exc16 - shifted
    repaired = shifted & pg16

    oi = m.orbit_sizes(inherited, gens)
    on = m.orbit_sizes(new, gens)

    print("SIX OF THE SEVEN MASS-16 EXCEPTIONS ARE INHERITED")
    print("=" * 74)
    print("  mass 12: %d admissible [%s], %d exceptional"
          % (len(a12), s12, len(exc12)))
    print("  mass 16: %d admissible [%s], %d exceptional"
          % (len(a16), s16, len(exc16)))
    print()
    print("  (mass-12 exceptional) + pencil -> %d distinct vectors" % len(shifted))
    print("    inherited (exceptional at 16) : %5d   %.1f%%"
          % (len(inherited), 100.0 * len(inherited) / len(exc16)))
    print("    new at mass 16                : %5d   %.1f%%"
          % (len(new), 100.0 * len(new) / len(exc16)))
    print("    repaired (pencil-generated at 16) : %d" % len(repaired))
    print()
    print("  inherited orbits : %s   (%d)" % (oi, sum(oi)))
    print("  NEW orbits       : %s   (%d)   stabiliser %s"
          % (on, sum(on), [gorder // s for s in on]))
    print()
    print("  so there is ONE inherited class propagating into six orbits,")
    print("  and ONE genuinely new object -- not seven unrelated classes.")

    ok = (s12 == "OPTIMAL" and s16 == "OPTIMAL"
          and len(exc12) == 1440 and len(exc16) == 46440
          and len(inherited) == 45360 and len(new) == 1080
          and len(oi) == 6 and len(on) == 1
          and sum(oi) + sum(on) == len(exc16)
          and len(repaired) == 2880)
    print()
    print("VALID: %s" % ok)

    if args.write:
        assert ok, "checks failed -- refusing to write"
        rec = {
            "schema": "holotrade.mass16-exceptions-are-inherited.v1",
            "valid": True,
            "lineActionGroupOrder": gorder,
            "mass12Exceptional": len(exc12),
            "mass16Exceptional": len(exc16),
            "shiftedVectors": len(shifted),
            "inherited": len(inherited),
            "newAtMass16": len(new),
            "repairedToPencilGenerated": len(repaired),
            "inheritedOrbits": oi,
            "newOrbits": on,
            "newOrbitStabilisers": [gorder // s for s in on],
            "theResult": (
                "adding a single point-pencil to each of the 1440 mass-12 "
                "exceptional excesses gives 48240 distinct vectors, and 45360 of "
                "the 46440 mass-16 exceptions -- 97.7 per cent -- are among them. "
                "The split is exactly along orbits: the inherited part is six "
                "orbits of sizes 720, 1440, 8640, 8640, 12960, 12960, and the "
                "residue is ONE orbit of size 1080 with stabiliser 24. So the "
                "seven exceptional orbits at mass 16 are one inherited class "
                "propagating from mass 12 into six orbits, plus one genuinely new "
                "object."),
            "addingAPencilCanRepairPencilGeneration": (
                "of the 48240 vectors of the form (mass-12 exceptional) + pencil, "
                "2880 are PENCIL-GENERATED at mass 16: an excess with no "
                "nonnegative pencil preimage acquires one when a pencil is added. "
                "That is the octet collision doing visible work -- mass 16 is the "
                "first mass at which the pencil-sum map stops being injective and "
                "it fails exactly on the 45 octet polarity pairs {L, L^perp} "
                "(the_kernel_is_spanned_by_octet_differences.py). The same "
                "degeneracy that makes the encoding ambiguous at mass 16 is what "
                "lets an exception become pencil-generated one pencil later."),
            "whyItMattersForTheProgramme": (
                "an argument that dispatches the mass-12 exception does most of "
                "the mass-16 work for free: six orbits of seven, 45360 profiles "
                "of 46440. The residue is a single orbit of 1080 with stabiliser "
                "24, small enough to attack directly. That is a very different "
                "situation from seven unrelated sporadic classes, which is what "
                "the census alone suggested and what 3aa3ad6 explicitly warned "
                "might be the case."),
            "whatItDoesNotDo": (
                "it says nothing about tau_2 and nothing about blockers. These "
                "are admissible load PROFILES -- a necessary condition on the row "
                "and column loads of a 114-leaf blocker, not a claim that any "
                "profile is realised by one. tau_2 stays open in [111, 115]."),
            "boundary": (
                "both censuses reach OPTIMAL with a SINGLE worker, since CP-SAT's "
                "enumerate_all_solutions is complete only with num_workers = 1, "
                "and the certificate is refused if either does not. The "
                "inherited/new split is a set computation over the full 46440 and "
                "not a sample; the orbit decomposition is a closure under "
                "generators of the line-action whose order is asserted to be "
                "25920. The mass-12 census is 139dd83's and the mass-16 census is "
                "3aa3ad6's, both re-run here rather than read from their "
                "certificates so that the split is computed from the same objects "
                "it describes."),
        }
        p = os.path.join(ROOT, "data", "mass16_exceptions_are_inherited.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=2)
        print("written: %s" % p)


if __name__ == "__main__":
    main()
