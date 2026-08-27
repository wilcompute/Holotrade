#!/usr/bin/env python3
"""
Decompose the tight case: first enumerate the degree sequences, then test them.

Two full-model attacks on |X| = 110 have returned UNKNOWN, one at 1901 s and
one at 2300 s with a sound symmetry break.  Throwing more time at the same
formulation is not a plan.  This splits the problem instead.

THE SPLIT.  Write f(p) = |X_p| for the fibre sizes.  At |X| = 110 the double
count is tight on every line, so

    sum of f over the four points of L  =  11,   for all 40 lines,

and every fibre is an independent set, so 0 <= f(p) <= alpha = 7.  That is a
finite integer program in 40 unknowns, entirely independent of WHICH points
each fibre contains.  So enumerate every such f first.

The solution set is a coset: N^T f = 11 * 1 where N is the point-line
incidence matrix.  N N^T = 4I + A has eigenvalues 16, 6, 0 with multiplicities
1, 24, 15, so N has rank 25 and the kernel is the 15-dimensional (-4)
eigenspace of A.  Hence f lies in (11/4) * 1 + E_{-4}, and the box 0 <= f <= 7
cuts that 15-dimensional affine space down to something finite.

WHY THIS IS WORTH KNOWING.  The count alone decides how to proceed:

  * a SMALL number of sequences, especially up to Aut(W33)-symmetry, turns
    the tight case into a short list of independent subproblems, each one
    massively more constrained than the free problem -- every fibre size is
    then a fixed integer rather than a variable;
  * a LARGE number says this decomposition is not the way in, and says so
    cheaply rather than after another half hour of UNKNOWN.

Either way it is information, which two UNKNOWNs were not.  Nothing here
proves anything about tau_2 on its own: a degree sequence is necessary for a
110-leaf blocker, never sufficient.
"""

import json
import os
import subprocess
import sys
import time

try:
    from ortools.sat.python import cp_model
except ImportError:
    sys.exit("needs ortools:  py -3 -m pip install ortools")

ROOT = r"C:\Repos\Holotrade"
N = 40
TAU1 = 11
ALPHA = 7


def load():
    out = subprocess.run(
        ["node", "-e",
         "global.window=global;"
         "const S=require('./js/substrate.js');"
         "const SH=require('./scheduler/w33-shapes.js');"
         "process.stdout.write(JSON.stringify({"
         "lines:S.LINES.map(l=>[...l].sort((a,b)=>a-b)),"
         "gens:SH.generators().map(g=>Array.from(g))}));"],
        cwd=ROOT, capture_output=True, text=True)
    if out.returncode:
        sys.exit("node failed: " + out.stderr[:600])
    d = json.loads(out.stdout)
    return d["lines"], d["gens"]


class Collect(cp_model.CpSolverSolutionCallback):
    def __init__(self, fv, cap):
        super().__init__()
        self.fv, self.cap, self.found = fv, cap, []

    def on_solution_callback(self):
        self.found.append(tuple(self.Value(v) for v in self.fv))
        if len(self.found) >= self.cap:
            self.StopSearch()


def canonical(seq, gens):
    """Lexicographically least image of seq under the group, by orbit BFS."""
    best = seq
    seen = {seq}
    frontier = [seq]
    while frontier:
        nxt = []
        for s in frontier:
            for g in gens:
                img = [0] * N
                for p in range(N):
                    img[g[p]] = s[p]
                img = tuple(img)
                if img not in seen:
                    seen.add(img)
                    nxt.append(img)
                    if img < best:
                        best = img
        frontier = nxt
    return best, len(seen)



def proved_bounds(lines):
    """Optimise directly, so the reported bounds are proved, not observed.

    Enumerating and then reading off the min and max of what turned up is
    only valid if the enumeration COMPLETED.  It did not, so the extremes
    are computed by optimisation instead, and the solver status is kept.
    """
    out = {}
    for what in ("support", "maxfibre"):
        for sense in ("min", "max"):
            m = cp_model.CpModel()
            f = [m.NewIntVar(0, ALPHA, "f%d" % p) for p in range(N)]
            for L in lines:
                m.Add(sum(f[p] for p in L) == TAU1)
            nz = [m.NewBoolVar("") for _ in range(N)]
            for p in range(N):
                m.Add(f[p] >= 1).OnlyEnforceIf(nz[p])
                m.Add(f[p] == 0).OnlyEnforceIf(nz[p].Not())
            mx = m.NewIntVar(0, ALPHA, "mx")
            m.AddMaxEquality(mx, f)
            obj = sum(nz) if what == "support" else mx
            m.Minimize(obj) if sense == "min" else m.Maximize(obj)
            s = cp_model.CpSolver()
            s.parameters.max_time_in_seconds = 30.0
            s.parameters.num_search_workers = 8
            st = s.Solve(m)
            out["%s_%s" % (what, sense)] = {
                "value": int(s.ObjectiveValue()) if st in (
                    cp_model.OPTIMAL, cp_model.FEASIBLE) else None,
                "status": s.StatusName(st),
                "proved": st == cp_model.OPTIMAL,
            }
    return out


