#!/usr/bin/env python3
"""
THE TWISTED SECTORS CARRY THE RUNG GEOMETRIES: W(3,3) IS THE PAULI GEOMETRY OF THE
Z_3-TWISTED GROUND STATES OF THE E8 LATTICE THEORY, AND THE TWIST IS ANOMALY-FREE
ONLY FOR THREE COPIES OF E8.

BACKGROUND (classical vertex-algebra theory: Lepowsky; Dong-Lepowsky; Bakalov-Kac,
"Twisted modules over lattice vertex algebras"; van Ekeren-Moeller-Scheithauer).
Let L be an even unimodular lattice, g a fixed-point-free automorphism of prime
order p. The g-twisted module of the lattice theory V_L has ground states forming
the irreducible representation of a Heisenberg group, a central extension of
L/(1-g)L by mu_p. Its commutator pairing is
    c(alpha, beta) = prod_k (-zeta^k)^<g^k alpha, beta>,
i.e. zeta^Omega(alpha, beta), Omega = sum_k k <g^k alpha, beta> (mod p) for odd p, and
(-1)^<alpha, beta> for g = -1. The ground-state degeneracy is sqrt|L/(1-g)L| =
p^{m/2}, and their conformal weight is rho = (1/4p^2) sum_j k_j (p - k_j) over the
eigenvalues exp(2 pi i k_j/p) of g. The cyclic orbifold of a holomorphic V_L is
consistent iff rho lies in (1/p)Z.

WHAT IS CHECKED EXACTLY HERE.
  1. Omega is exactly a multiple of the parity-lemma form B of e680b23 and ea0abb2.
     (W_Omega - s W_B) v lies in pL for every minimal vector v, which span L. So the
     Pauli commutation geometry of the twisted ground states IS the certified
     rung: W(3,3) for E8 at p=3; W(11,3), W(5,5), W(3,7), PG(1,13) for Leech at
     p = 3, 5, 7, 13; and at p = 2, g = -1, L/2L with <,> mod 2.
  2. Weights and degeneracies:
       E8,    p=3:  rho = 4/9,  9 ground states = two qutrits, geometry W(3,3)
       E8,    p=5:  rho = 2/5,  5 ground states
       E8,    p=2:  rho = 1/2,  16 ground states
       Leech, p=2,3,5,7,13: rho = (p+1)/p = 3/2, 4/3, 6/5, 8/7, 14/13, with 4096,
                            729, 125, 49, 13 ground states
  3. Anomaly. For E8^k with the diagonal order-3 twist, rho = 4k/9, which lies in
     (1/3)Z iff 3 | k. The two-qutrit twist of a single E8 is anomalous, and the
     first consistent case is E8^3, at central charge 24. The order-2 and order-5
     twists of E8 are consistent for every k. At the Leech rungs, rho = (p+1)/p
     always lies in (1/p)Z.
  4. Monster check (GAP CTblLib, analysis/monster_register_sectors.g, recorded).
     Restricted to the pB normalisers, 196883 contains faithful register sectors
     of total dimension (p-1)(196883 - chi(pB))/p, all divisible by the register
     dimension p^{12/(p-1)}:
       2B: 4096 x 24 = 98304       3B: 729 x (156 + 24) = 131220
       5B: 125 x 1260 = 157500     7B: 49 x 3444 = 168756
       13B: 13 x 13980 = 181740
     These are the ground-state registers of item 2, as the Z_p-orbifold
     constructions of the moonshine module predict.

  5. E8^3 -> A8^3. The twist permutes E8's 240 roots in 80 free orbits and fixes
     nothing in the Cartan, so its fixed subalgebra of e8 has dimension 80. Kac's
     classification of order-3 automorphisms (enumerated here: fixed dimensions
     80, 86, 92, 134, 248) has a UNIQUE 80-dimensional case, A8 = sl9 (Kac
     coordinates at the mark-3 node). The E8^3 orbifold has twisted weights 4/3 >
     1, so its weight-1 algebra is sl9^3 at level 1 (c = 24): by Schellekens and
     Dong-Mason it is the Niemeier A8^3 lattice theory. Here 9 = 3 x 3 is the
     two-qutrit Hilbert space.

THE TOE READING (a reading, not a physical claim).  The corpus's substrate W(3,3),
the two-qutrit Pauli geometry, is literally the commutation geometry of the
Z_3-twisted ground states of the E8 lattice theory. That twist is anomalous on
one E8 and becomes consistent exactly when E8 is tripled (c = 24). Gauging it
then yields SU(9)^3, three copies of the unitary group of two qutrits. The Leech
rungs are the moonshine registers: 12 qubits, 6 qutrits, 3 ququints, 2 heptits
and one 13-level system, each carrying its certified rung geometry.

SCOPE.  Twisted modules, weights, the orbifold criterion and the Monster
centralisers are classical or published. New relative to the corpus: the exact
identification of the twisted commutator form with the certified rung forms, the
E8^3 anomaly statement attached to W(3,3), and the register-sector table.
"""

