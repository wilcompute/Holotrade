#!/usr/bin/env python3
"""
Simulated annealing on the depth-2 upper bound: can 114 leaves block?

WHY A THIRD TOOL.  Two exact methods have stopped at 115 and neither can go
further on its own terms.  Symmetry-restricted CP-SAT is exhausted -- all 12
cycle-type classes of Aut(W33) and every twist, capped at 114, found nothing,
and non-cyclic subgroups are strictly more restrictive.  Large-neighbourhood
search from the 115 incumbent ran 40+ rounds freeing up to 680 leaves at a
time and never improved.  Both are exact-on-a-slice; both inherit the same
blind spot, which is that they only ever move through blockers.

Annealing does not.  It works at a FIXED size of 114 and lets the candidate
be an illegal set -- one that leaves some tiles unblocked -- while it walks.
The objective is the number of unblocked tiles, and any state reaching zero
is a 114-leaf blocker, which would improve the bound. That path crosses
regions no method restricted to valid blockers can enter.

THE INCREMENTAL TRICK.  A leaf (p,q) lies in exactly 4 x 4 = 16 tiles, since
each of p and q is on four lines.  Keeping a count of how many chosen leaves
each tile holds, a swap touches only the 16 tiles of the leaf leaving and the
16 of the leaf arriving.  The cost delta is therefore O(32) rather than
O(1600), which buys a few million moves per minute in plain Python and makes
the walk long enough to matter.

WHAT AN OUTCOME MEANS.  Reaching zero is a genuine, re-verified upper bound.
Failing to reach zero means nothing about tau_2 -- annealing is not a
decision procedure, and its failure bounds the search, not the object.  The
lower bound of 110 is untouched either way.
"""

import json
import math
import os
import random
import subprocess
import sys
import time

ROOT = r"C:\Repos\Holotrade"
N = 40


def load():
    out = subprocess.run(
        ["node", "-e",
         "global.window=global;"
         "const S=require('./js/substrate.js');"
         "const T=require('./js/tensor-sharding.js');"
         "process.stdout.write(JSON.stringify({"
         "lines:S.LINES.map(l=>[...l].sort((a,b)=>a-b)),"
         "witness:[...T.SYMMETRIC_WITNESS]}));"],
        cwd=ROOT, capture_output=True, text=True)
    if out.returncode:
        sys.exit("node failed: " + out.stderr[:600])
    d = json.loads(out.stdout)
    return d["lines"], d["witness"]


def build_index(lines):
    """tiles_of[leaf] -> the 16 tile ids containing it; tile id = a*40+b."""
    thru = [[li for li, L in enumerate(lines) if p in L] for p in range(N)]
    tiles_of = [None] * (N * N)
    for p in range(N):
        for q in range(N):
            tiles_of[p * N + q] = tuple(a * N + b for a in thru[p]
                                        for b in thru[q])
    assert all(len(t) == 16 for t in tiles_of)
    return tiles_of


def anneal(lines, tiles_of, size, seconds, seed, start=None, guided=True):
    rng = random.Random(seed)
    all_leaves = list(range(N * N))
    if start and len(start) >= size:
        cur = set(rng.sample(list(start), size))
    else:
        cur = set(rng.sample(all_leaves, size))

    count = [0] * (N * N)
    for v in cur:
        for t in tiles_of[v]:
            count[t] += 1
    cost = sum(1 for t in range(N * N) if count[t] == 0)

    outside = [v for v in all_leaves if v not in cur]
    inside = list(cur)
    pos_in = {v: i for i, v in enumerate(inside)}
    pos_out = {v: i for i, v in enumerate(outside)}

    best, best_state = cost, set(cur)
    t0 = time.time()
    T0, T1 = 3.0, 0.02
    moves = 0
    while True:
        moves += 1
        if moves % 4096 == 0:
            el = time.time() - t0
            if el > seconds or best == 0:
                break
        frac = min(1.0, (time.time() - t0) / seconds) if seconds else 1.0
        temp = T0 * (T1 / T0) ** frac

        # GUIDED MOVE.  A blind swap is nearly always useless once the
        # candidate is close: only 16 of 1600 tiles even notice it.  So most
        # of the time, pick a tile that is actually unblocked and bring in
        # one of ITS sixteen leaves -- the WalkSAT idea, that repairing a
        # live violation beats sampling the whole space.  The rest of the
        # time move blind, which is what keeps the walk from getting stuck
        # in a basin the guided move cannot leave.
        vin = None
        if guided and rng.random() < 0.85:
            for _ in range(24):
                t = rng.randrange(N * N)
                if count[t] == 0:
                    a, b = t // N, t % N
                    cand = [pp * N + qq for pp in lines[a] for qq in lines[b]
                            if (pp * N + qq) in pos_out]
                    if cand:
                        vin = rng.choice(cand)
                    break
        if vin is None:
            vin = outside[rng.randrange(len(outside))]
        j = pos_out[vin]
        i = rng.randrange(len(inside))
        vout = inside[i]

        delta = 0
        for t in tiles_of[vout]:
            if count[t] == 1:
                delta += 1
            count[t] -= 1
        for t in tiles_of[vin]:
            if count[t] == 0:
                delta -= 1
            count[t] += 1

        if delta <= 0 or rng.random() < math.exp(-delta / temp):
            inside[i], outside[j] = vin, vout
            pos_in[vin], pos_out[vout] = i, j
            del pos_in[vout], pos_out[vin]
            cost += delta
            if cost < best:
                best, best_state = cost, set(inside)
                if best == 0:
                    break
        else:                                   # roll back
            for t in tiles_of[vin]:
                count[t] -= 1
            for t in tiles_of[vout]:
                count[t] += 1
    return best, best_state, moves, time.time() - t0


