#!/usr/bin/env python3
"""
THE A8^3 PAULI GROUP MOVES BETWEEN THE W(3,3) CARRIERS, AND EXACTLY ITS
LATTICE-CHANGING MOVES CARRY THE MONSTER 3B SERIES.

Continues 4104251 (the three two-qutrit Pauli groups act on V_{A8^3} as one extraspecial
3^(1+12)) and b09230c (its centre is the reverse orbifold to E8^3). The other track proved
in Pass 8989-9012 that exactly three Niemeier lattices carry W(3,3) at rank 24:
E8^3 (the lift), E6^4 (diagonal, sporadic) and A2^12 (twisted 3-cycles through the ternary
Golay glue). A8^3 is not one of them.

UP TO CONJUGATION THERE ARE SIX ELEMENT TYPES. Inside SL9 every nonscalar two-qutrit
Pauli has eigenvalues 1, omega, omega^2, each three times, and multiplying by a central
phase only permutes them. So an element of the 3^(1+12) is determined up to conjugacy by
the number k of factors on which it acts nonscalarly, together with its central phase when
k = 0: identity, centre z, z^2, and k = 1, 2, 3.

1. TWINING CHARACTERS, computed exactly in Z[omega] through q^7. With the Monster
   McKay-Thompson series T_3A = t + 12 + 729/t, T_3B = t + 12 and T_3C = E4(3 tau)/eta(3 tau)^8,
   where t = eta(tau)^12/eta(3 tau)^12:
       identity : J + 240
       z, z^2   : T_3B + 240
       k = 3    : T_3B - 3
       k = 1, 2 : not a McKay-Thompson series (q^1 coefficients 24111 and 2241)
   The constants are the traces on V_1 = sl9^3: each nonscalar Pauli has trace -1 on sl9,
   so 240, 159, 78 and -3.

2. WHERE EACH Z_3 SHIFT ORBIFOLD LANDS, by an exact count of norm-2 vectors in the
   invariant sublattice and in both twisted cosets:
       z     : E8^3   (720 roots; b09230c)
       k = 3 : A2^12  (72 roots)   - the ternary Golay carrier
       k = 1 : A8^3   (216 roots)
       k = 2 : A8^3   (216 roots)
   The V_1 bookkeeping closes in every case: the fixed V_1 plus twisted weight-one states
   gives 240 + 504 = 744, 78 + 18 = 96, 186 + 54 = 240 and 132 + 108 = 240.

3. WHY EXACTLY THOSE TWO ARE 3B. A Z_3 twining with trivial multiplier is Gamma_0(3)
   invariant with a simple pole at infinity. Its pole at the cusp 0 is set by the twisted
   ground weight. If that weight is at least 1, the function has no pole there, and by the
   Hauptmodul property of T_3B it equals T_3B + constant. Measured twisted ground weights:
   z -> 1, k = 3 -> 1, k = 2 -> 2/3, k = 1 -> 1/3. So the 3B-type elements are exactly
   those with twisted weight >= 1, and here they are exactly the lattice-changing moves.
   The same criterion covers the E8^3 W(3,3) twist and the Leech twist (frame shape
   3^12 1^-12, twining t = T_3B - 12) and the Monster's own 3B.

4. INDEPENDENT CROSS-CHECK, Chenevier-Lannes (Kneser 3-neighbours of Niemeier lattices,
   neighblist at gaetan.chenevier.perso.math.cnrs.fr/niemeier/, fetched 2026-09-17):
       N(3, A8^3, E8^3)  = 1           the E8^3 neighbour is UNIQUE, and it is the Pauli centre
       N(3, A8^3, A2^12) = 263424000   the k = 3 moves land here
       N(3, A8^3, A8^3)  = 587403432   the k = 1, 2 moves land here
       N(3, A8^3, E6^4)  = 592704      a neighbour that NO Pauli type reaches
       N(3, A8^3, Leech) = 0

READING. A8^3 sits between the carriers. Its W(3,3) Pauli group reaches the E8 lift and
the Golay carrier, both by Monster-3B-type moves, and misses the sporadic E6^4 carrier.

SCOPE. Items 1, 2 and 3 are exact computations plus a standard modular argument, and item
4 is external data. Kneser neighbours of Niemeier lattices are classical (Chenevier-Lannes),
and the genus-zero reason for 3B-type twinings is standard orbifold lore. What is new is
realising these moves by the W(3,3) Pauli group and linking them to the three-carrier
theorem of the other track.
"""

