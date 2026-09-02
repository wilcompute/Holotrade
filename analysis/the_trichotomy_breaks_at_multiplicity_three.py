#!/usr/bin/env python3
"""
The 110 proof does not lift, and now we know exactly where it snaps: the
trichotomy's geometric half survives defect untouched and its arithmetic half
fails immediately, at multiplicity three.

THE QUESTION.  f445379 ended by naming the real open item: the multiplicity
trichotomy m_p in {0, 1, t+1} is derived from pencil reciprocity, reciprocity
from tightness, and slack removes tightness -- so does the trichotomy survive
defect? It is a geometry question and it is answerable, because a real object
in the defect regime already exists: the stored 115-leaf witness, at r = 5.

Measured on it, and both axes agree exactly.

    row shadows   sizes {11: 33, 12: 4, 13: 3}     33 minimum blockers
    col shadows   sizes {11: 33, 12: 3, 13: 3, 14: 1}   33 minimum blockers
    conservation  F = 10, D = 10, F + D = 20 = 4r      holds

  GEOMETRIC HALF -- SURVIVES.  All 33 colliding row-line pairs are CONCURRENT.
  Not one disjoint collision. Every fibre of the centre map is contained in a
  pencil. That half of the trichotomy needs no tightness at all.

  ARITHMETIC HALF -- FAILS, UNIFORMLY.  There are 11 distinct centres and
  every single fibre has multiplicity exactly THREE:

      multiplicities {3: 11},  11 x 3 = 33,  full pencils: 0.

  Three is neither 1 nor t+1 = 4. The trichotomy is violated by every fibre at
  once, on both axes, at the one intermediate value it forbids.

WHY THAT IS EXACTLY THE BARRIER.  The 110 argument needs m in {0, 1, t+1} to
run the counting |F| = 1 + kt/mu = 10 against alpha(W(3,3)) = 7, concluding
F empty, hence all multiplicities at most one, hence the centre maps are
bijections, hence a self-duality of W(3,3), which is impossible for odd q. At
r = 5, F IS empty -- there are no multiplicity-4 fibres -- and it buys nothing,
because the multiplicities are 3 rather than 1. The chain breaks at its second
link, not its last.

RECIPROCITY IS ONE-SIDED, and this is why. Over the 1,320 (L, M) pairs with a
defined centre, reciprocity holds 1,308 times and fails 12, and EVERY failure
is of one type: doubled but not predicted. Never the reverse. That is not luck.
The forward direction is unconditional --

    |X n (L x M)| = sum_{p in L} |X_p n M| >= |S_L n M| = 2 whenever c_L in M

needs no tightness, only that a minimum blocker doubles its centre's pencil.
Overlap can only ADD leaves to a tile, so it can manufacture spurious doubling
and never destroy real doubling. So the converse is the defect-limited
direction, bounded by the overlap D, and D = 10 here against 12 observed
failures on the row side alone -- the same order, as it must be.

AND THE BREAK IS CHEAP, which is the discouraging part. Eleven multiplicity-3
fibres fit inside a total defect budget of F + D = 20, so a fibre of
multiplicity three costs on the order of two units. At r = 1 the budget is 4,
which still admits one or two of them. So the failure is not a large-defect
phenomenon that vanishes near the bottom of the interval: it is available
immediately. That is a coherent explanation for eleven formulations returning
UNKNOWN rather than INFEASIBLE, at both ends of two intervals.

WHAT SURVIVES AND IS WORTH REUSING.  Two unconditional statements, neither
needing tightness:

  * c_L in M  =>  |X n (L x M)| >= 2, for any blocking set whatsoever;
  * fibres of the centre map are contained in pencils.

Any future attack should be built on those and must NOT assume m in {0,1,t+1}.

SCOPE.  One witness, at r = 5, measured not speculated. It establishes that the
trichotomy CAN fail under defect, which is what kills lifting the 110 proof
unchanged; it does not establish what the multiplicity distribution must be at
r = 1. The cheapness estimate is an order-of-magnitude reading of one object,
not a bound. tau_2 stays open in [111, 115].
"""

import collections
import itertools
import json
import os
import sys

ROOT = r"C:\Repos\Holotrade"
Q = 3
N = 40


