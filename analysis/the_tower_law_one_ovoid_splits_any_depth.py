#!/usr/bin/env python3
"""
One ovoid does not merely close a product -- it SPLITS a tower, at any depth.
So tower height is free, and the composition tax is paid exactly once.

WHAT IS ALREADY OWNED.  tensor_one_ovoid_suffices.py proves the depth-2
statement: for generalized quadrangles Q1, Q2, the shadow double-count gives
tau(Q1 x Q2) >= (s1 t1 + 1) tau_2 and the product of blockers gives
tau <= tau_1 tau_2, so if EITHER factor has an ovoid the two bounds meet and
tau(Q1 x Q2) = tau_1 tau_2. It computes the four instances -- W(3,2)^2 = 25,
W(3,2) x W(3,3) = 55, W(3,3) x Q(4,3) = 110, and W(3,3)^2 open in [110, 115].
All of that is that file's.

WHAT IS NEW HERE is that the same argument never used the second factor's
being a quadrangle at all. Run the shadow over the first axis only:

    THEOREM (splitting).  If Q1 has an ovoid then, for an ARBITRARY product R,
        tau(Q1 x R) = tau_1 * tau(R).

    Proof. Upper: B1 x X_R blocks, where B1 is a minimum blocker of Q1 and
    X_R an optimum for R. Lower: for each line L of Q1 the shadow of X in R
    must block R, so it has at least tau(R) leaves; summing over Q1's
    (t1+1)(s1 t1 + 1) lines and dividing by the t1+1 lines through a point
    gives |X| >= (s1 t1 + 1) tau(R), and an ovoid makes tau_1 = s1 t1 + 1. []

That peels ovoid-bearing factors off ONE AT A TIME, to any depth, leaving
only the ovoid-free ones. Verified at depth 3 below by explicit construction:
B x O x O is 1,100 leaves and blocks all 64,000 tiles of W x Q x Q, while the
shadow gives 10 * tau(W x Q) = 1,100 -- so that tower is exact, not bounded.

THE TOWER LAW.  Q(4,3) is the dual of W(3,3); its ovoids are W(3,3)'s
spreads, of which there are 36, so tau(Q) = 10, while W(3,3) has no ovoid at
all (Thas, odd q) and tau(W) = 11. Peeling every Q gives

        tau(W^k x Q^m)  =  10^m * tau(W^k)

    k = 0     10^m                       free
    k = 1     11 * 10^m                  free, exact
    k = 2     [111, 115] * 10^m          the tax, open
    k >= 2    open

THREE CONSEQUENCES, and the middle one corrects something I said earlier.

  1. THE TAX IS PAID ONCE, NOT PER TIER. Every ovoid-bearing tier multiplies
     the cost by exactly 10 and adds nothing. Tower HEIGHT is free; only the
     ovoid-free COUNT is expensive. That is the precise form of the
     asymptotic statement lim tau(H^n)^(1/n) = 10.

  2. IT IS A QUOTA, NOT AN ALTERNATION. I previously suggested the tower
     should alternate machine and dual. That is wrong: the product is
     commutative, so W x Q x W and W x W x Q cost the same. Arrangement is
     irrelevant. What is budgeted is how MANY factors lack an ovoid, and the
     budget is one.

  3. tau_2 PROPAGATES VERBATIM. The open interval [111, 115] is not a
     depth-2 curiosity: it is the exact cost of tau(W^2 x Q^m) for every m,
     divided by 10^m. Closing tau_2 closes an infinite family of tower costs
     at once.

THE OPERATIONAL READING.  An ovoid of Q(4,3) is a spread of W(3,3): a
partition of the 40 Pauli classes into 10 disjoint measurement contexts. An
ovoid of W(3,3) would be 10 pairwise NON-commuting classes, and none exists
for odd q. So the free side is the side that admits a PARTITION INTO
CONTEXTS, and the taxed side is the raw context geometry. Composing machines
through their spreads is free; composing them through their lines is not.
Route composition through spreads.

SCOPE.  The splitting theorem's proof is the depth-2 argument with the second
factor left arbitrary; the depth-3 instance is verified leaf by leaf against
all 64,000 tiles. tau(W^k) for k >= 2 is untouched, and tau_2 stays open in
[111, 115]. Nothing here is a claim about physical hardware.
"""

import itertools
import json
import os
import sys

ROOT = r"C:\Repos\Holotrade"
Q = 3
N = 40


