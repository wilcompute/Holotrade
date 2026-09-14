#!/usr/bin/env python3
"""
W33-Theory uses the word "chirality" for three different Z2's. They are not
the same, one of them cannot label the others, and each has a two-qutrit name.

THE THREE, AS THE CORPUS STATES THEM.
  (ABS)  BT746 / BT772 -- "absolute chirality": presentation pairs of W(3,3)
         come in two types (point-axis / line-axis), and "Type-A/Type-B
         chirality is invariant under EVERY collineation" -- two W(E6)-orbits
         of 25,920 (data/bt746_weyl_e6_torsor_fusion.json). BT746 itself notes
         the "naive sign character of W(E6)" reading died.
  (REL)  Pass 346 (THE_SELECTION_LAYER.md 5.6, papers/a_reflection_group_cannot_
         orient_itself.tex) -- the half-spin pair S+/S- is exchanged by an
         element T of W(E6) outside U4(2), with det T = -1: chirality is
         relative and unselectable. BT877: the odd permutations of the four
         gauge lines through p0 are exactly the anti-symplectic coset.
  (INN)  BT869 -- "the chirality Z2 of the matter register is the central
         involution that swaps a polar pair": the 45-class of involutions of
         PSp(4,3), 8 fixed points, Steinberg eigenspaces 45 + 36.

WHAT IS COMPUTED HERE, on PSp(4,3) < PGSp(4,3) = W(E6) as point permutations.
  1. The multiplier character mu (0 on PSp(4,3), 1 on the similitudes of
     multiplier -1) agrees, on every element of the relevant stabilisers, with
       * the orientation parity of a complete factorisation frame (e92a047),
       * the sign of the permutation on the frame's five factorisations,
       * the sign of the permutation on the four lines through p0 (BT877),
     while the sign of the permutation of the 40 points is NOT mu (some
     multiplier -1 elements act evenly on the points -- recorded, since it is the
     obvious guess). (W(E6) has abelianisation Z2, so every nontrivial homomorphism to Z2 is
     mu; the checks certify that each of these maps IS nontrivial.) By
     e92a047, mu = 1 exactly on the antiunitary Clifford operations. So (REL)
     is the time-reversal-type character.
  2. The 45 involutions of BT869's class are the projective images of the
     negation of one symplectic pair (in the labels (a1,b1,a2,b2) of 79e8074,
     diag(-1,-1,1,1); in this file's coordinates, whose form pairs x0 with x2
     and x1 with x3, diag(-1,1,-1,1)): local charge conjugation C (x) I on one factor of each
     of the 45 tensor factorisations (79e8074), whose fixed-point set is the
     factorisation's own octet. They have mu = 0: (INN) is INNER, and it maps
     every orientation class of frames to itself. It is a grading, not an
     exchange.
  3. (ABS) is fixed by all of W(E6) while (REL) is exchanged by it, so no
     W(E6)-equivariant map sends the two (ABS) types to the two half-spins or
     to the two orientation classes. The chirality the substrate CAN select is
     provably not the one Pass 346 shows it cannot.

THE DICTIONARY.
     (ABS)  point-versus-line type        absolute, selectable, NOT a half-spin label
     (REL)  handedness / S+ vs S-          exchanged exactly by antiunitary operations
     (INN)  subsystem charge conjugation   inner, a 45 + 36 grading, exchanges nothing

WHAT IT CHANGES.  Readings that connect matter's left/right split to BT869's
45 + 36 are using (INN), which cannot distinguish handedness; readings that
treat BT746's absolute chirality as the Standard Model's handedness would need
an equivariant link to (REL), and there is none. The no-go of Pass 346 stands,
and now has a precise physical form: selecting (REL) requires breaking every
antiunitary symmetry, while (INN) and (ABS) are available but are different
objects.

SCOPE.  Exact finite computation for items 1 and 2; item 3 is a one-line
equivariance argument using BT746's certified orbit count. No physical particle
assignment is made.
"""

import argparse
import importlib.util
import itertools
import json
import os
from collections import Counter, deque

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Q = 3


