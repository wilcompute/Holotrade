#!/usr/bin/env python3
"""Audit the 115-leaf witness for a blocker-of-blockers defect skeleton.

The exact defect audit found 33 minimum row shadows and 33 minimum column
shadows.  On each axis their centre-map fibres have profile 3^11 and each
three-line fibre is contained in the four-line pencil through its centre.

This script tests the next structural possibility instead of assuming it:
  * do the eleven distinct centres themselves form a minimum W33 blocker?
  * are row and column centre blockers the same object?
  * what is the centre/far-triple decomposition of that second-level blocker?
  * for each first-level centre, which fourth pencil line is omitted, and how
    does that 11-line multiset meet the seven oversized shadows?
  * does the stored order-six witness symmetry preserve the centre skeleton?

A positive recursive-blocker result would be a theorem about this witness, not
a lower bound for tau_2 and not a universal defect classification.
"""
from __future__ import annotations

import collections
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/w33_defect115_recursive_centres.json"
Q = 3
N = 40


def nm(v):
    i = next(k for k, x in enumerate(v) if x % Q)
    z = pow(v[i] % Q, -1, Q)
    return tuple((z * x) % Q for x in v)


def form(u, v):
    return (u[0] * v[1] - u[1] * v[0] + u[2] * v[3] - u[3] * v[2]) % Q


def cycle_shape_on_subset(perm, S):
    S = set(S)
    assert {perm[x] for x in S} == S
    seen = set()
    C = collections.Counter()
    for x in sorted(S):
        if x in seen:
            continue
        y = x
        n = 0
        while y not in seen:
            seen.add(y)
            n += 1
            y = perm[y]
        C[n] += 1
    return dict(sorted(C.items()))