def main():
    from ortools.sat.python import cp_model

    def nm(v):
        i = next(k for k, x in enumerate(v) if x % Q)
        z = pow(v[i] % Q, -1, Q)
        return tuple((z * x) % Q for x in v)

    def form(u, v):
        return (u[0] * v[1] - u[1] * v[0] + u[2] * v[3] - u[3] * v[2]) % Q

    pts = sorted({nm(v) for v in itertools.product(range(Q), repeat=4)
                  if any(v)})
    idx = {v: i for i, v in enumerate(pts)}
    W_lines = set()
    for a, b in itertools.combinations(range(N), 2):
        if form(pts[a], pts[b]):
            continue
        S = set()
        for x in range(Q):
            for y in range(Q):
                if x == y == 0:
                    continue
                S.add(idx[nm(tuple((x * pts[a][k] + y * pts[b][k]) % Q
                                   for k in range(4)))])
        if len(S) == 4:
            W_lines.add(tuple(sorted(S)))
    W_lines = sorted(W_lines)
    Q_lines = [tuple(sorted(li for li, L in enumerate(W_lines) if p in L))
               for p in range(N)]

    print("THE TOWER LAW: ONE OVOID SPLITS ANY DEPTH")
    print("=" * 72)
    print("  W(3,3): %d points, %d lines. Q(4,3) = its dual: %d points, %d"
          % (N, len(W_lines), len(W_lines), len(Q_lines)))
    print("  lines, all of size %s." % sorted({len(L) for L in Q_lines}))

    def tau1(npts, lines):
        m = cp_model.CpModel()
        x = [m.NewBoolVar("") for _ in range(npts)]
        for L in lines:
            m.AddBoolOr([x[p] for p in L])
        m.Minimize(sum(x))
        s = cp_model.CpSolver()
        s.parameters.max_time_in_seconds = 120
        st = s.Solve(m)
        return (sum(1 for p in range(npts) if s.Value(x[p])),
                s.StatusName(st))

    tW, sW = tau1(N, W_lines)
    tQ, sQ = tau1(len(W_lines), Q_lines)
    print("  tau_1(W) = %d (%s) ; tau_1(Q) = %d (%s)" % (tW, sW, tQ, sQ))
    print("     Q's ovoids are W's spreads, so tau_1(Q) = st+1 = 10: %s"
          % (tQ == 10))
    print("     W has no ovoid (Thas, odd q), so tau_1(W) = 11 > 10: %s"
          % (tW == 11))
    print()

    m = cp_model.CpModel()
    xb = [m.NewBoolVar("") for _ in range(N)]
    for L in W_lines:
        m.AddBoolOr([xb[p] for p in L])
    m.Add(sum(xb) == 11)
    s = cp_model.CpSolver()
    s.Solve(m)
    B = [p for p in range(N) if s.Value(xb[p])]
    m = cp_model.CpModel()
    xo = [m.NewBoolVar("") for _ in range(len(W_lines))]
    for L in Q_lines:
        m.AddExactlyOne([xo[p] for p in L])
    s = cp_model.CpSolver()
    s.Solve(m)
    O = [p for p in range(len(W_lines)) if s.Value(xo[p])]

    def blocks3(X, l1, l2, l3):
        S = set(X)
        for A in l1:
            for Bl in l2:
                for C in l3:
                    if not any((a, b, c) in S
                               for a in A for b in Bl for c in C):
                        return False
        return True

    X = {(a, b, c) for a in B for b in O for c in O}
    ok = blocks3(X, W_lines, Q_lines, Q_lines)
    X3 = {(a, b, c) for a in O for b in O for c in O}
    ok3 = blocks3(X3, Q_lines, Q_lines, Q_lines)
    print("  DEPTH 3, verified leaf by leaf against all %d tiles:"
          % (len(W_lines) * len(Q_lines) * len(Q_lines)))
    print("     B x O x O = %d leaves, blocks W x Q x Q: %s" % (len(X), ok))
    print("     shadow gives 10 * tau(W x Q) = 10 * 110 = 1100")
    print("     => tau(W x Q x Q) = 1100 EXACTLY: %s"
          % (ok and len(X) == 1100))
    print("     O x O x O = %d leaves, blocks Q x Q x Q: %s" % (len(X3), ok3))
    print()
    print("  THE TOWER LAW   tau(W^k x Q^m) = 10^m * tau(W^k)")
    print("     k=0  10^m                free")
    print("     k=1  11 * 10^m           free, exact")
    print("     k=2  [111,115] * 10^m    the tax, open")
    print()
    print("  1. The tax is paid ONCE, not per tier -- height is free.")
    print("  2. It is a QUOTA, not an alternation: the product is")
    print("     commutative, so arrangement is irrelevant. What is budgeted")
    print("     is how many factors lack an ovoid, and the budget is one.")
    print("  3. tau_2's interval propagates verbatim: [111,115] is the exact")
    print("     cost of tau(W^2 x Q^m) for every m, divided by 10^m.")
    print()
    print("  Operationally: an ovoid of Q is a SPREAD of W -- a partition of")
    print("  the 40 Pauli classes into 10 disjoint contexts. The free side is")
    print("  the side that admits a partition. Route composition through")
    print("  spreads, not through lines.")

    ok_all = (tW == 11 and tQ == 10 and sW == "OPTIMAL" and sQ == "OPTIMAL"
              and ok and ok3 and len(X) == 1100 and len(X3) == 1000)

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data",
                         "the_tower_law_one_ovoid_splits_any_depth.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.tower-law-one-ovoid-splits.v1",
                "valid": bool(ok_all),
                "priorArt": {
                    "file": "tensor_one_ovoid_suffices.py",
                    "owns": ("the depth-2 theorem -- if either factor has an "
                             "ovoid then tau(Q1 x Q2) = tau_1 tau_2 -- and the "
                             "four instances 25, 55, 110, and [110,115] open"),
                },
                "whatIsNew": ("the same shadow argument never used the second "
                              "factor's being a quadrangle, so it SPLITS a "
                              "tower of arbitrary depth, not just a product"),
                "splittingTheorem": {
                    "statement": ("if Q1 has an ovoid then tau(Q1 x R) = "
                                  "tau_1 * tau(R) for arbitrary R"),
                    "upper": "B1 x X_R blocks",
                    "lower": ("each line of Q1 has a shadow in R that must "
                              "block R, so |X| >= (s1 t1 + 1) tau(R), and an "
                              "ovoid makes tau_1 = s1 t1 + 1"),
                    "consequence": ("ovoid-bearing factors peel off one at a "
                                    "time, to any depth"),
                },
                "quadrangles": {
                    "tau1W": tW, "tau1WStatus": sW,
                    "tau1Q": tQ, "tau1QStatus": sQ,
                    "QIsDualOfW": True,
                    "QOvoidsAreWSpreads": True,
                    "WHasNoOvoid": "Thas, odd q",
                },
                "depth3Verified": {
                    "tiles": len(W_lines) * len(Q_lines) * len(Q_lines),
                    "BxOxO": len(X), "blocksWQQ": ok,
                    "shadow": 1100,
                    "tauWQQExact": bool(ok and len(X) == 1100),
                    "OxOxO": len(X3), "blocksQQQ": ok3,
                },
                "towerLaw": {
                    "formula": "tau(W^k x Q^m) = 10^m * tau(W^k)",
                    "k0": "10^m, free",
                    "k1": "11 * 10^m, free and exact",
                    "k2": "[111,115] * 10^m, the tax, open",
                },
                "consequences": {
                    "taxPaidOnce": ("every ovoid-bearing tier multiplies by "
                                    "exactly 10 and adds nothing, so tower "
                                    "HEIGHT is free and only the ovoid-free "
                                    "COUNT is expensive"),
                    "quotaNotAlternation": ("the product is commutative, so "
                                            "W x Q x W and W x W x Q cost the "
                                            "same; arrangement is irrelevant "
                                            "and the budget is one ovoid-free "
                                            "factor -- this corrects an "
                                            "earlier suggestion that the tower "
                                            "should alternate"),
                    "tau2Propagates": ("[111,115] is the exact cost of "
                                       "tau(W^2 x Q^m) for every m divided by "
                                       "10^m, so closing tau_2 closes an "
                                       "infinite family at once"),
                },
                "operationalReading": ("an ovoid of Q(4,3) is a spread of "
                                       "W(3,3), a partition of the 40 Pauli "
                                       "classes into 10 disjoint measurement "
                                       "contexts; an ovoid of W(3,3) would be "
                                       "10 pairwise NON-commuting classes and "
                                       "none exists for odd q. The free side "
                                       "is the side admitting a partition, so "
                                       "compose through spreads, not lines"),
                "boundary": ("the splitting proof is the depth-2 argument with "
                             "the second factor left arbitrary; the depth-3 "
                             "instance is verified leaf by leaf against all "
                             "64,000 tiles. tau(W^k) for k >= 2 is untouched "
                             "and tau_2 stays open in [111, 115]. Nothing here "
                             "is a claim about physical hardware"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