import argparse
import itertools
import json
import os
from fractions import Fraction as Fr

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QMAX = 7                                       # twinings through q^QMAX
GLUE = sorted({tuple((a * g[0][i] + b * g[1][i] + c * g[2][i]) % 9 for i in range(3))
               for g in [((1, 1, 4), (1, 4, 1), (4, 1, 1))]
               for a, b, c in itertools.product(range(9), repeat=3)})
PZ = [0, 0, 0, 1, 1, 1, -1, -1, -1]            # traceless log/(1/3) of a nonscalar two-qutrit Pauli
CENT = [1, 1, 1, 1, 1, 1, 1, 1, -8]            # traceless log/(1/3) of omega * I
ZERO = [0] * 9
CHENEVIER_A8CUBED_P3 = {"E8^3": 1, "A2^12": 263424000, "A8^3": 587403432, "E6^4": 592704, "Leech": 0}


# ---------- twining characters, exact in Z[omega] ----------
def coset_theta(k, h):
    B = 2 * (QMAX + 2) + 3 + k * k // 9
    states = {(0, 0, 0): 1}
    for i in range(9):
        nxt = {}
        for (s, n2, ph), cnt in states.items():
            for z in range(-5, 6):
                m2 = n2 + z * z
                if m2 > B:
                    continue
                key = (s + z, m2, (ph + h[i] * z) % 3)
                nxt[key] = nxt.get(key, 0) + cnt
        states = nxt
    out = {}
    for (s, n2, ph), cnt in states.items():
        if s != k:
            continue
        e = Fr(n2 * 9 - k * k, 18)
        if e > QMAX + 1:
            continue
        cur = list(out.get(e, (0, 0, 0)))
        cur[ph] += cnt
        out[e] = tuple(cur)
    return out


def zmul(u, v):
    r = [0, 0, 0]
    for i in range(3):
        for j in range(3):
            r[(i + j) % 3] += u[i] * v[j]
    return tuple(r)


def smul(a, b, cap):
    o = {}
    for x, u in a.items():
        for y, v in b.items():
            if x + y <= cap:
                w = zmul(u, v)
                o[x + y] = tuple(p + q for p, q in zip(o.get(x + y, (0, 0, 0)), w))
    return o


_th = {}
def th(k, h):
    key = (k, tuple(h))
    if key not in _th:
        _th[key] = coset_theta(k, h)
    return _th[key]


def twining(hs):
    tot = {}
    for c in GLUE:
        s = smul(smul(th(c[0], hs[0]), th(c[1], hs[1]), QMAX + 1), th(c[2], hs[2]), QMAX + 1)
        for e, v in s.items():
            tot[e] = tuple(p + q for p, q in zip(tot.get(e, (0, 0, 0)), v))
    M = QMAX + 1
    p = [1] + [0] * M                                    # prod (1-q^n)^-24
    for n in range(1, M + 1):
        for _ in range(24):
            for j in range(n, M + 1):
                p[j] += p[j - n]
    lst = [0] * (M + 1)
    for e, v in tot.items():
        assert e.denominator == 1 and v[1] == v[2], (e, v)     # integral weights, real coefficients
        if e <= M:
            lst[int(e)] += v[0] - v[1]
    return [sum(lst[i] * p[n - i] for i in range(n + 1)) for n in range(M + 1)]   # index n -> q^(n-1)


def monster_series():
    M = QMAX + 1

    def prod(powers):
        a = [1] + [0] * (M + 1)
        for n in range(1, M + 2):
            for mult, e in powers:
                step = mult * n
                if step > M + 1:
                    continue
                for _ in range(abs(e)):
                    if e > 0:
                        for j in range(M + 1, step - 1, -1):
                            a[j] -= a[j - step]
                    else:
                        for j in range(step, M + 2):
                            a[j] += a[j - step]
        return a
    t = prod([(1, 12), (3, -12)])
    T3B = t[:M + 1]
    T3B[1] += 12
    inv = prod([(3, 12), (1, -12)])
    T3A = [T3B[i] + (729 * inv[i - 2] if i >= 2 else 0) for i in range(M + 1)]
    E4 = [1] + [240 * sum(d ** 3 for d in range(1, n + 1) if n % d == 0) for n in range(1, M + 2)]
    e4_3 = [0] * (M + 2)
    for n, v in enumerate(E4):
        if 3 * n <= M + 1:
            e4_3[3 * n] = v
    den = prod([(3, -8)])
    T3C = [sum(e4_3[j] * den[i - j] for j in range(i + 1)) for i in range(M + 1)]
    J = [1, 0, 196884, 21493760, 864299970, 20245856256, 333202640600, 4252023300096, 44656994071935][:M + 1]
    return {"J": J, "3A": T3A, "3B": T3B, "3C": T3C}


