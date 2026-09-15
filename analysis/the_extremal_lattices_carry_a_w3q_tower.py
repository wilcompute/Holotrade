#!/usr/bin/env python3
"""
THE EXTREMAL LATTICES CARRY A W(3,q) TOWER: E8 -> W(3,3), LEECH -> W(3,7),
P48n -> W(3,13), AND THE NEXT RUNG IS AN OPEN QUESTION IN DIMENSION 72.

THE PATTERN.  A unimodular lattice L of rank 4(q-1), q an odd prime, with an
isometry sigma of type q-(4,0)-0 (characteristic polynomial Phi_q^4) is a rank-4
Z[zeta_q]-module. By the parity lemma (e680b23: delta = (zeta - zeta^-1)^(q-2)
generates the different and is sigma-antisymmetric), L/(1-zeta)L = F_q^4 carries
a nondegenerate alternating form. So L carries the symplectic quadrangle
W(3,q) -- the corpus's two-qudit Pauli geometry in prime dimension q. The
extremal even unimodular lattices in dimensions 8, 24, 48 realise this for
q = 3, 7, 13:

  dim  lattice   q   type        status
    8  E8        3   3-(4,0)-0   computed (e680b23 control; the corpus's P1021 fibration)
   24  Leech     7   7-(4,0)-0   computed (e680b23: 120/280 split, Feng-Xiang 2.A7)
   48  P48n     13   13-(4,0)-0  BUILT HERE from Z[zeta_65]; W(3,13) certified
   72  ?        19   19-(4,0)-0  OPEN: allowed by Nebe (Thm 3.4, arXiv:1409.8473), no lattice known

In dimensions 24k the pattern is q = 6k+1 (7, 13, 19, then 31 at 120 and 37 at
144; Nebe lists p = 37 as possible in dimension 144). E8 is the base case q = 3.

P48n, EXPLICITLY.  Nebe (arXiv:1212.0865, Thm 5.3) proves P48n is the only
extremal lattice with an automorphism of order 65, and that it is a principal
ideal lattice (Z[zeta_65], Tr(alpha x xbar)). This file carries that construction
out and certifies it:
  * alpha = (unit) * (1-zeta_5)^-3 (1-zeta_13)^-11, made real and totally
    positive with units of Q(zeta_65)+. PARI: class number 1, unit rank 23, sign
    map of F_2-rank 19, so 2^5 = 32 totally positive unit classes -- exactly
    Nebe's |U| = 32.
  * The 32 trace-form lattices, screened with fpylll (BKZ + exact enumeration):
    exactly TWO have no vectors of norm 2 or 4 (candidates 25 and 27), again
    matching Nebe ("only two of them are extremal"). Candidate 25 is extremal
    and has the order-65 automorphism zeta, so it is P48n by Nebe's theorem.
    Its Gram matrix is data/p48n_gram_zeta65.txt.
  * Checked exactly below: det 1, even, positive definite; sigma = zeta^5 has
    sigma^T G sigma = G and 1 + sigma + ... + sigma^12 = 0 (type 13-(4,0)-0).
  * The form matrix W = G * sum_k lam_k sigma^k mod 13 is skew with F_13-rank
    exactly 4. Its kernel contains piL, of index 13^4, so it induces a
    nondegenerate alternating form on L/piL = F_13^4: P48n carries W(3,13).
  * The same check for zeta^13 (order 5, type 5-(12,0)-0) gives F_5-rank 12,
    i.e. W(11,5).
  * Enumerating all 52,416,000 minimal vectors to distribute them over W(3,13)
    was attempted and is not feasible with this tooling (forqfvec made no
    checkpoint in 30 CPU-minutes). The distribution is left open.

THE TOE READING (a reading, not a physical claim).  In the corpus's dictionary
W(3,q) is the commutation geometry of two q-level systems. E8's 240 roots cover
all 40 two-qutrit classes (6:1, P1021). Leech's 196560 minimal vectors weight
the 400 two-heptit classes as 462/504, splitting them into the Feng-Xiang A7
tight pair. P48n carries the two-13-level geometry. So the substrate's W(3,3)
inside E8 is the first rung of a tower of extremal lattices, whose next rung
(W(3,19), dimension 72) is an open existence question.

SCOPE.  E8, Leech, P48n and their automorphism facts are classical (Conway-Sloane,
Nebe). The parity lemma is standard. What is new: the W(3,q) tower statement, the
explicit P48n construction and certificate here, and the dimension-72 question
posed as the next rung.
"""

