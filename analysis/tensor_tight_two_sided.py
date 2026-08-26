#!/usr/bin/env python3
"""
The lower bound, attacked with the FULL two-sided tight structure.

The previous attempt (tensor_tight_rows_and_columns.py) encoded tightness on
one axis and derived independence on the other, and returned UNKNOWN after
2101 s.  This one encodes the structure on BOTH axes simultaneously, plus the
degree identity that links them, and channels through explicit availability
variables so the solver never has to rediscover a conjunction.

WHAT IS FORCED AT |X| = 110.  Write X_p = {q : (p,q) in X} and
Y_q = {p : (p,q) in X}.  The double count 4|X| >= sum of shadows >= 440 has
exactly two inequalities, so at 110 both are equalities on every line, giving
the shadow S_L = union of X_p over p in L a size of exactly 11 and forcing the
four fibres over a line to be pairwise disjoint.  Blocking is symmetric in the
two coordinates and |X| = |X^T|, so the same holds transposed for the shadows
T_M = union of Y_q over q in M.  Four consequences, all encoded here:

  (A)  S_L is one of the exactly 360 minimum line blockers, for all 40 lines;
  (B)  T_M is one of the same 360, for all 40 lines -- the transposed half,
       which the previous model left for the solver to infer;
  (C)  every X_p and every Y_q is an INDEPENDENT set of W(3,3), hence of size
       at most alpha = 7.  (If X_p held two points of a line M, then p would
       lie in two of the Y_q for q in M, which transposed disjointness
       forbids.)  Note alpha = 7 and not the Hoffman value 10 -- the gap is
       exactly why W(3,3) has no ovoid;
  (D)  THE DEGREE IDENTITY.  Y_q is independent, so it meets exactly 4|Y_q|
       lines, once each; and the lines it meets are exactly those whose
       blocker contains q.  Therefore

           #{L : q in S_L}  =  4 |Y_q|      for every point q,

       and symmetrically #{M : p in T_M} = 4 |X_p|.  In particular every such
       degree is divisible by 4 and at most 28.  This links the two blocker
       families to the fibre sizes and is the constraint the earlier model had
       no way to express.

Availability channelling: X_p is contained in every blocker on a line through
p, so a leaf (p,q) is usable only if all four of those blockers contain q.
That conjunction is given its own variable rather than left implicit.

OUTCOMES.  INFEASIBLE raises the lower bound to 111 and gives [111, 115].
FEASIBLE means tau_2 = 110 and the interval closes, because 110 is already a
proved lower bound.  UNKNOWN proves nothing and is reported as such.
"""

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