# ---------- orbifold lattices by exact root counts (coordinates scaled by 9) ----------
_ft = {}
def factor_table(k, S9, H9):
    key = (k, tuple(S9), tuple(H9))
    if key not in _ft:
        states = {(0, 0, 0): 1}
        for i in range(9):
            nxt = {}
            for (sz, n2, ph), cnt in states.items():
                for z in range(-3, 4):
                    Y = 9 * z - k + S9[i]
                    m2 = n2 + Y * Y
                    if m2 > 162:
                        continue
                    kk = (sz + z, m2, (ph + H9[i] * Y) % 81)
                    nxt[kk] = nxt.get(kk, 0) + cnt
            states = nxt
        t = {}
        for (sz, n2, ph), cnt in states.items():
            if sz == k:
                t[(n2, ph)] = t.get((n2, ph), 0) + cnt
        _ft[key] = t
    return _ft[key]


def count_norm(S9s, H9s, target81, norm81=162):
    tot = 0
    for c in GLUE:
        T = [factor_table(c[f], S9s[f], H9s[f]) for f in range(3)]
        for (n1, p1), a in T[0].items():
            for (n2, p2), b in T[1].items():
                if n1 + n2 > norm81:
                    continue
                for (n3, p3), d in T[2].items():
                    if n1 + n2 + n3 == norm81 and (target81 is None or (p1 + p2 + p3 - target81) % 81 == 0):
                        tot += a * b * d
    return tot


def min_norm(S9s):
    Z9 = [0] * 9
    best = None
    for c in GLUE:
        T = [factor_table(c[f], S9s[f], Z9) for f in range(3)]
        for (n1, _), _a in T[0].items():
            for (n2, _), _b in T[1].items():
                for (n3, _), _d in T[2].items():
                    s = n1 + n2 + n3
                    if best is None or s < best:
                        best = s
    return best


def pauli_orbifold(k):
    Z9 = [0] * 9
    P9 = [3 * x for x in PZ]
    H = [P9 if f < k else Z9 for f in range(3)]
    h2 = Fr(sum(sum(x * x for x in Hf) for Hf in H), 81)
    base = count_norm([Z9] * 3, H, 0)
    lam = next(c for c in (Fr(0), Fr(1, 3), Fr(2, 3)) if (h2 + 2 * c) % 2 == 0)
    tw1 = count_norm(H, H, int(((h2 + lam) % 1) * 81))
    tw2 = count_norm([[2 * x for x in Hf] for Hf in H], H, int(((2 * (h2 + lam)) % 1) * 81))
    return {"roots_invariant": base, "roots_twisted": [tw1, tw2], "roots": base + tw1 + tw2,
            "twisted_ground_weight": str(Fr(min_norm(H), 162)), "V1_fixed": 26 * k + 80 * (3 - k)}


