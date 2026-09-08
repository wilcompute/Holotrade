#!/usr/bin/env python3
"""
Negativity depth grades the whole exceptional structure: 0 is
pencil-generated, the mass-12 exception and all six inherited mass-16 orbits
are 1, and the one new mass-16 orbit is 2 -- which PROVES it is not inherited.

THE INVARIANT.  the_kernel_is_spanned_by_octet_differences.py showed that an
admissible excess e always has an INTEGER preimage under N^T -- Z^40/im(N^T) is
torsion-free -- and that "e is k point-pencils" means that preimage can be taken
nonnegative. So the natural measure of failure is how far from nonnegative the
best preimage is. Define

    depth(e)  =  min over integer x with N^T x = e  of  sum_p max(0, -x_p).

depth(e) = 0 is exactly pencil-generated. Nothing else needs to be assumed; the
minimisation is an integer program in 40 variables with 40 equality
constraints, solved to OPTIMAL.

WHAT IT MEASURES, on every exceptional orbit in the programme:

    pencil-generated control                    depth 0
    mass 12, the single exceptional orbit 1440  depth 1
    mass 16, six INHERITED orbits               depth 1
        720, 1440, 8640, 8640, 12960, 12960
    mass 16, the ONE NEW orbit 1080 (stab 24)   depth 2

So the grading is exact: every exception known before mass 16 has depth 1, and
the single new object at mass 16 is the first depth-2 excess in the programme.

AND IT UPGRADES THE INHERITANCE SPLIT FROM A COMPUTATION TO A PROOF.  Depth
cannot increase when a pencil is added. If N^T x = e then N^T (x + 1_c) =
e + pencil(c), and adding 1 to a single coordinate cannot make any coordinate
more negative, so

    depth(e + pencil(c))  <=  depth(e).

Every mass-12 exception has depth 1. Hence nothing of depth 2 can be written as
(mass-12 exception) + pencil, and the new mass-16 orbit -- depth 2 -- is
provably NOT inherited. e62261f established that split by intersecting sets of
46440 vectors; this establishes it by a one-line monotonicity argument, and the
two agree.

It also explains the third finding of e62261f. Of the 48240 vectors
(mass-12 exception) + pencil, 2880 turn out PENCIL-GENERATED at mass 16: those
are exactly the cases where the inequality is strict and depth drops 1 -> 0. A
pencil can repair an exception, never create a deeper one.

WHAT IT IS NOT.  Depth is an invariant of a load-excess PROFILE, not of a
blocker. It says nothing about tau_2, which stays open in [111, 115]. It is
also not claimed to be a complete invariant: two orbits of the same depth are
not thereby equivalent, and the six inherited orbits all have depth 1 while
being six distinct orbits.

SCOPE.  Depths are computed by exact integer minimisation returning OPTIMAL,
with a pencil-generated vector carried as a control that must return 0. The
censuses behind the orbit lists reach OPTIMAL with a single worker (CP-SAT's
enumerate_all_solutions is complete only with num_workers = 1). Orbit
representatives come from closure under generators of the line-action of
PSp(4,3), order asserted 25920.
"""

