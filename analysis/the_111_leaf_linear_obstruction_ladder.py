#!/usr/bin/env python3
"""Outside-box linear obstruction ladder for frozen tau2=111 tile matrices.

The exact leaf lift asks for a binary 40x40 matrix X with

    T = N X N^T.

Before invoking nonlinear 0/1/blocker constraints, test the corresponding
linear map over several finite fields.  If T is not in the bilateral incidence
image for any prime, that alone certifies impossibility.  If it is in the image,
this quantifies exactly how much linear freedom remains and proves that the
observed leaf-lift UNSAT is genuinely nonlinear at that characteristic.

For a square matrix N of rank r over F_p, the linear map X -> N X N^T has rank
r^2 and nullity 1600-r^2.  T lies in its image iff every column lies in col(N)
and every row lies in row(N^T).  We test p=2,3,5,7 for all three frozen
factorizations, using T=J+E reconstructed independently from both token sides.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FACTOR = ROOT / "data" / "the_111_two_pencil_factorization.json"
OUT = ROOT / "data" / "the_111_leaf_linear_obstruction_ladder.json"
PRIMES = (2, 3, 5, 7)


def geometry():
    path = ROOT / "analysis" / "the_10480_twelve_point_blockers.py"
    spec = importlib.util.spec_from_file_location("b12_linear_ladder", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import geometry")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _lines, _adj, N = mod.geometry()
    return N


def rank_mod(rows, p):
    A = [[int(x) % p for x in row] for row in rows]
    if not A:
        return 0
    m, n = len(A), len(A[0]); r = 0
    for c in range(n):
        pivot = next((i for i in range(r, m) if A[i][c] % p), None)
        if pivot is None:
            continue
        A[r], A[pivot] = A[pivot], A[r]
        inv = pow(A[r][c] % p, -1, p)
        A[r] = [(x * inv) % p for x in A[r]]
        for i in range(m):
            if i == r or not A[i][c] % p:
                continue
            f = A[i][c] % p
            A[i] = [(A[i][j] - f * A[r][j]) % p for j in range(n)]
        r += 1
        if r == m:
            break
    return r


def in_colspace(N, v, p):
    # rank([N|v]) == rank(N)
    aug = [list(row) + [v[i]] for i, row in enumerate(N)]
    return rank_mod(aug, p) == rank_mod(N, p)


def transpose(A):
    return [list(x) for x in zip(*A)]


def reconstruct_T(row, N):
    rt, ct = row["rowTokens"], row["columnTokens"]
    E1 = [[sum(N[j][q] for q in rt[i]) for j in range(40)] for i in range(40)]
    E2 = [[sum(N[i][q] for q in ct[j]) for j in range(40)] for i in range(40)]
    assert E1 == E2 and sum(sum(x) for x in E1) == 176
    return [[1 + E1[i][j] for j in range(40)] for i in range(40)]


def main():
    N = geometry(); NT = transpose(N)
    factor = json.loads(FACTOR.read_text())
    assert factor["status"] == "PASS"
    ranks = {}
    for p in PRIMES:
        r = rank_mod(N, p)
        ranks[str(p)] = {"rankN": r, "mapRank": r * r, "mapNullity": 1600 - r * r}

    cases = {}
    all_consistent = True
    for name, row in sorted(factor["cases"].items()):
        T = reconstruct_T(row, N)
        per = {}
        for p in PRIMES:
            col_ok = all(in_colspace(N, [T[i][j] for i in range(40)], p) for j in range(40))
            row_ok = all(in_colspace(NT, T[i], p) for i in range(40))
            consistent = col_ok and row_ok
            all_consistent &= consistent
            per[str(p)] = {
                "consistent": consistent,
                "allColumnsInColN": col_ok,
                "allRowsInRowNT": row_ok,
                **ranks[str(p)],
            }
        cases[name] = per

    out = {
        "schema": "holotrade.tau2-111-leaf-linear-obstruction-ladder.v1",
        "status": "PASS",
        "primes": list(PRIMES),
        "incidenceRanks": ranks,
        "cases": cases,
        "allFrozenTileMatricesPassAllLinearImages": all_consistent,
        "consequence": (
            "If all consistency flags are true, the three frozen exact-leaf UNSAT results cannot be explained by the bare linear equation T=N X N^T over F2,F3,F5,F7. Their obstruction uses integrality/0-1/local blocker matching beyond these field-linear images."
        ),
        "boundary": "A linear consistency pass never proves existence of a binary 111-leaf blocker; it only rules out a class of linear obstructions. A failure at any prime would be an exact impossibility certificate for that frozen T.",
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    if "--write" in __import__("sys").argv:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
