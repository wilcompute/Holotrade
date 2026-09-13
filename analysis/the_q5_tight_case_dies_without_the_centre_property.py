#!/usr/bin/env python3
"""
tau_2(W(3,5)^2) > 754. The tight case is excluded at q = 5 even though the
centre property FAILS there -- because the two binary digits of every minimum
blocker's excess are pencils, and one digit is all the self-duality argument
ever needed. On the way: all 50,700 minimum blockers of W(3,5), classified.

WHERE THE MACHINERY STOPPED.  gq_diagonal_theorem.py proves: a GQ(s,s) with no
ovoid, the centre property, and no self-duality has tau_2 > (s^2+1) tau_1. It
records that this "would cover W(3,q) for every odd q -- but does NOT, because
the centre property fails at q = 5". The q = 5 tight size (q^2+1) tau_1 =
26 * 29 = 754 was therefore open.

THE MINIMUM BLOCKERS OF W(3,5), CLASSIFIED.  A 29-point blocker B has excess
e(M) = |B n M| - 1 >= 0 with total 6*29 - 156 = 18. Exactly two kinds exist:

  OCTET       e = 3 pencil(c),              B = (Adj(c) - L^perp) u (L - {c})
              c not in B, L hyperbolic through c;          156 * 25 =  3,900
  TWO-CENTRE  e = 2 pencil(a) + pencil(b),  a != b collinear on M0, neither in B;
              of the five hyperbolic lines through a inside b^perp choose two,
              l and l', and let m1, m2, m3 be the perps of the other three:
              B = (M0 - {a,b}) u (l u l' - {a}) u (m1 u m2 u m3 - {b})
                                                            4680 * 10 = 46,800
Both are e = N^T (2 delta_A + delta_B) with A, B collinear or equal, i.e.

    BIT 1 of e is the pencil of A and BIT 0 of e is the pencil of B.

THE PROOF OF THE CLASSIFICATION, in four parts.

 (a) TWO COUNTING IDENTITIES.  A point off a line M lies on exactly one line
     meeting M and on five lines disjoint from it. Summing |B n N| over the
     lines N meeting M, and over those disjoint from M, gives for c = |B n M|
            excess on the 30 lines meeting M     =  4c - 1  =  4 e(M) + 3,
            excess on the 125 lines disjoint     =  20 - 5c.
     The second forces c <= 4, so e <= 3. The first says A_L e = 4e + 3.1,
     with A_L the adjacency of lines: e is a WEIGHTED 3-TIGHT SET of lines.

 (b) THE PENCIL LEMMA.  For x = 1, 2, 3, every integer e with 0 <= e <= 3 and
     A_L e = 4e + x.1 contains a full pencil (some point with e >= 1 on all six
     of its lines): three exact CP-SAT infeasibilities, each with a control
     without the "no pencil" constraint that must be feasible. Removing a
     pencil lowers x by one and keeps the hypotheses, so by induction
            e = N^T y,     y >= 0 an integer vector on points,  sum y = 3.
     A single monolithic "any other profile" blocker query had returned UNKNOWN
     at 7200 s; the lemma turns the problem into a handful of tiny ones.

 (c) THE PATTERNS.  PSp(4,5) is transitive on points, on collinear pairs and on
     non-collinear pairs, so y is one of 3p, 2p+q (q collinear or not), or
     p+q+r with p, q representatives of the two pair orbits and r arbitrary --
     3 + 308 cases. In each, y fixes every line count and CP-SAT decides it:
     feasible exactly for 3p and for 2p+q with q collinear; all others
     INFEASIBLE.

 (d) THE CENSUS.  With (a,b) fixed, the ten constructions are the only
     two-centre blockers; with c fixed, the 25 octets are the only octet
     blockers -- each an INFEASIBLE after forbidding the constructions, with a
     control that forbids all but one and must recover it. So there are exactly
     3,900 + 46,800 = 50,700 minimum blockers (GAP independently finds two
     orbits of these sizes, stabilisers 1200 and 100).

THE ARGUMENT.  Suppose |X| = 754. Step 1 of gq_tight_case_theorem.py gives that
every row shadow B_L and column shadow D_M is a minimum blocker and that
T[L][M] = |X n (L x M)| = |B_L n M| = |D_M n L|. So

    E[L][M] = 2[A_L in M] + [B_L in M] = 2[A'_M in L] + [B'_M in L],

and binary expansion is unique, hence A_L in M <=> A'_M in L for all L, M.
That is EXACTLY the centre reciprocity, with A playing the centre, and the rest
of the existing proof uses nothing else: {L : A_L in M} = pencil(A'_M) gives
line sums 6 for m_p = #{L : A_L = p} (Step 4); m_p in {0,1,6} (Step 5); each
line is one point of multiplicity 6 or six of multiplicity 1 (Step 6); and at
t = s the multiplicity-1 set is empty or everything (the mixing lemma of
gq_diagonal_theorem.py). Empty gives an ovoid of W(3,5); everything makes
L -> A_L and M -> A'_M bijections that swap points and lines preserving
incidence, a duality. W(3,q) has an ovoid iff q is even and is self-dual iff q
is even (Payne and Thas, Finite Generalized Quadrangles; both classical). So

    tau_2(W(3,5) x W(3,5))  >=  755,        and <= 29^2 = 841 by B x B.

WHAT CHANGED.  The centre property was never the load-bearing input; a
THRESHOLD reading of the excess is. At q = 3 they coincide. At q = 5 the single
pencil is gone but the top bit still marks one.

CONSISTENT EVIDENCE, not part of the proof.  A symmetry sweep of the tight
model under 21 structured subgroups of SL(2,25).<sigma> found no tight set
(18 INFEASIBLE, 3 UNKNOWN); q = 2 recovered a tight set and q = 3 found none.

SCOPE.  (a) and the induction in (b) are argued in full; the lemma instances,
the patterns and the census are exact solver verdicts with controls; the step
from the classification to the ovoid/duality dichotomy uses results already
proved in this repository; the non-existence of ovoids and dualities of W(3,5)
is classical. Nothing is claimed for q >= 7. tau_2(W(3,3)^2) stays open in
[111, 115].
"""

