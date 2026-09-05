#!/usr/bin/env python3
"""Exact projective Sp(6,3) orbit census on the 14D rank-three quotient.

The earlier rank-three pass sampled ker(omega) and proved only that there are
at least eight orbits.  In characteristic three that model has a one-dimensional
radical because omega itself becomes primitive.  The line Symplectic
Grassmann code, however, is controlled by the 14-dimensional quotient

    Q = Lambda^2(F_3^6) / <omega>.

This verifier works on Q directly.  It uses the six positive/negative simple
root generators of type C3, enumerates every one of the

    (3^14 - 1) / 2 = 2,391,484

projective points, closes their exact generator orbits, and computes the line
Symplectic Grassmann code weight of one representative of each orbit.

The focused CI lane independently asks GAP for the order of the six 6x6
matrix generators; it must return |Sp(6,3)| = 9,170,703,360.  The center
{-I,I} acts trivially on projective Lambda^2, so the effective group has order
|PSp(6,3)| = 4,585,351,680.

No random sampling, floating point, graph recognition, or fitted formula is
used in the census.
"""
from __future__ import annotations

import argparse
import itertools
import json
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "rank_three_exact_sp6_orbit_census.json"
Q = 3
N = 3
D = 6
PAIR = tuple((i, j) for i in range(D) for j in range(i + 1, D))
PAIR_INDEX = {p: i for i, p in enumerate(PAIR)}
DEP = (2, 5)
DEP_INDEX = PAIR_INDEX[DEP]
FREE = tuple(p for p in PAIR if p != DEP)
FREE_INDEX = tuple(PAIR_INDEX[p] for p in FREE)
POW3 = (3 ** np.arange(14, dtype=np.int64))
PROJECTIVE_POINTS = (3 ** 14 - 1) // 2
SP6_ORDER = 9_170_703_360
PSP6_ORDER = SP6_ORDER // 2


def symplectic_form() -> np.ndarray:
    J = np.zeros((D, D), dtype=np.int8)
    for i in range(N):
        J[i, N + i] = 1
        J[N + i, i] = Q - 1
    return J


J = symplectic_form()
OMEGA = np.array([J[i, j] for i, j in PAIR], dtype=np.int8) % Q
assert int(OMEGA[DEP_INDEX]) == 1


def simple_root_generators() -> list[np.ndarray]:
    """x_{+-alpha_i}(1) for the three simple roots of C3."""
    out: list[np.ndarray] = []
    for i, j in ((0, 1), (1, 2)):
        g = np.eye(D, dtype=np.int8)
        g[i, j] = 1
        g[N + j, N + i] = Q - 1
        out.append(g)
        g = np.eye(D, dtype=np.int8)
        g[j, i] = 1
        g[N + i, N + j] = Q - 1
        out.append(g)
    g = np.eye(D, dtype=np.int8)
    g[2, N + 2] = 1
    out.append(g)
    g = np.eye(D, dtype=np.int8)
    g[N + 2, 2] = 1
    out.append(g)
    assert len(out) == 6
    for g in out:
        assert np.array_equal((g.T.astype(int) @ J.astype(int) @ g.astype(int)) % Q, J)
    return out


GEN6 = simple_root_generators()


def wedge(g: np.ndarray) -> np.ndarray:
    A = np.zeros((15, 15), dtype=np.int8)
    for c, (i, j) in enumerate(PAIR):
        gi, gj = g[:, i], g[:, j]
        for a, b in PAIR:
            A[PAIR_INDEX[(a, b)], c] = (int(gi[a]) * int(gj[b]) - int(gi[b]) * int(gj[a])) % Q
    return A


# Quotient representatives set the DEP=(2,5) coefficient to zero.  Projection
# subtracts b_DEP * omega before dropping that coordinate.
QB = np.zeros((14, 15), dtype=np.int8)
for r, k in enumerate(FREE_INDEX):
    QB[r, k] = 1


def quotient_coords(full: np.ndarray) -> np.ndarray:
    c = int(full[DEP_INDEX]) % Q
    rep = (full.astype(int) - c * OMEGA.astype(int)) % Q
    assert int(rep[DEP_INDEX]) == 0
    return rep[list(FREE_INDEX)].astype(np.int8)


