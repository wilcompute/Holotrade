#!/usr/bin/env python3
"""
The 27 of E6 is the set of COMPLETE FACTORISATION FRAMES of two qutrits, and
its SO(10) decomposition 27 = 1 + 10 + 16 is visible there as an operation on
tensor factors: the Weyl sign changes of SO(10) are EXCHANGES OF THE TWO
QUTRITS inside the frame's factorisations, always an even number of them.

PRIOR ART, CITED.
  * the_optimal_stabilizer_certificates_are_tensor_factorisations.py (feb5154):
    an octet L u L^perp of W(3,3) is the set of local Pauli classes of a tensor
    factorisation C^9 = C^3 (x) C^3; there are 45 (checked on matrices).
  * gq24_lives_inside_w33_as_its_octet_factors.py: the 40 points split into
    five pairwise disjoint octets in exactly 27 ways, and these 27
    "K(4,4)-factors", two collinear when they share an octet, form GQ(2,4) --
    the 27 lines and 45 tritangent planes of the cubic surface.
  * the_cost_anomalies_are_local_charge_conjugations.py (79e8074).
  * W33-Theory analysis/w33_20260901_gq24_k44_e8_atlas.py: the same 27
    K(4,4)-factors are its 27 ten-D4 partitions of the E8 root shell, in one
    27 x 45 incidence with the cubic lines and tritangent planes (no physical
    interpretation inferred there). Cited after the fact: this file's W(D5)
    stabiliser, sign-change and factor-exchange results are not in the atlas.
  * W33-Theory, analysis/2026-07-15_pass84_e6_w33_explicit_iso.md, records the
    classical branching 27 = 1 + 10 + 16 under W(D5) = 2^4.S5, the stabiliser of
    a line, and leaves the W33 realisation OPEN ("27 = 40 - 13 ???", "10 = ...
    12 collinear points minus some").

THE PHYSICAL NAME OF A LINE.  Compose the first two: a line of the cubic surface
is a set of five tensor factorisations of C^9 whose local Pauli sets partition
all 40 Pauli classes -- every non-identity Pauli observable is local in exactly
one of the five. Call it a complete factorisation frame.

WHAT IS COMPUTED HERE, with the full collineation group of W(3,3) built as
permutations (PSp(4,3), order 25920, and with the multiplier -1 similitude,
order 51840 = |W(E6)|):

  * the stabiliser of a frame F has order 960 in PSp(4,3) and 1920 = |W(D5)| in
    the full group, acting on F's five factorisations as A5 and S5;
  * the kernel -- elements fixing each of the five factorisations -- has order
    16. Each kernel element either keeps or EXCHANGES the two tensor factors of
    each factorisation (maps H_i to H_i or to H_i^perp), giving a vector in
    F_2^5. The map is injective and its image is exactly the 16 EVEN-weight
    vectors: the even sign-change group of D5;
  * the other frames split 10 + 16 by how many factorisations they share with F
    (one or none). The 16 form a single REGULAR orbit of the sign group -- a
    torsor for the even sign vectors, which is how the 16 spinor weights sit
    under W(D5). The 10 come in five pairs, one pair through each factorisation
    of F, and a kernel element swaps the pair through factorisation i exactly
    when it exchanges that factorisation's two qutrits: the vector weights
    +e_i and -e_i.

So   27 = 1 + 10 + 16   is:   the frame itself,
                              the frames sharing one of its factorisations,
                              the frames sharing none.

THE PARITY RULE.  No collineation of W(3,3) -- symplectic Clifford or the
antiunitary-type similitude -- preserves a frame factorisation by factorisation
while exchanging the two qutrits of an ODD number of them. Example: the SWAP of
the computational pair of qutrits lies in PSp(4,3), preserves exactly 3 frames,
and in each fixes all five factorisations while exchanging the factors of FOUR.

WHAT THIS IS AND IS NOT.  It is a finite, exact identification at the level of
Weyl groups and weights: W(E6), W(D5), and the orbit structure of the 27. It
resolves the open W33 realisation in Pass 84 with a two-qutrit operational
meaning. It is NOT a derivation of SO(10) gauge fields, fermion quantum numbers
or masses, and no Standard Model assignment is inferred -- the corpus has
already recorded that a graph decomposition does not license one
(PASS7376_7384_deep_followup.md), and that caution applies here verbatim.

SCOPE.  Exact group computation on 40 points; the octet = tensor-factorisation
dictionary is cited from feb5154, where it is checked with 9x9 matrices; the
27 frames and GQ(2,4) are cited from the gq24 file and recomputed here as
inputs. The D5 branching of the 27 of E6 is classical.
"""

import argparse
import itertools
import json
import os
from collections import Counter, deque

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Q = 3