import argparse
import itertools
import json
import os
import time
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Q = 5


def geometry():
    def nm(v):
        i = next(k for k, x in enumerate(v) if x % Q)
        z = pow(v[i] % Q, -1, Q)
        return tuple((z * x) % Q for x in v)
    pts = sorted({nm(v) for v in itertools.product(range(Q), repeat=4) if any(v)})
    idx = {p: i for i, p in enumerate(pts)}
    n = len(pts)

    def sf(u, v):
        return (u[0] * v[2] - u[2] * v[0] + u[1] * v[3] - u[3] * v[1]) % Q

    def span(a, b):
        S = set()
        for x in range(Q):
            for y in range(Q):
                if x or y:
                    S.add(idx[nm(tuple((x * pts[a][k] + y * pts[b][k]) % Q for k in range(4)))])
        return frozenset(S)
    perp = [frozenset(j for j in range(n) if sf(pts[i], pts[j]) == 0) for i in range(n)]
    lines = sorted({span(a, b) for a, b in itertools.combinations(range(n), 2)
                    if sf(pts[a], pts[b]) == 0}, key=sorted)
    assert n == 156 and len(lines) == 156 and all(len(L) == 6 for L in lines)
    return n, lines, perp, span


def solver(budget, workers=8):
    from ortools.sat.python import cp_model
    sv = cp_model.CpSolver()
    sv.parameters.num_workers = workers
    sv.parameters.max_time_in_seconds = budget
    return sv