def build(lines, blockers, target):
    nb = len(blockers)
    inblk = [[q in set(b) for q in range(N)] for b in blockers]
    thru = [[li for li, L in enumerate(lines) if p in L] for p in range(N)]
    assert all(len(t) == 4 for t in thru), "W(3,3) is 4-regular on lines"

    m = cp_model.CpModel()
    x = [[m.NewBoolVar("x%d_%d" % (p, q)) for q in range(N)] for p in range(N)]

    # (A) and (B): pick a minimum blocker for every line on each axis.
    selR = [[m.NewBoolVar("") for _ in range(nb)] for _ in range(N)]
    selC = [[m.NewBoolVar("") for _ in range(nb)] for _ in range(N)]
    for li in range(N):
        m.AddExactlyOne(selR[li])
        m.AddExactlyOne(selC[li])

    inR = [[m.NewBoolVar("") for q in range(N)] for li in range(N)]
    inC = [[m.NewBoolVar("") for p in range(N)] for li in range(N)]
    for li in range(N):
        for q in range(N):
            m.Add(inR[li][q] == sum(selR[li][bi] for bi in range(nb) if inblk[bi][q]))
            m.Add(inC[li][q] == sum(selC[li][bi] for bi in range(nb) if inblk[bi][q]))
        # each blocker has exactly tau_1 points, so each shadow does too
        m.Add(sum(inR[li][q] for q in range(N)) == TAU1)
        m.Add(sum(inC[li][p] for p in range(N)) == TAU1)

    # Shadow definition + tight disjointness, both axes at once.
    # "== " rather than ">=" is what tightness buys, and it also encodes (C):
    # the right-hand side is a single Boolean, so the sum is at most one.
    for li, L in enumerate(lines):
        for q in range(N):
            m.Add(sum(x[p][q] for p in L) == inR[li][q])
    for mi, M in enumerate(lines):
        for p in range(N):
            m.Add(sum(x[p][q] for q in M) == inC[mi][p])

    # (C) explicit size caps.  Implied above, but stated for propagation.
    for p in range(N):
        m.Add(sum(x[p][q] for q in range(N)) <= ALPHA)
    for q in range(N):
        m.Add(sum(x[p][q] for p in range(N)) <= ALPHA)

    # (D) the degree identity, linking the two blocker families to fibre sizes.
    for q in range(N):
        m.Add(sum(inR[li][q] for li in range(N))
              == 4 * sum(x[p][q] for p in range(N)))
    for p in range(N):
        m.Add(sum(inC[mi][p] for mi in range(N))
              == 4 * sum(x[p][q] for q in range(N)))

    # Availability: (p,q) is usable only if every blocker on a line through p
    # contains q.  Give the conjunction a name so it propagates immediately.
    for p in range(N):
        for q in range(N):
            for li in thru[p]:
                m.AddImplication(x[p][q], inR[li][q])
            for mi in thru[q]:
                m.AddImplication(x[p][q], inC[mi][p])

    m.Add(sum(x[p][q] for p in range(N) for q in range(N)) == target)

    # SYMMETRY BREAKING, worth 360.
    #
    # The problem's symmetry group is Aut(W33) x Aut(W33) acting as
    # (p,q) -> (g p, h q).  Under it the row shadow of line g(L) becomes
    # h(S_L), and the column shadow of line h(M) becomes g(T_M).
    #
    # The 360 minimum blockers form a SINGLE Aut(W33)-orbit, with stabiliser
    # of order 51840/360 = 144 (verified by explicit orbit computation from
    # the generators).  So for ANY g whatsoever, S_{g^-1(0)} is some minimum
    # blocker and transitivity supplies an h carrying it to a fixed beta_0.
    # Every solution therefore has an image whose row shadow on line 0 is
    # beta_0, and pinning it loses nothing.
    #
    # NOT ALSO THE COLUMN SHADOW.  It is tempting to pin T_0 = beta_0 by the
    # same argument on the other factor, for 360^2.  That is WRONG, and the
    # error is worth recording because it would manufacture a false
    # INFEASIBLE and hence a false theorem.  The two normalisations are
    # coupled, not independent: fixing the row shadow of line 0 determines h
    # up to Stab(beta_0), and the column condition g(T_{h^-1(0)}) = beta_0
    # then constrains g GIVEN that h.  Choosing h first inverts the coupling
    # rather than removing it.  Only one of the two may be assumed free.
    if "--break" in sys.argv:
        m.Add(selR[0][0] == 1)
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
    print("THE DEPTH-2 LOWER BOUND, TWO-SIDED")
    print("=" * 72)
    print("  minimum line blockers : %d, all of size %d"
          % (len(blockers), TAU1))
    print("  alpha(W(3,3))         : %d   (Hoffman gives 10)" % ALPHA)
    print("  encoded: (A) row shadows, (B) column shadows, (C) both fibre")
    print("           families independent, (D) degree = 4 * fibre size")
    if "--break" in sys.argv:
        print("  symmetry break: row shadow of line 0 pinned to one blocker")
        print("                  -- worth 360 (the column shadow may NOT")
        print("                  also be pinned; the two are coupled)")
    print()

    m, x = build(lines, blockers, target)
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
        "schema": "holotrade.tensor-tight-two-sided.v1",
        "target": target,
        "status": name,
        "wallSeconds": round(s.WallTime(), 1),
        "encoded": {
            "A_rowShadowIsMinimumBlocker": True,
            "B_columnShadowIsMinimumBlocker": True,
            "C_bothFibreFamiliesIndependent": True,
            "D_degreeEqualsFourTimesFibreSize": True,
        },
        "symmetryBroken": "--break" in sys.argv,
        "symmetryBreakJustification": (
            "the 360 minimum blockers form a single Aut(W33)-orbit, so for "
            "any g there is an h carrying the row shadow of line 0 to a "
            "fixed blocker. Only ONE of the two shadow families may be "
            "normalised: pinning the column shadow too would be unsound, "
            "because fixing the row shadow already constrains h and the "
            "column condition then constrains g given that h."),
    }

    if st == cp_model.INFEASIBLE:
        print("  ==> INFEASIBLE.  tau_2 >= %d." % (target + 1))
        print("      With the 115 construction: tau_2 in [%d, 115]." % (target + 1))
        res["conclusion"] = "lower bound rises to %d" % (target + 1)
        res["newLowerBound"] = target + 1
        res["proved"] = True
    elif st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        X = sorted(p * N + q for p in range(N) for q in range(N)
                   if s.Value(x[p][q]))
        ok = verify(X, lines)
        print("  ==> FEASIBLE: %d leaves, verified against all 1600 tiles: %s"
              % (len(X), ok))
        if ok and len(X) == TIGHT:
            print("      tau_2 = %d EXACTLY; the interval CLOSES." % TIGHT)
            res["exactTau"] = TIGHT
        res["witness"] = X
        res["witnessVerified"] = ok
        res["proved"] = ok
        res["conclusion"] = ("tau_2 = %d exactly" % TIGHT) if ok else "feasible"
    else:
        print("  ==> UNKNOWN in budget.  Nothing proved; tau_2 stays [110, 115].")
        res["conclusion"] = "undecided in budget"
        res["proved"] = False
        res["intervalUnchanged"] = [110, 115]

    if "--write" in sys.argv:
        out = os.path.join(ROOT, "data", "tensor_tight_two_sided.json")
        with open(out, "w") as fh:
            json.dump(res, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(out, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
