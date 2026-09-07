#!/usr/bin/env python3
"""
BT768's closing question has a q-general answer: the octet matrix annihilates
the g-sector at EVERY q, and it does so for a forced reason.

WHAT WAS ASKED.  analysis/w33_bt768_o5_24_15_closure.py (Theory-of-Everything
7b4ad2101) records that BT768 "constructed 45 intrinsic W33 K4,4 octets, with
point/octet incidence M, and proved M M^T = 8I + J + 2A, spec(MM^T) =
72^1, 12^24, 0^15. It ended by asking for the missing 15-sector object killed
by M." That commit answers it at q = 3: the missing sector is the nonsquare /
spread polar frame C. Both halves of that are q-general.

THE OCTETS ARE THE THICK POINTS OF A SQUARE POLAR SECTION.  ba74506 showed
N D = J + q B with B of column weight 2(q+1); B is exactly M. So the octet
generalises to a 2(q+1)-set, and it keeps its shape:

    q     octets   octet size 2(q+1)   collinearity degree inside   bipartition
    3        45           8                      4                  K(4,4)
    5       325          12                      6                  K(6,6)
    7      1225          16                      8                  K(8,8)

Inside an octet every point is collinear with exactly q+1 others and the
complement splits into two cliques of size q+1, so the octet is K(q+1,q+1) --
BT768's K4,4 is the q = 3 member. That is the grid Q+(3,q) seen from the W33
side: a hyperbolic section has two reguli of q+1 lines each.

THE GRAM MATRIX HAS A CLOSED FORM.

    B B^T = (q^2 - 1) I + J + (q - 1) A_points

              (I, J, A)        row weight q^2     spectrum
    q=3      8   1   2              9             72^1,  12^24,  0^15
    q=5     24   1   4             25            300^1,  40^90,  0^65
    q=7     48   1   6             49            784^1,  84^224, 0^175

verified entrywise at q = 3, 5, 7. The q = 3 row is BT768's 8I + J + 2A and its
spectrum 72, 12^24, 0^15 exactly.

THE ANNIHILATION IS FORCED, NOT OBSERVED.  On the g-sector A_points takes the
value -(q+1), so the eigenvalue of B B^T there is

    (q^2 - 1) - (q - 1)(q + 1) = 0

identically in q. The coefficient of I and the coefficient of A are not
independent -- (q^2-1) = (q-1)(q+1) is the whole reason the kernel exists. So
"M kills a 15-dimensional sector" is not a q = 3 coincidence to be explained
away; it is the q = 3 instance of an identity, and the sector killed always has
dimension g = q(q^2+1)/2: 15, 65, 175. The other two eigenvalues are
2q(q-1) = 12, 40, 84 on the f-sector of dimension q(q+1)^2/2 = 24, 90, 224, and
(q^2-1) + (q+1)(q^2+1) + q(q^2-1) = 72, 300, 784 on the all-ones vector.

SO THE BT768 ANSWER IS q-GENERAL IN BOTH DIRECTIONS.  What M kills is the
nonsquare / spread sector, and ba74506 already showed N C = J with N C0 = 0 at
q = 3, 5, 7 -- every nonsquare polar section is a spread because an elliptic
section of Q(4,q) is an ovoid. The object that was missing at q = 3 is missing
in the same way, and is the same object, at every q tested.

SCOPE.  q = 3, 5, 7 only, and the closed forms are read off three primes and
verified against them rather than proved -- except the kernel identity
(q^2-1) = (q-1)(q+1), which is an identity in q and needs no fitting once the
decomposition B B^T = (q^2-1)I + J + (q-1)A is granted. What IS proved for each
q tested is the decomposition itself, checked ENTRYWISE over the whole matrix,
together with the octet sizes, the internal degrees, and the bipartition into
two cliques. A_points here is the POINT collinearity graph of W(3,q), which for
odd q is not isomorphic to the line graph (W(3,q) is self-dual only for q even)
though it is co-parametric; the decomposition is against the point graph
throughout. q even and n > 2 are untouched, and so is tau_2.
"""