def quotient_actions() -> list[np.ndarray]:
    actions = []
    for g in GEN6:
        img = (QB.astype(int) @ wedge(g).T.astype(int)) % Q
        C = np.stack([quotient_coords(row) for row in img], axis=0).astype(np.int8)
        actions.append(C)
    return actions


ACTIONS = quotient_actions()


def decode(codes: np.ndarray) -> np.ndarray:
    z = codes.astype(np.int64).copy()
    X = np.empty((len(codes), 14), dtype=np.int8)
    for i in range(14):
        X[:, i] = (z % Q).astype(np.int8)
        z //= Q
    return X


def apply_action(X: np.ndarray, C: np.ndarray) -> np.ndarray:
    """Sparse exact row action X -> X C over F3."""
    Y = np.zeros_like(X)
    for j in range(14):
        inds = np.flatnonzero(C[:, j])
        if len(inds) == 1:
            i = int(inds[0])
            Y[:, j] = (X[:, i].astype(np.int16) * int(C[i, j]) % Q).astype(np.int8)
        else:
            s = np.zeros(len(X), dtype=np.int16)
            for ii in inds:
                i = int(ii)
                s += X[:, i].astype(np.int16) * int(C[i, j])
            Y[:, j] = (s % Q).astype(np.int8)
    return Y


def normalize_encode(Y: np.ndarray) -> np.ndarray:
    # Projective canonical representative: first nonzero trit is 1.
    nz = Y != 0
    assert np.all(nz.any(axis=1))
    first = nz.argmax(axis=1)
    vals = Y[np.arange(len(Y)), first]
    flip = vals == 2
    if np.any(flip):
        Y = Y.copy()
        Y[flip] = (2 * Y[flip]) % Q
    return (Y.astype(np.int64) @ POW3).astype(np.int32)


def canonical_projective_codes() -> np.ndarray:
    parts = []
    for i in range(14):
        tails = np.arange(3 ** (13 - i), dtype=np.int64)
        parts.append((3 ** i + tails * (3 ** (i + 1))).astype(np.int32))
    out = np.concatenate(parts)
    assert len(out) == PROJECTIVE_POINTS
    assert len(np.unique(out)) == PROJECTIVE_POINTS
    return out


def orbit_from_seed(seed: int, visited: np.ndarray, chunk: int = 200_000) -> int:
    frontier = np.array([seed], dtype=np.int32)
    visited[seed] = True
    size = 0
    while len(frontier):
        size += len(frontier)
        nxt = []
        for start in range(0, len(frontier), chunk):
            fc = frontier[start:start + chunk]
            X = decode(fc)
            z = np.unique(np.concatenate([
                normalize_encode(apply_action(X, C)) for C in ACTIONS
            ]))
            z = z[~visited[z]]
            if len(z):
                visited[z] = True
                nxt.append(z)
        frontier = np.unique(np.concatenate(nxt)) if nxt else np.empty(0, dtype=np.int32)
    return int(size)


def exact_orbits() -> list[tuple[int, int]]:
    canonical = canonical_projective_codes()
    visited = np.zeros(3 ** 14, dtype=bool)
    out = []
    for seed0 in canonical:
        seed = int(seed0)
        if not visited[seed]:
            out.append((seed, orbit_from_seed(seed, visited)))
    assert int(visited.sum()) == PROJECTIVE_POINTS
    assert sum(s for _, s in out) == PROJECTIVE_POINTS
    return out


def norm(v: tuple[int, ...]) -> tuple[int, ...]:
    i = next(k for k, x in enumerate(v) if x % Q)
    z = pow(v[i] % Q, -1, Q)
    return tuple((z * x) % Q for x in v)


def symplectic(u: tuple[int, ...], v: tuple[int, ...]) -> int:
    return int(np.array(u, dtype=int) @ J.astype(int) @ np.array(v, dtype=int)) % Q


def isotropic_line_plueckers() -> np.ndarray:
    points = sorted({norm(v) for v in itertools.product(range(Q), repeat=D) if any(v)})
    assert len(points) == 364
    lines = set()
    for ai, a in enumerate(points):
        for b in points[ai + 1:]:
            if symplectic(a, b):
                continue
            w = tuple((a[i] * b[j] - a[j] * b[i]) % Q for i, j in PAIR)
            if any(w):
                lines.add(norm(w))
    assert len(lines) == 3640
    return np.array(sorted(lines), dtype=np.int8).T


