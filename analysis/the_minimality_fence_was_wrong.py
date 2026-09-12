#!/usr/bin/env python3
"""
tau_1(W(3,5)) = 29 was already decided in this track, and the later file that
called it undecided drew the wrong fence. Minimality is NOT q = 3 only --
UNIQUENESS is.

THE CONTRADICTION, both files ours.

  gq_diagonal_theorem.py (972e5cd, 2026-08-29) states, and computes:
      "tau_1(W(3,5)) = 29, proved OPTIMAL"
  and goes further, conjecturing tau_1(W(3,q)) = q^2 + q - 1 for odd q on the
  two data points 11 and 29.

  the_minimum_blocker_labels_are_octets.py (aa42b38, 2026-09-04) states:
      "tau_1(W(3,5)) lies in [27,29], undecided"
  and builds its headline on that: "their minimality is a q = 3 coincidence
  with excess exactly q - 3".

The earlier commit owns the result and the later one contradicted it without
citing it. Verified independently here rather than trusting either file, since
they disagree: CP-SAT minimum hitting set over the full point set, proved
OPTIMAL, not sampled --

    q = 3    40 points, 40 lines of 4    tau_1 = 11    OPTIMAL
    q = 5   156 points, 156 lines of 6   tau_1 = 29    OPTIMAL
    q = 7   400 points, 400 lines of 8   tau_1 in [50,55]  FEASIBLE

and q^2+q-1 is 11, 29, 55. So 972e5cd is right and aa42b38 is wrong.

q = 7 IS RECORDED BUT DOES NOT COUNT.  The solver reached 55 = q^2+q-1, which
is only the octet construction turning up again as an upper bound, and bounded
below at 50 without closing in 900 seconds. So tau_1(W(3,7)) is undecided:
CONSISTENT with q^2+q-1 and not evidence for it. The shape of that interval is
worth noticing -- it is exactly the claim aa42b38 wrongly asserted at q = 5,
where the answer had already been proved.

AND THE SOLVER'S LOWER BOUND IS BEATEN BY A CITATION WE ALREADY HOLD.
w33_blocker_centre_structure.py cites Eisfeld, Storme, Szonyi and Sziklai,
"Covers and blocking sets of classical generalised quadrangles", Discrete
Mathematics 238 (2001) 35-51, for the fact that a cover of Q(4,q) with q odd
needs MORE than q^2 + 1 + (q-1)/3 lines; dualising, that is exactly tau_1 of
W(3,q). The corpus applies it only at q = 3, where it gives > 10.67 and hence
the sharp value 11. Applied at q = 7 it gives > 52, i.e. tau_1 >= 53 -- three
better than the 50 the solver proved. So the honest interval is

        tau_1(W(3,7)) in [53, 55]

and closing it needs only 53 and 54 ruled out. A direct attempt at 53, with the
point set reduced by fixing one point of the blocking set (valid, since the
group is transitive on points), returned UNKNOWN after 2700 seconds. The
narrowing is arithmetic on a citation this repository already owns; it is not a
new bound, and the interval is not closed.

CORRECTION ONE: MINIMALITY IS NOT A q = 3 COINCIDENCE.  The octet blockers have
size q^2+q-1, which equals tau_1 at q = 3 AND at q = 5. They are minimum
blockers at both. What is q = 3 only is that q^2+q-1 also meets the OVOID-DEFECT
BOUND q^2+2; the "excess q - 3" is excess over that bound, and the bound is
simply not tight for q > 3. aa42b38 read a statement about the bound as a
statement about minimality.

CORRECTION TWO: WHAT IS ACTUALLY q = 3 ONLY IS UNIQUENESS.  At q = 5 there are
3900 = q^2(q+1)(q^2+1) octet blockers, every one of size 29 and therefore
minimum -- but they are not the only minimum blockers. Enumerating distinct
size-29 blocking sets directly gives many that are NOT octet blockers, so

    q = 3   the octet blockers are minimum AND are all of them   (360)
    q = 5   the octet blockers are minimum but are NOT all of them

which is exactly what 972e5cd saw from the other side when it measured that
only about six per cent of sampled minimum blockers at q = 5 put their excess
on a single pencil.

CORRECTION THREE, and this one is about this session.  Several results in the
run e3ffec2..cddbb6e fenced the q = 3 classification with the reason "the octet
blockers are minimum only at q = 3". That reason is FALSE. The conclusion --
that the classification, the foot selector, the orbit census and the
intersection census are q = 3 statements -- still stands, but it stands because
uniqueness fails at q = 5, not because minimality does. Right fence, wrong
reason, and the certificates that carry that phrasing should be read with this
file beside them.

WHAT DOES NOT CHANGE.  The closed form B(c,m) = (Adj(c) \\ L^perp) u (L \\ {c})
is q-general and unaffected; it describes the octet blockers at every odd q, and
at q = 3 and q = 5 those are minimum blockers. The induced group result
(aa8691a) is unaffected. tau_2 is untouched and stays open in [111, 115].

SCOPE.  tau_1 is computed by exact optimisation over the whole point set and the
solver returns OPTIMAL, so 11 and 29 are proved, not sampled. The non-uniqueness
at q = 5 is EXISTENTIAL and that is all it needs to be: exhibiting minimum
blockers that are not octet blockers refutes the classification there. The
proportion of non-octet minimum blockers is NOT claimed -- the enumeration is
capped and is not a census. The conjecture tau_1(W(3,q)) = q^2+q-1 for odd q is
972e5cd's, rests on two points, and is not extended here.
"""

