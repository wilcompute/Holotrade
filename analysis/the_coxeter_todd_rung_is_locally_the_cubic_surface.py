#!/usr/bin/env python3
"""
THE COXETER-TODD RUNG OF THE QR TOWER: K12 MOD 2 IS A PROPER SHADOW, AND AT EVERY
REFLECTION LINE THE LATTICE CARRIES THE CUBIC SURFACE AND A DOUBLED W(3,3).

This settles two open items in W33-Theory:
  * the ledger row "m=6 Coxeter-Todd rung of the QR tower" (OPEN, P368/369,
    "handed to GAP track"): does 6.PSU(4,3).2 mod 2 distinguish itself inside
    the m=6 plus refinement's O+(12,2)?
  * Pass 7289's recorded-but-UNTESTED prediction: K12/(1-w)K12 carries the 126
    classes of minimal vectors as SRG(126,45,12,18).
Pass 7289 lists "K12 built" under NOT DONE; Pass 369 had already built it (the
hexacode construction below, det 729, rootless, 2080 isotropic classes). This
file uses that construction.

THE LATTICE.  K12 = { x in Z[w]^6 : x mod 2 in the hexacode }, norm sum |x_i|^2
(Pass 369's "(1/sqrt2), trace form halved"). Checked: Gram det 729, even, theta
series 1 + 756 q^4 + 4032 q^6 + 20412 q^8 + ...

THE REFLECTIONS.  For a minimal vector v (norm 4), h(x,v) lies in 2Z[w] for
every x in K12. So r_v(x) = x - (h(x,v)/2) v preserves K12 (checked on a
Z-basis). The 756 minimal vectors give 126 reflection lines. The group they
generate is Mitchell's complex reflection group G34 = 6.PSU(4,3).2.

1. MOD THETA (PREDICTION CONFIRMED).  K12/(1-w)K12 = F_3^6. The 126 lines
   reduce to 126 distinct projective points, all nonsingular for the reduced
   form. Their orthogonality graph is SRG(126,45,12,18). Two lines are adjacent
   iff h = 0 exactly: minimal vectors meet with |h|^2 in {0, 4, 16}. The group
   on the 126 has order 6,531,840 = |U4(3).2| and is rank 3, with derived
   subgroup of order 3,265,920 = |U4(3)|.

2. MOD 2 (THE OPEN ROW, ANSWERED: YES).  The 4095 nonzero classes of
   K12/2K12, by minimal norm, are:
       378 (norm 4, one +- pair each)  |  1701 (norm 8, 12 vectors each)  |
       2016 (norm 6, one +- pair each)
   q = norm/2 mod 2, so the singular classes are 1 + 378 + 1701 = 2080
   (Pass 369's PLUS count) and the nonsingular ones are 2016. The reflection
   group acts on K12/2K12 with image of order 19,595,520 = 3.|U4(3).2|, and
   its orbits are exactly 378, 1701, 2016. O+(12,2) is transitive on the 2079
   nonzero singular vectors (Witt), so the Coxeter-Todd shadow is a proper
   subgroup, of index about 5.1e12, and it splits the singular vectors.
   Compare the lower rungs: A2 -> O-(2,2) = W(A2), E6 -> O-(6,2) = W(E6),
   E8 -> O+(8,2) = W(E8)/+-1. There the lattice group IS the whole mod-2
   orthogonal group. Eisenstein rank 6 is where that coincidence ends.

3. THE LOCAL STRUCTURE AT A REFLECTION LINE (THE BRIDGE TO W(3,3)).  Fix one
   of the 126 lines, l. The stabiliser in U4(3) has order 25,920 (PSp(4,3) =
   U4(2), the W(3,3) group) and orbits 1 + 45 + 80.
   * The 45 lines orthogonal to l form GQ(4,2) = SRG(45,12,3,3). Its 27 lines
     (5-cliques) are the 27 orthogonal 6-frames through l: the 45 tritangent
     planes and 27 lines of the cubic surface. In all there are 567 = 1701/3
     frames.
   * The 80 non-orthogonal lines pair into 40 antipodal fibres (unique mu = 0
     partner). Distinct neighbours lie in distinct fibres. The quotient's
     complement is a GQ(3,3) whose points are all ANTIREGULAR
     (|{x,y}^perp^perp| = 2), so it is Q(4,3), the dual of W(3,3). The 40
     fibres are the 40 lines of W(3,3); the 80 double-cover its
     non-collinearity graph.
   So each of the 126 reflection lines of K12 carries, locally, the E6 cubic
   surface (27/45) and W(3,3) doubled -- the configurations the corpus
   assigns to the E6 rung.

SCOPE AND PRIOR ART.  The graph SRG(126,45,12,18) and U4(3)'s rank-3 action
are classical (Brouwer's tables; Pass 7288 already marks them NOT NEW).
Conway-Sloane (1983), "The Coxeter-Todd lattice, the Mitchell group, and
related sphere packings" (Math. Proc. Camb. Phil. Soc. 93, 421), says in its
abstract that it enumerates K12's congruence classes. So the mod-2 and mod-theta
class counts should be taken as classical. The scanned PDF could not be
text-extracted here, so no literature novelty is claimed for any lattice fact. What is
new relative to the corpus: the answer to the open row, the test of 7289's
prediction, and the identification of both subconstituents with the E6/W(3,3)
objects. Group orders come from Schreier-Sims here (sympy) and were
cross-checked in GAP 4.16 (derived group isomorphic to PSU(4,3), point
stabiliser isomorphic to PSp(4,3)). No physics is asserted.
"""

