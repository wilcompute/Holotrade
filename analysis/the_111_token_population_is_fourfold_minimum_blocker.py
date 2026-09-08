#!/usr/bin/env python3
"""Outside-box compression of the frozen 44-token factorization witnesses.

Every currently frozen SAT factorization has token multiplicity histogram
{4:11} on each axis.  This is not merely a pretty histogram.  If a is the
40-vector of row-side token multiplicities, the aggregate identity is

    N a = 4*1 + 4*P_{c_col}.

When a=4*1_S with |S|=11, division over the integers gives

    N 1_S = 1 + P_{c_col},

which is exactly the line-count profile of a minimum W33 blocker centered at
the opposite dirty-pencil centre.  The column population is dual.

This script verifies that interpretation for both axes of all three frozen SAT
factorizations, identifies the unique minimum-blocker support, and records the
compression 44 point tokens -> one 11-point blocker label plus a uniform
multiplicity four.  Scope: this is a theorem about the frozen witnesses and a
conditional algebraic implication of the {4:11} histogram; it does not claim
that every possible two-pencil factorization must have this histogram.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FACTOR = ROOT / "data" / "the_111_two_pencil_factorization.json"
OUT = ROOT / "data" / "the_111_token_population_fourfold_minimum_blocker.json"


def load_b12():
    path = ROOT / "analysis" / "the_10480_twelve_point_blockers.py"
    spec = importlib.util.spec_from_file_location("b12_token_support", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import blocker census")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def analyse_axis(tokens, opposite_centre, lines, N, min_index):
    mult = Counter(int(p) for row in tokens for p in row)
    assert sum(mult.values()) == 44
    hist = Counter(mult.values())
    support = frozenset(mult)
    fourfold = hist == Counter({4: 11})
    if not fourfold:
        return {"fourfold": False, "multiplicityHistogram": dict(sorted(hist.items()))}

    profile = tuple(sum(N[i][p] for p in support) for i in range(40))
    target = tuple(1 + N[i][opposite_centre] for i in range(40))
    assert profile == target
    matches = min_index.get(support, [])
    assert len(matches) == 1 and matches[0] == opposite_centre
    return {
        "fourfold": True,
        "multiplicityHistogram": {"4": 11},
        "support": sorted(support),
        "supportSize": 11,
        "uniqueMinimumBlockerCentre": matches[0],
        "centreIsOppositeDirtyPencilCentre": matches[0] == opposite_centre,
        "integerProfile": "N*1_S = 1 + P_c",
    }


def main():
    b12 = load_b12()
    lines, adj, N = b12.geometry()
    mins = b12.minimum_blockers(adj)
    min_index = defaultdict(list)
    for c, B in mins:
        min_index[B].append(c)
    assert len(min_index) == 360 and all(len(v) == 1 for v in min_index.values())

    factor = json.loads(FACTOR.read_text())
    assert factor["status"] == "PASS" and factor["statusHistogram"] == {"SAT": 3}
    cases = {}
    all_ok = True
    for name, row in sorted(factor["cases"].items()):
        rr = analyse_axis(row["rowTokens"], int(row["cCol"]), lines, N, min_index)
        cc = analyse_axis(row["columnTokens"], int(row["cRow"]), lines, N, min_index)
        all_ok &= rr.get("fourfold", False) and cc.get("fourfold", False)
        cases[name] = {"rowPopulation": rr, "columnPopulation": cc}

    out = {
        "schema": "holotrade.tau2-111-token-population-fourfold-minimum-blocker.v1",
        "status": "PASS" if all_ok else "FAIL",
        "cases": cases,
        "checks": {
            "all_six_frozen_populations_are_11_labels_times_four": all_ok,
            "all_six_supports_are_unique_minimum_blockers": all_ok,
            "row_support_centres_are_opposite_column_dirty_centres": all(v["rowPopulation"].get("centreIsOppositeDirtyPencilCentre") for v in cases.values()),
            "column_support_centres_are_opposite_row_dirty_centres": all(v["columnPopulation"].get("centreIsOppositeDirtyPencilCentre") for v in cases.values()),
        },
        "conditionalTheorem": (
            "For any two-pencil factorization whose aggregate token multiplicity vector has histogram {4:11}, the 11-point support is a minimum W33 blocker centered at the opposite axis's dirty-pencil centre, because N a=4(1+P_c) and a=4*1_S imply N1_S=1+P_c over the integers."
        ),
        "compression": "44 token occurrences -> uniform multiplicity four on one 11-point minimum-blocker support",
        "boundary": "The frozen SAT witnesses all satisfy the premise. This script does not prove that every factorization solution must have multiplicity histogram {4:11}.",
    }
    assert out["status"] == "PASS" and all(out["checks"].values())
    print(json.dumps(out, indent=2, sort_keys=True))
    if "--write" in __import__("sys").argv:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
