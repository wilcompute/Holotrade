#!/usr/bin/env python3
"""
THE BINARY LINE CODE OF A GENERALISED QUADRANGLE OF ODD ORDER HAS MINIMUM
WEIGHT s+1; FOR W(3,q) THE MINIMUM WORDS ARE EXACTLY THE LINES. THIS CLOSES
W33-THEORY'S OPEN LEDGER ROW "CSS distance d = q+1, q >= 5" (Pass 326).

SETTING.  Gamma a finite generalised quadrangle of order (s,t), s odd,
s <= t+1. C = the binary code spanned by the incidence vectors of its lines
(words on points). Adj(p) = points collinear with p, p excluded.

LEMMA (parity).  For every c = sum_{L in X} L in C and every point p,
    |Adj(p) & supp c| = |X|   (mod 2).
Proof: |Adj(p) & L| is s if p is on L and 1 if not (GQ axiom); both are odd.
So lambda(c) := |X| mod 2 depends only on c, and A c = lambda(c) * 1 over F_2.

THEOREM 1.  Every nonzero c in C has weight >= s+1. Hence d(C) = s+1.
Proof, S = supp c, w = |S|.
  lambda = 1: every point has an odd, so positive, number of neighbours in S.
    Counting pairs, w * s(t+1) >= (s+1)(st+1), and (s+1)(st+1) > s * s(t+1)
    because st + s + 1 > s^2 when t >= s-1. So w >= s+1.
  lambda = 0: take x in S. If some line M on x has M & S = {x}, each of the s
    points p of M - {x} is adjacent to x, so has a second neighbour t_p in S,
    off M; t_p determines p (a point off M sees one point of M). So
    w >= s+1. Otherwise all t+1 lines on x meet S again: w >= t+2 >= s+1.

THEOREM 2.  Let s be odd, t >= s, and c in C of weight s+1, with c_p =
|Adj(p) & S|.
  lambda = 1 => S is a line (any such GQ). For a line M,
    sum_{p in M} (c_p - 1) = (s-1)|M & S|, so a line missing S has c_p = 1
    throughout. A point p off S with c_p >= 3 therefore has all t+1 of its
    lines meeting S, in distinct points, so c_p >= t+1 >= s+1 = w. That forces
    c_p = s+1, which is even: a contradiction. So the whole excess
    sum_p (c_p - 1) = (s+1)(s-1) sits on S, where c_x <= s. Equality forces
    c_x = s: S is a clique of size s+1, hence a line (a GQ has no triangles).
  lambda = 0 => S is a partial ovoid in which no point is collinear with
    three points of S. For x in S, the s(t+1) neighbours of x each need a
    second neighbour in T = S - {x}. A point of T covers s-1 of them if it is
    collinear with x (SRG lambda) and t+1 if not (SRG mu). Since t+1 > s-1,
    this forces |T & Adj(x)| = 0 and a partition of Adj(x).
  In W(3,q), q odd, the lambda = 0 case is empty, because every triad has a
  centre: for s !~ t the trace {s,t}^perp is a line of PG(3,q), and u^perp is
  a plane, which meets it. So the words of weight q+1 in the binary code of
  W(3,q) are exactly its (q+1)(q^2+1) lines. (In Q(4,q) some triads have no
  centre, so this step does not transfer; there the conclusion is only
  checked, at q = 3, 5.)

COROLLARY (the CSS family).  Pass 229's sentinel S (the doubly-even part of
the hull) equals C^perp, so CSS(S,S) has logicals C - C^perp. A line is in
C - C^perp (it meets a concurrent line once), so the CSS distance is exactly
q+1. S = C^perp is certified below at q = 3, 5, 7. For larger odd q it follows
from dimensions: S lies in C^perp, and dim C^perp = q(q^2+1)/2 = dim S is the
corpus's rank law (P322) with k = q^2+1 (levi_next5).

INDEPENDENT CHECK.  At q = 3 and 5, for W(3,q) and its dual Q(4,q), every
word of weight <= q+1 is found by meet-in-the-middle on syndromes (all point
sets of size <= (q+1)/2). The words are exactly the lines in all four cases.
At q = 7 the theorems' hypotheses are checked exactly: GQ axiom, parity on
the spanning set, SRG parameters, and the centre of every triad.

PRIOR ART.  Petit & Van de Voorde, "On certain blocking sets and the minimum
weight of the code of generalised polygons" (arXiv:2511.07697), Theorem 7:
d = s+1 for thick GQs of order (s,t), s <= t, over any field with 1 - s != 0.
Over F_2 with s odd, 1 - s = 0, so the binary odd-order case is exactly the
case it excludes. (Their Remark 14 calls the condition automatic; over F_2
with s odd it is not.) Their Corollary 6, <c, c_v> constant, is the analogue
of the parity lemma. Assmus-Key and Bose-Burton cover projective spaces.
Bagchi-Brouwer-Wilbrink (1991) give 2-ranks. Kim-Mellinger-Storme (2007)
study the LDPC (dual) codes, not the row space. In-corpus: Pass 229 (the
family and q = 3), Pass 326 (the audit that left q >= 5 open), P322 (rank law).
"""

