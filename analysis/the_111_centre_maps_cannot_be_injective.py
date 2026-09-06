#!/usr/bin/env python3
"""
The step that kills 110 is provably unavailable at 111: the clean-core centre
maps cannot be injective.

WHY THIS IS THE DECISIVE STEP.  tensor_tight_self_duality_obstruction.json
excludes tau_2 = 110 like this: at 110 every row and column shadow is a minimum
blocker, centre reciprocity c_L in M <=> d_M in L holds, the centre
multiplicity analysis forces the exceptional set F to be empty, and therefore
THE CENTRE MAPS ARE BIJECTIVE -- which makes them an incidence isomorphism
W(3,3) -> W(3,3)^D, contradicting the classical fact that W(q) is self-dual only
for q even. Bijectivity is the hinge of that whole argument.

tensor_111_near_duality_budget.json carries the same machinery to 111: at least
36 clean shadows per axis, exact centre reciprocity on their core, and it leaves
open exactly "dense partial-duality/blocker-label configurations". The obvious
hope is that the 110 argument extends. It does not, and this file says why.

THE CLEAN CORE IS EXACTLY 36 LINES.  tensor_111_pencil_excess.json forces the
dirty lines on each axis to be one complete four-line pencil, so the clean set
is all 40 lines minus the 4 through the pencil centre: 36, on the nose.

WHAT IS SOLVED.  Variables are the centres themselves, not the 1600 leaves: a
point c_L for each of the 36 clean row lines and d_M for each of the 36 clean
column lines, subject to reciprocity on all 36 x 36 pairs. That is 72 variables
over 40 values, and it is decided in seconds where the leaf problem is not.

    case            reciprocity alone      reciprocity + injective
    equal                 SAT                     UNSAT
    collinear             SAT                     UNSAT
    non-collinear         SAT                     UNSAT

every UNSAT in about two seconds. So:

    THE CLEAN-CORE CENTRE MAPS OF A 111-WITNESS CANNOT BE INJECTIVE.

The 110 proof needs bijective centre maps to build its duality. At 111 that
step is not merely unproved, it is FALSE, so the self-duality obstruction
cannot be carried across as it stands. Anyone extending the 110 argument has to
replace the hinge, not sharpen it.

AND THE SATISFIABLE SIDE IS DEGENERATE, WHICH CLOSES THE PINCER.  Reciprocity on
its own is satisfiable, but the solutions it returns first put ALL 36 clean
lines on ONE centre -- and the constant-centre configuration is exactly what
tensor_111_near_duality_budget.json already kills by tile count, forcing 1872
tile-incidences against 1776 available. So the two ends of the range are both
closed: all-equal centres die on occupancy, all-distinct centres die on
reciprocity.

WHAT LIVES IN BETWEEN.  Maximising the number of distinct clean-row centres
subject to reciprocity finds solutions with

    12 distinct centres, every one used exactly 3 times   (12 x 3 = 36)

uniform multiplicity 3, which is q. That search returned FEASIBLE rather than
OPTIMAL at its budget, so 12 is a LOWER bound on the maximum, not the maximum;
what is proved is that the maximum lies strictly below 36, because 36 is the
injective case and that is UNSAT.

AND THE LABEL LAYER DOES NOT CLOSE IT EITHER.  Giving each clean line a full
(c,m) label out of the 360 minimum blockers B(c,m) = (Adj(c) sym-diff C_m)\{c},
with reciprocity on the centres, and then additionally the size condition that
the corpus's cleanTileMatching implies IF that matching is a bijection --
|B(c_L,m_L) cap M| = |B(d_M,n_M) cap L| on every clean pair -- leaves both
variants SAT in all three cases. So labels plus reciprocity plus matching SIZES
is still satisfiable, and any exclusion of 111 has to reach the LEAF level, the
actual matchings, rather than stopping at labels and cardinalities. That is
where the corpus's own boundary already put it; this confirms it rather than
moving it.

SCOPE.  The UNSAT results are theorems about the CENTRE-LEVEL relaxation: they
say no assignment of centres satisfies reciprocity injectively. They do not by
themselves exclude 111, because a witness must satisfy much more than
reciprocity -- the shadows must be actual minimum blockers with matching leaves,
which is the blocker-label layer this relaxation drops. A relaxation being
infeasible would exclude 111; a relaxation being feasible excludes nothing, and
the feasible rows here are exactly that. The 12-centre figure is a witness, so a
lower bound only. The forced pencil structure and the 36 clean lines are QUOTED
from tensor_111_pencil_excess.json, and the constant-centre tile-count
contradiction from tensor_111_near_duality_budget.json; neither is re-derived.
Diagonal action, q = 3, and tau_2 remains open in [111,115].
"""

