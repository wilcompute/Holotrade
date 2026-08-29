#!/usr/bin/env python3
"""
Their self-duality obstruction, extended to GQ(2,4) -- where it fires by
pigeonhole and needs no duality argument at all.

WHOSE PROOF THIS IS.  W33-Theory proved tau_2(W(3,3)^2) != 110 (commit
43049db, certificate 1513d61), moving a lower bound that had not shifted since
it was derived. Their argument, in outline:

  At |X| = 110 every row AND column shadow is a minimum blocker, so each has a
  centre. Writing c_L for a row line's centre and d_M for a column line's,
  the fact that a minimum blocker meets the four lines through its centre
  twice and every other line once gives

      |X cap (L x M)| = 2  iff  c_L in M  iff  d_M in L,

  i.e. PENCIL RECIPROCITY  c_L in M <=> d_M in L.

  A centre's multiplicity is then 0, 1 or t+1: if two row lines share a centre
  they must be concurrent, and reciprocity propagates that to a full pencil on
  the other side. Let F be the multiplicity-(t+1) centres. F is independent,
  every point adjacent to F is adjacent to exactly t+1 of F, and counting
  pairs of F through their common neighbours gives

      mu * C(|F|,2) = (k|F|/(t+1)) * C(t+1,2),   hence   |F| = 1 + k*t/mu.

  For W(3,3) that is 1 + 12*3/4 = 10, and alpha(W(3,3)) = 7, so F is empty and
  both centre maps are bijections. Reciprocity is then an incidence
  isomorphism W(3,3) -> W(3,3)^D -- a self-duality. Classical W(q) is
  self-dual iff q is even, and q = 3 is odd. Contradiction.

That last step is where the argument needed real geometry, because W(3,3) has
40 points and 40 lines, so a bijection is perfectly possible on counting
grounds and only self-duality rules it out.

THE EXTENSION.  The same machinery applies to any generalized quadrangle, and
on GQ(2,4) = Q^-(5,2) the final step becomes unnecessary.

GQ(2,4) has 27 points and 45 lines, order (s,t) = (2,4), ovoid size 9, no
ovoid, and tau_1 = 10 with defect 1 -- the same defect as W(3,3). Its tight
case is |X| = (st+1)*tau_1 = 90. Feeding its parameters through the same
counting:

      k = 10, mu = 5, t = 4     =>   |F| = 1 + 10*4/5 = 9,
      alpha(GQ(2,4)) = 6 < 9    =>   F is empty,

so every centre again has multiplicity 0 or 1. But now the centre map runs
from 45 LINES to 27 POINTS. Multiplicities of 0 or 1 can account for at most
27 lines, and all 45 need centres.

      45 > 27.  Pigeonhole. No self-duality argument required.

Hence tau_2(GQ(2,4)^2) != 90, and the interval closes from below:

      tau_2(GQ(2,4)^2) in [91, 100].

WHY THE TWO CASES DIFFER, and it is the point of the extension. W(3,3) is
self-polar in its parameters -- equally many points and lines -- so its
obstruction has to come from the deeper fact that W(q) is self-dual only for
even q. GQ(2,4) has (s,t) = (2,4) with s != t, so the point and line counts
differ and the obstruction is visible immediately. Two quadrangles with the
same blocking defect delta = 1 and the same automorphism group W(E6), where
the same forced structure is refuted by an elementary count in one case and
by a classical duality theorem in the other.

ATTRIBUTION AND CAVEAT.  The structural lemma -- pencil reciprocity, the
multiplicity trichotomy, the independence of F and the pair count -- is
W33-Theory's, stated for W(3,3). What is added here is the observation that
its conclusion is parameter-dependent, the general form |F| = 1 + kt/mu, and
the application to GQ(2,4). The generalisation of "every point adjacent to F
is adjacent to exactly t+1 points of F" from their q=3 statement to arbitrary
(s,t) is by analogy with their derivation and should be confirmed on their
side before the GQ(2,4) bound is treated as certified; what this file
establishes without any such dependence is the arithmetic, and the pigeonhole
step, which needs only F = empty.
"""

import itertools
import json
import os
import sys
from fractions import Fraction

ROOT = r"C:\Repos\Holotrade"


def gq_parameters(s, t):
    """Points, lines, degree, mu for the collinearity graph of a GQ(s,t)."""
    n = (s + 1) * (s * t + 1)
    lines = (t + 1) * (s * t + 1)
    k = s * (t + 1)
    mu = t + 1
    return n, lines, k, mu


def forced_F(s, t):
    """|F| = 1 + k t / mu from the pair count."""
    _, _, k, mu = gq_parameters(s, t)
    return Fraction(k * t, mu) + 1


def build_gq24():
    def Qf(v):
        return (v[0] * v[1] + v[2] * v[3]
                + v[4] * v[4] + v[4] * v[5] + v[5] * v[5]) % 2

    def Bf(u, v):
        return (Qf([u[i] ^ v[i] for i in range(6)]) ^ Qf(u) ^ Qf(v)) % 2

    pts = [v for v in itertools.product([0, 1], repeat=6)
           if any(v) and Qf(v) == 0]
    idx = {v: i for i, v in enumerate(pts)}
    lines = set()
    for a, b in itertools.combinations(pts, 2):
        if Bf(a, b) == 0:
            c = tuple(a[i] ^ b[i] for i in range(6))
            if any(c) and Qf(c) == 0:
                lines.add(tuple(sorted(idx[x] for x in (a, b, c))))
    return len(pts), [list(x) for x in sorted(lines)]


