#!/usr/bin/env python3
"""
The depth-2 tight case as a single matrix equation, and an independent
re-derivation of the centre balance.

Six CP-SAT formulations and several SAT encodings have attacked tau_2 = 110
from the constraint side. This file steps back and asks what the tight case
IS, in one line of linear algebra.

THE EQUATION.  Let N be the 40 x 40 point-line incidence matrix of W(3,3) and
X the 0/1 leaf matrix of a candidate blocker. Then

    T = N^T X N        has      T[L][M] = |B_L cap M|,

the trace of the row shadow of line L on line M. Our centre theorem says every
minimum blocker meets each line once or twice, with exactly four doubled lines
forming a pencil. So T = J + D, where D is 0/1 with all row sums 4.

Row L of D marks the four lines that B_L meets twice, and the centre theorem
identifies those as the pencil of c(L). Row p of N is exactly the indicator
vector of pencil(p). Therefore D = P N, where P is the 0/1 centre-selection
matrix with P[L][c(L)] = 1, and the whole tight case collapses to

    N^T X N  =  J + P N.

WHAT FALLS OUT, and it is a genuine cross-check rather than a restatement.

  * The column sums of D must also be 4, since T's column sums are 44 by the
    transposed tightness. Column M of D = P N has sum #{L : c(L) in M}. So

        #{L : c(L) in M} = 4  for every line M,

    which is EXACTLY the centre-balance condition derived earlier by an
    entirely different route -- counting the excess |B_L cap M| - 1 over all
    40 blockers. Two independent derivations of the same condition.

  * rank(N^T X N) <= rank(N) = 25, and the all-ones vector lies in rowspace(N)
    because the rows of N sum to 4 * 1. So D's rows lie in a 25-dimensional
    space -- consistent with D = P N, whose rows literally ARE rows of N.

HONEST SCOPE.  Everything closes. This is NOT an obstruction, and a matrix
identity that merely restates a problem is easy to oversell. What it provides
is the sharpest available formulation:

    tau_2 = 110 iff there exist a 0/1 leaf matrix X and a centre map P with
    N^T X N = J + P N, every row and column of X independent, and P's column
    sums meeting every line exactly four times.

and a second, independent derivation of the centre balance, which had
previously rested on one counting argument alone.
"""

import json
import os
import subprocess
import sys

ROOT = r"C:\Repos\Holotrade"
N_PTS = 40


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
        sys.exit("node failed: " + out.stderr[:400])
    d = json.loads(out.stdout)
    return d["lines"], d["blockers"]


def main():
    lines, blockers = load()
    n = N_PTS
    # N[p][L] = 1 iff p lies on L
    Nmat = [[1 if p in lines[li] else 0 for li in range(n)] for p in range(n)]
    pencil = {p: frozenset(li for li in range(n) if Nmat[p][li]) for p in range(n)}
    by_pencil = {v: k for k, v in pencil.items()}

    print("THE TIGHT CASE AS A MATRIX EQUATION")
    print("=" * 70)
    checks = {}
    checks["everyPointOnFourLines"] = all(len(v) == 4 for v in pencil.values())
    checks["rowsOfNSumToFour"] = all(sum(Nmat[p]) == 4 for p in range(n))
    # 1 lies in rowspace(N): the rows of N sum to 4*1 over lines
    colsum = [sum(Nmat[p][li] for p in range(n)) for li in range(n)]
    checks["allOnesInRowspaceOfN"] = all(c == 4 for c in colsum)

    # For every minimum blocker, its doubled-line set IS a pencil, so the
    # D = P N identification is exactly our centre theorem.
    pencil_rows, centres = 0, []
    for b in blockers:
        bs = set(b)
        dbl = frozenset(li for li, L in enumerate(lines) if len(bs & set(L)) == 2)
        one = sum(1 for L in lines if len(bs & set(L)) == 1)
        if dbl in by_pencil and len(dbl) == 4 and one == 36:
            pencil_rows += 1
            centres.append(by_pencil[dbl])
    checks["everyBlockerRowOfDIsAPencilRowOfN"] = pencil_rows == len(blockers)
    checks["traceSumIs44"] = all(
        sum(len(set(b) & set(L)) for L in lines) == 44 for b in blockers)

    print("  T = N^T X N has T[L][M] = |B_L cap M|; the centre theorem gives")
    print("  T = J + D with D 0/1 and four 1s per row, and each such row is")
    print("  the pencil of c(L) -- i.e. a row of N. Hence D = P N and")
    print()
    print("      N^T X N  =  J + P N")
    print()
    for k, v in checks.items():
        print("  %-38s %s" % (k, v))
    print()
    print("  CROSS-CHECK: the column sums of D = P N must be 4, which says")
    print("  #{L : c(L) in M} = 4 for every line M -- exactly the centre")
    print("  balance derived earlier by counting excess over all 40 blockers.")
    print("  Two independent derivations of the same condition.")
    print()
    print("  rank(N^T X N) <= rank(N) = 25, and 1 is in rowspace(N), so D's")
    print("  rows live in 25 dimensions -- consistent with D = P N.")
    print()
    print("  This is NOT an obstruction: everything closes. It is the sharpest")
    print("  formulation, plus a second derivation of the centre balance.")

    ok = all(checks.values())
    if "--write" in sys.argv:
        out = os.path.join(ROOT, "data", "tensor_tight_matrix_equation.json")
        with open(out, "w") as fh:
            json.dump({
                "schema": "holotrade.tensor-tight-matrix-equation.v1",
                "valid": ok,
                "equation": "N^T X N = J + P N",
                "meaning": ("T[L][M] = |B_L cap M| is 1 or 2 with exactly four "
                            "2s per row; those four lines are the pencil of "
                            "c(L), and pencil rows are rows of N, so the "
                            "excess matrix D factors as P N with P the "
                            "centre-selection matrix"),
                "checks": checks,
                "crossCheck": ("column sums of D = 4 give #{L : c(L) in M} = 4 "
                               "for every line M -- the centre-balance "
                               "condition, previously derived by a different "
                               "counting argument. Two independent routes to "
                               "the same statement."),
                "rankNote": ("rank(N^T X N) <= rank(N) = 25 and 1 lies in "
                             "rowspace(N) since N's rows sum to 4*1, so D's "
                             "rows lie in 25 dimensions, consistent with "
                             "D = P N"),
                "sharpestFormulation": ("tau_2 = 110 iff there exist a 0/1 leaf "
                                        "matrix X and a centre map P with "
                                        "N^T X N = J + P N, every row and "
                                        "column of X independent, and P's "
                                        "column sums meeting every line "
                                        "exactly four times"),
                "isAnObstruction": False,
                "boundary": ("everything closes, so this proves nothing about "
                             "tau_2, which stays open in [110, 115]. A matrix "
                             "identity that restates a problem is easy to "
                             "oversell and this one is recorded as a "
                             "reformulation plus a cross-check, nothing more."),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(out, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