def geometry():
    def nm(v):
        i = next(k for k, x in enumerate(v) if x % Q)
        z = pow(v[i] % Q, -1, Q)
        return tuple((z * x) % Q for x in v)
    pts = sorted({nm(v) for v in itertools.product(range(Q), repeat=4) if any(v)})
    idx = {p: i for i, p in enumerate(pts)}
    n = len(pts)

    def sf(u, v):
        return (u[0] * v[2] - u[2] * v[0] + u[1] * v[3] - u[3] * v[1]) % Q

    def span(a, b):
        return frozenset(idx[nm(tuple((x * pts[a][k] + y * pts[b][k]) % Q for k in range(4)))]
                         for x in range(Q) for y in range(Q) if x or y)
    perp = [frozenset(j for j in range(n) if sf(pts[i], pts[j]) == 0) for i in range(n)]
    tlines = {span(a, b) for a, b in itertools.combinations(range(n), 2) if sf(pts[a], pts[b]) == 0}
    hyp = {span(a, b) for a, b in itertools.combinations(range(n), 2) if sf(pts[a], pts[b])}
    octs, halves = [], {}
    for H in hyp:
        Hp = frozenset.intersection(*[perp[i] for i in H])
        O = H | Hp
        if O not in halves:
            halves[O] = (H, Hp)
            octs.append(O)
    octs.sort(key=sorted)
    assert n == 40 and len(tlines) == 40 and len(octs) == 45
    return pts, idx, nm, n, tlines, octs, halves


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    pts, idx, nm, n, tlines, octs, halves = geometry()
    disj = [[not (octs[i] & octs[j]) for j in range(45)] for i in range(45)]
    frames = []

    def ext(cur, start):
        if len(cur) == 5:
            frames.append(tuple(cur))
            return
        for j in range(start, 45):
            if all(disj[j][i] for i in cur):
                ext(cur + [j], j + 1)
    ext([], 0)
    per_oct = Counter(i for f in frames for i in f)

    def mat_perm(M):
        return tuple(idx[nm(tuple(sum(M[r][c] * pts[p][c] for c in range(4)) % Q for r in range(4)))]
                     for p in range(n))

    def sfv(u, v):
        return (u[0] * v[2] - u[2] * v[0] + u[1] * v[3] - u[3] * v[1]) % Q

    def transvection(v):
        return [[((1 if r == c else 0) + sfv(tuple(1 if k == c else 0 for k in range(4)), v) * v[r]) % Q
                 for c in range(4)] for r in range(4)]

    gens = [mat_perm(transvection(v)) for v in pts]
    sim = mat_perm([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 2, 0], [0, 0, 0, 2]])
    preserves = all(frozenset(g[x] for x in L) in tlines for g in gens + [sim] for L in tlines)

    def comp(a, b):
        return tuple(a[b[i]] for i in range(n))

    def closure(gs):
        I = tuple(range(n))
        seen, dq = {I}, deque([I])
        while dq:
            x = dq.popleft()
            for g in gs:
                y = comp(g, x)
                if y not in seen:
                    seen.add(y)
                    dq.append(y)
        return seen

    G1 = closure(gens)
    G2 = closure(gens + [sim])
    octid = {O: i for i, O in enumerate(octs)}
    fidx = {tuple(sorted(f)): j for j, f in enumerate(frames)}
    F = frames[0]
    FO = [octs[i] for i in F]
    near = [j for j, f in enumerate(frames) if len(set(f) & set(F)) == 1]
    far = [j for j, f in enumerate(frames) if not set(f) & set(F)]

    def img(g, S):
        return frozenset(g[x] for x in S)

    def img_frame(g, f):
        return fidx[tuple(sorted(octid[img(g, octs[i])] for i in f))]

    def analyse(G):
        stab = [g for g in G if {img(g, O) for O in FO} == set(FO)]
        induced, K = set(), []
        for g in stab:
            pm = tuple(FO.index(img(g, O)) for O in FO)
            induced.add(pm)
            if pm == tuple(range(5)):
                K.append(g)
        bits = []
        for g in K:
            b = []
            for O in FO:
                H, Hp = halves[O]
                assert img(g, H) in (H, Hp)
                b.append(0 if img(g, H) == H else 1)
            bits.append(tuple(b))
        orbit16 = {img_frame(g, frames[far[0]]) for g in K}
        pair_rule = True
        for i, O in enumerate(FO):
            pair = [j for j in near if octid[O] in frames[j]]
            if len(pair) != 2:
                pair_rule = False
                continue
            for g, b in zip(K, bits):
                if (img_frame(g, frames[pair[0]]) == pair[1]) != bool(b[i]):
                    pair_rule = False
        return {"stabiliser": len(stab), "inducedOnFactorisations": len(induced), "kernel": len(K),
                "swapVectorsDistinct": len(set(bits)),
                "swapVectorsAllEven": all(sum(b) % 2 == 0 for b in bits),
                "orbitOnSixteen": len(orbit16),
                "pairSwapIffFactorExchange": pair_rule}

    r1, r2 = analyse(G1), analyse(G2)

    SW = mat_perm([[0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]])
    swap_in_psp = SW in G1
    swap_frames = []
    for f in frames:
        fo = [octs[i] for i in f]
        if {img(SW, O) for O in fo} == set(fo):
            fixed = [O for O in fo if img(SW, O) == O]
            exch = [O for O in fixed if img(SW, halves[O][0]) == halves[O][1]]
            swap_frames.append((len(fixed), len(exch)))

    print("THE 27 FACTORISATION FRAMES CARRY THE SO(10) WEIGHTS")
    print("=" * 74)
    print("  frames (partitions of the 40 Pauli classes into 5 factorisation octets): %d; per octet %s"
          % (len(frames), dict(Counter(per_oct.values()))))
    print("  frames sharing one / no factorisation with a given frame: %d / %d" % (len(near), len(far)))
    print("  collineation groups: PSp(4,3) %d, with similitude %d (generators preserve lines: %s)"
          % (len(G1), len(G2), preserves))
    for name, r in (("PSp(4,3)", r1), ("Aut W(3,3)", r2)):
        print("  %-11s stabiliser %d, on the 5 factorisations %d, kernel %d; swap vectors %d distinct, all even %s;"
              % (name, r["stabiliser"], r["inducedOnFactorisations"], r["kernel"], r["swapVectorsDistinct"],
                 r["swapVectorsAllEven"]))
        print("              orbit on the 16 = %d; pair through factorisation i swapped iff its qutrits exchanged: %s"
              % (r["orbitOnSixteen"], r["pairSwapIffFactorExchange"]))
    print("  SWAP of the computational qutrits in PSp(4,3): %s; frames it preserves %d, (fixed, exchanged) = %s"
          % (swap_in_psp, len(swap_frames), sorted(set(swap_frames))))

    def good(r, stab, induced):
        return (r["stabiliser"] == stab and r["inducedOnFactorisations"] == induced and r["kernel"] == 16
                and r["swapVectorsDistinct"] == 16 and r["swapVectorsAllEven"]
                and r["orbitOnSixteen"] == 16 and r["pairSwapIffFactorExchange"])

    ok = (len(frames) == 27 and set(per_oct.values()) == {3} and len(near) == 10 and len(far) == 16
          and len(G1) == 25920 and len(G2) == 51840 and preserves
          and good(r1, 960, 60) and good(r2, 1920, 120)
          and swap_in_psp and len(swap_frames) == 3 and set(swap_frames) == {(5, 4)})
    print()
    print("VALID: %s" % ok)

    if args.write:
        assert ok, "checks failed -- refusing to write"
        rec = {
            "schema": "holotrade.27-frames-so10-weights.v1",
            "valid": True,
            "frames": len(frames), "framesPerOctet": 3,
            "nearFrames": len(near), "farFrames": len(far),
            "pspOrder": len(G1), "fullOrder": len(G2),
            "psp": r1, "full": r2,
            "swapInPsp": swap_in_psp, "swapPreservedFrames": len(swap_frames),
            "swapFixedExchanged": sorted(set(swap_frames))[0],
            "priorArt": (
                "feb5154 (octet = tensor factorisation); gq24_lives_inside_w33_as_its_octet_factors.py (27 "
                "K(4,4)-factors = GQ(2,4)); 79e8074 (cost anomalies = local charge conjugations); W33-Theory "
                "Pass 84, 2026-07-15_pass84_e6_w33_explicit_iso.md, which records 27 = 1 + 10 + 16 under W(D5) "
                "and leaves its W33 realisation open."),
            "thePhysicalNameOfALine": (
                "a line of the cubic surface is a complete factorisation frame: five tensor factorisations of C^9 "
                "whose local Pauli sets partition all 40 Pauli classes, so every non-identity Pauli observable is "
                "local in exactly one of them."),
            "theStabiliser": (
                "a frame's stabiliser has order 960 in PSp(4,3) and 1920 = |W(D5)| in Aut W(3,3), acting on its "
                "five factorisations as A5 and S5, with a kernel of order 16."),
            "theSignChanges": (
                "each kernel element keeps or exchanges the two qutrits of each factorisation; the resulting map to "
                "F_2^5 is injective with image the 16 even-weight vectors, the even sign changes of D5."),
            "oneTenSixteen": (
                "27 = 1 + 10 + 16 is the frame, the frames sharing one of its factorisations, and those sharing none. "
                "The 16 are one regular orbit of the sign group; the 10 are five pairs, and a kernel element swaps "
                "the pair through factorisation i exactly when it exchanges that factorisation's qutrits."),
            "theParityRule": (
                "no collineation of W(3,3) preserves a frame factorisation by factorisation while exchanging the "
                "qutrits of an odd number of them. The computational SWAP preserves 3 frames and in each exchanges "
                "the factors of four of the five factorisations."),
            "whatThisIsNot": (
                "a Weyl-group and weight-level identification only. No SO(10) gauge field, fermion quantum number or "
                "mass is derived and no Standard Model assignment is inferred, following the caution already "
                "recorded in PASS7376_7384_deep_followup.md."),
            "boundary": (
                "exact group computation on 40 points; the octet = factorisation dictionary is cited from feb5154, "
                "where it is checked with matrices; the 27 frames and GQ(2,4) are cited and recomputed as inputs; "
                "the D5 branching of the 27 of E6 is classical."),
        }
        p = os.path.join(ROOT, "data", "twenty_seven_frames_so10_weights.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=2)
        print("written: %s" % p)


if __name__ == "__main__":
    main()
