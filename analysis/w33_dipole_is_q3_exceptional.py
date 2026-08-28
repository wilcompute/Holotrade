#!/usr/bin/env python3
"""
The defect-dipole shape is q=3 exceptional: proved infeasible at q=5.

WHAT THE OTHER TRACK PROVED.  Their W33 optimal near-ovoid theorem (commits
dd770350d / 7b71c98cb / 517614707, integrated here as
analysis/w33_ovoid_defect_dipole_integration.py) classifies the optimum this
repository had only computed. Our CP-SAT gave def(3) = 3 with line profile
{0:3, 1:34, 2:3}; they identified the SHAPE:

    the missed triple and the doubled triple are punctured line-pencils at
    two distinct collinear points, and their common line is singly hit,

with 2,880 optimal 10-sets, 480 defect patterns and 6 completions per
oriented collinear pair. That is a genuine advance on a number.

THE QUESTION IT RAISES, and it is sharp.  A pencil in W(3,q) has q+1 lines, so
a punctured pencil has q. At q=3 that is 3, which is exactly def(3). If the
dipole shape generalised, the deficiency would be q at every odd q -- and
"def(q) = q" would be a theorem rather than a q=3 observation.

There is a rival prediction. Lovasz theta of W(3,q) equals the Hoffman ratio
bound n(-s)/(k-s) = q^2+1 (the graph is vertex-transitive and strongly
regular), so theta - alpha is 10 - 7 = 3 at q=3 and 26 - 18 = 8 at q=5. The
two predictions AGREE at q=3, both giving 3, and DIVERGE at q=5: the dipole
says 5, theta - alpha says 8.

THE TEST, and it is cheap because the shape is rigid.  Aut(W(3,q)) is
flag-transitive, so one choice of a line M and two of its points x, y covers
every case up to symmetry. Imposing the dipole profile exactly -- zero on the
q lines through x other than M, two on the q lines through y other than M,
one on every other line -- turns a blind search over (q^2+1)-sets into a model
with a handful of constraints.

    q = 3:  FEASIBLE, profile {0:3, 1:34, 2:3}  -- reproduces their theorem
    q = 5:  INFEASIBLE

So the dipole shape does NOT generalise. Their theorem is q=3 exceptional, and
this is the obstruction. The arithmetic alone does not forbid it -- a profile
with 5 missed and 5 doubled sums to 0*5 + 1*146 + 2*5 = 156 = (q+1)|S|,
exactly as the counting identity requires -- so the failure is genuinely
combinatorial rather than a parity accident.

WHAT THIS DOES AND DOES NOT SETTLE.  It kills the dipole ROUTE to def(5) = 5;
it does not prove def(5) != 5, since some other shape could achieve it. def(5)
remains open in [1, 12]. What is now established is that whatever realises the
q=5 optimum, it is not the punctured-pencil dipole that realises the q=3 one.

That makes this the fourth q=3 pattern tested at q=5 this session, and the
fourth to fail there -- after alpha = Phi_6(q), the deficit = q reading of the
coclique defect, and the ten-state carrier. The prior is now well earned: q=3
is small enough that many unrelated structures coincide, and every one of them
has to be re-tested at the next prime before it counts as a pattern.
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


def dipole_test(q, seconds=60):
    """Is there a (q^2+1)-set whose defect is a punctured-pencil dipole?"""
    n, lines = geometry(q)
    size = q * q + 1
    thru = [[li for li, L in enumerate(lines) if p in L] for p in range(n)]
    # flag-transitivity: one line and two of its points cover every case
    mi = 0
    x, y = lines[mi][0], lines[mi][1]
    missed = [li for li in thru[x] if li != mi]
    doubled = [li for li in thru[y] if li != mi]
    assert len(missed) == q and len(doubled) == q, "a punctured pencil has q lines"

    # the counting identity must permit the profile, or infeasibility is trivial
    singles = len(lines) - len(missed) - len(doubled)
    total = 0 * len(missed) + 1 * singles + 2 * len(doubled)
    permitted = total == (q + 1) * size

    m = cp_model.CpModel()
    v = [m.NewBoolVar("") for _ in range(n)]
    for li, L in enumerate(lines):
        s = sum(v[p] for p in L)
        if li in missed:
            m.Add(s == 0)
        elif li in doubled:
            m.Add(s == 2)
        else:
            m.Add(s == 1)
    m.Add(sum(v) == size)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(seconds)
    solver.parameters.num_search_workers = 8
    st = solver.Solve(m)
    status = solver.StatusName(st)
    prof = None
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        S = [i for i in range(n) if solver.Value(v[i])]
        prof = dict(sorted(collections.Counter(
            len(set(L) & set(S)) for L in lines).items()))
    return {"q": q, "points": n, "lines": len(lines), "setSize": size,
            "puncturedPencilSize": len(missed),
            "countingIdentityPermits": permitted,
            "requiredTotal": (q + 1) * size, "profileTotal": total,
            "status": status, "feasible": prof is not None,
            "profile": {str(k): val for k, val in (prof or {}).items()}}


def main():
    print("IS THE DEFECT-DIPOLE SHAPE q=3 EXCEPTIONAL?")
    print("=" * 70)
    print("  their theorem: the missed and doubled triples are punctured")
    print("  line-pencils at two collinear points, common line singly hit.")
    print("  A punctured pencil has q lines, so the shape predicts def(q) = q.")
    print()
    print("  rival prediction: theta - alpha, where theta = Hoffman = q^2+1.")
    print("    q=3: 10 - 7 = 3      q=5: 26 - 18 = 8")
    print("  the two AGREE at q=3 and DIVERGE at q=5 (5 versus 8).")
    print()

    rows = [dipole_test(3, 45), dipole_test(5, 90)]
    for r in rows:
        print("  q=%d: %d points, dipole needs %d missed and %d doubled"
              % (r["q"], r["points"], r["puncturedPencilSize"], r["puncturedPencilSize"]))
        print("       counting identity permits it: %s  (%d = %d)"
              % (r["countingIdentityPermits"], r["profileTotal"],
                 r["requiredTotal"]))
        print("       %s   profile %s" % (r["status"], r["profile"]))
        print()

    ok = (rows[0]["feasible"] and not rows[1]["feasible"]
          and rows[1]["status"] == "INFEASIBLE"
          and all(r["countingIdentityPermits"] for r in rows))

    print("  ==> the shape realises the optimum at q=3 and is INFEASIBLE at")
    print("      q=5, though the counting identity permits it there. So the")
    print("      defect dipole is q=3 exceptional, and the failure is")
    print("      combinatorial rather than a parity accident.")
    print()
    print("      This kills the dipole ROUTE to def(5) = 5. It does not prove")
    print("      def(5) != 5 -- another shape could achieve it -- and def(5)")
    print("      stays open in [1, 12].")

    if "--write" in sys.argv:
        out = os.path.join(ROOT, "data", "w33_dipole_q3_exceptional.json")
        with open(out, "w") as fh:
            json.dump({
                "schema": "holotrade.w33-dipole-q3-exceptional.v1",
                "valid": ok,
                "theirTheorem": ("missed and doubled triples are punctured "
                                 "line-pencils at two distinct collinear "
                                 "points, common line singly hit"),
                "theirSource": ["dd770350d", "7b71c98cb", "517614707"],
                "shapePredicts": "def(q) = q, since a punctured pencil has q lines",
                "rivalPredicts": ("theta - alpha, with theta = Hoffman ratio "
                                  "bound = q^2+1; 3 at q=3, 8 at q=5"),
                "predictionsAgreeAtQ3": True,
                "instances": rows,
                "conclusion": ("the dipole shape is q=3 exceptional: feasible "
                               "at q=3, INFEASIBLE at q=5"),
                "notAParityAccident": ("the counting identity permits the "
                                       "profile at q=5, so the obstruction is "
                                       "combinatorial"),
                "whatItSettles": "kills the dipole route to def(5) = 5",
                "whatItDoesNotSettle": ("def(5) != 5 is NOT proved; another "
                                        "shape could achieve it. def(5) stays "
                                        "open in [1, 12]"),
                "fourthQ3PatternToFail": ("after alpha = Phi_6(q), the "
                                          "deficit = q reading, and the "
                                          "ten-state carrier"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(out, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