def quotient_code_to_full(code: int) -> np.ndarray:
    x = decode(np.array([code], dtype=np.int32))[0]
    return (x.astype(int) @ QB.astype(int) % Q).astype(np.int8)


def mod_rank(A: np.ndarray) -> int:
    M = np.asarray(A, dtype=np.int16).copy() % Q
    m, n = M.shape
    r = 0
    for c in range(n):
        p = next((i for i in range(r, m) if int(M[i, c]) % Q), None)
        if p is None:
            continue
        M[[r, p]] = M[[p, r]]
        M[r] = (M[r] * pow(int(M[r, c]), -1, Q)) % Q
        for i in range(m):
            if i != r and int(M[i, c]) % Q:
                M[i] = (M[i] - int(M[i, c]) * M[r]) % Q
        r += 1
    return r


def bivector_rank(full: np.ndarray) -> int:
    A = np.zeros((D, D), dtype=np.int16)
    for k, (i, j) in enumerate(PAIR):
        A[i, j] = int(full[k]) % Q
        A[j, i] = (-int(full[k])) % Q
    return mod_rank(A)


def pfaffian6(full: np.ndarray) -> int:
    A = np.zeros((D, D), dtype=np.int16)
    for k, (i, j) in enumerate(PAIR):
        A[i, j] = int(full[k]) % Q
        A[j, i] = (-int(full[k])) % Q
    def pf(indices: tuple[int, ...]) -> int:
        if not indices:
            return 1
        a = indices[0]
        total = 0
        for k in range(1, len(indices)):
            b = indices[k]
            rest = indices[1:k] + indices[k + 1:]
            total += ((-1) ** (k - 1)) * int(A[a, b]) * pf(rest)
        return total
    return pf(tuple(range(D))) % Q


def coset_signature(full: np.ndarray) -> dict:
    ranks, pfs = [], []
    for c in range(Q):
        z = (full.astype(int) + c * OMEGA.astype(int)) % Q
        ranks.append(bivector_rank(z))
        pfs.append(pfaffian6(z))
    return {"rankMultiset": sorted(ranks), "pfaffianMultiset": sorted(pfs)}