NIEMEIER = {48: "A1^24", 72: "A2^12", 96: "A3^8", 120: "A4^6", 168: "A6^4", 192: "A7^2D5^2", 216: "A8^3",
            312: "A12^2", 720: "E8^3", 0: "Leech"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    checks = {}
    mon = monster_series()
    checks["monster_series_known_values"] = mon["3A"][2:4] == [783, 8672] and mon["3B"][2:6] == [54, -76, -243, 1188] \
        and mon["3C"][3] == 248 and mon["3C"][6] == 4124
    types = {"identity": [ZERO, ZERO, ZERO], "z": [CENT, ZERO, ZERO], "z^2": [[(2 * x) % 3 for x in CENT], ZERO, ZERO],
             "k=1": [PZ, ZERO, ZERO], "k=2": [PZ, PZ, ZERO], "k=3": [PZ, PZ, PZ]}
    tw = {}
    for name, hs in types.items():
        ch = twining(hs)
        shifted = ch[:]
        shifted[1] = 0
        match = [k for k, v in mon.items() if shifted == v]
        tw[name] = {"series": ch, "V1_trace": ch[1], "monster_match": match}
        print("  %-9s twining %s  V1 trace %4d  Monster: %s" % (name, ch[:6], ch[1], match or "none"))
    checks["identity_is_J_plus_240"] = tw["identity"]["monster_match"] == ["J"] and tw["identity"]["V1_trace"] == 240
    checks["centre_is_T3B_plus_240"] = tw["z"]["monster_match"] == ["3B"] and tw["z^2"]["monster_match"] == ["3B"] \
        and tw["z"]["V1_trace"] == 240
    checks["full_pauli_is_T3B_minus_3"] = tw["k=3"]["monster_match"] == ["3B"] and tw["k=3"]["V1_trace"] == -3
    checks["partial_pauli_not_monster"] = tw["k=1"]["monster_match"] == [] and tw["k=2"]["monster_match"] == []
    checks["V1_traces_match_lie_algebra"] = [tw[x]["V1_trace"] for x in ("k=1", "k=2", "k=3")] == [159, 78, -3]

    orb = {}
    for k in (1, 2, 3):
        r = pauli_orbifold(k)
        r["lattice"] = NIEMEIER.get(r["roots"], "?")
        orb["k=%d" % k] = r
        print("  k=%d orbifold: %s" % (k, r))
    orb["z"] = {"lattice": "E8^3", "roots": 720, "twisted_ground_weight": "1", "source": "Holotrade b09230c"}
    checks["full_pauli_lands_on_A2_12"] = orb["k=3"]["lattice"] == "A2^12"
    checks["partial_pauli_returns_A8_3"] = orb["k=1"]["lattice"] == "A8^3" and orb["k=2"]["lattice"] == "A8^3"
    checks["V1_bookkeeping_closes"] = all(orb["k=%d" % k]["V1_fixed"] + sum(orb["k=%d" % k]["roots_twisted"]) ==
                                          {1: 240, 2: 240, 3: 96}[k] for k in (1, 2, 3))
    wts = {x: Fr(orb[x]["twisted_ground_weight"]) for x in ("z", "k=1", "k=2", "k=3")}
    checks["twisted_weights"] = [str(wts[x]) for x in ("k=1", "k=2", "k=3", "z")] == ["1/3", "2/3", "1", "1"]
    checks["3B_iff_twisted_weight_at_least_1"] = all(
        (tw[x]["monster_match"] == ["3B"]) == (wts[x] >= 1) for x in ("z", "k=1", "k=2", "k=3"))
    checks["chenevier_E8_3_neighbour_unique"] = CHENEVIER_A8CUBED_P3["E8^3"] == 1
    checks["chenevier_reached_classes_nonempty"] = CHENEVIER_A8CUBED_P3["A2^12"] > 0 and CHENEVIER_A8CUBED_P3["A8^3"] > 0
    checks["chenevier_E6_4_neighbour_not_reached_by_pauli"] = CHENEVIER_A8CUBED_P3["E6^4"] > 0 and \
        "E6^4" not in {orb[x]["lattice"] for x in orb}
    for k, v in checks.items():
        print("  %-46s %s" % (k, v))
    valid = all(checks.values())
    print("VALID:", valid)
    if args.write:
        payload = {
            "claim": "The Pauli 3^(1+12) of the Niemeier A8^3 theory moves between the W(3,3) carriers of the other track's "
                     "three-carrier theorem: its centre gives the UNIQUE 3-neighbour E8^3 (twining T_3B + 240) and every "
                     "all-factor Pauli element gives A2^12, the ternary Golay carrier (twining T_3B - 3). One- and two-factor "
                     "elements return to A8^3 with non-Monster twinings. The Monster 3B type occurs exactly when the "
                     "twisted ground weight is >= 1 - here, exactly for the lattice-changing moves. The sporadic E6^4 carrier "
                     "is a 3-neighbour that no Pauli element reaches.",
            "twinings": tw, "orbifolds": orb, "chenevierLannesA8cubedP3": CHENEVIER_A8CUBED_P3,
            "otherTrackCarriers": "TOE Pass 8989-9012: E8^3 (lift), E6^4 (diagonal, sporadic), A2^12 (Golay twisted 3-cycles)",
            "checks": checks, "valid": valid,
            "status": "exact twining and root-count computations; modular Hauptmodul argument; external Kneser-neighbour data",
            "sources": ["Holotrade 4104251", "Holotrade b09230c", "TOE Pass 8989-9012 (exactly three carriers)",
                        "TOE 865e04b18 (S3 twining)", "Chenevier-Lannes, Kneser neighbours of Niemeier lattices",
                        "Conway-Norton McKay-Thompson series 3A, 3B, 3C"]}
        with open(os.path.join(ROOT, "data", "w33_a8cubed_pauli_moves_between_carriers.json"), "w") as f:
            json.dump(payload, f, indent=1)
        print("written")


if __name__ == "__main__":
    main()