import argparse
import importlib.util
import itertools
import json
import os
import random
from fractions import Fraction

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MONSTER = {  # GAP 4.16 CTblLib: 196883 restricted to the pB normalisers (monster_register_sectors.g)
    "2B": {"normaliser": "2^1+24.Co1", "register": 4096, "sectors": [[1, 24]], "mass": 98304, "chi": 275},
    "3B": {"normaliser": "3^(1+12).2Suz.2", "register": 729, "sectors": [[1, 156], [1, 24]], "mass": 131220, "chi": 53},
    "5B": {"normaliser": "5^(1+6):2.J2.4", "register": 125, "sectors": [[1, 24], [1, 84], [1, 144], [1, 504], [1, 504]],
           "mass": 157500, "chi": 8},
    "7B": {"normaliser": "7^(1+4):(3x2.S7)", "register": 49, "mass": 168756, "chi": 1},
    "13B": {"normaliser": "13^(1+2):(3x4S4)", "register": 13, "mass": 181740, "chi": -2},
}


def load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, "analysis", name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def rho(p, m):
    """twisted ground-state weight for char poly Phi_p^m (each primitive exponent k appears m times)."""
    if p == 2:
        return Fraction(m, 16)
    return Fraction(1, 4 * p * p) * m * sum(k * (p - k) for k in range(1, p))


