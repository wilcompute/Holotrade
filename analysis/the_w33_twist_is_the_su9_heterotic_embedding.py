#!/usr/bin/env python3
"""
THE W(3,3) TWIST IS THE SU(9) HETEROTIC EMBEDDING: ITS Z_3 ANOMALY IS THE GENERATOR,
AND ON T^6/Z_3 ITS ONLY CONSISTENT PARTNER IS SO(14) x U(1).

Continues 68df33f (the_twisted_sectors_carry_the_rung_geometries.py). There the
fixed-point-free order-3 rotation of E8, whose twisted ground states carry W(3,3),
was shown to be conjugate to the order-3 automorphism with fixed algebra A8 = sl9,
with twisted weight 4/9 and 9 ground states. This file puts that automorphism into
the heterotic string.

BACKGROUND (classical: Dixon-Harvey-Vafa-Witten orbifolds; Ibanez-Nilles-Quevedo and
Ibanez-Mas-Nilles-Quevedo on Z_3 gauge embeddings; Kobayashi-Nakano on anomalous
U(1)).  An inner order-3 automorphism of E8 is a shift V with 3V in E8. Its
twisted module is the coset E8 + V. The heterotic E8 x E8 string on T^6/Z_3, with
spacetime twist v = (1/3, 1/3, -2/3), is modular invariant iff
3(V^2 - v^2) is in 2Z. Its massless left-chiral spectrum is:
    untwisted:  E8 x E8 roots P with P.V = 1/3 mod 1, once per complex plane (x3);
    twisted:    P in (E8 x E8) + V with P^2/2 + N = 2/3, where N is the oscillator
                level (N = 1/3 has 3 oscillators), once per fixed point (x27).

WHAT IS CHECKED EXACTLY HERE.
  1. Classification. The shifts V = u/3, over all E8 vectors u with |u|^2 <= 8
     (26641 vectors), fall into exactly five classes. These are the five Kac
     classes of order-3 automorphisms:
         fixed algebra   dim   twisted ground weight x states   a = |3V|^2/2 mod 3
         E8              248   0 x 1                            0
         E6 + A2          86   1/3 x 3                          0
         E7 + U1         134   1/9 x 1                          1
         A8               80   4/9 x 9                          1
         D7 + U1          92   2/9 x 1                          2
     The invariant a is well defined (V -> V + lambda changes |3V|^2/2 by 0 mod 3)
     and is the Z_3 anomaly of the twist. The A8 class has dimension 80, weight 4/9
     and 9 states: it is the W(3,3) twist of 68df33f.
  2. Level matching. v^2 = 2/3 carries a = 0, so a heterotic pair (V1, V2) is
     modular invariant iff a1 + a2 = 0 mod 3. Up to exchange, exactly five class
     pairs survive. The A8 class has ONE partner, D7 + U1. So the W(3,3) twist
     embeds in exactly one T^6/Z_3 vacuum, with gauge group SU(9) x SO(14) x U(1).
     On E8^k the diagonal A8 twist has a = k mod 3, which recovers 68df33f's
     condition 3 | k.
  3. Fixed points. det(1 - theta) on the A2^3 torus lattice is 27.
  4. The spectrum, built by exact enumeration and split into irreducible multiplets:
         3 (84, 1)_0  +  27 (9bar, 1)_{2/3}  +  3 (1, 64)_{1/2}  +  3 (1, 14)_{-1}
     Here 84 = Lambda^3 of the fundamental 9, and 9bar is its conjugate. U(1)
     charges are for t = e_1 of the second E8, up to an overall sign.
  5. Anomalies:
         SU(9)^3:   3 A(84) + 27 A(9bar) = 27 - 27 = 0  (sampled cubic forms vanish)
         Green-Schwarz universality for the anomalous U(1), with k_Q = 2|t|^2:
         Tr_SU9 Q T^2  =  Tr_SO14 Q T^2  =  Tr Q^3 / (3 k_Q)  =  Tr Q / 24  =  9  (up to sign)
  6. Controls with teeth.
     Standard embedding E6 x SU(3) x E8: 36 net 27-plets (27 twisted + 9 untwisted)
     and SU(3)^3 = 0. The opposite chirality convention breaks both, so the
     convention is fixed by the control rather than chosen.
     A level-mismatched pair (A8, E8) gives a nonzero SU(9)^3 anomaly.

THE TOE READING (a reading, not a physical claim).  Placing the substrate twist in
a string vacuum is not a free choice. Its anomaly class forces the second E8 to be
broken to SO(14) x U(1). Each of the 27 fixed points of T^6/Z_3 then carries one
two-qutrit register (the 9bar of SU(9)). The three untwisted complex planes carry
84 = Lambda^3(9), whose anomaly 3 x 9 is cancelled exactly by the 27 fixed-point
registers. This corrects scripts/w33_string_worldsheet.py in TOE, which gives
T^6/Z_3 "3 fixed points = 3 generations": the torus orbifold has 27, and the vacuum
forced by the W(3,3) twist has no Standard Model generations at all.

SCOPE.  The model SU(9) x SO(14) x U(1) and the level-matching rule are classical
(late-1980s Z_3 orbifold classification). New relative to the corpus: identifying the
W(3,3) twist as the SU(9) shift, its anomaly class a = 1, the uniqueness of its
heterotic partner, and the anomaly certificate built from the substrate side.
"""