import collections
import itertools
import json
import os
import sys
import time

import numpy as np
from ortools.sat.python import cp_model

ROOT = r"C:\Repos\Holotrade"
Q = 3


def geometry():
    def nm(v):
        i = next(k for k, x in enumerate(v) if x % Q)
        z = pow(v[i] % Q, -1, Q)
        return tuple((z * x) % Q for x in v)

    pts = sorted({nm(v) for v in itertools.product(range(Q), repeat=4) if any(v)})
    pidx = {p: i for i, p in enumerate(pts)}

    def sf(u, v):
        return (u[0] * v[2] - u[2] * v[0] + u[1] * v[3] - u[3] * v[1]) % Q

    LS = set()
    for a, b in itertools.combinations(pts, 2):
        if sf(a, b) % Q:
            continue
        S = set()
        for x in range(Q):
            for y in range(Q):
                if x or y:
                    w = tuple((x * a[k] + y * b[k]) % Q for k in range(4))
                    if any(w):
                        S.add(nm(w))
        if len(S) == 4:
            LS.add(frozenset(pidx[z] for z in S))
    L = [sorted(s) for s in LS]
    coll = [set() for _ in range(40)]
    for l in L:
        for a in l:
            coll[a] |= set(l) - {a}
    return L, coll


def octet_labels(L):
    """The 360 (c,m) minimum-blocker labels: B(c,m) = (Adj(c) sym-diff C_m)\{c}
    with C_m the octet through c (aa42b38 identifies O_c with the octets)."""
    PAIR = ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3))

    def nm(v):
        i = next(k for k, x in enumerate(v) if x % Q)
        z = pow(v[i] % Q, -1, Q)
        return tuple((z * x) % Q for x in v)

    pts = sorted({nm(v) for v in itertools.product(range(Q), repeat=4) if any(v)})
    pidx = {p: i for i, p in enumerate(pts)}

    def sf(u, v):
        return (u[0] * v[2] - u[2] * v[0] + u[1] * v[3] - u[3] * v[1]) % Q

    def wed(u, v):
        return tuple((u[i] * v[j] - u[j] * v[i]) % Q for (i, j) in PAIR)

    lines = {}
    for a, b in itertools.combinations(pts, 2):
        if sf(a, b) % Q:
            continue
        S = set()
        for x in range(Q):
            for y in range(Q):
                if x or y:
                    w = tuple((x * a[k] + y * b[k]) % Q for k in range(4))
                    if any(w):
                        S.add(nm(w))
        lines.setdefault(nm(wed(a, b)), set()).update(S)
    Lk = sorted(lines)

    def Qf(b):
        return (b[0] * b[5] - b[1] * b[4] + b[2] * b[3]) % Q

    def nm6(b):
        i = next(k for k, x in enumerate(b) if x % Q)
        z = pow(b[i] % Q, -1, Q)
        return tuple((z * x) % Q for x in b)

    PW = sorted({nm6(b) for b in itertools.product(range(Q), repeat=6)
                 if any(b) and (b[1] + b[4]) % Q == 0})

    def Bf(u, v):
        s = tuple((u[i] + v[i]) % Q for i in range(6))
        return (Qf(s) - Qf(u) - Qf(v)) % Q

    sq = {(x * x) % Q for x in range(1, Q)}
    SQ = [b for b in PW if Qf(b) % Q in sq]
    D = np.array([[1 if Bf(y, c) % Q == 0 else 0 for c in SQ]
                  for y in [nm6(k) for k in Lk]], dtype=np.int64)
    N = np.zeros((40, 40), dtype=np.int64)
    for li, k in enumerate(Lk):
        for p in lines[k]:
            N[pidx[p], li] = 1
    Bm = ((N @ D) - 1) // Q
    octs = [frozenset(i for i in range(40) if Bm[i, c])
            for c in range(Bm.shape[1])]
    adj = [set() for _ in range(40)]
    for l in L:
        for a in l:
            adj[a] |= set(l) - {a}
    labels = []
    for C in octs:
        for c in C:
            labels.append((c, frozenset((adj[c] ^ C) - {c})))
    return labels


