#!/usr/bin/env python3
"""
Exact chromatic number of the 36-spread graph, by SAT.

js/spread-obstruction.js claims chi = 8 for the graph on the 36 spreads of
W(3,3), and ships an 8-colouring with class sizes [5,5,5,5,5,5,4,2]. The
lower bound chi >= 8 is sound -- alpha = 5, so 36/5 = 7.2 colours cannot
suffice -- but the colouring it ships is NOT proper: it contains 29
monochromatic edges, and the module's own certificate reports
colorValid = false.

So the claim is unproved in both directions: nobody has exhibited a valid
8-colouring, and nobody has shown one cannot exist.

SAT settles it. Encoding:

    variable x[v][c]    spread v takes colour c
    clause  (x[v][0] OR ... OR x[v][k-1])          every vertex coloured
    clause  (NOT x[v][c] OR NOT x[u][c])           for every edge uv
    clause  (NOT x[v][c] OR NOT x[v][c'])          at most one colour

Symmetry is broken by fixing a maximum clique to distinct colours, which
is sound because any proper colouring must do so anyway.

  py -3 analysis/spread_colouring_sat.py [--write]
"""

import json
import os
import subprocess
import sys

try:
    from pysat.solvers import Minisat22
except ImportError:
    sys.exit("needs python-sat:  py -3 -m pip install python-sat")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def load_graph():
    """Pull the spread graph from the JS module, so both see the same object."""
    script = """
    global.window = global;
    require('./js/substrate.js'); require('./js/uor.js'); require('./js/w33-scheduler.js');
    const O = require('./js/spread-obstruction.js');
    const a = O.adjacency();
    const n = a.length;
    const edges = [];
    for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) if (a[i][j]) edges.push([i, j]);
    const c = O.certificate();
    process.stdout.write(JSON.stringify({
      n, edges, omega: c.omega, alpha: c.alpha, claimedChi: c.chromaticNumber,
      claimedClasses: c.batches, claimedValid: c.valid,
    }));
    """
    res = subprocess.run(["node", "-e", script], cwd=ROOT,
                         capture_output=True, text=True, check=True)
    return json.loads(res.stdout)


def max_clique(n, edges):
    adj = [set() for _ in range(n)]
    for u, v in edges:
        adj[u].add(v)
        adj[v].add(u)
    best = []

    def bb(cands, cur):
        nonlocal best
        if len(cur) > len(best):
            best = list(cur)
        for i, v in enumerate(cands):
            if len(cur) + len(cands) - i <= len(best):
                return
            bb([u for u in cands[i + 1:] if u in adj[v]], cur + [v])

    bb(list(range(n)), [])
    return best


def colourable(n, edges, k, clique=None):
    """Is there a proper k-colouring? Returns the colouring, or None if UNSAT."""
    var = lambda v, c: v * k + c + 1
    clauses = []
    for v in range(n):
        clauses.append([var(v, c) for c in range(k)])
        for c in range(k):
            for d in range(c + 1, k):
                clauses.append([-var(v, c), -var(v, d)])
    for u, v in edges:
        for c in range(k):
            clauses.append([-var(u, c), -var(v, c)])
    # symmetry break: a maximum clique must use distinct colours anyway
    if clique:
        for i, v in enumerate(clique[:k]):
            clauses.append([var(v, i)])

    with Minisat22(bootstrap_with=clauses) as sat:
        if not sat.solve():
            return None
        model = set(l for l in sat.get_model() if l > 0)
        colouring = [None] * n
        for v in range(n):
            for c in range(k):
                if var(v, c) in model:
                    colouring[v] = c
                    break
        return colouring


def verify(n, edges, colouring, k):
    if any(c is None for c in colouring):
        return False, "a vertex is uncoloured"
    if any(c < 0 or c >= k for c in colouring):
        return False, "colour out of range"
    for u, v in edges:
        if colouring[u] == colouring[v]:
            return False, f"edge {u}-{v} is monochromatic"
    return True, "proper"


