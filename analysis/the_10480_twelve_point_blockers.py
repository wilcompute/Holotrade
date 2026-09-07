#!/usr/bin/env python3
"""Exact census of every 12-point blocking set of W(3,3).

The companion theorem ``the_mass_eight_excess_is_two_pencils.py`` proves that
for every 12-point blocker S the line-excess vector

    e_L = |S cap L| - 1

has total mass eight and is exactly the sum of two point pencils P_a + P_b,
with the unordered pair {a,b} uniquely determined by e.  The recent closed
form for the 360 minimum 11-blockers supplies the other direction.

This file closes the census without CP-SAT:

* every minimum blocker B has a unique centre c and excludes c;
* for every x outside B, B union {x} is automatically a 12-point blocker and
  has excess P_c + P_x;
* the 360*29 = 10,440 such one-point extensions are all distinct;
* the only 12-blockers not of that form are the 40 neighbourhoods Adj(c), whose
  excess is 2 P_c.

Hence there are exactly 10,480 twelve-point blockers.  By the type of their
unique two-pencil excess pair:

    equal pencils        400 = 40 * 10
    collinear pair      1440 = 240 * 6
    noncollinear pair   8640 = 540 * 16.

For a fixed equal pair {c,c}, the ten supports are the nine B(c,m) union {c}
plus Adj(c).  For a fixed collinear pair {a,b}, three extensions come from
centre a and three from centre b.  For a fixed noncollinear pair, eight come
from either centre.  Every extension contains exactly one minimum blocker;
Adj(c) contains none.

This is a finite q=3 blocking-set statement.  It does not decide tau_2.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import importlib.util
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "the_10480_twelve_point_blockers.json"
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
        span = set()
        for x, y in itertools.product(range(Q), repeat=2):
            if not (x or y):
                continue
            w = tuple((x * pts[a][k] + y * pts[b][k]) % Q for k in range(4))
            span.add(pidx[norm(w)])
        if len(span) == 4:
            line_sets.add(frozenset(span))
    lines = sorted(line_sets, key=lambda s: tuple(sorted(s)))
    adj = [set() for _ in range(40)]
    for line in lines:
        for p in line:
            adj[p] |= set(line) - {p}
    N = [[1 if p in line else 0 for p in range(40)] for line in lines]
    assert len(pts) == len(lines) == 40 and all(len(x) == 12 for x in adj)
    return lines, adj, N


def octet_module():
    path = ROOT / "analysis" / "the_minimum_blocker_labels_are_octets.py"
    spec = importlib.util.spec_from_file_location("octet_labels", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import octet blocker module")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def minimum_blockers(adj):
    n, _, _, B = octet_module().build(3)
    assert n == 40 and B.shape == (40, 45)
    octets = [frozenset(i for i in range(40) if B[i, j]) for j in range(45)]
    assert len(set(octets)) == 45 and all(len(C) == 8 for C in octets)
    rows = []
    for c in range(40):
        through = [C for C in octets if c in C]
        assert len(through) == 9
        for C in through:
            block = frozenset((adj[c] ^ set(C)) - {c})
            assert len(block) == 11 and c not in block
            rows.append((c, block))
    assert len(rows) == 360 and len({B for _, B in rows}) == 360
    return rows


def line_counts(S, lines):
    return tuple(len(S & line) for line in lines)


def build():
    lines, adj, N = geometry()
    mins = minimum_blockers(adj)
    min_sets = {B for _, B in mins}

    pair_for_excess = {}
    pair_type = {}
    for a in range(40):
        for b in range(a, 40):
            e = tuple(N[i][a] + N[i][b] for i in range(40))
            if e in pair_for_excess:
                raise AssertionError("two-pencil excess must recover its unordered pair")
            pair_for_excess[e] = (a, b)
            pair_type[(a, b)] = (
                "equal" if a == b else "collinear" if b in adj[a] else "noncollinear"
            )
    assert len(pair_for_excess) == 820
    assert Counter(pair_type.values()) == Counter({"noncollinear": 540, "collinear": 240, "equal": 40})

    extension_instances = []
    for c, B in mins:
        for x in range(40):
            if x not in B:
                extension_instances.append((c, x, frozenset(set(B) | {x})))
    assert len(extension_instances) == 360 * 29 == 10440
    extension_sets = {S for _, _, S in extension_instances}
    assert len(extension_sets) == 10440

    neighbourhoods = {frozenset(adj[c]) for c in range(40)}
    assert len(neighbourhoods) == 40
    assert not (extension_sets & neighbourhoods)
    blockers12 = extension_sets | neighbourhoods
    assert len(blockers12) == 10480

    by_pair = defaultdict(int)
    by_type = Counter()
    contained_minimum = Counter()
    for S in blockers12:
        counts = line_counts(S, lines)
        assert len(S) == 12 and min(counts) >= 1 and sum(counts) == 48
        excess = tuple(x - 1 for x in counts)
        assert sum(excess) == 8 and excess in pair_for_excess
        pair = pair_for_excess[excess]
        typ = pair_type[pair]
        by_pair[pair] += 1
        by_type[typ] += 1
        nmin = sum(1 for x in S if frozenset(set(S) - {x}) in min_sets)
        contained_minimum[nmin] += 1

    assert by_type == Counter({"noncollinear": 8640, "collinear": 1440, "equal": 400})
    assert all(by_pair[p] == (10 if pair_type[p] == "equal" else 6 if pair_type[p] == "collinear" else 16)
               for p in by_pair)
    assert contained_minimum == Counter({1: 10440, 0: 40})

    extension_type = Counter()
    for c, x, S in extension_instances:
        typ = "equal" if x == c else "collinear" if x in adj[c] else "noncollinear"
        extension_type[typ] += 1
        pair = tuple(sorted((c, x)))
        e = tuple(z - 1 for z in line_counts(S, lines))
        assert pair_for_excess[e] == pair
    assert extension_type == Counter({"noncollinear": 8640, "collinear": 1440, "equal": 360})

    neighbourhood_ok = True
    for c in range(40):
        S = frozenset(adj[c])
        e = tuple(z - 1 for z in line_counts(S, lines))
        neighbourhood_ok &= pair_for_excess[e] == (c, c)
    assert neighbourhood_ok

    checks = {
        "minimum_blockers_360": len(mins) == 360,
        "one_point_extension_instances_10440": len(extension_instances) == 10440,
        "extensions_are_all_distinct": len(extension_sets) == 10440,
        "forty_neighbourhood_exceptions": len(neighbourhoods) == 40 and not extension_sets.intersection(neighbourhoods),
        "all_10480_are_blockers": len(blockers12) == 10480,
        "two_pencil_pair_is_unique": len(pair_for_excess) == 820,
        "pair_support_multiplicities_10_6_16": all(by_pair[p] == (10 if pair_type[p] == "equal" else 6 if pair_type[p] == "collinear" else 16) for p in by_pair),
        "type_totals_400_1440_8640": by_type == Counter({"equal": 400, "collinear": 1440, "noncollinear": 8640}),
        "all_extensions_contain_exactly_one_minimum_blocker": contained_minimum[1] == 10440,
        "only_neighbourhoods_contain_none": contained_minimum[0] == 40,
        "neighbourhood_excess_is_double_centre_pencil": neighbourhood_ok,
    }
    assert all(checks.values())
    return {
        "schema": "holotrade.w33-twelve-point-blocker-census.v1",
        "status": "PASS",
        "checks": checks,
        "total": 10480,
        "onePointExtensions": 10440,
        "neighbourhoodExceptions": 40,
        "twoPencilPairTypes": dict(sorted(by_type.items())),
        "supportsPerFixedPair": {"equal": 10, "collinear": 6, "noncollinear": 16},
        "construction": (
            "Every one-point extension B(c,m) union {x}, x outside B, is a 12-point blocker with line excess P_c+P_x. The 360 minimum blockers have 29 outside points each and all 10,440 extensions are distinct. The only remaining supports are the 40 neighbourhoods Adj(c), with excess 2P_c."
        ),
        "fixedPairReading": (
            "For {c,c}: nine B(c,m) union {c} plus Adj(c). For a collinear pair {a,b}: three unique-minimum-blocker extensions centred at a and three centred at b. For a noncollinear pair: eight centred at either endpoint."
        ),
        "minimumSubblockerHistogram": {str(k): v for k, v in sorted(contained_minimum.items())},
        "boundary": "Exact finite q=3 blocker census. It classifies size-12 shadows but does not itself decide the tensor blocker number tau_2.",
    }


def main():
    out = build()
    print(json.dumps(out, indent=2, sort_keys=True))
    if "--write" in __import__("sys").argv:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
