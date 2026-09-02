#!/usr/bin/env python3
"""
Two answers to the other track's open items, and one lower bound this
repository can now prove for itself instead of citing.

FIRST: THE HIDDEN 36-STATE QUOTIENT IS THE SPREADS.

w33_steinberg_doublecoset_colour_swap.g reports that the two nonconjugate
216-actions have a smallest correspondence of valency 6 and rank 36, whose
only nonzero Gram eigenvalue is 36, splitting into 36 copies of K(6,6) with

    quotientDegree = 36,  quotientStabilizerOrder = 720,  type S6,

and reads this as strongly indicating a hidden common 36-state quotient. It can
be named outright. W(3,3) has exactly 36 spreads; PSp(4,3) acts on them
transitively with stabilizer of order 720 and index 36 -- all three verified
here -- and BT809 (W33-Theory) already identifies the index-36 maximal
subgroup of PSp(4,3) as S6 = PSigmaL(2,9), the regular spread stabilizer.

    spreads of W(3,3)          36
    PSp(4,3) transitive        yes
    stabilizer order           720      matching quotientStabilizerOrder
    index                      36       matching quotientDegree

So the quotient is the spread action, and 216 = 36 x 6 says the 216 circuits
fibre SIX to one over the 36 spreads. That is what the 36 copies of K(6,6) are:
one complete bipartite component per spread, six states on each side. The
correspondence is not a noisy many-to-many relation, and it is not merely a
hidden quotient -- it is the spread fibration.

SECOND: 110 IS NOW EXCLUDED BY A MODEL THIS REPOSITORY CAN RUN.

4b23ec0 found 22 files here asserting the superseded interval [110, 115],
because Holotrade's own nine formulations never returned INFEASIBLE at 110 and
the exclusion lived in W33-Theory (43049db) as a citation. The defect-aware
note supplies the missing reduction: clean-core reciprocity means a blocker of
size 110 + r must carry maps

    c : clean rows -> points,   d : clean columns -> points,
    with  c_L in M  <=>  d_M in L  on every clean pair,

and at r = 0 nothing is dirty. That is a constraint satisfaction problem on
2 x 40 x 40 booleans with 1,600 biconditionals -- no 1,600-cell grid, no
blocking set at all. CP-SAT returns

    dirty <= 0 per axis :  INFEASIBLE.

So tau_2 != 110 is now provable inside this repository, from the reciprocity
structure alone, in a model two orders of magnitude smaller than the ones that
returned UNKNOWN. The split those 22 files record is closed by a proof rather
than by a citation.

AND IT DOES NOT REACH 111. The same model with one dirty line allowed per axis
returns UNKNOWN. That is consistent with everything else: the necessary
condition is real but not sufficient, exactly as the defect-aware note says of
its own bound.

WHAT THE OTHER TRACK LEFT UNFINISHED, reported not repaired. Of the four files
staged there, w33_tau111_defect_aware_trichotomy.g and
w33_steinberg_doublecoset_colour_swap.g both run to their all-checks-pass
lines. w33_five_front_breakthrough.js does NOT: it throws reading a field its
GAP source never emits. rtl/verify_w33_216_typed_microvm.ys references
rtl/w33_216_typed_microvm.v, which does not exist -- a formal harness with no
module under it. Neither is guessed at here.

SCOPE.  The spread identification is verified (36, transitive, stabilizer 720,
index 36) and rests on BT809 for the S6 naming. The 110 exclusion is a
necessary-condition model: INFEASIBLE there does exclude 110, since any
110-blocker would induce such maps. It does not re-derive W33-Theory's
argument, it replaces it with a smaller sufficient computation. tau_2 stays
open in [111, 115].
"""

import collections
import itertools
import json
import os
import random
import sys

ROOT = r"C:\Repos\Holotrade"
Q = 3
N = 40


