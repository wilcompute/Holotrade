#!/usr/bin/env python3
"""
The lower bound, with the centre structure and two proved facts the earlier
models did not have.

THE RECORD SO FAR.  Three attacks on |X| = 110 have returned UNKNOWN: the
one-sided tight model (1901 s), the two-sided model with the degree identity
(1901 s), and the same with a sound 360-fold symmetry break (2302 s).  The
degree-sequence decomposition was tried and abandoned: 41,672 sequences found
before the enumeration timed out, so splitting on f is not the way in.

Rather than spend more time on the same formulation, this one adds three
things that are genuinely new to the model.

(1) THE CENTRE, AND THE EXCESS BALANCE.  Every minimum blocking set of
W(3,3) has a centre: a point p whose four lines it meets twice, all other 36
lines once, and which it never contains.  There are 9 blockers per centre and
40 centres (analysis/w33_blocker_centre_structure.py verifies this; it is
presumed prior art, dual to the published structure of small-excess covers of
Q(4,3), and is used here, not claimed).

At |X| = 110 the row shadows S_L are 40 minimum blockers, and tightness on
the transposed axis forces, for every line L,

    sum over M of |T_M cap L|  =  sum over p in L of 4|X_p|  =  44.

Each |T_M cap L| is 1 or 2, over 40 blockers, so the number of M with
|T_M cap L| = 2 is exactly 4.  Since those are precisely the lines of the
centre's pencil, the condition becomes:

    the multiset of the 40 CENTRES meets every line exactly 4 times.

That is a balanced-design constraint on 40 point-valued variables, and it is
far more propagating than the raw blocker choice it replaces.

(2) SUPPORT AT LEAST 24, PROVED.  Naive counting gives only
support >= ceil(110/7) = 16, from alpha = 7.  Optimising the fibre-size
program directly -- line sums exactly 11, 0 <= f <= 7 -- proves the minimum
support is 24, and CP-SAT reports OPTIMAL.  The geometry beats the counting
bound by eight, on both axes.  Also proved there: the largest fibre is at
least 4, so no tight solution is flat.

(3) The sound 360-fold symmetry break carried over from the previous model.
Not 360^2 -- the row and column normalisations are coupled, and assuming both
would manufacture a false INFEASIBLE.

OUTCOMES, unchanged.  INFEASIBLE raises the lower bound to 111 and gives
[111, 115].  FEASIBLE closes the interval at 110.  UNKNOWN proves nothing and
is reported as nothing.
"""

import collections
import json
import os
import subprocess
import sys

try:
    from ortools.sat.python import cp_model
except ImportError:
    sys.exit("needs ortools:  py -3 -m pip install ortools")

ROOT = r"C:\Repos\Holotrade"
N = 40
TAU1 = 11
TIGHT = 110
ALPHA = 7
MIN_SUPPORT = 24        # proved by direct optimisation, not assumed
EXCESS_PER_LINE = 4     # 4*tau_1 - 40


def load():
    out = subprocess.run(
        ["node", "-e",
         "global.window=global;"
         "const S=require('./js/substrate.js');"
         "const R=require('./analysis/tensor_blocking_reformulation.js');"
         "process.stdout.write(JSON.stringify({"
         "lines:S.LINES.map(l=>[...l].sort((a,b)=>a-b)),"
         "blockers:R.minimumBlockers().map(b=>[...b].sort((a,b)=>a-b))}));"],
        cwd=ROOT, capture_output=True, text=True)
    if out.returncode:
        sys.exit("node failed: " + out.stderr[:600])
    d = json.loads(out.stdout)
    return d["lines"], d["blockers"]


def centres_of(lines, blockers):
    pencil = {p: frozenset(li for li, L in enumerate(lines) if p in L)
              for p in range(N)}
    by_pencil = {v: k for k, v in pencil.items()}
    cent = []
    for b in blockers:
        s = set(b)
        exc = frozenset(li for li, L in enumerate(lines)
                        if len(s & set(L)) >= 2)
        c = by_pencil.get(exc)
        if c is None:
            sys.exit("a blocker's excess set is not a pencil; structure broken")
        cent.append(c)
    return cent


