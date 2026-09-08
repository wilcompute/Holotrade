#!/usr/bin/env python3
"""
The mass-12 excess census, completed: 12920 admissible = 11480 pencil-generated
in eight orbits + 1440 exceptional in exactly ONE orbit.

WHAT WAS OPEN.  The other track's mass-excess programme proves that a W(3,3)
axis load-excess of mass 4 is exactly one point-pencil and of mass 8 exactly
two, then reports the induction FAILING at mass 12 and 16 with CP-SAT
counterexamples in milliseconds, and builds the_mass12_mass16_exact_orbit_
census.py to classify what is really there. That script self-labels its result
PARTIAL unless OR-Tools finishes all-solution enumeration with OPTIMAL, and its
committed run does not reach OPTIMAL at either mass -- indeed it crashed before
writing anything at all until ebd9a84 fixed a dict-sort TypeError in it.

This completes MASS 12 exactly. Mass 16 is not completed here and no claim is
made about it.

THE CENSUS.  Enumerating every nonnegative integer e with A e = 2 e + k 1 and
sum(e) = 4k, where A is the line-graph adjacency of W(3,3):

    mass  4   admissible    40   pencil-generated    40   exceptional     0
    mass  8   admissible   820   pencil-generated   820   exceptional     0
    mass 12   admissible 12920   pencil-generated 11480   exceptional  1440

all three with solver status OPTIMAL, so all three are exhaustive. Masses 4 and
8 reproduce the other track's two theorems independently, from a separately
built geometry and adjacency, and find no exceptions -- which is what those
theorems assert.

MASS 12 SPLITS INTO NINE PSp(4,3) ORBITS, AND EXACTLY ONE IS EXCEPTIONAL.
Acting with the line-action of PSp(4,3), order 25920, generated from symplectic
transvections:

    pencil-generated   40, 160, 360, 480, 1080, 2160, 2880, 4320   (8 orbits)
    exceptional        1440                                        (1 orbit)

and 40+160+360+480+1080+2160+2880+4320 = 11480, plus 1440, is 12920. The single
exceptional orbit has stabiliser of order 25920/1440 = 18. So the failure of
the pencil induction at mass 12 is not a spray of sporadic counterexamples: it
is one class.

A GOTCHA THAT COST ME THE FIRST ANSWER, AND IS WORTH RECORDING.  CP-SAT's
enumerate_all_solutions is only complete with num_workers = 1. Run with four
workers the same models return 38, 202 and 12756 -- under-counts -- and still
report OPTIMAL, which is silent and would have been believed had mass 4 not had
a known answer of 40. The control saved it. The other track's census sets
num_search_workers = 1 correctly; this was my error alone and their enumeration
is sound.

WHAT THIS DOES NOT DO.  It does not decide tau_2 and does not touch mass 16,
where the pencil-generated family alone has 123365 vectors -- a number this file
reproduces independently and which agrees with the other track's census. The
mass-12 result is a classification of load-excess profiles, which is a necessary
condition on a 113-leaf blocker, not a statement about blockers themselves.
tau_2 stays open in [111, 115].
"""

import argparse
import itertools
import json
import os
from collections import Counter, deque

Q = 3
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def geometry():
    def nm(v):
        i = next(k for k, x in enumerate(v) if x % Q)
        z = pow(v[i] % Q, -1, Q)
        return tuple((z * x) % Q for x in v)

    pts = sorted({nm(v) for v in itertools.product(range(Q), repeat=4)
                  if any(v)})
    idx = {p: i for i, p in enumerate(pts)}

    def sf(u, v):
        return (u[0] * v[1] - u[1] * v[0] + u[2] * v[3] - u[3] * v[2]) % Q

    lines = set()
    for a, b in itertools.combinations(range(40), 2):
        if sf(pts[a], pts[b]):
            continue
        S = set()
        for x in range(Q):
            for y in range(Q):
                if x or y:
                    S.add(idx[nm(tuple((x * pts[a][k] + y * pts[b][k]) % Q
                                       for k in range(4)))])
        if len(S) == 4:
            lines.add(tuple(sorted(S)))
    lines = sorted(lines)
    return pts, idx, sf, lines


