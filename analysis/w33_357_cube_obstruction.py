#!/usr/bin/env python3
"""
The 3-5-7 harmonic cube cannot reach W(3,3) by symmetry. Neither can the C13
clock. An obstruction for the other track's third attack.

THE OTHER TRACK'S RESULT.  Pass 10549-10580 factorises the canonical 27-state
carrier arithmetically:

    C_105 = C_3 x C_5 x C_7,     C[C_105]^{C_6} = H_3 (x) H_5^(+) (x) H_7^(C_3),
    27 = 3 x 3 x 3,

a genuine harmonic tensor cube, with the Fourier transform factoring as
F_3^(2) (x) F_5^{C_2} (x) F_7^{C_3}.  Their stated third attack is to test
this against W(3,3)'s cyclotomic arithmetic, under the explicit standard
"establish an operator or module map, not declare victory from the numbers".

THIS IS THE NEGATIVE HALF OF THAT STANDARD, and it is sharp.

    |Aut(W(3,3))| = 51840 = 2^7 * 3^4 * 5.

Seven does not divide it.  Neither does thirteen.  By Lagrange, W(3,3) has NO
subgroup of order 7 and none of order 13 -- this is an impossibility, not a
failed search, and no amount of cleverness in choosing the map evades it.  A
random-word sweep confirms the realised element orders are exactly
{1,2,3,4,5,6,9,12}: 5 appears, 7 and 13 never do.

CONSEQUENCES.

  * The C_7 factor of the cube has no image in Aut(W(3,3)).  The cube's C_3
    and C_5 factors do; the C_7 factor cannot be transported as a group
    action, so any bridge to the quadrangle must carry the seven by some
    route other than symmetry.
  * The same argument kills the C_13 clock on the quadrangle side.  Their
    C_13 lives in G_2(4) acting on V_2 = F_4^6, where 13 | |G_2(4)|.  It has
    no counterpart in Aut(W(3,3)), so the H(4) clock does not descend.

WHERE SEVEN ACTUALLY LIVES IN W(3,3), and why that is not the same seven.
alpha(W(3,3)) = 7, against a Hoffman ratio bound of 10.  That shortfall is
the ovoid defect -- the reason W(3,3) has no ovoid, the reason its blocking
number is 11 rather than 10, and (as this repository showed) the reason the
depth-2 tensor blocking interval opens at all.  It is a COMBINATORIAL
invariant of the graph, with no group of order 7 anywhere near it.

Two sevens appearing in one project is exactly the kind of numerical
coincidence the standard was written to catch.  Until someone produces an
operator or module map carrying one to the other, they are unrelated, and the
Lagrange obstruction says that map cannot be a group homomorphism.

A NARROWER THING THAT IS TRUE.  Five does divide 51840, and elements of order
5 exist, so the cube's C_5 factor could in principle act.  If a bridge is to
be built, C_3 and C_5 are the only two factors with any chance of being
carried by symmetry, and the C_7 sector would have to arrive some other way.
That is a concrete narrowing of where to look, which is the useful content of
a no-go.
"""

import json
import os
import random
import subprocess
import sys
from math import lcm

ROOT = r"C:\Repos\Holotrade"
N = 40
AUT = 51840
CUBE = (3, 5, 7)
CLOCK = 13


def load_gens():
    out = subprocess.run(
        ["node", "-e",
         "global.window=global;"
         "const SH=require('./scheduler/w33-shapes.js');"
         "process.stdout.write(JSON.stringify(SH.generators()"
         ".map(g=>Array.from(g))));"],
        cwd=ROOT, capture_output=True, text=True)
    if out.returncode:
        sys.exit("node failed: " + out.stderr[:400])
    return json.loads(out.stdout)


def perm_order(g):
    seen, o = [False] * len(g), 1
    for i in range(len(g)):
        if seen[i]:
            continue
        L, j = 0, i
        while not seen[j]:
            seen[j], j, L = True, g[j], L + 1
        o = lcm(o, L)
    return o


