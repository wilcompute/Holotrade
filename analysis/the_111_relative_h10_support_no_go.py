#!/usr/bin/env python3
"""Support-level relative H10 cannot be the missing tau2=111 obstruction.

The previous aggregate-parity pass proved

    ker_F2(N) = im_F2(M),

where N is W(3,3) line/point incidence and M is the 40x45 point/octet
incidence.  Hence H10 = ker(M^T)/im(M) is ten-dimensional, but aggregate token
parity has zero H10 class.

This pass asks the sharper question required by the 10,480-blocker census:
could *choosing one concrete blocker support rather than another* inside a
fixed two-pencil token pair create a nonzero relative H10 class?

No.  Exhaustively:

* for a clean line with fixed centre c, the nine minimum blockers B(c,m) all
  have the same line-count vector, and their affine difference space has rank
  8 over F2;
* a dirty equal pair has exactly ten decorated 12-leaf states, all 12-distinct
  blocker supports, with affine difference rank 9;
* a dirty collinear pair has 18 decorated states: six 12-point blockers plus
  twelve 11-point minimum blockers with one duplicated point; affine rank 13;
* a dirty noncollinear pair has 18 decorated states: sixteen 12-point blockers
  plus two 11-point-plus-duplicate states; affine rank 13.

For every fixed local token datum, every pairwise state difference is killed by
N, hence lies in ker(N)=im(M), the octet boundary code.  The script does not
merely infer this: it reconstructs all states for all 40/240/540 point-pair
orbits, checks their exact integer line counts, builds the complete 2^15 octet
span, and tests membership of every difference.

Therefore any genuinely nonzero characteristic-two obstruction must include
matching/gluing data between row and column shadows (a higher chain object), not
only the point-support or point-multiplicity parity of one shadow.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "the_111_relative_h10_support_no_go.json"


def load_module(name: str, filename: str):
    path = ROOT / "analysis" / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {filename}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


B12 = load_module("blockers12", "the_10480_twelve_point_blockers.py")
PAR = load_module("parity", "the_111_aggregate_parity_is_octet_boundary.py")


def mask_from_vector(v) -> int:
    return sum((int(x) & 1) << i for i, x in enumerate(v))


def mask_from_set(S) -> int:
    return sum(1 << int(i) for i in S)


def gf2_rank(masks) -> int:
    piv = {}
    for value in masks:
        x = int(value)
        while x:
            p = x.bit_length() - 1
            if p in piv:
                x ^= piv[p]
            else:
                piv[p] = x
                break
    return len(piv)


def state_variation_rank(states) -> int:
    base = mask_from_vector(states[0])
    return gf2_rank(mask_from_vector(v) ^ base for v in states[1:])


def build():
    lines, adj, N = B12.geometry()
    mins = B12.minimum_blockers(adj)
    mins_by_center = defaultdict(list)
    for c, B in mins:
        mins_by_center[c].append(B)
    assert all(len(mins_by_center[c]) == 9 for c in range(40))

    # Rebuild the octet boundary code as an explicit set of 2^15 masks.
    n, _, _, M = PAR.octet_module().build(3)
    assert n == 40 and M.shape == (40, 45)
    octet_masks = [sum((int(M[p, j]) & 1) << p for p in range(40))
                   for j in range(45)]
    basis = PAR.basis2(octet_masks)
    assert len(basis) == 15
    boundary = set()
    for selector in range(1 << len(basis)):
        x = 0
        for i, b in enumerate(basis):
            if selector & (1 << i):
                x ^= b
        boundary.add(x)
    assert len(boundary) == 1 << 15

    # Every boundary is also an H10 numerator vector because M is self-orthogonal.
    def in_ker_mt(mask: int) -> bool:
        return all(((mask & o).bit_count() & 1) == 0 for o in octet_masks)
    assert all(in_ker_mt(x) for x in boundary)

    # Full 12-point blocker catalogue indexed by its unique two-pencil pair.
    pair_for_excess = {}
    pair_type = {}
    for a in range(40):
        for b in range(a, 40):
            e = tuple(N[i][a] + N[i][b] for i in range(40))
            assert e not in pair_for_excess
            pair_for_excess[e] = (a, b)
            pair_type[(a, b)] = (
                "equal" if a == b else "collinear" if b in adj[a]
                else "noncollinear"
            )
    assert Counter(pair_type.values()) == Counter(
        {"equal": 40, "collinear": 240, "noncollinear": 540}
    )

    blockers_by_pair = defaultdict(set)
    for c, B in mins:
        for x in range(40):
            if x in B:
                continue
            S = frozenset(set(B) | {x})
            counts = B12.line_counts(S, lines)
            e = tuple(z - 1 for z in counts)
            blockers_by_pair[pair_for_excess[e]].add(S)
    for c in range(40):
        S = frozenset(adj[c])
        e = tuple(z - 1 for z in B12.line_counts(S, lines))
        blockers_by_pair[pair_for_excess[e]].add(S)
    assert sum(len(v) for v in blockers_by_pair.values()) == 10480

    # Clean local fibres: all nine labels at fixed centre differ by boundaries.
    clean_ranks = Counter()
    clean_differences = 0
    for c in range(40):
        states = []
        target = tuple(1 + N[i][c] for i in range(40))
        for B in mins_by_center[c]:
            v = tuple(1 if p in B else 0 for p in range(40))
            counts = tuple(sum(N[i][p] * v[p] for p in range(40)) for i in range(40))
            assert counts == target
            states.append(v)
        base = mask_from_vector(states[0])
        for v in states[1:]:
            d = mask_from_vector(v) ^ base
            assert d in boundary and in_ker_mt(d)
            clean_differences += 1
        clean_ranks[state_variation_rank(states)] += 1
    assert clean_ranks == Counter({8: 40})

    # Complete dirty state fibre for a fixed unordered pair {a,b}.
    # State entries are point multiplicities, summing to 12.
    dirty_state_count_by_type = defaultdict(Counter)
    dirty_rank_by_type = defaultdict(Counter)
    dirty_kind_by_type = defaultdict(Counter)
    dirty_differences = 0
    total_dirty_states = 0

    for pair, typ in pair_type.items():
        a, b = pair
        states = []
        kinds = []

        # Twelve distinct second-coordinate points.
        for S in blockers_by_pair[pair]:
            v = tuple(1 if p in S else 0 for p in range(40))
            states.append(v)
            kinds.append("shadow12")

        # Eleven-point minimum shadow plus one duplicated fibre point.
        if a != b:
            for centre, duplicate in ((a, b), (b, a)):
                for B in mins_by_center[centre]:
                    if duplicate not in B:
                        continue
                    v = [1 if p in B else 0 for p in range(40)]
                    v[duplicate] += 1
                    states.append(tuple(v))
                    kinds.append("shadow11_plus_duplicate")

        assert len(states) == len(set(states))
        target = tuple(1 + N[i][a] + N[i][b] for i in range(40))
        for v in states:
            assert sum(v) == 12
            counts = tuple(sum(N[i][p] * v[p] for p in range(40)) for i in range(40))
            assert counts == target

        base = mask_from_vector(states[0])
        for v in states[1:]:
            d = mask_from_vector(v) ^ base
            assert d in boundary and in_ker_mt(d)
            dirty_differences += 1

        dirty_state_count_by_type[typ][len(states)] += 1
        dirty_rank_by_type[typ][state_variation_rank(states)] += 1
        dirty_kind_by_type[typ].update(kinds)
        total_dirty_states += len(states)

    expected_counts = {
        "equal": Counter({10: 40}),
        "collinear": Counter({18: 240}),
        "noncollinear": Counter({18: 540}),
    }
    expected_ranks = {
        "equal": Counter({9: 40}),
        "collinear": Counter({13: 240}),
        "noncollinear": Counter({13: 540}),
    }
    assert dict(dirty_state_count_by_type) == expected_counts
    assert dict(dirty_rank_by_type) == expected_ranks
    assert dirty_kind_by_type["equal"] == Counter({"shadow12": 400})
    assert dirty_kind_by_type["collinear"] == Counter(
        {"shadow11_plus_duplicate": 2880, "shadow12": 1440}
    )
    assert dirty_kind_by_type["noncollinear"] == Counter(
        {"shadow12": 8640, "shadow11_plus_duplicate": 1080}
    )
    assert total_dirty_states == 14440

    checks = {
        "octet_boundary_dimension_15": len(boundary) == 1 << 15,
        "octet_boundaries_lie_in_H10_numerator": all(in_ker_mt(x) for x in boundary),
        "clean_fixed_centre_state_count_9": all(len(mins_by_center[c]) == 9 for c in range(40)),
        "clean_affine_variation_rank_8_everywhere": clean_ranks == Counter({8: 40}),
        "dirty_complete_state_counts_10_18_18": dict(dirty_state_count_by_type) == expected_counts,
        "dirty_affine_variation_ranks_9_13_13": dict(dirty_rank_by_type) == expected_ranks,
        "dirty_state_total_14440": total_dirty_states == 14440,
        "all_tested_local_state_differences_are_octet_boundaries": clean_differences > 0 and dirty_differences > 0,
    }
    assert all(checks.values())

    return {
        "schema": "holotrade.tau2-111-relative-h10-support-no-go.v1",
        "status": "PASS",
        "checks": checks,
        "clean": {
            "statesPerCentre": 9,
            "centres": 40,
            "affineVariationRank": 8,
        },
        "dirty": {
            "pairOrbitCounts": {"equal": 40, "collinear": 240, "noncollinear": 540},
            "statesPerPair": {"equal": 10, "collinear": 18, "noncollinear": 18},
            "affineVariationRank": {"equal": 9, "collinear": 13, "noncollinear": 13},
            "stateKindTotals": {
                typ: dict(sorted(counter.items()))
                for typ, counter in sorted(dirty_kind_by_type.items())
            },
            "totalDecoratedStates": total_dirty_states,
        },
        "theorem": (
            "For every fixed clean centre or dirty two-pencil token pair, all local shadow/multiplicity refinements have pairwise mod-2 differences in ker_F2(N)=im_F2(M). Hence every support-local relative vector has zero class in H10=ker(M^T)/im(M)."
        ),
        "consequence": (
            "A nonzero characteristic-two obstruction to tau_2=111 must include row/column leaf-matching or gluing data. Individual blocker-support choice, even with the dirty duplicate fibre marked, is H10-boundary-trivial."
        ),
        "boundary": (
            "Exact finite q=3 binary/incidence statement. It rules out a class of support-local H10 obstructions; it does not prove or disprove a 111-leaf tensor blocker."
        ),
    }


def main():
    out = build()
    print(json.dumps(out, indent=2, sort_keys=True))
    if "--write" in __import__("sys").argv:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
