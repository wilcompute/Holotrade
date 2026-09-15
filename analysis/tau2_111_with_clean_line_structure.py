#!/usr/bin/env python3
"""
tau_2(W(3,3)^2) at 111: the exact three-centre leaf model plus the structure every
clean line is forced to carry.

The exact model (the_111_exact_three_centre_leaf_csp.py) pins line loads -- on
each axis, 36 clean lines of load 11 and a dirty pencil of four lines of load
12 -- and requires every product tile L x M to be hit. It returned three
UNKNOWNs at 90 minutes a case (a104478).

THE MISSING IMPLIED STRUCTURE.  Row sets C_p = {q : X[p][q] = 1}. For a line L,
the union U_L of the C_p over p in L must block W(3,3), so |U_L| >= tau_1 = 11.
  * Clean line (load 11): |U_L| <= 11, so the four rows over L are pairwise
    DISJOINT and U_L is a MINIMUM blocker. At q = 3, delta = 11 - 10 = 1, and
    the excess of a minimum blocker is one point-pencil at a centre u. So for
    every line M, |U_L n M| = 1 + [u in M]; for every octet O = H u H^perp,
    |U_L n O| = 2 + [u in O] (the octet identity).
  * Dirty line (load 12): |U_L| >= 11, so at most one column is covered twice.
Both hold symmetrically for columns. CP-SAT cannot derive any of this from
local constraints, because it needs tau_1 = 11.

CONTROL.  The structural encoding (a centre one-hot, line counts, octet
identities) is checked by enumerating all 11-point sets that satisfy it, with
one worker (multi-worker enumeration undercounts). The result must be exactly
the minimum blockers of W(3,3), each verified to block.
"""

import argparse
import importlib.util
import itertools
import json
import os
import time