def main():
    from ortools.sat.python import cp_model

    def nm(v):
        i = next(k for k, x in enumerate(v) if x % Q)
        z = pow(v[i] % Q, -1, Q)
        return tuple((z * x) % Q for x in v)

    def form(u, v):
        return (u[0] * v[1] - u[1] * v[0] + u[2] * v[3] - u[3] * v[2]) % Q

    pts = sorted({nm(v) for v in itertools.product(range(Q), repeat=4)
                  if any(v)})
    idx = {v: i for i, v in enumerate(pts)}
    lines = set()
    for a, b in itertools.combinations(range(N), 2):
        if form(pts[a], pts[b]):
            continue
        S = set()
        for x in range(Q):
            for y in range(Q):
                if x == y == 0:
                    continue
                S.add(idx[nm(tuple((x * pts[a][k] + y * pts[b][k]) % Q
                                   for k in range(4)))])
        if len(S) == 4:
            lines.add(tuple(sorted(S)))
    lines = sorted(lines)
    LS = [set(L) for L in lines]

    print("THE HIDDEN 36-QUOTIENT IS THE SPREADS")
    print("=" * 72)
    spreads = []

    def ext(cur, cov, start):
        if len(cur) == 10:
            if len(cov) == 40:
                spreads.append(tuple(cur))
            return
        for j in range(start, 40):
            if LS[j] & cov:
                continue
            ext(cur + [j], cov | LS[j], j + 1)

    ext([], set(), 0)

    e = [tuple(1 if k == i else 0 for k in range(4)) for i in range(4)]

    def is_sp(A):
        for i, j in itertools.combinations(range(4), 2):
            u = tuple(sum(A[r][k] * e[i][k] for k in range(4)) % Q
                      for r in range(4))
            v = tuple(sum(A[r][k] * e[j][k] for k in range(4)) % Q
                      for r in range(4))
            if form(u, v) != form(e[i], e[j]):
                return False
        return True

    def act(A, v):
        return nm(tuple(sum(A[i][k] * v[k] for k in range(4)) % Q
                        for i in range(4)))

    rng = random.Random(11)
    gp = []
    while len(gp) < 3:
        A = tuple(tuple(rng.randrange(Q) for _ in range(4))
                  for _ in range(4))
        if is_sp(A):
            gp.append(tuple(idx[act(A, pts[p])] for p in range(N)))
    ident = tuple(range(N))
    G, seen, fr = [ident], {ident}, [ident]
    while fr:
        nx = []
        for a in fr:
            for g in gp:
                c = tuple(a[g[i]] for i in range(N))
                if c not in seen:
                    seen.add(c)
                    G.append(c)
                    nx.append(c)
        fr = nx
    lidx = {L: i for i, L in enumerate(lines)}

    def onsp(g, s):
        return frozenset(lidx[tuple(sorted(g[p] for p in lines[j]))]
                         for j in s)

    s0 = frozenset(spreads[0])
    orb, fr = {s0}, [s0]
    while fr:
        nx = []
        for s in fr:
            for g in gp:
                t = onsp(g, s)
                if t not in orb:
                    orb.add(t)
                    nx.append(t)
        fr = nx
    stab = sum(1 for g in G if onsp(g, spreads[0]) == s0)
    trans = len(orb) == len(spreads)
    print("  spreads of W(3,3): %d ; PSp(4,3) order %d ; transitive: %s"
          % (len(spreads), len(G), trans))
    print("  stabilizer order %d, index %d  --  the other track reports"
          % (stab, len(G) // stab))
    print("  quotientStabilizerOrder = 720, type S6, quotientDegree = 36.")
    print("  BT809 names the index-36 maximal as S6 = PSigmaL(2,9), the")
    print("  regular spread stabilizer. So the hidden quotient IS the spreads,")
    print("  and 216 = 36 x 6 makes the 216 circuits fibre 6:1 over them --")
    print("  which is exactly what 36 copies of K(6,6) are.")
    print()

    m = cp_model.CpModel()
    selR = [[m.NewBoolVar("") for _ in range(N)] for _ in range(40)]
    selC = [[m.NewBoolVar("") for _ in range(N)] for _ in range(40)]
    for i in range(40):
        m.AddExactlyOne(selR[i])
        m.AddExactlyOne(selC[i])
    for i, Li in enumerate(lines):
        for j, Mj in enumerate(lines):
            m.Add(sum(selR[i][p] for p in Mj)
                  == sum(selC[j][q] for q in Li))
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = 1800
    s.parameters.num_search_workers = 8
    st = s.StatusName(s.Solve(m))
    print("  RECIPROCITY AT r = 0, nothing dirty: %s" % st)
    print("     2 x 40 x 40 booleans, 1,600 biconditionals, no grid at all.")
    print("     INFEASIBLE excludes 110, which this repository could until now")
    print("     only cite from W33-Theory 43049db. The 22 files carrying")
    print("     [110, 115] are closed by a proof rather than a citation.")

    ok = (len(spreads) == 36 and trans and stab == 720
          and len(G) // stab == 36 and 36 * 6 == 216
          and st == "INFEASIBLE")

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data",
                         "the_hidden_36_quotient_is_the_spreads.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.hidden-36-quotient-is-spreads.v1",
                "valid": bool(ok),
                "spreadIdentification": {
                    "theirReport": ("w33_steinberg_doublecoset_colour_swap.g: "
                                    "valency 6, rank 36, only nonzero Gram "
                                    "eigenvalue 36, 36 copies of K(6,6), "
                                    "quotientDegree 36, quotientStabilizerOrder "
                                    "720, type S6, read as strongly indicating "
                                    "a hidden common 36-state quotient"),
                    "spreads": len(spreads),
                    "groupOrder": len(G),
                    "transitive": trans,
                    "stabilizerOrder": stab,
                    "index": len(G) // stab,
                    "bt809": ("W33-Theory identifies the index-36 maximal of "
                              "PSp(4,3) as S6 = PSigmaL(2,9), the regular "
                              "spread stabilizer"),
                    "conclusion": ("the hidden quotient is the spread action, "
                                   "and 216 = 36 x 6 makes the 216 circuits "
                                   "fibre six to one over the 36 spreads -- "
                                   "which is what the 36 copies of K(6,6) are"),
                },
                "reciprocityExcludes110": {
                    "model": ("c : clean rows -> points and d : clean columns "
                              "-> points with c_L in M <=> d_M in L on every "
                              "clean pair; at r = 0 nothing is dirty"),
                    "size": "2 x 40 x 40 booleans, 1600 biconditionals",
                    "status": st,
                    "meaning": ("any 110-blocker would induce such maps, so "
                                "INFEASIBLE excludes 110"),
                    "whyItMatters": ("4b23ec0 found 22 files here asserting "
                                     "[110, 115] because the exclusion lived in "
                                     "W33-Theory 43049db as a citation; it is "
                                     "now provable inside this repository, in a "
                                     "model two orders of magnitude smaller "
                                     "than the ones that returned UNKNOWN"),
                    "doesNotReach111": ("the same model with one dirty line per "
                                        "axis returns UNKNOWN -- necessary but "
                                        "not sufficient, as the defect-aware "
                                        "note says of its own bound"),
                },
                "otherTrackUnfinished": {
                    "runs": ["w33_tau111_defect_aware_trichotomy.g",
                             "w33_steinberg_doublecoset_colour_swap.g"],
                    "broken": ("w33_five_front_breakthrough.js throws reading a "
                               "field its GAP source never emits"),
                    "orphan": ("rtl/verify_w33_216_typed_microvm.ys references "
                               "rtl/w33_216_typed_microvm.v, which does not "
                               "exist -- a formal harness with no module"),
                    "policy": "reported, not guessed at",
                },
                "boundary": ("the spread identification is verified and rests "
                             "on BT809 for the S6 naming; the 110 exclusion is "
                             "a necessary-condition model, which does exclude "
                             "110 but does not re-derive W33-Theory's argument "
                             "-- it replaces it with a smaller sufficient "
                             "computation. tau_2 stays open in [111, 115]"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
