#!/usr/bin/env python3
"""A 36-spread / double-six section invariant for the tau_2=111 factorization.

W33-Theory already proves an equivariant chain from the 36 W(3,3) spreads to
the 36 Schlaefli double-sixes and their 15-coordinate Pfaffian sections.  This
file does not re-prove that E6/Pfaffian identification.  It asks what each of
those 36 finite sections sees in the new two-pencil factorization

    E = U N^T = N V.

A spread D partitions the 40 points into ten W33 lines.  Restrict a dirty row,
whose two tokens are a,b, to the ten columns in D.  The squared entries sum to

    2 + 2 q_D(a,b),

where q_D=1 iff a,b occupy the same spread line.  A clean row contributes 1.
Since there are 36 clean and four dirty rows,

    sum_i sum_{j in D} E_ij^2 = 44 + 2 R_D,

where R_D counts dirty row token-pairs co-located in D.  Viewed by columns, D
contains exactly one of the four dirty column lines (because those four lines
are one point-pencil and a spread contains exactly one line through that
point).  The same squared sum is

    9*4 + ||P_a+P_b||^2 = 44 + 2 s(a,b),

with s=4,1,0 for equal, collinear, noncollinear column tokens.  Therefore, for
EVERY one of the 36 spreads,

    R_D = s(the unique dirty column pair carried by D).

The dual equation holds after exchanging rows and columns.  This converts the
four dirty-pair problem to a tiny exact signature system.  A pair contributes
to the 36 section signatures as:

    equal          all 36 sections,
    collinear      the 9 spreads containing its unique joining line,
    noncollinear   no section.

Exhausting the signature system leaves exactly 95 ordered row/column type
assignments (out of 81^2) in each of the equal/collinear/noncollinear dirty-centre
cases, collapsing to nine histogram-pair families.  The section invariant is
strong but does NOT distinguish the three centre relations and therefore does
not by itself settle 111.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "the_111_double_six_section_invariant.json"
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
    point_lines = [[] for _ in range(40)]
    adj = [set() for _ in range(40)]
    for li, L in enumerate(lines):
        for p in L:
            point_lines[p].append(li)
            adj[p] |= set(L) - {p}
    assert len(lines) == 40 and all(len(x) == 4 for x in point_lines)
    return lines, point_lines, adj


def spreads(lines, point_lines):
    out = []
    def rec(chosen, covered):
        if len(covered) == 40:
            assert len(chosen) == 10
            out.append(tuple(sorted(chosen)))
            return
        p = min(set(range(40)) - covered)
        for li in point_lines[p]:
            if lines[li].isdisjoint(covered):
                rec(chosen + [li], covered | lines[li])
    rec([], frozenset())
    out = sorted(set(out))
    assert len(out) == 36
    return out


def hist_name(types):
    c = Counter(types)
    return "S%d-C%d-N%d" % (c["S"], c["C"], c["N"])


def build():
    lines, point_lines, adj = geometry()
    SP = spreads(lines, point_lines)
    line_sig = [tuple(1 if li in D else 0 for D in SP) for li in range(40)]
    assert all(sum(v) == 9 for v in line_sig)

    # Section collision counts for point pairs: 36 / 9 / 0.
    collision = Counter()
    for a in range(40):
        for b in range(a, 40):
            if a == b:
                count = 36
                typ = "equal"
            else:
                count = sum(1 for D in SP if any(a in lines[li] and b in lines[li] for li in D))
                typ = "collinear" if b in adj[a] else "noncollinear"
            collision[(typ, count)] += 1
    assert collision == Counter({("equal", 36): 40, ("collinear", 9): 240, ("noncollinear", 0): 540})

    all1 = (1,) * 36
    zero = (0,) * 36
    signature_types = [("N", None, zero), ("S", None, all1)] + [
        ("C", li, line_sig[li]) for li in range(40)
    ]

    # For a multiset of four dirty row pair signatures, retain the possible
    # type histogram for each exact 36-vector sum.
    sum_to_hists = defaultdict(set)
    for inds in itertools.combinations_with_replacement(range(len(signature_types)), 4):
        vec = tuple(sum(signature_types[t][2][d] for t in inds) for d in range(36))
        types = [signature_types[t][0] for t in inds]
        sum_to_hists[vec].add(hist_name(types))
    assert len(sum_to_hists) == 143225

    value = {"S": 4, "C": 1, "N": 0}
    def target(types4, centre):
        pencil = sorted(point_lines[centre])
        assert len(pencil) == 4
        # The four pencil-line signatures partition the 36 spreads.
        assert all(sum(line_sig[li][d] for li in pencil) == 1 for d in range(36))
        row = []
        for d in range(36):
            k = next(k for k, li in enumerate(pencil) if line_sig[li][d])
            row.append(value[types4[k]])
        return tuple(row)

    reps = {
        "equal": 0,
        "collinear": min(adj[0]),
        "noncollinear": min(set(range(40)) - {0} - adj[0]),
    }
    per_case = {}
    expected_hist_pairs = {
        ("S4-C0-N0", "S4-C0-N0"),
        ("S1-C3-N0", "S1-C3-N0"),
        ("S1-C0-N3", "S0-C4-N0"),
        ("S0-C4-N0", "S1-C0-N3"),
        ("S0-C4-N0", "S0-C4-N0"),
        ("S0-C3-N1", "S0-C3-N1"),
        ("S0-C2-N2", "S0-C2-N2"),
        ("S0-C1-N3", "S0-C1-N3"),
        ("S0-C0-N4", "S0-C0-N4"),
    }
    for label, ccol in reps.items():
        ordered = []
        hist_pairs = set()
        for rt in itertools.product("SCN", repeat=4):
            tr = target(rt, 0)
            rh = hist_name(rt)
            for ct in itertools.product("SCN", repeat=4):
                tc = target(ct, ccol)
                ch = hist_name(ct)
                # First section equation: row signature sum = column block target.
                # Dual equation: column signature sum = row block target.
                if ch in sum_to_hists.get(tr, set()) and rh in sum_to_hists.get(tc, set()):
                    ordered.append(("".join(rt), "".join(ct)))
                    hist_pairs.add((rh, ch))
        assert len(ordered) == 95
        assert hist_pairs == expected_hist_pairs
        per_case[label] = {
            "orderedTypeAssignmentsSurviving": 95,
            "naiveOrderedTypeAssignments": 81 * 81,
            "histogramPairFamilies": sorted([list(x) for x in hist_pairs]),
        }

    checks = {
        "exactly_36_spreads": len(SP) == 36,
        "every_line_occurs_in_9_spreads": all(sum(v) == 9 for v in line_sig),
        "pair_section_collisions_are_36_9_0": collision == Counter({("equal",36):40,("collinear",9):240,("noncollinear",0):540}),
        "signature_sum_census_complete": len(sum_to_hists) == 143225,
        "95_ordered_type_pairs_survive_each_centre_case": all(x["orderedTypeAssignmentsSurviving"] == 95 for x in per_case.values()),
        "nine_histogram_pair_families": all(len(x["histogramPairFamilies"]) == 9 for x in per_case.values()),
        "centre_relation_not_distinguished_at_this_layer": len({json.dumps(x["histogramPairFamilies"]) for x in per_case.values()}) == 1,
    }
    assert all(checks.values())
    return {
        "schema": "holotrade.tau2-111-double-six-section-invariant.v1",
        "status": "PASS",
        "checks": checks,
        "sectionIdentity": (
            "For each spread D, the number R_D of dirty row token-pairs whose two points lie on one line of D equals s(a,b) for the unique dirty column in D, where s=4/1/0 for equal/collinear/noncollinear tokens. The row/column-dual identity holds simultaneously."
        ),
        "pairSectionCollisionCounts": {"equal": 36, "collinear": 9, "noncollinear": 0},
        "cases": per_case,
        "survivingHistogramFamilies": sorted([list(x) for x in expected_hist_pairs]),
        "crossTrackE6Anchor": (
            "W33-Theory w33_pass7305_7306_cspread_intrinsic_double_six.py and w33_pass7307_7309_double_six_naimark_isometry.py identify these same 36 spreads equivariantly with the 36 Schlaefli double-sixes/Pfaffian sections. That identification is imported, not re-proved here."
        ),
        "boundary": (
            "This is an exact necessary condition on the two-pencil factorization. It cuts dirty-pair type assignments sharply but leaves the same nine histogram families in all three dirty-centre relations, so it does not by itself improve tau_2 beyond [111,115]."
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