import argparse
import itertools
import json
import os
import random
from fractions import Fraction

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = 36  # all vectors in x6 coordinates; real inner product = integer dot / 36


def e8_roots6():
    out = []
    for i, j in itertools.combinations(range(8), 2):
        for a in (6, -6):
            for b in (6, -6):
                v = [0] * 8
                v[i], v[j] = a, b
                out.append(v)
    for s in itertools.product((3, -3), repeat=8):
        if sum(1 for c in s if c < 0) % 2 == 0:
            out.append(list(s))
    return np.array(out, dtype=np.int64)


def e8_vectors_doubled(maxnorm):
    """E8 vectors of norm <= maxnorm in doubled coordinates z (real vector z/2)."""
    out = []
    lim = int(np.floor(np.sqrt(maxnorm)))
    for w in itertools.product(range(-lim, lim + 1), repeat=8):
        if sum(c * c for c in w) <= maxnorm and sum(w) % 2 == 0:
            out.append([2 * c for c in w])
    odd = [c for c in range(-5, 6, 2) if c * c <= 4 * maxnorm]
    for z in itertools.product(odd, repeat=8):
        if sum(c * c for c in z) <= 4 * maxnorm and sum(z) % 4 == 0:
            out.append(list(z))
    return np.array(out, dtype=np.int64)


def in_e8_doubled(z):
    return (all(c % 2 == 0 for c in z) or all(c % 2 != 0 for c in z)) and sum(z) % 4 == 0


