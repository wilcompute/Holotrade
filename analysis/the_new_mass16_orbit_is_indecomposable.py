#!/usr/bin/env python3
"""
The one new mass-16 orbit is INDECOMPOSABLE: not a sum of two admissible
excesses at either possible splitting. Two invariants, two different
separations.

WHAT WAS LEFT.  3aa3ad6 completed the mass-16 census, e62261f showed six of its
seven exceptional orbits are (the mass-12 exception) + a pencil, and 1075622
graded them by negativity depth -- inherited orbits depth 1, the single new
orbit of 1080 depth 2. What the new object actually IS was still open.

THE OBJECT.  A representative has entry histogram

    value  0  1  2
    lines 26 12  2

so it is supported on 14 of the 40 lines with mass 12*1 + 2*2 = 16. That is a
sparse profile: a 114-leaf blocker realising it would put load 12 on twelve
lines, load 13 on two, and the bare 11 on the remaining twenty-six.

IT IS INDECOMPOSABLE.  Masses are multiples of four, so an excess of mass 16
splits into two admissible parts only as 4 + 12 or 8 + 8. Neither happens:

    rep - pencil admissible at mass 12, over all 40 pencils      0
    rep - a in mass-8 admissible, over all 820 such a            0

and the mass-4 admissible set is exactly the 40 pencils, so 4 + 12 is fully
covered by the first line. A CONTROL is carried: an INHERITED representative
does decompose, with exactly one pencil working -- without it, two zeros would
be as consistent with a broken test as with a theorem.

THE MASS-12 EXCEPTION IS INDECOMPOSABLE TOO, and that is a proof rather than a
computation. Its only splitting is 4 + 8; every mass-8 admissible excess is a
sum of two pencils (the other track's mass-eight theorem, and this census finds
zero exceptions at mass 8), so pencil + mass-8 is a sum of three pencils and
therefore pencil-generated. The mass-12 exception is not pencil-generated, so
no such splitting exists.

SO THE TWO INVARIANTS SEPARATE DIFFERENT THINGS, and neither is redundant:

    indecomposable       separates {mass-12 exception, new mass-16 orbit}
                         from the six INHERITED mass-16 orbits
    negativity depth     separates the new mass-16 orbit (depth 2)
                         from everything else (depth 0 or 1)

The inherited orbits are decomposable and shallow; the mass-12 exception is
indecomposable but shallow; the new orbit is indecomposable AND deep. It is the
only object in the programme with both properties.

WHAT IT IS NOT.  This describes an admissible load PROFILE, not a blocker. No
claim is made that any 114-leaf blocker realises this profile -- that is exactly
the question a decision model would have to settle, and it is not settled here.
tau_2 stays open in [111, 115].

SCOPE.  The decomposition tests are exhaustive over the full mass-4 and mass-8
admissible sets, not sampled, and every census reaches OPTIMAL with a single
worker (CP-SAT's enumerate_all_solutions is complete only with num_workers = 1).
The indecomposability of the mass-12 exception is argued from the mass-eight
theorem and also checked. Orbit representatives come from closure under
generators of the line-action of PSp(4,3), order asserted 25920.
"""