def main():
    reps = {}
    cap = (int(sys.argv[sys.argv.index("--cap") + 1])
           if "--cap" in sys.argv else 200000)
    lines, gens = load()
    bounds = proved_bounds(lines)

    print("DEGREE SEQUENCES FORCED AT |X| = 110")
    print("=" * 72)
    print("  f(p) = |X_p|, with sum 11 on every line and 0 <= f <= alpha = 7")
    print("  solution space: (11/4)*1 + E_{-4}, a 15-dimensional coset,")
    print("                  cut down by the box")
    print()

    m = cp_model.CpModel()
    f = [m.NewIntVar(0, ALPHA, "f%d" % p) for p in range(N)]
    for L in lines:
        m.Add(sum(f[p] for p in L) == TAU1)
    m.Add(sum(f) == 110)          # implied; stated so the model is explicit

    s = cp_model.CpSolver()
    s.parameters.enumerate_all_solutions = True
    s.parameters.num_search_workers = 1     # required for enumeration
    s.parameters.max_time_in_seconds = 600.0
    cb = Collect(f, cap)
    t0 = time.time()
    st = s.Solve(m, cb)
    seqs = cb.found
    complete = (st == cp_model.OPTIMAL and len(seqs) < cap)

    print("  PROVED bounds (by optimisation, not by reading off an")
    print("  enumeration that did not complete):")
    for k in sorted(bounds):
        b = bounds[k]
        print("    %-14s %s   (%s%s)" % (k, b["value"], b["status"],
                                         ", proved" if b["proved"] else ""))
    print("    naive counting gives support >= ceil(110/7) = %d"
          % -(-110 // ALPHA))
    print()
    print("  sequences found : %d%s" % (len(seqs), "" if complete else "  (CAPPED)"))
    print("  enumeration     : %s   (%.1f s)"
          % ("COMPLETE" if complete else "incomplete", time.time() - t0))
    print()

    if not seqs:
        print("  ==> NONE.  No degree sequence can satisfy the tight equations,")
        print("      so no 110-leaf blocker exists and tau_2 >= 111.")
        result = {"count": 0, "complete": complete,
                  "conclusion": "lower bound rises to 111", "proved": complete}
    else:
        supports = sorted({sum(1 for v in q if v) for q in seqs})
        maxima = sorted({max(q) for q in seqs})
        print("  distinct supports (non-zero fibres) : %s" % supports)
        print("  distinct maxima                     : %s" % maxima)
        print("  support must be at least ceil(110/7) = %d" % -(-110 // ALPHA))
        print()

        reps, total = {}, 0
        if complete and len(seqs) <= 20000:
            print("  reducing modulo Aut(W33) ...")
            for q in seqs:
                c, orb = canonical(q, gens)
                if c not in reps:
                    reps[c] = orb
                    total += orb
            print("  orbits under Aut(W33)               : %d" % len(reps))
            print("  orbit sizes cover all sequences     : %s"
                  % (total == len(seqs)))
            print()
            print("  ==> the tight case reduces to %d independent subproblems,"
                  % len(reps))
            print("      each with every fibre size FIXED rather than free.")
        else:
            print("  ==> too many to reduce by symmetry here; this decomposition")
            print("      is not the way in, and that is now known cheaply.")

        result = {
            "count": len(seqs),
            "complete": complete,
            "supports": supports,
            "maxima": maxima,
            "orbitsUnderAut": len(reps) if reps else None,
            "orbitReduction": (len(seqs) / len(reps)) if reps else None,
            "conclusion": "degree sequences exist; necessary, never sufficient",
            "proved": False,
        }

    result.update({
        "schema": "holotrade.tensor-tight-degree-sequences.v2",
        "provedBounds": bounds,
        "naiveCountingSupport": -(-110 // ALPHA),
        "observedRangesAreNotBounds": ("supports and maxima below are what the "
                                       "INCOMPLETE enumeration happened to "
                                       "produce; only provedBounds are facts"),
        "alpha": ALPHA,
        "tau1": TAU1,
        "boundary": ("a degree sequence is necessary for a 110-leaf blocker "
                     "and never sufficient; nothing here bounds tau_2 unless "
                     "the count is zero and the enumeration is complete"),
    })

    if "--write" in sys.argv:
        out = os.path.join(ROOT, "data", "tensor_tight_degree_sequences.json")
        with open(out, "w") as fh:
            json.dump(result, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(out, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
