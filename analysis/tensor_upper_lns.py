#!/usr/bin/env python3
"""
Push the depth-2 upper bound below 115 by large-neighbourhood search.

WHY THIS, AND WHY NOW.  The symmetric search that took 121 down to 115 is
exhausted: sweeping all 12 cycle-type classes of Aut(W33) and every twist,
with the objective capped at 114, produced nothing.  Non-cyclic subgroups
would only be more restrictive.  So the symmetric family has been mined out,
and anything smaller than 115 -- if it exists -- carries no cyclic symmetry
at all, or carries one this parameterisation cannot reach.

Direct search over all 1,600 leaves is hopeless for the reason that motivated
the symmetric approach in the first place.  LNS threads between the two: keep
the 115-leaf incumbent, FREE a slice of it, and re-optimise that slice exactly
while the rest stays fixed.  The freed subproblem is small enough for CP-SAT
to close, and repeated over different slices the search can leave the
symmetric family entirely -- which the exact symmetric solver structurally
cannot do.

Two neighbourhood shapes, alternated:

  ROW SLICE     free every leaf in k randomly chosen rows (points of the
                first coordinate).  Rows are the natural unit because the
                blocking condition decomposes over first-coordinate lines.
  LINE SLICE    free every leaf whose first coordinate lies on k randomly
                chosen W(3,3) lines.  Lines cut across rows and respect the
                geometry, so the two shapes fail in different ways.

Every improvement is re-verified from scratch against all 1,600 tiles before
it is accepted, so a solver bug cannot quietly lower the reported bound.

ONE-SIDEDNESS, again.  An improvement is a real upper bound.  Exhausting this
search proves nothing whatsoever about tau_2: it bounds the method, not the
object.  The lower bound of 110 is untouched by anything here.
"""

import json
import os
import random
import subprocess
import sys
import time

try:
    from ortools.sat.python import cp_model
except ImportError:
    sys.exit("needs ortools:  py -3 -m pip install ortools")

ROOT = r"C:\Repos\Holotrade"
N = 40
SHADOW_LOWER = 110


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


def verify(X, lines):
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


def reoptimise(lines, incumbent, free, seconds):
    """Re-solve exactly on `free`, holding every other leaf at its incumbent."""
    inc = set(incumbent)
    m = cp_model.CpModel()
    var = {}
    for v in free:
        var[v] = m.NewBoolVar("v%d" % v)
    fixed_in = [v for v in inc if v not in free]
    fixed_set = set(fixed_in)

    for A in lines:
        for B in lines:
            leaves = [p * N + q for p in A for q in B]
            if any(v in fixed_set for v in leaves):
                continue                      # already blocked by fixed part
            lits = [var[v] for v in leaves if v in var]
            if not lits:
                return None                   # tile unblockable: reject slice
            m.AddBoolOr(lits)

    total = len(fixed_in) + sum(var.values())
    m.Add(total <= len(incumbent) - 1)        # only accept a strict improvement
    m.Add(total >= SHADOW_LOWER)
    m.Minimize(total)

    for v in free:                            # warm start from the incumbent
        m.AddHint(var[v], 1 if v in inc else 0)

    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = float(seconds)
    s.parameters.num_search_workers = 8
    st = s.Solve(m)
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return sorted(fixed_in + [v for v in free if s.Value(var[v])])
    return None


def main():
    budget = (float(sys.argv[sys.argv.index("--minutes") + 1]) * 60
              if "--minutes" in sys.argv else 900.0)
    per = (float(sys.argv[sys.argv.index("--per") + 1])
           if "--per" in sys.argv else 30.0)
    lines, witness = load()

    print("LNS ON THE DEPTH-2 UPPER BOUND")
    print("=" * 72)
    print("  incumbent            : %d leaves" % len(witness))
    print("  verified on load     : %s" % verify(witness, lines))
    print("  proved lower bound   : %d" % SHADOW_LOWER)
    print("  a hit is a real upper bound; exhausting the search proves nothing")
    print()

    best = list(witness)
    rng = random.Random(19)
    t0, rounds, hits = time.time(), 0, 0
    trace = []
    print("   round  shape       freed   result")
    while time.time() - t0 < budget:
        rounds += 1
        if rounds % 2:
            k = rng.choice([5, 6, 7, 8])
            rows = rng.sample(range(N), k)
            free = [p * N + q for p in rows for q in range(N)]
            shape = "rows k=%d" % k
        else:
            k = rng.choice([3, 4, 5])
            chosen = rng.sample(range(len(lines)), k)
            pts = sorted({p for li in chosen for p in lines[li]})
            free = [p * N + q for p in pts for q in range(N)]
            shape = "lines k=%d" % k

        cand = reoptimise(lines, best, free, per)
        if cand and len(cand) < len(best) and verify(cand, lines):
            hits += 1
            print("  %6d  %-10s  %5d   %d  *** IMPROVED"
                  % (rounds, shape, len(free), len(cand)))
            trace.append({"round": rounds, "shape": shape,
                          "freed": len(free), "size": len(cand)})
            best = cand
        elif rounds % 10 == 0:
            print("  %6d  %-10s  %5d   holding at %d"
                  % (rounds, shape, len(free), len(best)))

    print()
    print("  rounds run     : %d" % rounds)
    print("  improvements   : %d" % hits)
    print("  final          : %d leaves" % len(best))
    ok = verify(best, lines)
    minimal = is_minimal(best, lines)
    print("  verified       : %s   minimal: %s" % (ok, minimal))
    if len(best) < len(witness):
        print()
        print("  ==> UPPER BOUND %d -> %d;  tau_2 in [%d, %d]"
              % (len(witness), len(best), SHADOW_LOWER, len(best)))
    else:
        print()
        print("  ==> no improvement.  That bounds the METHOD, not tau_2, which")
        print("      stays in [%d, %d]." % (SHADOW_LOWER, len(witness)))

    if "--write" in sys.argv:
        out = os.path.join(ROOT, "data", "tensor_upper_lns.json")
        with open(out, "w") as fh:
            json.dump({
                "schema": "holotrade.tensor-upper-lns.v1",
                "startedFrom": len(witness),
                "result": len(best),
                "improved": len(best) < len(witness),
                "rounds": rounds,
                "improvements": hits,
                "trace": trace,
                "witness": best if len(best) < len(witness) else None,
                "witnessVerified": ok,
                "witnessMinimal": minimal,
                "lowerBound": SHADOW_LOWER,
                "onesided": ("an improvement is a real upper bound; exhausting "
                             "the search bounds the method, not tau_2"),
                "exactTau": None,
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(out, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
