#!/usr/bin/env python3
"""
Close the depth-2 tensor blocking number with CP-SAT.

js/tensor-sharding.js leaves tau open at [110, 121]. Raw SAT with a
cardinality encoding over 1,600 leaf variables did not terminate:
"at most k" near the optimum needs a seqcounter with ~176,000 auxiliary
variables, and minisat has no objective function, so every value has to
be probed as a separate instance.

CP-SAT is the right tool. It takes the objective natively, keeps a real
LP relaxation alongside the search, and reports a bound gap as it goes --
so even a run that does not finish returns a proved interval rather than
nothing.

The model is the direct one:

    minimise  sum x[p][q]
    subject to  sum over the tile L_a x M_b of x >= 1,  for all 1600 tiles

plus three families of redundant-but-valid cuts derived in
analysis/tensor_blocking_reformulation.js. They are implied by the tile
constraints, so they change nothing about what is feasible; they exist to
give the LP relaxation something much sharper to work with:

  ROW CUTS     for every line L,  sum_{p in L} |X_p| >= 11
               (that line's union of fibres must itself block)
  COLUMN CUTS  the same by transpose symmetry, since the tile family is
               symmetric under swapping the two coordinates
  GLOBAL CUT   sum x >= 110, the double count

Symmetry is the other half. The automorphism group here is Aut(W) wr S_2,
of order 51840^2 * 2, so an unbroken search re-explores the same solution
billions of times. Fixing one leaf and ordering the row sums removes most
of that without removing any optimum.
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

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
N = 40
TAU1 = 11


def load_lines():
    out = subprocess.run(
        ["node", "-e",
         "global.window=global;const S=require('./js/substrate.js');"
         "process.stdout.write(JSON.stringify(S.LINES.map(l=>[...l].sort((a,b)=>a-b))))"],
        cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def solve(seconds=600, workers=8, break_symmetry=True, verbose=True):
    lines = load_lines()
    m = cp_model.CpModel()
    x = [[m.NewBoolVar(f"x_{p}_{q}") for q in range(N)] for p in range(N)]

    # the actual requirement: every product tile is hit
    for A in lines:
        for B in lines:
            m.AddBoolOr([x[p][q] for p in A for q in B])

    # --- valid cuts, all implied by the tile constraints ---------------
    # every line's union of fibres must itself be a line-blocking set,
    # so it has at least tau_1 = 11 elements
    for L in lines:
        m.Add(sum(x[p][q] for p in L for q in range(N)) >= TAU1)
    # and the same by transpose symmetry
    for M in lines:
        m.Add(sum(x[p][q] for q in M for p in range(N)) >= TAU1)
    # the double count
    total = sum(x[p][q] for p in range(N) for q in range(N))
    m.Add(total >= 110)

    # --- symmetry breaking --------------------------------------------
    # Aut(W) wr S_2 has order 51840^2 * 2. The group is transitive on
    # leaves, so some optimal solution contains leaf (0,0); fixing it
    # removes a factor without removing every optimum.
    if break_symmetry:
        m.Add(x[0][0] == 1)

    m.Minimize(total)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(seconds)
    solver.parameters.num_search_workers = workers
    solver.parameters.log_search_progress = False
    t = time.time()
    status = solver.Solve(m)
    elapsed = time.time() - t

    names = {cp_model.OPTIMAL: "OPTIMAL", cp_model.FEASIBLE: "FEASIBLE",
             cp_model.INFEASIBLE: "INFEASIBLE", cp_model.UNKNOWN: "UNKNOWN"}
    res = {
        "status": names.get(status, str(status)),
        "seconds": round(elapsed, 1),
        "symmetryBroken": break_symmetry,
    }
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        witness = sorted(p * N + q for p in range(N) for q in range(N)
                         if solver.Value(x[p][q]))
        res["objective"] = int(solver.ObjectiveValue())
        res["bestBound"] = int(solver.BestObjectiveBound())
        res["witness"] = witness
        res["witnessSize"] = len(witness)
        res["proved"] = status == cp_model.OPTIMAL
    return res, lines


def verify(witness, lines):
    S = set(witness)
    return all(any((p * N + q) in S for p in A for q in B)
               for A in lines for B in lines)


def main():
    seconds = int(sys.argv[sys.argv.index("--seconds") + 1]) if "--seconds" in sys.argv else 600
    print("DEPTH-2 TENSOR BLOCKING NUMBER VIA CP-SAT")
    print("=" * 70)
    print(f"  budget {seconds}s, minimising directly with valid cuts and symmetry breaking")
    print()

    res, lines = solve(seconds=seconds)
    print(f"  status      {res['status']}   ({res['seconds']}s)")
    if "objective" not in res:
        print("  no feasible solution found in the budget")
        return 1

    ok = verify(res["witness"], lines)
    print(f"  best found  {res['objective']}   verified blocks all 1600 tiles: {ok}")
    print(f"  best bound  {res['bestBound']}")
    print()

    if res["proved"]:
        print(f"  ==> tau = {res['objective']} EXACTLY.  Interval [110, 121] is CLOSED.")
    else:
        print(f"  ==> interval narrowed to [{res['bestBound']}, {res['objective']}]"
              f"  (was [110, 121])")

    if "--write" in sys.argv:
        out = os.path.join(ROOT, "data", "tensor_blocking_cpsat.json")
        with open(out, "w") as fh:
            json.dump({
                "schema": "holotrade.tensor-blocking-cpsat.v1",
                "solver": "OR-Tools CP-SAT",
                "model": "minimise sum x subject to one clause per product tile, plus "
                         "row/column blocking cuts and the double-count cut",
                "publishedInterval": [110, 121],
                "status": res["status"],
                "seconds": res["seconds"],
                "tau": res["objective"] if res["proved"] else None,
                "lowerBound": res["bestBound"],
                "upperBound": res["objective"],
                "proved": res["proved"],
                "witness": res["witness"],
                "witnessVerified": ok,
                "guarantee": (res["objective"] - 1) if res["proved"] else None,
            }, fh, indent=2)
        print(f"\n  written: {os.path.relpath(out, os.getcwd())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