def line_action_generators(pts, idx, sf, lines):
    """PSp(4,3) on the 40 lines, grown until the order is 25920 and asserted."""
    def nm(v):
        i = next(k for k, x in enumerate(v) if x % Q)
        z = pow(v[i] % Q, -1, Q)
        return tuple((z * x) % Q for x in v)

    lidx = {L: i for i, L in enumerate(lines)}
    ident = tuple(range(40))
    cands = []
    for v in pts:
        gp = tuple(idx[nm(tuple((pts[p][k] + sf(pts[p], v) * v[k]) % Q
                                for k in range(4)))] for p in range(40))
        if gp == ident:
            continue
        gl = tuple(lidx[tuple(sorted(gp[p] for p in lines[i]))]
                   for i in range(40))
        if gl != ident:
            cands.append(gl)

    gens, order = [], 1
    for g in cands:
        gens.append(g)
        S, frontier = {ident}, [ident]
        while frontier:
            nf = []
            for a in frontier:
                for h in gens:
                    b = tuple(h[a[i]] for i in range(40))
                    if b not in S:
                        S.add(b)
                        nf.append(b)
            frontier = nf
        order = len(S)
        if order == 25920:
            break
    assert order == 25920, order
    return gens, order


def census(k, adjL, thru, budget):
    from ortools.sat.python import cp_model
    m = cp_model.CpModel()
    e = [m.NewIntVar(0, 4 * k, "e%d" % i) for i in range(40)]
    for i in range(40):
        m.Add(sum(adjL[i][j] * e[j] for j in range(40)) == 2 * e[i] + k)
    m.Add(sum(e) == 4 * k)
    sols = []

    class CB(cp_model.CpSolverSolutionCallback):
        def __init__(self):
            cp_model.CpSolverSolutionCallback.__init__(self)

        def on_solution_callback(self):
            sols.append(tuple(self.Value(x) for x in e))

    sv = cp_model.CpSolver()
    # enumerate_all_solutions is COMPLETE ONLY WITH ONE WORKER. With more it
    # silently under-counts and still reports OPTIMAL.
    sv.parameters.num_workers = 1
    sv.parameters.enumerate_all_solutions = True
    sv.parameters.max_time_in_seconds = budget
    st = sv.Solve(m, CB())
    return set(sols), sv.StatusName(st)


def pencil_vectors(k, thru):
    out = set()
    for combo in itertools.combinations_with_replacement(range(40), k):
        v = [0] * 40
        for c in combo:
            for i in thru[c]:
                v[i] += 1
        out.add(tuple(v))
    return out