def classify_shift(V6, R6, lam6):
    """fixed-root count, anomaly class, twisted ground weight and multiplicity."""
    d = R6 @ V6
    fixed = int(np.sum(d % S == 0))
    a = int((V6 @ V6) // 8) % 3              # |3V|^2/2 = |z|^2/8 with z = V6
    norms = np.sum((lam6 + V6) ** 2, axis=1)
    mn = norms.min()
    return fixed, a, Fraction(int(mn), 2 * S), int(np.sum(norms == mn))


def root_components(R):
    """split a simply-laced root set into simple components."""
    n = len(R)
    G = (R @ R.T) != 0
    seen, comps = [False] * n, []
    for i in range(n):
        if seen[i]:
            continue
        stack, comp = [i], []
        seen[i] = True
        while stack:
            k = stack.pop()
            comp.append(k)
            for j in np.nonzero(G[k])[0]:
                if not seen[j]:
                    seen[j] = True
                    stack.append(j)
        comps.append(R[sorted(comp)])
    return comps


def comp_name(C):
    n = len(C)
    rank = np.linalg.matrix_rank(C.astype(float))
    table = {(72, 8): "A8", (6, 2): "A2", (72, 6): "E6", (126, 7): "E7", (84, 7): "D7", (240, 8): "E8"}
    return table.get((n, rank), "?%d/%d" % (n, rank))


def frac_basis(R):
    """greedy basis of span(R) and the inverse Gram matrix, in Fractions."""
    basis = []
    M = []
    for r in R:
        cand = M + [list(map(Fraction, r))]
        if np.linalg.matrix_rank(np.array(cand, dtype=float)) > len(M):
            M = cand
            basis.append(r)
        if len(basis) == np.linalg.matrix_rank(R.astype(float)):
            break
    B = np.array(basis, dtype=np.int64)
    G = [[Fraction(int(x @ y), S) for y in B] for x in B]
    n = len(G)
    A = [row[:] + [Fraction(int(i == j)) for j in range(n)] for i, row in enumerate(G)]
    for c in range(n):
        p = next(r for r in range(c, n) if A[r][c] != 0)
        A[c], A[p] = A[p], A[c]
        piv = A[c][c]
        A[c] = [x / piv for x in A[c]]
        for r in range(n):
            if r != c and A[r][c] != 0:
                f = A[r][c]
                A[r] = [x - f * y for x, y in zip(A[r], A[c])]
    Ginv = [row[n:] for row in A]
    return B, Ginv


def proj_pair(B, Ginv, w1, w2):
    b1 = [Fraction(int(x @ w1), S) for x in B]
    b2 = [Fraction(int(x @ w2), S) for x in B]
    return sum(b1[i] * Ginv[i][j] * b2[j] for i in range(len(B)) for j in range(len(B)))


def model(V1, V2, R6, lam6, sign=1):
    """massless left-chiral spectrum of E8 x E8 on T^6/Z_3 with gauge shift (V1, V2)."""
    V = np.concatenate([V1, V2])
    Z8 = np.zeros_like(R6)
    R16 = np.vstack([np.hstack([R6, Z8]), np.hstack([Z8, R6])])
    d = R16 @ V
    gauge = R16[d % S == 0]
    matter_mask = (d % S) == ((sign * 12) % S)      # P.V = sign/3 mod 1  (1/3 = 12/36)
    untw = R16[matter_mask]
    # twisted: cosets E8 + V_i with weight <= 2/3, combined with oscillators
    def coset(Vi):
        W = lam6 + Vi
        h = np.sum(W ** 2, axis=1)
        keep = h <= 2 * S * 2 // 3                  # P^2/2 <= 2/3  <=>  |P6|^2 <= 48
        return W[keep], h[keep]
    W1, h1 = coset(V1)
    W2, h2 = coset(V2)
    osc = {0: 1, 24: 3, 48: 9}                     # N in units of 1/36 of P^2/2 ... P^2/2 = |P6|^2/72
    tw = []
    for i in range(len(W1)):
        for j in range(len(W2)):
            tot = int(h1[i] + h2[j])                # |P6|^2; P^2/2 = tot/72; need tot/72 + N = 2/3 -> tot = 48 - 72N
            for Nk, m in ((0, 1), (1, 3), (2, 9)):
                if tot == 48 - 24 * Nk:
                    tw.append((np.concatenate([W1[i], W2[j]]), m, Nk))
    return gauge, untw, tw


def multiplets(states, gauge):
    """connected components of weight sets under the gauge roots (irreducible multiplets)."""
    key = {tuple(s): i for i, s in enumerate(states)}
    seen, comps = set(), []
    for i in range(len(states)):
        if i in seen:
            continue
        stack, comp = [i], []
        seen.add(i)
        while stack:
            k = stack.pop()
            comp.append(k)
            for r in gauge:
                j = key.get(tuple(states[k] + r))
                if j is not None and j not in seen:
                    seen.add(j)
                    stack.append(j)
        comps.append([states[k] for k in comp])
    return comps


def analyse(name, V1, V2, R6, lam6, sign, rng, verbose=True):
    gauge, untw, tw = model(V1, V2, R6, lam6, sign)
    comps = root_components(gauge)
    names = sorted(comp_name(C) for C in comps)
    rank_ss = int(np.linalg.matrix_rank(gauge.astype(float))) if len(gauge) else 0
    n_u1 = 16 - rank_ss
    # U(1) directions: exact null space of the gauge roots (rational), from numpy SVD then rationalised by symmetry
    u1 = []
    if n_u1:
        _, _, vt = np.linalg.svd(gauge.astype(float))
        for row in vt[rank_ss:]:
            row = row / row[np.argmax(np.abs(row))]
            u1.append(np.array([Fraction(x).limit_denominator(12) for x in row]))
    # chiral multiplets with multiplicity
    mult = []
    for c in multiplets(list(untw), gauge):
        mult.append((c, 3, "untwisted"))
    twk = {}
    for P, m, Nk in tw:
        twk.setdefault((Nk, m), []).append(P)
    for (Nk, m), sts in twk.items():
        for c in multiplets(sts, gauge):
            mult.append((c, 27 * m, "twisted N=%d/3" % Nk))
    summary = []
    bases = [frac_basis(C) for C in comps]
    for c, m, sec in mult:
        dims = []
        for B, Ginv in bases:
            projs = {tuple(proj_pair(B, Ginv, w, b) for b in B) for w in c}
            dims.append(len(projs))
        charges = [sum(Fraction(int(x), 6) * y for x, y in zip(c[0], t)) for t in u1]
        summary.append({"sector": sec, "multiplicity": m, "states": len(c),
                        "dims": dict(zip([comp_name(C) for C in comps], dims)),
                        "charges": [str(q) for q in charges]})
    # cubic anomaly of each SU(n) factor: sum over states of (w.x)^3 for random x in the factor's span
    cubic = {}
    for C in comps:
        nm = comp_name(C)
        if not nm.startswith("A"):
            continue
        vals = []
        for _ in range(3):
            x = sum(rng.randint(-5, 5) * r for r in C[rng.sample(range(len(C)), min(len(C), 12))])
            tot = 0
            for c, m, _ in mult:
                tot += m * sum(int(w @ x) ** 3 for w in c)
            vals.append(tot)
        cubic[nm] = vals
    # Green-Schwarz traces for each U(1)
    gs = []
    for t in u1:
        tt = sum(y * y for y in t)
        kq = 2 * tt
        trQ = trQ3 = Fraction(0)
        mixed = {}
        for c, m, _ in mult:
            for w in c:
                q = sum(Fraction(int(x), 6) * y for x, y in zip(w, t))
                trQ += m * q
                trQ3 += m * q ** 3
        for C in comps:
            alpha = C[0]
            val = Fraction(0)
            for c, m, _ in mult:
                for w in c:
                    q = sum(Fraction(int(x), 6) * y for x, y in zip(w, t))
                    val += m * q * Fraction(int(w @ alpha) ** 2, S * S)
            mixed[comp_name(C)] = val / 4
        gs.append({"t": [str(y) for y in t], "TrQ/24": trQ / 24, "TrQ3/(3k)": trQ3 / (3 * kq), "mixed": mixed})
    if verbose:
        print("  %s (convention %+d): gauge %s x U(1)^%d" % (name, sign, "x".join(names), n_u1))
        agg = {}
        for s_ in summary:
            k_ = (s_["sector"], tuple(sorted(s_["dims"].items())), tuple(s_["charges"]))
            agg[k_] = agg.get(k_, 0) + s_["multiplicity"]
        for (sec, dims, ch), m in sorted(agg.items(), key=lambda z: (z[0][0], str(z[0][1]))):
            print("     %3d x %s charges %s  [%s]" % (m, dict(dims), list(ch), sec))
        print("     cubic SU(n) anomaly samples:", cubic)
        for g_ in gs:
            print("     GS: TrQ/24 =", g_["TrQ/24"], " TrQ^3/3k =", g_["TrQ3/(3k)"],
                  " mixed =", {k: str(v) for k, v in g_["mixed"].items()})
    return {"gauge": names, "u1": n_u1, "summary": summary, "cubic": cubic, "gs": gs, "mult": mult, "comps": comps}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    rng = random.Random(3)
    checks = {}
    R6 = e8_roots6()
    U = e8_vectors_doubled(8)
    checks["e8_theta_to_norm8"] = sorted(np.unique(np.sum(U ** 2, axis=1) // 4, return_counts=True)[1].tolist()) == \
        sorted([1, 240, 2160, 6720, 17520])
    lamD = e8_vectors_doubled(4)
    lam6 = 3 * lamD

    # 1. classification of order-3 shifts
    classes = {}
    for z in U:
        V6 = z                                      # V = u/3 with u = z/2  ->  6V = z
        d = R6 @ V6
        fixed = int(np.sum(d % S == 0))
        a = int(z @ z // 8) % 3
        classes.setdefault((fixed, a), []).append(z)
    table = {}
    for (fixed, a), zs in sorted(classes.items()):
        reps = [zs[0]] + [zs[i] for i in rng.sample(range(len(zs)), min(20, len(zs) - 1))]
        data = {classify_shift(np.array(r), R6, lam6) for r in reps}
        assert len(data) == 1, (fixed, a, data)
        _, _, w, mlt = data.pop()
        best = min(zs, key=lambda r: int(r @ r))
        table[(fixed, a)] = {"dim": 8 + fixed, "weight": w, "states": mlt, "rep6": [int(c) for c in best], "count": len(zs)}
    print("order-3 shifts of E8 (V = u/3, |u|^2 <= 8):")
    names = {240: "E8", 78: "E6+A2", 126: "E7+U1", 72: "A8", 84: "D7+U1"}
    for (fixed, a), t in sorted(table.items(), key=lambda kv: -kv[1]["dim"]):
        print("  %-6s dim %3d  anomaly a=%d  twisted weight %-4s x %d states   (%d shifts)" % (
            names.get(fixed, "?"), t["dim"], a, t["weight"], t["states"], t["count"]))
    sig = {names[f]: (a, t["dim"], str(t["weight"]), t["states"]) for (f, a), t in table.items()}
    checks["five_kac_classes"] = sorted(t["dim"] for t in table.values()) == [80, 86, 92, 134, 248] and len(table) == 5
    checks["anomaly_classes"] = {k: v[0] for k, v in sig.items()} == {"E8": 0, "E6+A2": 0, "E7+U1": 1, "A8": 1, "D7+U1": 2}
    checks["w33_twist_is_A8_class"] = sig["A8"][1:] == (80, "4/9", 9)
    rep = {names[f]: np.array(t["rep6"]) for (f, a), t in table.items()}

    # 2. level matching on T^6/Z_3
    v2 = Fraction(2, 3)
    pairs = []
    for x, y in itertools.combinations_with_replacement(sorted(rep), 2):
        V2sum = Fraction(int(rep[x] @ rep[x]) + int(rep[y] @ rep[y]), S)
        ok = (3 * (V2sum - v2)) % 2 == 0
        assert ok == ((sig[x][0] + sig[y][0]) % 3 == 0)
        if ok:
            pairs.append((x, y))
    print("modular-invariant T^6/Z3 class pairs:", pairs)
    checks["five_level_matched_pairs"] = len(pairs) == 5
    checks["A8_unique_partner_D7U1"] = [p for p in pairs if "A8" in p] == [("A8", "D7+U1")]
    checks["e8k_diagonal_A8_consistent_iff_3_divides_k"] = all(
        ((k * sig["A8"][0]) % 3 == 0) == (k % 3 == 0) for k in range(1, 10))

    # 3. fixed points of the A2^3 torus
    th = np.array([[0, -1], [1, -1]])               # order-3 rotation of A2 in a root basis
    TH = np.kron(np.eye(3, dtype=int), th)
    checks["t6z3_fixed_points_27"] = int(round(np.linalg.det(np.eye(6) - TH))) == 27 and \
        np.array_equal(np.linalg.matrix_power(TH, 3), np.eye(6, dtype=int))

    # control: standard embedding (E6+A2, E8), both conventions
    zero = np.zeros(8, dtype=np.int64)
    ctrl = {}
    for sign in (1, -1):
        res = analyse("standard embedding", rep["E6+A2"], zero, R6, lam6, sign, rng)
        e6 = next(C for C in res["comps"] if comp_name(C) == "E6")
        B, Ginv = frac_basis(e6)
        ref = None
        net = 0
        for c, m, _ in res["mult"]:
            projs = {tuple(proj_pair(B, Ginv, w, b) for b in B) for w in c}
            if len(projs) != 27:
                continue
            w0 = c[0]
            if ref is None:
                ref = w0
            cls = proj_pair(B, Ginv, w0, ref) % 1
            n27 = len(c) // 27
            net += m * n27 * (1 if cls == Fraction(1, 3) else -1)
        ctrl[sign] = {"net27": abs(net), "su3cubic": res["cubic"].get("A2")}
    print("  control nets:", {k: v["net27"] for k, v in ctrl.items()})
    conv = [s for s in (1, -1) if ctrl[s]["net27"] == 36 and all(x == 0 for x in ctrl[s]["su3cubic"])]
    checks["control_36_generations_and_su3_free_fixes_convention"] = len(conv) == 1
    sign = conv[0] if conv else 1

    # 4-5. the W(3,3) twist vacuum
    res = analyse("W(3,3) twist (A8, D7+U1)", rep["A8"], rep["D7+U1"], R6, lam6, sign, rng)
    agg = {}
    for s_ in res["summary"]:
        k_ = (s_["sector"].split()[0], s_["dims"]["A8"], s_["dims"]["D7"], tuple(s_["charges"]))
        agg[k_] = agg.get(k_, 0) + s_["multiplicity"]
    expected = {("untwisted", 84, 1): 3, ("twisted", 9, 1): 27, ("untwisted", 1, 64): 3, ("untwisted", 1, 14): 3}
    got = {(k[0], k[1], k[2]): v for k, v in agg.items()}
    checks["gauge_su9_so14_u1"] = res["gauge"] == ["A8", "D7"] and res["u1"] == 1
    checks["spectrum_3x84_27x9_3x64_3x14"] = got == expected
    checks["su9_cubic_anomaly_vanishes"] = all(x == 0 for x in res["cubic"]["A8"])
    g0 = res["gs"][0]
    vals = {g0["TrQ/24"], g0["TrQ3/(3k)"], g0["mixed"]["A8"], g0["mixed"]["D7"]}
    checks["green_schwarz_universal"] = len(vals) == 1 and vals.pop() != 0
    gsval = str(g0["TrQ/24"])

    # 6. teeth: opposite convention and level-mismatched pair
    wrong = analyse("W(3,3) twist, opposite convention", rep["A8"], rep["D7+U1"], R6, lam6, -sign, rng, verbose=False)
    mism = analyse("mismatched (A8, E8)", rep["A8"], zero, R6, lam6, sign, rng)
    checks["teeth_opposite_convention_anomalous"] = any(x != 0 for x in wrong["cubic"]["A8"])
    checks["teeth_mismatched_pair_anomalous"] = any(x != 0 for x in mism["cubic"]["A8"])

    for k, v in checks.items():
        print("  %-55s %s" % (k, v))
    valid = all(checks.values())
    print("VALID:", valid)
    if args.write:
        out = {
            "claim": "The W(3,3) twist of E8 (68df33f) is the order-3 shift of class A8, Z3 anomaly a=1; on T^6/Z3 its unique "
                     "modular-invariant partner is D7+U1, giving SU(9)xSO(14)xU(1) with 3(84)+27(9bar)+3(64)+3(14), SU(9)^3-free "
                     "and Green-Schwarz universal.",
            "classes": {k: {"anomaly": v[0], "dim": v[1], "twistedWeight": v[2], "groundStates": v[3]} for k, v in sig.items()},
            "levelMatchedPairs": pairs,
            "spectrum": {"%s (%d,%d) Q=%s" % (k[0], k[1], k[2], ",".join(k[3])): v for k, v in agg.items()},
            "greenSchwarz": gsval,
            "chiralityConvention": sign,
            "checks": checks,
            "valid": valid,
            "sources": ["Holotrade 68df33f the_twisted_sectors_carry_the_rung_geometries.py",
                        "Dixon-Harvey-Vafa-Witten orbifold rules; Ibanez-Mas-Nilles-Quevedo Z3 gauge embeddings; "
                        "Kobayashi-Nakano anomalous U(1) universality"],
        }
        path = os.path.join(ROOT, "data", "w33_twist_su9_heterotic_embedding.json")
        with open(path, "w") as f:
            json.dump(out, f, indent=1, default=str)
        print("written", path)


if __name__ == "__main__":
    main()