import itertools
import json
import os
import sys

import numpy as np

ROOT = r"C:\Repos\Holotrade"
PAIR = ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3))


def study(q):
    def nm(v):
        i = next(k for k, x in enumerate(v) if x % q)
        z = pow(v[i] % q, -1, q)
        return tuple((z * x) % q for x in v)

    P3 = sorted({nm(v) for v in itertools.product(range(q), repeat=4) if any(v)})
    i3 = {p: i for i, p in enumerate(P3)}

    def sf(u, v):
        return (u[0] * v[2] - u[2] * v[0] + u[1] * v[3] - u[3] * v[1]) % q

    def wed(u, v):
        return tuple((u[i] * v[j] - u[j] * v[i]) % q for (i, j) in PAIR)

    lines = {}
    for a, b in itertools.combinations(P3, 2):
        if sf(a, b) % q:
            continue
        pts = set()
        for x in range(q):
            for y in range(q):
                if x or y:
                    w = tuple((x * a[k] + y * b[k]) % q for k in range(4))
                    if any(w):
                        pts.add(nm(w))
        lines.setdefault(nm(wed(a, b)), set()).update(pts)
    L = sorted(lines)

    def Qf(b):
        return (b[0] * b[5] - b[1] * b[4] + b[2] * b[3]) % q

    def nm6(b):
        i = next(k for k, x in enumerate(b) if x % q)
        z = pow(b[i] % q, -1, q)
        return tuple((z * x) % q for x in b)

    PW = sorted({nm6(b) for b in itertools.product(range(q), repeat=6)
                 if any(b) and (b[1] + b[4]) % q == 0})

    def Bf(u, v):
        s = tuple((u[i] + v[i]) % q for i in range(6))
        return (Qf(s) - Qf(u) - Qf(v)) % q

    sq = {(x * x) % q for x in range(1, q)}
    SQ = [b for b in PW if Qf(b) % q in sq]

    D = np.array([[1 if Bf(y, c) % q == 0 else 0 for c in SQ] for y in L],
                 dtype=np.int64)
    n = len(P3)
    N = np.zeros((n, len(L)), dtype=np.int64)
    for li, lp in enumerate(L):
        for p in lines[lp]:
            N[i3[p], li] = 1
    B = ((N @ D) - 1) // q

    Ap = np.zeros((n, n), dtype=np.int64)
    for a in range(n):
        for b in range(n):
            if a != b and sf(P3[a], P3[b]) % q == 0:
                Ap[a, b] = 1

    I = np.eye(n, dtype=np.int64)
    J = np.ones((n, n), dtype=np.int64)
    BB = B @ B.T
    oA = next((i, j) for i in range(n) for j in range(n) if i != j and Ap[i, j])
    oN = next((i, j) for i in range(n) for j in range(n)
              if i != j and not Ap[i, j])
    bb = int(BB[oN])
    cc = int(BB[oA]) - bb
    aa = int(BB[0, 0]) - bb
    exact = bool(np.array_equal(BB, aa * I + bb * J + cc * Ap))

    # octet shape: size 2(q+1), internal degree q+1, complement = 2 K_{q+1}
    sizes, degs, biparts = set(), set(), []
    for c in range(B.shape[1]):
        oc = [i for i in range(n) if B[i, c]]
        m = len(oc)
        S = Ap[np.ix_(oc, oc)]
        sizes.add(m)
        degs.add(tuple(sorted(set(S.sum(1).tolist()))))
        comp = 1 - S - np.eye(m, dtype=np.int64)
        seen, comps = set(), []
        for s in range(m):
            if s in seen:
                continue
            stack, part = [s], []
            while stack:
                x = stack.pop()
                if x in seen:
                    continue
                seen.add(x)
                part.append(x)
                stack += [y for y in range(m) if comp[x, y] and y not in seen]
            comps.append(sorted(part))
        biparts.append(sorted(len(p) for p in comps) == [q + 1, q + 1]
                       and all(comp[np.ix_(p, p)].sum() == len(p) * (len(p) - 1)
                               for p in comps))

    f, g = q * (q + 1) ** 2 // 2, q * (q * q + 1) // 2
    ev = np.round(np.linalg.eigvalsh(BB.astype(float)), 6)
    mult = {}
    for x in ev:
        mult[float(abs(x))] = mult.get(float(abs(x)), 0) + 1
    big = (q * q - 1) + (q + 1) * (q * q + 1) + q * (q * q - 1)

    return {
        "q": q, "points": n, "octets": int(B.shape[1]),
        "octetSize": sorted(sizes), "internalDegrees": [list(d) for d in degs],
        "isCompleteBipartite": bool(all(biparts)),
        "BBT": [aa, bb, cc], "BBTexact": exact,
        "closedForm": [q * q - 1, 1, q - 1],
        "closedFormMatches": [aa, bb, cc] == [q * q - 1, 1, q - 1],
        "rowWeight": sorted(set(B.sum(1).tolist())),
        "columnWeight": sorted(set(B.sum(0).tolist())),
        "spectrum": {"zero": int(mult.get(0.0, 0)),
                     "middle": int(mult.get(float(2 * q * (q - 1)), 0)),
                     "top": int(mult.get(float(big), 0))},
        "predictedSpectrum": {"zero": g, "middle": f, "top": 1,
                              "middleValue": 2 * q * (q - 1), "topValue": big},
        "spectrumMatches": (mult.get(0.0, 0) == g
                            and mult.get(float(2 * q * (q - 1)), 0) == f
                            and mult.get(float(big), 0) == 1),
        "kernelIsForced": (q * q - 1) - (q - 1) * (q + 1) == 0,
    }


