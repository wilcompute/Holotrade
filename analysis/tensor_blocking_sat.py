#!/usr/bin/env python3
"""
Close the depth-2 tensor blocking interval, exactly.

js/tensor-sharding.js leaves the blocking number of the product tile
family explicitly open:

    "Shadow double-counting gives 110 <= tau_tensor,2 <= 121.
     The exact value inside this interval remains OPEN."

That interval matters. The tile L x M is the construction that buys
robustness by giving up density -- the level-n classification proves no
DENSEST shape can be robust, so a sub-optimal shape is the only way out,
and the tile is the candidate. How robust it actually is decides whether
the trade is worth making.

The lower bound is a clean double count. For each of the 40 first-axis
lines L_a, the set of second coordinates appearing in X above L_a must
hit every line M_b, hence has size >= tau_1 = 11. Summing over a gives
440, and each blocked leaf is counted once per first-axis line through
its first coordinate, which is 4. So |X| >= 440/4 = 110.

The upper bound is B x B for an 11-element line blocker B: 121 leaves.

SAT decides everything between. Encoding:

    variable x[p][q]                       leaf (p,q) is blocked
    clause  OR over (p,q) in L_a x M_b     every one of the 1600 tiles is hit
    cardinality  sum x <= k

UNSAT at k proves tau > k. The first SAT gives tau and a witness.
"""

import itertools
import json
import os
import subprocess
import sys

try:
    from pysat.solvers import Minisat22
    from pysat.card import CardEnc, EncType
    from pysat.formula import IDPool
except ImportError:
    sys.exit("needs python-sat:  py -3 -m pip install python-sat")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
N = 40


def load():
    script = """
    global.window = global;
    const S = require('./js/substrate.js');
    const T = require('./js/tensor-sharding.js');
    process.stdout.write(JSON.stringify({
      lines: S.LINES.map(l => [...l].sort((a,b)=>a-b)),
      tau1: T.TAU1,
      blocker: [...T.BLOCKER],
      bounds: T.tensorBlockingBounds(2),
    }));
    """
    res = subprocess.run(["node", "-e", script], cwd=ROOT,
                         capture_output=True, text=True, check=True)
    return json.loads(res.stdout)


def leaf(p, q):
    return p * N + q


def tiles(lines):
    """All 1600 product tiles L_a x M_b, as lists of leaf indices."""
    out = []
    for A in lines:
        for B in lines:
            out.append([leaf(p, q) for p in A for q in B])
    return out


def blocks(X, tl):
    S = set(X)
    return all(any(v in S for v in t) for t in tl)


def solve_at(tl, k):
    """Is there a blocking set of size <= k? Returns witness or None."""
    pool = IDPool(start_from=N * N + 1)
    clauses = [[v + 1 for v in t] for t in tl]
    card = CardEnc.atmost(lits=list(range(1, N * N + 1)), bound=k,
                          vpool=pool, encoding=EncType.seqcounter)
    with Minisat22(bootstrap_with=clauses + card.clauses) as sat:
        if not sat.solve():
            return None
        model = set(sat.get_model())
        return sorted(v - 1 for v in range(1, N * N + 1) if v in model)


def main():
    g = load()
    lines = g["lines"]
    tl = tiles(lines)
    lo, hi = g["bounds"]["lower"], g["bounds"]["upper"]

    print("DEPTH-2 TENSOR BLOCKING NUMBER, EXACTLY")
    print("=" * 70)
    print(f"  tiles: {len(tl)} products of two lines, {len(tl[0])} leaves each")
    print(f"  module interval: [{lo}, {hi}]   (open)")
    print(f"  tau_1 = {g['tau1']}, so B x B gives the upper witness of {g['tau1']**2}")

    # sanity: the constructive upper witness really blocks
    upper = [leaf(p, q) for p in g["blocker"] for q in g["blocker"]]
    print(f"  B x B blocks all {len(tl)} tiles: {blocks(upper, tl)}  (size {len(upper)})")

    print()
    print("  searching the interval:")
    tau, witness, proofs = None, None, []
    for k in range(lo, hi + 1):
        w = solve_at(tl, k)
        if w is None:
            proofs.append(k)
            print(f"    k = {k:>3}: UNSAT")
        else:
            tau, witness = k, w
            print(f"    k = {k:>3}: SAT     <- tau")
            break

    if tau is None:
        print(f"\n  UNSAT throughout [{lo},{hi}] -- contradicts the constructive upper bound")
        return 1

    ok = blocks(witness, tl)
    print()
    print(f"  tau_tensor,2 = {tau}   witness verified: {ok}")
    print(f"  UNSAT proved at k = {proofs if proofs else 'none needed'}")
    print(f"  guarantee: {tau - 1} busy leaves may be blocked with a tile still placeable")

    # what the trade actually buys, against the lift
    lift_tau = g["tau1"]
    print()
    print("  THE TRADE, AGAINST A LIFT OF THE SAME LINE")
    print(f"    lift:  160 leaves, densest (attains the bound), tau = {lift_tau}")
    print(f"    tile:   16 leaves, NOT densest,                  tau = {tau}")
    print(f"    capacity ratio  160/16 = {160 // 16}x")
    print(f"    robustness ratio {tau}/{lift_tau} = {tau / lift_tau:.2f}x")
    print(f"    => giving up {160 // 16}x capacity buys {tau / lift_tau:.2f}x robustness")

    if "--write" in sys.argv:
        out = os.path.join(ROOT, "data", "tensor_blocking_sat.json")
        with open(out, "w") as fh:
            json.dump({
                "schema": "holotrade.tensor-blocking-sat.v1",
                "closes": "js/tensor-sharding.js depth-2 interval [110,121]",
                "method": "SAT over 1600 leaf variables, one clause per product tile, "
                          "sequential-counter cardinality; UNSAT at every k below tau",
                "solver": "minisat22 via python-sat",
                "tiles": len(tl), "tileSize": len(tl[0]),
                "moduleLower": lo, "moduleUpper": hi,
                "tau": tau, "guarantee": tau - 1,
                "unsatProofs": proofs,
                "witness": witness, "witnessVerified": ok,
                "liftTau": lift_tau,
                "capacityRatio": 160 // 16,
                "robustnessRatio": tau / lift_tau,
            }, fh, indent=2)
        print(f"\n  written: {os.path.relpath(out, os.getcwd())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
