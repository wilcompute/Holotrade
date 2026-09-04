#!/usr/bin/env python3
"""Optimal PSp(4,3) microsequencer with the concrete 45-slot slow-path ROM.

This is the compiler/ROM integration that the previous pass left separate.
Runtime compilation remains algorithmic: it never searches the 25,920-element
projective group.  The 45-entry certificate is consulted only to classify the
known one-extra-transvection branch and return its GQ(4,2) slot/banks.

Verification is independent and exhaustive over PSp(4,3): a BFS supplies the
pointwise ground-truth word metric for all 25,920 projective targets.  Every
algorithmic word is reconstructed and compared against that metric, and the
slow decoder is checked to be exactly the set where projective length exceeds
projective residue.
"""
from __future__ import annotations

from collections import deque
from pathlib import Path
import itertools
import json
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
Q = 3
D = 4
Matrix = tuple[tuple[int, ...], ...]
Vector = tuple[int, int, int, int]
I: Matrix = tuple(tuple(1 if i == j else 0 for j in range(D)) for i in range(D))
MINUS_I: Matrix = tuple(tuple(2 if i == j else 0 for j in range(D)) for i in range(D))
E = tuple(tuple(1 if k == j else 0 for k in range(D)) for j in range(D))


def mul(A: Matrix, B: Matrix) -> Matrix:
    return tuple(tuple(sum(A[i][k] * B[k][j] for k in range(D)) % Q for j in range(D)) for i in range(D))


def neg(A: Matrix) -> Matrix:
    return tuple(tuple((-x) % Q for x in row) for row in A)


def canonical_projective(A: Matrix) -> Matrix:
    B = neg(A)
    return min(A, B)


def form(u: Iterable[int], v: Iterable[int]) -> int:
    a = tuple(u); b = tuple(v)
    return (a[0]*b[2] - a[2]*b[0] + a[1]*b[3] - a[3]*b[1]) % Q


def act(A: Matrix, v: Vector) -> Vector:
    return tuple(sum(A[i][k] * v[k] for k in range(D)) % Q for i in range(D))  # type: ignore[return-value]


def canonical_axis(v: Vector) -> Vector:
    i = next(i for i, x in enumerate(v) if x)
    inv = pow(v[i], -1, Q)
    return tuple((inv*x) % Q for x in v)  # type: ignore[return-value]


AXES: tuple[Vector, ...] = tuple(sorted({canonical_axis(v) for v in itertools.product(range(Q), repeat=D) if any(v)}))
assert len(AXES) == 40
AXIS_INDEX = {v: i for i, v in enumerate(AXES)}


def transvection(v: Vector, lam: int) -> Matrix:
    return tuple(tuple(((1 if i == j else 0) + int(lam)*form(E[j], v)*v[i]) % Q for j in range(D)) for i in range(D))


GENS: tuple[tuple[int, int, Matrix], ...] = tuple((axis, lam, transvection(v, lam)) for axis, v in enumerate(AXES) for lam in (1, 2))
GEN_BY_MATRIX = {M: (axis, lam) for axis, lam, M in GENS}
assert len(GEN_BY_MATRIX) == 80
VECS: tuple[Vector, ...] = tuple(v for v in itertools.product(range(Q), repeat=D) if any(v))


def inverse(A: Matrix) -> Matrix:
    aug = [[A[i][j] for j in range(D)] + [1 if i == j else 0 for j in range(D)] for i in range(D)]
    r = 0
    for c in range(D):
        p = next(i for i in range(r, D) if aug[i][c] % Q)
        aug[r], aug[p] = aug[p], aug[r]
        iv = pow(aug[r][c], -1, Q)
        aug[r] = [(x*iv) % Q for x in aug[r]]
        for i in range(D):
            if i != r and aug[i][c] % Q:
                f = aug[i][c]
                aug[i] = [(aug[i][j] - f*aug[r][j]) % Q for j in range(2*D)]
        r += 1
    return tuple(tuple(aug[i][D+j] for j in range(D)) for i in range(D))


