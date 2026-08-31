#!/usr/bin/env python3
"""
The load-balance spectrum: perfectly balanced measurement schedules exist at
every level except the two extremes, and the extremes fail exactly for odd q.

THE OBJECT.  An m-ovoid of W(3,q) is a set of Pauli observables meeting EVERY
measurement context in exactly m of them -- a perfectly load-balanced
schedule, every setting seeing the same number of your observables. The load
level m runs from 1 to q, since a context holds q+1 points and m = 0 or q+1
are trivial.

The two extremes are exactly the objects this repository has been chasing:

    m = 1   an OVOID -- one observable per context. This is certification,
            and perfect_context_transversal_classification.py showed it exists
            iff q is even (Thas).
    m = q   its COMPLEMENT, which exists exactly when the ovoid does, since
            complementation sends an m-ovoid to a (q+1-m)-ovoid.

The natural question is what happens in between, and the answer is that
nothing else ever fails.

THE SPECTRUM, computed here:

    q = 2   m=1: 6      m=2: 6                                  all levels
    q = 3   m=1: NONE   m=2: 432    m=3: NONE                   middle only
    q = 4   m=1: 120    m=2: many   m=3: many   m=4: 120        all levels
    q = 5   m=1: NONE   m=2: many   m=3: many   m=4: many
            m=5: NONE                                           all but ends

So the rule across everything tested:

    an m-ovoid of W(3,q) exists for every m in {1..q} when q is EVEN,
    and for every m in {2..q-1} when q is ODD.

The only obstructed load levels are the two extremes, and only for odd q.
Every intermediate level is available at every q.

WHY q = 3 LOOKED SPECIAL AND IS NOT.  At q = 3 the only surviving level is
m = 2, which is the hemisystem (q+1)/2, and it is tempting to read that as
"odd q admits only the hemisystem". q = 5 refutes it: m = 2, 3 and 4 all
exist there. q = 3 is simply the smallest odd case, where removing the two
extremes from {1,2,3} leaves exactly the middle. The hemisystem is not
privileged; it is what is left when the range is short enough.

THE COMPLEMENTATION CHECK, which every row passes. Complementation maps an
m-ovoid to a (q+1-m)-ovoid, so existence must be symmetric under
m -> q+1-m. Pairing the rows: q=2 (1,2) both exist; q=3 (1,3) both fail and
(2,2) exists; q=4 (1,4) and (2,3) both exist; q=5 (1,5) both fail while (2,4)
and (3,3) exist. Perfectly symmetric, which is a real check on the
computation rather than a restatement of it.

WHAT IT UNIFIES.  Every certification result in this repository is the m = 1
edge of this spectrum -- and that edge, with its mirror, is the ONLY place the
spectrum is ever obstructed. Load-balancing a measurement schedule is always
possible; insisting on exactly ONE observable per context is what is hard, and
only in odd local dimension.

PRIOR ART AND SCOPE.  The W(3,3) row is already ours:
analysis/w33_shape_catalogue.js records m-ovoids of W(3,3) at set size 20 and
nowhere else, with 432 of them, which this reproduces exactly. m-ovoids of
generalized quadrangles are a studied topic in finite geometry. What is
computed here is the spectrum across q = 2, 3, 4, 5 with the measurement
reading; the pattern is verified at those four values and is NOT proved as a
family. Counts marked "many" hit an enumeration cap and are lower bounds.
"""

import itertools
import json
import os
import sys

try:
    from ortools.sat.python import cp_model
except ImportError:
    sys.exit("needs ortools:  py -3 -m pip install ortools")

ROOT = r"C:\Repos\Holotrade"


def gf(q):
    if q in (2, 3, 5, 7):
        els = list(range(q))
        return (els, [[(a + b) % q for b in els] for a in els],
                [[(a * b) % q for b in els] for a in els])
    if q == 4:
        return ([0, 1, 2, 3],
                [[0, 1, 2, 3], [1, 0, 3, 2], [2, 3, 0, 1], [3, 2, 1, 0]],
                [[0, 0, 0, 0], [0, 1, 2, 3], [0, 2, 3, 1], [0, 3, 1, 2]])
    raise ValueError(q)


def build(q):
    els, add, mul = gf(q)
    inv = {a: next(b for b in els if mul[a][b] == 1) for a in els if a}

    def nm(v):
        i = next(k for k, x in enumerate(v) if x != 0)
        return tuple(mul[inv[v[i]]][x] for x in v)

    def form(u, v):
        a, b = mul[u[0]][v[1]], mul[u[1]][v[0]]
        c, d = mul[u[2]][v[3]], mul[u[3]][v[2]]
        return (a ^ b ^ c ^ d) if q % 2 == 0 else (a - b + c - d) % q

    pts = sorted({nm(v) for v in itertools.product(els, repeat=4) if any(v)})
    idx = {p: i for i, p in enumerate(pts)}
    lines = set()
    for a, b in itertools.combinations(range(len(pts)), 2):
        if form(pts[a], pts[b]) != 0:
            continue
        S = set()
        for x in els:
            for y in els:
                if x == 0 and y == 0:
                    continue
                w = tuple(add[mul[x][pts[a][k]]][mul[y][pts[b][k]]]
                          for k in range(4))
                if any(w):
                    S.add(idx[nm(w)])
        if len(S) == q + 1:
            lines.add(tuple(sorted(S)))
    return len(pts), sorted(lines)


