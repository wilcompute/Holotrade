#!/usr/bin/env python3
"""
A theorem for every generalized quadrangle with t > s: the depth-2 tight case
is impossible. The borrowed lemma is replaced by a proof.

WHERE THIS CAME FROM.  W33-Theory proved tau_2(W(3,3)^2) != 110 by showing the
tight case forces a self-duality of W(3,3), impossible for odd q. Their
argument passes through a multiplicity trichotomy stated for q = 3. An earlier
file here, gq24_tight_obstruction.py, generalised that trichotomy to arbitrary
(s,t) BY ANALOGY and flagged the generalisation as needing confirmation.

This file removes the flag. The trichotomy is proved below for every GQ(s,t),
from pencil reciprocity and the quadrangle axioms alone, and the proof turns
out to be shorter than the analogy it replaces. With it, the tight case
resolves into exactly two branches, and for t > s one of them does not exist.

SETUP.  Let Q be a GQ(s,t): every line has s+1 points, every point lies on
t+1 lines, and there is no triangle. It has (s+1)(st+1) points and
(t+1)(st+1) lines. An ovoid is a point set meeting every line exactly once,
necessarily of size st+1. Let tau_1 be the blocking number and
delta = tau_1 - (st+1) the blocking-ovoid defect, so delta = 0 iff Q has an
ovoid.

A depth-2 blocker is X in points x points meeting every tile L x M. Write
B_L for the row shadow of L, C_q for the column class of q, and
T[L][M] = |X cap (L x M)|.

STEP 1 (tightness, derived).  B_L blocks every line, so |B_L| >= tau_1. Also
sum_L |B_L| = sum_q |H_q| with H_q = {L : L meets C_q}, and |H_q| <=
(t+1)|C_q| with equality iff C_q is independent. Hence

    #lines * tau_1 <= (t+1)|X|,   i.e.   |X| >= (st+1) * tau_1,

and at equality EVERY B_L is a minimum blocker and EVERY C_q is independent.
Transposing gives the same for columns. Call this size the TIGHT CASE.

STEP 2 (the centre property, verified not assumed).  Every minimum blocker
here meets the t+1 lines of a single pencil in delta+1 points and every other
line exactly once. Its excess is sum_M (|B cap M| - 1) = (t+1)tau_1 - #lines
= (t+1)delta, which is exactly (t+1) lines carrying delta each. The property
is CHECKED per geometry in this file -- exhaustively where enumeration
finishes, and otherwise by re-solving with a no-good cut after each hit. It is
an input, and the one input that is geometry-specific.

It is worth stressing that delta is NOT assumed to be 1. On Q^-(5,3) the
defect is 2 and every sampled minimum blocker meets one pencil in THREE points
and every other line once. Steps 3 to 6 never use the value of delta, which is
why the argument survives that.

Write c_L for the centre of B_L and d_M for the centre of the column shadow.

STEP 3 (reciprocity).  T[L][M] = |B_L cap M| is delta+1 when M is in the
pencil of c_L and 1 otherwise; transposing, it is delta+1 when d_M is on L.
So

    c_L in M  <=>  T[L][M] > 1  <=>  d_M in L.

STEP 4 (centre balance, delta drops out).  Summing T over L for fixed M,

    #lines + delta * #{L : c_L in M} = sum_L |B_L cap M|
                                     = sum_{q in M} |H_q|
                                     = (t+1) * sum_{q in M} |C_q|
                                     = (t+1) * tau_1,

using |D_M| = tau_1 and the disjointness that tightness forces. Therefore

    #{L : c_L in M} = ((t+1)tau_1 - #lines)/delta = t+1     for EVERY line M,

independent of delta. Equivalently, with m_p = #{L : c_L = p},

    sum_{p in M} m_p = t+1  for every line M,   sum_p m_p = #lines.

STEP 5 (THE TRICHOTOMY, proved here).  m_p is 0, 1 or t+1.

    Suppose c_L = c_L' = p for distinct lines L, L'. Reciprocity read the
    other way says {L : c_L in M} = {L : d_M in L} = pencil(d_M) for every
    line M. Take any M through p. Both L and L' have centre p in M, so both
    lie in pencil(d_M): both pass through d_M. Two distinct lines of a GQ meet
    in at most one point, so L cap L' = {d_M}, and since L, L' do not depend
    on M, the point x := d_M is THE SAME for all t+1 lines M through p.

    Now take ANY line L'' through x. For every M through p we have
    L'' in pencil(x) = pencil(d_M) = {L : c_L in M}, so c_L'' lies on M -- on
    every one of the t+1 lines through p. Distinct lines through p meet only
    at p (no triangles), so c_L'' = p.

    Hence as soon as m_p >= 2, every one of the t+1 lines through x has
    centre p, giving m_p = t+1 exactly.                                    []

STEP 6 (the two branches).  Each line has s+1 points, and by Step 4 its
multiplicities sum to t+1 with each in {0, 1, t+1}. Writing a for the number
of multiplicity-(t+1) points on the line and b for the multiplicity-1 points,
a(t+1) + b = t+1 with a + b <= s+1 leaves exactly two possibilities:

    (A)  a = 1, b = 0.   Every line carries exactly one point of multiplicity
         t+1. Let F be that set. Counting incidences, |F|(t+1) = #lines, so
         |F| = st+1, and F meets every line exactly once: F IS AN OVOID.

    (B)  a = 0, b = t+1.  Every line carries t+1 points of multiplicity 1,
         which requires t+1 <= s+1, i.e. t <= s.

THEOREM.  Let Q be a GQ(s,t) with no ovoid, satisfying the centre property of
Step 2. If t > s, then

        tau_2(Q x Q) > (st+1) * tau_1(Q).

    Proof. At the tight size Steps 1-5 apply. Branch (B) needs t <= s and is
    unavailable. Branch (A) produces an ovoid, and Q has none. []

WHAT IT EXPLAINS, and this is the part worth keeping.  W(3,3) has t = s = 3,
so branch (B) is open -- and branch (B) is precisely the bijection whose
refutation needed the classical self-duality theorem. The theorem does not
apply to W(3,3), and the reason it does not apply is exactly the reason
W33-Theory's proof had to reach for geometry rather than counting. The two
results fit together: counting closes every quadrangle with t > s, and the
diagonal t = s is where the hard case lives.

SCOPE, honestly.  The centre property of Step 2 is an input, verified here by
exhaustive or sampled enumeration on each geometry rather than proved. On
Q^-(5,3) it rests on 60 sampled minimum blockers, not on all of them.
Everything downstream of it -- reciprocity, balance, trichotomy, the two
branches -- is proved for all (s,t). No claim is made for a quadrangle whose
centre property has not been checked.
"""