def build() -> dict:
    # Six exact simple-root generators are symplectic and induce quotient actions.
    generator_checks = []
    for g, C in zip(GEN6, ACTIONS):
        symp = np.array_equal((g.T.astype(int) @ J.astype(int) @ g.astype(int)) % Q, J)
        generator_checks.append({
            "symplectic6x6": bool(symp),
            "quotientActionRank": mod_rank(C),
            "quotientActionInvertible": mod_rank(C) == 14,
        })
    assert all(x["symplectic6x6"] and x["quotientActionInvertible"] for x in generator_checks)

    orbits = exact_orbits()
    assert len(orbits) == 9

    L = isotropic_line_plueckers()
    # Every simple-root generator permutes the 3640 isotropic line coordinates.
    line_set = {tuple(map(int, L[:, j])) for j in range(L.shape[1])}
    line_action_checks = []
    for g in GEN6:
        W = wedge(g)
        image = set()
        for j in range(L.shape[1]):
            z = (W.astype(int) @ L[:, j].astype(int)) % Q
            image.add(norm(tuple(map(int, z))))
        line_action_checks.append(image == line_set)
    assert all(line_action_checks)

    orbit_rows = []
    weight_enum = Counter()
    LT = L.T.astype(np.int16)
    for oi, (seed, size) in enumerate(orbits):
        full = quotient_code_to_full(seed)
        weight = int(np.count_nonzero((LT.astype(int) @ full.astype(int)) % Q))
        # Directly recheck weight invariance on the six generator neighbours.
        X = decode(np.array([seed], dtype=np.int32))
        neighbour_weights = []
        for C in ACTIONS:
            s2 = int(normalize_encode(apply_action(X, C))[0])
            f2 = quotient_code_to_full(s2)
            neighbour_weights.append(int(np.count_nonzero((LT.astype(int) @ f2.astype(int)) % Q)))
        assert set(neighbour_weights) == {weight}
        sig = coset_signature(full)
        assert PSP6_ORDER % size == 0
        orbit_rows.append({
            "orbit": oi,
            "canonicalSeed": seed,
            "projectiveSize": size,
            "PSpStabilizerOrder": PSP6_ORDER // size,
            "codeWeight": weight,
            "representative15": [int(x) for x in full],
            "representativeCosetSignature": sig,
            "generatorNeighbourWeights": neighbour_weights,
        })
        weight_enum[weight] += 2 * size

    assert sum(weight_enum.values()) == 3 ** 14 - 1
    assert min(weight_enum) == 2160
    # The previously missed minimum shell is an entire projective orbit.
    minimum_orbits = [r for r in orbit_rows if r["codeWeight"] == 2160]
    assert len(minimum_orbits) == 1 and minimum_orbits[0]["projectiveSize"] == 7371

    expected_sizes = sorted([3640, 7371, 589680, 262080, 110565, 530712, 265356, 466560, 155520])
    assert sorted(r["projectiveSize"] for r in orbit_rows) == expected_sizes
    expected_enum = {
        2160: 14742,
        2187: 7280,
        2376: 221130,
        2403: 1179360,
        2430: 2116296,
        2457: 1244160,
    }
    assert dict(sorted(weight_enum.items())) == expected_enum

    checks = {
        "six_simple_root_generators_are_symplectic": all(x["symplectic6x6"] for x in generator_checks),
        "six_quotient_actions_are_invertible": all(x["quotientActionInvertible"] for x in generator_checks),
        "all_2391484_projective_points_partitioned": sum(r["projectiveSize"] for r in orbit_rows) == PROJECTIVE_POINTS,
        "exactly_nine_projective_orbits": len(orbit_rows) == 9,
        "all_orbit_sizes_divide_PSp6_order": all(PSP6_ORDER % r["projectiveSize"] == 0 for r in orbit_rows),
        "all_six_generators_permute_3640_isotropic_lines": all(line_action_checks),
        "generator_neighbours_preserve_code_weight": all(len(set(r["generatorNeighbourWeights"])) == 1 for r in orbit_rows),
        "full_nonzero_codeword_count_is_3pow14_minus_1": sum(weight_enum.values()) == 3 ** 14 - 1,
        "published_minimum_distance_2160_is_reached": min(weight_enum) == 2160,
        "minimum_shell_is_one_projective_orbit_of_7371": len(minimum_orbits) == 1 and minimum_orbits[0]["projectiveSize"] == 7371,
    }
    assert all(checks.values())

    return {
        "schema": "holotrade.rank-three-exact-sp6-orbit-census.v1",
        "status": "PASS",
        "module": {
            "field": "F3",
            "ambient": "Lambda^2(F3^6)",
            "quotient": "Lambda^2(F3^6)/<omega>",
            "dimension": 14,
            "nonzeroVectors": 3 ** 14 - 1,
            "projectivePoints": PROJECTIVE_POINTS,
            "whyQuotientNotKerOmega": "At q=3,n=3 the invariant form on ker(omega) has a one-dimensional radical generated by omega; the line-code functional module is the 14D quotient by <omega>.",
        },
        "group": {
            "generators": "six positive/negative simple-root unipotents of type C3",
            "expectedSp6Order": SP6_ORDER,
            "effectiveProjectiveOrder": PSP6_ORDER,
            "gapGate": "focused CI independently computes Size(Group(g1,...,g6)) and requires 9170703360",
            "generatorChecks": generator_checks,
        },
        "checks": checks,
        "orbits": orbit_rows,
        "weightEnumerator": {"0": 1, **{str(k): int(v) for k, v in sorted(weight_enum.items())}},
        "minimumDistance": 2160,
        "minimumProjectiveOrbitSize": 7371,
        "theorem": "The 14D rank-three quotient has exactly nine projective Sp(6,3) orbits. Their orbit sizes account for all 2,391,484 projective points, and their six code weights give the complete 3^14-word weight enumerator of the q=3 line Symplectic Grassmann code.",
        "priorArtBoundary": "Cardinali-Giuzzi prove the line-code parameters and minimum distance. Their paper states full weight enumerators for the Lagrangian rank-2 and rank-3 codes, not for this line W(3,2) code. No novelty claim is made here beyond this repository-local exact orbit/enumerator computation without a separate literature classification audit.",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    out = build()
    if args.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if out["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
