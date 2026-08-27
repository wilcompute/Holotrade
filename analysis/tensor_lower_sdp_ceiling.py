#!/usr/bin/env python3
"""
A ceiling on convex relaxations: why no 2-point cone can prove tau_2 >= 111.

Seven combinatorial attacks on |X| = 110 have returned UNKNOWN.  Before
building an eighth, it is worth asking whether the OTHER standard tool --
convex relaxation -- could work at all, because that answer is cheap and it
either opens a route or closes one permanently.

It closes one.

THE SETUP.  Minimise sum(x) over 0/1 leaf variables subject to
sum_{i in T} x_i >= 1 for each of the 1,600 product tiles.  The Shor
relaxation (Lasserre level 1) adds the moment matrix

    Y = [[1, x^T], [x, Z]]  psd,   Z_ii = x_i,   Z >= 0 entrywise,

together with the products of each tile constraint with each variable.

THE SYMMETRY REDUCTION, which makes this tiny.  Aut(W(3,3)) x Aut(W(3,3))
acts on the 1,600 leaves, and the point action has exactly three orbitals --
equal, collinear, non-collinear -- so the leaf action has 3 x 3 = 9.  The
optimum can be symmetrised, so x is constant and Z lies in the commutant:

    Z = sum_{a,b} z_ab (A_a kron A_b),        nine unknowns,

with A_0 = I, A_1 the adjacency of SRG(40,12,2,4) and A_2 = J - I - A_1.
Their eigenvalues are (1,1,1), (12,2,-4) and (27,-3,3) on the three
eigenspaces of multiplicity 1, 24, 15, so Z's spectrum is the outer product
and the psd condition becomes nine scalar inequalities.  The whole SDP has
ten variables.

The product constraints also collapse, and for a reason worth naming: in a
generalized quadrangle a point off a line is collinear with EXACTLY one of
its points.  So the relation-count vector from a point to the four points of
a line is (1,3,0) if it lies on the line and (0,1,3) otherwise -- two cases
per coordinate, four constraints in total.

THE ANSWER.  The optimum is exactly 100 -- the same as the plain fractional
bound 1600/16 that transitivity gives for free.  The SDP does not merely fail
to beat the shadow bound of 110; it fails to REACH it.

WHY, AND WHAT IT RULES OUT.  The shadow argument is about LINES: it says the
union of the four fibres over a line must itself block, which is a statement
about a four-point object.  A relaxation whose only structure is the
two-point association scheme cannot express that, so it is capped below 110
no matter how much psd machinery is stacked on it.  Strengthening the cone at
the two-point level -- theta-body, tighter Lasserre-1, more valid pairwise
cuts -- cannot prove tau_2 >= 111.

That leaves two honest routes: a relaxation whose variables live at the level
of lines or higher (Lasserre level 4 or a line-indexed formulation), or a
combinatorial argument that converts the ovoid defect directly into a
statement about the product.  This file exists so the next attempt does not
spend its time on a bigger SDP.
"""

import itertools
import json
import os
import sys

try:
    import cvxpy as cp
    import numpy as np
except ImportError:
    sys.exit("needs cvxpy and numpy:  py -3 -m pip install cvxpy")

ROOT = r"C:\Repos\Holotrade"
LEAVES = 1600
TILE = 16
LP_BOUND = LEAVES // TILE          # 100, by transitivity
SHADOW_BOUND = 110                 # the elementary double count

# eigenvalues of I, A_1 and A_2 on the three eigenspaces of SRG(40,12,2,4)
LAM = {0: np.array([1., 1., 1.]),
       1: np.array([12., 2., -4.]),
       2: np.array([27., -3., 3.])}


def solve():
    z = {(a, b): cp.Variable(nonneg=True) for a in range(3) for b in range(3)}
    c = cp.Variable(nonneg=True)          # x_i = c for every leaf

    cons = [z[(0, 0)] == c]               # Z_ii = x_i; only A_0 x A_0 is diagonal
    cons += [TILE * c >= 1]               # the tile constraint itself

    # products of a tile constraint with a variable.  In a GQ a point off a
    # line meets exactly one of its points, so only two count-vectors occur.
    for np_, nq_ in itertools.product([(1, 3, 0), (0, 1, 3)], repeat=2):
        cons += [cp.sum([np_[a] * nq_[b] * z[(a, b)]
                         for a in range(3) for b in range(3)]) >= c]

    # psd, blockwise on the nine tensor eigenspaces
    for i in range(3):
        for j in range(3):
            ev = cp.sum([z[(a, b)] * LAM[a][i] * LAM[b][j]
                         for a in range(3) for b in range(3)])
            if (i, j) == (0, 0):
                cons += [ev >= LEAVES * cp.square(c)]   # border block
            else:
                cons += [ev >= 0]

    prob = cp.Problem(cp.Minimize(LEAVES * c), cons)
    val = prob.solve(solver=cp.SCS, eps=1e-9, max_iters=200000, verbose=False)
    return prob.status, float(val)


def main():
    status, val = solve()
    reaches = val >= SHADOW_BOUND - 1e-6
    print("A CEILING ON CONVEX RELAXATIONS")
    print("=" * 70)
    print("  symmetry-reduced Shor/Lasserre-1 over the 9-dimensional")
    print("  commutant of Aut(W33) x Aut(W33) on the 1600 leaves")
    print()
    print("  status                            : %s" % status)
    print("  plain fractional bound 1600/16    : %d" % LP_BOUND)
    print("  shadow double-count               : %d" % SHADOW_BOUND)
    print("  this SDP                          : %.4f" % val)
    print()
    if not reaches:
        print("  ==> the SDP does not even REACH the shadow bound.")
        print("      The shadow argument is about lines -- four-point objects")
        print("      the two-point scheme cannot express -- so no relaxation")
        print("      built on pairwise structure can prove tau_2 >= 111,")
        print("      however much psd machinery is stacked on it.")
        print()
        print("      Remaining honest routes: a formulation whose variables")
        print("      live at the level of lines, or a combinatorial argument")
        print("      converting the ovoid defect into a product statement.")
    else:
        print("  ==> reaches the shadow bound; worth pushing further.")

    if "--write" in sys.argv:
        out = os.path.join(ROOT, "data", "tensor_lower_sdp_ceiling.json")
        with open(out, "w") as fh:
            json.dump({
                "schema": "holotrade.tensor-lower-sdp-ceiling.v1",
                "status": status,
                "sdpBound": round(val, 6),
                "plainFractionalBound": LP_BOUND,
                "shadowBound": SHADOW_BOUND,
                "reachesShadowBound": bool(reaches),
                "commutantDimension": 9,
                "conclusion": ("a symmetry-reduced Lasserre-1 SDP returns the "
                               "plain fractional bound and does not reach 110"),
                "rulesOut": ("any convex relaxation whose only structure is the "
                             "two-point association scheme; the shadow argument "
                             "concerns lines, which are four-point objects"),
                "remainingRoutes": [
                    "a relaxation with line-level variables (Lasserre level 4 "
                    "or a line-indexed formulation)",
                    "a combinatorial argument converting the ovoid defect into "
                    "a statement about the product",
                ],
                "boundary": ("this bounds the METHOD family, not tau_2, which "
                             "stays open in [110, 115]"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(out, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
