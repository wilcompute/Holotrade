#!/usr/bin/env python3
"""
The chirality torsor has a two-qutrit name. The 32 orientations of a complete
factorisation frame -- which qutrit is called "first" in each of its five
tensor factorisations -- split 16 + 16 exactly as the weights of the two
half-spin representations of D5 do. Unitary Clifford operations preserve each
half. Antiunitary ones -- complex conjugation composed with a Clifford --
exchange them, and nothing else does.

PRIOR ART, CITED.
  * the_27_factorisation_frames_carry_the_so10_weights.py (5419c27): a line of
    the cubic surface is a complete factorisation frame; its stabiliser is
    W(D5) and the kernel on its five factorisations is the even sign-change
    group, realised as exchanging the two qutrits of an even number of them.
  * W33-Theory Pass 346 (THE_SELECTION_LAYER.md): the substrate carries chiral
    half-spin modules S+ and S-, an element of W(E6) = PGSp(4,3) outside the
    index-2 subgroup exchanges them, so no invariant selects a chirality; the
    missing input is a SECTION of a two-element torsor.
  * W33-Theory BT1041 / BT1045: the finite Dirac candidate on
    K = C^3_weak (x) C^3_colour with an antiunitary real structure J satisfying
    J gamma = - gamma J (the KO-dimension-6 sign), with gamma imposed on an extra
    C^2_chiral factor.

WHAT IS ADDED. An intrinsic Z_2 on K's own Pauli geometry, with a named
physical operation that flips it.

  ORIENTATION PARITY.  Orient each octet of a frame by choosing one of its two
  hyperbolic lines H_i (one tensor factor). A collineation g preserving the
  frame carries orientations to orientations; the number of octets whose
  orientation it reverses, mod 2, is a homomorphism Stab(F) -> Z_2 that does
  not depend on the reference orientations chosen. Computed on ALL 27 frames:

      PSp(4,3) part of the stabiliser (960 elements)     parity 0, every one
      multiplier -1 part (the other 960)                 parity 1, every one

  So orientation parity IS the index-2 character of Aut W(3,3) = W(E6).

  THE SIXTEEN AND THE SIXTEEN.  The 32 orientations of a frame fall into two
  orbits of 16 under the PSp(4,3)-stabiliser (even and odd numbers of reversals
  from a reference -- the weight sets of S+ and S- of D5), and into a single
  orbit of 32 under the full stabiliser. The even sign-change kernel acts
  regularly on each 16.

  WHICH PHYSICAL OPERATIONS ARE ODD.  The Pauli label map of a unitary Clifford
  preserves the commutation phase; that of an ANTIUNITARY operation reverses
  it. Checked on 9x9 matrices: complex conjugation sends every two-qutrit Pauli
  to a Pauli whose label is (a1, a2, -b1, -b2), and reverses the commutation
  exponent on all 3160 ordered pairs -- a similitude of multiplier -1, the odd
  coset. Hadamard, phase and CSUM gates preserve it -- the even coset. Hence:

      a unitary Clifford that preserves a frame never changes its chirality;
      an antiunitary one that preserves it always does.

WHAT IT MEANS.  The torsor Pass 346 proved unselectable is, on the two-qutrit
carrier, the orientation parity of a factorisation frame -- a convention for
ordering subsystems modulo even changes -- and the operations that exchange the
two halves are exactly the time-reversal-type ones. This is the same sign
pattern as J gamma = - gamma J in BT1041, now arising from the geometry of K
itself rather than from an adjoined C^2. It does not select a chirality: it
names what a selection would have to fix, and confirms that no unitary
symmetry can.

SCOPE.  Exact computation with the collineation groups (25920, 51840) on all 27
frames, and with 9x9 matrices for the gate cosets. Group- and weight-level only:
no Dirac operator, gauge field or fermion assignment is constructed, and the
correspondence with BT1041's J is a shared sign pattern, not a proved equality
of operators.
"""

import argparse
import itertools
import json
import os
from collections import Counter, deque

import numpy as np
import importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Q = 3


