#!/usr/bin/env python3
"""
The tight case's centre multiplicities as a pure Diophantine system -- and a
test of whether GQ(2,4) can be refuted with NONE of the structural lemmas.

WHY THIS FILE EXISTS.  The GQ(2,4) bound recorded in gq24_tight_obstruction.py
inherits W33-Theory's multiplicity trichotomy, generalised from their q=3
statement to arbitrary (s,t) by analogy. That inheritance was flagged there as
needing confirmation on their side. This file tries to remove the dependency:
the same conclusion, if it follows, should follow from an integer program
whose every constraint is derived here from scratch.

THE DERIVATION, with nothing assumed.  Let X be a depth-2 blocker of a
GQ(s,t) at the tight size, and write the tile trace T[L][M] = |X cap (L x M)|.

  1. Each B_L = {q : some (p,q) in X with p in L} is a blocking set, so
     |B_L| >= tau_1, and summing over lines,  sum_L |B_L| >= #lines * tau_1.

  2. sum_L |B_L| = sum_q |H_q| where H_q = {L : q in B_L}, and H_q is the set
     of lines meeting C_q = {p : (p,q) in X}, so |H_q| <= (t+1)|C_q| with
     equality iff C_q is independent. Hence #lines * tau_1 <= (t+1)|X|, and at
     the tight size |X| = #lines * tau_1 / (t+1) every inequality is an
     equality: EVERY B_L is a minimum blocker and EVERY C_q is independent.

  3. Column-wise, sum_L T[L][M] = sum_{q in M} |H_q| = (t+1) * sigma_M with
     sigma_M = sum_{q in M} |C_q|. The column shadow D_M is the union of those
     C_q, and the transposed form of step 2 gives |D_M| = tau_1, so
     sigma_M >= tau_1.

  4. T[L][M] >= 1 always, and equals 1 + [M doubled for L]. With m_p the
     number of lines whose row shadow doubles exactly the pencil of p,

         sum_L T[L][M] = #lines + sum_{p in M} m_p,

     so   sum_{p in M} m_p = (t+1)*sigma_M - #lines >= (t+1)*tau_1 - #lines.

  5. Summing 4 over all M and comparing with sum_p (t+1) m_p forces EQUALITY
     in every one of the #lines inequalities. So

         sum_{p in M} m_p = (t+1)*tau_1 - #lines   for EVERY line M,
         sum_p m_p        = #lines,                m_p >= 0 integers.

Step 4's identification of doubled tiles with pencils is the centre theorem,
verified here by exhaustive enumeration on the geometry itself -- not assumed.
Nothing else is inherited.

THE SYSTEM.

    W(3,3):   40 points, 40 lines of 4, tau_1 = 11, line sum 4*11 - 40 = 4.
              m = all-ones solves it.
    GQ(2,4):  27 points, 45 lines of 3, tau_1 = 10, line sum 5*10 - 45 = 5.
              The uniform value would be 5/3, not an integer -- but that alone
              proves nothing, so the integer program is solved exhaustively.

This docstring does not state the GQ(2,4) outcome, because the outcome is the
point of running it, and a docstring written before the computation is how a
result gets asserted rather than found.

A HUMAN-READABLE CERTIFICATE is searched for when infeasible: an integer
vector y on lines with (y^T N)_p == 0 mod d at every point while the right
side is not, which is a one-line mod-d refutation checkable by hand.
"""

import itertools
import json
import os
import sys
from fractions import Fraction

try:
    from ortools.sat.python import cp_model
except ImportError:
    sys.exit("needs ortools:  py -3 -m pip install ortools")

ROOT = r"C:\Repos\Holotrade"


def build_gq24():
    def Qf(v):
        return (v[0] * v[1] + v[2] * v[3]
                + v[4] * v[4] + v[4] * v[5] + v[5] * v[5]) % 2

    def Bf(u, v):
        return (Qf([u[i] ^ v[i] for i in range(6)]) ^ Qf(u) ^ Qf(v)) % 2

    pts = [v for v in itertools.product([0, 1], repeat=6)
           if any(v) and Qf(v) == 0]
    idx = {v: i for i, v in enumerate(pts)}
    lines = set()
    for a, b in itertools.combinations(pts, 2):
        if Bf(a, b) == 0:
            c = tuple(a[i] ^ b[i] for i in range(6))
            if any(c) and Qf(c) == 0:
                lines.add(tuple(sorted(idx[x] for x in (a, b, c))))
    return len(pts), [list(x) for x in sorted(lines)]