import argparse
import importlib.util
import json
import os
from collections import deque

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
    ap.add_argument("--depth-budget", type=float, default=120.0)
    args = ap.parse_args()

    from ortools.sat.python import cp_model

    m = mass12_module()
    pts, idx, sf, lines = m.geometry()
    adjL = [[1 if i != j and set(lines[i]) & set(lines[j]) else 0
             for j in range(40)] for i in range(40)]
    thru = [[i for i, L in enumerate(lines) if p in L] for p in range(40)]
    gens, gorder = m.line_action_generators(pts, idx, sf, lines)
    assert gorder == 25920, gorder

    def act(vec, g):
        out = [0] * 40
        for i in range(40):
            out[g[i]] = vec[i]
        return tuple(out)

    def orbits(vecs):
        rem, out = set(vecs), []
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

    def depth(e):
        mdl = cp_model.CpModel()
        x = [mdl.NewIntVar(-60, 60, "x%d" % p) for p in range(40)]
        for L in range(40):
            mdl.Add(sum(x[p] for p in lines[L]) == e[L])
        d = []
        for p in range(40):
            dp = mdl.NewIntVar(0, 60, "d%d" % p)
            mdl.Add(dp >= -x[p])
            d.append(dp)
        mdl.Minimize(sum(d))
        sv = cp_model.CpSolver()
        sv.parameters.num_workers = 8
        sv.parameters.max_time_in_seconds = args.depth_budget
        st = sv.Solve(mdl)
        if st != cp_model.OPTIMAL:
            return None
        return int(sv.ObjectiveValue())

    a12, s12 = m.census(3, adjL, thru, args.budget12)
    a16, s16 = m.census(4, adjL, thru, args.budget16)
    assert s12 == "OPTIMAL" and s16 == "OPTIMAL", (s12, s16)
    pg16 = m.pencil_vectors(4, thru)
    e12 = a12 - m.pencil_vectors(3, thru)
    e16 = a16 - pg16

    control = depth(next(iter(pg16 & a16)))

    inh = set()
    for e in e12:
        for c in range(40):
            p = [0] * 40
            for i in thru[c]:
                p[i] = 1
            inh.add(tuple(e[i] + p[i] for i in range(40)))

    rows12 = [{"mass": 12, "orbit": sz, "stabiliser": gorder // sz,
               "inherited": None, "depth": depth(rep)}
              for rep, sz in orbits(e12)]
    rows16 = [{"mass": 16, "orbit": sz, "stabiliser": gorder // sz,
               "inherited": rep in inh, "depth": depth(rep)}
              for rep, sz in orbits(e16)]

    print("THE EXCEPTIONS ARE GRADED BY NEGATIVITY DEPTH")
    print("=" * 74)
    print("  depth(e) = min over integer x with N^T x = e of sum max(0, -x_p)")
    print()
    print("  control, a pencil-generated vector : depth %s" % control)
    print()
    for r in rows12:
        print("  mass 12   orbit %6d  stab %5d              depth %s"
              % (r["orbit"], r["stabiliser"], r["depth"]))
    for r in rows16:
        print("  mass 16   orbit %6d  stab %5d  %-9s  depth %s"
              % (r["orbit"], r["stabiliser"],
                 "inherited" if r["inherited"] else "NEW", r["depth"]))
    print()
    print("  depth cannot increase when a pencil is added, since x + 1_c is a")
    print("  preimage of e + pencil(c) and no coordinate gets more negative.")
    print("  Every mass-12 exception has depth 1, so nothing of depth 2 is")
    print("  (mass-12 exception) + pencil: the new orbit is PROVABLY not")
    print("  inherited, independently of the set computation in e62261f.")

    inherited16 = [r for r in rows16 if r["inherited"]]
    new16 = [r for r in rows16 if not r["inherited"]]
    ok = (control == 0
          and len(rows12) == 1 and rows12[0]["depth"] == 1
          and len(inherited16) == 6
          and all(r["depth"] == 1 for r in inherited16)
          and len(new16) == 1 and new16[0]["depth"] == 2
          and new16[0]["orbit"] == 1080 and new16[0]["stabiliser"] == 24)
    print()
    print("VALID: %s" % ok)

    if args.write:
        assert ok, "checks failed -- refusing to write"
        rec = {
            "schema": "holotrade.exceptions-graded-by-negativity-depth.v1",
            "valid": True,
            "controlDepth": control,
            "mass12Orbits": rows12,
            "mass16Orbits": rows16,
            "inheritedDepths": sorted({r["depth"] for r in inherited16}),
            "newOrbitDepth": new16[0]["depth"],
            "theInvariant": (
                "an admissible excess always has an INTEGER preimage under N^T, "
                "because Z^40/im(N^T) is torsion-free, and 'e is k point-pencils' "
                "means that preimage can be taken nonnegative. So define depth(e) "
                "as the minimum, over integer x with N^T x = e, of the total "
                "negativity sum_p max(0, -x_p). Then depth 0 is exactly "
                "pencil-generated. It is an integer program in 40 variables with "
                "40 equality constraints, solved to OPTIMAL."),
            "theGrading": (
                "pencil-generated control has depth 0; the single mass-12 "
                "exceptional orbit of 1440 has depth 1; all SIX inherited mass-16 "
                "orbits -- 720, 1440, 8640, 8640, 12960, 12960 -- have depth 1; "
                "and the ONE new mass-16 orbit, 1080 with stabiliser 24, has "
                "depth 2. Every exception known before mass 16 has depth 1, and "
                "the new object is the first depth-2 excess in the programme."),
            "depthIsMonotoneUnderAddingAPencil": (
                "if N^T x = e then N^T (x + 1_c) = e + pencil(c), and adding 1 to "
                "a single coordinate cannot make any coordinate more negative, so "
                "depth(e + pencil(c)) <= depth(e). Depth can never increase."),
            "whichUpgradesTheSplitToAProof": (
                "every mass-12 exception has depth 1, so by monotonicity nothing "
                "of depth 2 can be written as (mass-12 exception) + pencil. The "
                "new mass-16 orbit has depth 2 and is therefore PROVABLY not "
                "inherited. e62261f established that split by intersecting sets "
                "of 46440 vectors; this establishes it by a one-line "
                "monotonicity argument, and the two agree."),
            "andItExplainsTheRepairs": (
                "e62261f found that 2880 of the 48240 vectors (mass-12 "
                "exception) + pencil are PENCIL-GENERATED at mass 16. Those are "
                "exactly the cases where the monotonicity is strict and depth "
                "drops 1 -> 0. A pencil can repair an exception; it can never "
                "create a deeper one."),
            "whatItIsNot": (
                "depth is an invariant of a load-excess PROFILE, not of a "
                "blocker, and says nothing about tau_2, which stays open in "
                "[111, 115]. It is also not claimed to be a COMPLETE invariant: "
                "two orbits of equal depth are not thereby equivalent, and the "
                "six inherited orbits all have depth 1 while being six distinct "
                "orbits."),
            "boundary": (
                "depths are exact integer minimisations returning OPTIMAL, with a "
                "pencil-generated vector carried as a control that must return 0 "
                "-- if the control were nonzero the invariant would be "
                "miscalibrated and nothing below it would mean anything. The "
                "censuses behind the orbit lists reach OPTIMAL with a SINGLE "
                "worker, since CP-SAT's enumerate_all_solutions is complete only "
                "with num_workers = 1. Orbit representatives come from closure "
                "under generators of the line-action of PSp(4,3), order asserted "
                "to be 25920 before use."),
        }
        p = os.path.join(ROOT, "data", "exceptions_graded_by_depth.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=2)
        print("written: %s" % p)


if __name__ == "__main__":
    main()