def orbit_sizes(vectors, gens):
    def act(vec, g):
        out = [0] * 40
        for i in range(40):
            out[g[i]] = vec[i]
        return tuple(out)

    rem, sizes = set(vectors), []
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
        assert o <= set(vectors), "orbit leaves the enumerated set"
        rem -= o
        sizes.append(len(o))
    return sorted(sizes)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--budget", type=float, default=900.0)
    ap.add_argument("--ks", type=int, nargs="+", default=[1, 2, 3])
    args = ap.parse_args()

    pts, idx, sf, lines = geometry()
    adjL = [[1 if i != j and set(lines[i]) & set(lines[j]) else 0
             for j in range(40)] for i in range(40)]
    thru = [[i for i, L in enumerate(lines) if p in L] for p in range(40)]
    gens, gorder = line_action_generators(pts, idx, sf, lines)

    rows = []
    for k in args.ks:
        adm, status = census(k, adjL, thru, args.budget)
        pg = pencil_vectors(k, thru)
        exc = adm - pg
        row = {
            "k": k, "mass": 4 * k,
            "admissible": len(adm), "solverStatus": status,
            "complete": status == "OPTIMAL",
            "pencilGenerated": len(adm & pg),
            "pencilFamilySize": len(pg),
            "exceptional": len(exc),
            "allPencilGenerated": not exc,
        }
        if status == "OPTIMAL":
            row["pencilOrbitSizes"] = orbit_sizes(adm & pg, gens)
            row["exceptionalOrbitSizes"] = orbit_sizes(exc, gens) if exc else []
            row["exceptionalOrbitCount"] = len(row["exceptionalOrbitSizes"])
            if row["exceptionalOrbitSizes"]:
                row["exceptionalStabiliserOrders"] = [
                    gorder // s for s in row["exceptionalOrbitSizes"]]
        rows.append(row)

    print("THE MASS-12 CENSUS, COMPLETED")
    print("=" * 74)
    print("  line-action group order: %d" % gorder)
    print()
    for r in rows:
        print("  mass %2d  admissible %6d [%s]  pencil-generated %6d"
              "  exceptional %5d"
              % (r["mass"], r["admissible"], r["solverStatus"],
                 r["pencilGenerated"], r["exceptional"]))
        if r.get("pencilOrbitSizes"):
            print("           pencil orbits      : %s" % r["pencilOrbitSizes"])
            print("           exceptional orbits : %s   stabilisers %s"
                  % (r["exceptionalOrbitSizes"],
                     r.get("exceptionalStabiliserOrders", [])))
    print()
    print("  masses 4 and 8 reproduce the other track's two theorems from an")
    print("  independently built geometry and find NO exceptions.")
    print("  mass 12 is exhaustive and splits into 8 pencil orbits + exactly")
    print("  ONE exceptional orbit -- the induction fails on a single class.")

    ok = all(r["complete"] for r in rows)
    print()
    print("VALID: %s" % ok)

    if args.write:
        assert ok, "a census did not reach OPTIMAL -- refusing to write"
        rec = {
            "schema": "holotrade.mass12-census-complete.v1",
            "valid": True,
            "lineActionGroupOrder": gorder,
            "rows": rows,
            "whatWasOpen": (
                "the other track proves mass 4 is one point-pencil and mass 8 "
                "exactly two, then reports the induction FAILING at mass 12 and "
                "16 and builds the_mass12_mass16_exact_orbit_census.py to "
                "classify what is really there. That script self-labels PARTIAL "
                "unless enumeration finishes OPTIMAL, and its committed run does "
                "not reach OPTIMAL at either mass -- it crashed before writing "
                "anything until ebd9a84 fixed a dict-sort TypeError in it. This "
                "completes MASS 12 exactly; mass 16 is NOT completed here and no "
                "claim is made about it."),
            "theResult": (
                "mass 12 has exactly 12920 admissible excesses, of which 11480 "
                "are pencil-generated and 1440 are not, with solver status "
                "OPTIMAL so the census is exhaustive. Under the line-action of "
                "PSp(4,3) the pencil-generated ones fall into EIGHT orbits of "
                "sizes 40, 160, 360, 480, 1080, 2160, 2880, 4320 -- summing to "
                "11480 -- and the exceptional ones form EXACTLY ONE orbit of size "
                "1440, stabiliser order 25920/1440 = 18. So the failure of the "
                "pencil induction at mass 12 is not a spray of sporadic "
                "counterexamples: it is a single class."),
            "massEightOrbitsAreTheirPairSplit": (
                "the mass-8 pencil orbits come out 40, 240, 540 -- which is "
                "exactly the pair_relation_split_40_240_540 recorded in the other "
                "track's mass_eight_excess_two_pencils.json: the same, collinear "
                "and non-collinear point pairs. Their theorem says mass 8 is two "
                "pencils, so the orbits of mass-8 excesses must be the orbits of "
                "unordered point pairs with repetition, and they are, computed "
                "here from an independently built line-action. That is a "
                "confirmation of their theorem down to the orbit decomposition, "
                "not merely the count."),
            "massesFourAndEightConfirmTheirTheorems": (
                "mass 4 gives 40 admissible against 40 pencil-generated and mass "
                "8 gives 820 against 820, both OPTIMAL and both with zero "
                "exceptions, from a geometry and adjacency built independently "
                "here. That is exactly what the mass-4 and mass-8 theorems "
                "assert, so those theorems are independently reproduced rather "
                "than assumed."),
            "theEnumerationGotcha": (
                "CP-SAT's enumerate_all_solutions is COMPLETE ONLY WITH "
                "num_workers = 1. Run with four workers the identical models "
                "return 38, 202 and 12756 -- under-counts -- and still report "
                "OPTIMAL, silently. It was caught only because mass 4 has a known "
                "answer of 40 and the control failed. The other track's census "
                "sets num_search_workers = 1 correctly; this was my error alone "
                "and their enumeration is sound."),
            "whatItDoesNotDo": (
                "it does not decide tau_2 and does not touch mass 16, where the "
                "pencil-generated family alone has 123365 vectors -- reproduced "
                "independently here and agreeing with the other track's census. A "
                "mass-12 classification is a necessary condition on a 113-leaf "
                "blocker's load profile, not a statement about blockers "
                "themselves. tau_2 stays open in [111, 115]."),
            "boundary": (
                "exhaustive at masses 4, 8 and 12: every census reached OPTIMAL "
                "with a single worker, and the certificate is refused if any did "
                "not. Orbits are computed by closure under generators of the "
                "line-action, whose order is ASSERTED to be 25920 before use, and "
                "each orbit is checked not to leave the enumerated set. Mass 16 "
                "is out of scope."),
        }
        p = os.path.join(ROOT, "data", "mass12_census_complete.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=2)
        print("written: %s" % p)


if __name__ == "__main__":
    main()
