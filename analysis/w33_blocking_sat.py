#!/usr/bin/env python3
"""
Exact blocking numbers for W(3,3) shape orbits, by SAT.

  py -3 analysis/w33_blocking_sat.py [--write]

analysis/w33_shape_guarantees.js computes the minimum blocking set of each
shape orbit by branch and bound. That closes for most sizes but leaves
m = 12 and m = 20 as intervals, because the orbits are large (1,080 and
3,240 images) and heavily overlapping, which is exactly the regime where
a combinatorial bound is weak.

A SAT solver settles them. The encoding is direct:

    variable x_v      point v is blocked
    clause  (OR_{v in I} x_v)   for every image I in the orbit
                                -- every image must be hit
    cardinality  sum x_v <= k   -- at most k blocked points

UNSAT at k means no blocking set of size k exists, so tau > k. SAT at k
gives a witness. Searching upward from the certified counting lower bound
until the first SAT gives tau exactly, with an UNSAT proof for every value
below it -- which is what makes the guarantee a guarantee rather than a
failure to find something.

This is a genuinely different solver from the JS branch and bound, so
agreement on the sizes both can do is a cross-check, not a repetition.
"""

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


def shape_orbits():
    """Ask the JS module for each shape's orbit, so both solvers see identical input."""
    script = """
    global.window = global;
    const shapes = require('./scheduler/w33-shapes.js');
    const cat = shapes.frozenCatalogue();
    const out = {};
    for (const m of Object.keys(cat.tight)) {
      out[m] = shapes.shapeOrbit(cat.tight[m]);
    }
    out.spread20 = shapes.shapeOrbit(cat.spread[20]);
    process.stdout.write(JSON.stringify(out));
    """
    res = subprocess.run(["node", "-e", script], cwd=ROOT,
                         capture_output=True, text=True, check=True)
    return json.loads(res.stdout)


def blocking_number(orbit, lower=1, upper=None):
    """
    Smallest k with a size-k set meeting every image.

    Returns (tau, witness, proofs) where `proofs` records the UNSAT result
    for every k below tau -- the part that makes this a proof of a lower
    bound and not merely an unsuccessful search.
    """
    if upper is None:
        upper = N
    proofs = []
    for k in range(lower, upper + 1):
        pool = IDPool(start_from=N + 1)
        clauses = [[v + 1 for v in img] for img in orbit]
        card = CardEnc.atmost(lits=list(range(1, N + 1)), bound=k,
                              vpool=pool, encoding=EncType.seqcounter)
        with Minisat22(bootstrap_with=clauses + card.clauses) as sat:
            if sat.solve():
                model = set(sat.get_model())
                witness = sorted(v - 1 for v in range(1, N + 1) if v in model)
                return k, witness, proofs
            proofs.append({"k": k, "result": "UNSAT", "meaning": f"no blocking set of size {k} exists"})
    return None, None, proofs


def verify(witness, orbit):
    X = set(witness)
    return all(any(v in X for v in img) for img in orbit)


def guarantee_holds(orbit, size):
    """Exhaustive-by-SAT: is it true that NO set of this size blocks the shape?"""
    pool = IDPool(start_from=N + 1)
    clauses = [[v + 1 for v in img] for img in orbit]
    card = CardEnc.atmost(lits=list(range(1, N + 1)), bound=size,
                          vpool=pool, encoding=EncType.seqcounter)
    with Minisat22(bootstrap_with=clauses + card.clauses) as sat:
        return not sat.solve()          # UNSAT => nothing that small blocks


def main():
    orbits = shape_orbits()
    print("EXACT BLOCKING NUMBERS BY SAT")
    print("=" * 74)
    print("  tau = smallest number of blocked points that defeats EVERY placement")
    print("  guarantee = tau - 1 nodes may be busy and a placement still always exists")
    print()
    print("  shape        m   orbit      counting LB   tau   guarantee   UNSAT proofs")

    rows = []
    for key in sorted(orbits, key=lambda x: (x == "spread20", int(x.replace("spread", "")) if x != "spread20" else 20)):
        orbit = orbits[key]
        m = len(orbit[0])
        kind = "spread" if key == "spread20" else "densest"
        counting = -(-N // m)                       # ceil(N/m), the transitivity bound
        tau, witness, proofs = blocking_number(orbit, lower=counting)
        ok = verify(witness, orbit) if witness else False
        # the guarantee, proved rather than sampled
        gproof = guarantee_holds(orbit, tau - 1) if tau and tau > 1 else True
        rows.append({
            "kind": kind, "m": m, "orbitSize": len(orbit),
            "countingLowerBound": counting, "tau": tau, "guarantee": tau - 1,
            "witness": witness, "witnessValid": ok,
            "unsatProofs": len(proofs) + (counting - 1),
            "guaranteeProvedUnsat": gproof,
            "countingBoundTight": tau == counting,
        })
        print(f"  {kind:<9} {m:>4}   {len(orbit):>6}      {counting:>10}   {tau:>3}   {tau-1:>9}   "
              f"{len(proofs):>4}   {'proved' if gproof else 'FAILED'}")

    print()
    print("Cross-check against the JS branch and bound:")
    jspath = os.path.join(ROOT, "data", "w33_shape_guarantees.json")
    agree = True
    if os.path.exists(jspath):
        js = json.load(open(jspath))
        by_m = {r["m"]: r for r in js["shapes"]}
        for r in rows:
            if r["kind"] != "densest":
                continue
            j = by_m.get(r["m"])
            if not j:
                continue
            if j.get("tau") is not None:
                same = j["tau"] == r["tau"]
                agree &= same
                print(f"  m={r['m']:>2}: JS exact tau={j['tau']}  SAT tau={r['tau']}  {'agree' if same else 'DISAGREE'}")
            else:
                lo, hi = j.get("tauLowerBound"), j.get("tauUpperBound")
                inside = lo <= r["tau"] <= hi
                agree &= inside
                print(f"  m={r['m']:>2}: JS interval [{lo},{hi}]  SAT tau={r['tau']}  "
                      f"{'consistent' if inside else 'OUTSIDE INTERVAL'}")
    print()
    print("ALL SOLVERS AGREE" if agree else "*** SOLVERS DISAGREE ***")

    if "--write" in sys.argv:
        out = os.path.join(ROOT, "data", "w33_blocking_sat.json")
        with open(out, "w") as fh:
            json.dump({
                "schema": "holotrade.w33-blocking-sat.v1",
                "method": "SAT: one clause per orbit image, sequential-counter cardinality, "
                          "UNSAT at every k below tau",
                "solver": "minisat22 via python-sat",
                "shapes": rows,
            }, fh, indent=2)
        print(f"\nwritten: {os.path.relpath(out, os.getcwd())}")

    return 0 if agree else 1


if __name__ == "__main__":
    sys.exit(main())
