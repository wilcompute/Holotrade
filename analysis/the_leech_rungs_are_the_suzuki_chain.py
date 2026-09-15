#!/usr/bin/env python3
"""
THE LEECH RUNGS OF THE TOWER ARE THE SUZUKI CHAIN, AND THE d = 9 RUNG DOES NOT EXIST.

W33-Theory Passes 7293-7294 mapped a lattice tower by arithmetic alone:
det(I - M) = Phi_d(1)^k, so the quotient L/(1-M)L is computable before any
lattice is built. They marked one row "THE ONE TO LOOK AT": the Leech lattice
at d = 9, of rank 4 over Z[zeta_9], quotient F_3^4, 40 projective points,
196560/80 = 2457 minimal vectors per class, "the SAME target as E8 at d=3".
It was recorded as untested, with the Leech lattice not built. This file
builds it and answers.

1. THE d = 9 ROW IS EMPTY.  A Z[zeta_9]-structure needs an isometry g of the
   Leech lattice with characteristic polynomial Phi_9^4, so trace(g) = 0 and
   trace(g^3) = 4 * (-3) = -12. In the character table of Co0 = 2.Co1 (GAP
   4.16 CTblLib; co0_fixed_point_free_classes.g), every element of order 9
   has trace(g^3) = -3. For 9b (trace 0) that forces the characteristic
   polynomial Phi_9^3 Phi_3^2 Phi_1^2, and 9a and 9c are no better. So the
   Leech lattice has no Z[zeta_9]-structure. The same table shows which
   fixed-point-free rungs do exist: 3a (Phi_3^12), 4a (Phi_4^12),
   5a (Phi_5^6), 7a (Phi_7^4) and 13a (Phi_13^2).

2. THE GEOMETRY IS ALWAYS SYMPLECTIC (PARITY LEMMA).  Let L be a unimodular
   lattice and g a fixed-point-free isometry of odd prime order p, so L is a
   Z[zeta]-module. There is a Hermitian h with <x,y> = Tr h(x,y), namely
   h = (1/p) sum_k <x, g^k y> zeta^k. It takes values in the inverse
   different pi^-(p-2). delta = (zeta - zeta^-1)^(p-2) generates the
   different and satisfies sigma(delta) = -delta. So delta*h is
   anti-Hermitian, Z[zeta]-valued, and unimodular. Its reduction mod
   pi = 1 - zeta is a nondegenerate ALTERNATING form on L/piL = F_p^m.
   (For Q(zeta_{p^k}) the different exponent p^(k-1)((p-1)k - 1) is always
   odd, so the conclusion holds for every odd prime power.) The quotient
   geometry is therefore W(m-1, p), whatever the lattice. The form is built
   explicitly here, and checked to be alternating, well defined on L/piL, and
   nondegenerate.

3. THE RUNGS, COMPUTED.  The Leech lattice is built from the Golay code, with
   generators PSL(2,23), a sign change and Conway's xi_T; each generator is
   checked exactly to preserve all 196560 minimal vectors. For each d a
   fixed-point-free element is found and verified (it preserves the minimal
   vectors, and 1 + g + ... + g^(d-1) = 0).
     d = 7: L/piL = F_7^4, i.e. W(3,7). All 2400 nonzero classes are hit,
       720 with 77 minimal vectors and 1680 with 84, constant on projective
       points. The 120 lighter points form a 15-tight set: 21 of them are
       collinear with each of its points, 15 with each other point. It meets
       lines in 0/1/4 points (70/120/210 lines) and contains no line. Its
       stabiliser in PSp(4,7) is A7 (GAP, recorded), with orbits 120 + 280.
     d = 5: F_5^6, i.e. W(5,5). The 3906 points split 1890 + 2016 (10 vs 15
       per class) = 15*126 + 16*126, and the sets are checked as 15- and
       16-ovoids.
     d = 3: F_3^12, i.e. W(11,3). Only 65520 classes are hit, 3 vectors each,
       so the unit classes of minimal vectors embed as 32760 = 90*364
       projective points. The 90-tight parameters are checked on the set and
       on a sample outside.
     d = 13: F_13^2, i.e. PG(1,13). 936 minimal vectors lie in piL, and the
       14 points split 6 + 8 (1157 vs 1170 per class).
   Controls on E8: d = 3 gives W(3,3) = SRG(40,12,2,4), uniformly 3 roots per
   class; d = 5 gives PG(1,5), uniformly 10.

4. WHAT THIS IS.  The splits are exactly the two-orbit intriguing sets of
   Feng-Xiang (arXiv:2310.09460, Tables 1.6 and 1.9): 2.Suz on W(11,3)
   (90, 640-tight), 2.J2 on W(5,5) (15, 16-ovoids), 2.A7 on W(3,7)
   (15, 35-tight). The acting groups are the centralisers of 3a, 5a, 7a in
   Co0 -- the Suzuki chain. So above E8 the tower does not return to
   W(3,3). Its Leech rungs are W(11,3), W(5,5), W(3,7), PG(1,13), and the
   minimal vectors of the Leech lattice separate the Suzuki-chain orbits.

5. THE P1021 FIBRATION, ONE RUNG UP.  W33-Theory P1021 has a 6:1
   Sp(4,3)-equivariant fibration from the 240 E8 roots onto the 40 points of
   W(3,3), with fibre the Eisenstein units Z6. The d = 3 Leech rung is the same
   construction. Each nonzero F_3-class holds exactly 3 minimal vectors; they
   are {v, wv, w^2 v}, since w = g is congruent to 1 mod pi. So a projective
   point carries the Z6 unit orbit, and the Leech lattice fibres 6:1 onto
   32760 points of W(11,3). The image is not the whole space: it is the
   90-tight 2.Suz-orbit. Top to bottom: E8 -> W(3,3), all 40 points,
   Sp(4,3); Leech -> W(11,3), a 90-tight set of 32760, 2.Suz. In the corpus's
   own dictionary (F_3^(2n) with its symplectic form = n-qutrit Pauli phase
   space), the second is a Suz-invariant tight family of six-qutrit Pauli
   classes. That is a reading of the certified combinatorics, not a physical
   claim.

PRIOR ART AND SCOPE.  Complex and cyclotomic structures on the Leech lattice
and the Suzuki chain are classical (Lindsey; Tits; Wilson, "The complex Leech
lattice and maximal subgroups of the Suzuki group", 1983; Conway-Sloane). The
intriguing sets are Feng-Xiang's. The parity lemma is standard Hermitian
lattice theory and is stated with proof, not claimed. What is new relative to
the corpus: the refutation of Pass 7294's d = 9 row, the corrected rung map,
and the certificate that the Leech minimal vectors realise the Feng-Xiang
splits. No physics is asserted.
"""