import argparse
import itertools
import json
import os
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def mul(x, y):
    a, b = x
    c, d = y
    return (a * c - b * d, a * d + b * c - b * d)


def conj(x):
    return (x[0] - x[1], -x[1])


def nrm(x):
    return x[0] * x[0] - x[0] * x[1] + x[1] * x[1]


UNITS = [(1, 0), (0, 1), (-1, -1), (-1, 0), (0, -1), (1, 1)]
F4MUL = [[0, 0, 0, 0], [0, 1, 2, 3], [0, 2, 3, 1], [0, 3, 1, 2]]
F4CONJ = [0, 1, 3, 2]
HEXGEN = [[1, 0, 0, 1, 1, 1], [0, 1, 0, 1, 2, 3], [0, 0, 1, 1, 3, 2]]
LIFT = {0: (0, 0), 1: (1, 0), 2: (0, 1), 3: (-1, -1)}


def hexacode():
    code = set()
    for cf in itertools.product(range(4), repeat=3):
        w = [0] * 6
        for k in range(3):
            for j in range(6):
                w[j] ^= F4MUL[cf[k]][HEXGEN[k][j]]
        code.add(tuple(w))
    return code


def vnorm(v):
    return sum(nrm(x) for x in v)


def h(x, y):
    a = b = 0
    for xi, yi in zip(x, y):
        p = mul(xi, conj(yi))
        a += p[0]
        b += p[1]
    return (a, b)


