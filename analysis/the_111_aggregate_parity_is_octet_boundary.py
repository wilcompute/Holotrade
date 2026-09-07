#!/usr/bin/env python3
"""The aggregate mod-2 route for tau_2=111 lands in the octet *boundary* code.

For the two-pencil factorization E = U N^T = N V, let

    a_p = total number of row-side point tokens equal to p,
    b_p = total number of column-side point tokens equal to p.

There are 44 tokens on either side.  Summing E down its rows/columns and using
that the four dirty lines form a pencil gives, exactly,

    N a = 4*1 + 4*P_{c_col},
    N b = 4*1 + 4*P_{c_row},

where N is the 40x40 W(3,3) line/point incidence matrix and P_c=N e_c is the
four-line pencil at c.  Therefore modulo two

    N (a mod 2) = N (b mod 2) = 0.

The tempting hope was that these parity classes might directly occupy the H10
logical quotient.  They do not.  This file reconstructs the full binary chain:

* rank_F2(N)=25, so ker_F2(N) has dimension 15;
* the 45 intrinsic octets span a [40,15,8] code M;
* N M = 0 mod 2 and rank(M)=15, hence ker_F2(N)=im_F2(M);
* M^T M=0, rank(M)=15, so ker(M^T)/im(M) has dimension 25-15=10 = H10.

Thus every aggregate token-parity vector forced by a 111 factorization lies in
im(M), the octet boundary subspace, and has ZERO H10 class.  Aggregate parity
alone cannot be the missing 111 obstruction; any characteristic-two obstruction
must live at a finer matching/relative-parity level.

The exact weight enumerator of ker_F2(N)=im(M) is also recomputed:
  1 + 45 z^8 + 720 z^12 + 6930 z^16 + 17376 z^20
    + 6930 z^24 + 720 z^28 + 45 z^32 + z^40.

This is a finite binary coding statement, not a physical CSS implementation.
"""
from __future__ import annotations

from collections import Counter
import importlib.util
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "the_111_aggregate_parity_is_octet_boundary.json"
Q = 3


def norm(v):
    i = next(k for k, x in enumerate(v) if x % Q)
    z = pow(v[i] % Q, -1, Q)
    return tuple((z * x) % Q for x in v)


def form(u, v):
    return (u[0] * v[2] - u[2] * v[0] + u[1] * v[3] - u[3] * v[1]) % Q


def geometry():
    pts = sorted({norm(v) for v in itertools.product(range(Q), repeat=4) if any(v)})
    pidx = {p: i for i, p in enumerate(pts)}
    line_sets = set()
    for a, b in itertools.combinations(range(40), 2):
        if form(pts[a], pts[b]):
            continue
        S = set()
        for x, y in itertools.product(range(Q), repeat=2):
            if not (x or y):
                continue
            w = tuple((x * pts[a][k] + y * pts[b][k]) % Q for k in range(4))
            S.add(pidx[norm(w)])
        if len(S) == 4:
            line_sets.add(frozenset(S))
    lines = sorted(line_sets, key=lambda s: tuple(sorted(s)))
    N = [[1 if p in L else 0 for p in range(40)] for L in lines]
    adj = [set() for _ in range(40)]
    for L in lines:
        for p in L:
            adj[p] |= set(L) - {p}
    assert len(lines) == 40
    return lines, N, adj


def rank2(rows, ncols):
    piv = {}
    for row in rows:
        x = row if isinstance(row, int) else sum((int(v) & 1) << j for j, v in enumerate(row))
        while x:
            p = x.bit_length() - 1
            if p in piv:
                x ^= piv[p]
            else:
                piv[p] = x
                break
    return len(piv)


def basis2(rows):
    piv = {}
    out = []
    for row in rows:
        x = row if isinstance(row, int) else sum((int(v) & 1) << j for j, v in enumerate(row))
        while x:
            p = x.bit_length() - 1
            if p in piv:
                x ^= piv[p]
            else:
                piv[p] = x
                out.append(x)
                break
    return out