def residue(A: Matrix) -> int:
    M = [[(A[i][j] - (1 if i == j else 0)) % Q for j in range(D)] for i in range(D)]
    r = 0
    for c in range(D):
        p = next((i for i in range(r, D) if M[i][c]), None)
        if p is None:
            continue
        M[r], M[p] = M[p], M[r]
        iv = pow(M[r][c], -1, Q)
        M[r] = [(x*iv) % Q for x in M[r]]
        for i in range(D):
            if i != r and M[i][c]:
                f = M[i][c]
                M[i] = [(M[i][j] - f*M[r][j]) % Q for j in range(D)]
        r += 1
    return r


def projective_residue(A: Matrix) -> int:
    return min(residue(A), residue(neg(A)))


def is_hyperbolic(A: Matrix) -> bool:
    # q(v)=<v,Av> vanishes identically iff J*A is alternating in odd characteristic.
    # Evaluate the bilinear matrix through basis vectors to avoid scanning all 80 nonzero vectors.
    B = [[form(E[i], act(A, E[j])) for j in range(D)] for i in range(D)]
    return all(B[i][i] == 0 for i in range(D)) and all((B[i][j] + B[j][i]) % Q == 0 for i in range(D) for j in range(D))


def compile_sp_peeling(g: Matrix) -> list[tuple[int, int]]:
    """Return an execution word whose product is exactly g."""
    peeled: list[tuple[int, int]] = []
    cur = g
    while cur != I:
        if is_hyperbolic(cur):
            chosen = None
            for axis, lam, M in GENS:
                C = mul(cur, M)
                if residue(C) == residue(cur) and not is_hyperbolic(C):
                    chosen = (axis, lam, C)
                    break
            if chosen is None:
                raise RuntimeError("hyperbolic fix-up missing")
            peeled.append((chosen[0], chosen[1]))
            cur = chosen[2]
            continue

        gi = inverse(cur)
        fallback = None
        chosen = None
        for x in VECS:
            gx = act(gi, x)
            c = form(x, gx) % Q
            if c == 0:
                continue
            v = tuple((gx[k]-x[k]) % Q for k in range(D))  # type: ignore[assignment]
            if not any(v):
                continue
            lam = pow(c, -1, Q)
            M = transvection(v, lam)
            C = mul(cur, M)
            if residue(C) != residue(cur)-1:
                continue
            meta = GEN_BY_MATRIX[M]
            item = (meta[0], meta[1], C)
            if C == I or not is_hyperbolic(C):
                chosen = item
                break
            if fallback is None:
                fallback = item
        step = chosen or fallback
        if step is None:
            raise RuntimeError("residue-dropping pivot missing")
        peeled.append((step[0], step[1]))
        cur = step[2]

    # peeled satisfies g*T1*...*Tk=I.  Execution from I to g therefore uses
    # Tk^-1...T1^-1, with inverse lambda = -lambda mod 3.
    return [(axis, (-lam) % Q) for axis, lam in reversed(peeled)]


def word_product(word: Iterable[tuple[int, int]]) -> Matrix:
    P = I
    for axis, lam in word:
        P = mul(P, transvection(AXES[int(axis)], int(lam)))
    return P


def load_slow_certificate() -> dict[str, Any]:
    return json.loads((ROOT / "data/the_45_slot_rom_bijection.json").read_text(encoding="utf-8"))


def matrix_from_json(rows: list[list[int]]) -> Matrix:
    return tuple(tuple(int(x) % Q for x in row) for row in rows)


def slow_index(cert: dict[str, Any]) -> dict[Matrix, dict[str, Any]]:
    banks = {slot: [] for slot in range(45)}
    for b, line in enumerate(cert["linesB"]):
        for slot in line:
            banks[int(slot)].append(b)
    out = {}
    for anomaly, row in enumerate(cert["table"]):
        key = canonical_projective(matrix_from_json(row["spMatrix"]))
        out[key] = {
            "anomaly_index": anomaly,
            "slot": int(row["slot"]),
            "banks": tuple(banks[int(row["slot"])]),
            "h34_point": tuple(row["h34Point"]),
        }
    if len(out) != 45:
        raise AssertionError("slow certificate does not contain 45 projective targets")
    return out