def pencil_lemma(n, lines, budget):
    from ortools.sat.python import cp_model
    thru = [[j for j, L in enumerate(lines) if p in L] for p in range(n)]
    meet = [[k for k, M in enumerate(lines) if k != j and lines[j] & M] for j in range(n)]
    assert all(len(r) == 30 for r in meet)
    pen = [1 if 0 in L else 0 for L in lines]
    pencil_is_one_tight = all(sum(pen[k] for k in meet[j]) == 4 * pen[j] + 1 for j in range(n))
    out = {}
    for x in (1, 2, 3):
        for mode in ("noPencil", "control"):
            m = cp_model.CpModel()
            e = [m.NewIntVar(0, 3, "") for _ in range(n)]
            for j in range(n):
                m.Add(sum(e[k] for k in meet[j]) == 4 * e[j] + x)
            m.Add(e[0] >= 1)
            if mode == "noPencil":
                for p in range(n):
                    pos = []
                    for j in thru[p]:
                        b = m.NewBoolVar("")
                        m.Add(e[j] >= 1).OnlyEnforceIf(b)
                        m.Add(e[j] == 0).OnlyEnforceIf(b.Not())
                        pos.append(b)
                    m.Add(sum(pos) <= 5)
            sv = solver(budget)
            t0 = time.time()
            out["x%d_%s" % (x, mode)] = (sv.StatusName(sv.Solve(m)), round(time.time() - t0, 1))
    return pencil_is_one_tight, out


def patterns(n, lines, perp, budget):
    from ortools.sat.python import cp_model

    def test(y):
        m = cp_model.CpModel()
        x = [m.NewBoolVar("") for _ in range(n)]
        m.Add(sum(x) == 29)
        for L in lines:
            e = sum(y.get(p, 0) for p in L)
            if e > 3:
                return "INFEASIBLE"      # a count of 5+ contradicts (a)
            m.Add(sum(x[i] for i in L) == 1 + e)
        sv = solver(budget)
        return sv.StatusName(sv.Solve(m))

    p = 0
    qc = next(j for j in range(1, n) if j in perp[p])
    qn = next(j for j in range(1, n) if j not in perp[p])
    rows = {"3p": test({p: 3}), "2p+q collinear": test({p: 2, qc: 1}),
            "2p+q noncollinear": test({p: 2, qn: 1})}
    triples = Counter()
    for q in (qc, qn):
        for r in range(n):
            if r not in (p, q):
                triples[test({p: 1, q: 1, r: 1})] += 1
    return rows, dict(triples)