def octet_module():
    path = ROOT / "analysis" / "the_minimum_blocker_labels_are_octets.py"
    spec = importlib.util.spec_from_file_location("octet_labels", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import octet blocker module")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build():
    lines, N, adj = geometry()
    n, _, _, B = octet_module().build(3)
    assert n == 40 and B.shape == (40, 45)
    octets = [frozenset(i for i in range(40) if B[i, j]) for j in range(45)]
    assert len(set(octets)) == 45 and all(len(C) == 8 for C in octets)

    Nrows = [sum((v & 1) << p for p, v in enumerate(row)) for row in N]
    rankN = rank2(Nrows, 40)
    assert rankN == 25

    Mcols = [sum(1 << p for p in C) for C in octets]
    rankM = rank2(Mcols, 40)
    assert rankM == 15

    # N M = 0: every W33 line meets every octet evenly.
    NMzero = all((row & col).bit_count() % 2 == 0 for row in Nrows for col in Mcols)
    assert NMzero
    assert 40 - rankN == rankM == 15

    # M^T M = 0: octet code is self-orthogonal.
    MTMzero = all((a & b).bit_count() % 2 == 0 for a in Mcols for b in Mcols)
    assert MTMzero
    kerMT = 40 - rankM
    h10 = kerMT - rankM
    assert (kerMT, h10) == (25, 10)

    basis = basis2(Mcols)
    assert len(basis) == 15
    weights = Counter()
    span = set()
    for mask in range(1 << 15):
        x = 0
        for i, v in enumerate(basis):
            if mask & (1 << i):
                x ^= v
        span.add(x)
        weights[x.bit_count()] += 1
    expected_weights = Counter({0: 1, 8: 45, 12: 720, 16: 6930, 20: 17376,
                                24: 6930, 28: 720, 32: 45, 40: 1})
    assert len(span) == 2 ** 15 and weights == expected_weights
    weight8 = {frozenset(i for i in range(40) if (x >> i) & 1)
               for x in span if x.bit_count() == 8}
    assert weight8 == set(octets)

    # Exact aggregate equation at one centre, with two independent integer lifts.
    c = 0
    target = [4 + 4 * N[i][c] for i in range(40)]
    dense = [1] * 40
    dense[c] += 4
    assert [sum(N[i][p] * dense[p] for p in range(40)) for i in range(40)] == target

    through = [C for C in octets if c in C]
    C = through[0]
    minimum = frozenset((adj[c] ^ set(C)) - {c})
    assert len(minimum) == 11
    sparse = [4 if p in minimum else 0 for p in range(40)]
    assert [sum(N[i][p] * sparse[p] for p in range(40)) for i in range(40)] == target
    assert sum(dense) == sum(sparse) == 44
    dense_parity = sum((dense[p] & 1) << p for p in range(40))
    sparse_parity = sum((sparse[p] & 1) << p for p in range(40))
    assert dense_parity in span and sparse_parity in span
    assert dense_parity.bit_count() == 40 and sparse_parity == 0

    checks = {
        "rank_F2_N_is_25": rankN == 25,
        "kernel_N_dimension_is_15": 40 - rankN == 15,
        "octet_span_rank_is_15": rankM == 15,
        "N_times_octet_incidence_is_zero_mod2": NMzero,
        "kernel_N_equals_octet_span_by_inclusion_and_dimension": NMzero and 40 - rankN == rankM,
        "octet_span_is_self_orthogonal": MTMzero,
        "ker_MT_dimension_is_25": kerMT == 25,
        "H10_quotient_dimension_is_10": h10 == 10,
        "kernel_weight_enumerator_exact": weights == expected_weights,
        "minimum_words_are_exactly_the_45_octets": weight8 == set(octets),
        "dense_and_sparse_integer_aggregate_lifts_exist": sum(dense) == sum(sparse) == 44,
    }
    assert all(checks.values())

    return {
        "schema": "holotrade.tau2-111-aggregate-parity-octet-boundary.v1",
        "status": "PASS",
        "checks": checks,
        "aggregateEquation": "N a = 4*1 + 4*P_c on either axis (with the opposite dirty-pencil centre c)",
        "binaryConsequence": "a mod 2 lies in ker_F2(N) = im_F2(M), where M is point/octet incidence",
        "dimensions": {"rankN": rankN, "kerN": 40-rankN, "rankOctetSpan": rankM,
                       "kerMT": kerMT, "H10": h10},
        "octetCodeWeightEnumerator": {str(k): v for k, v in sorted(weights.items())},
        "H10Reading": (
            "Because aggregate parity lies in im(M), its class in H10 = ker(M^T)/im(M) is zero. The aggregate mod-2 route therefore cannot by itself exclude a 111 factorization. Any characteristic-two obstruction must use relative row/column matching data or another quotient, not only total point-token multiplicities."
        ),
        "integerLiftWitnesses": {"denseParityWeight": 40, "sparseParityWeight": 0,
                                  "tokenMassEach": 44},
        "boundary": "Exact finite binary/integer incidence statement. H10 is a coding/homology quotient here; no physical error-correction implementation is inferred.",
    }


def main():
    out = build()
    print(json.dumps(out, indent=2, sort_keys=True))
    if "--write" in __import__("sys").argv:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
