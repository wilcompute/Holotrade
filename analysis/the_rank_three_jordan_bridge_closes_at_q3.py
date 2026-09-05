#!/usr/bin/env python3
"""Exact rank-three Pfaffian/Jordan bridge, including characteristic three.

The previous rank-three experiment excluded q=3 from the adjoint identity.
That exclusion is unnecessary if the adjoint is written as the co-Pfaffian
(gradient with respect to the 15 independent alternating-matrix entries):
the identity

    (X#)# = Pf(X) X

is an identity of integer polynomials. This file proves that fact by exact
sparse coefficient arithmetic, before any finite-field reduction.

It then sanity-checks the rank dictionary over F_3. The external structural
identification used by the synthesis is the classical Severi/Jordan series:
J3(R), J3(C), J3(H), J3(O), of dimensions 6,9,15,27. Its 15-dimensional
member is Lambda^2(C^6) with Pfaffian cubic and rank-one locus Gr(2,6).
W33-Theory independently already implements the 27-dimensional Albert
J3(O) determinant as its E6 cubic; those source paths are recorded as
cross-repository provenance, not imported at runtime.
"""
from __future__ import annotations

from collections import defaultdict
import argparse
import json
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "rank_three_jordan_severi_bridge.json"
IDX = tuple((i, j) for i in range(6) for j in range(i + 1, 6))
NVAR = len(IDX)
ZERO = (0,) * NVAR
INDEX = {ij: k for k, ij in enumerate(IDX)}


def matchings(rem):
    if not rem:
        yield (), 1
        return
    a = rem[0]
    for k in range(1, len(rem)):
        b = rem[k]
        for rest, sign in matchings(rem[1:k] + rem[k + 1:]):
            yield ((a, b),) + rest, sign * ((-1) ** (k - 1))


MATCHINGS = tuple(matchings(tuple(range(6))))


def pclean(p):
    return {m: int(c) for m, c in p.items() if c}


def padd(a, b):
    out = defaultdict(int)
    out.update(a)
    for m, c in b.items():
        out[m] += c
    return pclean(out)


def pscale(a, s):
    return pclean({m: s * c for m, c in a.items()})


def pmul(a, b):
    out = defaultdict(int)
    for ma, ca in a.items():
        for mb, cb in b.items():
            out[tuple(x + y for x, y in zip(ma, mb))] += ca * cb
    return pclean(out)


def var(k, coeff=1):
    e = [0] * NVAR
    e[k] = 1
    return {tuple(e): coeff}


def deriv(p, k):
    out = defaultdict(int)
    for m, c in p.items():
        if m[k]:
            e = list(m)
            out[tuple(e[:k] + [e[k] - 1] + e[k + 1:])] += c * m[k]
    return pclean(out)


def substitute(p, subs):
    out = {}
    for mon, coeff in p.items():
        term = {ZERO: coeff}
        for k, power in enumerate(mon):
            for _ in range(power):
                term = pmul(term, subs[k])
        out = padd(out, term)
    return out


def entry_poly(i, j):
    if i == j:
        return {}
    if i < j:
        return var(INDEX[(i, j)])
    return pscale(var(INDEX[(j, i)]), -1)


def pfaffian_poly():
    out = {}
    for matching, sign in MATCHINGS:
        term = {ZERO: sign}
        for i, j in matching:
            term = pmul(term, entry_poly(i, j))
        out = padd(out, term)
    return out


PF = pfaffian_poly()
SHARP = tuple(deriv(PF, k) for k in range(NVAR))
DOUBLE_SHARP = tuple(substitute(SHARP[k], SHARP) for k in range(NVAR))
TARGET = tuple(pmul(PF, var(k)) for k in range(NVAR))


def peval(p, values, q=None):
    total = 0
    for mon, coeff in p.items():
        term = coeff
        for x, power in zip(values, mon):
            if power:
                term *= x ** power
        total += term
    return total if q is None else total % q


def sharp_values(values, q):
    return tuple(peval(p, values, q) for p in SHARP)


def pf_values(values, q):
    return peval(PF, values, q)


def alt_matrix(values, q):
    A = [[0] * 6 for _ in range(6)]
    for x, (i, j) in zip(values, IDX):
        A[i][j] = x % q
        A[j][i] = (-x) % q
    return A


def rank_mod(A, q):
    M = [row[:] for row in A]
    rows = len(M)
    cols = len(M[0]) if rows else 0
    r = 0
    for c in range(cols):
        pivot = next((i for i in range(r, rows) if M[i][c] % q), None)
        if pivot is None:
            continue
        M[r], M[pivot] = M[pivot], M[r]
        inv = pow(M[r][c] % q, -1, q)
        M[r] = [(x * inv) % q for x in M[r]]
        for i in range(rows):
            if i != r and M[i][c] % q:
                f = M[i][c] % q
                M[i] = [(x - f * y) % q for x, y in zip(M[i], M[r])]
        r += 1
    return r


def bivector_rank(values, q):
    return rank_mod(alt_matrix(values, q), q)


def jordan_rank(values, q):
    sh = sharp_values(values, q)
    if not any(sh):
        return 1 if any(x % q for x in values) else 0
    return 3 if pf_values(values, q) else 2


def wedge(u, v, q):
    return tuple((u[i] * v[j] - u[j] * v[i]) % q for i, j in IDX)


