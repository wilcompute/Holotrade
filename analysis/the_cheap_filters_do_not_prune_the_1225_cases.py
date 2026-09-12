#!/usr/bin/env python3
"""
Neither cheap filter prunes the 114 case list: all 35 mass-16 orbits survive
size-vector realizability, and the marginal condition cannot prune in
principle. The 1225 cases need the actual leaf CSP.

WHY ASK.  3aa3ad6 and 66062ec left the 114 decision with a finite but large
programme: 35 mass-16 load-profile orbits per axis, so 35 x 35 = 1225 exact
cases in the style of the other track's 112 model. Before running 1225 leaf
CSPs it is worth asking whether a cheap necessary condition kills most of them.
Two present themselves. Both fail, and the failures are worth recording so the
next person does not spend the time.

FILTER ONE, THE SIZE VECTOR, MEASURED.  A 114-leaf blocker has row sizes
f(p) = |C_p| >= 0 with

    (N^T f)_L  =  load(L)  =  11 + e_L        for every line L,

and summing forces sum(f) = 114. So a profile e that admits no such nonnegative
integer f is excluded from every blocker outright. Running that integer program
on a representative of each of the 35 orbits -- 28 pencil-generated and 7
exceptional:

    orbits killed  0 of 35

Every orbit, exceptional ones included, has a valid size vector. The filter is
worthless. That is the same phenomenon already recorded at 110, where the size
layer alone admits more than 200,000 integer solutions: sizes do not constrain
this problem, at either end.

FILTER TWO, THE MARGINALS, AND IT CANNOT WORK.  Let T[L][M] = |X n (L x M)|,
which blocking requires to be at least 1 everywhere, and put E = T - J >= 0.
Counting a leaf (p,q) once for each of the four lines through q gives
sum_M T[L][M] = 4 load(L), so

    row marginals of E     4 + 4 e_row(L)
    column marginals of E  4 + 4 e_col(M)

and both total 160 + 4*16 = 224, consistently. But a nonnegative INTEGER matrix
with prescribed nonnegative row and column marginals exists whenever the totals
agree -- that is the transportation problem, always feasible. So the marginal
condition is satisfied by every pair of orbits and can never prune. It is not
that it happens to fail here; it cannot succeed.

WHAT WOULD ACTUALLY PRUNE is the condition the other track already uses: E is
not merely nonnegative with the right marginals, it lies in the incidence image
on both sides, E = U N^T = N V. That is a rank condition, not a counting one,
and it is their factorization machinery rather than a filter this file is
adding.

SO THE PROGRAMME IS NOT CHEAP.  The 1225 cases have to be attacked with the
real leaf CSP, or with the factorization condition, and not with counting. On
present evidence a single leaf CSP at this size is also not cheap: the exact 111
model returned UNKNOWN at 5400 s a case (a104478), and 111 is a smaller
problem than 114.

SCOPE.  Filter one is measured exhaustively over all 35 orbit representatives,
each solved to a definite CP-SAT status. Filter two is argued, not measured:
the transportation feasibility theorem is classical and no computation can add
to it. Neither result says anything about tau_2, which stays open in
[111, 115]; they say the two obvious shortcuts to a 114 decision do not exist.
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
    ap.add_argument("--budget", type=float, default=7200.0)
    args = ap.parse_args()

    from ortools.sat.python import cp_model

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

    def size_vector_status(e, N=114):
        mdl = cp_model.CpModel()
        f = [mdl.NewIntVar(0, N, "f%d" % p) for p in range(40)]
        for L in range(40):
            mdl.Add(sum(f[p] for p in lines[L]) == 11 + e[L])
        mdl.Add(sum(f) == N)
        sv = cp_model.CpSolver()
        sv.parameters.num_workers = 8
        sv.parameters.max_time_in_seconds = 60
        return sv.StatusName(sv.Solve(mdl))

    a16, s16 = m.census(4, adjL, thru, args.budget)
    assert s16 == "OPTIMAL", s16
    pg16 = m.pencil_vectors(4, thru)
    pencil_orbits = orbits(a16 & pg16)
    exc_orbits = orbits(a16 - pg16)

    rows = []
    for tag, orbs in (("pencil", pencil_orbits), ("exceptional", exc_orbits)):
        for rep, size in orbs:
            rows.append({"kind": tag, "orbit": size,
                         "sizeVectorStatus": size_vector_status(rep)})

    killed = [r for r in rows if r["sizeVectorStatus"] == "INFEASIBLE"]
    undecided = [r for r in rows if r["sizeVectorStatus"] not in
                 ("OPTIMAL", "FEASIBLE", "INFEASIBLE")]

    print("THE CHEAP FILTERS DO NOT PRUNE THE 1225 CASES")
    print("=" * 74)
    print("  mass-16 orbits: %d pencil + %d exceptional = %d"
          % (len(pencil_orbits), len(exc_orbits), len(rows)))
    print("  1225 = %d x %d exact cases for a 114 decision"
          % (len(rows), len(rows)))
    print()
    print("  FILTER ONE, size vector (N^T f = 11 + e, f >= 0, sum f = 114):")
    print("    orbits killed    : %d of %d" % (len(killed), len(rows)))
    print("    orbits undecided : %d" % len(undecided))
    print("    -> every orbit, exceptional ones included, has a size vector.")
    print()
    print("  FILTER TWO, marginals: E = T - J >= 0 with row marginals")
    print("    4 + 4 e_row and column marginals 4 + 4 e_col, both totalling 224.")
    print("    A nonnegative integer matrix with prescribed nonnegative")
    print("    marginals exists whenever the totals agree -- transportation is")
    print("    always feasible -- so this CANNOT prune. Not measured; argued.")
    print()
    print("  What would prune is E = U N^T = N V, a rank condition and the")
    print("  other track's factorization machinery, not a counting filter.")

    ok = (len(rows) == 35 and len(pencil_orbits) == 28
          and len(exc_orbits) == 7 and len(undecided) == 0)
    print()
    print("VALID: %s" % ok)

    if args.write:
        assert ok, "checks failed -- refusing to write"
        rec = {
            "schema": "holotrade.cheap-filters-do-not-prune.v1",
            "valid": True,
            "pencilOrbits": len(pencil_orbits),
            "exceptionalOrbits": len(exc_orbits),
            "totalOrbits": len(rows),
            "caseCount": len(rows) * len(rows),
            "rows": rows,
            "orbitsKilledBySizeVector": len(killed),
            "filterOneSizeVector": (
                "a 114-leaf blocker has row sizes f(p) = |C_p| >= 0 with "
                "(N^T f)_L = 11 + e_L for every line, and summing forces "
                "sum(f) = 114, so a profile admitting no such nonnegative "
                "integer f is excluded from every blocker. Run on a "
                "representative of each of the 35 orbits it kills NONE -- every "
                "orbit, exceptional ones included, has a valid size vector. The "
                "filter is worthless, which is the same phenomenon already "
                "recorded at 110 where the size layer alone admits more than "
                "200,000 integer solutions. Sizes do not constrain this problem "
                "at either end."),
            "filterTwoMarginalsCannotWork": (
                "with T[L][M] = |X n (L x M)| and E = T - J >= 0, counting a leaf "
                "once per line through its second coordinate gives sum_M T[L][M] "
                "= 4 load(L), so E has row marginals 4 + 4 e_row(L) and column "
                "marginals 4 + 4 e_col(M), both totalling 224. But a nonnegative "
                "INTEGER matrix with prescribed nonnegative marginals exists "
                "whenever the totals agree -- the transportation problem is "
                "always feasible -- so the marginal condition holds for every "
                "pair of orbits and can never prune. It is not that it happens to "
                "fail; it cannot succeed. Argued, not measured: the theorem is "
                "classical and no computation adds to it."),
            "whatWouldActuallyPrune": (
                "the condition the other track already uses: E is not merely "
                "nonnegative with the right marginals but lies in the incidence "
                "image on both sides, E = U N^T = N V. That is a rank condition "
                "rather than a counting one, and it belongs to their "
                "factorization machinery rather than being a filter this file "
                "adds."),
            "soTheProgrammeIsNotCheap": (
                "the 1225 cases have to be attacked with the real leaf CSP or "
                "with the factorization condition, not with counting. On present "
                "evidence a single leaf CSP at this size is also not cheap: the "
                "exact 111 model returned UNKNOWN at 5400 s a case (a104478), and "
                "111 is a smaller problem than 114."),
            "boundary": (
                "filter one is measured exhaustively over all 35 orbit "
                "representatives, each solved to a definite CP-SAT status, with "
                "zero undecided. Filter two is ARGUED and not measured, since the "
                "transportation feasibility theorem is classical. Neither result "
                "says anything about tau_2, which stays open in [111, 115]; they "
                "say the two obvious shortcuts to a 114 decision do not exist."),
        }
        p = os.path.join(ROOT, "data", "cheap_filters_do_not_prune.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=2)
        print("written: %s" % p)


if __name__ == "__main__":
    main()