import argparse
import json
import os

import numpy as np
import sympy
from sympy.polys.matrices import DomainMatrix
from sympy import GF

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M65, N = 65, 48


def load_gram():
    s = open(os.path.join(ROOT, "data", "p48n_gram_zeta65.txt")).read().strip()
    return [[int(v) for v in r.split(",")] for r in s.strip("[]").split(";")]


def mult_matrix(shift):
    """column matrix of multiplication by zeta^shift on the power basis of Z[zeta_65]."""
    x = sympy.symbols("x")
    phi = sympy.Poly(sympy.cyclotomic_poly(M65, x), x)
    cols = []
    for j in range(N):
        r = sympy.Poly(x ** (j + shift), x).rem(phi)
        coeffs = r.all_coeffs()[::-1]
        cols.append([int(coeffs[i]) if i < len(coeffs) else 0 for i in range(N)])
    return np.array(cols, dtype=object).T


def lam_coefficients(p):
    # delta = (z - z^-1)^(p-2); lam_k = value at z=1 of the reduction of delta * z^k / p
    from fractions import Fraction

    def polmul(a, b):
        out = [Fraction(0)] * (len(a) + len(b) - 1)
        for i, u in enumerate(a):
            for j, v in enumerate(b):
                out[i + j] += u * v
        return out

    def red(a):
        b = [Fraction(0)] * p
        for i, u in enumerate(a):
            b[i % p] += u
        return [b[k] - b[p - 1] for k in range(p - 1)]
    base = [Fraction(0)] * p
    base[1] += 1
    base[p - 1] -= 1
    delta = [Fraction(1)]
    for _ in range(p - 2):
        delta = red(polmul(delta, base)) + [Fraction(0)]
    delta = red(delta)
    lam = []
    for k in range(p):
        c = [Fraction(0)] * p
        c[k] = Fraction(1, p)
        lam.append(sum(red(polmul(red(c), delta))))
    assert all(v.denominator == 1 for v in lam)
    return [int(v) for v in lam]


