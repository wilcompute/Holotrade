#!/usr/bin/env python3
"""
Independent cross-check of analysis/w33_shape_catalogue.js.

The JS catalogue reaches its answers by COMBINATORIAL SEARCH: backtracking
over neighbourhood-count constraints. This file reaches them by LINEAR
ALGEBRA: it builds the adjacency matrix, diagonalises it, and tests each
reported witness by projecting its indicator vector onto the eigenspaces.

Two different methods, no shared code path, no shared graph construction --
the point graph is rebuilt here from the symplectic form directly. If the
two agree, the result is not an artefact of one implementation.

  py -3 analysis/w33_shape_catalogue_check.py
"""

import itertools
import json
import os
import sys

try:
    import numpy as np
except ImportError:
    sys.exit("needs numpy: py -3 -m pip install numpy")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


# ---------------------------------------------------------------------
# Rebuild W(3,3) from scratch -- deliberately not importing anything JS
# ---------------------------------------------------------------------
def build_points():
    """The 40 projective points of PG(3, F_3), first nonzero coord = 1."""
    seen, pts = {}, []
    for v in itertools.product(range(3), repeat=4):
        if all(x == 0 for x in v):
            continue
        lead = next(x for x in v if x != 0)
        inv = 1 if lead == 1 else 2          # 2*2 = 1 mod 3
        norm = tuple((x * inv) % 3 for x in v)
        if norm in seen:
            continue
        seen[norm] = len(pts)
        pts.append(norm)
    return pts


def symplectic(u, v):
    """<u,v> = u0*v1 - u1*v0 + u2*v3 - u3*v2  (mod 3)."""
    return (u[0] * v[1] - u[1] * v[0] + u[2] * v[3] - u[3] * v[2]) % 3


POINTS = build_points()
N = len(POINTS)
A = np.zeros((N, N), dtype=int)
for i in range(N):
    for j in range(N):
        if i != j and symplectic(POINTS[i], POINTS[j]) == 0:
            A[i, j] = 1

ONE = np.ones(N)


def report(ok, label, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f"  {detail}" if detail else ""))
    return ok