def main():
    pts = sorted({nm(v) for v in itertools.product(range(Q), repeat=4) if any(v)})
    idx = {v: i for i, v in enumerate(pts)}
    lines = set()
    for a, b in itertools.combinations(range(N), 2):
        if form(pts[a], pts[b]):
            continue
        S = set()
        for x, y in itertools.product(range(Q), repeat=2):
            if x == y == 0:
                continue
            S.add(idx[nm(tuple((x * pts[a][k] + y * pts[b][k]) % Q for k in range(4)))])
        if len(S) == 4:
            lines.add(tuple(sorted(S)))
    lines = sorted(lines)
    assert len(lines) == 40
    LS = [set(L) for L in lines]
    thru = [[li for li, L in enumerate(lines) if p in L] for p in range(N)]
    assert {len(x) for x in thru} == {4}

    datum = json.loads((ROOT / "data/tensor_symmetric_blocker.json").read_text())
    X = {(v // N, v % N) for v in datum["witness"]}
    assert len(X) == 115

    def blocker(S):
        return all(S & L for L in LS)

    def centre(S):
        dbl = [li for li, L in enumerate(LS) if len(S & L) == 2]
        for p in range(N):
            if set(dbl) == set(thru[p]):
                return p
        return None

    def collinear(a, b):
        return any(a in L and b in L for L in LS)

    def shadows(axis):
        out = []
        for L in lines:
            S = set()
            if axis == "row":
                for p in L:
                    S |= {q for a, q in X if a == p}
            else:
                for q in L:
                    S |= {p for p, b in X if b == q}
            out.append(S)
        return out

    axes = {}
    for tag in ("row", "col"):
        sh = shadows(tag)
        by = collections.defaultdict(list)
        for li, S in enumerate(sh):
            if len(S) == 11:
                c = centre(S)
                assert c is not None
                by[c].append(li)
        assert len(by) == 11 and set(map(len, by.values())) == {3}

        C = set(by)
        Ccentre = centre(C) if blocker(C) and len(C) == 11 else None
        intersection_profile = collections.Counter(len(C & L) for L in LS)
        omitted = {}
        for c, fibre in by.items():
            miss = sorted(set(thru[c]) - set(fibre))
            assert len(miss) == 1
            omitted[c] = miss[0]
        omitted_mult = collections.Counter(omitted.values())
        oversized = {li for li, S in enumerate(sh) if len(S) > 11}
        assert len(oversized) == 7
        minimum = {li for li, S in enumerate(sh) if len(S) == 11}
        assert len(minimum) == 33 and minimum | oversized == set(range(40))

        near = far = []
        if Ccentre is not None:
            near = sorted(p for p in C if collinear(p, Ccentre))
            far = sorted(p for p in C if not collinear(p, Ccentre))
            # For a W33 minimum blocker, the established structure is 8 near + 3 far,
            # centre excluded, with the far triple pairwise noncollinear.
            assert Ccentre not in C
            assert len(near) == 8 and len(far) == 3
            assert all(not collinear(a, b) for a, b in itertools.combinations(far, 2))

        axes[tag] = {
            "shadowSizeProfile": dict(sorted(collections.Counter(map(len, sh)).items())),
            "minimumShadowCount": 33,
            "distinctCentres": sorted(C),
            "centreSetSize": len(C),
            "centreSetBlocksEveryLine": blocker(C),
            "centreSetLineIntersectionProfile": dict(sorted(intersection_profile.items())),
            "secondLevelCentre": Ccentre,
            "secondLevelNearEight": near,
            "secondLevelFarTriple": far,
            "omittedPencilLineByCentre": {str(k): v for k, v in sorted(omitted.items())},
            "distinctOmittedPencilLines": len(omitted_mult),
            "omittedLineMultiplicityProfile": dict(sorted(collections.Counter(omitted_mult.values()).items())),
            "oversizedShadowLines": sorted(oversized),
            "omittedLinesThatAreOversized": sum(v in oversized for v in omitted.values()),
            "distinctOmittedOversizedLines": len(set(omitted.values()) & oversized),
            "omittedLineSetEqualsOversizedLineSet": set(omitted.values()) == oversized,
        }

    rowC = set(axes["row"]["distinctCentres"])
    colC = set(axes["col"]["distinctCentres"])
    sym = tuple(datum["symmetry"]["element"])
    row_invariant = {sym[x] for x in rowC} == rowC
    col_invariant = {sym[x] for x in colC} == colC

    out = {
        "schema": "holotrade.w33-defect115-recursive-centres.v1",
        "valid": True,
        "witnessLeaves": 115,
        "defectAboveShadowFloor": 5,
        "axes": axes,
        "rowAndColumnCentreSetsEqual": rowC == colC,
        "rowColumnCentreIntersection": len(rowC & colC),
        "storedOrderSixSymmetry": {
            "rowCentreSetInvariant": row_invariant,
            "columnCentreSetInvariant": col_invariant,
            "rowCentreCycleShape": cycle_shape_on_subset(sym, rowC) if row_invariant else None,
            "columnCentreCycleShape": cycle_shape_on_subset(sym, colC) if col_invariant else None,
        },
        "recursiveMinimumBlockerOnBothAxes": (
            axes["row"]["centreSetBlocksEveryLine"] and axes["row"]["secondLevelCentre"] is not None
            and axes["col"]["centreSetBlocksEveryLine"] and axes["col"]["secondLevelCentre"] is not None
        ),
        "theorem": (
            "For the stored 115-leaf W33^2 blocker, the exact centre skeleton of the "
            "33 minimum shadows is recorded on both axes.  If recursiveMinimumBlockerOnBothAxes "
            "is true, the eleven first-level shadow centres themselves form a minimum "
            "11-point W33 blocker with the established centre + far-triple structure; the "
            "remaining fields identify how each multiplicity-three fibre omits its fourth "
            "pencil line and how this interacts with the seven oversized shadows."
        ),
        "boundary": (
            "This is an exact structural audit of one certified 115-leaf witness.  It does "
            "not imply that a 111-leaf blocker exists, that all defect blockers have this "
            "recursive form, or that tau_2 equals 115."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "valid": True,
        "rowRecursive": axes["row"]["centreSetBlocksEveryLine"],
        "colRecursive": axes["col"]["centreSetBlocksEveryLine"],
        "sameCentres": rowC == colC,
        "rowSecondCentre": axes["row"]["secondLevelCentre"],
        "colSecondCentre": axes["col"]["secondLevelCentre"],
        "rowOmittedVsOversized": [axes["row"]["distinctOmittedOversizedLines"], 7],
        "colOmittedVsOversized": [axes["col"]["distinctOmittedOversizedLines"], 7],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