import argparse
import itertools
import json
import os
import random
from collections import Counter
from fractions import Fraction

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N = 24

# GAP 4.16, CharacterTable("2.Co1"), the 24-dimensional character: values chi(g^k) for k | d
CO0_TRACES = {
    "3a": [-12, 24], "3b": [6, 24], "3c": [-3, 24], "3d": [0, 24],
    "5a": [-6, 24], "5b": [4, 24], "5c": [-1, 24],
    "7a": [-4, 24], "7b": [3, 24],
    "9a": [-3, -3, 24], "9b": [0, -3, 24], "9c": [3, -3, 24],
    "13a": [-2, 24],
}


def cyclotomic_multiplicities_order9(t1, t3):
    """dims: 6a (Phi_9) + 2b (Phi_3) + c (Phi_1) = 24; trace = -b + c; trace(g^3) = -3a + 2b + c."""
    sols = []
    for a in range(5):
        for b in range(13):
            c = 24 - 6 * a - 2 * b
            if c >= 0 and -b + c == t1 and -3 * a + 2 * b + c == t3:
                sols.append((a, b, c))
    return sols


def golay():
    gpoly = [1, 0, 1, 0, 1, 1, 1, 0, 0, 0, 1, 1]
    basis = []
    for s in range(12):
        w = [0] * 23
        for k, c in enumerate(gpoly):
            if c:
                w[(k + s) % 23] = 1
        w = w + [sum(w) % 2]
        basis.append(sum(1 << i for i, b in enumerate(w) if b))
    code = {0}
    for b in basis:
        code |= {c ^ b for c in code}
    return code, basis