def main():
    print("INDEPENDENT SPECTRAL CROSS-CHECK OF THE W(3,3) SHAPE CATALOGUE")
    print("=" * 68)
    allok = True

    # ---- the graph itself --------------------------------------------
    print("\nGRAPH")
    deg = A.sum(axis=1)
    allok &= report(N == 40, "40 points", f"got {N}")
    allok &= report(bool((deg == 12).all()), "12-regular")
    allok &= report(int(A.sum() // 2) == 240, "240 edges", f"got {int(A.sum()//2)}")

    A2 = A @ A
    lam = {A2[i, j] for i in range(N) for j in range(N) if i != j and A[i, j] == 1}
    mu = {A2[i, j] for i in range(N) for j in range(N) if i != j and A[i, j] == 0}
    allok &= report(lam == {2}, "lambda = 2", str(lam))
    allok &= report(mu == {4}, "mu = 4", str(mu))

    # ---- the spectrum the bounds are derived from --------------------
    print("\nSPECTRUM")
    ev = np.linalg.eigvalsh(A.astype(float))
    rounded = np.round(ev).astype(int)
    allok &= report(bool(np.allclose(ev, rounded, atol=1e-8)), "eigenvalues are integers")
    counts = {int(v): int((rounded == v).sum()) for v in sorted(set(rounded.tolist()))}
    allok &= report(counts == {-4: 15, 2: 24, 12: 1},
                    "spectrum {12^1, 2^24, (-4)^15}", str(counts))

    # ---- eigenprojectors ---------------------------------------------
    # P_2  = (A - 12I)(A + 4I) / ((2-12)(2+4))
    # P_-4 = (A - 12I)(A - 2I) / ((-4-12)(-4-2))
    I = np.eye(N)
    P2 = (A - 12 * I) @ (A + 4 * I) / ((2 - 12) * (2 + 4))
    Pm4 = (A - 12 * I) @ (A - 2 * I) / ((-4 - 12) * (-4 - 2))
    P1 = np.outer(ONE, ONE) / N
    allok &= report(bool(np.allclose(P1 + P2 + Pm4, I, atol=1e-9)),
                    "projectors resolve the identity")

    # ---- load the JS catalogue and test every witness ----------------
    cat_path = os.path.join(ROOT, "data", "w33_shape_catalogue.json")
    if not os.path.exists(cat_path):
        print(f"\n(no frozen catalogue at {cat_path}; run the JS with --write first)")
        return 0 if allok else 1
    with open(cat_path) as fh:
        cat = json.load(fh)

    print("\nTIGHT SETS  (indicator must have ZERO component in the -4 eigenspace)")
    for row in cat["tightSets"]:
        if not row.get("witness"):
            continue
        T = row["witness"]
        x = np.zeros(N)
        x[T] = 1.0
        resid = float(np.linalg.norm(Pm4 @ x))
        e = int(sum(A[i, j] for i in T for j in T) // 2)
        b = int(sum(A[i, j] for i in T for j in range(N) if j not in set(T)))
        bound = row["boundInducedEdges"]
        ok = resid < 1e-9 and e == bound and (2 * e + b) == 12 * len(T)
        allok &= report(ok, f"m={len(T):>2}  e(T)={e:>3} (bound {bound:>3})  b(T)={b:>3}",
                        f"|P_-4 1_T| = {resid:.2e}")

    print("\nm-OVOIDS  (indicator must have ZERO component in the 2 eigenspace)")
    for row in cat["mOvoids"]:
        if not row.get("witness"):
            continue
        T = row["witness"]
        x = np.zeros(N)
        x[T] = 1.0
        resid = float(np.linalg.norm(P2 @ x))
        e = int(sum(A[i, j] for i in T for j in T) // 2)
        b = int(sum(A[i, j] for i in T for j in range(N) if j not in set(T)))
        bound = row["boundInducedEdges"]
        ok = resid < 1e-9 and e == bound and (2 * e + b) == 12 * len(T)
        allok &= report(ok, f"m={len(T):>2}  e(T)={e:>3} (bound {bound:>3})  b(T)={b:>3}",
                        f"|P_2 1_T| = {resid:.2e}")

    # ---- non-existence claims ----------------------------------------
    # The JS search reports these sizes as impossible. Independently
    # confirm the strongest one: no 10-set is independent, which is what
    # an ovoid of this quadrangle would have to be.
    print("\nNON-EXISTENCE")
    alpha = cat["extremes"]["independenceNumber"]
    omega = cat["extremes"]["cliqueNumber"]

    ind_w = cat["extremes"]["independenceWitness"]
    ok = all(A[i, j] == 0 for i in ind_w for j in ind_w if i != j)
    allok &= report(ok, f"independence witness of size {len(ind_w)} has no internal edge")

    cli_w = cat["extremes"]["cliqueWitness"]
    ok = all(A[i, j] == 1 for i in cli_w for j in cli_w if i != j)
    allok &= report(ok, f"clique witness of size {len(cli_w)} is complete")

    # exhaustive independent-set search by a different algorithm:
    # grow only in increasing-index order over the complement graph
    best = [0]

    def grow(chosen, cands):
        if len(chosen) > best[0]:
            best[0] = len(chosen)
        for idx, v in enumerate(cands):
            if len(chosen) + len(cands) - idx <= best[0]:
                return
            grow(chosen + [v], [u for u in cands[idx + 1:] if A[v, u] == 0])

    grow([], list(range(N)))
    allok &= report(best[0] == alpha,
                    f"independent alpha = {best[0]} by an independent search",
                    f"catalogue says {alpha}")
    allok &= report(alpha < 10,
                    "Hoffman ratio bound 10 is NOT attained",
                    f"alpha = {alpha}, so this quadrangle has no ovoid")
    allok &= report(omega == 4, "clique number 4 attains its Hoffman bound")

    # ---- complementation theorem -------------------------------------
    # If T is intriguing of one type, so is its complement. Check it on
    # every witness rather than only asserting it.
    print("\nCOMPLEMENTATION")
    for row in cat["tightSets"]:
        if not row.get("witness"):
            continue
        T = set(row["witness"])
        C = [v for v in range(N) if v not in T]
        x = np.zeros(N)
        x[C] = 1.0
        resid = float(np.linalg.norm(Pm4 @ x))
        allok &= report(resid < 1e-9,
                        f"complement of the m={len(T)} tight set is tight (m={len(C)})",
                        f"|P_-4| = {resid:.1e}")

    print("\n" + "=" * 68)
    print("ALL INDEPENDENT CHECKS PASS" if allok else "*** DISAGREEMENT WITH THE JS CATALOGUE ***")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
