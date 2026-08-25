#!/usr/bin/env python3
"""
Numerical check of the level-2 closed-form spectra.

analysis/w33_level2.js states the spectra of the Cartesian and
lexicographic products in closed form, derived from the level-1 spectrum
rather than computed. Closed forms are exactly the kind of thing that is
right in the textbook and wrong in the transcription, so this builds the
1600x1600 adjacency matrices and diagonalises them.

  py -3 analysis/w33_level2_check.py
"""

import itertools
import json
import os
import subprocess
import sys

try:
    import numpy as np
except ImportError:
    sys.exit("needs numpy")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
N1 = 40


def build_level1():
    seen, pts = {}, []
    for v in itertools.product(range(3), repeat=4):
        if all(x == 0 for x in v):
            continue
        lead = next(x for x in v if x != 0)
        inv = 1 if lead == 1 else 2
        norm = tuple((x * inv) % 3 for x in v)
        if norm not in seen:
            seen[norm] = len(pts)
            pts.append(norm)
    form = lambda u, w: (u[0]*w[1] - u[1]*w[0] + u[2]*w[3] - u[3]*w[2]) % 3
    A = np.zeros((N1, N1), dtype=int)
    for i in range(N1):
        for j in range(N1):
            if i != j and form(pts[i], pts[j]) == 0:
                A[i, j] = 1
    return A


A1 = build_level1()
I = np.eye(N1, dtype=int)
J = np.ones((N1, N1), dtype=int)


def spectrum(M, tol=1e-7):
    ev = np.linalg.eigvalsh(M.astype(float))
    rounded = np.rint(ev).astype(int)
    integral = bool(np.allclose(ev, rounded, atol=tol))
    counts = {}
    for v in rounded:
        counts[int(v)] = counts.get(int(v), 0) + 1
    return integral, dict(sorted(counts.items(), reverse=True))


def report(ok, label, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f"  {detail}" if detail else ""))
    return ok


def main():
    print("LEVEL-2 SPECTRA — NUMERICAL CHECK OF THE CLOSED FORMS")
    print("=" * 70)
    allok = True

    # level 1, to anchor
    integral, spec1 = spectrum(A1)
    allok &= report(spec1 == {12: 1, 2: 24, -4: 15}, "level-1 spectrum", str(spec1))

    # Cartesian:  A = A1 (x) I + I (x) A1
    print("\nCARTESIAN  W [] W")
    Ac = np.kron(A1, I) + np.kron(I, A1)
    allok &= report(Ac.shape == (1600, 1600), "1600 x 1600")
    deg = Ac.sum(axis=1)
    allok &= report(bool((deg == 24).all()), "24-regular", f"min {deg.min()} max {deg.max()}")
    allok &= report(int(Ac.sum() // 2) == 19200, "19,200 edges")
    integral, spec = spectrum(Ac)
    allok &= report(integral, "eigenvalues are integers")
    expected = {}
    for a, ma in [(12, 1), (2, 24), (-4, 15)]:
        for b, mb in [(12, 1), (2, 24), (-4, 15)]:
            expected[a + b] = expected.get(a + b, 0) + ma * mb
    expected = dict(sorted(expected.items(), reverse=True))
    allok &= report(spec == expected, "matches the closed form { lambda + mu }", str(spec))
    allok &= report(sum(spec.values()) == 1600, "multiplicities sum to 1600")

    # Lexicographic: A = A1 (x) J + I (x) A1
    print("\nLEXICOGRAPHIC  W [ W ]")
    Al = np.kron(A1, J) + np.kron(I, A1)
    deg = Al.sum(axis=1)
    allok &= report(bool((deg == 492).all()), "492-regular", f"min {deg.min()} max {deg.max()}")
    allok &= report(int(Al.sum() // 2) == 393600, "393,600 edges")
    integral, spec = spectrum(Al)
    allok &= report(integral, "eigenvalues are integers")
    exp2 = {}
    for lam, m in [(12, 1), (2, 24), (-4, 15)]:
        e = N1 * lam + 12
        exp2[e] = exp2.get(e, 0) + m
    for mu, m in [(2, 24), (-4, 15)]:
        exp2[mu] = exp2.get(mu, 0) + N1 * m
    exp2 = dict(sorted(exp2.items(), reverse=True))
    allok &= report(spec == exp2, "matches the closed form", str(spec))
    allok &= report(sum(spec.values()) == 1600, "multiplicities sum to 1600")

    # expansion comparison -- the number that actually matters
    print("\nEXPANSION  (k - lambda_2)/k")
    def expansion(spec_dict):
        ks = sorted(spec_dict, reverse=True)
        k = ks[0]
        l2 = ks[0] if spec_dict[ks[0]] > 1 else ks[1]
        return k, l2, (k - l2) / k

    k1, l1, e1 = expansion(spec1)
    print(f"    level 1       ({k1} - {l1})/{k1} = {e1:.4f}")
    kc, lc, ec = expansion(spectrum(Ac)[1])
    print(f"    cartesian     ({kc} - {lc})/{kc} = {ec:.4f}")
    kl, ll, el = expansion(spectrum(Al)[1])
    print(f"    lexicographic ({kl} - {ll})/{kl} = {el:.4f}")
    allok &= report(ec < e1 and el < e1,
                    "both products expand strictly worse than a single cell")

    # cross-check the JS artifact
    art = os.path.join(ROOT, "data", "w33_level2.json")
    if os.path.exists(art):
        print("\nAGAINST THE JS ARTIFACT")
        js = json.load(open(art))
        by = {c["name"]: c for c in js["constructions"]}
        for name, M, exp in [("cartesian", Ac, expected), ("lexicographic", Al, exp2)]:
            c = by.get(name)
            if not c:
                continue
            jsspec = {int(e): int(m) for e, m in c["spectrumClosedForm"]}
            allok &= report(jsspec == exp, f"{name}: JS closed form matches numpy")
            allok &= report(c["edges"] == int(M.sum() // 2), f"{name}: edge count agrees")
            allok &= report(c["degree"]["max"] == int(M.sum(axis=1)[0]), f"{name}: degree agrees")

    print("\n" + "=" * 70)
    print("ALL CHECKS PASS" if allok else "*** MISMATCH ***")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