def main():
    def nm(v):
        i = next(k for k, x in enumerate(v) if x % Q)
        z = pow(v[i] % Q, -1, Q)
        return tuple((z * x) % Q for x in v)

    def form(u, v):
        return (u[0] * v[1] - u[1] * v[0] + u[2] * v[3] - u[3] * v[2]) % Q

    pts = sorted({nm(v) for v in itertools.product(range(Q), repeat=4)
                  if any(v)})
    idx = {v: i for i, v in enumerate(pts)}
    lines = set()
    for a, b in itertools.combinations(range(N), 2):
        if form(pts[a], pts[b]):
            continue
        S = set()
        for x in range(Q):
            for y in range(Q):
                if x == y == 0:
                    continue
                S.add(idx[nm(tuple((x * pts[a][k] + y * pts[b][k]) % Q
                                   for k in range(4)))])
        if len(S) == 4:
            lines.add(tuple(sorted(S)))
    lines = sorted(lines)
    LS = [set(L) for L in lines]
    thru = [[li for li, L in enumerate(lines) if p in L] for p in range(N)]

    W = json.load(open(os.path.join(ROOT, "data",
                                    "tensor_symmetric_blocker.json")))["witness"]
    X = {(v // N, v % N) for v in W}
    r = len(X) - 110
    blocks = all(any((p, q) in X for p in L for q in M) for L in LS for M in LS)

    def centre(S):
        dbl = [li for li, L in enumerate(lines) if len(S & set(L)) == 2]
        for p in range(N):
            if set(dbl) == set(thru[p]):
                return p
        return None

    rows, cols = [], []
    for L in lines:
        S = set()
        for p in L:
            S |= {q for (a, q) in X if a == p}
        rows.append((S, centre(S) if len(S) == 11 else None))
    for M in lines:
        T = set()
        for q in M:
            T |= {p for (p, b) in X if b == q}
        cols.append((T, centre(T) if len(T) == 11 else None))

    print("THE TRICHOTOMY BREAKS AT MULTIPLICITY THREE")
    print("=" * 72)
    print("  witness: %d leaves, r = %d, blocks all 1600 tiles: %s"
          % (len(X), r, blocks))
    F = sum(len(S) - 11 for S, _ in rows)
    D = sum(sum(len({q for (a, q) in X if a == p}) for p in L) - len(S)
            for L, (S, _) in zip(lines, rows))
    print("  conservation F + D = (t+1)r : %d + %d = %d = %d  %s"
          % (F, D, F + D, 4 * r, F + D == 4 * r))
    print()

    out = {}
    for tag, shad in (("row", rows), ("col", cols)):
        by = collections.defaultdict(list)
        for li, (S, c) in enumerate(shad):
            if c is not None:
                by[c].append(li)
        mult = collections.Counter(len(v) for v in by.values())
        inpencil = all(any(set(v) <= set(thru[p]) for p in range(N))
                       for v in by.values())
        disjoint = 0
        for c, ls in by.items():
            for a, b in itertools.combinations(ls, 2):
                if not (LS[a] & LS[b]):
                    disjoint += 1
        sizes = dict(collections.Counter(len(S) for S, _ in shad))
        out[tag] = {"shadowSizes": {str(k): v for k, v in sizes.items()},
                    "minimumShadows": sum(1 for S, _ in shad if len(S) == 11),
                    "distinctCentres": len(by),
                    "multiplicities": {str(k): v for k, v in mult.items()},
                    "everyFibreInAPencil": inpencil,
                    "disjointCollisions": disjoint,
                    "fullPencils": sum(1 for v in by.values() if len(v) == 4),
                    "trichotomyRespected": set(mult) <= {1, 4}}
        print("  %s: shadows %s ; %d minimum ; %d distinct centres"
              % (tag, sizes, out[tag]["minimumShadows"], len(by)))
        print("       multiplicities %s ; every fibre in a pencil: %s ;"
              % (dict(mult), inpencil))
        print("       disjoint collisions: %d ; full pencils: %d ;"
              " trichotomy {0,1,4} respected: %s"
              % (disjoint, out[tag]["fullPencils"],
                 out[tag]["trichotomyRespected"]))
    print()

    good = bad = 0
    modes = collections.Counter()
    for li, (S, c) in enumerate(rows):
        if c is None:
            continue
        for M in lines:
            two = sum(1 for p in lines[li] for q in M if (p, q) in X) >= 2
            pred = c in set(M)
            if two == pred:
                good += 1
            else:
                bad += 1
                modes[(two, pred)] += 1
    print("  reciprocity over %d defined (L,M) pairs: holds %d, fails %d"
          % (good + bad, good, bad))
    print("     failure modes (doubled, predicted): %s -- one-sided: %s"
          % (dict(modes), set(modes) <= {(True, False)}))
    print()
    print("  GEOMETRIC HALF SURVIVES: fibres are concurrent, always.")
    print("  ARITHMETIC HALF FAILS: every fibre has multiplicity 3, which is")
    print("  neither 1 nor t+1 = 4. The 110 chain breaks at its second link.")
    print("  And 11 such fibres fit in a budget of 20, so they cost about two")
    print("  units each -- available even at r = 1, where the budget is 4.")

    ok = (blocks and r == 5 and F + D == 4 * r
          and all(o["multiplicities"] == {"3": 11} for o in out.values())
          and all(o["everyFibreInAPencil"] for o in out.values())
          and all(o["disjointCollisions"] == 0 for o in out.values())
          and all(not o["trichotomyRespected"] for o in out.values())
          and set(modes) <= {(True, False)})

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data",
                         "the_trichotomy_breaks_at_multiplicity_three.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.trichotomy-breaks-at-three.v1",
                "valid": bool(ok),
                "question": ("f445379 asked whether the multiplicity trichotomy "
                             "survives defect, since it is derived from pencil "
                             "reciprocity and reciprocity from tightness"),
                "witness": {"leaves": len(X), "r": r, "blocksAllTiles": blocks,
                            "source": "tensor_symmetric_blocker.json"},
                "conservation": {"F": F, "D": D, "sum": F + D,
                                 "expected": 4 * r, "holds": F + D == 4 * r},
                "axes": out,
                "geometricHalfSurvives": ("every fibre of the centre map is "
                                          "contained in a pencil and there is "
                                          "not one disjoint collision, on "
                                          "either axis; this half needs no "
                                          "tightness"),
                "arithmeticHalfFails": ("there are 11 distinct centres on each "
                                        "axis and EVERY fibre has multiplicity "
                                        "exactly 3, which is neither 1 nor "
                                        "t+1 = 4 -- the trichotomy is violated "
                                        "by every fibre at once, at the "
                                        "intermediate value it forbids"),
                "whereTheProofSnaps": ("the 110 argument needs m in {0,1,t+1} "
                                       "to run |F| = 1 + kt/mu = 10 against "
                                       "alpha = 7, concluding F empty and all "
                                       "multiplicities at most one, hence "
                                       "bijections, hence a self-duality of "
                                       "W(3,3), impossible for odd q. At r = 5 "
                                       "F IS empty and buys nothing, because "
                                       "the multiplicities are 3. The chain "
                                       "breaks at its second link, not its "
                                       "last"),
                "reciprocityIsOneSided": {
                    "holds": good, "fails": bad,
                    "modes": {str(k): v for k, v in modes.items()},
                    "oneSided": set(modes) <= {(True, False)},
                    "why": ("|X n (L x M)| = sum_{p in L} |X_p n M| >= "
                            "|S_L n M| = 2 whenever c_L in M needs no "
                            "tightness, so overlap can manufacture spurious "
                            "doubling but never destroy real doubling; the "
                            "converse is the defect-limited direction, bounded "
                            "by the overlap D"),
                },
                "theBreakIsCheap": ("eleven multiplicity-3 fibres fit inside a "
                                    "total budget of F + D = 20, so such a "
                                    "fibre costs on the order of two units; at "
                                    "r = 1 the budget is 4, which still admits "
                                    "one or two, so the failure is available "
                                    "immediately rather than only at large "
                                    "defect -- a coherent explanation for "
                                    "eleven formulations returning UNKNOWN"),
                "whatSurvivesAndIsReusable": [
                    "c_L in M implies |X n (L x M)| >= 2, for ANY blocking set",
                    "fibres of the centre map are contained in pencils",
                ],
                "boundary": ("one witness at r = 5, measured not speculated; it "
                             "establishes that the trichotomy CAN fail under "
                             "defect, which is what kills lifting the 110 proof "
                             "unchanged, but not what the distribution must be "
                             "at r = 1. The cheapness estimate is an "
                             "order-of-magnitude reading of one object, not a "
                             "bound. tau_2 stays open in [111, 115]"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