def refl(v, x):
    c = h(x, v)
    assert c[0] % 2 == 0 and c[1] % 2 == 0
    s = (c[0] // 2, c[1] // 2)
    return tuple((xi[0] - mul(s, vi)[0], xi[1] - mul(s, vi)[1]) for xi, vi in zip(x, v))


def orbits(perms, n):
    seen = [False] * n
    out = []
    for s in range(n):
        if seen[s]:
            continue
        orb, seen[s], i = [s], True, 0
        while i < len(orb):
            for p in perms:
                t = p[orb[i]]
                if not seen[t]:
                    seen[t] = True
                    orb.append(t)
            i += 1
        out.append(orb)
    return out


def srg(V, adj):
    Vs = set(V)
    k = sorted({len(adj[v] & Vs) for v in V})
    lam, mu = set(), set()
    for a, b in itertools.combinations(V, 2):
        (lam if b in adj[a] else mu).add(len(adj[a] & adj[b] & Vs))
    return k, sorted(lam), sorted(mu)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    import sympy
    from sympy.combinatorics import Permutation, PermutationGroup

    code = hexacode()
    ok_code = len(code) == 64 and min(sum(1 for t in c if t) for c in code if any(c)) == 4
    herm_dual = True
    for c in code:
        for d in code:
            s = 0
            for i in range(6):
                s ^= F4MUL[c[i]][F4CONJ[d[i]]]
            herm_dual = herm_dual and s == 0

    # short vectors, norm <= 8
    elems = sorted(((a, b) for a in range(-4, 5) for b in range(-4, 5) if nrm((a, b)) <= 8), key=nrm)
    vecs = []

    def rec(prefix, budget):
        if len(prefix) == 6:
            if budget < 8 and tuple((x[0] % 2) + 2 * (x[1] % 2) for x in prefix) in code:
                vecs.append(tuple(prefix))
            return
        for x in elems:
            if nrm(x) > budget:
                break
            rec(prefix + [x], budget - nrm(x))
    rec([], 8)
    theta = Counter(vnorm(v) for v in vecs)

    # Z-basis, Gram, coordinates
    basis = [tuple(mul(s, LIFT[c]) for c in r) for r in HEXGEN for s in ((1, 0), (0, 1))]
    basis += [tuple(s if j == i else (0, 0) for j in range(6)) for i in range(3, 6) for s in ((2, 0), (0, 2))]

    def real(v):
        return [c for x in v for c in x]
    Bm = sympy.Matrix([real(b) for b in basis])
    DET = int(Bm.det())
    ADJ = [[int(x) for x in row] for row in Bm.adjugate().tolist()]

    def coords(v):
        r = real(v)
        c = [sum(r[i] * ADJ[i][j] for i in range(12)) for j in range(12)]
        if any(x % DET for x in c):
            return None
        return tuple(x // DET for x in c)
    gram = sympy.Matrix(12, 12, lambda i, j: sympy.Rational(
        vnorm(tuple((a[0] + b[0], a[1] + b[1]) for a, b in zip(basis[i], basis[j]))) - vnorm(basis[i]) - vnorm(basis[j]), 2))
    gram_det = int(gram.det())
    even = all(vnorm(b) % 2 == 0 for b in basis)

    mins = [v for v in vecs if vnorm(v) == 4]
    line_of, lines = {}, []
    for v in mins:
        if v not in line_of:
            cls = {tuple(mul(u, x) for x in v) for u in UNITS}
            for w in cls:
                line_of[w] = len(lines)
            lines.append(min(cls))
    reflections_preserve = all(coords(refl(v, b)) is not None for v in lines for b in basis)
    hvals = sorted(Counter(nrm(h(mins[0], w)) for w in mins).items())

    # 1. mod theta
    def red3(v):
        return tuple((x[0] + x[1]) % 3 for x in v)

    def proj3(t):
        i = next(k for k, a in enumerate(t) if a)
        return tuple((a * t[i]) % 3 for a in t)
    rep3 = {}
    for m in mins:
        rep3.setdefault(proj3(red3(m)), m)
    pts = sorted(rep3)
    pidx = {p: i for i, p in enumerate(pts)}
    B3 = [[sum(a * b for a, b in zip(p, r)) % 3 for r in pts] for p in pts]
    nonsingular = all(B3[i][i] != 0 for i in range(len(pts)))
    S = {i: {j for j in range(len(pts)) if j != i and B3[i][j] == 0} for i in range(len(pts))}
    orth_exact = all((B3[pidx[proj3(red3(a))]][pidx[proj3(red3(b))]] == 0) == (h(a, b) == (0, 0))
                     for a in lines for b in lines if a != b)
    srg126 = srg(list(range(126)), S)
    perm126 = [[pidx[proj3(red3(refl(v, rep3[p])))] for p in pts] for v in lines]
    G126 = PermutationGroup([Permutation(p) for p in perm126])
    order126 = int(G126.order())
    D126 = G126.derived_subgroup()
    orderD = int(D126.order())
    pair_perms = [[p[i // 126] * 126 + p[i % 126] for i in range(126 * 126)] for p in perm126]
    pair_orbits = len(orbits(pair_perms, 126 * 126))  # orbitals, diagonal included: rank
    stab = D126.stabilizer(0)
    stab_orbits = sorted(len(o) for o in stab.orbits())
    stab_order = int(stab.order())

    # 3. local structure at line 0
    N = sorted(S[0])
    M = sorted(j for j in range(1, 126) if j not in S[0])
    srg45 = srg(N, S)
    Ns = set(N)
    loc_lines = {frozenset({a, b} | (S[a] & S[b] & Ns)) for a in N for b in S[a] & Ns}
    gq42 = (all(len(L) == 5 for L in loc_lines) and len(loc_lines) == 27
            and all(sum(1 for L in loc_lines if x in L) == 3 for x in N)
            and all(sum(1 for y in L if y in S[x]) == 1 for L in loc_lines for x in N if x not in L))
    frames = set()
    for p in range(126):
        for a in S[p]:
            for b in S[p] & S[a]:
                c = frozenset({p, a, b} | (S[p] & S[a] & S[b]))
                if len(c) == 6:
                    frames.add(c)
    Ms = set(M)
    A = {a: S[a] & Ms for a in M}
    zero = {a: [b for b in M if b != a and b not in A[a] and not (A[a] & A[b])] for a in M}
    antipodal = all(len(z) == 1 for z in zero.values())
    fib = {frozenset((a, zero[a][0])) for a in M}
    fid = {a: i for i, f in enumerate(sorted(fib, key=sorted)) for a in f}
    cover = all(len({fid[b] for b in A[a]}) == len(A[a]) for a in M)
    V40 = list(range(40))
    Qg = {i: set() for i in V40}
    for a in M:
        for b in A[a]:
            Qg[fid[a]].add(fid[b])
    col = {v: set(V40) - Qg[v] - {v} for v in V40}
    srg40 = srg(V40, col)
    glines = {frozenset({x, y} | (col[x] & col[y])) for x in V40 for y in col[x]}
    gq33 = (all(len(L) == 4 for L in glines) and len(glines) == 40
            and all(sum(1 for y in L if y in col[x]) == 1 for L in glines for x in V40 if x not in L))

    def perp(X):
        s = set(V40)
        for x in X:
            s &= col[x] | {x}
        return s
    antiregular = all(len(perp(perp({x, y}))) == 2 for x, y in itertools.combinations(V40, 2) if y not in col[x])

    # 2. mod 2
    classes = defaultdict(list)
    for v in vecs:
        classes[tuple(x % 2 for x in coords(v))].append(v)
    minnorm = {k: min(vnorm(v) for v in vs) for k, vs in classes.items()}
    per_class = {n: sorted(Counter(sum(1 for v in classes[k] if vnorm(v) == n)
                                   for k in classes if minnorm[k] == n).items()) for n in (4, 6, 8)}
    keys = sorted(classes)
    kidx = {k: i for i, k in enumerate(keys)}
    rep2 = {k: min(classes[k], key=vnorm) for k in keys}
    perm2 = [[kidx[tuple(x % 2 for x in coords(refl(v, rep2[k])))] for k in keys] for v in lines]
    orb2 = sorted((len(o), minnorm[keys[o[0]]]) for o in orbits(perm2, len(keys)))
    order2 = int(PermutationGroup([Permutation(p) for p in perm2]).order())
    O12 = 2 * 2 ** 30 * (2 ** 6 - 1)
    for i in range(1, 6):
        O12 *= 2 ** (2 * i) - 1

    checks = {
        "hexacode": ok_code and herm_dual,
        "gramDet729Even": gram_det == 729 and even,
        "theta": [theta.get(2, 0), theta[4], theta[6], theta[8]] == [0, 756, 4032, 20412],
        "reflectionLines126": len(lines) == 126,
        "reflectionsPreserveK12": reflections_preserve,
        "minimalInnerProducts": [n for n, _ in hvals] == [0, 4, 16],
        "modTheta126Nonsingular": len(pts) == 126 and nonsingular,
        "orthogonalModThetaIffExactly": orth_exact,
        "srg126_45_12_18": srg126 == ([45], [12], [18]),
        "group126": order126 == 6531840 and orderD == 3265920 and pair_orbits == 3,
        "pointStabiliser25920_1_45_80": stab_order == 25920 and stab_orbits == [1, 45, 80],
        "local45IsGQ42": srg45 == ([12], [3], [3]) and gq42,
        "frames567": len(frames) == 567,
        "eightyIsAntipodalCover": antipodal and cover and len(fib) == 40,
        "quotientIsQ43": srg40 == ([12], [2], [4]) and gq33 and antiregular,
        "mod2Split": sorted(Counter(minnorm.values()).items()) == [(4, 378), (6, 2016), (8, 1701)],
        "mod2PerClass": per_class == {4: [(2, 378)], 6: [(2, 2016)], 8: [(12, 1701)]},
        "singular2080": 1 + 378 + 1701 == 2080,
        "mod2Orbits": orb2 == [(378, 4), (1701, 8), (2016, 6)],
        "mod2Image19595520": order2 == 19595520,
        "properInO12plus": O12 % order2 == 0 and O12 // order2 > 1,
    }
    ok = all(checks.values())
    for k, v in checks.items():
        print("  %-34s %s" % (k, v))
    print("  index of the shadow in O+(12,2): %d" % (O12 // order2))
    print()
    print("VALID: %s" % ok)
    if args.write:
        assert ok, "checks failed -- refusing to write"
        rec = {
            "schema": "holotrade.coxeter-todd-rung.v1",
            "valid": True,
            "checks": checks,
            "theta": {"4": theta[4], "6": theta[6], "8": theta[8]},
            "modTheta": {"points": 126, "srg": [126, 45, 12, 18], "groupOrder": order126,
                         "derivedOrder": orderD, "rank": pair_orbits,
                         "pointStabiliser": {"order": stab_order, "orbits": stab_orbits, "isomorphicTo": "PSp(4,3) (GAP)"}},
            "mod2": {"classesByMinNorm": {"4": 378, "6": 2016, "8": 1701}, "singular": 2080, "nonsingular": 2016,
                     "imageOrder": order2, "orbits": [378, 1701, 2016],
                     "O12plusOrder": O12, "index": O12 // order2},
            "local": {"orthogonal45": "GQ(4,2) = SRG(45,12,3,3), 27 lines = the 27 orthogonal 6-frames through the line",
                      "frames": len(frames),
                      "nonOrthogonal80": "antipodal double cover; fibres = 40 lines of W(3,3); quotient complement = Q(4,3)"},
            "closes": ["W33-Theory ledger row 'm=6 Coxeter-Todd rung of the QR tower' (open, P368/369)",
                       "Pass 7289 prediction SRG(126,45,12,18) (recorded untested)"],
            "corrects": "Pass 7289 lists K12 as unbuilt; Pass 369 built it (hexacode construction, used here)",
            "boundary": ("classical graph, group and congruence-class facts (U4(3) rank 3, G34; Conway-Sloane 1983 "
                         "enumerates K12's congruence classes, not text-read here) are not "
                         "claimed new; the corpus-facing content is the answer to the open row, the prediction test, and "
                         "the subconstituent identification. No physics."),
        }
        p = os.path.join(ROOT, "data", "coxeter_todd_rung.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=2)
        print("written: %s" % p)


if __name__ == "__main__":
    main()