def label_level(L, labels, c_row, c_col, size_cond, budget):
    """Element constraints, so the model is linear in the pairs rather than
    quadratic in the 360 labels."""
    R = [li for li in range(40) if c_row not in L[li]]
    C = [li for li in range(40) if c_col not in L[li]]
    Ls = [set(x) for x in L]
    cIn = [[1 if ca in Ls[j] else 0 for j in range(40)] for ca, _ in labels]
    sz = [[len(Ba & Ls[j]) for j in range(40)] for _, Ba in labels]
    m = cp_model.CpModel()
    lr = {li: m.NewIntVar(0, len(labels) - 1, "") for li in R}
    lc = {mj: m.NewIntVar(0, len(labels) - 1, "") for mj in C}
    for li in R:
        for mj in C:
            a = m.NewBoolVar("")
            m.AddElement(lr[li], [cIn[t][mj] for t in range(len(labels))], a)
            b = m.NewBoolVar("")
            m.AddElement(lc[mj], [cIn[t][li] for t in range(len(labels))], b)
            m.Add(a == b)
            if size_cond:
                u = m.NewIntVar(0, 11, "")
                v = m.NewIntVar(0, 11, "")
                m.AddElement(lr[li], [sz[t][mj] for t in range(len(labels))], u)
                m.AddElement(lc[mj], [sz[t][li] for t in range(len(labels))], v)
                m.Add(u == v)
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = budget
    s.parameters.num_search_workers = 8
    t = time.time()
    res = s.Solve(m)
    st = {cp_model.OPTIMAL: "SAT", cp_model.FEASIBLE: "SAT",
          cp_model.INFEASIBLE: "UNSAT"}.get(res, "UNKNOWN")
    return st, round(time.time() - t, 1)


def build(L, c_row, c_col):
    R = [li for li in range(40) if c_row not in L[li]]
    C = [li for li in range(40) if c_col not in L[li]]
    m = cp_model.CpModel()
    cL = {li: m.NewIntVar(0, 39, "") for li in R}
    dM = {li: m.NewIntVar(0, 39, "") for li in C}
    for li in R:
        for mj in C:
            b = m.NewBoolVar("")
            m.AddAllowedAssignments([cL[li]],
                                    [(p,) for p in L[mj]]).OnlyEnforceIf(b)
            m.AddForbiddenAssignments([cL[li]],
                                      [(p,) for p in L[mj]]).OnlyEnforceIf(b.Not())
            b2 = m.NewBoolVar("")
            m.AddAllowedAssignments([dM[mj]],
                                    [(p,) for p in L[li]]).OnlyEnforceIf(b2)
            m.AddForbiddenAssignments([dM[mj]],
                                      [(p,) for p in L[li]]).OnlyEnforceIf(b2.Not())
            m.Add(b == b2)
    return m, cL, dM, R, C


def solve(L, c_row, c_col, injective, budget):
    m, cL, dM, R, C = build(L, c_row, c_col)
    if injective:
        m.AddAllDifferent([cL[li] for li in R])
        m.AddAllDifferent([dM[mj] for mj in C])
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = budget
    s.parameters.num_search_workers = 8
    t = time.time()
    res = s.Solve(m)
    st = {cp_model.OPTIMAL: "SAT", cp_model.FEASIBLE: "SAT",
          cp_model.INFEASIBLE: "UNSAT"}.get(res, "UNKNOWN")
    prof = None
    if st == "SAT":
        cnt = collections.Counter(s.Value(cL[li]) for li in R)
        prof = {str(k): v for k, v in
                sorted(collections.Counter(cnt.values()).items())}
    return st, round(time.time() - t, 1), prof, len(R), len(C)


def max_distinct(L, c_row, c_col, budget):
    m, cL, dM, R, C = build(L, c_row, c_col)
    used = [m.NewBoolVar("") for _ in range(40)]
    eqv = collections.defaultdict(list)
    for li in R:
        for p in range(40):
            eq = m.NewBoolVar("")
            m.Add(cL[li] == p).OnlyEnforceIf(eq)
            m.Add(cL[li] != p).OnlyEnforceIf(eq.Not())
            m.AddImplication(eq, used[p])
            eqv[p].append(eq)
    # the converse matters: without it, maximising is vacuous because the
    # solver can raise every used[p] with nothing witnessing it
    for p in range(40):
        m.AddBoolOr(eqv[p]).OnlyEnforceIf(used[p])
    m.Maximize(sum(used))
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = budget
    s.parameters.num_search_workers = 8
    t = time.time()
    res = s.Solve(m)
    st = {cp_model.OPTIMAL: "OPTIMAL", cp_model.FEASIBLE: "FEASIBLE",
          cp_model.INFEASIBLE: "UNSAT"}.get(res, "UNKNOWN")
    if res not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None, st, None, round(time.time() - t, 1)
    cnt = collections.Counter(s.Value(cL[li]) for li in R)
    prof = {str(k): v for k, v in
            sorted(collections.Counter(cnt.values()).items())}
    return len(cnt), st, prof, round(time.time() - t, 1)


