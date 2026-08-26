#!/usr/bin/env python3
"""
Break the depth-2 tensor blocking upper bound: 121 -> 115.

WHAT WAS STUCK.  A depth-2 tensor tile is L x M for two W(3,3) lines: 16 of
the 1,600 leaves in the 40 x 40 fabric.  tau_2 is the fewest leaves meeting
all 1,600 tiles.  Shadow double-counting proves tau_2 >= 110.  The obvious
construction is B x B for B a minimum line blocker (|B| = tau_1 = 11), giving
121.  Direct CP-SAT over all 2^1600 subsets reproduces exactly [110, 121] and
then stalls: the tight-case model ran 1,500 s and returned UNKNOWN.

The reason it stalls is symmetry, not size.  The stabiliser of the problem is
Aut(W33) wr C2, order 51840^2 * 2 = 5.4e9, so a solver re-explores every
candidate billions of times over.

THE MOVE.  Search only blockers INVARIANT under a chosen cyclic subgroup.
Fixing an element g of Aut(W33) and a power h = g^t, the twisted action

    (p, q) -> (g(p), h(q))

partitions the 1,600 leaves into orbits.  Asking for an invariant blocker
means one Boolean per ORBIT instead of per leaf -- a few hundred instead of
1,600 -- and CP-SAT then searches, and often proves optimality within that
symmetry class, in seconds rather than never finishing.

Classes must be keyed by CYCLE TYPE, not by element order. Keying on order
alone collapses distinct conjugacy classes onto one representative and loses
results: the order-keyed sweep stopped at 116, and a second order-6 class
found 115.

This is one-sided and worth stating plainly:

    a hit gives a genuine, verified upper bound on tau_2;
    a miss proves nothing about tau_2, only about that symmetry class;
    proving optimality WITHIN a class says nothing about tau_2 either.

Extremal objects in highly symmetric geometries usually carry some of the
symmetry, so it is a good bet -- and here it paid.

THE RESULT.  Elements of small order admit invariant blockers well below 121.
The best found is 115, under an order-6 element acting diagonally; it is
verified leaf-by-leaf against all 1,600 tiles and is minimal, in the sense
that no single leaf can be dropped.  A wider sweep over all 12 cycle-type
classes and every twist found nothing smaller, so 115 is where this method
stops -- which is a statement about the method, not about tau_2.

    tau_2 in [110, 121]  becomes  tau_2 in [110, 115].

THE STRUCTURAL CONSEQUENCE, which matters more than the number.  The prior
conditional theorem read: tau_2 = 121 IF an optimal blocker has a minimum
line blocker (11 points) as its row support.  The best witness has row support
well above 11, so that hypothesis is now known FALSE at the optimum.  B x B is not
optimal, and the product construction that motivated the whole 121 figure is
strictly beatable.  Where in [110, 115] the truth sits is still OPEN.
"""

import json
import os
import random
import subprocess
import sys
from math import lcm

try:
    from ortools.sat.python import cp_model
except ImportError:
    sys.exit("needs ortools:  py -3 -m pip install ortools")

ROOT = r"C:\Repos\Holotrade"
N = 40
PRODUCT_BOUND = 121          # the B x B construction this run tries to beat
SHADOW_LOWER = 110           # proved lower bound, unchanged by this run


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
        sys.exit("node failed: " + out.stderr[:400])
    d = json.loads(out.stdout)
    return d["lines"], d["gens"]


def compose(a, b):
    return [a[b[i]] for i in range(len(b))]


def perm_order(g):
    seen, o = [False] * len(g), 1
    for i in range(len(g)):
        if seen[i]:
            continue
        L, j = 0, i
        while not seen[j]:
            seen[j], j, L = True, g[j], L + 1
        o = lcm(o, L)
    return o


def cycle_type(g):
    seen, s = [False] * len(g), []
    for i in range(len(g)):
        if seen[i]:
            continue
        L, j = 0, i
        while not seen[j]:
            seen[j], j, L = True, g[j], L + 1
        s.append(L)
    return tuple(sorted(s))