import argparse
import importlib.util
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def octet_module():
    p = os.path.join(ROOT, "analysis",
                     "the_minimum_blocker_labels_are_octets.py")
    spec = importlib.util.spec_from_file_location("octmod", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def tau1(q, mod, budget):
    from ortools.sat.python import cp_model
    n, LSET, adj, B = mod.build(q)
    m = cp_model.CpModel()
    x = [m.NewBoolVar("x%d" % i) for i in range(n)]
    for S in LSET:
        m.AddBoolOr([x[i] for i in S])
    m.Minimize(sum(x))
    sv = cp_model.CpSolver()
    sv.parameters.num_workers = 8
    sv.parameters.max_time_in_seconds = budget
    st = sv.Solve(m)
    return {
        "q": q, "points": n, "lines": len(LSET), "lineSize": len(LSET[0]),
        "tau1": int(sv.ObjectiveValue()) if st in (cp_model.OPTIMAL,
                                                   cp_model.FEASIBLE) else None,
        "bound": int(sv.BestObjectiveBound()),
        "status": sv.StatusName(st),
        "proved": sv.StatusName(st) == "OPTIMAL",
        "qSquaredPlusQMinus1": q * q + q - 1,
        "ovoidDefectBound": q * q + 2,
        "matchesQSquaredPlusQMinus1": (st == cp_model.OPTIMAL
                                       and int(sv.ObjectiveValue())
                                       == q * q + q - 1),
        "meetsOvoidDefectBound": (st == cp_model.OPTIMAL
                                  and int(sv.ObjectiveValue()) == q * q + 2),
        "interval": [int(sv.BestObjectiveBound()),
                     int(sv.ObjectiveValue())] if st in (
                         cp_model.OPTIMAL, cp_model.FEASIBLE) else None,
        "decided": sv.StatusName(st) == "OPTIMAL",
    }


def uniqueness(q, mod, cap, budget):
    """Existential: are there minimum blockers that are not octet blockers?"""
    from ortools.sat.python import cp_model
    n, LSET, adj, B = mod.build(q)
    octs = [frozenset(i for i in range(n) if B[i, c])
            for c in range(B.shape[1])]
    oct_blockers = {frozenset((adj[c] ^ frozenset(C)) - {c})
                    for C in octs for c in C}
    size = q * q + q - 1
    m = cp_model.CpModel()
    x = [m.NewBoolVar("x%d" % i) for i in range(n)]
    for S in LSET:
        m.AddBoolOr([x[i] for i in S])
    m.Add(sum(x) == size)
    seen = []

    class CB(cp_model.CpSolverSolutionCallback):
        def __init__(self):
            cp_model.CpSolverSolutionCallback.__init__(self)
            self.k = 0

        def on_solution_callback(self):
            self.k += 1
            seen.append(frozenset(i for i in range(n) if self.Value(x[i])))
            if self.k >= cap:
                self.StopSearch()

    sv = cp_model.CpSolver()
    sv.parameters.num_workers = 8
    sv.parameters.enumerate_all_solutions = True
    sv.parameters.max_time_in_seconds = budget
    sv.Solve(m, CB())
    distinct = list(dict.fromkeys(seen))
    inside = sum(1 for b in distinct if b in oct_blockers)
    return {
        "q": q,
        "octetBlockers": len(oct_blockers),
        "octetBlockerClosedForm": q * q * (q + 1) * (q * q + 1),
        "octetBlockerSizes": sorted({len(b) for b in oct_blockers}),
        "minimumBlockersEnumerated": len(distinct),
        "ofThoseAreOctetBlockers": inside,
        "ofThoseAreNot": len(distinct) - inside,
        "nonOctetMinimumBlockersExist": len(distinct) - inside > 0,
        "enumerationIsCappedNotACensus": True,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--qs", type=int, nargs="+", default=[3, 5])
    ap.add_argument("--budget", type=float, default=900.0)
    args = ap.parse_args()

    mod = octet_module()
    taus = [tau1(q, mod, args.budget) for q in args.qs]
    uniq = uniqueness(5, mod, cap=400, budget=1200.0) if 5 in args.qs else None

    print("THE MINIMALITY FENCE WAS WRONG")
    print("=" * 74)
    print("  tau_1 by exact optimisation over the whole point set:")
    for t in taus:
        print("    q=%d  %3d points, %3d lines of %d   tau_1 = %s  [%s]"
              "   q^2+q-1 = %d   q^2+2 = %d   interval %s"
              % (t["q"], t["points"], t["lines"], t["lineSize"], t["tau1"],
                 t["status"], t["qSquaredPlusQMinus1"], t["ovoidDefectBound"],
                 t["interval"]))
    print()
    print("  so the octet size q^2+q-1 IS tau_1 at q = 3 and q = 5:")
    print("  the octet blockers are MINIMUM at both. What is q = 3 only is")
    print("  that q^2+q-1 also meets the ovoid-defect BOUND q^2+2.")
    if uniq:
        print()
        print("  and at q = 5 they are not the only minimum blockers:")
        print("    %d octet blockers, all of size %s"
              % (uniq["octetBlockers"], uniq["octetBlockerSizes"]))
        print("    %d distinct minimum blockers enumerated; %d octet, %d NOT"
              % (uniq["minimumBlockersEnumerated"],
                 uniq["ofThoseAreOctetBlockers"], uniq["ofThoseAreNot"]))
        print("    non-octet minimum blockers EXIST: %s"
              % uniq["nonOctetMinimumBlockersExist"])
    print()
    print("  CORRECTION: aa42b38 said tau_1(W(3,5)) is undecided in [27,29]")
    print("  and framed minimality as a q=3 coincidence. Both are wrong;")
    print("  972e5cd (2026-08-29) had already proved tau_1(W(3,5)) = 29.")
    print("  The q=3 classification still does not generalise -- but because")
    print("  UNIQUENESS fails at q=5, not because minimality does.")

    # q = 3 and 5 must be PROVED; q = 7 is recorded as an interval and is not
    # allowed to count as support -- the solver reached 55 but only bounded
    # below by 50, so tau_1(W(3,7)) is genuinely undecided in [50,55].
    decided = [t for t in taus if t["q"] in (3, 5)]
    ok = (all(t["proved"] and t["matchesQSquaredPlusQMinus1"] for t in decided)
          and len(decided) == len([q for q in args.qs if q in (3, 5)])
          and (uniq is None or uniq["nonOctetMinimumBlockersExist"]))
    print()
    print("VALID: %s" % ok)

    if args.write:
        assert ok, "checks failed -- refusing to write"
        rec = {
            "schema": "holotrade.minimality-fence-was-wrong.v1",
            "valid": True,
            "tau1": taus,
            "uniquenessAtQ5": uniq,
            "theContradiction": (
                "gq_diagonal_theorem.py (972e5cd, 2026-08-29) computes "
                "tau_1(W(3,5)) = 29 and proves it OPTIMAL, and conjectures "
                "tau_1(W(3,q)) = q^2+q-1 for odd q on the two points 11 and 29. "
                "the_minimum_blocker_labels_are_octets.py (aa42b38, 2026-09-04) "
                "says tau_1(W(3,5)) lies in [27,29] undecided, and builds its "
                "headline on that. Both files are ours; the earlier owns the "
                "result and the later contradicted it without citing it."),
            "verifiedIndependently": (
                "since the two files disagree, tau_1 was recomputed here rather "
                "than trusting either: exact CP-SAT minimum hitting set over the "
                "whole point set, status OPTIMAL, giving 11 at q = 3 and 29 at "
                "q = 5. So 972e5cd is right and aa42b38 is wrong."),
            "correctionOneMinimality": (
                "minimality is NOT a q = 3 coincidence. The octet blockers have "
                "size q^2+q-1, which equals tau_1 at q = 3 AND q = 5, so they are "
                "minimum blockers at both. What is q = 3 only is that q^2+q-1 "
                "also meets the OVOID-DEFECT BOUND q^2+2; the 'excess q-3' is "
                "excess over that bound, and the bound is not tight for q > 3. "
                "aa42b38 read a statement about the bound as a statement about "
                "minimality."),
            "correctionTwoUniqueness": (
                "what is actually q = 3 only is UNIQUENESS. At q = 5 there are "
                "3900 = q^2(q+1)(q^2+1) octet blockers, all of size 29 and hence "
                "minimum, but enumerating size-29 blocking sets directly produces "
                "many that are NOT octet blockers. So at q = 3 the octet blockers "
                "are minimum and are all of them; at q = 5 they are minimum and "
                "are not all of them. This is the same fact 972e5cd saw from the "
                "other side when it measured that only about six per cent of "
                "sampled minimum blockers at q = 5 put their excess on a single "
                "pencil."),
            "correctionThreeThisSession": (
                "several results in the run e3ffec2..cddbb6e fenced the q = 3 "
                "classification with the reason 'the octet blockers are minimum "
                "only at q = 3'. That reason is false. The conclusion -- that the "
                "classification, the foot selector, the orbit census and the "
                "intersection census are q = 3 statements -- stands, but it "
                "stands because uniqueness fails at q = 5, not because minimality "
                "does. Right fence, wrong reason."),
            "whatDoesNotChange": (
                "the closed form B(c,m) = (Adj(c) minus L^perp) union (L minus "
                "{c}) is q-general and unaffected; it describes the octet "
                "blockers at every odd q, and at q = 3 and q = 5 those are "
                "minimum blockers. The induced group result (aa8691a) is "
                "unaffected. tau_2 is untouched and stays open in [111, 115]."),
            "publishedBoundBeatsTheSolverAtQ7": (
                "w33_blocker_centre_structure.py already cites Eisfeld, Storme, "
                "Szonyi and Sziklai, 'Covers and blocking sets of classical "
                "generalised quadrangles', Discrete Mathematics 238 (2001) 35-51, "
                "for the fact that a cover of Q(4,q) with q odd needs MORE than "
                "q^2+1+(q-1)/3 lines; dualising, that is tau_1(W(3,q)). The corpus "
                "applies it only at q = 3, where it gives > 10.67 and hence the "
                "sharp 11. Applied at q = 7 it gives > 52, so tau_1 >= 53 -- three "
                "better than the 50 the solver proved. The honest interval is "
                "therefore [53,55], and closing it needs only 53 and 54 ruled out. "
                "A direct attempt at 53, with one point of the blocking set fixed "
                "(valid since the group is transitive on points), returned UNKNOWN "
                "after 2700 seconds. This is arithmetic on a citation we already "
                "hold, not a new bound, and the interval is NOT closed."),
            "qSevenIsUndecidedAndDoesNotSupportTheConjecture": (
                "at q = 7 the solver reached 55 = q^2+q-1, which is only the "
                "octet construction being rediscovered as an upper bound, but "
                "bounded below at 50 and returned FEASIBLE rather than OPTIMAL in "
                "900 seconds. So tau_1(W(3,7)) is genuinely undecided in [50,55]. "
                "It is CONSISTENT with tau_1 = q^2+q-1 and is not evidence for "
                "it, and it is recorded that way rather than counted as a third "
                "data point. The irony is noted: an undecided interval at q = 7 is "
                "exactly the shape of the claim aa42b38 wrongly asserted at "
                "q = 5, where the answer was already proved."),
            "boundary": (
                "tau_1 is computed by exact optimisation over the whole point set "
                "with the solver returning OPTIMAL, so 11 and 29 are PROVED, not "
                "sampled. The non-uniqueness at q = 5 is EXISTENTIAL and that is "
                "all it needs to be: exhibiting minimum blockers that are not "
                "octet blockers refutes the classification there. The PROPORTION "
                "of non-octet minimum blockers is not claimed -- the enumeration "
                "is capped and is not a census. The conjecture tau_1(W(3,q)) = "
                "q^2+q-1 for odd q is 972e5cd's, rests on two points, and is not "
                "extended here."),
        }
        p = os.path.join(ROOT, "data", "minimality_fence_was_wrong.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=2)
        print("written: %s" % p)


if __name__ == "__main__":
    main()