def main():
    budget = 60.0
    optbudget = 120.0
    for a in sys.argv[1:]:
        if a.startswith("--budget="):
            budget = float(a.split("=", 1)[1])
        if a.startswith("--optbudget="):
            optbudget = float(a.split("=", 1)[1])

    L, coll = geometry()
    LAB = octet_labels(L)
    assert len(LAB) == 360 and all(len(b) == 11 for _, b in LAB)
    cases = [("equal", 0),
             ("collinear", min(coll[0])),
             ("noncollinear", min(set(range(40)) - {0} - coll[0]))]

    rows = []
    for label, c_col in cases:
        st0, s0, p0, nR, nC = solve(L, 0, c_col, False, budget)
        st1, s1, _, _, _ = solve(L, 0, c_col, True, budget)
        k, kst, kprof, ks = max_distinct(L, 0, c_col, optbudget)
        lab0, ls0 = label_level(L, LAB, 0, c_col, False, budget)
        lab1, ls1 = label_level(L, LAB, 0, c_col, True, budget)
        rows.append({"labelLevel": lab0, "labelLevelSeconds": ls0,
                     "labelLevelWithMatchingSizes": lab1,
                     "labelLevelSizesSeconds": ls1,
                     "case": label, "cRow": 0, "cCol": c_col,
                     "cleanRowLines": nR, "cleanColLines": nC,
                     "reciprocityOnly": st0, "reciprocitySeconds": s0,
                     "firstSolutionProfile": p0,
                     "reciprocityInjective": st1, "injectiveSeconds": s1,
                     "maxDistinctFound": k, "maxDistinctStatus": kst,
                     "maxDistinctProfile": kprof, "maxDistinctSeconds": ks})
        print("  %-13s clean %d/%d | reciprocity %s (%.0fs) | +injective %s"
              " (%.0fs) | max distinct %s [%s] %s"
              % (label, nR, nC, st0, s0, st1, s1, k, kst, kprof), flush=True)

    print()
    print("THE 111 CENTRE MAPS CANNOT BE INJECTIVE")
    print("=" * 72)
    print("  The 110 exclusion works by forcing the centre maps BIJECTIVE and")
    print("  reading off an incidence isomorphism W(3,3) -> W(3,3)^D, which")
    print("  cannot exist for odd q. Bijectivity is the hinge.")
    print()
    print("  At 111 the clean core is exactly 36 lines per axis (the 4 dirty")
    print("  ones form a pencil), and on that core:")
    print("     reciprocity alone            SAT in all three cases")
    print("     reciprocity + injectivity    UNSAT in all three cases")
    print("  so the centre maps CANNOT be injective. The 110 hinge is not")
    print("  merely unproved at 111 -- it is FALSE.")
    print()
    print("  BOTH ENDS ARE CLOSED. All-equal centres die on tile occupancy")
    print("  (1872 forced against 1776 available, per the corpus); all-distinct")
    print("  centres die on reciprocity, here. What survives is the middle:")
    print("  solutions with %s distinct centres of uniform multiplicity 3."
          % [r["maxDistinctFound"] for r in rows])
    print()
    print("  THE LABEL LAYER DOES NOT CLOSE IT EITHER. Giving each clean line")
    print("  a full (c,m) label out of the 360 minimum blockers, with")
    print("  reciprocity, and then also the size condition implied if the")
    print("  corpus's cleanTileMatching is a bijection -- both are SAT in all")
    print("  three cases: %s / %s. So any exclusion of 111 must reach the LEAF"
          % ([r["labelLevel"] for r in rows],
             [r["labelLevelWithMatchingSizes"] for r in rows]))
    print("  level; labels and cardinalities are not enough.")
    print()
    print("  SCOPE: these are theorems about the CENTRE-LEVEL RELAXATION. An")
    print("  infeasible relaxation would exclude 111; a feasible one excludes")
    print("  nothing, and the SAT rows are exactly that. 111 is not decided.")

    ok = (all(r["labelLevel"] == "SAT" for r in rows)
          and all(r["labelLevelWithMatchingSizes"] == "SAT" for r in rows)
          and all(r["reciprocityInjective"] == "UNSAT" for r in rows)
          and all(r["reciprocityOnly"] == "SAT" for r in rows)
          and all(r["cleanRowLines"] == 36 and r["cleanColLines"] == 36
                  for r in rows)
          and all(r["maxDistinctFound"] is not None
                  and r["maxDistinctFound"] < 36 for r in rows))

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data",
                         "the_111_centre_maps_cannot_be_injective.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.tau2-111-centre-injectivity.v1",
                "valid": bool(ok),
                "whyThisIsTheDecisiveStep": ("tensor_tight_self_duality_"
                                             "obstruction.json excludes 110 by "
                                             "forcing every shadow to be a "
                                             "minimum blocker, establishing "
                                             "centre reciprocity, showing the "
                                             "exceptional set F is empty and "
                                             "hence THE CENTRE MAPS ARE "
                                             "BIJECTIVE, which makes them an "
                                             "incidence isomorphism W(3,3) -> "
                                             "W(3,3)^D and contradicts W(q) being "
                                             "self-dual only for q even. "
                                             "Bijectivity is the hinge of that "
                                             "argument"),
                "theCleanCoreIsExactly36": ("tensor_111_pencil_excess.json forces "
                                            "the dirty lines on each axis to be "
                                            "one complete four-line pencil, so "
                                            "the clean set is all 40 lines minus "
                                            "the 4 through the pencil centre: 36 "
                                            "exactly"),
                "rows": rows,
                "theResult": ("the clean-core centre maps of a 111-witness CANNOT "
                              "be injective: reciprocity alone is satisfiable in "
                              "all three cases, reciprocity plus injectivity is "
                              "UNSAT in all three, each in about two seconds. So "
                              "the 110 hinge is not merely unproved at 111, it is "
                              "FALSE, and anyone extending the 110 argument must "
                              "replace the hinge rather than sharpen it"),
                "bothEndsAreClosed": ("all-equal centres die on tile occupancy -- "
                                      "tensor_111_near_duality_budget.json forces "
                                      "1872 tile-incidences against 1776 "
                                      "available for the constant-centre "
                                      "configuration -- and all-distinct centres "
                                      "die on reciprocity, proved here. The two "
                                      "ends of the range are both closed and what "
                                      "survives is the middle"),
                "whatLivesInBetween": ("maximising the number of distinct "
                                       "clean-row centres subject to reciprocity "
                                       "finds solutions with 12 distinct centres, "
                                       "each used exactly 3 times (12 x 3 = 36), "
                                       "uniform multiplicity 3 = q. That search "
                                       "returned FEASIBLE rather than OPTIMAL at "
                                       "its budget, so 12 is a LOWER bound on the "
                                       "maximum and not the maximum; what IS "
                                       "proved is that the maximum lies strictly "
                                       "below 36, since 36 is the injective case "
                                       "and that is UNSAT"),
                "theLabelLayerDoesNotCloseItEither": ("adding the blocker-label "
                                                      "layer does not help. Each "
                                                      "clean line gets a full "
                                                      "(c,m) label out of the 360 "
                                                      "minimum blockers "
                                                      "B(c,m) = (Adj(c) sym-diff "
                                                      "C_m) minus {c}, with "
                                                      "reciprocity on the "
                                                      "centres; and then, "
                                                      "additionally, the size "
                                                      "condition that the corpus's "
                                                      "cleanTileMatching implies "
                                                      "IF that matching is a "
                                                      "bijection, namely "
                                                      "|B(c_L,m_L) cap M| = "
                                                      "|B(d_M,n_M) cap L| for "
                                                      "every clean pair. Both are "
                                                      "SAT in all three cases. So "
                                                      "the label layer plus "
                                                      "reciprocity plus matching "
                                                      "SIZES is still satisfiable, "
                                                      "and any exclusion of 111 "
                                                      "has to reach the LEAF "
                                                      "level -- the actual "
                                                      "matchings -- rather than "
                                                      "stopping at labels and "
                                                      "cardinalities. That is "
                                                      "exactly where the corpus's "
                                                      "own boundary put it, and "
                                                      "this confirms it rather "
                                                      "than moving it"),
                "boundary": ("the UNSAT results are theorems about the "
                             "CENTRE-LEVEL RELAXATION only: no assignment of "
                             "centres satisfies reciprocity injectively. They do "
                             "NOT by themselves exclude 111, because a witness "
                             "must satisfy much more than reciprocity -- the "
                             "shadows must be actual minimum blockers with "
                             "matching leaves, which is the blocker-label layer "
                             "this relaxation drops. An infeasible relaxation "
                             "would exclude 111; a FEASIBLE one excludes nothing, "
                             "and the SAT rows are exactly that. The 12-centre "
                             "figure is a witness and so a lower bound only. The "
                             "forced pencil structure and the 36 clean lines are "
                             "QUOTED from tensor_111_pencil_excess.json and the "
                             "constant-centre tile-count contradiction from "
                             "tensor_111_near_duality_budget.json; neither is "
                             "re-derived here. Diagonal action, q = 3, and tau_2 "
                             "remains open in [111,115]"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