def build_w33():
    """W(3,3) from the symplectic form on F_3^4."""
    def sym(u, v):
        return (u[0] * v[1] - u[1] * v[0] + u[2] * v[3] - u[3] * v[2]) % 3

    def norm(v):
        return min(tuple((c * s) % 3 for c in v) for s in (1, 2))

    seen, pts = set(), []
    for v in itertools.product(range(3), repeat=4):
        if not any(v):
            continue
        k = norm(v)
        if k not in seen:
            seen.add(k)
            pts.append(k)
    idx = {p: i for i, p in enumerate(pts)}

    lines = set()
    for a, b in itertools.combinations(pts, 2):
        if sym(a, b) == 0:
            pt = set()
            for x in range(3):
                for y in range(3):
                    if x == 0 and y == 0:
                        continue
                    w = tuple((x * a[i] + y * b[i]) % 3 for i in range(4))
                    pt.add(idx[norm(w)])
            if len(pt) == 4:
                lines.add(tuple(sorted(pt)))
    return len(pts), [list(x) for x in sorted(lines)]


def solve_system(n, lines, line_sum, total):
    """All nonnegative integer m with every line summing to line_sum."""
    m = cp_model.CpModel()
    v = [m.NewIntVar(0, line_sum, "") for _ in range(n)]
    for L in lines:
        m.Add(sum(v[p] for p in L) == line_sum)
    m.Add(sum(v) == total)

    class C(cp_model.CpSolverSolutionCallback):
        def __init__(self, vv):
            super().__init__()
            self.v, self.sols, self.count = vv, [], 0

        def on_solution_callback(self):
            self.count += 1
            if len(self.sols) < 40:
                self.sols.append([self.Value(x) for x in self.v])
            if self.count >= 20000:
                self.StopSearch()

    s = cp_model.CpSolver()
    s.parameters.enumerate_all_solutions = True
    s.parameters.num_search_workers = 1
    s.parameters.max_time_in_seconds = 180.0
    cb = C(v)
    st = s.Solve(m, cb)
    return s.StatusName(st), cb.sols, cb.count


def mod_certificate(n, lines, line_sum, max_d=16):
    """Search small moduli for a one-line refutation of N m = line_sum * 1.

    A congruence certificate is a vector y on lines with (y^T N)_p == 0 mod d
    at every point p, while y . (line_sum * 1) != 0 mod d. Any such y refutes
    solvability over Z, hence over the nonnegative integers. Searched in the
    span of natural vectors: all-ones, and each point's pencil indicator.
    """
    out = []
    thru = [[li for li, L in enumerate(lines) if p in L] for p in range(n)]
    cands = {"allOnes": [1] * len(lines)}
    for p in range(n):
        y = [0] * len(lines)
        for li in thru[p]:
            y[li] = 1
        cands["pencil%d" % p] = y
    for d in range(2, max_d + 1):
        for name, y in cands.items():
            col = [sum(y[li] for li, L in enumerate(lines) if p in L) % d
                   for p in range(n)]
            rhs = (sum(y) * line_sum) % d
            if all(c == 0 for c in col) and rhs != 0:
                out.append({"modulus": d, "vector": name, "rhsResidue": rhs})
                if len(out) >= 4:
                    return out
    return out


def verify_centre_theorem(n, lines, tau1):
    """Exhaustively: is every minimum blocker's doubled-line set a pencil?"""
    by_pencil = {frozenset(li for li, L in enumerate(lines) if p in L): p
                 for p in range(n)}
    m = cp_model.CpModel()
    y = [m.NewBoolVar("") for _ in range(n)]
    for L in lines:
        m.AddBoolOr([y[p] for p in L])
    m.Add(sum(y) == tau1)

    class C(cp_model.CpSolverSolutionCallback):
        def __init__(self, vv):
            super().__init__()
            self.v, self.all = vv, []

        def on_solution_callback(self):
            self.all.append([i for i in range(n) if self.Value(self.v[i])])

    s = cp_model.CpSolver()
    s.parameters.enumerate_all_solutions = True
    s.parameters.num_search_workers = 1
    s.parameters.max_time_in_seconds = 240.0
    cb = C(y)
    st = s.Solve(m, cb)
    good = 0
    for b in cb.all:
        bs = set(b)
        dbl = frozenset(li for li, L in enumerate(lines)
                        if len(bs & set(L)) == 2)
        if dbl in by_pencil:
            good += 1
    return {"blockers": len(cb.all), "complete": s.StatusName(st) == "OPTIMAL",
            "allDoubledSetsArePencils": good == len(cb.all) and good > 0}