def frames_module():
    p = os.path.join(ROOT, "analysis", "the_27_factorisation_frames_carry_the_so10_weights.py")
    spec = importlib.util.spec_from_file_location("frames27", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def perm_sign(p):
    seen, sign = [False] * len(p), 0
    for i in range(len(p)):
        if not seen[i]:
            j, L = i, 0
            while not seen[j]:
                seen[j] = True
                j = p[j]
                L += 1
            sign ^= (L - 1) & 1
    return sign


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    fm = frames_module()
    pts, idx, nm, n, tlines, octs, halves = fm.geometry()
    disj = [[not (octs[i] & octs[j]) for j in range(45)] for i in range(45)]
    frames = []

    def ext(cur, s):
        if len(cur) == 5:
            frames.append(tuple(cur))
            return
        for j in range(s, 45):
            if all(disj[j][i] for i in cur):
                ext(cur + [j], j + 1)
    ext([], 0)

    def sfv(u, v):
        return (u[0] * v[2] - u[2] * v[0] + u[1] * v[3] - u[3] * v[1]) % Q

    def mat_perm(M):
        return tuple(idx[nm(tuple(sum(M[r][c] * pts[p][c] for c in range(4)) % Q for r in range(4)))]
                     for p in range(n))

    def tv(v):
        return [[((1 if r == c else 0) + sfv(tuple(1 if k == c else 0 for k in range(4)), v) * v[r]) % Q
                 for c in range(4)] for r in range(4)]

    def comp(a, b):
        return tuple(a[b[i]] for i in range(n))
    I = tuple(range(n))

    def closure(gs):
        H, dq = {I}, deque([I])
        while dq:
            x = dq.popleft()
            for g in gs:
                y = comp(g, x)
                if y not in H:
                    H.add(y)
                    dq.append(y)
        return H

    gens = [mat_perm(tv(v)) for v in pts]
    G1 = closure(gens)
    SIM = mat_perm([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 2, 0], [0, 0, 0, 2]])
    G2 = closure(gens + [SIM])

    def mu(g):
        return 0 if g in G1 else 1

    def img(g, S):
        return frozenset(g[x] for x in S)

    # 1a. sign on the 40 points
    sign_points_ok = all(perm_sign(g) == mu(g) for g in G2)

    # 1b. frames: orientation parity and sign on the five factorisations
    frame_ok = True
    for f in frames:
        FO = [octs[i] for i in f]
        for g in G2:
            images = [img(g, O) for O in FO]
            if set(images) != set(FO):
                continue
            perm = [FO.index(O) for O in images]
            parity = sum(0 if img(g, halves[O][0]) == halves[img(g, O)][0] else 1 for O in FO) % 2
            if not (parity == mu(g) == perm_sign(perm)):
                frame_ok = False

    # 1c. the four lines through p0 (BT877)
    p0 = 0
    Lp0 = [L for L in tlines if p0 in L]
    lines_ok = True
    for g in G2:
        if g[p0] != p0:
            continue
        perm = [Lp0.index(img(g, L)) for L in Lp0]
        if perm_sign(perm) != mu(g):
            lines_ok = False

    # 2. BT869's 45-class = local charge conjugation of the 45 factorisations
    C = mat_perm([[2, 0, 0, 0], [0, 1, 0, 0], [0, 0, 2, 0], [0, 0, 0, 1]])
    C_in_PSp = C in G1
    order2 = comp(C, C) == I
    cls = set()
    for g in G1:
        gi = [0] * n
        for i, v in enumerate(g):
            gi[v] = i
        cls.add(comp(comp(g, C), tuple(gi)))
    fixed_sets = {frozenset(x for x in range(n) if c[x] == x) for c in cls}
    fixed_are_octets = fixed_sets == set(octs)
    involution_classes = Counter()
    for g in G1:
        if g != I and comp(g, g) == I:
            involution_classes[sum(1 for x in range(n) if g[x] == x)] += 1

    ok = (len(G1) == 25920 and len(G2) == 51840 and (not sign_points_ok) and frame_ok and lines_ok
          and C_in_PSp and order2 and len(cls) == 45 and fixed_are_octets
          and dict(involution_classes) == {8: 45, 0: 270})

    print("THE CORPUS HAS THREE CHIRALITIES")
    print("=" * 74)
    print("  mu = sign on the 40 points, on all of W(E6): %s  (expected False)" % sign_points_ok)
    print("  mu = frame orientation parity = sign on the five factorisations (all 27 frames): %s" % frame_ok)
    print("  mu = sign on the four lines through p0 (BT877): %s" % lines_ok)
    print("  one-pair negation (local charge conjugation) inner: %s, involution: %s, class size %d, fixed sets are exactly the 45 octets: %s"
          % (C_in_PSp, order2, len(cls), fixed_are_octets))
    print("  involution classes of PSp(4,3) by fixed points: %s  (BT869: 45 with 8, 270 with 0)" % dict(involution_classes))
    print("  (ABS) fixed by W(E6) [BT746 certificate], (REL) exchanged by it: no equivariant identification")
    print()
    print("VALID: %s" % ok)

    if args.write:
        assert ok, "checks failed -- refusing to write"
        rec = {
            "schema": "holotrade.corpus-three-chiralities.v1",
            "valid": True,
            "signOnPointsIsMu": sign_points_ok,
            "signOnPointsNote": "the sign of the action on the 40 points is not the multiplier character",
            "frameParityAndFactorisationSignAreMu": frame_ok,
            "gaugeLineSignIsMu": lines_ok,
            "localChargeConjugationInner": C_in_PSp,
            "localChargeConjugationClassSize": len(cls),
            "fixedSetsAreTheOctets": fixed_are_octets,
            "involutionClassesByFixedPoints": {str(k): v for k, v in involution_classes.items()},
            "abs": ("BT746/BT772 point-versus-line presentation type: invariant under all of W(E6) (two orbits of "
                    "25,920, data/bt746_weyl_e6_torsor_fusion.json); selectable; not the sign character."),
            "rel": ("Pass 346 half-spin chirality = the multiplier character mu = frame orientation parity = sign on "
                    "factorisations = sign on gauge lines (BT877), but not the sign on the 40 points; mu = 1 exactly on antiunitary "
                    "Clifford operations (e92a047)."),
            "inn": ("BT869's 45-class involutions are local charge conjugations C (x) I of the 45 tensor factorisations "
                    "(79e8074), fixed set = the octet; inner (mu = 0), so they preserve every orientation class: a 45 + 36 "
                    "grading, not an exchange."),
            "consequence": ("since W(E6) fixes (ABS) and exchanges (REL), no W(E6)-equivariant map sends absolute types to "
                            "half-spins; selecting handedness requires breaking every antiunitary symmetry."),
            "boundary": "exact finite computation for mu and the involution class; equivariance argument for (ABS); no particle assignment.",
        }
        pth = os.path.join(ROOT, "data", "corpus_three_chiralities.json")
        with open(pth, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=2)
        print("written: %s" % pth)


if __name__ == "__main__":
    main()