def compile_projective(target: Matrix, cert_index: dict[Matrix, dict[str, Any]] | None = None) -> dict[str, Any]:
    g = canonical_projective(target)
    candidates = []
    for lift_bit, lift in ((0, g), (1, neg(g))):
        word = tuple(compile_sp_peeling(lift))
        candidates.append((len(word), word, lift_bit, lift))
    _, word, lift_bit, lift = min(candidates, key=lambda x: (x[0], x[1], x[2]))
    if canonical_projective(word_product(word)) != g:
        raise AssertionError("compiled word does not reconstruct projective target")
    index = cert_index if cert_index is not None else slow_index(load_slow_certificate())
    slow = index.get(g)
    return {
        "target": g,
        "word": word,
        "length": len(word),
        "projective_residue": projective_residue(g),
        "central_lift_bit": lift_bit,
        "chosen_sp_lift": lift,
        "slow": slow is not None,
        "slow_rom": slow,
    }


def projective_bfs() -> dict[Matrix, int]:
    identity = canonical_projective(I)
    dist = {identity: 0}
    q = deque([identity])
    while q:
        A = q.popleft()
        d = dist[A]
        for _, _, M in GENS:
            C = canonical_projective(mul(A, M))
            if C not in dist:
                dist[C] = d + 1
                q.append(C)
    return dist


def verify() -> dict[str, Any]:
    cert = load_slow_certificate()
    index = slow_index(cert)
    dist = projective_bfs()
    if len(dist) != 25920:
        raise AssertionError(f"expected PSp(4,3) order 25920, got {len(dist)}")

    exact = reconstructed = residue_rule = 0
    slow_seen = set()
    histogram: dict[int, int] = {}
    for g, truth in dist.items():
        row = compile_projective(g, index)
        histogram[row["length"]] = histogram.get(row["length"], 0) + 1
        exact += row["length"] == truth
        reconstructed += canonical_projective(word_product(row["word"])) == g
        expected_slow = truth > projective_residue(g)
        residue_rule += bool(row["slow"]) == expected_slow
        if row["slow"]:
            slow_seen.add(g)
            if row["length"] != row["projective_residue"] + 1:
                raise AssertionError("slow target is not exactly one extra transvection")
            if len(row["slow_rom"]["banks"]) != 3:
                raise AssertionError("slow target lost its three GQ banks")

    checks = {
        "psp_order_25920": len(dist) == 25920,
        "projective_diameter_4": max(dist.values()) == 4,
        "all_compiler_lengths_equal_bfs": exact == len(dist),
        "all_words_reconstruct_projective_target": reconstructed == len(dist),
        "slow_decoder_equals_exact_residue_anomaly_set": residue_rule == len(dist),
        "exactly_45_slow_targets": len(slow_seen) == len(index) == 45,
        "all_45_certificate_targets_seen": slow_seen == set(index),
        "expected_length_histogram": histogram == {0: 1, 1: 80, 2: 1980, 3: 13005, 4: 10854},
    }
    return {
        "schema": "holotrade.projective-slowpath-microsequencer.v1",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "verification": {
            "projective_targets": len(dist),
            "slow_targets": len(slow_seen),
            "length_histogram": histogram,
            "max_word": max(histogram),
        },
        "runtime_rule": (
            "Compile both central Sp lifts algorithmically, choose the shorter projective word, then attach GQ(4,2) slot/bank metadata iff the fixed 45-target certificate recognizes the projective target. The ROM classifies the exceptional path; it never replaces the compiler."
        ),
        "boundary": (
            "Exhaustive optimality is proved here for PSp(4,3) only. The emitted word is symplectic control; physical qutrit phase/optical lowering is a separate W33-Theory boundary."
        ),
    }


if __name__ == "__main__":
    out = verify()
    print(json.dumps(out, indent=2, sort_keys=True))
    raise SystemExit(0 if out["status"] == "PASS" else 1)
