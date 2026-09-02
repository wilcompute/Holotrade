#!/usr/bin/env python3
"""Audit the 115-leaf witness for a two-level centre/concurrency skeleton.

The frozen defect theorem says that the 33 minimum shadows on each axis have
11 blocker centres with multiplicity profile 3^11, and that every three-line
fibre of the CENTRE MAP is contained in some W33 pencil.  Crucially, it does
NOT say that the concurrency point of that three-line fibre equals the blocker
centre labelling the fibre.  The first version of this audit intentionally
failed on exactly that stronger assumption.

This corrected audit keeps the two point maps separate:

  c(L) = centre of the minimum blocker shadow S_L,
  p(c) = unique W33 point whose four-line pencil contains the three domain
         lines L with c(L)=c.

For each axis it tests:
  * whether the eleven blocker centres C themselves form a minimum blocker;
  * whether the eleven concurrency points P do;
  * the exact map c -> p, including fixed points, collinearity and overlap;
  * the omitted fourth pencil line at p and its relation to the seven oversized
    shadows;
  * row/column cross-identifications C_row,P_row,C_col,P_col;
  * invariance under the stored order-six witness symmetry.

Any recursive blocker discovered here is a theorem about this certified
115-leaf witness only, not a universal defect theorem and not a tau_2 bound.
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
    if {perm[x] for x in S} != S:
        return None
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
        return all(set(S) & L for L in LS)

    def centre(S):
        dbl = [li for li, L in enumerate(LS) if len(set(S) & L) == 2]
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

    def minimum_blocker_record(S):
        S = set(S)
        isb = len(S) == 11 and blocker(S)
        c = centre(S) if isb else None
        near = far = []
        if c is not None:
            near = sorted(p for p in S if collinear(p, c))
            far = sorted(p for p in S if not collinear(p, c))
            assert c not in S and len(near) == 8 and len(far) == 3
            assert all(not collinear(a, b) for a, b in itertools.combinations(far, 2))
        return {
            "size": len(S),
            "blocksEveryLine": blocker(S),
            "isMinimumBlocker": isb,
            "centre": c,
            "nearEight": near,
            "farTriple": far,
            "lineIntersectionProfile": dict(sorted(collections.Counter(len(S & L) for L in LS).items())),
        }

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
        centre_to_pencil = {}
        omitted = {}
        for c, fibre in sorted(by.items()):
            cps = [p for p in range(N) if set(fibre) <= set(thru[p])]
            # Three distinct concurrent GQ lines determine their point uniquely.
            assert len(cps) == 1
            p = cps[0]
            centre_to_pencil[c] = p
            miss = sorted(set(thru[p]) - set(fibre))
            assert len(miss) == 1
            omitted[c] = miss[0]

        P = set(centre_to_pencil.values())
        oversized = {li for li, S in enumerate(sh) if len(S) > 11}
        minimum = {li for li, S in enumerate(sh) if len(S) == 11}
        assert len(oversized) == 7 and len(minimum) == 33
        assert minimum | oversized == set(range(40))

        pair_rel = collections.Counter()
        for c, p in centre_to_pencil.items():
            if c == p:
                pair_rel["equal"] += 1
            elif collinear(c, p):
                pair_rel["distinct_collinear"] += 1
            else:
                pair_rel["noncollinear"] += 1

        omitted_values = list(omitted.values())
        axes[tag] = {
            "shadowSizeProfile": dict(sorted(collections.Counter(map(len, sh)).items())),
            "minimumShadowCount": 33,
            "multiplicityProfile": {"3": 11},
            "blockerCentres": sorted(C),
            "centreSet": minimum_blocker_record(C),
            "pencilConcurrencyPoints": sorted(P),
            "concurrencySet": minimum_blocker_record(P),
            "centreToConcurrencyPoint": {str(k): v for k, v in sorted(centre_to_pencil.items())},
            "mapImageSize": len(P),
            "mapIsBijectionOnEleven": len(P) == 11,
            "centreConcurrencyRelationProfile": dict(pair_rel),
            "centreConcurrencySetIntersection": len(C & P),
            "omittedFourthPencilLineByCentre": {str(k): v for k, v in sorted(omitted.items())},
            "distinctOmittedPencilLines": len(set(omitted_values)),
            "omittedLineMultiplicityProfile": dict(sorted(collections.Counter(collections.Counter(omitted_values).values()).items())),
            "oversizedShadowLines": sorted(oversized),
            "omittedOccurrencesThatAreOversized": sum(v in oversized for v in omitted_values),
            "distinctOmittedLinesThatAreOversized": len(set(omitted_values) & oversized),
            "omittedLineSetEqualsOversizedLineSet": set(omitted_values) == oversized,
        }

    rowC = set(axes["row"]["blockerCentres"])
    rowP = set(axes["row"]["pencilConcurrencyPoints"])
    colC = set(axes["col"]["blockerCentres"])
    colP = set(axes["col"]["pencilConcurrencyPoints"])
    sym = tuple(datum["symmetry"]["element"])

    named_sets = {"rowC": rowC, "rowP": rowP, "colC": colC, "colP": colP}
    cross = {}
    for a, b in itertools.combinations(named_sets, 2):
        A, B = named_sets[a], named_sets[b]
        cross[f"{a}_{b}"] = {
            "equal": A == B,
            "intersection": len(A & B),
        }

    symmetry = {}
    for name, S in named_sets.items():
        inv = {sym[x] for x in S} == S
        symmetry[name] = {
            "invariant": inv,
            "cycleShape": cycle_shape_on_subset(sym, S) if inv else None,
        }

    out = {
        "schema": "holotrade.w33-defect115-centre-concurrency.v2",
        "valid": True,
        "witnessLeaves": 115,
        "defectAboveShadowFloor": 5,
        "axes": axes,
        "crossSetComparisons": cross,
        "storedOrderSixSymmetry": symmetry,
        "theorem": (
            "For the stored 115-leaf W33^2 blocker, each axis has eleven blocker "
            "centres c with three minimum-shadow domain lines per centre.  Those three "
            "domain lines are concurrent at a uniquely computed point p(c), which is "
            "kept distinct from c.  The certificate records the exact c->p incidence, "
            "whether either eleven-point set is itself a minimum blocker, and how the "
            "omitted fourth lines of the p(c) pencils meet the seven oversized shadows."
        ),
        "boundary": (
            "This corrects the stronger false assumption p(c)=c.  It is an exact audit "
            "of one certified 115-leaf witness; it does not classify all defect blockers "
            "or change the certified tau_2 interval."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "valid": True,
        "rowCBlocker": axes["row"]["centreSet"]["isMinimumBlocker"],
        "rowPBlocker": axes["row"]["concurrencySet"]["isMinimumBlocker"],
        "colCBlocker": axes["col"]["centreSet"]["isMinimumBlocker"],
        "colPBlocker": axes["col"]["concurrencySet"]["isMinimumBlocker"],
        "rowMapImage": axes["row"]["mapImageSize"],
        "colMapImage": axes["col"]["mapImageSize"],
        "rowRelation": axes["row"]["centreConcurrencyRelationProfile"],
        "colRelation": axes["col"]["centreConcurrencyRelationProfile"],
        "cross": cross,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