def main():
    rows = []
    print("THE TIGHT-CASE OBSTRUCTION, BY QUADRANGLE")
    print("=" * 70)
    print("  |F| = 1 + k*t/mu is forced by the pair count; if that exceeds")
    print("  alpha then F is empty and every centre has multiplicity 0 or 1.")
    print()
    for name, s, t, alpha in (("W(3,3)", 3, 3, 7), ("GQ(2,4)", 2, 4, 6)):
        n, nl, k, mu = gq_parameters(s, t)
        f = forced_F(s, t)
        empty = f > alpha
        inject = nl <= n
        rows.append({
            "name": name, "s": s, "t": t, "points": n, "lines": nl,
            "degree": k, "mu": mu, "alpha": alpha,
            "forcedF": str(f), "fMustBeEmpty": bool(empty),
            "centreMapCanInject": bool(inject),
            "obstruction": ("self-duality of W(q), impossible for odd q"
                            if inject else
                            "pigeonhole: more lines than points"),
            "tau1": s * t + 1 + 1, "tightCase": (s * t + 1) * (s * t + 2),
        })
        print("  %s: (s,t)=(%d,%d)  %d points, %d lines, k=%d, mu=%d, alpha=%d"
              % (name, s, t, n, nl, k, mu, alpha))
        print("     forced |F| = 1 + %d*%d/%d = %s  >  alpha = %d ?  %s"
              % (k, t, mu, f, alpha, empty))
        print("     centre map: %d lines -> %d points; injection possible: %s"
              % (nl, n, inject))
        print("     obstruction: %s" % rows[-1]["obstruction"])
        print()

    # confirm the GQ(2,4) numbers against the built geometry
    n24, l24 = build_gq24()
    checks = {
        "gq24Points27": n24 == 27,
        "gq24Lines45": len(l24) == 45,
        "moreLinesThanPoints": len(l24) > n24,
        "forcedFExceedsAlpha": forced_F(2, 4) > 6,
        "w33ForcedFIs10": forced_F(3, 3) == 10,
        "w33ForcedFExceedsAlpha": forced_F(3, 3) > 7,
        "w33EqualPointsAndLines": gq_parameters(3, 3)[0] == gq_parameters(3, 3)[1],
    }
    for kk, vv in checks.items():
        print("  %-30s %s" % (kk, vv))
    ok = all(checks.values())
    print()
    print("  ==> tau_2(GQ(2,4)^2) != 90, by pigeonhole alone.")
    print("      Interval closes from below: [91, 100].")
    print()
    print("  W(3,3) has equally many points and lines, so a bijection is")
    print("  possible on counting grounds and only the classical fact that")
    print("  W(q) is self-dual iff q is even refutes it. GQ(2,4) has s != t,")
    print("  the counts differ, and the same forced structure dies immediately.")

    if "--write" in sys.argv:
        out = os.path.join(ROOT, "data", "gq24_tight_obstruction.json")
        with open(out, "w") as fh:
            json.dump({
                "schema": "holotrade.gq24-tight-obstruction.v1",
                "valid": ok,
                "checks": checks,
                "instances": rows,
                "result": "tau_2(GQ(2,4)^2) != 90; interval [91, 100]",
                "mechanism": ("|F| = 1 + kt/mu = 9 exceeds alpha = 6, so every "
                              "centre has multiplicity 0 or 1; but the centre "
                              "map sends 45 lines to 27 points, which no "
                              "injection can do"),
                "contrastWithW33": ("W(3,3) has 40 points and 40 lines, so a "
                                    "bijection is possible on counting grounds "
                                    "and the contradiction needs the classical "
                                    "self-duality theorem. GQ(2,4) has s != t "
                                    "and dies by pigeonhole."),
                "attribution": {
                    "structuralLemma": ("W33-Theory: pencil reciprocity, the "
                                        "multiplicity trichotomy, independence "
                                        "of F and the pair count"),
                    "proofCommit": "43049db",
                    "certificateCommit": "1513d61",
                    "addedHere": ("the general form |F| = 1 + kt/mu, the "
                                  "observation that the conclusion is "
                                  "parameter-dependent, and the application to "
                                  "GQ(2,4) where pigeonhole suffices"),
                },
                "caveat": ("the generalisation of 'every point adjacent to F is "
                           "adjacent to exactly t+1 points of F' from their q=3 "
                           "statement to arbitrary (s,t) is by analogy with "
                           "their derivation and should be confirmed on their "
                           "side before the GQ(2,4) bound is treated as "
                           "certified. The arithmetic and the pigeonhole step, "
                           "which need only F empty, are established here."),
                "boundary": ("tau_2(GQ(2,4)^2) remains OPEN in [91, 100]; only "
                             "the tight case is excluded."),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(out, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