def rank_mod(Mx, p):
    rows = [[GF(p)(int(v) % p) for v in r] for r in Mx.tolist()]
    return DomainMatrix(rows, (len(rows), len(rows[0])), GF(p)).rank()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    G = np.array(load_gram(), dtype=object)
    Gs = sympy.Matrix(G.tolist())
    checks = {}
    checks["symmetric"] = (G == G.T).all()
    checks["even"] = all(int(G[i, i]) % 2 == 0 for i in range(N))
    checks["unimodular"] = Gs.det() == 1
    checks["positiveDefinite"] = bool(np.all(np.linalg.eigvalsh(np.array(G, dtype=float)) > 0))
    screen = json.load(open(os.path.join(ROOT, "data", "p48n_extremality_screen.json")))
    checks["extremalScreenMatchesNebe"] = screen["extremal"] == [25, 27] and len(screen["candidates"]) == 32

    rungs = {}
    for p, shift, z in ((13, 5, 4), (5, 13, 12)):
        S = mult_matrix(shift)
        preserves = (S.T.dot(G).dot(S) == G).all()
        pw = [np.identity(N, dtype=object)]
        for _ in range(p):
            pw.append(S.dot(pw[-1]))
        order_ok = (pw[p] == np.identity(N, dtype=object)).all()
        phi_zero = (sum(pw[:p]) == 0).all()
        lam = lam_coefficients(p)
        W = G.dot(sum(lam[k] * pw[k] for k in range(p)))
        Wm = np.vectorize(lambda v: int(v) % p)(W)
        skew = ((Wm + Wm.T) % p == 0).all() and all(Wm[i, i] == 0 for i in range(N))
        r = rank_mod(Wm, p)
        # pi L = (1 - sigma) L lies in the kernel: W (1 - sigma) = 0 mod p on the right and left
        piL = np.vectorize(lambda v: int(v) % p)(W.dot(np.identity(N, dtype=object) - S))
        kernel_ok = (piL == 0).all()
        rungs[str(p)] = {"shift": shift, "preservesForm": bool(preserves), "orderP": bool(order_ok),
                         "phiZero": bool(phi_zero), "formSkew": bool(skew), "rankModP": r,
                         "piLInKernel": bool(kernel_ok), "geometry": "W(%d,%d)" % (z - 1, p) if r == z else None}
        print("  zeta^%d: order %d, preserves %s, Phi_%d = 0 %s, skew %s, rank mod %d = %d, piL in radical %s -> %s" % (
            shift, p, preserves, p, phi_zero, skew, p, r, kernel_ok, rungs[str(p)]["geometry"]))
    checks["sigma13_fixed_point_free_type_13_4_0_0"] = all(rungs["13"][k] for k in ("preservesForm", "orderP", "phiZero"))
    checks["W3_13"] = rungs["13"]["formSkew"] and rungs["13"]["rankModP"] == 4 and rungs["13"]["piLInKernel"]
    checks["sigma5_type_5_12_0_0"] = all(rungs["5"][k] for k in ("preservesForm", "orderP", "phiZero"))
    checks["W11_5"] = rungs["5"]["formSkew"] and rungs["5"]["rankModP"] == 12 and rungs["5"]["piLInKernel"]
    tower = [{"dim": 8, "lattice": "E8", "q": 3, "geometry": "W(3,3)", "source": "e680b23"},
             {"dim": 24, "lattice": "Leech", "q": 7, "geometry": "W(3,7)", "source": "e680b23"},
             {"dim": 48, "lattice": "P48n", "q": 13, "geometry": "W(3,13)", "source": "this file"},
             {"dim": 72, "lattice": None, "q": 19, "geometry": "W(3,19)", "source": "open (Nebe Thm 3.4 allows 19-(4,0)-0)"}]
    checks["arithmetic"] = all(t["dim"] == 4 * (t["q"] - 1) for t in tower) and all(
        (t["q"] - 1) % 6 == 0 for t in tower[1:])
    try:
        e680 = json.load(open(os.path.join(ROOT, "data", "leech_suzuki_chain_rungs.json")))
        checks["lowerRungsCertified"] = (e680["valid"] and e680["checks"]["controlE8d3_W33_uniform3"]
                                         and e680["checks"]["d7_W37_120_280"])
    except OSError:
        checks["lowerRungsCertified"] = False
    ok = all(bool(v) for v in checks.values())
    for k, v in checks.items():
        print("  %-40s %s" % (k, v))
    print()
    print("VALID: %s" % ok)
    if args.write:
        assert ok, "checks failed -- refusing to write"
        rec = {"schema": "holotrade.extremal-lattice-w3q-tower.v1", "valid": True,
               "checks": {k: bool(v) for k, v in checks.items()}, "p48nRungs": rungs, "tower": tower,
               "construction": {"field": "Q(zeta_65)", "alpha": "unit * (1-zeta_5)^-3 (1-zeta_13)^-11, totally positive",
                                "totallyPositiveUnitClasses": 32, "extremalCandidates": screen["extremal"],
                                "identification": "Nebe arXiv:1212.0865 Thm 5.3: order-65 automorphism + extremal => P48n",
                                "scripts": "analysis/p48n/"},
               "open": ["distribution of the 52,416,000 minimal vectors of P48n over W(3,13)",
                        "existence of an extremal 72-dimensional lattice with a 19-(4,0)-0 automorphism (W(3,19) rung)"],
               "boundary": "lattices and automorphism facts classical (Nebe, Conway-Sloane); new: the tower statement and the explicit certified P48n rung; no physics"}
        with open(os.path.join(ROOT, "data", "extremal_lattice_w3q_tower.json"), "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=2)
        print("written")


if __name__ == "__main__":
    main()
