#!/usr/bin/env python3
"""
The ovoid deficiency of W(3,q), and a third carrier coincidence defused.

W(3,q) has no ovoid for odd q. This repository has measured that absence two
ways already -- the BLOCKING defect tau_1 - (q^2+1), which is 1 at q=3, and
the COCLIQUE deficit (q^2+1) - alpha, which is 3 at q=3 and 8 at q=5. Here is
a third, and arguably the most direct: take a set of exactly ovoid size and
ask how close it can come to meeting every line once.

THE COUNTING IDENTITY THAT MAKES IT ONE NUMBER.  For any set S of points,
each point lies on q+1 lines, so

    sum over lines L of |S cap L|  =  (q+1) |S|.

At |S| = q^2 + 1 that is (q+1)(q^2+1), which is exactly the number of lines of
W(3,q). So the total excess over "once per line" equals the number of lines
MISSED, always. Deficiency is a single well-defined number:

    def(q) = min over (q^2+1)-sets of the number of lines missed,

and def(q) = 0 would say an ovoid exists.

AT q = 3 THE ANSWER IS 3, and CP-SAT reports OPTIMAL. The optimal 10-set has
line profile {0: 3, 1: 34, 2: 3} -- it misses three lines, meets thirty-four
exactly once, and doubles on three, with missed and doubled balancing as the
identity requires. So W(3,3) comes within three lines of having an ovoid and
no closer.

THE COINCIDENCE, AND WHY IT IS NOT ONE.  The other track's Pass 10869-10876
lands on a ten-state carrier, P1(F9) isomorphic to Q^-(3,3), the elliptic
quadric in PG(3,3). Ten is exactly W(3,3)'s ovoid size, which invites the
reading that their carrier is a near-ovoid of our quadrangle.

It is not. Computing the elliptic quadric x0*x1 + x2^2 + x3^2 = 0 against the
standard symplectic form, its line profile is {0: 12, 1: 16, 2: 12}: it misses
TWELVE of the forty lines, four times the optimum of three. So the elliptic
quadric is a poor near-ovoid of W(3,3), and the match with their carrier is a
match of SIZE only -- both objects have q^2+1 = 10 elements because both are
governed by the same parameter, not because they are the same object.

That is the third such coincidence this session, after the nine-triple carrier
and the cyclotomic seven. All three were tested and all three failed. The
pattern in the failures is itself worth stating: at q = 3 the small numbers
(3, 5, 7, 10, 27, 40) recur across genuinely unrelated constructions because
there are not many small numbers, and a shared value is evidence of a shared
PARAMETER, not a shared object.

WHAT WOULD MAKE def(q) INTERESTING: whether it equals q. It does at q = 3,
where CP-SAT reports OPTIMAL with a matching bound.

At q = 5 the question is OPEN and must be reported that way. A 26-set missing
12 lines exists, so def(5) <= 12, but the solver's lower bound is still 0, so
nothing is proved. A first pass at this file read the feasible value 12 as
though it were the answer and concluded "deficiency is not q" -- that was
wrong, and it is the same over-claim this session has caught three times
already. A FEASIBLE status gives an upper bound and nothing else. Until the
q = 5 optimum is closed, def(q) = q is neither confirmed nor refuted, and the
artifact records "open", not "false".
"""

import collections
import itertools
import json
import os
import sys

try:
    from ortools.sat.python import cp_model
except ImportError:
    sys.exit("needs ortools:  py -3 -m pip install ortools")

ROOT = r"C:\Repos\Holotrade"


def geometry(q):
    """Points and totally isotropic lines of W(3,q)."""
    pts = []
    for v in itertools.product(range(q), repeat=4):
        if not any(v):
            continue
        i = next(k for k in range(4) if v[k])
        if v[i] != 1:
            continue
        pts.append(v)
    idx = {v: i for i, v in enumerate(pts)}

    def form(u, v):
        return (u[0] * v[1] - u[1] * v[0] + u[2] * v[3] - u[3] * v[2]) % q

    lines = set()
    for a, b in itertools.combinations(pts, 2):
        if form(a, b) == 0:
            span = set()
            for s in range(q):
                for t in range(q):
                    if s == 0 and t == 0:
                        continue
                    w = tuple((s * a[k] + t * b[k]) % q for k in range(4))
                    i = next((k for k in range(4) if w[k]), None)
                    if i is None:
                        continue
                    inv = pow(w[i], q - 2, q)
                    span.add(tuple((w[k] * inv) % q for k in range(4)))
            if len(span) == q + 1:
                lines.add(tuple(sorted(idx[x] for x in span)))
    return pts, [list(x) for x in sorted(lines)]


def profile(S, lines):
    return dict(sorted(collections.Counter(
        len(set(L) & set(S)) for L in lines).items()))


