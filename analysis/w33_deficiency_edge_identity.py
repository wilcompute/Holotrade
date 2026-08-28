#!/usr/bin/env python3
"""
An identity: the ovoid deficiency is bounded by the induced edge count.

The exact deficiency question at q=5 stalled -- CP-SAT returned UNKNOWN at
deficiencies 6, 7 and 8, even with a sound 156-fold line-transitive symmetry
break. So reformulate it rather than push harder.

THE IDENTITY.  Let S be a set of points of W(3,q) with |S| = q^2 + 1, let
r = N^T chi_S be its line profile, and let f = r - 1.  Every point lies on
q+1 lines, so sum r = (q+1)|S| = (q+1)(q^2+1), which is exactly the number of
lines; hence sum f = 0.  For the norm,

    ||f||^2 = sum r_i^2 - #lines
            = chi_S^T (N N^T) chi_S - #lines
            = (q+1)|S| + 2 e(S) - #lines
            = 2 e(S),

where e(S) is the number of COLLINEAR PAIRS inside S, because
N N^T = (q+1) I + A on points.

Now let d be the deficiency, the number of missed lines. A missed line has
r_i = 0, so f_i = -1, and sum f = 0 forces the positive part to total d.
Therefore

    2 e(S) = ||f||^2 = d * 1 + sum_{f_i > 0} f_i^2
                     >= d + sum_{f_i > 0} f_i  =  d + d  =  2d,

so

    d <= e(S),   with equality exactly when every line is met 0, 1 or 2 times.

The deficiency of a set is bounded by its internal collinear pairs, and the
two coincide precisely for the "profile in {0,1,2}" configurations.

WHY THIS IS THE RIGHT REFORMULATION.  Minimising induced edges is a different
optimisation from minimising deficiency, and CP-SAT handles it far better --
at q = 3 it closes:

    q = 3 : minimum induced edges in a 10-set = 3, OPTIMAL with a matching
            bound. The minimiser has profile {0:3, 1:34, 2:3}, so d = e = 3,
            and def(3) = 3 is recovered from the edge side.
    q = 5 : a 26-set with e = 12 exists, profile {0:12, 1:132, 2:12}, so
            d = e = 12 there too, giving def(5) <= 12.

WHAT IT DOES AND DOES NOT GIVE.  Since d <= e(S) for every S,
def(q) <= min_S e(S): the edge minimum is an UPPER bound on the deficiency.
It is not a lower bound, because a set with some line met three or more times
can have d strictly below e. So this reformulation can improve the upper end
and cannot by itself close the lower end.

It also explains why 12 keeps recurring at q = 5: it is the smallest induced
edge count found for a 26-set, and the corresponding configuration is exactly
of the equality type, so its deficiency equals it.

A SPECTRAL NOTE, since it is the obvious thing to try next and it fails. The
standard eigenvalue bound on induced edges says the average internal degree of
an m-set is at least k*m/n + s*(1 - m/n) with s the least eigenvalue. For
W(3,5): n = 156, k = 30, s = -6, m = 26 gives 30*26/156 - 6*(130/156) = 5 - 5
= 0. It degenerates to e >= 0 and says nothing -- which is not an accident:
m = 26 is exactly the Hoffman ratio bound, so the inequality is tight there by
construction. Any useful lower bound on e must come from alpha = 18 < 26, not
from the spectrum.
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
    return len(pts), [list(x) for x in sorted(lines)]


def adjacency(n, lines):
    adj = [[False] * n for _ in range(n)]
    for L in lines:
        for a, b in itertools.combinations(L, 2):
            adj[a][b] = adj[b][a] = True
    return adj


def min_edges(q, seconds):
    n, lines = geometry(q)
    adj = adjacency(n, lines)
    size = q * q + 1
    m = cp_model.CpModel()
    x = [m.NewBoolVar("") for _ in range(n)]
    ev = []
    for a, b in itertools.combinations(range(n), 2):
        if adj[a][b]:
            e = m.NewBoolVar("")
            m.AddBoolOr([x[a].Not(), x[b].Not(), e])
            m.Add(e <= x[a])
            m.Add(e <= x[b])
            ev.append(e)
    m.Add(sum(x) == size)
    m.Minimize(sum(ev))
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = float(seconds)
    s.parameters.num_search_workers = 8
    st = s.Solve(m)
    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None
    S = [i for i in range(n) if s.Value(x[i])]
    e = sum(1 for a, b in itertools.combinations(S, 2) if adj[a][b])
    prof = dict(sorted(collections.Counter(
        len(set(L) & set(S)) for L in lines).items()))
    # verify the identity on this witness, from scratch
    total = sum(k * v for k, v in prof.items())
    return {
        "q": q, "points": n, "lines": len(lines), "setSize": size,
        "minEdges": int(s.ObjectiveValue()),
        "bound": int(s.BestObjectiveBound()),
        "status": s.StatusName(st),
        "proved": s.StatusName(st) == "OPTIMAL",
        "witnessEdges": e, "profile": {str(k): v for k, v in prof.items()},
        "deficiency": prof.get(0, 0),
        "profileTotal": total,
        "countingIdentityHolds": total == (q + 1) * size,
        "normIdentityHolds": sum((k - 1) ** 2 * v for k, v in prof.items()) == 2 * e,
        "dAtMostE": prof.get(0, 0) <= e,
        "equalityCase": max(prof) <= 2,
    }


def main():
    seconds = (float(sys.argv[sys.argv.index("--seconds") + 1])
               if "--seconds" in sys.argv else 60.0)
    print("THE DEFICIENCY / INDUCED-EDGE IDENTITY")
    print("=" * 70)
    print("  ||f||^2 = 2 e(S)  and  sum f = 0  give  d <= e(S),")
    print("  with equality exactly when every line is met 0, 1 or 2 times.")
    print()
    rows = []
    for q in (3, 5):
        r = min_edges(q, seconds if q > 3 else 45)
        rows.append(r)
        print("  q=%d: minimum induced edges in a %d-set = %s  (bound %s, %s)"
              % (r["q"], r["setSize"], r["minEdges"], r["bound"], r["status"]))
        print("       witness: e=%d, profile %s, deficiency %d"
              % (r["witnessEdges"], r["profile"], r["deficiency"]))
        print("       ||f||^2 = 2e checks: %s   d <= e: %s   equality case: %s"
              % (r["normIdentityHolds"], r["dAtMostE"], r["equalityCase"]))
        print("       => def(%d) <= %d" % (r["q"], r["deficiency"]))
        print()

    ok = all(r["normIdentityHolds"] and r["dAtMostE"]
             and r["countingIdentityHolds"] for r in rows)
    print("  The identity holds on every witness. Minimising edges bounds the")
    print("  deficiency from ABOVE only, so this improves the upper end and")
    print("  cannot close the lower end on its own.")

    if "--write" in sys.argv:
        out = os.path.join(ROOT, "data", "w33_deficiency_edge_identity.json")
        with open(out, "w") as fh:
            json.dump({
                "schema": "holotrade.w33-deficiency-edge-identity.v1",
                "valid": ok,
                "identity": ("for |S| = q^2+1, ||N^T chi_S - 1||^2 = 2 e(S) and "
                             "the sum is zero, hence d <= e(S) with equality "
                             "iff every line is met 0, 1 or 2 times"),
                "derivation": ("N N^T = (q+1)I + A on points, so "
                               "sum r_i^2 = (q+1)|S| + 2e(S); subtracting the "
                               "line count leaves 2e(S). Missed lines "
                               "contribute -1 each and the positive part must "
                               "total d, so 2e >= 2d."),
                "instances": rows,
                "direction": ("an UPPER bound on the deficiency: "
                              "def(q) <= min_S e(S). Not a lower bound, since "
                              "a line met three or more times lets d fall "
                              "strictly below e."),
                "whyTwelveRecurs": ("12 is the smallest induced edge count "
                                    "found for a 26-set, and that configuration "
                                    "is of the equality type, so its deficiency "
                                    "equals it"),
                "spectralNoteFails": ("the eigenvalue bound gives average "
                                      "internal degree >= k m/n + s(1 - m/n) = "
                                      "30*26/156 - 6*130/156 = 0 at q=5, so "
                                      "e >= 0 and nothing more; m = 26 is "
                                      "exactly the Hoffman bound, so the "
                                      "inequality is tight there by "
                                      "construction. A useful lower bound must "
                                      "come from alpha = 18 < 26."),
                "boundary": ("def(5) stays open in [6, 12]; this reformulation "
                             "does not close it."),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(out, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