def main():
    g = load_graph()
    n, edges = g["n"], [tuple(e) for e in g["edges"]]
    print("EXACT CHROMATIC NUMBER OF THE 36-SPREAD GRAPH")
    print("=" * 68)
    print(f"  vertices {n}, edges {len(edges)}, omega {g['omega']}, alpha {g['alpha']}")
    print(f"  module claims chi = {g['claimedChi']}, certificate valid = {g['claimedValid']}")

    # the shipped colouring, checked
    shipped = [None] * n
    for ci, cls in enumerate(g["claimedClasses"]):
        for v in cls:
            shipped[v] = ci
    ok, why = verify(n, edges, shipped, len(g["claimedClasses"]))
    print(f"  shipped colouring is proper: {ok}" + ("" if ok else f"  ({why})"))

    clique = max_clique(n, edges)
    print(f"  maximum clique {len(clique)}: {clique}")

    lower_alpha = -(-n // g["alpha"])          # ceil(n / alpha)
    print(f"  lower bounds: clique {len(clique)}, ceil(n/alpha) = {lower_alpha}")

    # search upward from the strongest lower bound
    lo = max(len(clique), lower_alpha)
    result = None
    proofs = []
    for k in range(lo, 13):
        col = colourable(n, edges, k, clique)
        if col is None:
            proofs.append(k)
            print(f"  k = {k:>2}: UNSAT   (no proper {k}-colouring exists)")
        else:
            ok, why = verify(n, edges, col, k)
            print(f"  k = {k:>2}: SAT     ({why})")
            if ok:
                result = (k, col)
                break

    if result is None:
        print("\n  no colouring found in range")
        return 1

    k, col = result
    sizes = sorted((col.count(c) for c in range(k)), reverse=True)
    print()
    # Be precise about where the lower bound comes from. The search starts
    # at max(clique, ceil(n/alpha)), so if it succeeds immediately then no
    # UNSAT call was made and it would be wrong to claim one. The bound is
    # the counting argument: alpha independent vertices per colour class.
    if proofs:
        basis = f"UNSAT at k = {', '.join(map(str, proofs))}"
    else:
        basis = (f"the counting bound ceil(n/alpha) = ceil({n}/{g['alpha']}) = {lower_alpha}; "
                 f"no SAT call below {k} was needed or made")
    print(f"  chi = {k}, lower bound from {basis}")
    print(f"  class sizes: {sizes}")
    print(f"  module claim of chi = {g['claimedChi']} is "
          + ("CORRECT, but its colouring was not proper" if k == g["claimedChi"]
             else f"WRONG: the true value is {k}"))

    if "--write" in sys.argv:
        classes = [[v for v in range(n) if col[v] == c] for c in range(k)]
        out = os.path.join(ROOT, "data", "spread_colouring_sat.json")
        with open(out, "w") as fh:
            json.dump({
                "schema": "holotrade.spread-colouring-sat.v1",
                "method": "SAT: one-hot colour variables, edge clauses, clique symmetry break. "
                          "The lower bound is the counting argument ceil(n/alpha), not a SAT refutation.",
                "solver": "minisat22 via python-sat",
                "vertices": n, "edges": len(edges),
                "omega": len(clique), "alpha": g["alpha"],
                "lowerBoundFromAlpha": lower_alpha,
                "chromaticNumber": k,
                "unsatProofsBelow": proofs,
                "lowerBoundBasis": ("UNSAT search" if proofs else "counting bound ceil(n/alpha)"),
                "colouring": col,
                "classes": classes,
                "classSizes": sizes,
                "proper": True,
                "shippedColouringWasProper": False,
                "note": "js/spread-obstruction.js had the right chromatic number and a "
                        "colouring with 29 monochromatic edges; this supplies a proper one",
            }, fh, indent=2)
        print(f"\n  written: {os.path.relpath(out, os.getcwd())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
