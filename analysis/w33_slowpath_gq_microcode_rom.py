#!/usr/bin/env python3
"""Geometry-checked slow-path ROM for the W33 projective qutrit ISA.

Current exhaustive HoloTrade control results show that exactly 45 of the 25,920
PSp(4,3) projective targets cost one transvection more than projective residue,
and that those 45 targets form GQ(4,2)=H(3,4) under anticommutation of Sp lifts.
They have 27 maximal lines, each of size five; every target lies on three lines.

That means a production compiler should not treat the slow path as an opaque
45-entry exception table.  Its microcode catalogue has a native incidence
checksum.  This file constructs the abstract H(3,4) quadrangle independently
from GF(4), verifies all structural invariants, and emits a ROM contract:

    45 unique slow target slots
    27 five-entry line banks
    135 target-bank incidences
    each target repeated in exactly 3 banks
    collinearity graph SRG(45,12,3,3)

The triple incidence is useful engineering redundancy: a target-ID catalogue
mapped onto this abstract geometry can be checked at load/boot time for line
size, per-target multiplicity, pair uniqueness and the GQ axiom before any
exception microcode is admitted.

Boundary: this constructs an abstract canonical GQ(4,2) ROM shape and validates
the invariants reported by the matrix-level anomaly computation.  It does NOT
construct the missing explicit isomorphism from this lexicographically labelled
H(3,4) model to the 45 concrete PSp anomaly classes.  That target-ID mapping is
the next compiler integration step and must be certified rather than guessed.
"""

from __future__ import annotations

from collections import Counter
from itertools import combinations, product
import json

# GF(4) = F2[a]/(a^2+a+1), encoded as bit pair c0 + c1*a.
Q4 = range(4)


def add(a: int, b: int) -> int:
    return a ^ b


def mul(a: int, b: int) -> int:
    a0, a1 = a & 1, (a >> 1) & 1
    b0, b1 = b & 1, (b >> 1) & 1
    # a^2 = a + 1
    c0 = (a0 * b0) ^ (a1 * b1)
    c1 = (a0 * b1) ^ (a1 * b0) ^ (a1 * b1)
    return c0 | (c1 << 1)


def fpow(a: int, n: int) -> int:
    r = 1
    while n:
        if n & 1:
            r = mul(r, a)
        a = mul(a, a)
        n >>= 1
    return r


def inv(a: int) -> int:
    if a == 0:
        raise ZeroDivisionError
    return fpow(a, 2)  # every nonzero GF(4) element satisfies a^3=1


def conj(a: int) -> int:
    return mul(a, a)  # Frobenius x -> x^2


def scale(s: int, v: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(mul(s, x) for x in v)


def vadd(u: tuple[int, ...], v: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(add(x, y) for x, y in zip(u, v))


def canon(v: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    i = next(i for i, x in enumerate(v) if x)
    return scale(inv(v[i]), v)  # type: ignore[return-value]


def hermitian(u: tuple[int, ...], v: tuple[int, ...]) -> int:
    out = 0
    for x, y in zip(u, v):
        out = add(out, mul(conj(x), y))
    return out


def build_h34() -> tuple[list[tuple[int, ...]], list[tuple[int, ...]]]:
    vectors = [v for v in product(Q4, repeat=4) if any(v)]
    points = sorted({canon(v) for v in vectors if hermitian(v, v) == 0})
    if len(points) != 45:
        raise AssertionError(f"H(3,4) should have 45 points, got {len(points)}")
    index = {p: i for i, p in enumerate(points)}

    line_set: set[tuple[int, ...]] = set()
    for i, j in combinations(range(len(points)), 2):
        if hermitian(points[i], points[j]) != 0:
            continue
        span = set()
        for a, b in product(Q4, repeat=2):
            if a == b == 0:
                continue
            w = vadd(scale(a, points[i]), scale(b, points[j]))
            span.add(index[canon(w)])
        if len(span) == 5 and all(hermitian(points[k], points[k]) == 0 for k in span):
            line_set.add(tuple(sorted(span)))
    lines = sorted(line_set)
    if len(lines) != 27 or {len(L) for L in lines} != {5}:
        raise AssertionError("H(3,4) line census failed")
    return points, lines


def verify() -> dict[str, object]:
    points, lines = build_h34()
    n = len(points)
    adjacency = [[0] * n for _ in range(n)]
    lines_per_point = Counter()
    pair_line_count = Counter()

    for li, line in enumerate(lines):
        for p in line:
            lines_per_point[p] += 1
        for a, b in combinations(line, 2):
            pair = tuple(sorted((a, b)))
            pair_line_count[pair] += 1
            adjacency[a][b] = adjacency[b][a] = 1

    degrees = Counter(sum(row) for row in adjacency)
    edges = sum(sum(row) for row in adjacency) // 2
    lam = set()
    mu = set()
    for i, j in combinations(range(n), 2):
        common = sum(1 for k in range(n) if adjacency[i][k] and adjacency[j][k])
        (lam if adjacency[i][j] else mu).add(common)

    gq_offline_counts = []
    for p in range(n):
        for line in lines:
            if p in line:
                continue
            gq_offline_counts.append(sum(adjacency[p][q] for q in line))

    checks = {
        "points_45": n == 45,
        "lines_27": len(lines) == 27,
        "line_size_5": {len(L) for L in lines} == {5},
        "three_lines_per_point": set(lines_per_point.values()) == {3},
        "flags_135": sum(lines_per_point.values()) == 135,
        "collinearity_edges_270": edges == 270,
        "degree_12": degrees == Counter({12: 45}),
        "srg_lambda_3": lam == {3},
        "srg_mu_3": mu == {3},
        "pair_on_at_most_one_line": set(pair_line_count.values()) == {1},
        "gq_axiom": set(gq_offline_counts) == {1},
    }
    if not all(checks.values()):
        raise AssertionError(checks)

    banks = [
        {"bank": i, "slowTargetSlots": list(line)}
        for i, line in enumerate(lines)
    ]
    point_banks = {
        str(p): [i for i, line in enumerate(lines) if p in line]
        for p in range(n)
    }

    return {
        "schema": "holotrade.w33-slowpath-gq-microcode-rom.v1",
        "valid": True,
        "checks": checks,
        "rom": {
            "slowTargetSlots": 45,
            "lineBanks": 27,
            "entriesPerBank": 5,
            "incidenceReferences": 135,
            "banksPerTarget": 3,
            "collinearityGraph": [45, 12, 3, 3],
            "banks": banks,
            "targetToBanks": point_banks,
        },
        "runtimeRule": (
            "admit a concrete 45-target slow-path catalogue only after a certified "
            "bijection to these slots preserves all 27 five-target banks and the GQ axiom"
        ),
        "crossRepoSource": {
            "projectiveCost": "3a0a1945439e674171cfbd815043a69e916d0025",
            "matrixAnticommutationGQ": "605f5e585ce1a124d1cddce9745b47d6f7592708",
            "linePauliShape": "34f2a841925dec20c5fae9c3429686e8390b67ba",
            "slowTargets": 45,
            "extraTransvectionsPerSlowTarget": 1,
        },
        "boundary": (
            "The abstract ROM geometry is exact. The identity map from abstract H(3,4) "
            "slot labels to concrete PSp anomaly target IDs is NOT established here and "
            "must be separately generated/certified before runtime use."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2, sort_keys=True))