def main():
    print("CENTRE MULTIPLICITIES AS A DIOPHANTINE SYSTEM")
    print("=" * 70)
    print("  Derived from scratch: every B_L minimum, every C_q independent,")
    print("  doubled tiles are pencils, and the column count forces")
    print("      sum_{p in M} m_p = (t+1)*tau_1 - #lines   for every line M,")
    print("      sum_p m_p = #lines,   m_p >= 0 integer.")
    print()

    cases = []
    for name, builder, s_, t_, tau1 in (
            ("W(3,3)", build_w33, 3, 3, 11),
            ("GQ(2,4)", build_gq24, 2, 4, 10)):
        n, lines = builder()
        nl = len(lines)
        ls = (t_ + 1) * tau1 - nl
        ct = verify_centre_theorem(n, lines, tau1)
        status, sols, count = solve_system(n, lines, ls, nl)
        uniform = Fraction(ls, s_ + 1)
        feasible = bool(sols)
        certs = [] if feasible else mod_certificate(n, lines, ls)
        cases.append({
            "name": name, "s": s_, "t": t_, "points": n, "lines": nl,
            "pointsPerLine": s_ + 1, "tau1": tau1,
            "tightSize": nl * tau1 // (t_ + 1),
            "lineSum": ls, "totalSum": nl,
            "uniformSolution": str(uniform),
            "uniformIsIntegral": uniform.denominator == 1,
            "centreTheoremVerified": ct,
            "status": status, "feasible": feasible,
            "solutionsCounted": count, "solutionsSampled": len(sols),
            "exampleSolution": sols[0] if sols else None,
            # checked directly, not looked for in a sample: m = 1 has every
            # line summing to s+1 and totals n, so it solves the system
            # exactly when those match the required line sum and total
            "allOnesIsASolution": bool(ls == s_ + 1 and nl == n),
            "modCertificates": certs,
        })
        print("  %s: %d points, %d lines of %d, tau_1 = %d, tight |X| = %d"
              % (name, n, nl, s_ + 1, tau1, nl * tau1 // (t_ + 1)))
        print("     centre theorem re-verified: %d blockers, complete %s, "
              "all doubled sets pencils %s"
              % (ct["blockers"], ct["complete"], ct["allDoubledSetsArePencils"]))
        print("     every line must sum to %d, total %d; uniform value %s (%s)"
              % (ls, nl, uniform,
                 "integral" if uniform.denominator == 1 else "NOT integral"))
        print("     integer program: %s, %d solutions found"
              % (status, count))
        if sols:
            print("     example m = %s%s"
                  % (sols[0][:14], " ..." if n > 14 else ""))
        for c in certs:
            print("     mod-%d certificate via %s: every column sum vanishes, "
                  "right side is %d" % (c["modulus"], c["vector"],
                                        c["rhsResidue"]))
        print()

    w33, gq = cases[0], cases[1]
    if w33["feasible"] and not gq["feasible"]:
        conclusion = ("the counting permits W(3,3) and forbids GQ(2,4): "
                      "tau_2(GQ(2,4)^2) != 90 with no borrowed lemma")
        print("  ==> W(3,3) FEASIBLE, GQ(2,4) INFEASIBLE.")
        print("      tau_2(GQ(2,4)^2) != 90 follows from this system alone,")
        print("      independent of the multiplicity trichotomy. And W(3,3)")
        print("      being feasible is exactly why it needed self-duality:")
        print("      the counting there permits the bijection.")
    elif w33["feasible"] and gq["feasible"]:
        conclusion = ("both systems are feasible, so the counting alone "
                      "settles neither and the GQ(2,4) bound keeps its "
                      "dependence on the trichotomy")
        print("  ==> BOTH FEASIBLE. The counting alone settles neither.")
        print("      The GQ(2,4) bound in gq24_tight_obstruction.py keeps its")
        print("      stated dependence on the multiplicity trichotomy; this")
        print("      file does NOT remove it. Recorded as a negative result,")
        print("      and it sharpens what the trichotomy is actually doing:")
        print("      it is not a counting fact.")
    else:
        conclusion = "unexpected combination; see the status fields"
        print("  ==> unexpected combination; see the artifact.")

    if "--write" in sys.argv:
        out = os.path.join(ROOT, "data", "gq24_centre_balance_diophantine.json")
        with open(out, "w") as fh:
            json.dump({
                "schema": "holotrade.gq24-centre-balance-diophantine.v1",
                "valid": True,
                "system": ("m_p >= 0 integers with sum_{p in M} m_p = "
                           "(t+1)*tau_1 - #lines for every line M and "
                           "sum_p m_p = #lines"),
                "derivedNotAssumed": [
                    "every row shadow is a minimum blocker (tightness)",
                    "every column class C_q is independent (tightness)",
                    "sigma_M >= tau_1 from the column shadow",
                    "equality in all #lines column inequalities from the total",
                ],
                "inherited": ("only the centre theorem -- doubled tiles are "
                              "pencils -- and it is re-verified here by "
                              "exhaustive enumeration on each geometry"),
                "cases": cases,
                "conclusion": conclusion,
                "boundary": ("this decides the COUNTING layer only. A feasible "
                             "system does not produce a blocker, and an "
                             "infeasible one refutes the tight case outright."),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(out, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