def verify(X, lines):
    S = set(X)
    return all(any((p * N + q) in S for p in A for q in B)
               for A in lines for B in lines)


def main():
    size = (int(sys.argv[sys.argv.index("--size") + 1])
            if "--size" in sys.argv else 114)
    per = (float(sys.argv[sys.argv.index("--per") + 1])
           if "--per" in sys.argv else 60.0)
    restarts = (int(sys.argv[sys.argv.index("--restarts") + 1])
                if "--restarts" in sys.argv else 12)

    lines, witness = load()
    tiles_of = build_index(lines)

    print("ANNEALING THE DEPTH-2 UPPER BOUND")
    print("=" * 72)
    print("  target size      : %d   (current bound %d)" % (size, len(witness)))
    print("  objective        : number of unblocked tiles, zero is a blocker")
    print("  restarts x budget: %d x %.0f s" % (restarts, per))
    print("  moves            : guided (WalkSAT-style) 85%, blind 15%")
    print("  a hit is a real upper bound; a miss bounds only the search")
    print()

    overall, hit, total_moves = None, None, 0
    print("   run   seed  moves       best unblocked tiles")
    for r in range(restarts):
        seed = 1000 + r
        # warm starts dominated the cold ones in every trial run, so most
        # restarts begin from the incumbent and a few stay cold for diversity
        warm = None if r % 4 == 3 else witness
        best, state, moves, el = anneal(lines, tiles_of, size, per, seed, warm)
        total_moves += moves
        tag = "  <- from the 115 witness" if warm else ""
        print("  %4d  %5d  %9d   %d%s" % (r + 1, seed, moves, best, tag))
        if overall is None or best < overall:
            overall = best
        if best == 0:
            hit = sorted(state)
            break

    print()
    print("  total moves      : %d" % total_moves)
    print("  best cost reached: %d unblocked tiles" % overall)
    res = {
        "schema": "holotrade.tensor-upper-anneal.v1",
        "size": size,
        "restarts": restarts,
        "secondsPerRestart": per,
        "totalMoves": total_moves,
        "bestUnblockedTiles": overall,
        "improved": hit is not None,
        "currentUpperBound": len(witness),
        "lowerBound": 110,
        "exactTau": None,
    }
    if hit is not None:
        ok = verify(hit, lines)
        print("  ==> FOUND a %d-leaf candidate; verified against all 1600 "
              "tiles: %s" % (len(hit), ok))
        if ok:
            print("      UPPER BOUND %d -> %d" % (len(witness), len(hit)))
        res["witness"] = hit
        res["witnessVerified"] = ok
    else:
        print("  ==> no %d-leaf blocker found.  This bounds the SEARCH, not" % size)
        print("      tau_2, which stays in [110, %d]." % len(witness))
        res["onesided"] = ("annealing is not a decision procedure; failing to "
                           "reach zero bounds the search, not tau_2")

    if "--write" in sys.argv:
        out = os.path.join(ROOT, "data", "tensor_upper_anneal.json")
        with open(out, "w") as fh:
            json.dump(res, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(out, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