def deficiency(q, pts, lines, seconds):
    n, size = len(pts), q * q + 1
    m = cp_model.CpModel()
    x = [m.NewBoolVar("") for _ in range(n)]
    miss = [m.NewBoolVar("") for _ in lines]
    for li, L in enumerate(lines):
        m.Add(sum(x[p] for p in L) >= 1).OnlyEnforceIf(miss[li].Not())
        m.Add(sum(x[p] for p in L) == 0).OnlyEnforceIf(miss[li])
    m.Add(sum(x) == size)
    m.Minimize(sum(miss))
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = float(seconds)
    s.parameters.num_search_workers = 8
    st = s.Solve(m)
    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None, None, s.StatusName(st), None
    S = [i for i in range(n) if s.Value(x[i])]
    return (int(s.ObjectiveValue()), int(s.BestObjectiveBound()),
            s.StatusName(st), profile(S, lines))


def main():
    seconds = (float(sys.argv[sys.argv.index("--seconds") + 1])
               if "--seconds" in sys.argv else 900.0)
    qs = [3, 5] if "--q5" in sys.argv else [3]

    print("THE OVOID DEFICIENCY OF W(3,q)")
    print("=" * 70)
    print("  sum_L |S cap L| = (q+1)|S|, and at |S| = q^2+1 that equals the")
    print("  number of lines -- so missed lines and total excess coincide,")
    print("  and deficiency is one well-defined number. Zero means an ovoid.")
    print()

    rows = []
    for q in qs:
        pts, lines = geometry(q)
        val, bound, status, prof = deficiency(q, pts, lines,
                                              seconds if q > 3 else 60)
        print("  q=%d : %d points, %d lines, set size %d"
              % (q, len(pts), len(lines), q * q + 1))
        print("        deficiency = %s   (bound %s, %s)" % (val, bound, status))
        print("        optimal profile: %s" % prof)
        proved = status == "OPTIMAL"
        verdict = ("equals q" if (proved and val == q)
                   else "differs from q" if proved
                   else "UNPROVED -- feasible only, so this is an upper bound")
        print("        equals q? %s" % verdict)
        rows.append({"q": q, "points": len(pts), "lines": len(lines),
                     "setSize": q * q + 1, "deficiency": val,
                     "bound": bound, "status": status,
                     "profile": {str(k): v for k, v in (prof or {}).items()},
                     "proved": status == "OPTIMAL",
                     "upperBoundOnly": status == "FEASIBLE",
                     "equalsQ": (val == q) if status == "OPTIMAL" else None})
        print()

    # the elliptic quadric, i.e. the other track's P1(F9) ten-state carrier
    pts3, lines3 = geometry(3)
    Q = [i for i, v in enumerate(pts3)
         if (v[0] * v[1] + v[2] * v[2] + v[3] * v[3]) % 3 == 0]
    qprof = profile(Q, lines3)
    qmiss = qprof.get(0, 0)
    opt3 = rows[0]["deficiency"]
    print("  THE TEN-STATE CARRIER COINCIDENCE")
    print("  " + "-" * 62)
    print("  Q^-(3,3) = P1(F9), the elliptic quadric: %d points" % len(Q))
    print("    line profile %s -> misses %d lines" % (qprof, qmiss))
    print("    the optimum is %d, so it is %.0fx worse"
          % (opt3, qmiss / opt3 if opt3 else 0))
    print("    => a match of SIZE only. Both are q^2+1 because both are")
    print("       governed by the same parameter, not because they are the")
    print("       same object.")

    ok = (rows[0]["deficiency"] == 3 and rows[0]["status"] == "OPTIMAL"
          and len(Q) == 10 and qmiss == 12)

    if "--write" in sys.argv:
        out = os.path.join(ROOT, "data", "w33_ovoid_deficiency.json")
        with open(out, "w") as fh:
            json.dump({
                "schema": "holotrade.w33-ovoid-deficiency.v1",
                "valid": ok,
                "definition": ("fewest lines missed by a set of exactly ovoid "
                               "size q^2+1; zero iff an ovoid exists"),
                "countingIdentity": ("sum_L |S cap L| = (q+1)|S| = #lines at "
                                     "|S| = q^2+1, so missed lines equal total "
                                     "excess and deficiency is one number"),
                "instances": rows,
                "ellipticQuadric": {
                    "isTheirCarrier": "P1(F9) = Q^-(3,3), Pass10869-10876",
                    "size": len(Q),
                    "profile": {str(k): v for k, v in qprof.items()},
                    "linesMissed": qmiss,
                    "optimum": opt3,
                    "isNearOptimal": qmiss == opt3,
                    "verdict": ("a match of size only; the elliptic quadric is "
                                "a poor near-ovoid of W(3,3)"),
                },
                "deficiencyEqualsQ": ("holds at q=3 (proved); OPEN at q=5, "
                                      "where only an upper bound of 12 is "
                                      "known. Not claimed either way."),
                "thirdCoincidenceDefused": ("after the nine-triple carrier and "
                                            "the cyclotomic seven; a shared "
                                            "value is evidence of a shared "
                                            "parameter, not a shared object"),
                "boundary": ("deficiency is a new invariant of W(3,q); it is "
                             "not claimed to determine tau_2, which stays open "
                             "in [110, 115]"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(out, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
