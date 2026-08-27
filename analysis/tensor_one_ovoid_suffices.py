#!/usr/bin/env python3
"""
One ovoid suffices -- and the dual product of W(3,3) is exactly 110.

Ten attacks on tau_2(W(3,3)) failed to close [110, 115]. This file stops
attacking that object and studies its NEIGHBOURS instead: products of two
different quadrangles, where the answer can actually be computed. The pattern
that comes out explains the open case completely, and closes three others.

THE THEOREM.  For generalized quadrangles Q1, Q2 of orders (s1,t1), (s2,t2),
let tau_i be the blocking number of Q_i and let tau(Q1 x Q2) be the fewest
cells of the point-by-point grid meeting every tile L x M.

Running the shadow double-count over the FIRST axis: for each line L of Q1
the shadow in Q2's points must block Q2, so it has at least tau_2 points;
summing over Q1's (t1+1)(s1t1+1) lines and dividing by the t1+1 lines through
each point,

    tau(Q1 x Q2)  >=  (s1 t1 + 1) * tau_2,

and symmetrically >= (s2 t2 + 1) * tau_1. The product B1 x B2 of blockers
gives tau(Q1 x Q2) <= tau_1 * tau_2.

Now suppose Q1 has an OVOID. A blocking set of size s1t1+1 is exactly an
ovoid, so tau_1 = s1t1 + 1, and the first lower bound reads tau_1 * tau_2 --
which is the upper bound. The two MEET:

    if EITHER factor has an ovoid, tau(Q1 x Q2) = tau_1 * tau_2.

One ovoid suffices. This is strictly stronger than the earlier statement
about a single quadrangle squared, and it is what makes the open case
diagnosable rather than merely stubborn.

FOUR INSTANCES, three closed and one open, all on comparable objects.

  W(3,2) x W(3,2)    both have ovoids      tau = 25   solved exactly
  W(3,2) x W(3,3)    one has an ovoid      tau = 55   bound meets witness
  W(3,3) x Q(4,3)    one has an ovoid      tau = 110  bound meets witness
  W(3,3) x W(3,3)    NEITHER has one       [110, 115] OPEN

THE THIRD ROW IS THE POINT.  W(3,3) has no ovoid -- that is Thas's theorem
for odd q, and it is why tau_1 = 11 rather than 10. But W(3,3) DOES have
spreads: 36 of them, ten pairwise disjoint lines covering all forty points.
A spread of W(3,3) is precisely an ovoid of the dual quadrangle Q(4,3). So
Q(4,3) has an ovoid, tau(Q(4,3)) = 10, and the theorem applies.

The two products then sit on the SAME 40 x 40 grid, with 1600 tiles of 16
leaves each, differing only in which tiles:

    W(3,3) x W(3,3):  tiles are  line x line
    W(3,3) x Q(4,3):  tiles are  line x pencil

and the answers are [110, 115] open versus 110 exactly. Swapping one factor
for its dual closes the problem outright, because duality converts "no ovoid"
into "has an ovoid". That is a precise measurement of what the defect costs:
not a vague obstruction, but the difference between an interval of width five
and a closed value, on two problems of identical size and shape.

The witness for the dual product is constructed and verified here leaf by
leaf against all 1600 tiles: an eleven-point blocker of W(3,3) crossed with a
ten-line spread of W(3,3), 110 leaves.
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
    """W(3,2) = GQ(2,2), built from scratch."""
    def form(u, v):
        return (u[0] * v[1] + u[1] * v[0] + u[2] * v[3] + u[3] * v[2]) % 2
    pts = [v for v in itertools.product([0, 1], repeat=4) if any(v)]
    idx = {v: i for i, v in enumerate(pts)}
    lines = set()
    for a, b in itertools.combinations(pts, 2):
        if form(a, b) == 0:
            c = tuple(a[i] ^ b[i] for i in range(4))
            lines.add(tuple(sorted(idx[x] for x in (a, b, c))))
    return len(pts), [list(x) for x in sorted(lines)]


def w33():
    out = subprocess.run(
        ["node", "-e",
         "global.window=global;const S=require('./js/substrate.js');"
         "const W=require('./js/w33-scheduler.js');"
         "const T=require('./js/tensor-sharding.js');"
         "process.stdout.write(JSON.stringify({"
         "lines:S.LINES.map(l=>[...l].sort((a,b)=>a-b)),"
         "spreads:W.spreads(),blocker:[...T.BLOCKER]}));"],
        cwd=ROOT, capture_output=True, text=True)
    if out.returncode:
        sys.exit("node failed: " + out.stderr[:400])
    d = json.loads(out.stdout)
    return 40, d["lines"], d["spreads"], d["blocker"]


def params(n, lines):
    s = len(lines[0]) - 1
    t = sum(1 for L in lines if 0 in L) - 1
    return s, t, s * t + 1


def blocking_number(n, lines, seconds=40):
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


def product_bounds(p1, tau1, p2, tau2):
    """(lower from each axis, product upper)."""
    _, _, o1 = p1
    _, _, o2 = p2
    return max(o1 * tau2, o2 * tau1), tau1 * tau2


def main():
    rows = []

    # --- W(3,2), which has an ovoid -----------------------------------
    n2, L2 = w32()
    p2 = params(n2, L2)
    t2, st2 = blocking_number(n2, L2)

    # --- W(3,3), which does not ---------------------------------------
    n3, L3, spreads, B = w33()
    p3 = params(n3, L3)
    t3 = 11                                   # frozen SAT certificate

    print("ONE OVOID SUFFICES")
    print("=" * 70)
    print("  W(3,2): order %s, ovoid size %d, tau = %d (%s) -> has an ovoid: %s"
          % (p2[:2], p2[2], t2, st2, t2 == p2[2]))
    print("  W(3,3): order %s, ovoid size %d, tau = %d (certificate) -> "
          "has an ovoid: %s" % (p3[:2], p3[2], t3, t3 == p3[2]))
    print()

    # Q(4,3) is the dual of W(3,3): its points are W(3,3)'s lines and its
    # ovoids are W(3,3)'s SPREADS, which exist even though ovoids do not.
    sp = spreads[0]
    covered = set()
    for li in sp:
        covered |= set(L3[li])
    spread_ok = len(sp) == 10 and len(covered) == 40
    tQ = 10
    print("  Q(4,3) = dual of W(3,3): an ovoid of it is a SPREAD of W(3,3).")
    print("    spreads available: %d;  one has %d disjoint lines covering %d "
          "points: %s" % (len(spreads), len(sp), len(covered), spread_ok))
    print("    so tau(Q(4,3)) = %d = st+1 -> Q(4,3) HAS an ovoid" % tQ)
    print()

    print("  %-20s %-12s %-10s %-10s %s"
          % ("product", "lower", "upper", "tau", "status"))
    for name, pa, ta, pb, tb in [
            ("W(3,2) x W(3,2)", p2, t2, p2, t2),
            ("W(3,2) x W(3,3)", p2, t2, p3, t3),
            ("W(3,3) x Q(4,3)", p3, t3, (3, 3, 10), tQ),
            ("W(3,3) x W(3,3)", p3, t3, p3, t3)]:
        lo, up = product_bounds(pa, ta, pb, tb)
        closed = lo == up
        rows.append({"product": name, "lower": lo, "upper": up,
                     "multiplicative": closed,
                     "tau": up if closed else None})
        print("  %-20s %-12d %-10d %-10s %s"
              % (name, lo, up, up if closed else "?",
                 "CLOSED, multiplicative" if closed else "OPEN"))
    print()

    # verify the dual-product witness leaf by leaf
    X = {(p, M) for p in B for M in sp}
    thru = [[li for li, L in enumerate(L3) if r in L] for r in range(40)]
    unblocked = 0
    for L in L3:
        for r in range(40):
            if not any((p, M) in X for p in L for M in thru[r]):
                unblocked += 1
    print("  DUAL-PRODUCT WITNESS: (11-point blocker) x (10-line spread)")
    print("    size %d, tiles checked 1600, unblocked %d -> blocks all: %s"
          % (len(X), unblocked, unblocked == 0))
    print()
    print("  THE CONTRAST, on the same 40x40 grid with 1600 tiles of 16 leaves:")
    print("    W(3,3) x W(3,3)  tiles line x line    tau in [110, 115]  OPEN")
    print("    W(3,3) x Q(4,3)  tiles line x pencil  tau = 110          CLOSED")
    print()
    print("  Swapping one factor for its dual closes the problem, because")
    print("  duality turns 'no ovoid' into 'has an ovoid'. That is what the")
    print("  defect costs, measured on two problems of identical size.")

    ok = (t2 == p2[2] and t3 != p3[2] and spread_ok and unblocked == 0
          and len(X) == 110
          and rows[0]["multiplicative"] and rows[1]["multiplicative"]
          and rows[2]["multiplicative"] and not rows[3]["multiplicative"])

    if "--write" in sys.argv:
        out = os.path.join(ROOT, "data", "tensor_one_ovoid_suffices.json")
        with open(out, "w") as fh:
            json.dump({
                "schema": "holotrade.tensor-one-ovoid-suffices.v1",
                "valid": ok,
                "theorem": ("if EITHER factor of a product of generalized "
                            "quadrangles has an ovoid, the shadow lower bound "
                            "run over that axis equals the product upper bound, "
                            "so tau(Q1 x Q2) = tau_1 * tau_2"),
                "strongerThan": ("the earlier single-quadrangle statement: one "
                                 "ovoid suffices, not two"),
                "instances": rows,
                "w33HasNoOvoid": True,
                "w33HasSpreads": len(spreads),
                "dualOvoidIsASpread": ("an ovoid of Q(4,3) is a spread of "
                                       "W(3,3); spreads exist, ovoids do not"),
                "dualProduct": {
                    "tau": 110,
                    "witness": "11-point blocker x 10-line spread",
                    "witnessSize": len(X),
                    "tilesChecked": 1600,
                    "unblocked": unblocked,
                    "proof": "shadow count gives >= 110 and the witness attains it",
                },
                "contrast": ("same 40x40 grid, same 1600 tiles of 16 leaves: "
                             "line x line is open in [110,115], line x pencil "
                             "is exactly 110"),
                "boundary": ("this closes three products and explains the "
                             "fourth; it does NOT decide tau_2(W(3,3)), which "
                             "stays open in [110, 115]"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(out, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