def spectrum(q, budget, cap):
    N, lines = build(q)
    rows = []
    for m in range(1, q + 1):
        mm = cp_model.CpModel()
        x = [mm.NewBoolVar("") for _ in range(N)]
        for L in lines:
            mm.Add(sum(x[p] for p in L) == m)
        state = {"k": 0}

        class C(cp_model.CpSolverSolutionCallback):
            def on_solution_callback(self):
                state["k"] += 1
                if state["k"] >= cap:
                    self.StopSearch()

        s = cp_model.CpSolver()
        s.parameters.enumerate_all_solutions = True
        s.parameters.num_search_workers = 1
        s.parameters.max_time_in_seconds = budget
        st = s.Solve(mm, C())
        rows.append({
            "m": m, "size": m * (q * q + 1), "status": s.StatusName(st),
            "count": state["k"], "countIsCapped": state["k"] >= cap,
            "exists": state["k"] > 0,
            "isExtreme": m == 1 or m == q,
            "isHemisystem": 2 * m == q + 1,
        })
    return N, len(lines), rows


def main():
    print("THE LOAD-BALANCE SPECTRUM")
    print("=" * 72)
    print("  An m-ovoid meets EVERY context in exactly m observables -- a")
    print("  perfectly load-balanced schedule. m = 1 is certification (an")
    print("  ovoid), m = q is its complement.")
    print()
    out = []
    for q, budget, cap in ((2, 60.0, 3000), (3, 180.0, 3000),
                           (4, 420.0, 3000), (5, 900.0, 2000)):
        N, nl, rows = spectrum(q, budget, cap)
        print("  W(3,%d): %d Paulis, %d contexts of %d" % (q, N, nl, q + 1))
        for r in rows:
            tag = (" <- certification" if r["m"] == 1 else
                   " <- complement" if r["m"] == q else
                   " <- hemisystem" if r["isHemisystem"] else "")
            print("     m=%d size %4d  %-11s count %s%s"
                  % (r["m"], r["size"], r["status"],
                     (">=%d" % r["count"]) if r["countIsCapped"]
                     else r["count"], tag))
        # complementation must pair m with q+1-m
        ex = {r["m"]: r["exists"] for r in rows}
        sym = all(ex[m] == ex[q + 1 - m] for m in range(1, q + 1))
        extremes_fail = (not ex[1]) and (not ex[q])
        middles_all = all(ex[m] for m in range(2, q))
        print("     complementation symmetric (m <-> q+1-m): %s | extremes "
              "fail: %s | all intermediate exist: %s"
              % (sym, extremes_fail, middles_all))
        out.append({"q": q, "pauliClasses": N, "contexts": nl, "rows": rows,
                    "complementationSymmetric": sym,
                    "extremesFail": extremes_fail,
                    "allIntermediateExist": middles_all,
                    "qEven": q % 2 == 0})
        print()

    rule = all((o["extremesFail"] != o["qEven"]) and o["allIntermediateExist"]
               and o["complementationSymmetric"] for o in out)
    print("  RULE across everything tested: an m-ovoid exists for every m in")
    print("  1..q when q is EVEN, and for every m in 2..q-1 when q is ODD.")
    print("  Only the two extremes are ever obstructed: %s" % rule)
    print()
    print("  q = 3 looked like 'odd q admits only the hemisystem'. q = 5")
    print("  refutes that -- m = 2, 3 and 4 all exist there. q = 3 is just the")
    print("  smallest odd case, where dropping both ends of {1,2,3} leaves the")
    print("  middle. The hemisystem is not privileged; it is what is left.")

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data",
                         "load_balance_spectrum_only_extremes_fail.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.load-balance-spectrum.v1",
                "valid": bool(rule),
                "definition": ("an m-ovoid meets every measurement context in "
                               "exactly m observables: a perfectly "
                               "load-balanced schedule"),
                "rule": ("exists for every m in 1..q when q is even, and for "
                         "every m in 2..q-1 when q is odd; only the two "
                         "extremes are ever obstructed"),
                "extremesAre": ("m = 1 is certification (an ovoid, which "
                                "exists iff q is even, by Thas) and m = q is "
                                "its complement"),
                "spectra": out,
                "ruleHolds": bool(rule),
                "q3IsNotSpecial": ("at q = 3 only the hemisystem m = 2 "
                                   "survives, which looks like a rule for odd "
                                   "q; q = 5 refutes it with m = 2, 3 and 4 "
                                   "all existing. q = 3 is the smallest odd "
                                   "case, where dropping both ends of {1,2,3} "
                                   "leaves only the middle"),
                "unifies": ("every certification result here is the m = 1 edge "
                            "of this spectrum, and that edge with its mirror "
                            "is the only place the spectrum is obstructed"),
                "priorArt": ("the W(3,3) row is already ours -- "
                             "w33_shape_catalogue.js records m-ovoids of "
                             "W(3,3) at set size 20 and nowhere else, 432 of "
                             "them, reproduced exactly here; m-ovoids of "
                             "generalized quadrangles are a studied topic"),
                "boundary": ("verified at q = 2, 3, 4, 5 and NOT proved as a "
                             "family; counts marked capped are lower bounds"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if rule else 1


if __name__ == "__main__":
    sys.exit(main())
