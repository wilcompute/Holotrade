#!/usr/bin/env python3
"""
Three defect witnesses under three symmetries. One structure survives, one
fails everywhere, and the prettiest finding turned out to be an artefact.

WHY THIS RUN EXISTS.  the_trichotomy_breaks_at_multiplicity_three.py measured
the defect regime on ONE object, the stored 115-leaf witness, and found
something striking on top of the trichotomy break: its 11 centres form a
MINIMUM BLOCKING SET of W(3,3) -- one of the 360 -- with the concurrency map
c -> z(c) a permutation of that same 11-set with three fixed points. Rows and
columns identical.

That witness is invariant under an order-6 element of Aut(W(3,3)). A structure
seen once, on a symmetric object, is not a structure. So: build blockers under
other symmetry classes and rerun the identical analysis.

    symmetry   |X|   r    min shadows   centres   multiplicities
    order 6    115    5        33          11        {3: 11}
    order 12   116    6        36          12        {3: 12}
    order  5   125   15        15          10        {1: 5, 2: 5}

WHAT SURVIVES -- the geometric half, in all three.

    fibres of the centre map contained in pencils:  True, True, True

Three witnesses, three symmetry classes, three different defects (5, 6, 15).
That is the one fact worth carrying forward, and it now has the variation
behind it that the single-witness version did not. It also needs no tightness
to prove, which is why it survives: two lines sharing a centre are forced to be
concurrent by the geometry, not by the counting.

WHAT FAILS EVERYWHERE -- the arithmetic half.

    multiplicities observed:  {3}, {3}, {1, 2}

Never the trichotomy's {0, 1, t+1} = {0, 1, 4}. Multiplicity 2 and 3 both
occur; multiplicity 4 -- a full pencil -- occurs in none of the three. So the
break found on one object is not an accident of that object: the trichotomy is
simply false in the defect regime, and it fails toward the intermediate values
rather than toward the extreme one the proof would have tolerated.

WHAT WAS AN ARTEFACT -- and this is the useful part of running it.

    centres form a blocking set:      True,  True,  False
    centres are a MINIMUM blocker:    True,  False, False

The self-referential structure held for the order-6 witness ALONE. The order-12
witness's 12 centres block but are not minimum; the order-5 witness's 10
centres do not block at all. Had it been reported from the single object it
would have been a false structure with a very persuasive shape -- 11 centres,
11 = tau_1, forming one of the 360, with a permutation on it. It is a property
of that witness's symmetry.

THE STANDING RULE THAT CAUGHT IT.  A combinatorial law with no exceptions on a
convenience sample is not a finding until the sample is varied. The sample here
was one object; varying it cost three CP-SAT runs and removed a wrong claim
before it was made.

WHAT A FUTURE ATTACK SHOULD ASSUME.  Exactly two things, both unconditional and
both now varied:

  * c_L in M  =>  |X n (L x M)| >= 2, for ANY blocking set;
  * fibres of the centre map are contained in pencils.

And nothing about multiplicities.

SCOPE.  Three witnesses, found by symmetry-restricted CP-SAT, so each is an
upper-bound construction and none is optimal in its class. The negative -- that
the centre-set structure is not general -- is established by exhibiting
counterexamples and is solid. The positive -- that fibres lie in pencils -- is
now three-for-three but still not a proof. tau_2 stays open in [111, 115].
"""

import collections
import itertools
import json
import os
import random
import sys

ROOT = r"C:\Repos\Holotrade"
Q = 3
N = 40