import argparse
import itertools
import json
import os
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def w3q(q):
    def nm(v):
        i = next(k for k, x in enumerate(v) if x % q)
        z = pow(v[i] % q, -1, q)
        return tuple((z * x) % q for x in v)

    pts = sorted({nm(v) for v in itertools.product(range(q), repeat=4) if any(v)})
    idx = {p: i for i, p in enumerate(pts)}
    n = len(pts)

    def sf(a, b):
        return (a[0] * b[2] - a[2] * b[0] + a[1] * b[3] - a[3] * b[1]) % q

    lines = set()
    for a in range(n):
        for b in range(a + 1, n):
            if sf(pts[a], pts[b]) == 0:
                L = {a} | {idx[nm(tuple((pts[b][k] + x * pts[a][k]) % q for k in range(4)))] for x in range(q)}
                lines.add(frozenset(L))
    lines = sorted(lines, key=sorted)
    return n, [sum(1 << i for i in L) for L in lines], (pts, sf)


def dual(n, lines):
    m = len(lines)
    return m, [sum(1 << j for j in range(m) if lines[j] >> p & 1) for p in range(n)]


def popcount(x):
    return bin(x).count("1")


def rref(vectors):
    basis = {}
    for v in vectors:
        while v:
            h = v.bit_length() - 1
            if h in basis:
                v ^= basis[h]
            else:
                basis[h] = v
                break
    return basis


def in_span(v, basis):
    while v:
        h = v.bit_length() - 1
        if h not in basis:
            return False
        v ^= basis[h]
    return True


def nullspace(basis_vectors, n):
    """Vectors x in F_2^n with <x, b> = 0 for every b (returns a basis)."""
    rows = list(rref(basis_vectors).values())
    # reduced echelon form
    piv = {}
    for r in sorted(rows, key=lambda v: -v.bit_length()):
        h = r.bit_length() - 1
        for ph in list(piv):
            if piv[ph] >> h & 1:
                piv[ph] ^= r
        for ph in piv:
            if r >> ph & 1:
                r ^= piv[ph]
        piv[h] = r
    free = [j for j in range(n) if j not in piv]
    out = []
    for f in free:
        x = 1 << f
        for ph, r in piv.items():
            if r >> f & 1:
                x |= 1 << ph
        out.append(x)
    return out


def geometry_checks(n, lines, s):
    adj = [0] * n
    for L in lines:
        for p in range(n):
            if L >> p & 1:
                adj[p] |= L
    adj = [adj[p] & ~(1 << p) for p in range(n)]
    ok_orders = all(popcount(L) == s + 1 for L in lines)
    t = sum(1 for L in lines if L & 1) - 1
    ok_orders = ok_orders and all(sum(1 for L in lines if L >> p & 1) == t + 1 for p in range(n))
    gq_axiom = all(popcount(adj[p] & L) == (s if L >> p & 1 else 1) for p in range(n) for L in lines)
    # parity lemma on the spanning set: A L = 1 for every line
    parity = all(all(popcount(adj[p] & L) % 2 == 1 for p in range(n)) for L in lines)
    lam = {popcount(adj[a] & adj[b]) for a in range(n) for b in range(a + 1, n) if adj[a] >> b & 1}
    mu = {popcount(adj[a] & adj[b]) for a in range(n) for b in range(a + 1, n) if not adj[a] >> b & 1}
    return adj, t, {
        "orders": ok_orders, "gqAxiom": gq_axiom, "parityOnLines": parity,
        "srgLambda": sorted(lam), "srgMu": sorted(mu),
    }


def every_triad_has_a_centre(n, adj):
    full = (1 << n) - 1
    for a in range(n):
        for b in range(a + 1, n):
            if adj[a] >> b & 1:
                continue
            trace = adj[a] & adj[b]
            U = 0
            x = trace
            while x:
                low = x & -x
                U |= adj[low.bit_length() - 1]
                x ^= low
            uncovered = full & ~U & ~adj[a] & ~adj[b] & ~(1 << a) & ~(1 << b)
            if uncovered:
                return False
    return True


def css_data(n, lines, q):
    Cb = rref(lines)
    dimC = len(Cb)
    perp = nullspace(list(Cb.values()), n)
    dimP = len(perp)
    self_orth = all(popcount(u & v) % 2 == 0 for u in perp for v in perp)
    doubly_even = self_orth and all(popcount(u) % 4 == 0 for u in perp)
    perp_in_C = all(in_span(v, Cb) for v in perp)
    line_not_in_perp = not in_span(lines[0], rref(perp))
    return {
        "dimC": dimC, "dimCperp": dimP, "rankLawDimC": (q * q + 1) * (q + 2) // 2,
        "CperpInC": perp_in_C, "CperpDoublyEven": doubly_even,
        "k": n - 2 * dimP, "lineIsLogical": line_not_in_perp,
    }, perp