import collections
import itertools
import random
import json
import os
import sys

try:
    from ortools.sat.python import cp_model
except ImportError:
    sys.exit("needs ortools:  py -3 -m pip install ortools")

ROOT = r"C:\Repos\Holotrade"


# ---------------------------------------------------------------- geometries

def _proj_points(q, nvar, Qf):
    def norm(v):
        return min(tuple((c * m) % q for c in v) for m in range(1, q))
    seen, reps = set(), []
    for v in itertools.product(range(q), repeat=nvar):
        if not any(v):
            continue
        k = norm(v)
        if k not in seen:
            seen.add(k)
            reps.append(k)
    return [p for p in reps if Qf(p) == 0], norm


def _quadric(q, nvar, Qf, Bf):
    pts, norm = _proj_points(q, nvar, Qf)
    idx = {p: i for i, p in enumerate(pts)}
    lines = set()
    for a, b in itertools.combinations(pts, 2):
        if Bf(a, b) != 0:
            continue
        L, ok = set(), True
        for x in range(q):
            for y in range(q):
                if x == 0 and y == 0:
                    continue
                w = tuple((x * a[i] + y * b[i]) % q for i in range(nvar))
                if Qf(w) != 0:
                    ok = False
                    break
                L.add(idx[norm(w)])
            if not ok:
                break
        if ok and len(L) == q + 1:
            lines.add(tuple(sorted(L)))
    return len(pts), [list(x) for x in sorted(lines)]


def q_minus_5(q):
    """Q^-(5,q) = GQ(q, q^2), the elliptic quadric. Never has an ovoid."""
    if q == 2:
        def Qf(v):
            return (v[0] * v[1] + v[2] * v[3]
                    + v[4] * v[4] + v[4] * v[5] + v[5] * v[5]) % 2
    else:
        def Qf(v):
            return (v[0] * v[1] + v[2] * v[3]
                    + v[4] * v[4] + v[5] * v[5]) % q

    def Bf(u, v):
        return (Qf(tuple((u[i] + v[i]) % q for i in range(6)))
                - Qf(u) - Qf(v)) % q
    return _quadric(q, 6, Qf, Bf)


