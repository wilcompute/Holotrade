#!/usr/bin/env python3
"""
Look for a SYMMETRIC depth-2 tile blocker of size 110.

The direct search is stuck: CP-SAT reproduces [110, 121] and the tight-case
feasibility model returns UNKNOWN. The obstruction, if any, is combinatorial,
and the search space is 2^1600 with an automorphism group of order
51840^2 * 2 re-exploring every solution billions of times.

So flip it around. Instead of searching all sets, search only those
INVARIANT under a chosen subgroup. That is a one-sided move and worth
being explicit about:

    a hit PROVES tau <= 110, closing the interval, since 110 is already
    a proved lower bound;
    a miss proves nothing about tau -- only that no blocker of that size
    has that particular symmetry.

Extremal objects in highly symmetric geometries very often carry some of
the symmetry, so it is a good bet even though it is not a decision
procedure.

The reduction is large. Fixing a group element g and asking for X
invariant under the diagonal action (p,q) -> (g(p), g(q)) collapses the
1,600 leaf variables to one variable per orbit -- typically a few
hundred. Twisted actions (p,q) -> (g(p), h(q)) with h a power of g give
further families at no extra cost.
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


def load():
    out = subprocess.run(
        ["node", "-e",
         "global.window=global;"
         "const S=require('./js/substrate.js');"
         "const SH=require('./scheduler/w33-shapes.js');"
         "const gens=SH.generators().map(g=>Array.from(g));"
         "process.stdout.write(JSON.stringify({lines:S.LINES.map(l=>[...l].sort((a,b)=>a-b)),gens}));"],
        cwd=ROOT, capture_output=True, text=True)
    if out.returncode:
        sys.exit("node failed: " + out.stderr[:400])
    d = json.loads(out.stdout)
    return d["lines"], d["gens"]


def perm_order(g):
    n = len(g)
    seen = [False] * n
    from math import lcm
    o = 1
    for i in range(n):
        if seen[i]:
            continue
        L, j = 0, i
        while not seen[j]:
            seen[j] = True
            j = g[j]
            L += 1
        o = lcm(o, L)
    return o


def compose(a, b):
    return [a[b[i]] for i in range(len(b))]


def power(g, k):
    r = list(range(len(g)))
    for _ in range(k):
        r = compose(g, r)
    return r


def orbits_of(g, h):
    """Orbits of the 1600 leaves under (p,q) -> (g(p), h(q))."""
    seen = [False] * (N * N)
    out = []
    for v in range(N * N):
        if seen[v]:
            continue
        orb, cur = [], v
        while not seen[cur]:
            seen[cur] = True
            orb.append(cur)
            p, q = cur // N, cur % N
            cur = g[p] * N + h[q]
        out.append(orb)
    return out


def search(lines, g, h, target=110, seconds=45):
    orbs = orbits_of(g, h)
    m = cp_model.CpModel()
    y = [m.NewBoolVar(f"o{i}") for i in range(len(orbs))]
    member = [[] for _ in range(N * N)]
    for i, o in enumerate(orbs):
        for v in o:
            member[v].append(i)

    for A in lines:
        for B in lines:
            lits = set()
            for p in A:
                for q in B:
                    for i in member[p * N + q]:
                        lits.add(i)
            m.AddBoolOr([y[i] for i in sorted(lits)])
    m.Add(sum(len(orbs[i]) * y[i] for i in range(len(orbs))) == target)

    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = float(seconds)
    s.parameters.num_search_workers = 8
    st = s.Solve(m)
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        X = sorted(v for i, o in enumerate(orbs) if s.Value(y[i]) for v in o)
        return len(orbs), X
    return len(orbs), None


def verify(X, lines):
    S = set(X)
    return all(any((p * N + q) in S for p in A for q in B)
               for A in lines for B in lines)


def main():
    target = int(sys.argv[sys.argv.index("--target") + 1]) if "--target" in sys.argv else 110
    per = int(sys.argv[sys.argv.index("--per") + 1]) if "--per" in sys.argv else 40
    lines, gens = load()

    print("SYMMETRIC SEARCH FOR A DEPTH-2 BLOCKER")
    print("=" * 70)
    print(f"  target |X| = {target}")
    print("  a hit proves tau <= target and CLOSES the interval;")
    print("  a miss proves nothing about tau, only about that symmetry")
    print()

    # distinct element orders available among the generators and their powers
    tried, found = 0, None
    seen_sig = set()
    print("   order   twist   orbits   result")
    for gi, g in enumerate(gens[:24]):
        o = perm_order(g)
        if o < 2:
            continue
        for tw in range(1, o):
            h = power(g, tw)
            sig = (o, tw, tuple(g[:6]), tuple(h[:6]))
            if sig in seen_sig:
                continue
            seen_sig.add(sig)
            norb, X = search(lines, g, h, target=target, seconds=per)
            tried += 1
            ok = X is not None and verify(X, lines)
            print(f"  {o:>6}   {tw:>5}   {norb:>6}   {'HIT' if ok else 'none'}")
            if ok:
                found = X
                break
        if found:
            break

    print()
    print(f"  symmetry classes tried: {tried}")
    if found:
        print(f"  ==> FOUND a blocker of size {len(found)} that blocks all 1600 tiles.")
        print(f"      With the proved lower bound of 110, tau = {len(found)} and the")
        print(f"      interval [110, 121] CLOSES.")
    else:
        print("  ==> no symmetric blocker of that size under the symmetries tried.")
        print("      This bounds nothing: tau stays open in [110, 121].")

    if "--write" in sys.argv:
        out = os.path.join(ROOT, "data", "tensor_symmetric_search.json")
        with open(out, "w") as fh:
            json.dump({
                "schema": "holotrade.tensor-symmetric-search.v1",
                "target": target,
                "symmetryClassesTried": tried,
                "found": found is not None,
                "witness": found,
                "conclusion": (f"tau = {len(found)}" if found
                               else "no conclusion; a miss bounds nothing"),
                "onesided": "a hit closes the interval; a miss proves nothing about tau",
            }, fh, indent=2)
        print(f"\n  written: {os.path.relpath(out, os.getcwd())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