def main():
    rows = [study(q) for q in (3, 5, 7)]

    print("THE OCTET MATRIX IS q-GENERAL")
    print("=" * 72)
    print("  BT768 (TOE 7b4ad2101) proved M M^T = 8I + J + 2A with spectrum")
    print("  72^1, 12^24, 0^15 and asked for the missing 15-sector. Both the")
    print("  question and the answer generalise.")
    print()
    print("    q   octets   size 2(q+1)   internal deg   K(q+1,q+1)")
    for r in rows:
        print("   %2d    %5d        %3d            %3d           %s"
              % (r["q"], r["octets"], r["octetSize"][0],
                 r["internalDegrees"][0][0], r["isCompleteBipartite"]))
    print("  BT768's K4,4 is the q = 3 member: a hyperbolic section is a grid")
    print("  Q+(3,q) with two reguli of q+1 lines.")
    print()
    print("  B B^T = (q^2-1) I + J + (q-1) A_points")
    print("     q    (I, J, A)      row wt   spectrum (value^multiplicity)")
    for r in rows:
        p = r["predictedSpectrum"]
        print("    %2d   %3d %2d %2d        %3d     %d^1, %d^%d, 0^%d"
              % (r["q"], r["BBT"][0], r["BBT"][1], r["BBT"][2],
                 r["rowWeight"][0], p["topValue"], p["middleValue"],
                 p["middle"], p["zero"]))
    print("  exact entrywise: %s ; spectrum as predicted: %s"
          % (all(r["BBTexact"] and r["closedFormMatches"] for r in rows),
             all(r["spectrumMatches"] for r in rows)))
    print()
    print("  THE ANNIHILATION IS FORCED. On the g-sector A_points = -(q+1), so")
    print("  the eigenvalue is (q^2-1) - (q-1)(q+1) = 0 identically. The I and")
    print("  A coefficients are not independent -- that identity IS the kernel.")
    print("  So 'M kills a 15-dimensional sector' is not a q = 3 coincidence:")
    print("  it is the q = 3 instance of an identity, and the sector killed")
    print("  always has dimension g = q(q^2+1)/2 = %s."
          % [r["predictedSpectrum"]["zero"] for r in rows])
    print()
    print("  And what it kills is the spread sector: ba74506 showed N C = J")
    print("  with N C0 = 0 at q = 3, 5, 7, because an elliptic section of")
    print("  Q(4,q) is an ovoid. Same object, same way, every q tested.")

    ok = all(r["BBTexact"] and r["closedFormMatches"] and r["spectrumMatches"]
             and r["isCompleteBipartite"] and r["kernelIsForced"]
             and r["octetSize"] == [2 * (r["q"] + 1)]
             and r["rowWeight"] == [r["q"] ** 2] for r in rows)

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "octet_matrix_q_general.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.octet-matrix-q-general.v1",
                "valid": bool(ok),
                "whatWasAsked": ("analysis/w33_bt768_o5_24_15_closure.py "
                                 "(Theory-of-Everything 7b4ad2101) records that "
                                 "BT768 constructed 45 intrinsic W33 K4,4 octets "
                                 "with point/octet incidence M and proved "
                                 "M M^T = 8I + J + 2A with spectrum 72^1, 12^24, "
                                 "0^15, and 'ended by asking for the missing "
                                 "15-sector object killed by M'. That commit "
                                 "answers it at q = 3; both halves are q-general"),
                "rows": rows,
                "theOctetGeneralises": ("ba74506 showed N D = J + q B with B of "
                                        "column weight 2(q+1), and B is exactly "
                                        "M; inside an octet every point is "
                                        "collinear with exactly q+1 others and "
                                        "the complement splits into two cliques "
                                        "of size q+1, so the octet is "
                                        "K(q+1,q+1) and BT768's K(4,4) is its "
                                        "q = 3 member -- the grid Q+(3,q) seen "
                                        "from the W33 side, two reguli of q+1 "
                                        "lines"),
                "closedForm": "B B^T = (q^2 - 1) I + J + (q - 1) A_points",
                "theAnnihilationIsForced": ("on the g-sector A_points takes the "
                                            "value -(q+1), so the eigenvalue of "
                                            "B B^T there is "
                                            "(q^2-1) - (q-1)(q+1) = 0 identically "
                                            "in q; the I and A coefficients are "
                                            "NOT independent, and that identity "
                                            "is the whole reason the kernel "
                                            "exists. 'M kills a 15-dimensional "
                                            "sector' is therefore not a q = 3 "
                                            "coincidence but the q = 3 instance "
                                            "of an identity, and the sector "
                                            "killed always has dimension "
                                            "g = q(q^2+1)/2: 15, 65, 175"),
                "andWhatItKillsIsTheSpreadSector": ("ba74506 showed N C = J with "
                                                    "N C0 = 0 at q = 3, 5, 7, "
                                                    "because an elliptic section "
                                                    "of Q(4,q) is an ovoid and "
                                                    "dually a spread; the object "
                                                    "missing at q = 3 is missing "
                                                    "in the same way, and is the "
                                                    "same object, at every q "
                                                    "tested"),
                "boundary": ("q = 3, 5, 7 only, and the closed forms are read off "
                             "three primes and verified against them rather than "
                             "proved -- EXCEPT the kernel identity "
                             "(q^2-1) = (q-1)(q+1), which is an identity in q and "
                             "needs no fitting once the decomposition is granted. "
                             "What IS proved for each q tested is the "
                             "decomposition itself, checked ENTRYWISE over the "
                             "whole matrix, together with the octet sizes, the "
                             "internal degrees and the bipartition into two "
                             "cliques. A_points is the POINT collinearity graph "
                             "of W(3,q), which for odd q is NOT isomorphic to the "
                             "line graph (W(3,q) is self-dual only for q even) "
                             "though it is co-parametric; the decomposition is "
                             "against the point graph throughout. q even and "
                             "n > 2 are untouched, and so is tau_2"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