from ortools.sat.python import cp_model

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def geometry():
    spec = importlib.util.spec_from_file_location("g12", os.path.join(ROOT, "analysis", "the_10480_twelve_point_blockers.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    lines, adj, N = mod.geometry()
    lines = [sorted(L) for L in lines]
    assert len(lines) == 40 and all(len(L) == 4 for L in lines)
    return lines, [set(a) for a in adj]


def octets(lines, adj):
    out = set()
    for x in range(40):
        for y in range(x + 1, 40):
            if y in adj[x]:
                continue
            perp = set(range(40))
            for z in (x, y):
                perp &= adj[z] | {z} if False else adj[z]
            # {x,y}^perp (4 points), then its perp contains x, y (the hyperbolic line)
            hperp = perp
            hl = set(range(40))
            for z in hperp:
                hl &= adj[z]
            assert len(hperp) == 4 and len(hl) == 4 and x in hl and y in hl
            out.add(frozenset(hl | hperp))
    out = sorted(out, key=sorted)
    assert len(out) == 45
    return out


def blocker_structure(model, lines, octs, cells, prefix):
    """cells: 40 linear expressions (0/1-valued) giving the 11-point set. Adds centre one-hot and pinned counts."""
    a = [model.NewBoolVar(f"{prefix}_u{u}") for u in range(40)]
    model.AddExactlyOne(a)
    for M in lines:
        model.Add(sum(cells[q] for q in M) == 1 + sum(a[u] for u in M))
    for O in octs:
        model.Add(sum(cells[q] for q in O) == 2 + sum(a[u] for u in O))
    return a


def control(lines, adj, octs):
    """Enumerate 11-sets satisfying the structure; they must be exactly the minimum blockers."""
    m = cp_model.CpModel()
    x = [m.NewBoolVar(f"x{i}") for i in range(40)]
    m.Add(sum(x) == 11)
    blocker_structure(m, lines, octs, x, "c")
    sols = []

    class CB(cp_model.CpSolverSolutionCallback):
        def __init__(self):
            super().__init__()

        def on_solution_callback(self):
            sols.append(frozenset(i for i in range(40) if self.Value(x[i])))
    s = cp_model.CpSolver()
    s.parameters.enumerate_all_solutions = True
    s.parameters.num_workers = 1
    s.Solve(m, CB())
    structural = set(sols)
    # all minimum blockers by brute-force CP-SAT enumeration of 11-point blockers (no structure)
    m2 = cp_model.CpModel()
    y = [m2.NewBoolVar(f"y{i}") for i in range(40)]
    m2.Add(sum(y) == 11)
    for M in lines:
        m2.Add(sum(y[q] for q in M) >= 1)
    sols2 = []

    class CB2(cp_model.CpSolverSolutionCallback):
        def __init__(self):
            super().__init__()

        def on_solution_callback(self):
            sols2.append(frozenset(i for i in range(40) if self.Value(y[i])))
    s2 = cp_model.CpSolver()
    s2.parameters.enumerate_all_solutions = True
    s2.parameters.num_workers = 1
    s2.Solve(m2, CB2())
    blockers = set(sols2)
    return len(structural), len(blockers), structural == blockers


def dirty_structure(model, lines, octs, cover, d, prefix):
    """load-12 union: set s = cover - d has 11 or 12 points; excess = y with y >= 0 integer,
    sum y = 2 - sum d (12-point blockers: two pencils, the_10480_twelve_point_blockers.py; 11: one)."""
    y = [model.NewIntVar(0, 2, f"{prefix}_y{u}") for u in range(40)]
    s = [cover[q] - d[q] for q in range(40)]
    model.Add(sum(y) + sum(d) == 2)
    for M in lines:
        model.Add(sum(s[q] for q in M) == 1 + sum(y[u] for u in M))
    for O in octs:
        model.Add(sum(s[q] for q in O) == 2 + sum(y[u] for u in O))
    return y


def control_dirty(lines, octs):
    """12-sets satisfying the two-pencil pinned structure (d = 0) must be exactly the 10,480 twelve-point blockers."""
    counts = []
    for structured in (True, False):
        m = cp_model.CpModel()
        x = [m.NewBoolVar(f"x{i}") for i in range(40)]
        m.Add(sum(x) == 12)
        if structured:
            dirty_structure(m, lines, octs, x, [0] * 40, "t")
        else:
            for M in lines:
                m.Add(sum(x[q] for q in M) >= 1)
        sols = set()

        class CB(cp_model.CpSolverSolutionCallback):
            def on_solution_callback(self):
                sols.add(frozenset(i for i in range(40) if self.Value(x[i])))
        s = cp_model.CpSolver()
        s.parameters.enumerate_all_solutions = True
        s.parameters.num_workers = 1
        s.Solve(m, CB())
        counts.append(sols)
    return len(counts[0]), len(counts[1]), counts[0] == counts[1]


def solve_case(name, centres, lines, octs, budget, workers, structure=True, dirty=False, recip=False, adj=None):
    c_row, c_col = centres
    dirty_rows = {i for i, L in enumerate(lines) if c_row in L}
    dirty_cols = {j for j, L in enumerate(lines) if c_col in L}
    m = cp_model.CpModel()
    X = [[m.NewBoolVar(f"x_{p}_{q}") for q in range(40)] for p in range(40)]
    m.Add(sum(X[p][q] for p in range(40) for q in range(40)) == 111)
    for i, L in enumerate(lines):
        m.Add(sum(X[p][q] for p in L for q in range(40)) == (12 if i in dirty_rows else 11))
    for j, M in enumerate(lines):
        m.Add(sum(X[p][q] for p in range(40) for q in M) == (12 if j in dirty_cols else 11))
    for L in lines:
        for M in lines:
            m.Add(sum(X[p][q] for p in L for q in M) >= 1)
    aR, aC, dR, dC, yR, yC = {}, {}, {}, {}, {}, {}
    if structure:
        for i, L in enumerate(lines):
            cover = [sum(X[p][q] for p in L) for q in range(40)]
            if i in dirty_rows:
                d = [m.NewBoolVar(f"dr{i}_{q}") for q in range(40)]
                for q in range(40):
                    m.Add(cover[q] <= 1 + d[q])
                    m.Add(cover[q] >= 2 * d[q])
                m.Add(sum(d) <= 1)
                dR[i] = d
                if dirty:
                    yR[i] = dirty_structure(m, lines, octs, cover, d, f"DR{i}")
            else:
                for q in range(40):
                    m.Add(cover[q] <= 1)
                aR[i] = blocker_structure(m, lines, octs, cover, f"R{i}")
                for q in range(40):
                    m.Add(cover[q] + aR[i][q] <= 1)
        for j, M in enumerate(lines):
            cover = [sum(X[p][q] for q in M) for p in range(40)]
            if j in dirty_cols:
                d = [m.NewBoolVar(f"dc{j}_{p}") for p in range(40)]
                for p in range(40):
                    m.Add(cover[p] <= 1 + d[p])
                    m.Add(cover[p] >= 2 * d[p])
                m.Add(sum(d) <= 1)
                dC[j] = d
                if dirty:
                    yC[j] = dirty_structure(m, lines, octs, cover, d, f"DC{j}")
            else:
                for p in range(40):
                    m.Add(cover[p] <= 1)
                aC[j] = blocker_structure(m, lines, octs, cover, f"C{j}")
                for p in range(40):
                    m.Add(cover[p] + aC[j][p] <= 1)
    if recip:
        assert dirty and adj is not None
        # centre reciprocity: |X n (L x M)| from both sides, L and M clean
        for i in aR:
            for j in aC:
                m.Add(sum(aR[i][q] for q in lines[j]) == sum(aC[j][p] for p in lines[i]))
        cperp = adj[c_row] - {c_row}
        cpperp = adj[c_col] - {c_col}
        E = [sum(yR[i][q] + dR[i][q] for i in yR) for q in range(40)]
        F = [sum(yC[j][p] + dC[j][p] for j in yC) for p in range(40)]
        for j, M in enumerate(lines):
            if j in aC:
                m.Add(sum(E[q] for q in M) == sum(aC[j][p] for p in cperp) + 4 * aC[j][c_row])
            else:
                m.Add(sum(E[q] for q in M) == 8 - sum(aR[i][q] for i in aR for q in M))
        for i, L in enumerate(lines):
            if i in aR:
                m.Add(sum(F[p] for p in L) == sum(aR[i][q] for q in cpperp) + 4 * aR[i][c_col])
            else:
                m.Add(sum(F[p] for p in L) == 8 - sum(aC[j][p] for j in aC for p in L))
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = budget
    s.parameters.num_workers = workers
    t0 = time.time()
    st = s.Solve(m)
    status = {cp_model.OPTIMAL: "SAT", cp_model.FEASIBLE: "SAT", cp_model.INFEASIBLE: "UNSAT"}.get(st, "UNKNOWN")
    out = {"case": name, "centres": [c_row, c_col], "status": status, "seconds": round(time.time() - t0, 1),
           "branches": s.NumBranches(), "conflicts": s.NumConflicts()}
    if status == "SAT":
        leaves = {(p, q) for p in range(40) for q in range(40) if s.Value(X[p][q])}
        assert len(leaves) == 111
        assert all(any((p, q) in leaves for p in L for q in M) for L in lines for M in lines)
        out["leaves"] = sorted(map(list, leaves))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=float, default=1200)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--case", default="all")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--dirty", action="store_true", help="also pin the load-12 unions (two-pencil excess)")
    ap.add_argument("--recip", action="store_true", help="add explicit centre reciprocity and dirty-excess bookkeeping")
    args = ap.parse_args()
    lines, adj = geometry()
    octs = octets(lines, adj)
    ns, nb, same = control(lines, adj, octs)
    print("control: structural 11-sets %d, 11-point blockers %d, identical %s" % (ns, nb, same), flush=True)
    assert same
    dctl = None
    if args.dirty:
        dctl = control_dirty(lines, octs)
        print("dirty control: structural 12-sets %d, 12-point blockers %d, identical %s" % dctl, flush=True)
        assert dctl[2] and dctl[1] == 10480
    c0 = 0
    reps = {"equal": (c0, c0), "collinear": (c0, min(adj[c0])), "noncollinear": (c0, min(set(range(40)) - adj[c0] - {c0}))}
    names = list(reps) if args.case == "all" else [args.case]
    cases = {}
    for nm in names:
        r = solve_case(nm, reps[nm], lines, octs, args.budget, args.workers, dirty=args.dirty, recip=args.recip, adj=adj)
        cases[nm] = r
        print("%-13s %s %.1fs (branches %d, conflicts %d)" % (nm, r["status"], r["seconds"], r["branches"], r["conflicts"]), flush=True)
    all_unsat = set(cases) == set(reps) and all(r["status"] == "UNSAT" for r in cases.values())
    print("all three UNSAT (tau_2 >= 112):", all_unsat)
    if args.write:
        rec = {"schema": "holotrade.tau2-111-clean-line-structure.v1", "controlStructuralSets": ns,
               "controlMinimumBlockers": nb, "controlIdentical": same, "cases": cases,
               "dirtyStructure": bool(args.dirty), "reciprocity": bool(args.recip),
               "dirtyControl": list(dctl) if dctl else None,
               "allThreeUnsat": all_unsat, "tau2Interval": [112, 115] if all_unsat else [111, 115]}
        with open(os.path.join(ROOT, "data", "tau2_111_clean_line_structure.json"), "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=2)


if __name__ == "__main__":
    main()