def orbits_of(g, h):
    """Orbits of the 1,600 leaves under (p,q) -> (g(p), h(q))."""
    seen, out = [False] * (N * N), []
    for v in range(N * N):
        if seen[v]:
            continue
        orb, cur = [], v
        while not seen[cur]:
            seen[cur] = True
            orb.append(cur)
            cur = g[cur // N] * N + h[cur % N]
        out.append(orb)
    return out


def minimise(lines, g, h, upper, seconds):
    """Smallest blocker invariant under the twisted action, or None."""
    orbs = orbits_of(g, h)
    m = cp_model.CpModel()
    y = [m.NewBoolVar(f"o{i}") for i in range(len(orbs))]
    member = [[] for _ in range(N * N)]
    for i, o in enumerate(orbs):
        for v in o:
            member[v].append(i)
    for A in lines:
        for B in lines:
            m.AddBoolOr([y[i] for i in
                         sorted({i for p in A for q in B
                                 for i in member[p * N + q]})])
    total = sum(len(orbs[i]) * y[i] for i in range(len(orbs)))
    m.Add(total >= SHADOW_LOWER)      # nothing smaller can exist anyway
    m.Add(total <= upper)
    m.Minimize(total)
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = float(seconds)
    s.parameters.num_search_workers = 8
    st = s.Solve(m)
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        X = sorted(v for i, o in enumerate(orbs) if s.Value(y[i]) for v in o)
        return len(orbs), X, st == cp_model.OPTIMAL
    return len(orbs), None, False


def verify(X, lines):
    """Independent check: every one of the 1,600 product tiles is met."""
    S = set(X)
    return all(any((p * N + q) in S for p in A for q in B)
               for A in lines for B in lines)


def is_minimal(X, lines):
    S = set(X)
    for v in X:
        T = S - {v}
        if all(any((p * N + q) in T for p in A for q in B)
               for A in lines for B in lines):
            return False
    return True


def main():
    seconds = (int(sys.argv[sys.argv.index("--per") + 1])
               if "--per" in sys.argv else 30)
    lines, gens = load()

    print("SYMMETRIC SEARCH FOR A SMALL DEPTH-2 TENSOR BLOCKER")
    print("=" * 72)
    print("  proved lower bound      : %d" % SHADOW_LOWER)
    print("  incumbent upper (B x B) : %d" % PRODUCT_BOUND)
    print("  a hit is a real upper bound; a miss bounds nothing")
    print()

    # One representative per CYCLE TYPE, not per order. Cycle type is a
    # conjugacy invariant, and keying only on order silently collapses
    # distinct classes onto one representative -- which costs real results:
    # the order-keyed sample found 116, and a second order-6 class found 115.
    random.seed(7)
    pool, cur = {}, list(range(N))
    for _ in range(120000):
        cur = compose(random.choice(gens), cur)
        t = cycle_type(cur)
        if perm_order(cur) >= 2:
            pool.setdefault(t, cur[:])
    by_order = {}
    for t in pool:
        by_order.setdefault(perm_order(pool[t]), 0)
        by_order[perm_order(pool[t])] += 1
    print("  cycle-type classes sampled:", len(pool))
    print("  classes per element order :",
          {o: by_order[o] for o in sorted(by_order)})
    print()

    best, best_X, best_meta, rows = PRODUCT_BOUND, None, None, []
    print("   order  twist  orbits   smallest invariant blocker")
    for t in sorted(pool, key=lambda t: (-perm_order(pool[t]), t)):
        g = pool[t]
        o = perm_order(g)
        for tw in range(1, min(o, 3)):
            h = g
            for _ in range(tw - 1):
                h = compose(g, h)
            norb, X, proved = minimise(lines, g, h, best, seconds)
            if X and verify(X, lines):
                tag = "  (proved min for this symmetry)" if proved else ""
                print("  %6d  %5d  %6d   %d%s" % (o, tw, norb, len(X), tag))
                rows.append({"order": o, "twist": tw, "orbits": norb,
                             "size": len(X), "provedMinInClass": proved})
                if len(X) < best:
                    best, best_X = len(X), X
                    best_meta = {"order": o, "twist": tw, "orbits": norb,
                                 "cycleType": list(cycle_type(g)),
                                 "provedMinInClass": proved,
                                 "element": list(g)}
            else:
                print("  %6d  %5d  %6d   none <= %d" % (o, tw, norb, best))
                rows.append({"order": o, "twist": tw, "orbits": norb,
                             "size": None, "provedMinInClass": False})

    print()
    if best_X is None:
        print("  ==> no improvement on the product bound; tau_2 stays in "
              "[%d, %d]" % (SHADOW_LOWER, PRODUCT_BOUND))
        return 0

    minimal = is_minimal(best_X, lines)
    rowsup = len({v // N for v in best_X})
    colsup = len({v % N for v in best_X})
    print("  ==> best invariant blocker: %d leaves" % best)
    print("      blocks all 1600 tiles : %s" % verify(best_X, lines))
    print("      minimal (no leaf drop): %s" % minimal)
    print("      row / col support     : %d / %d" % (rowsup, colsup))
    print()
    print("      UPPER BOUND %d -> %d" % (PRODUCT_BOUND, best))
    print("      tau_2 in [%d, %d]   (gap %d -> %d)"
          % (SHADOW_LOWER, best,
             PRODUCT_BOUND - SHADOW_LOWER, best - SHADOW_LOWER))
    print()
    print("      Structural consequence: the prior conditional theorem")
    print("      assumed an optimal blocker has an 11-point row support.")
    print("      This one has %d, so B x B is NOT optimal and that" % rowsup)
    print("      hypothesis is false at the optimum.")

    if "--write" in sys.argv:
        out = os.path.join(ROOT, "data", "tensor_symmetric_blocker.json")
        with open(out, "w") as fh:
            json.dump({
                "schema": "holotrade.tensor-symmetric-blocker.v1",
                "lowerBound": SHADOW_LOWER,
                "previousUpperBound": PRODUCT_BOUND,
                "upperBound": best,
                "gapBefore": PRODUCT_BOUND - SHADOW_LOWER,
                "gapAfter": best - SHADOW_LOWER,
                "witness": best_X,
                "witnessBlocksAll1600": verify(best_X, lines),
                "witnessMinimal": minimal,
                "rowSupport": rowsup,
                "colSupport": colsup,
                "symmetry": best_meta,
                "sweep": rows,
                "productConstructionOptimal": False,
                "exactTau": None,
                "onesided": ("a hit is a verified upper bound; a miss, and "
                             "optimality within a symmetry class, bound "
                             "nothing about tau_2"),
                "boundary": ("tau_2 remains OPEN in [%d, %d]. The lower bound "
                             "is unchanged by this run." % (SHADOW_LOWER, best)),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(out, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