def census(n, lines, perp, span, budget):
    from ortools.sat.python import cp_model

    def lperp(L):
        return frozenset.intersection(*[perp[i] for i in L])

    def blocks(B):
        return all(B & L for L in lines)

    a = 0
    b = next(j for j in sorted(perp[a]) if j != a)
    M0 = span(a, b)
    hyp = sorted({span(a, y) for y in perp[b] - M0}, key=sorted)
    assert len(hyp) == 5 and all(b not in l and l <= perp[b] for l in hyp)
    two = []
    for S in itertools.combinations(range(5), 2):
        B = set(M0 - {a, b})
        for i in range(5):
            B |= (hyp[i] - {a}) if i in S else (lperp(hyp[i]) - {b})
        two.append(frozenset(B))
    c = 0
    hyp_c = sorted({span(c, y) for y in range(n) if y not in perp[c]}, key=sorted)
    octs = [frozenset((perp[c] - {c} - lperp(L)) | (L - {c})) for L in hyp_c]

    def excess(B):
        return [len(B & L) - 1 for L in lines]

    def shape_two(B):
        return all(v == 2 * (a in L) + (b in L) for v, L in zip(excess(B), lines))

    def shape_oct(B):
        return all(v == 3 * (c in L) for v, L in zip(excess(B), lines))

    def query(kind, forbid):
        m = cp_model.CpModel()
        x = [m.NewBoolVar("") for _ in range(n)]
        m.Add(sum(x) == 29)
        for L in lines:
            want = (4 if L == M0 else 3 if a in L else 2 if b in L else 1) if kind == 2 \
                else (4 if c in L else 1)
            m.Add(sum(x[i] for i in L) == want)
        for B in forbid:
            m.Add(sum(x[i] for i in B) <= 28)
        sv = solver(budget, 4)
        st = sv.StatusName(sv.Solve(m))
        sol = frozenset(i for i in range(n) if sv.Value(x[i])) if st in ("OPTIMAL", "FEASIBLE") else None
        return st, sol

    ctl2, all2 = query(2, two[:-1]), query(2, two)
    ctl8, all8 = query(8, octs[:-1]), query(8, octs)
    return {
        "twoCentreConstructions": len(set(two)),
        "twoCentreConstructionsValid": all(len(B) == 29 and blocks(B) and shape_two(B) for B in two),
        "octetConstructions": len(set(octs)),
        "octetConstructionsValid": all(len(B) == 29 and blocks(B) and shape_oct(B) for B in octs),
        "controlTwoRecoversLast": ctl2[0] in ("OPTIMAL", "FEASIBLE") and ctl2[1] == two[-1],
        "twoCentreOthers": all2[0],
        "controlOctetRecoversLast": ctl8[0] in ("OPTIMAL", "FEASIBLE") and ctl8[1] == octs[-1],
        "octetOthers": all8[0],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--budget", type=float, default=1800.0)
    args = ap.parse_args()

    n, lines, perp, span = geometry()
    print("THE q = 5 TIGHT CASE DIES WITHOUT THE CENTRE PROPERTY")
    print("=" * 74)
    print("  W(3,5): %d points, %d lines; tau_1 = 29 (the_minimality_fence_was_wrong.py)" % (n, len(lines)))

    one_tight, lemma = pencil_lemma(n, lines, args.budget)
    print("  (b) pencil lemma (a pencil is 1-tight: %s)" % one_tight)
    for k, v in lemma.items():
        print("        %-16s %s  %ss" % (k, v[0], v[1]))
    lemma_ok = one_tight and all(lemma["x%d_noPencil" % x][0] == "INFEASIBLE" and
                                 lemma["x%d_control" % x][0] in ("OPTIMAL", "FEASIBLE") for x in (1, 2, 3))

    rows, triples = patterns(n, lines, perp, 600)
    print("  (c) patterns: %s; p+q+r over 308 cases: %s" % (rows, triples))
    pat_ok = (rows["3p"] in ("OPTIMAL", "FEASIBLE") and rows["2p+q collinear"] in ("OPTIMAL", "FEASIBLE")
              and rows["2p+q noncollinear"] == "INFEASIBLE" and triples == {"INFEASIBLE": 308})

    cen = census(n, lines, perp, span, 1800)
    print("  (d) census: %s" % cen)
    cen_ok = (cen["twoCentreOthers"] == "INFEASIBLE" and cen["octetOthers"] == "INFEASIBLE"
              and cen["controlTwoRecoversLast"] and cen["controlOctetRecoversLast"]
              and cen["twoCentreConstructions"] == 10 and cen["octetConstructions"] == 25
              and cen["twoCentreConstructionsValid"] and cen["octetConstructionsValid"])

    classified = lemma_ok and pat_ok and cen_ok
    print()
    print("  classification exact: %s   minimum blockers: 156*25 + 4680*10 = %d"
          % (classified, 156 * 25 + 4680 * 10))
    print("  => digits unique, so A_L in M <=> A'_M in L: centre reciprocity, hence an ovoid or a")
    print("     duality of W(3,5); neither exists, so tau_2(W(3,5)^2) >= 755 (and <= 841).")
    ok = classified
    print()
    print("VALID: %s" % ok)

    if args.write:
        assert ok, "checks failed -- refusing to write"
        rec = {
            "schema": "holotrade.q5-tight-case-dies.v2",
            "valid": True,
            "q": Q, "points": n, "lines": len(lines), "tau1": 29,
            "tightSize": 754, "lowerBound": 755, "upperBound": 841,
            "minimumBlockers": 50700, "octetBlockers": 3900, "twoCentreBlockers": 46800,
            "pencilIsOneTight": one_tight,
            "pencilLemma": {k: v[0] for k, v in lemma.items()},
            "pencilLemmaSeconds": {k: v[1] for k, v in lemma.items()},
            "patterns": rows, "tripleCases": triples,
            "census": cen,
            "shapes": {
                "octet": "e = 3 pencil(c); B = (Adj(c) - L^perp) u (L - {c}); 3,900",
                "twoCentre": ("e = 2 pencil(a) + pencil(b), a != b collinear on M0; B = (M0 - {a,b}) u "
                              "(l u l' - {a}) u (m1 u m2 u m3 - {b}); 46,800")},
            "whereTheMachineryStopped": (
                "gq_diagonal_theorem.py proves the tight case impossible for a GQ(s,s) with no ovoid, the "
                "centre property and no self-duality, and records that it does NOT cover q = 5 because the "
                "centre property fails there. The q = 5 tight size 754 was therefore open."),
            "theCountingIdentities": (
                "a point off a line M lies on exactly one line meeting M and five disjoint from it, so with "
                "c = |B n M| the excess on lines meeting M is 4c - 1 = 4 e(M) + 3 and on lines disjoint from M "
                "is 20 - 5c. Hence c <= 4, e <= 3, and A_L e = 4e + 3.1: e is a weighted 3-tight set of lines."),
            "thePencilLemma": (
                "for x = 1, 2, 3 every integer 0 <= e <= 3 with A_L e = 4e + x.1 contains a full pencil (three "
                "INFEASIBLE verdicts, each with a feasible control). Removing a pencil lowers x by one, so by "
                "induction e = N^T y with y >= 0 integer and sum y = 3."),
            "thePatterns": (
                "by transitivity on points and on collinear and non-collinear pairs, y is 3p, 2p+q or p+q+r "
                "over 3 + 308 cases, each deciding a blocker with every line count fixed: feasible exactly for "
                "3p and 2p+q with q collinear."),
            "theDigitLemma": (
                "every minimum blocker of W(3,5) has e = N^T (2 delta_A + delta_B) with A, B collinear or "
                "equal: BIT 1 of the excess is the pencil of A and BIT 0 is the pencil of B."),
            "theArgument": (
                "at |X| = 754 every shadow is a minimum blocker and E[L][M] = 2[A_L in M] + [B_L in M] = "
                "2[A'_M in L] + [B'_M in L]. Binary expansion is unique, so A_L in M <=> A'_M in L: exactly "
                "the centre reciprocity. Steps 4-6 of gq_tight_case_theorem.py and the mixing lemma of "
                "gq_diagonal_theorem.py use nothing else, and give either an ovoid of W(3,5) or a duality of "
                "W(3,5). W(3,q) has an ovoid iff q is even and is self-dual iff q is even (Payne and Thas, "
                "Finite Generalized Quadrangles; both classical). So no tight set exists and "
                "tau_2(W(3,5)^2) >= 755."),
            "whatChanged": (
                "the centre property was never the load-bearing input; a threshold reading of the excess is. "
                "At q = 3 they coincide. At q = 5 the single pencil is gone but the top bit still marks one."),
            "consistentEvidenceNotProof": (
                "a symmetry sweep of the tight model under 21 structured subgroups of SL(2,25).<sigma> found no "
                "tight set (18 INFEASIBLE, 3 UNKNOWN); q = 2 recovered a tight set and q = 3 found none. A "
                "monolithic any-other-profile blocker query returned UNKNOWN at 7200 s."),
            "boundary": (
                "the counting identities and the induction are argued; the lemma instances, the patterns and "
                "the census are exact solver verdicts with controls; the step to the ovoid/duality dichotomy "
                "uses results already proved here; the non-existence of ovoids and dualities of W(3,5) is "
                "classical. Nothing is claimed for q >= 7. tau_2(W(3,3)^2) stays open in [111, 115]."),
        }
        p = os.path.join(ROOT, "data", "q5_tight_case_dies.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=2)
        print("written: %s" % p)


if __name__ == "__main__":
    main()