def build(lines, blockers, cent, target, do_break):
    nb = len(blockers)
    inblk = [[q in set(b) for q in range(N)] for b in blockers]

    m = cp_model.CpModel()
    x = [[m.NewBoolVar("x%d_%d" % (p, q)) for q in range(N)] for p in range(N)]
    selR = [[m.NewBoolVar("") for _ in range(nb)] for _ in range(N)]
    selC = [[m.NewBoolVar("") for _ in range(nb)] for _ in range(N)]
    for li in range(N):
        m.AddExactlyOne(selR[li])
        m.AddExactlyOne(selC[li])

    inR = [[m.NewBoolVar("") for _ in range(N)] for _ in range(N)]
    inC = [[m.NewBoolVar("") for _ in range(N)] for _ in range(N)]
    for li in range(N):
        for q in range(N):
            m.Add(inR[li][q] == sum(selR[li][bi] for bi in range(nb) if inblk[bi][q]))
            m.Add(inC[li][q] == sum(selC[li][bi] for bi in range(nb) if inblk[bi][q]))
        m.Add(sum(inR[li]) == TAU1)
        m.Add(sum(inC[li]) == TAU1)

    for li, L in enumerate(lines):
        for q in range(N):
            m.Add(sum(x[p][q] for p in L) == inR[li][q])
    for mi, M in enumerate(lines):
        for p in range(N):
            m.Add(sum(x[p][q] for q in M) == inC[mi][p])

    # degree identity
    for q in range(N):
        m.Add(sum(inR[li][q] for li in range(N))
              == 4 * sum(x[p][q] for p in range(N)))
    for p in range(N):
        m.Add(sum(inC[mi][p] for mi in range(N))
              == 4 * sum(x[p][q] for q in range(N)))

    # (1) centres, and the excess balance on both axes
    cR = [[m.NewBoolVar("") for _ in range(N)] for _ in range(N)]
    cC = [[m.NewBoolVar("") for _ in range(N)] for _ in range(N)]
    for li in range(N):
        for p in range(N):
            same = [bi for bi in range(nb) if cent[bi] == p]
            m.Add(cR[li][p] == sum(selR[li][bi] for bi in same))
            m.Add(cC[li][p] == sum(selC[li][bi] for bi in same))
        m.AddExactlyOne(cR[li])
        m.AddExactlyOne(cC[li])
    for L in lines:
        m.Add(sum(cR[li][p] for li in range(N) for p in L) == EXCESS_PER_LINE)
        m.Add(sum(cC[li][p] for li in range(N) for p in L) == EXCESS_PER_LINE)
    # a blocker never contains its own centre
    for li in range(N):
        for p in range(N):
            m.AddImplication(cR[li][p], inR[li][p].Not())
            m.AddImplication(cC[li][p], inC[li][p].Not())

    # (2) support at least 24 on both axes, proved separately
    rowNZ = [m.NewBoolVar("") for _ in range(N)]
    colNZ = [m.NewBoolVar("") for _ in range(N)]
    for p in range(N):
        rs = sum(x[p][q] for q in range(N))
        m.Add(rs >= 1).OnlyEnforceIf(rowNZ[p])
        m.Add(rs == 0).OnlyEnforceIf(rowNZ[p].Not())
        m.Add(rs <= ALPHA)
        cs = sum(x[pp][p] for pp in range(N))
        m.Add(cs >= 1).OnlyEnforceIf(colNZ[p])
        m.Add(cs == 0).OnlyEnforceIf(colNZ[p].Not())
        m.Add(cs <= ALPHA)
    m.Add(sum(rowNZ) >= MIN_SUPPORT)
    m.Add(sum(colNZ) >= MIN_SUPPORT)

    m.Add(sum(x[p][q] for p in range(N) for q in range(N)) == target)
    if do_break:
        m.Add(selR[0][0] == 1)      # sound; see tensor_tight_two_sided.py
    return m, x


def verify(X, lines):
    S = set(X)
    return all(any((p * N + q) in S for p in A for q in B)
               for A in lines for B in lines)


def main():
    seconds = (float(sys.argv[sys.argv.index("--seconds") + 1])
               if "--seconds" in sys.argv else 1800.0)
    target = (int(sys.argv[sys.argv.index("--target") + 1])
              if "--target" in sys.argv else TIGHT)
    lines, blockers = load()
    cent = centres_of(lines, blockers)
    per = collections.Counter(cent)

    print("THE DEPTH-2 LOWER BOUND, WITH CENTRES")
    print("=" * 72)
    print("  minimum blockers      : %d" % len(blockers))
    print("  distinct centres      : %d, %s blockers each"
          % (len(per), sorted(set(per.values()))))
    print("  excess per line       : 4*%d - %d = %d" % (TAU1, N, EXCESS_PER_LINE))
    print("  proved min support    : %d   (naive counting gives only %d)"
          % (MIN_SUPPORT, -(-TIGHT // ALPHA)))
    print("  symmetry break        : 360-fold, row axis only (sound)")
    print()

    m, x = build(lines, blockers, cent, target, "--break" in sys.argv)
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = seconds
    s.parameters.num_search_workers = 8
    s.parameters.symmetry_level = 4
    print("  solving at |X| = %d, budget %.0f s ..." % (target, seconds))
    st = s.Solve(m)
    name = s.StatusName(st)
    print("  status: %s   (%.1f s)" % (name, s.WallTime()))
    print()

    res = {
        "schema": "holotrade.tensor-tight-centred.v1",
        "target": target,
        "status": name,
        "wallSeconds": round(s.WallTime(), 1),
        "added": {
            "centreExcessBalanceBothAxes": True,
            "centreNotInItsOwnBlocker": True,
            "provedMinimumSupport": MIN_SUPPORT,
            "naiveCountingSupport": -(-TIGHT // ALPHA),
            "soundSymmetryBreak360": "--break" in sys.argv,
        },
    }
    if st == cp_model.INFEASIBLE:
        print("  ==> INFEASIBLE.  tau_2 >= %d, so tau_2 in [%d, 115]."
              % (target + 1, target + 1))
        res.update({"conclusion": "lower bound rises to %d" % (target + 1),
                    "newLowerBound": target + 1, "proved": True})
    elif st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        X = sorted(p * N + q for p in range(N) for q in range(N)
                   if s.Value(x[p][q]))
        ok = verify(X, lines)
        print("  ==> FEASIBLE: %d leaves, verified: %s" % (len(X), ok))
        if ok and len(X) == TIGHT:
            print("      tau_2 = %d EXACTLY; the interval CLOSES." % TIGHT)
            res["exactTau"] = TIGHT
        res.update({"witness": X, "witnessVerified": ok, "proved": ok,
                    "conclusion": ("tau_2 = %d exactly" % TIGHT) if ok
                                  else "feasible"})
    else:
        print("  ==> UNKNOWN in budget.  Nothing proved; tau_2 stays [110, 115].")
        res.update({"conclusion": "undecided in budget", "proved": False,
                    "intervalUnchanged": [110, 115]})

    if "--write" in sys.argv:
        out = os.path.join(ROOT, "data", "tensor_tight_centred.json")
        with open(out, "w") as fh:
            json.dump(res, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(out, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