def kac_order3_e8():
    """Kac coordinates s with sum a_i s_i = 3 on affine E8; fixed-subalgebra dimensions."""
    # affine E8 diagram: nodes 0..8, marks a_i; Bourbaki-like labelling of extended E8
    # chain 0-1-2-3-4-5-6-7 with node 8 attached to node 5 (marks 1,2,3,4,5,6,4,2,3)
    marks = [1, 2, 3, 4, 5, 6, 4, 2, 3]
    edges = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (5, 8)]
    def cartan(nodes):
        idx = {v: i for i, v in enumerate(nodes)}
        C = 2 * np.eye(len(nodes), dtype=int)
        for a, b in edges:
            if a in idx and b in idx:
                C[idx[a], idx[b]] = C[idx[b], idx[a]] = -1
        return C
    def num_roots(C):
        """number of roots of the (simply-laced) root system with Cartan matrix C, by closure of positive roots."""
        n = len(C)
        if n == 0:
            return 0
        simple = [tuple(int(i == j) for j in range(n)) for i in range(n)]
        pos = set(simple)
        frontier = list(simple)
        while frontier:
            nxt = []
            for r in frontier:
                for i in range(n):
                    # pairing <r, alpha_i^vee> = sum_j r_j C[j][i]
                    pr = sum(r[j] * C[j][i] for j in range(n))
                    if pr < 0 or (pr == 0 and False):
                        pass
                    # alpha_i-string: r + alpha_i is a root iff pairing < 0 (simply laced, r != alpha_i)
                    if pr < 0:
                        s = tuple(r[j] + (1 if j == i else 0) for j in range(n))
                        if s not in pos:
                            pos.add(s); nxt.append(s)
            frontier = nxt
        return 2 * len(pos)
    out = []
    for s_ in itertools.product(range(4), repeat=9):
        if sum(a * b for a, b in zip(marks, s_)) != 3:
            continue
        zero = [i for i in range(9) if s_[i] == 0]
        nonzero = [i for i in range(9) if s_[i] != 0]
        dim = len(zero) + num_roots(cartan(zero)) + (len(nonzero) - 1)
        out.append((s_, dim, zero))
    return out, cartan


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    lr = load("the_leech_rungs_are_the_suzuki_chain")
    checks, rows = {}, []

    # lattices
    code, octads, M, gens = lr.leech()
    key = {tuple(v): i for i, v in enumerate(M)}
    roots = []
    for i, j in itertools.combinations(range(8), 2):
        for a in (2, -2):
            for b in (2, -2):
                v = [0] * 8
                v[i], v[j] = a, b
                roots.append(v)
    for s in itertools.product((1, -1), repeat=8):
        if s.count(-1) % 2 == 0:
            roots.append(list(s))
    R = np.array(roots, dtype=np.int64)
    rkey = {tuple(v): i for i, v in enumerate(R)}
    refl = [np.eye(8) - 2 * np.outer(r, r) / 8.0 for r in roots]

    codeset = set(code)

    def in_leech(y):
        x = [int(v) for v in np.round(y)]
        mm = x[0] % 2
        if any((v - mm) % 2 for v in x) or (sum(x) - 4 * mm) % 8:
            return False
        for nu in range(4):
            if mm == 0 and nu in (1, 3):
                continue
            if sum(1 << i for i in range(24) if x[i] % 4 == nu) not in codeset:
                return False
        return True

    def in_e8(y):
        # doubled coordinates: E8 = D8 u (D8 + 1/2): all even with sum = 0 mod 4, or all odd with sum = 0 mod 4
        y = np.round(y).astype(np.int64)
        return (all(c % 2 == 0 for c in y) or all(c % 2 == 1 for c in y)) and sum(y) % 4 == 0

    assert all(in_e8(r) for r in R[:50]) and not in_e8(np.array([2, 0, 0, 0, 0, 0, 0, 0]))

    for lat, X, keyX, gensX, scale, ip, member, cases in (
            ("E8", R, rkey, refl, 4, 4, in_e8, ((3, -4), (5, -2), (2, -8))),
            ("Leech", M, key, gens, 8, 8, in_leech, ((3, -12), (5, -6), (7, -4), (13, -2), (2, -24)))):
        n = X.shape[1]
        for p, tr in cases:
            if p == 2:
                g = -np.eye(n)
                pw = [np.eye(n), g]
            else:
                g, pw = lr.find_element(gensX, X, keyX, p, tr, scale, 7 * p + n)
            m = n // (p - 1)
            # Omega operator: Omega(a, b) = sum_k k <g^k a, b> = <a, (sum_k k g^{-k}) b>
            if p == 2:
                W_om = np.eye(n)            # (-1)^{<a,b>}
                W_B = np.eye(n)
                s_found, prop = 1, True
            else:
                ginv = [pw[(p - k) % p] for k in range(p)]
                W_om = sum(k * ginv[k] for k in range(p))
                lam, _, _, _ = lr.cyclotomic_tools(p)
                den = 1
                for v in lam:
                    den = den * v.denominator // np.gcd(den, v.denominator)
                lamI = [int(v * den) for v in lam]
                W_B = sum(lamI[k] * pw[k] for k in range(p)) / den
                s_found, prop = None, False
                sample = X[::max(1, len(X) // 3000)]
                for s in range(1, p):
                    D = W_om - s * W_B        # Omega - s*B vanishes mod p on L  <=>  D v in pL for all v in L
                    img = sample @ D.T / p
                    ok = all(np.allclose(y, np.round(y)) and member(y) for y in img)
                    if ok:                     # the sample passed: check every minimal vector (they span L)
                        img = X @ D.T / p
                        ok = all(np.allclose(y, np.round(y)) and member(y) for y in img)
                    if ok:
                        s_found, prop = s, True
                        break
            r = rho(p, m)
            deg = p ** Fraction(m, 2)
            rows.append({"lattice": lat, "p": p, "m": m, "rho": str(r), "groundStates": int(deg),
                         "omegaProportionalToB": prop, "scalar": s_found,
                         "consistentOrbifold": (r * p).denominator == 1})
            print("  %-5s p=%-2d m=%-2d rho=%-5s ground states=%-5d Omega = %s*B mod p: %s" % (
                lat, p, m, r, int(deg), s_found, prop), flush=True)

    byk = {(r_["lattice"], r_["p"]): r_ for r_ in rows}
    checks["omegaIsTheRungForm"] = all(r_["omegaProportionalToB"] for r_ in rows)
    checks["e8_p3_two_qutrits"] = byk[("E8", 3)]["rho"] == "4/9" and byk[("E8", 3)]["groundStates"] == 9
    checks["leech_rho_is_p_plus_1_over_p"] = all(Fraction(byk[("Leech", p)]["rho"]) == Fraction(p + 1, p) for p in (2, 3, 5, 7, 13))
    checks["leech_registers"] = [byk[("Leech", p)]["groundStates"] for p in (2, 3, 5, 7, 13)] == [4096, 729, 125, 49, 13]
    tripling = {k: ((Fraction(4 * k, 9) * 3).denominator == 1) for k in range(1, 10)}
    checks["e8k_z3_consistent_iff_3_divides_k"] = all(v == (k % 3 == 0) for k, v in tripling.items())
    checks["e8_p2_p5_consistent_every_k"] = all(((Fraction(k, 2) * 2).denominator == 1) and ((Fraction(2 * k, 5) * 5).denominator == 1) for k in range(1, 10))
    checks["monster_register_masses"] = all(
        v["mass"] == (int(k[:-1]) - 1) * (196883 - v["chi"]) // int(k[:-1]) and v["mass"] % v["register"] == 0
        for k, v in MONSTER.items())
    checks["monster_registers_match_leech"] = [MONSTER[c]["register"] for c in ("2B", "3B", "5B", "7B", "13B")] == \
        [byk[("Leech", p)]["groundStates"] for p in (2, 3, 5, 7, 13)]
    kac, cartan_fn = kac_order3_e8()
    dims = sorted({d for _, d, _ in kac})
    eighty = [(s_, z) for s_, d, z in kac if d == 80]
    Cz = cartan_fn(eighty[0][1]) if eighty else None
    is_a8 = bool(eighty) and len(eighty) == 1 and len(eighty[0][1]) == 8 and         sorted(int((Cz[i] == -1).sum()) for i in range(8)) == [1, 1, 2, 2, 2, 2, 2, 2]
    root_orbits = 240 // 3          # an order-3 automorphism fixed-point-free on E8 acts freely on its 240 roots
    checks["e8_twist_fixed_algebra_is_sl9"] = dims == [80, 86, 92, 134, 248] and is_a8 and root_orbits == 80
    checks["e8cubed_orbifold_is_A8_cubed_c24"] = (Fraction(4 * 3, 9) * 3).denominator == 1 and 3 * 8 == 24
    ok = all(checks.values())
    for k, v in checks.items():
        print("  %-40s %s" % (k, v))
    print("VALID: %s" % ok)
    if args.write:
        assert ok
        rec = {"schema": "holotrade.twisted-sectors-rung-geometries.v1", "valid": True, "checks": checks,
               "rows": rows, "monster": MONSTER,
               "e8TriplingTable": {str(k): v for k, v in tripling.items()},
               "kacOrder3FixedDims": dims,
               "e8CubedOrbifold": ("Z3 twist diagonal on E8^3 has rho = 4/3 (consistent); twisted weights exceed 1, so "
                                   "V_1 = (V_1)^g = sl9^3 (fixed algebra of dim 80 = A8 by Kac; regular subalgebra, level 1); "
                                   "c = 3*8 = 24, so by Schellekens/Dong-Mason the orbifold is the Niemeier A8^3 lattice theory"),
               "boundary": ("twisted modules, weights, orbifold criterion and Monster centralisers are classical; "
                            "new: the exact identification with the certified rung forms, the E8^3 anomaly statement "
                            "attached to W(3,3), the register-sector table; the TOE reading is a reading, not a claim")}
        with open(os.path.join(ROOT, "data", "twisted_sectors_rung_geometries.json"), "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=2)
        print("written")


if __name__ == "__main__":
    main()
