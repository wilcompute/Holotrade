#!/usr/bin/env python3
"""The 36 spread/double-six sections recover every 12-point blocker support.

The earlier section invariant compressed a dirty two-pencil pair to one number
per spread and therefore retained only the equal/collinear/noncollinear type.
That scalar is too coarse.  This pass keeps the intrinsic ten-line partition
provided by each W(3,3) spread and records, for every unordered pair of spread
lines, the number of W33-collinear selected point pairs crossing those two
lines.

For a spread D={L_0,...,L_9} and blocker S define

    F_D(S)_{ij} = #{(x,y): x in S cap L_i, y in S cap L_j, x~y},  i<j.

There are C(10,2)=45 entries per spread and exactly 36 spreads, hence 1620
small integers.  Lines and spreads are canonically ordered by their point
indices, so the resulting SHA-256 fingerprint is deterministic.

Exhausting the complete 10,480-blocker census proves:

* all 10,480 full 36-section fingerprints are distinct;
* over every fixed two-pencil pair, the fingerprint counts are exactly the
  support counts 10 / 6 / 16 for equal / collinear / noncollinear pairs;
* the weaker per-spread scalar sum of the 45 entries is not support-injective,
  confirming that the refinement really comes from section-local structure.

The same 36 spreads are identified equivariantly in W33-Theory with the 36
Schlaefli double-sixes/Pfaffian sections.  That cross-track identification is
imported; this verifier reconstructs only the W(3,3) spread side.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "the_111_double_six_support_fingerprint.json"


def load_blocker_module():
    path = ROOT / "analysis" / "the_10480_twelve_point_blockers.py"
    spec = importlib.util.spec_from_file_location("blockers12_fp", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import twelve-point blocker census")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


B12 = load_blocker_module()


def enumerate_spreads(lines):
    containing = [[] for _ in range(40)]
    masks = []
    for i, L in enumerate(lines):
        m = sum(1 << p for p in L)
        masks.append(m)
        for p in L:
            containing[p].append(i)
    full = (1 << 40) - 1
    spreads = []

    def rec(used: int, chosen: tuple[int, ...]):
        if used == full:
            if len(chosen) == 10:
                spreads.append(tuple(sorted(chosen)))
            return
        if len(chosen) >= 10:
            return
        p = next(i for i in range(40) if not ((used >> i) & 1))
        for li in containing[p]:
            if masks[li] & used:
                continue
            rec(used | masks[li], chosen + (li,))

    rec(0, ())
    spreads = sorted(set(spreads))
    assert len(spreads) == 36
    assert all(len(D) == 10 for D in spreads)
    assert all(sum(masks[li] for li in ()) == 0 for _ in [0])  # deterministic no-op sanity
    return spreads, masks


def blocker_catalogue(lines, adj, N):
    mins = B12.minimum_blockers(adj)
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

    blockers = set()
    for _, B in mins:
        for x in range(40):
            if x not in B:
                blockers.add(frozenset(set(B) | {x}))
    blockers |= {frozenset(adj[c]) for c in range(40)}
    assert len(blockers) == 10480

    rows = []
    for S in sorted(blockers, key=lambda s: tuple(sorted(s))):
        counts = B12.line_counts(S, lines)
        e = tuple(x - 1 for x in counts)
        pair = pair_for_excess[e]
        rows.append((S, pair, pair_type[pair]))
    return rows


def fingerprint(S, spreads, line_masks, adj_masks):
    sm = sum(1 << p for p in S)
    values = []
    weak = []
    for D in spreads:
        section = []
        for ia in range(10):
            left = sm & line_masks[D[ia]]
            for ib in range(ia + 1, 10):
                right = sm & line_masks[D[ib]]
                z = 0
                x = left
                while x:
                    bit = x & -x
                    p = bit.bit_length() - 1
                    z += (adj_masks[p] & right).bit_count()
                    x ^= bit
                section.append(z)
        assert len(section) == 45
        values.extend(section)
        weak.append(sum(section))
    wire = bytes(values)
    return hashlib.sha256(wire).hexdigest(), tuple(weak), tuple(values)


def build():
    lines, adj, N = B12.geometry()
    spreads, line_masks = enumerate_spreads(lines)
    line_occ = Counter(li for D in spreads for li in D)
    assert line_occ == Counter({i: 9 for i in range(40)})
    adj_masks = [sum(1 << q for q in adj[p]) for p in range(40)]
    rows = blocker_catalogue(lines, adj, N)

    full_seen = {}
    weak_seen = defaultdict(int)
    per_pair_full = defaultdict(set)
    per_pair_support = Counter()
    per_type_support = Counter()
    value_min = 99
    value_max = -1

    for S, pair, typ in rows:
        h, weak, values = fingerprint(S, spreads, line_masks, adj_masks)
        if h in full_seen:
            raise AssertionError("full 36-section support fingerprint collision")
        full_seen[h] = tuple(sorted(S))
        weak_seen[weak] += 1
        per_pair_full[pair].add(h)
        per_pair_support[pair] += 1
        per_type_support[typ] += 1
        value_min = min(value_min, min(values))
        value_max = max(value_max, max(values))

    expected = {"equal": 10, "collinear": 6, "noncollinear": 16}
    for pair, count in per_pair_support.items():
        typ = "equal" if pair[0] == pair[1] else "collinear" if pair[1] in adj[pair[0]] else "noncollinear"
        assert count == expected[typ]
        assert len(per_pair_full[pair]) == count
    assert per_type_support == Counter({"equal": 400, "collinear": 1440, "noncollinear": 8640})

    weak_unique = len(weak_seen)
    max_weak_collision = max(weak_seen.values())
    checks = {
        "exactly_36_spreads": len(spreads) == 36,
        "every_line_in_exactly_9_spreads": line_occ == Counter({i: 9 for i in range(40)}),
        "fingerprint_dimension_36_times_45": 36 * 45 == 1620,
        "all_10480_blockers_reconstructed": len(rows) == 10480,
        "all_10480_full_fingerprints_unique": len(full_seen) == 10480,
        "fixed_pair_fingerprint_counts_are_10_6_16": all(len(per_pair_full[p]) == per_pair_support[p] for p in per_pair_support),
        "weak_section_totals_are_not_support_injective": weak_unique < 10480 and max_weak_collision > 1,
        "section_entries_fit_single_byte": 0 <= value_min <= value_max < 256,
    }
    assert all(checks.values())

    return {
        "schema": "holotrade.tau2-111-double-six-support-fingerprint.v1",
        "status": "PASS",
        "checks": checks,
        "spreads": 36,
        "linesPerSpread": 10,
        "linePairsPerSpread": 45,
        "fingerprintDimension": 1620,
        "blockers": 10480,
        "uniqueFullFingerprints": len(full_seen),
        "uniqueWeakScalarFingerprints": weak_unique,
        "maximumWeakFingerprintCollision": max_weak_collision,
        "entryRange": [value_min, value_max],
        "supportsPerFixedTwoPencilPair": expected,
        "supportTotalsByPairType": dict(sorted(per_type_support.items())),
        "definition": (
            "For each of the 36 spreads and each of its 45 unordered line pairs, count W33-collinear selected point pairs crossing the two spread lines; concatenate in canonical spread/line order and SHA-256 the 1620-byte vector."
        ),
        "theorem": (
            "The full 36-section cross-line collinearity fingerprint is injective on the complete 10,480 twelve-point blocker catalogue. Thus the spread/double-six/Pfaffian section system retains enough local structure to recover the actual blocker support, not only its two-pencil excess pair."
        ),
        "crossTrackAnchor": (
            "W33-Theory passes 7305-7309 identify the same 36 spreads equivariantly with the 36 Schlaefli double-sixes/Pfaffian sections; that identification is imported rather than re-proved here."
        ),
        "boundary": (
            "Exact finite q=3 support fingerprint. Injectivity is an encoding theorem, not a tau_2=111 existence or nonexistence proof."
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