def leech():
    code, basis = golay()
    octads = [c for c in code if bin(c).count("1") == 8]
    mins = []
    for o in octads:
        idx = [i for i in range(N) if o >> i & 1]
        for signs in itertools.product((1, -1), repeat=7):
            last = 1 if signs.count(-1) % 2 == 0 else -1
            v = [0] * N
            for i, s in zip(idx, list(signs) + [last]):
                v[i] = 2 * s
            mins.append(v)
    for c in code:
        for i in range(N):
            v = [1 if c >> j & 1 else -1 for j in range(N)]
            v[i] = -3 if v[i] == 1 else 3
            if sum(v) % 8 == 4:
                mins.append(v)
    for i, j in itertools.combinations(range(N), 2):
        for a in (4, -4):
            for b in (4, -4):
                v = [0] * N
                v[i], v[j] = a, b
                mins.append(v)
    M = np.array(mins, dtype=np.int64)
    inf = 23

    def mob(a, b, c, d):
        def f(i):
            if i == inf:
                return inf if c % 23 == 0 else (a * pow(c, -1, 23)) % 23
            num, den = (a * i + b) % 23, (c * i + d) % 23
            return inf if den == 0 else (num * pow(den, -1, 23)) % 23
        return [f(i) for i in range(N)]
    gens = []
    for p in (mob(1, 1, 0, 1), mob(2, 0, 0, 1), mob(0, -1, 1, 0)):
        P = np.zeros((N, N))
        for i in range(N):
            P[p[i], i] = 1
        gens.append(P)
    o0 = octads[0]
    gens.append(np.diag([-1.0 if o0 >> i & 1 else 1.0 for i in range(N)]))
    T = [i for i in range(N) if o0 >> i & 1][:4]
    tetrads = [T] + [[i for i in range(N) if o >> i & 1 and i not in T]
                     for o in octads if all(o >> i & 1 for i in T)]
    eta = np.eye(N)
    for t in tetrads:
        for i in t:
            for j in t:
                eta[i, j] -= 0.5
    gens.append(np.diag([-1.0 if i in T else 1.0 for i in range(N)]) @ eta)
    return code, octads, M, gens


def preserves(M, key, A):
    img = np.round(M @ A.T).astype(np.int64)
    return all(tuple(v) in key for v in img)


def cyclotomic_tools(d):
    def polmul(a, b):
        out = [Fraction(0)] * (len(a) + len(b) - 1)
        for i, x in enumerate(a):
            if x:
                for j, y in enumerate(b):
                    out[i + j] += x * y
        return out

    def red(a):
        b = [Fraction(0)] * d
        for i, x in enumerate(a):
            b[i % d] += x
        return [b[k] - b[d - 1] for k in range(d - 1)]
    base = [Fraction(0)] * d
    base[1] += 1
    base[d - 1] -= 1
    delta = [Fraction(1)]
    for _ in range(d - 2):
        delta = red(polmul(delta, base)) + [Fraction(0)]
    delta = red(delta)
    lam = []
    for k in range(d):
        c = [Fraction(0)] * d
        c[k] = Fraction(1, d)
        prod = red(polmul(red(c), delta))
        lam.append(sum(prod))
    return lam, polmul, red, delta