def w33():
    """W(3,3) = GQ(3,3) from the symplectic form on F_3^4."""
    q = 3

    def norm(v):
        return min(tuple((c * m) % q for c in v) for m in (1, 2))

    def sym(u, v):
        return (u[0] * v[1] - u[1] * v[0] + u[2] * v[3] - u[3] * v[2]) % q

    seen, pts = set(), []
    for v in itertools.product(range(q), repeat=4):
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
            L = set()
            for x in range(q):
                for y in range(q):
                    if x == 0 and y == 0:
                        continue
                    w = tuple((x * a[i] + y * b[i]) % q for i in range(4))
                    L.add(idx[norm(w)])
            if len(L) == q + 1:
                lines.add(tuple(sorted(L)))
    return len(pts), [list(x) for x in sorted(lines)]


def t2star_gq35():
    """T_2*(hyperoval in PG(2,4)) = GQ(3,5). Has an ovoid -- the control."""
    add = [[0, 1, 2, 3], [1, 0, 3, 2], [2, 3, 0, 1], [3, 2, 1, 0]]
    mul = [[0, 0, 0, 0], [0, 1, 2, 3], [0, 2, 3, 1], [0, 3, 1, 2]]

    def npt(v):
        best = v
        for c in (1, 2, 3):
            w = tuple(mul[c][x] for x in v)
            if w < best:
                best = w
        return best

    O = {npt((1, t, mul[t][t])) for t in range(4)}
    O |= {npt((0, 0, 1)), npt((0, 1, 0))}
    pts = [(a, b, c) for a in range(4) for b in range(4) for c in range(4)]
    idx = {p: i for i, p in enumerate(pts)}
    lines = set()
    for d in sorted(O):
        for p in pts:
            L = frozenset(
                idx[tuple(add[p[i]][mul[k][d[i]]] for i in range(3))]
                for k in range(4))
            lines.add(tuple(sorted(L)))
    return len(pts), [list(x) for x in sorted(lines)]


# ---------------------------------------------------------------- machinery

def tau1(n, lines, tl=600.0):
    m = cp_model.CpModel()
    x = [m.NewBoolVar("") for _ in range(n)]
    for L in lines:
        m.AddBoolOr([x[p] for p in L])
    m.Minimize(sum(x))
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = tl
    s.parameters.num_search_workers = 8
    st = s.Solve(m)
    return int(s.ObjectiveValue()), s.StatusName(st) == "OPTIMAL"


def centre_property(n, lines, tau, cap, tl, mode="enumerate"):
    """Every minimum blocker's >1 lines form one pencil, all traces equal.

    Two samplers. "enumerate" walks all minimum blockers and is exhaustive
    where it finishes. "cuts" re-solves with a randomised seed and a no-good
    cut after each hit, which is the only way to get samples at all on
    Q^-(5,3), where plain enumeration produced none in seven minutes.
    """
    lsets = [set(L) for L in lines]
    thru = {p: frozenset(li for li, L in enumerate(lines) if p in L)
            for p in range(n)}
    by_pencil = {v: k for k, v in thru.items()}
    profiles = collections.Counter()
    pencil, centres, inside, seen = 0, collections.Counter(), 0, 0

    def score(bs):
        nonlocal pencil, inside
        pr = collections.Counter(len(bs & L) for L in lsets)
        profiles[tuple(sorted(pr.items()))] += 1
        exc = frozenset(li for li, L in enumerate(lsets) if len(bs & L) > 1)
        if exc in by_pencil and len(pr) == 2:
            pencil += 1
            c = by_pencil[exc]
            centres[c] += 1
            if c in bs:
                inside += 1

    m = cp_model.CpModel()
    y = [m.NewBoolVar("") for _ in range(n)]
    for L in lines:
        m.AddBoolOr([y[p] for p in L])
    m.Add(sum(y) == tau)
    exhaustive = False

    if mode == "enumerate":
        class C(cp_model.CpSolverSolutionCallback):
            def __init__(self, v):
                super().__init__()
                self.v, self.k = v, 0

            def on_solution_callback(self):
                self.k += 1
                score({i for i in range(n) if self.Value(self.v[i])})
                if self.k >= cap:
                    self.StopSearch()

        s = cp_model.CpSolver()
        s.parameters.enumerate_all_solutions = True
        s.parameters.num_search_workers = 1
        s.parameters.max_time_in_seconds = tl
        cb = C(y)
        st = s.Solve(m, cb)
        seen = cb.k
        exhaustive = s.StatusName(st) == "OPTIMAL" and cb.k < cap
    else:
        rng = random.Random(11)
        for _ in range(cap):
            s = cp_model.CpSolver()
            s.parameters.max_time_in_seconds = tl
            s.parameters.num_search_workers = 8
            s.parameters.random_seed = rng.randrange(10 ** 6)
            s.parameters.randomize_search = True
            st = s.Solve(m)
            if s.StatusName(st) not in ("FEASIBLE", "OPTIMAL"):
                break
            bs = {i for i in range(n) if s.Value(y[i])}
            score(bs)
            seen += 1
            m.Add(sum(y[i] for i in bs) <= tau - 1)

    return {
        "sampler": mode,
        "sampled": seen,
        "exhaustive": exhaustive,
        "profiles": {str(dict(k)): v for k, v in profiles.items()},
        "excessIsOnePencil": pencil,
        "holdsOnEverySampled": pencil == seen and seen > 0,
        "distinctCentres": len(centres),
        "centreInsideItsBlocker": inside,
    }