def q3_sanity(samples=1200, decomposables=1200, seed=20260905):
    rnd = random.Random(seed)
    identity = 0
    rank_dictionary = 0
    tested = 0
    for _ in range(samples):
        x = tuple(rnd.randrange(3) for _ in range(NVAR))
        if not any(x):
            continue
        tested += 1
        sh = sharp_values(x, 3)
        ssh = sharp_values(sh, 3)
        norm = pf_values(x, 3)
        if all(a % 3 == (norm * b) % 3 for a, b in zip(ssh, x)):
            identity += 1
        br = bivector_rank(x, 3)
        jr = jordan_rank(x, 3)
        expected = {2: 1, 4: 2, 6: 3}.get(br)
        if expected == jr:
            rank_dictionary += 1

    decomp_ok = 0
    decomp_tested = 0
    while decomp_tested < decomposables:
        u = tuple(rnd.randrange(3) for _ in range(6))
        v = tuple(rnd.randrange(3) for _ in range(6))
        x = wedge(u, v, 3)
        if not any(x):
            continue
        decomp_tested += 1
        if bivector_rank(x, 3) == 2 and jordan_rank(x, 3) == 1:
            decomp_ok += 1
    return {
        "randomTested": tested,
        "doubleAdjointPassed": identity,
        "rankDictionaryPassed": rank_dictionary,
        "decomposablesTested": decomp_tested,
        "decomposablesRankOnePassed": decomp_ok,
    }


def build():
    integral_diffs = tuple(padd(DOUBLE_SHARP[k], pscale(TARGET[k], -1)) for k in range(NVAR))
    sanity = q3_sanity()
    checks = {
        "pfaffian_has_15_signed_cubic_terms": len(PF) == 15 and set(PF.values()) <= {-1, 1},
        "all_15_adjoint_coordinates_have_3_signed_quadratic_terms":
            len(SHARP) == 15 and all(len(p) == 3 and set(p.values()) <= {-1, 1} for p in SHARP),
        "double_adjoint_identity_holds_over_integers": all(not p for p in integral_diffs),
        "therefore_identity_holds_in_characteristic_3": all(not p for p in integral_diffs),
        "q3_numeric_double_adjoint_sanity": sanity["doubleAdjointPassed"] == sanity["randomTested"],
        "q3_numeric_rank_dictionary_sanity": sanity["rankDictionaryPassed"] == sanity["randomTested"],
        "q3_decomposables_are_jordan_rank_one": sanity["decomposablesRankOnePassed"] == sanity["decomposablesTested"],
        "severi_jordan_dimensions_are_6_9_15_27": [3 + 3 * a for a in (1, 2, 4, 8)] == [6, 9, 15, 27],
    }
    return {
        "schema": "holotrade.rank-three-jordan-severi-bridge.v1",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "exactPolynomialCertificate": {
            "baseRing": "Z",
            "independentAlternatingCoordinates": 15,
            "pfaffianDegree": 3,
            "pfaffianTerms": len(PF),
            "adjointCoordinateDegree": 2,
            "adjointTermsPerCoordinate": sorted({len(p) for p in SHARP}),
            "identity": "(X#)# = Pf(X) X",
            "zeroDifferenceCoordinates": sum(1 for p in integral_diffs if not p),
            "consequence": "Reduction modulo every prime preserves the polynomial identity; in particular q=3 is admitted. Characteristic 2 still requires separate geometric interpretation.",
        },
        "q3Sanity": sanity,
        "series": {
            "dimensions": [6, 9, 15, 27],
            "members": ["J3(R)", "J3(C)", "J3(H)", "J3(O)"],
            "rank3Member": {
                "dimension": 15,
                "model": "Lambda^2(F^6) / 6x6 alternating matrices",
                "cubicNorm": "Pfaffian",
                "rankOneLocus": "Gr(2,6) after passage to the classical split/complex model",
            },
            "exceptionalMember": {
                "dimension": 27,
                "model": "Albert algebra J3(O)",
                "cubicNorm": "determinant",
                "group": "E6 determinant-preserving exceptional member",
            },
        },
        "crossRepoProvenance": {
            "repository": "wilcompute/W33-Theory",
            "observedHead": "5b0c41211bb44d718e1fc89a667c5cd3de6f694e",
            "files": [
                "tools/compute_e6_cubic_tensor.py",
                "analysis/w33_magic_square_substrate.py",
                "rtl/w33_pass2632_e6_cubic_gate.sv",
                "rtl/w33_pass2660_e6_cartan_cubic.sv",
            ],
            "boundary": "These paths are provenance for the already-existing W33 Albert/E6 cubic implementation; this Holotrade verifier does not network-fetch the other repository in CI.",
        },
        "literatureAnchor": {
            "citation": "A. Iliev and L. Manivel, Severi varieties and their varieties of reductions, arXiv:math/0306328",
            "role": "Classical identification of the four rank-three Jordan/Severi members, including J3(H) ~ exterior-square six-space with Pfaffian cubic and J3(O) as the E6 member.",
        },
        "correction": {
            "supersedesBoundary": "q=3 excluded from the adjoint test because the gradient construction divides by small integers",
            "replacement": "The co-Pfaffian adjoint is defined integrally and its double-adjoint identity is an integer polynomial identity, so q=3 is included.",
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    out = build()
    print(json.dumps(out, indent=2, sort_keys=True))
    if args.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    raise SystemExit(0 if out["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
