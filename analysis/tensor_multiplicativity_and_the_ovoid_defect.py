#!/usr/bin/env python3
"""
Why the gap exists at all: the tensor blocking number is multiplicative
exactly when the quadrangle has an ovoid.

Five attacks on tau_2(W(3,3)) have failed to close [110, 115].  This file
stops attacking and asks a different question -- where does the interval come
from? -- and the answer turns out to be a theorem with a one-line proof and a
clean computational confirmation.

SETUP.  Let Q be a generalized quadrangle of order (s,t): it has
(s+1)(st+1) points and (t+1)(st+1) lines, every line carries s+1 points, and
every point lies on t+1 lines.  Write tau_1 for its blocking number -- the
fewest points meeting every line -- and tau_2 for the blocking number of the
product, the fewest cells of the point-by-point grid meeting every tile
L x M.

THE TWO BOUNDS.  For a blocker X of the product and a line L, the shadow
S_L = union of X_p over p in L must itself block, so |S_L| >= tau_1.  Summing
over all lines, and using that each point lies on t+1 of them,

    (t+1)|X|  =  sum over L of sum over p in L of |X_p|
              >= sum over L of |S_L|
              >= (t+1)(st+1) * tau_1,

so tau_2 >= (st+1) * tau_1.  In the other direction B x B blocks every tile
for any line blocker B, so tau_2 <= tau_1^2.  Hence

    (st+1) * tau_1  <=  tau_2  <=  tau_1^2,

and the width of that interval is exactly

    tau_1^2 - (st+1)*tau_1  =  tau_1 * (tau_1 - (st+1))  =  tau_1 * delta,

where delta = tau_1 - (st+1) is the OVOID DEFECT: how far the quadrangle's
blocking number sits above the ovoid size st+1.

THE THEOREM.  A blocking set of size st+1 is precisely an ovoid.  So delta = 0
if and only if Q has an ovoid, and in that case the two bounds COINCIDE:

    Q has an ovoid   ==>   tau_2 = tau_1^2 = (st+1)^2,

the product construction is optimal, and the tensor blocking number is
multiplicative.  No gap can open.  Conversely a positive defect opens an
interval of width exactly tau_1 * delta, and nothing in the counting decides
where inside it the truth lies.

THE TWO INSTANCES.

  GQ(2,2) = W(3,2).  q even, so it HAS an ovoid: tau_1 = 5 = st+1, delta = 0.
  Both bounds give 25, and CP-SAT confirms tau_2 = 25 exactly, OPTIMAL, over
  the full 225-cell grid with no symmetry assumptions.  Multiplicative.

  W(3,3).  q odd, so by Thas it has NO ovoid.  tau_1 = 11 > st+1 = 10, so
  delta = 1 and the interval has width 11 * 1 = 11 -- which is precisely the
  [110, 121] we started from.  The 115 witness shows the truth is at neither
  end: the product bound is not attained, and the shadow bound is not known
  to be.

NOVELTY, CALIBRATED.  No literature on blocking numbers of PRODUCTS of
generalized quadrangles turned up.  But the statement follows in one line
from two standard bounds, and "an expert would see it immediately" is the
correct description of a one-line consequence of a standard double count.
It is recorded here as a derivation that explains our interval, not as a
discovery, and the repository's own history is the reason for that caution:
a result whose novelty cannot be established is not new.

So the difficulty is not an artefact of the search.  It is the missing ovoid,
showing up two levels above where it was proved missing.  That also says what
would settle it: an argument that converts the ovoid defect into a statement
about the product, rather than more search inside the interval it opens.
"""

import itertools
import json
import os
import subprocess
import sys

try:
    from ortools.sat.python import cp_model
except ImportError:
    sys.exit("needs ortools:  py -3 -m pip install ortools")

ROOT = r"C:\Repos\Holotrade"


def w32():
    """W(3,2): the symplectic GQ of order (2,2), built from scratch."""
    def form(u, v):
        return (u[0] * v[1] + u[1] * v[0] + u[2] * v[3] + u[3] * v[2]) % 2
    pts = [v for v in itertools.product([0, 1], repeat=4) if any(v)]
    idx = {v: i for i, v in enumerate(pts)}
    lines = set()
    for a, b in itertools.combinations(pts, 2):
        if form(a, b) == 0:
            c = tuple(a[i] ^ b[i] for i in range(4))
            lines.add(tuple(sorted(idx[x] for x in (a, b, c))))
    return len(pts), [list(L) for L in sorted(lines)]


def w33():
    out = subprocess.run(
        ["node", "-e",
         "global.window=global;const S=require('./js/substrate.js');"
         "process.stdout.write(JSON.stringify(S.LINES.map(l=>[...l]"
         ".sort((a,b)=>a-b))))"],
        cwd=ROOT, capture_output=True, text=True)
    if out.returncode:
        sys.exit("node failed: " + out.stderr[:400])
    return 40, json.loads(out.stdout)