def frames_module():
    p = os.path.join(ROOT, "analysis", "the_27_factorisation_frames_carry_the_so10_weights.py")
    spec = importlib.util.spec_from_file_location("frames27", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def gate_multipliers():
    w = np.exp(2j * np.pi / 3)
    X = np.roll(np.eye(3), 1, axis=0)
    Z = np.diag([w ** j for j in range(3)])
    I = np.eye(3)

    def pauli(a1, a2, b1, b2):
        return np.kron(np.linalg.matrix_power(X, a1) @ np.linalg.matrix_power(Z, b1),
                       np.linalg.matrix_power(X, a2) @ np.linalg.matrix_power(Z, b2))
    labels = [v for v in itertools.product(range(3), repeat=4) if any(v)]
    mats = {v: pauli(*v) for v in labels}

    def label_of(M):
        for v, P in mats.items():
            if abs(abs(np.vdot(P.flatten(), M.flatten())) / 9 - 1) < 1e-9:
                return v
        raise AssertionError("not a Pauli")

    def form(u, v):          # labels (a1, a2, b1, b2)
        return (u[0] * v[2] - u[2] * v[0] + u[1] * v[3] - u[3] * v[1]) % 3

    def multiplier(action):
        img = {v: label_of(action(P)) for v, P in mats.items()}
        ratios = set()
        for u, v in itertools.product(labels, labels):
            fu = form(u, v)
            fi = form(img[u], img[v])
            if fu:
                ratios.add((fi * pow(fu, -1, 3)) % 3)
            elif fi:
                ratios.add("broken")
        return ratios, img

    H = np.array([[w ** (j * k) for k in range(3)] for j in range(3)]) / np.sqrt(3)
    S = np.diag([w ** (j * (j - 1) // 2) for j in range(3)])
    CSUM = np.zeros((9, 9))
    for a in range(3):
        for b in range(3):
            CSUM[a * 3 + (a + b) % 3, a * 3 + b] = 1
    out = {}
    for name, U in (("H(x)I", np.kron(H, I)), ("S(x)I", np.kron(S, I)), ("CSUM", CSUM)):
        r, _ = multiplier(lambda P, U=U: U @ P @ U.conj().T)
        out[name] = sorted(r, key=str)
    r, img = multiplier(lambda P: P.conj())
    out["complexConjugation"] = sorted(r, key=str)
    conj_is_diag = all(img[v] == (v[0], v[1], (-v[2]) % 3, (-v[3]) % 3) for v in labels)
    return out, conj_is_diag


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    m = frames_module()
    pts, idx, nm, n, tlines, octs, halves = m.geometry()
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

    gens = [mat_perm(tv(v)) for v in pts]
    CONJ = mat_perm([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 2, 0], [0, 0, 0, 2]])
    G1 = closure(gens)
    G2 = closure(gens + [CONJ])

    def img(g, S):
        return frozenset(g[x] for x in S)

    parity_rows = []
    orbit_rows = []
    for f in frames:
        FO = [octs[i] for i in f]
        stab = [g for g in G2 if {img(g, O) for O in FO} == set(FO)]
        par = {"psp": Counter(), "outer": Counter()}
        for g in stab:
            flips = sum(0 if img(g, halves[O][0]) == halves[img(g, O)][0] else 1 for O in FO)
            par["psp" if g in G1 else "outer"][flips % 2] += 1
        parity_rows.append({"psp": dict(par["psp"]), "outer": dict(par["outer"])})
        # orientations as tuples of chosen halves; orbits under the two stabilisers
        orients = list(itertools.product((0, 1), repeat=5))

        def act(g, o):
            chosen = {img(g, halves[O][o[i]]) for i, O in enumerate(FO)}
            return tuple(0 if halves[O][0] in chosen else 1 for O in FO)

        def orbits(group):
            rem, sizes = set(orients), []
            while rem:
                s = rem.pop()
                orb = {act(g, s) for g in group}
                rem -= orb
                sizes.append(len(orb))
            return sorted(sizes)
        orbit_rows.append({"psp": orbits([g for g in stab if g in G1]), "full": orbits(stab)})

    gates, conj_is_diag = gate_multipliers()

    parity_ok = all(r["psp"] == {0: 960} and r["outer"] == {1: 960} for r in parity_rows)
    orbit_ok = all(r["psp"] == [16, 16] and r["full"] == [32] for r in orbit_rows)
    gates_ok = (gates["H(x)I"] == [1] and gates["S(x)I"] == [1] and gates["CSUM"] == [1]
                and gates["complexConjugation"] == [2] and conj_is_diag and CONJ not in G1 and CONJ in G2)

    print("FRAME CHIRALITY IS REVERSED ONLY BY ANTIUNITARIES")
    print("=" * 74)
    print("  frames %d; PSp(4,3) %d; Aut W(3,3) %d" % (len(frames), len(G1), len(G2)))
    print("  orientation parity on every frame stabiliser: PSp part all even, multiplier -1 part all odd: %s"
          % parity_ok)
    print("  orientations per frame: PSp-stabiliser orbits %s, full-stabiliser orbits %s  (all frames: %s)"
          % (orbit_rows[0]["psp"], orbit_rows[0]["full"], orbit_ok))
    print("  commutation-form multipliers on 9x9 matrices: %s" % gates)
    print("  complex conjugation acts on labels as (a1,a2,b1,b2) -> (a1,a2,-b1,-b2): %s; outside PSp: %s"
          % (conj_is_diag, CONJ not in G1))
    ok = len(frames) == 27 and len(G1) == 25920 and len(G2) == 51840 and parity_ok and orbit_ok and gates_ok
    print()
    print("VALID: %s" % ok)

    if args.write:
        assert ok, "checks failed -- refusing to write"
        rec = {
            "schema": "holotrade.frame-chirality-antiunitary.v1",
            "valid": True,
            "frames": len(frames), "pspOrder": len(G1), "fullOrder": len(G2),
            "parityPerFrame": parity_rows[0],
            "parityAllFramesAsStated": parity_ok,
            "orientationOrbitsPsp": orbit_rows[0]["psp"],
            "orientationOrbitsFull": orbit_rows[0]["full"],
            "orientationOrbitsAllFramesAsStated": orbit_ok,
            "gateMultipliers": {k: [str(x) for x in v] for k, v in gates.items()},
            "complexConjugationLabelMap": "(a1,a2,b1,b2) -> (a1,a2,-b1,-b2)",
            "complexConjugationIsThatMap": conj_is_diag,
            "priorArt": (
                "5419c27 (frames and W(D5)); W33-Theory Pass 346 THE_SELECTION_LAYER.md (chirality torsor, "
                "exchange by an element outside the index-2 subgroup); BT1041/BT1045 (J antiunitary with "
                "J gamma = - gamma J on K = C^3_weak (x) C^3_colour)."),
            "orientationParity": (
                "orienting each octet of a frame by one of its two hyperbolic lines, the parity of the number of "
                "orientations reversed by a frame-preserving collineation is a homomorphism to Z_2. On all 27 frames "
                "it is 0 on the 960 PSp(4,3) elements and 1 on the 960 multiplier -1 elements: it is the index-2 "
                "character of W(E6)."),
            "theSixteenAndTheSixteen": (
                "the 32 orientations of a frame form two orbits of 16 under the PSp(4,3)-stabiliser -- even and odd "
                "numbers of reversals, the weight sets of S+ and S- of D5 -- and one orbit of 32 under the full "
                "stabiliser."),
            "whichOperationsAreOdd": (
                "checked with 9x9 matrices over all ordered Pauli pairs: H, S and CSUM preserve the commutation "
                "form (multiplier 1); complex conjugation reverses it (multiplier -1) and acts on labels as "
                "(a1,a2,b1,b2) -> (a1,a2,-b1,-b2), outside PSp(4,3). Unitary Cliffords preserving a frame keep "
                "its chirality; antiunitary ones reverse it."),
            "whatItMeans": (
                "the torsor Pass 346 proved unselectable is, on the two-qutrit carrier, the orientation parity of a "
                "factorisation frame, and the operations exchanging the halves are the time-reversal-type ones -- "
                "the same sign pattern as J gamma = - gamma J in BT1041, arising from the geometry of K itself. It "
                "names what a selection would fix; it does not select one."),
            "boundary": (
                "exact computation with the collineation groups on all 27 frames and with 9x9 matrices for the gate "
                "cosets; group- and weight-level only. No Dirac operator, gauge field or fermion assignment is "
                "constructed, and the link to BT1041's J is a shared sign pattern, not an operator equality."),
        }
        p = os.path.join(ROOT, "data", "frame_chirality_antiunitary.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=2)
        print("written: %s" % p)


if __name__ == "__main__":
    main()