def find_element(gens, M, key, d, trace, scale, seed):
    n = gens[0].shape[0]
    I = np.eye(n)
    rng = random.Random(seed)

    def rnd(A):
        return np.round(A * scale) / scale
    for _ in range(200000):
        A = I
        for _ in range(rng.randint(8, 30)):
            A = rnd(A @ gens[rng.randrange(len(gens))])
        C, o = A.copy(), None
        for k in range(1, 121):
            if np.allclose(C, I, atol=1e-6):
                o = k
                break
            C = rnd(C @ A)
        if not o or o % d:
            continue
        g = rnd(np.linalg.matrix_power(A, o // d))
        if abs(np.trace(g) - trace) < 1e-6:
            pw = [I]
            for _ in range(d):
                pw.append(rnd(pw[-1] @ g))
            if np.allclose(pw[d], I) and np.allclose(sum(pw[:d]), 0) and preserves(M, key, g):
                return g, pw
    raise RuntimeError("no element found")


def reduce_mod_pi(M, pw, d, ipscale, seed):
    """classes of the rows of M in L/piL = F_d^m, via the alternating form."""
    lam, polmul, red, delta = cyclotomic_tools(d)
    den = 1
    for v in lam:
        den = den * v.denominator // np.gcd(den, v.denominator)
    lamI = [int(v * den) for v in lam]
    W = sum(lamI[k] * pw[k] for k in range(d))
    rng = random.Random(seed)

    def form(X, y):
        num = np.round(X @ (W @ y)).astype(np.int64)
        assert (num % (ipscale * den) == 0).all()
        return (num // (ipscale * den)) % d
    n = M.shape[1]
    m = n // (d - 1)
    sample = [M[rng.randrange(len(M))] for _ in range(10)]
    alternating = all(form(np.array([v]), v)[0] == 0 for v in sample)
    gI = np.eye(n) - pw[1]
    welldefined = all(form(np.array([np.round(gI @ a).astype(np.int64)]), b)[0] == 0 for a in sample for b in sample)
    from sympy import GF, Matrix
    from sympy.polys.matrices import DomainMatrix
    while True:
        bas = [M[rng.randrange(len(M))] for _ in range(m)]
        G = [[int(form(np.array([a]), b)[0]) for b in bas] for a in bas]
        if DomainMatrix([[GF(d)(v) for v in r] for r in G], (m, m), GF(d)).rank() == m:
            break
    Gi = np.array(Matrix(G).inv_mod(d).tolist(), dtype=np.int64)
    P = np.stack([form(M, b) for b in bas], axis=1)
    C = (P @ Gi) % d
    return C, np.array(G) % d, alternating and welldefined


def proj_key(v, d):
    i = next(k for k, a in enumerate(v) if a)
    inv = pow(int(v[i]), -1, d)
    return tuple((int(a) * inv) % d for a in v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    checks, data = {}, {}

    # 1. no Z[zeta_9]-structure
    nine = {c: cyclotomic_multiplicities_order9(*CO0_TRACES[c][:2]) for c in ("9a", "9b", "9c")}
    checks["noPhi9FourthPower"] = all((4, 0, 0) not in s for s in nine.values())
    checks["class9bIsPhi9cubed"] = nine["9b"] == [(3, 2, 2)]
    fpf = {"3a": -12, "5a": -6, "7a": -4, "13a": -2}
    checks["fixedPointFreeClassesExist"] = all(CO0_TRACES[c][0] == t for c, t in fpf.items())
    data["order9CharpolyMultiplicities"] = {c: s for c, s in nine.items()}

    # Leech
    code, octads, M, gens = leech()
    key = {tuple(v): i for i, v in enumerate(M)}
    checks["golay"] = len(code) == 4096 and sorted({bin(c).count("1") for c in code}) == [0, 8, 12, 16, 24]
    checks["leechMinimal196560"] = len(M) == 196560 and (np.einsum("ij,ij->i", M, M) == 32).all()
    checks["generatorsPreserveMinimalVectors"] = all(preserves(M, key, A) for A in gens)

    rungs = {}
    for d, tr in ((7, -4), (5, -6), (3, -12), (13, -2)):
        g, pw = find_element(gens, M, key, d, tr, 8, d)
        C, G, ok_form = reduce_mod_pi(M, pw, d, 8, d)   # <x,y> = x.y/8 in Leech coordinates
        m = C.shape[1]
        cnt = Counter(tuple(r) for r in C.tolist())
        zero = cnt.pop(tuple([0] * m), 0)
        hist = sorted(Counter(cnt.values()).items())
        pc, const = {}, True
        for c, k in cnt.items():
            p = proj_key(c, d)
            if p in pc and pc[p] != k:
                const = False
            pc[p] = k
        rungs[d] = {"m": m, "formAlternatingWellDefinedNondegenerate": ok_form, "zeroClass": zero,
                    "classesHit": len(cnt), "classes": d ** m - 1, "countHistogram": hist,
                    "constantOnProjectivePoints": const,
                    "projectiveSplit": sorted(Counter(pc.values()).items())}
        if d == 7:
            pts = sorted({proj_key(v, 7) for v in itertools.product(range(7), repeat=4) if any(v)})
            light = min(set(pc.values()))
            S = [i for i, p in enumerate(pts) if pc.get(p) == light]
            V = np.array(pts)
            orth = ((V @ G @ V.T) % 7 == 0)
            np.fill_diagonal(orth, False)
            Sset = set(S)
            inS = np.zeros(400, dtype=bool)
            inS[S] = True
            nS = orth[:, inS].sum(axis=1)
            lines = {frozenset([a, b] + [c for c in np.nonzero(orth[a] & orth[b])[0]])
                     for a in range(400) for b in np.nonzero(orth[a])[0]}
            lines = {L for L in lines if len(L) == 8}
            rungs[7]["lightPoints"] = len(S)
            rungs[7]["tightInside"] = sorted(set(nS[inS].tolist()))
            rungs[7]["tightOutside"] = sorted(set(nS[~inS].tolist()))
            rungs[7]["lineIntersections"] = sorted(Counter(len(L & Sset) for L in lines).items())
            rungs[7]["lines"] = len(lines)
        if d == 5:
            pts = list(pc)
            light = min(set(pc.values()))
            V = np.array(pts, dtype=np.int64)
            inO = np.array([pc[p] == light for p in pts])
            A = (V @ G) % 5
            counts_in = ((A @ V[inO].T) % 5 == 0).sum(axis=1)
            counts_out = ((A @ V[~inO].T) % 5 == 0).sum(axis=1)
            rungs[5]["lightPoints"] = int(inO.sum())
            rungs[5]["perpCountsInLight"] = sorted(set(counts_in[inO].tolist()))
            rungs[5]["perpCountsInLightFromOutside"] = sorted(set(counts_in[~inO].tolist()))
            rungs[5]["perpCountsInHeavy"] = sorted(set(counts_out[~inO].tolist()))
            rungs[5]["perpCountsInHeavyFromLight"] = sorted(set(counts_out[inO].tolist()))
        if d == 3:
            Spts = np.array(sorted(pc), dtype=np.int64)
            A = (Spts @ G) % 3
            inside = set()
            for s in range(0, len(Spts), 250):
                inside |= set((((A[s:s + 250] @ Spts.T) % 3) == 0).sum(axis=1).tolist())
            rng = random.Random(3)
            Sk = set(map(tuple, Spts.tolist()))
            outs = []
            while len(outs) < 300:
                v = tuple(rng.randrange(3) for _ in range(12))
                if any(v):
                    p = proj_key(v, 3)
                    if p not in Sk:
                        outs.append(p)
            O = np.array(outs, dtype=np.int64)
            outside = set((((O @ G % 3) @ Spts.T) % 3 == 0).sum(axis=1).tolist())
            rungs[3]["perpCountsInside"] = sorted(inside)          # includes the point itself
            rungs[3]["perpCountsOutsideSample"] = sorted(outside)
        print("d=%d: %s" % (d, rungs[d]), flush=True)

    r7, r5, r3, r13 = rungs[7], rungs[5], rungs[3], rungs[13]
    checks["allFormsSymplectic"] = all(r["formAlternatingWellDefinedNondegenerate"] for r in rungs.values())
    checks["d7_W37_120_280"] = (r7["classesHit"] == 2400 and r7["countHistogram"] == [(77, 720), (84, 1680)]
                                and r7["constantOnProjectivePoints"] and r7["projectiveSplit"] == [(77, 120), (84, 280)])
    checks["d7_15tight_0_1_4"] = (r7["tightInside"] == [21] and r7["tightOutside"] == [15] and r7["lines"] == 400
                                  and r7["lineIntersections"] == [(0, 70), (1, 120), (4, 210)])
    checks["d5_W55_1890_2016"] = (r5["classesHit"] == 15624 and r5["countHistogram"] == [(10, 7560), (15, 8064)]
                                  and r5["constantOnProjectivePoints"] and r5["projectiveSplit"] == [(10, 1890), (15, 2016)])
    # m-ovoid in rank 3 (q = 5): |p^perp n O| = (m-1)(q^2+1)+1 for p in O (incl. p), m(q^2+1) otherwise
    checks["d5_15_and_16_ovoids"] = (r5["perpCountsInLight"] == [14 * 26 + 1] and r5["perpCountsInLightFromOutside"] == [15 * 26]
                                     and r5["perpCountsInHeavy"] == [15 * 26 + 1] and r5["perpCountsInHeavyFromLight"] == [16 * 26])
    checks["d3_32760_classes_of_three"] = (r3["zeroClass"] == 0 and r3["countHistogram"] == [(3, 65520)]
                                           and r3["projectiveSplit"] == [(3, 32760)] and 32760 == 90 * 364)
    # i-tight in rank 6 (q = 3): |p^perp n T| = i(q^5-1)/(q-1) + q^5 for p in T (incl. p), i(q^5-1)/(q-1) otherwise
    checks["d3_90tight"] = r3["perpCountsInside"] == [90 * 121 + 243] and r3["perpCountsOutsideSample"] == [90 * 121]
    checks["d13_PG1_13_6_8"] = (r13["zeroClass"] == 936 and r13["countHistogram"] == [(1157, 72), (1170, 96)]
                                and r13["projectiveSplit"] == [(1157, 6), (1170, 8)])

    # E8 controls
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
    e8 = {}
    for d, tr in ((3, -4), (5, -2)):
        g, pw = find_element(refl, R, rkey, d, tr, 4, 100 + d)
        C, G, ok_form = reduce_mod_pi(R, pw, d, 4, 100 + d)   # <x,y> = x.y/4 in doubled E8 coordinates
        cnt = Counter(tuple(r) for r in C.tolist())
        e8[d] = {"form": ok_form, "hist": sorted(Counter(cnt.values()).items()), "zero": cnt.get(tuple([0] * C.shape[1]), 0)}
        if d == 3:
            pts = sorted({proj_key(v, 3) for v in itertools.product(range(3), repeat=4) if any(v)})
            V = np.array(pts)
            orth = (V @ G @ V.T) % 3 == 0
            np.fill_diagonal(orth, False)
            k = set(orth.sum(axis=1).tolist())
            lam = {int((orth[a] & orth[b]).sum()) for a in range(40) for b in range(40) if orth[a, b]}
            mu = {int((orth[a] & orth[b]).sum()) for a in range(40) for b in range(40) if a != b and not orth[a, b]}
            e8[3]["srg"] = [sorted(k), sorted(lam), sorted(mu)]
    checks["controlE8d3_W33_uniform3"] = (e8[3]["form"] and e8[3]["hist"] == [(3, 80)] and e8[3]["zero"] == 0
                                          and e8[3]["srg"] == [[12], [2], [4]])
    checks["controlE8d5_PG15_uniform10"] = e8[5]["form"] and e8[5]["hist"] == [(10, 24)] and e8[5]["zero"] == 0

    ok = all(checks.values())
    for k, v in checks.items():
        print("  %-34s %s" % (k, v))
    print()
    print("VALID: %s" % ok)
    if args.write:
        assert ok, "checks failed -- refusing to write"
        rec = {
            "schema": "holotrade.leech-suzuki-chain-rungs.v1",
            "valid": True,
            "checks": {k: bool(v) for k, v in checks.items()},
            "co0Traces": CO0_TRACES,
            "order9CharpolyMultiplicities(Phi9,Phi3,Phi1)": {c: [list(t) for t in s] for c, s in nine.items()},
            "rungs": {str(d): {k: (v if not isinstance(v, list) else [list(x) if isinstance(x, tuple) else x for x in v])
                               for k, v in r.items()} for d, r in rungs.items()},
            "e8Controls": {str(d): {k: (v if not isinstance(v, list) else [list(x) if isinstance(x, tuple) else x for x in v])
                                    for k, v in r.items()} for d, r in e8.items()},
            "a7SetStabiliser": {"order": 2520, "isomorphicTo": "A7", "orbits": [120, 280], "source": "GAP 4.16 (recorded)"},
            "feng_xiang": {"W(11,3)": "2.Suz, 90 and 640-tight", "W(5,5)": "2.J2, 15 and 16-ovoids",
                           "W(3,7)": "2.A7, 15 and 35-tight", "ref": "arXiv:2310.09460 Tables 1.6, 1.9"},
            "refutes": "W33-Theory Pass 7294: 'LEECH at d=9 gives 40 points -- the same target as E8 at d=3'",
            "boundary": ("lattice, group and intriguing-set facts are classical or Feng-Xiang's; the parity lemma is "
                         "standard; new relative to the corpus: the d=9 refutation, the corrected rung map, and the "
                         "certificate that Leech minimal vectors realise the Suzuki-chain splits. No physics."),
        }
        p = os.path.join(ROOT, "data", "leech_suzuki_chain_rungs.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=2, default=int)
        print("written: %s" % p)


if __name__ == "__main__":
    main()