def solve_tau1(n, lines, seconds=30):
    m = cp_model.CpModel()
    x = [m.NewBoolVar("") for _ in range(n)]
    for L in lines:
        m.AddBoolOr([x[p] for p in L])
    m.Minimize(sum(x))
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = float(seconds)
    s.parameters.num_search_workers = 8
    st = s.Solve(m)
    return int(s.ObjectiveValue()), s.StatusName(st)


def solve_tau2(n, lines, seconds=120):
    m = cp_model.CpModel()
    x = [[m.NewBoolVar("") for _ in range(n)] for _ in range(n)]
    for A in lines:
        for B in lines:
            m.AddBoolOr([x[p][q] for p in A for q in B])
    m.Minimize(sum(x[p][q] for p in range(n) for q in range(n)))
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = float(seconds)
    s.parameters.num_search_workers = 8
    st = s.Solve(m)
    return int(s.ObjectiveValue()), s.StatusName(st)


def report(name, n, lines, tau1, tau1_status, tau2=None, tau2_status=None):
    spl = len(lines[0])
    s = spl - 1
    tpl = sum(1 for L in lines if 0 in L)
    t = tpl - 1
    ovoid_size = s * t + 1
    delta = tau1 - ovoid_size
    lower = ovoid_size * tau1
    upper = tau1 * tau1
    print("  %s" % name)
    print("    order (s,t)          : (%d, %d)" % (s, t))
    print("    points / lines       : %d / %d" % (n, len(lines)))
    print("    ovoid size st+1      : %d" % ovoid_size)
    print("    tau_1                : %d   (%s)" % (tau1, tau1_status))
    print("    ovoid defect delta   : %d   -> has an ovoid: %s"
          % (delta, delta == 0))
    print("    shadow lower (st+1)*tau_1 : %d" % lower)
    print("    product upper tau_1^2     : %d" % upper)
    print("    interval width tau_1*delta: %d" % (tau1 * delta))
    assert upper - lower == tau1 * delta, "the width formula must close"
    if tau2 is not None:
        print("    tau_2                : %d   (%s)" % (tau2, tau2_status))
        if delta == 0:
            print("    => MULTIPLICATIVE: tau_2 = tau_1^2, product optimal")
        else:
            print("    => tau_2 sits inside an interval of width %d"
                  % (tau1 * delta))
    return {
        "name": name, "s": s, "t": t, "points": n, "lines": len(lines),
        "ovoidSize": ovoid_size, "tau1": tau1, "tau1Status": tau1_status,
        "ovoidDefect": delta, "hasOvoid": delta == 0,
        "shadowLower": lower, "productUpper": upper,
        "intervalWidth": tau1 * delta,
        "tau2": tau2, "tau2Status": tau2_status,
        "multiplicative": (tau2 == upper) if tau2 is not None else None,
    }


def main():
    print("MULTIPLICATIVITY AND THE OVOID DEFECT")
    print("=" * 72)
    print("  (st+1)*tau_1 <= tau_2 <= tau_1^2, an interval of width")
    print("  tau_1*(tau_1 - (st+1)) = tau_1 * delta.  delta = 0 exactly when")
    print("  the quadrangle has an ovoid, and then the bounds coincide.")
    print()

    rows = []
    n2, l2 = w32()
    t1, s1 = solve_tau1(n2, l2)
    t2, s2 = solve_tau2(n2, l2)
    rows.append(report("GQ(2,2) = W(3,2), q even", n2, l2, t1, s1, t2, s2))
    print()

    n3, l3 = w33()
    rows.append(report("W(3,3), q odd -- no ovoid (Thas)", n3, l3, 11,
                       "frozen SAT certificate"))
    print("    tau_2                : OPEN in [110, 115]")
    print("       the 115 witness beats the product bound, so the upper end is")
    print("       NOT attained; the lower end is not known to be either")
    print()
    print("  The W(3,3) interval is not an artefact of the search. It is the")
    print("  missing ovoid, surfacing two levels above where it was proved")
    print("  missing. Closing it needs an argument that converts the defect")
    print("  into a statement about the product, not more search inside it.")

    ok = (rows[0]["multiplicative"] is True
          and rows[0]["hasOvoid"] is True
          and rows[1]["hasOvoid"] is False
          and rows[1]["intervalWidth"] == 11)

    if "--write" in sys.argv:
        out = os.path.join(ROOT, "data",
                           "tensor_multiplicativity_ovoid_defect.json")
        with open(out, "w") as fh:
            json.dump({
                "schema": "holotrade.tensor-multiplicativity.v1",
                "valid": ok,
                "theorem": ("a GQ of order (s,t) with an ovoid has "
                            "tau_2 = tau_1^2 = (st+1)^2; the bounds coincide "
                            "because tau_1 = st+1 makes the shadow lower bound "
                            "(st+1)*tau_1 equal to the product upper bound"),
                "widthFormula": "tau_1^2 - (st+1)*tau_1 = tau_1 * delta",
                "instances": rows,
                "w33Interval": [110, 115],
                "w33Open": True,
                "reading": ("the W(3,3) gap is the ovoid defect delta = 1 "
                            "multiplied by tau_1 = 11, not a search artefact"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(out, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