import argparse
import importlib.util
import json
import os
from collections import Counter, deque

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
    args = ap.parse_args()

    m = mass12_module()
    pts, idx, sf, lines = m.geometry()
    adjL = [[1 if i != j and set(lines[i]) & set(lines[j]) else 0
             for j in range(40)] for i in range(40)]
    thru = [[i for i, L in enumerate(lines) if p in L] for p in range(40)]
    gens, gorder = m.line_action_generators(pts, idx, sf, lines)
    assert gorder == 25920, gorder

    def act(v, g):
        o = [0] * 40
        for i in range(40):
            o[g[i]] = v[i]
        return tuple(o)

    def orbits(vs):
        rem, out = set(vs), []
        while rem:
            s = next(iter(rem))
            o, q = {s}, deque([s])
            while q:
                x = q.popleft()
                for g in gens:
                    y = act(x, g)
                    if y not in o:
                        o.add(y)
                        q.append(y)
            out.append((s, len(o)))
            rem -= o
        return out

    def pencil(c):
        v = [0] * 40
        for i in thru[c]:
            v[i] = 1
        return tuple(v)

    a4, s4 = m.census(1, adjL, thru, 600.0)
    a8, s8 = m.census(2, adjL, thru, 1200.0)
    a12, s12 = m.census(3, adjL, thru, 3600.0)
    a16, s16 = m.census(4, adjL, thru, 7200.0)
    assert {s4, s8, s12, s16} == {"OPTIMAL"}, (s4, s8, s12, s16)

    e12 = a12 - m.pencil_vectors(3, thru)
    e16 = a16 - m.pencil_vectors(4, thru)
    inh = set()
    for e in e12:
        for c in range(40):
            p = pencil(c)
            inh.add(tuple(e[i] + p[i] for i in range(40)))
    new = e16 - inh

    reps_new = orbits(new)
    rep = reps_new[0][0]
    hist = dict(sorted(Counter(rep).items()))
    support = sum(1 for v in rep if v)

    def splits_4_12(v, pool12):
        n = 0
        for c in range(40):
            p = pencil(c)
            d = tuple(v[i] - p[i] for i in range(40))
            if min(d) >= 0 and d in pool12:
                n += 1
        return n

    def splits_8_8(v):
        n = 0
        for a in a8:
            d = tuple(v[i] - a[i] for i in range(40))
            if min(d) >= 0 and d in a8:
                n += 1
        return n

    new_412 = splits_4_12(rep, a12)
    new_88 = splits_8_8(rep)

    rep_inh = orbits(e16 & inh)[0][0]
    ctrl_412 = splits_4_12(rep_inh, a12)

    rep12 = orbits(e12)[0][0]
    m12_48 = 0
    for c in range(40):
        p = pencil(c)
        d = tuple(rep12[i] - p[i] for i in range(40))
        if min(d) >= 0 and d in a8:
            m12_48 += 1

    print("THE NEW MASS-16 ORBIT IS INDECOMPOSABLE")
    print("=" * 74)
    print("  new-at-16 vectors %d in orbits %s"
          % (len(new), [s for _, s in reps_new]))
    print("  representative: entry histogram %s, support %d lines, mass %d"
          % (hist, support, sum(rep)))
    print()
    print("  masses are multiples of 4, so mass 16 splits only as 4+12 or 8+8:")
    print("    rep - pencil admissible at mass 12 (over 40 pencils) : %d" % new_412)
    print("    rep - a in mass-8 admissible (over %d such a)        : %d"
          % (len(a8), new_88))
    print("    CONTROL, an INHERITED rep, must decompose            : %d" % ctrl_412)
    print()
    print("  mass-12 exception, only splitting is 4+8               : %d" % m12_48)
    print("  (a proof too: every mass-8 admissible is two pencils, so")
    print("   pencil + mass-8 is three pencils, hence pencil-generated.)")
    print()
    print("  indecomposable separates {mass-12 exc, new orbit} from the six")
    print("  inherited; depth separates the new orbit (2) from all else (0/1).")
    print("  The new orbit is the only object that is BOTH.")

    ok = (len(reps_new) == 1 and reps_new[0][1] == 1080
          and new_412 == 0 and new_88 == 0
          and ctrl_412 > 0 and m12_48 == 0
          and len(a4) == 40)
    print()
    print("VALID: %s" % ok)

    if args.write:
        assert ok, "checks failed -- refusing to write"
        rec = {
            "schema": "holotrade.new-mass16-orbit-indecomposable.v1",
            "valid": True,
            "newOrbitSize": reps_new[0][1],
            "newOrbitStabiliser": gorder // reps_new[0][1],
            "representativeHistogram": {str(k): v for k, v in hist.items()},
            "representativeSupport": support,
            "splits4plus12": new_412,
            "splits8plus8": new_88,
            "controlInheritedSplits": ctrl_412,
            "mass12ExceptionSplits4plus8": m12_48,
            "mass4AdmissibleCount": len(a4),
            "mass8AdmissibleCount": len(a8),
            "theObject": (
                "a representative of the new orbit has entry histogram 0 on 26 "
                "lines, 1 on 12 and 2 on 2 -- supported on 14 of the 40 lines "
                "with mass 12*1 + 2*2 = 16. A 114-leaf blocker realising it would "
                "carry load 12 on twelve lines, 13 on two, and the bare 11 on the "
                "remaining twenty-six."),
            "itIsIndecomposable": (
                "masses are multiples of four, so an excess of mass 16 splits "
                "into two admissible parts only as 4 + 12 or 8 + 8, and neither "
                "happens: rep minus a pencil is admissible at mass 12 for none of "
                "the 40 pencils, and rep minus a mass-8 admissible lands in the "
                "mass-8 admissible set for none of the 820. The mass-4 admissible "
                "set is exactly the 40 pencils, so the first line covers 4 + 12 "
                "completely. A CONTROL is carried -- an INHERITED representative "
                "does decompose, with exactly one pencil working -- because "
                "without it two zeros would be as consistent with a broken test "
                "as with a theorem."),
            "theMass12ExceptionIsIndecomposableToo": (
                "its only splitting is 4 + 8, and every mass-8 admissible excess "
                "is a sum of two pencils (the other track's mass-eight theorem, "
                "and this census finds zero exceptions at mass 8), so pencil + "
                "mass-8 is a sum of three pencils and hence pencil-generated. The "
                "mass-12 exception is not pencil-generated, so no such splitting "
                "exists. That is a proof; it is also checked."),
            "twoInvariantsTwoSeparations": (
                "indecomposability separates {the mass-12 exception, the new "
                "mass-16 orbit} from the six INHERITED mass-16 orbits, which do "
                "decompose. Negativity depth separates the new mass-16 orbit "
                "(depth 2) from everything else (depth 0 or 1). So the inherited "
                "orbits are decomposable and shallow, the mass-12 exception is "
                "indecomposable but shallow, and the new orbit is indecomposable "
                "AND deep -- the only object in the programme with both "
                "properties. Neither invariant is redundant."),
            "whatItIsNot": (
                "this describes an admissible load PROFILE, not a blocker. No "
                "claim is made that any 114-leaf blocker realises this profile; "
                "that is exactly what a decision model would have to settle and "
                "it is not settled here. tau_2 stays open in [111, 115]."),
            "boundary": (
                "the decomposition tests are exhaustive over the FULL mass-4 and "
                "mass-8 admissible sets, not sampled, and every census reaches "
                "OPTIMAL with a SINGLE worker since CP-SAT's "
                "enumerate_all_solutions is complete only with num_workers = 1. "
                "The indecomposability of the mass-12 exception is argued from "
                "the mass-eight theorem and also checked directly. Orbit "
                "representatives come from closure under generators of the "
                "line-action of PSp(4,3), order asserted to be 25920 before use."),
        }
        p = os.path.join(ROOT, "data", "new_mass16_orbit_indecomposable.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=2)
        print("written: %s" % p)


if __name__ == "__main__":
    main()