def branches(s_, t_):
    """Solutions of a(t+1) + b = t+1 with a + b <= s+1, a,b >= 0."""
    out = []
    for a in range(0, 2):
        b = (t_ + 1) - a * (t_ + 1)
        if b >= 0 and a + b <= s_ + 1:
            out.append({"multTPlus1Points": a, "mult1Points": b,
                        "width": a + b,
                        "meaning": ("F is an ovoid" if a == 1
                                    else "every centre map fibre is a "
                                         "singleton (a bijection)")})
    return out


def main():
    cases = [
        ("Q^-(5,2) = GQ(2,4)", q_minus_5, 2, (2, 4), 4000, 300.0, "enumerate"),
        ("Q^-(5,3) = GQ(3,9)", q_minus_5, 3, (3, 9), 60, 25.0, "cuts"),
        ("W(3,3) = GQ(3,3)", None, None, (3, 3), 4000, 300.0, "enumerate"),
        ("T_2*(O) = GQ(3,5)", None, None, (3, 5), 4000, 300.0, "enumerate"),
    ]
    print("THE DEPTH-2 TIGHT CASE IS IMPOSSIBLE WHENEVER t > s")
    print("=" * 72)
    print("  The multiplicity trichotomy is PROVED here for all (s,t) from")
    print("  reciprocity and the no-triangle axiom (see Step 5 in the")
    print("  docstring), so nothing is borrowed by analogy. It leaves exactly")
    print("  two branches; branch (B) needs t <= s, branch (A) needs an ovoid.")
    print()

    rows = []
    for name, fam, q, (s_, t_), cap, tl, mode in cases:
        if fam is not None:
            n, lines = fam(q)
        elif (s_, t_) == (3, 3):
            n, lines = w33()
        else:
            n, lines = t2star_gq35()
        nl = len(lines)
        ov = s_ * t_ + 1
        tv, proved = tau1(n, lines)
        delta = tv - ov
        if delta == 0:
            # An ovoid exists, so minimum blockers ARE ovoids, the excess is
            # empty and there is no centre to speak of. The tight case is
            # attained and nothing here applies. Recorded as the control.
            cp = {"sampler": "not run", "sampled": 0, "exhaustive": False,
                  "profiles": {}, "excessIsOnePencil": 0,
                  "holdsOnEverySampled": None,
                  "notApplicable": "delta = 0: minimum blockers are ovoids, "
                                   "the excess is empty and the tight case is "
                                   "attained",
                  "distinctCentres": 0, "centreInsideItsBlocker": 0}
        else:
            cp = centre_property(n, lines, tv, cap, tl, mode)
        br = branches(s_, t_) if delta >= 1 else []
        applies = bool(delta >= 1 and t_ > s_
                       and cp["holdsOnEverySampled"])
        row = {
            "name": name, "s": s_, "t": t_, "points": n, "lines": nl,
            "pointsPerLine": s_ + 1, "linesPerPoint": t_ + 1,
            "ovoidSize": ov, "hasOvoid": delta == 0,
            "tau1": tv, "tau1Proved": proved, "delta": delta,
            "tightSize": ov * tv,
            "centreBalancePerLine": t_ + 1,
            "centreProperty": cp,
            "branches": br,
            "branchBAvailable": t_ <= s_,
            "theoremApplies": bool(applies),
            "conclusion": ("tau_2 > %d" % (ov * tv)) if applies else
                          ("tight case attained: an ovoid exists, tau_2 = %d"
                           % (ov * tv) if delta == 0 else
                           "t <= s: branch (B) open, needs a geometric "
                           "argument (this is the W(3,3) case)"),
        }
        rows.append(row)
        print("  %-20s %4d pts, %4d lines | tau_1 = %d%s, ovoid %d, delta %d"
              % (name, n, nl, tv, "" if proved else " (unproved)", ov, delta))
        if delta == 0:
            print("     centre property: not applicable -- %s"
                  % cp["notApplicable"])
        else:
            print("     centre property: %d sampled by %s%s, holds on every "
                  "one: %s"
                  % (cp["sampled"], cp["sampler"],
                     " (EXHAUSTIVE)" if cp["exhaustive"] else "",
                     cp["holdsOnEverySampled"]))
        if br:
            print("     trace profiles: %s"
                  % "; ".join("%s x%d" % (k, v)
                              for k, v in list(cp["profiles"].items())[:3]))
            print("     branches with m in {0,1,%d}: %s"
                  % (t_ + 1,
                     ", ".join("(%d of mult %d, %d of mult 1)"
                               % (b["multTPlus1Points"], t_ + 1,
                                  b["mult1Points"])
                               for b in br)))
        print("     t > s: %s   ==>  %s" % (t_ > s_, row["conclusion"]))
        print()

    print("  Q^-(5,q) = GQ(q,q^2) has no ovoid for every q and always has")
    print("  t = q^2 > s = q, so the theorem covers the whole family wherever")
    print("  the centre property is checked. It is checked here for q = 2 and")
    print("  q = 3 -- including delta = 2 at q = 3, where the excess is still")
    print("  ONE pencil, each of its lines met delta+1 = 3 times. The argument")
    print("  never uses delta, which is why it survives.")
    print()
    print("  W(3,3) sits exactly on the diagonal t = s, where branch (B) is")
    print("  the bijection that W33-Theory had to refute with the classical")
    print("  self-duality theorem. Counting closes t > s; t = s is the hard")
    print("  case, and now it is visibly the ONLY hard case.")

    ok = all(r["centreProperty"]["holdsOnEverySampled"] for r in rows
             if r["delta"] >= 1)
    if "--write" in sys.argv:
        out = os.path.join(ROOT, "data", "gq_tight_case_theorem.json")
        with open(out, "w") as fh:
            json.dump({
                "schema": "holotrade.gq-tight-case-theorem.v1",
                "valid": bool(ok),
                "theorem": ("let Q be a GQ(s,t) with no ovoid satisfying the "
                            "centre property; if t > s then "
                            "tau_2(Q x Q) > (st+1) tau_1(Q)"),
                "provedHere": [
                    "tightness forces every row shadow minimum and every "
                    "column class independent",
                    "pencil reciprocity c_L in M <=> d_M in L",
                    "centre balance #{L : c_L in M} = t+1, independent of delta",
                    "the multiplicity trichotomy m_p in {0, 1, t+1}, for all "
                    "(s,t), from reciprocity and the no-triangle axiom",
                    "exactly two branches: F an ovoid, or t <= s",
                ],
                "inputNotProved": ("the centre property -- every minimum "
                                   "blocker meets one pencil in delta+1 points "
                                   "and every other line once. Verified by "
                                   "enumeration per geometry, not proved."),
                "removesCaveat": ("gq24_tight_obstruction.py generalised the "
                                  "trichotomy by analogy and flagged it; Step 5 "
                                  "here proves it, so the GQ(2,4) bound no "
                                  "longer depends on an unconfirmed analogy"),
                "attribution": ("the tight-case attack and the W(3,3) "
                                "self-duality proof are W33-Theory's "
                                "(43049db, 1513d61); what is added here is the "
                                "proof of the trichotomy for all (s,t), the "
                                "observation that delta cancels, and the t > s "
                                "theorem"),
                "instances": rows,
                "explainsW33": ("W(3,3) has t = s, so branch (B) survives, and "
                                "branch (B) is exactly the bijection whose "
                                "refutation needed self-duality. The theorem "
                                "shows t = s is the only hard case."),
                "boundary": ("the theorem excludes the tight SIZE only; it "
                             "gives no upper bound and does not determine "
                             "tau_2 for any quadrangle."),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(out, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