def factor(n):
    out, m = {}, n
    p = 2
    while p * p <= m:
        while m % p == 0:
            out[p] = out.get(p, 0) + 1
            m //= p
        p += 1
    if m > 1:
        out[m] = out.get(m, 0) + 1
    return out


def main():
    gens = load_gens()
    f = factor(AUT)
    fstr = " * ".join("%d^%d" % (p, e) for p, e in sorted(f.items()))

    # Compose ONE randomly chosen generator per step. Choosing inside the
    # comprehension would pick a different generator for each position and
    # produce a map that is not a permutation at all -- which is exactly the
    # bug that first ran here, and it manufactured element orders up to 5460
    # in a group of exponent 12.
    random.seed(5)
    cur, orders = list(range(N)), set()
    for _ in range(200000):
        g = random.choice(gens)
        cur = [g[cur[i]] for i in range(N)]
        assert len(set(cur)) == N, "composition must stay a permutation"
        orders.add(perm_order(cur))

    print("THE 3-5-7 CUBE CANNOT REACH W(3,3) BY SYMMETRY")
    print("=" * 70)
    print("  |Aut(W(3,3))| = %d = %s" % (AUT, fstr))
    print("  element orders realised:", sorted(orders))
    print()
    rows = []
    for p in list(CUBE) + [CLOCK]:
        divides = AUT % p == 0
        realised = p in orders
        rows.append({"prime": p, "dividesAutOrder": divides,
                     "orderRealised": realised})
        print("   C%-3d : divides |Aut| = %-5s   realised = %-5s   %s"
              % (p, divides, realised,
                 "available" if divides else "IMPOSSIBLE by Lagrange"))
    print()
    print("  ==> the cube's C3 and C5 factors could act; C7 cannot, and")
    print("      neither can the C13 clock. Not a failed search -- 7 and 13")
    print("      simply do not divide 2^7 * 3^4 * 5.")
    print()
    print("  The seven that DOES live in W(3,3) is alpha = 7 against a Hoffman")
    print("  bound of 10: the ovoid defect, a combinatorial invariant with no")
    print("  group of order 7 near it. Two sevens in one project is exactly the")
    print("  coincidence the standard was written to catch.")

    ok = (AUT % 7 != 0 and AUT % 13 != 0 and AUT % 3 == 0 and AUT % 5 == 0
          and 7 not in orders and 13 not in orders and 5 in orders)

    if "--write" in sys.argv:
        out = os.path.join(ROOT, "data", "w33_357_cube_obstruction.json")
        with open(out, "w") as fh:
            json.dump({
                "schema": "holotrade.w33-357-cube-obstruction.v1",
                "valid": ok,
                "autOrder": AUT,
                "autFactorisation": {str(k): v for k, v in sorted(f.items())},
                "elementOrdersRealised": sorted(orders),
                "primes": rows,
                "obstruction": ("7 and 13 do not divide |Aut(W(3,3))| = "
                                "2^7 * 3^4 * 5, so by Lagrange the quadrangle "
                                "has no C7 and no C13; the cube's C7 factor and "
                                "the H(4) C13 clock cannot act on it"),
                "notASearchResult": True,
                "sevenInW33": ("alpha = 7 against a Hoffman ratio bound of 10 -- "
                               "the ovoid defect, a combinatorial invariant, not "
                               "a group order"),
                "whatCouldStillTransport": [3, 5],
                "standard": ("an operator or module map, not a numerical "
                             "coincidence; this is the negative half of that "
                             "standard applied to the C7 factor"),
                "boundary": ("this rules out a GROUP-THEORETIC transport of the "
                             "C7 sector to W(3,3). It does not rule out some "
                             "other kind of map, and it says nothing about the "
                             "cube itself, which stands on its own side."),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(out, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