def low_weight_words(n, perp, wmax):
    """All nonzero codewords of weight <= wmax, exhaustively (meet in the middle)."""
    col = [0] * n
    for j, h in enumerate(perp):
        for i in range(n):
            if h >> i & 1:
                col[i] |= 1 << j
    half = (wmax + 1) // 2
    groups = defaultdict(list)
    for r in range(half + 1):
        for sub in itertools.combinations(range(n), r):
            syn = 0
            m = 0
            for i in sub:
                syn ^= col[i]
                m |= 1 << i
            groups[syn].append(m)
    words = set()
    for g in groups.values():
        for i in range(len(g)):
            for j in range(i + 1, len(g)):
                c = g[i] ^ g[j]
                if c and popcount(c) <= wmax:
                    words.add(c)
    return words


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--qs", default="3,5,7")
    args = ap.parse_args()
    report = {}
    ok = True
    for q in map(int, args.qs.split(",")):
        n, lines, _ = w3q(q)
        for name, (N, Ls) in (("W(3,%d)" % q, (n, lines)), ("Q(4,%d)" % q, dual(n, lines))):
            adj, t, geo = geometry_checks(N, Ls, q)
            entry = {"points": N, "lines": len(Ls), "s": q, "t": t, **geo}
            good = (geo["orders"] and geo["gqAxiom"] and geo["parityOnLines"] and t == q
                    and geo["srgLambda"] == [q - 1] and geo["srgMu"] == [q + 1] and N == (q + 1) * (q * q + 1))
            if name.startswith("W"):
                entry["everyTriadHasACentre"] = every_triad_has_a_centre(N, adj)
                good = good and entry["everyTriadHasACentre"]
                css, perp = css_data(N, Ls, q)
                entry["css"] = css
                good = good and (css["dimC"] == css["rankLawDimC"] and css["dimC"] + css["dimCperp"] == N
                                 and css["CperpInC"] and css["CperpDoublyEven"] and css["k"] == q * q + 1
                                 and css["lineIsLogical"])
            else:
                entry["everyTriadHasACentre"] = every_triad_has_a_centre(N, adj)
                perp = None
            if q <= 5:
                if perp is None:
                    perp = nullspace(list(rref(Ls).values()), N)
                words = low_weight_words(N, perp, q + 1)
                entry["wordsOfWeightAtMostQPlus1"] = len(words)
                entry["theyAreExactlyTheLines"] = words == set(Ls)
                good = good and words == set(Ls)
            entry["valid"] = good
            ok = ok and good
            report[name] = entry
            print("%-8s n=%d  GQ(%d,%d) axiom %s  parity %s  srg(%s,%s)  triads centred %s%s%s  -> %s" % (
                name, N, q, t, geo["gqAxiom"], geo["parityOnLines"], geo["srgLambda"], geo["srgMu"],
                entry["everyTriadHasACentre"],
                ("  css dimC=%d k=%d Cperp<=C %s doubly-even %s" % (
                    entry["css"]["dimC"], entry["css"]["k"], entry["css"]["CperpInC"], entry["css"]["CperpDoublyEven"])
                 if "css" in entry else ""),
                ("  words wt<=%d: %d = lines %s" % (q + 1, entry["wordsOfWeightAtMostQPlus1"], entry["theyAreExactlyTheLines"])
                 if "wordsOfWeightAtMostQPlus1" in entry else ""),
                good), flush=True)
    print()
    print("VALID: %s" % ok)
    if args.write:
        assert ok and args.qs == "3,5,7", "checks failed -- refusing to write"
        rec = {
            "schema": "holotrade.binary-line-code-distance.v1",
            "valid": True,
            "theorem1": "binary line code of any finite GQ of order (s,t), s odd, s <= t+1, has minimum weight s+1",
            "theorem2": ("s odd, t >= s: a weight-(s+1) word with lambda=1 is a line; with lambda=0 it is a partial "
                         "ovoid with no centred triad, impossible in W(3,q); so for W(3,q), q odd, the words of "
                         "weight q+1 are exactly the (q+1)(q^2+1) isotropic lines"),
            "corollary": "Pass 229's CSS family [[(q+1)(q^2+1), q^2+1, q+1]] has distance exactly q+1 "
                         "(certified S = C^perp at q = 3,5,7; beyond, by the rank law P322 and k = q^2+1)",
            "closes": "W33-Theory claims ledger row 'CSS distance d=q+1, q>=5' (open, P326)",
            "priorArt": {
                "PetitVanDeVoorde2025": "arXiv:2511.07697 Theorem 7 needs 1-s != 0 in F; binary with s odd is excluded",
                "corpus": ["Pass 229 (family, q=3 exact)", "Pass 326 (audit: d <= q+1 only for q >= 5)", "P322 (rank law)"],
            },
            "cases": report,
            "boundary": ("Theorem 1 and 2 are proofs; the script checks their hypotheses exactly at q = 3,5,7 and "
                         "confirms the conclusions exhaustively at q = 3,5 for W(3,q) and Q(4,q). For Q(4,q) only "
                         "Theorem 1 is proved in general; its line characterisation is checked, not proved."),
        }
        p = os.path.join(ROOT, "data", "binary_line_code_distance.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=2)
        print("written: %s" % p)


if __name__ == "__main__":
    main()