def main():
    from ortools.sat.python import cp_model

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

    e = [tuple(1 if k == i else 0 for k in range(4)) for i in range(4)]

    def is_sp(A):
        for i, j in itertools.combinations(range(4), 2):
            u = tuple(sum(A[r][k] * e[i][k] for k in range(4)) % Q
                      for r in range(4))
            v = tuple(sum(A[r][k] * e[j][k] for k in range(4)) % Q
                      for r in range(4))
            if form(u, v) != form(e[i], e[j]):
                return False
        return True

    def act(A, v):
        return nm(tuple(sum(A[i][k] * v[k] for k in range(4)) % Q
                        for i in range(4)))

    rng = random.Random(3)
    gens = []
    while len(gens) < 40:
        A = tuple(tuple(rng.randrange(Q) for _ in range(4))
                  for _ in range(4))
        if is_sp(A):
            gens.append(tuple(idx[act(A, pts[p])] for p in range(N)))

    def order(g):
        o, h = 1, g
        while h != tuple(range(N)):
            h = tuple(g[i] for i in h)
            o += 1
        return o

    def centre(S):
        dbl = [li for li, L in enumerate(lines) if len(S & set(L)) == 2]
        for p in range(N):
            if set(dbl) == set(thru[p]):
                return p
        return None

    def analyse(X, o):
        rows = []
        for L in lines:
            S = set()
            for p in L:
                S |= {q for (a, q) in X if a == p}
            rows.append((S, centre(S) if len(S) == 11 else None))
        by = collections.defaultdict(list)
        for li, (S, c) in enumerate(rows):
            if c is not None:
                by[c].append(li)
        C = sorted(by)
        mult = collections.Counter(len(v) for v in by.values())
        pen = all(any(set(v) <= set(thru[p]) for p in range(N))
                  for v in by.values())
        blk = bool(C) and all(set(L) & set(C) for L in lines)
        mn = False
        if blk and len(C) == 11:
            d = [li for li, L in enumerate(lines) if len(set(C) & set(L)) == 2]
            mn = any(set(d) == set(thru[p]) for p in range(N))
        return {"symmetryOrder": o, "leaves": len(X), "r": len(X) - 110,
                "minimumShadows": sum(1 for S, _ in rows if len(S) == 11),
                "centres": len(C),
                "multiplicities": {str(k): v for k, v in sorted(mult.items())},
                "fibresInPencils": pen, "centresBlock": blk,
                "centresAreMinimumBlocker": mn}

    print("THREE WITNESSES, AND WHAT SURVIVES VARIATION")
    print("=" * 72)
    rowsout, seen = [], set()
    for g in gens:
        o = order(g)
        if o in seen or o < 4 or o > 12:
            continue
        seen.add(o)
        mark = [False] * (N * N)
        orb = []
        for v in range(N * N):
            if mark[v]:
                continue
            cur, cyc = v, []
            while not mark[cur]:
                mark[cur] = True
                cyc.append(cur)
                cur = g[cur // N] * N + g[cur % N]
            orb.append(cyc)
        inorb = [0] * (N * N)
        for i, cyc in enumerate(orb):
            for v in cyc:
                inorb[v] = i
        m = cp_model.CpModel()
        y = [m.NewBoolVar("") for _ in orb]
        for L in lines:
            for M in lines:
                m.AddBoolOr([y[inorb[p * N + q]] for p in L for q in M])
        m.Minimize(sum(len(c) * y[i] for i, c in enumerate(orb)))
        s = cp_model.CpSolver()
        s.parameters.max_time_in_seconds = 300
        s.parameters.num_search_workers = 8
        st = s.Solve(m)
        if s.StatusName(st) not in ("OPTIMAL", "FEASIBLE"):
            continue
        X = {(v // N, v % N) for i, c in enumerate(orb) if s.Value(y[i])
             for v in c}
        if not all(any((p, q) in X for p in L for q in M)
                   for L in LS for M in LS):
            continue
        rowsout.append(analyse(X, o))
        if len(rowsout) >= 3:
            break
    rowsout.sort(key=lambda d: d["leaves"])

    print("  symmetry  |X|   r   minShadows  centres  multiplicities")
    for d in rowsout:
        print("  order %-3d %4d %4d %9d %8d   %s"
              % (d["symmetryOrder"], d["leaves"], d["r"],
                 d["minimumShadows"], d["centres"], d["multiplicities"]))
    print()
    pen = [d["fibresInPencils"] for d in rowsout]
    blk = [d["centresBlock"] for d in rowsout]
    mn = [d["centresAreMinimumBlocker"] for d in rowsout]
    print("  SURVIVES  fibres in pencils      : %s" % pen)
    print("  FAILS     trichotomy {0,1,4}     : %s"
          % [set(d["multiplicities"]) <= {"1", "4"} for d in rowsout])
    print("  ARTEFACT  centres block          : %s" % blk)
    print("  ARTEFACT  centres = MIN blocker  : %s" % mn)
    print()
    print("  The self-referential structure -- 11 centres forming one of the")
    print("  360, with a permutation on it -- held for the order-6 witness")
    print("  ALONE. Reported from one object it would have been a false")
    print("  finding with a very persuasive shape. Varying the sample cost")
    print("  three solver runs and removed it before it was claimed.")
    print()
    print("  A future attack may assume exactly two things, both unconditional")
    print("  and now varied: c_L in M => |X n (LxM)| >= 2 for ANY blocking")
    print("  set, and fibres of the centre map lie in pencils. Nothing about")
    print("  multiplicities.")

    ok = (len(rowsout) == 3 and all(pen)
          and not all(mn) and any(mn)
          and all(not (set(d["multiplicities"]) <= {"1", "4"})
                  for d in rowsout))

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data",
                         "three_witnesses_and_what_survives_variation.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.three-witnesses-variation.v1",
                "valid": bool(ok),
                "why": ("the_trichotomy_breaks_at_multiplicity_three.py "
                        "measured one object, the order-6-symmetric 115-leaf "
                        "witness, and found its 11 centres forming a MINIMUM "
                        "blocking set with the concurrency map a permutation "
                        "of them; a structure seen once on a symmetric object "
                        "is not a structure"),
                "witnesses": rowsout,
                "survives": {
                    "fact": "fibres of the centre map are contained in pencils",
                    "observed": pen,
                    "why": ("needs no tightness -- two lines sharing a centre "
                            "are forced concurrent by the geometry, not by the "
                            "counting"),
                },
                "failsEverywhere": {
                    "fact": "the trichotomy m in {0, 1, t+1} = {0, 1, 4}",
                    "multiplicitiesObserved": [d["multiplicities"]
                                               for d in rowsout],
                    "reading": ("multiplicity 2 and 3 both occur and "
                                "multiplicity 4 occurs in none, so the break is "
                                "not an accident of one object and it fails "
                                "toward the intermediate values rather than the "
                                "extreme one the proof would tolerate"),
                },
                "artefact": {
                    "claimAvoided": ("the centres form a minimum blocking set "
                                     "of W(3,3), with the concurrency map a "
                                     "permutation of them"),
                    "centresBlock": blk,
                    "centresAreMinimumBlocker": mn,
                    "heldFor": "the order-6 witness alone",
                    "reading": ("the order-12 witness's centres block but are "
                                "not minimum; the order-5 witness's do not "
                                "block at all"),
                },
                "standingRule": ("a combinatorial law with no exceptions on a "
                                 "convenience sample is not a finding until the "
                                 "sample is varied; varying it cost three "
                                 "solver runs and removed a wrong claim before "
                                 "it was made"),
                "whatToAssume": [
                    "c_L in M implies |X n (L x M)| >= 2, for ANY blocking set",
                    "fibres of the centre map are contained in pencils",
                ],
                "boundary": ("three witnesses from symmetry-restricted CP-SAT, "
                             "so each is an upper-bound construction and none "
                             "is optimal in its class; the negative is "
                             "established by counterexample and is solid, the "
                             "positive is three-for-three but still not a "
                             "proof. tau_2 stays open in [111, 115]"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
