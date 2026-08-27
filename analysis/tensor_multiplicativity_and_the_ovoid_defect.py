#!/usr/bin/env python3
"""
Why the generic depth-2 tensor blocking interval is controlled by the ovoid
defect, and why an ovoid is a sufficient condition for multiplicativity.

Five attacks on tau_2(W(3,3)) have failed to close [110, 115]. This file
stops attacking and asks a different question -- where does the generic
interval come from? -- and the answer is a one-line derivation with a clean
computational confirmation.

SETUP. Let Q be a generalized quadrangle of order (s,t): it has
(s+1)(st+1) points and (t+1)(st+1) lines, every line carries s+1 points, and
every point lies on t+1 lines. Write tau_1 for its blocking number -- the
fewest points meeting every line -- and tau_2 for the blocking number of the
product, the fewest cells of the point-by-point grid meeting every tile
L x M.

THE TWO BOUNDS. For a blocker X of the product and a line L, the shadow
S_L = union of X_p over p in L must itself block, so |S_L| >= tau_1. Summing
over all lines, and using that each point lies on t+1 of them,

    (t+1)|X|  =  sum over L of sum over p in L of |X_p|
              >= sum over L of |S_L|
              >= (t+1)(st+1) * tau_1,

so tau_2 >= (st+1) * tau_1. In the other direction B x B blocks every tile
for any line blocker B, so tau_2 <= tau_1^2. Hence

    (st+1) * tau_1  <=  tau_2  <=  tau_1^2,

and the width of that generic interval is exactly

    tau_1^2 - (st+1)*tau_1  =  tau_1 * (tau_1 - (st+1))  =  tau_1 * delta,

where delta = tau_1 - (st+1) is the BLOCKING OVOID DEFECT: how far the
blocking number sits above the ovoid size st+1.

THE PROVED IMPLICATION. A blocking set of size st+1 is precisely an ovoid.
Thus delta = 0 iff Q has an ovoid. When delta = 0 the two bounds coincide:

    Q has an ovoid   ==>   tau_2 = tau_1^2 = (st+1)^2.

So an ovoid is sufficient for depth-2 multiplicativity and makes the product
construction optimal. The converse does NOT follow from these bounds: when
delta > 0 they merely open an interval, and tau_2 could in principle still
sit at its upper endpoint. Nonmultiplicativity for a no-ovoid quadrangle needs
an additional strict upper construction (or some other argument).

THE TWO INSTANCES.

  GQ(2,2) = W(3,2). q even, so it HAS an ovoid: tau_1 = 5 = st+1, delta = 0.
  Both bounds give 25, and CP-SAT confirms tau_2 = 25 exactly, OPTIMAL, over
  the full 225-cell grid with no symmetry assumptions. Multiplicative.

  W(3,3). q odd, so by Thas it has NO ovoid. tau_1 = 11 > st+1 = 10, so
  delta = 1 and the generic interval has width 11 * 1 = 11 -- precisely the
  [110, 121] interval we started from. Separately, the certified 115-leaf
  blocker gives tau_2 <= 115 < 121 = tau_1^2, which proves W(3,3) itself is
  nonmultiplicative at depth 2. The exact value remains open in [110,115].

A SECOND, DISTINCT OVOID DEFICIT. W(3,3) has independence number alpha = 7,
where an ovoid would be an independent set of size st+1 = 10. That gives a
COCLIQUE OVOID DEFICIT 10 - 7 = 3. It witnesses the same absent object but it
is not numerically the same invariant as the blocking ovoid defect 11 - 10 =
1. Keeping these two defects separate matters.

NOVELTY, CALIBRATED. No literature on blocking numbers of PRODUCTS of
generalized quadrangles turned up. But the one-way implication above follows
immediately from two standard bounds, so it is recorded as a derivation that
explains the generic interval, not as a discovery.

The missing ovoid therefore explains why the elementary lower and product
upper bounds fail to collapse for W(3,3); it does not by itself decide where
tau_2 lies in that interval. The independent 115 construction is what proves
that the product upper endpoint is not attained for W(3,3).
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
    print("    blocking ovoid defect: %d   -> has an ovoid: %s"
          % (delta, delta == 0))
    print("    shadow lower (st+1)*tau_1 : %d" % lower)
    print("    product upper tau_1^2     : %d" % upper)
    print("    interval width tau_1*delta: %d" % (tau1 * delta))
    assert upper - lower == tau1 * delta, "the width formula must close"
    if tau2 is not None:
        print("    tau_2                : %d   (%s)" % (tau2, tau2_status))
        if delta == 0:
            print("    => OVOID SUFFICES: bounds collapse and tau_2 = tau_1^2")
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
    print("MULTIPLICATIVITY BOUND COLLAPSE AND THE OVOID DEFECT")
    print("=" * 72)
    print("  (st+1)*tau_1 <= tau_2 <= tau_1^2, an interval of width")
    print("  tau_1*(tau_1 - (st+1)) = tau_1 * delta. delta = 0 exactly when")
    print("  the quadrangle has an ovoid, and then the bounds coincide.")
    print("  The converse is not implied when delta > 0.")
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
    print("       the 115 witness gives tau_2 < 121 = tau_1^2, hence")
    print("       W(3,3) is nonmultiplicative; exact tau_2 remains open")
    print()
    print("  The missing ovoid explains why the elementary bounds do not")
    print("  collapse. It does not prove the converse. The separate 115")
    print("  construction is what proves nonmultiplicativity for W(3,3).")

    ok = (rows[0]["multiplicative"] is True
          and rows[0]["hasOvoid"] is True
          and rows[1]["hasOvoid"] is False
          and rows[1]["intervalWidth"] == 11
          and 115 < rows[1]["productUpper"])

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
                "converseProved": False,
                "converseBoundary": ("delta > 0 opens a gap between the generic "
                                     "bounds but does not by itself imply "
                                     "tau_2 < tau_1^2"),
                "widthFormula": "tau_1^2 - (st+1)*tau_1 = tau_1 * delta",
                "instances": rows,
                "w33Interval": [110, 115],
                "w33Open": True,
                "w33Nonmultiplicative": True,
                "w33NonmultiplicativityReason": ("the explicit 115-leaf blocker "
                                                 "gives tau_2 <= 115 < 121 = tau_1^2"),
                "w33CocliqueOvoidDeficit": 3,
                "defectBoundary": ("blocking ovoid defect is 11-10=1; coclique "
                                   "ovoid deficit is 10-7=3; they witness the "
                                   "same absent ovoid but are distinct invariants"),
                "reading": ("the W(3,3) generic-bound gap is the blocking ovoid "
                            "defect delta = 1 multiplied by tau_1 = 11; the "
                            "strict 115 construction, not delta>0 alone, proves "
                            "nonmultiplicativity"),
                "novelty": ("no literature on blocking numbers of products of "
                            "generalized quadrangles turned up, but the proved "
                            "one-way implication is a one-line consequence of "
                            "two standard bounds; recorded as a derivation, not "
                            "as a discovery"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(out, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
