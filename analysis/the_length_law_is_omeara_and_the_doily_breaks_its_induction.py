#!/usr/bin/env python3
"""
The length law I proved in ba7ac5a is O'Meara's theorem. Retracting the
novelty, keeping what is actually ours, and reporting where the doily breaks
the classical induction.

THE RETRACTION.  ba7ac5a stated, as though new, that an element of Sp(4,3) has
transvection length > residue exactly when it is -1 on a nondegenerate U and +1
on U^perp. That is the classical hyperbolic-map theorem. O'Meara defines F to be
HYPERBOLIC when <v, vF> = 0 for every v, and the theorem is that a
non-hyperbolic F is a product of exactly res(F) transvections while a hyperbolic
one needs res(F) + 1. Checked here against my own set:

    q = 3    anomalies (length > residue)  91
             O'Meara hyperbolic maps       91
             equal as SETS                yes

So the result is a rediscovery. Sources: O'Meara, "Symplectic Groups" (AMS
Mathematical Surveys 16, 1978); Callan, "The generation of Sp(F_2) by
transvections", J. Algebra 42 (1976) 378-390; quoted in that form by
Pllaha-Volanto-Tirkkonen, "Decomposition of Clifford Gates", arXiv:2102.11380.
I have read the secondhand statement in the last of these, NOT the primary
texts, and the discrepancy reported below should be read with that in mind.

AND MY CHARACTERISATION IS NOT THE GENERAL ONE.  "-1 on a nondegenerate U" is a
q-ODD specialisation. It coincides with hyperbolicity at q = 3, but at q = 2 it
is empty while fifteen hyperbolic maps exist. The general criterion is O'Meara's;
mine is a coincidence of odd characteristic.

A TERMINOLOGY TRAP WORTH RECORDING.  "Hyperbolic map" (O'Meara: <v, vF> = 0 for
all v) and "hyperbolic line" (PG(3,3): a 2-space on which the form is
non-degenerate) are unrelated notions that both appear in this result, and at
q = 3 their counts are 91 and 90 -- one apart. Anything reusing these numbers
must not conflate them.

WHAT ACTUALLY SURVIVES AS OURS.  3f93821's bijection stands and is not in the
literature: g -> im(g - 1) carries the 90 residue-2 anomalies onto the 90
hyperbolic LINES of PG(3,3), whose polar pairs are BT810's 45 tritangent planes
= the 45 octets = the sentinel code's 45 minimum-weight words. That the ISA's
extra instruction is charged to the code's minimum-weight objects is a
statement about this substrate, not about symplectic groups, and the literature
result is what makes it precise rather than what supersedes it.

THE NEW PART: AT q = 2 THE CRITERION FAILS, AND THE INDUCTION SHOWS WHY.

    q = 2    anomalies    225        hyperbolic maps    15        equal:  no

Hyperbolicity is a strict subset, so 210 non-hyperbolic elements of Sp(4,2) have
length res + 1. The classical proof drops the residue by one -- pick x with
<x, xF> =/= 0, set v = x + xF, then res(F T_v) = res(F) - 1 -- and that step does
succeed on all of them. The INDUCTION is what breaks, because the step has to
land on a non-hyperbolic element to be repeatable:

    res 2, len 3   15   hyperbolic
    res 3, len 4   90   EVERY residue-dropping step lands HYPERBOLIC
    res 4, len 5  120   a clean step exists -- into the res-3 anomalies above

so the anomaly is a CASCADE, not 225 independent exceptions. Fifteen genuinely
hyperbolic elements poison every escape route out of the ninety at residue 3,
and those in turn are the only exits available to the hundred and twenty at
residue 4. At q = 3 nothing propagates: the (3,3) and (4,4) cells are entirely
clean, because eighty transvections leave escape routes that fifteen do not.

That is a better account of the 178x anomaly-density gap than 6bb8975's, and it
does not replace it -- the centre still explains why the extreme element is
removed by projectivisation. The doily is exceptional twice over: no centre to
quotient, and too few generators to escape its own hyperbolic elements.

A SEPARATE METRIC, AS THE PARALLEL TRACK FLAGGED.  Ellers' 1994 lambda-length
counts transvections from ONE conjugacy class. That is a different quantity from
this repository's, which uses all of them, and the gap is not small:

    q = 3    all transvections  80, diameter 5
             one class          40, diameter 6
             elements where the two lengths differ:  38,264 of 51,840
    q = 2    the two coincide exactly (one lambda available), 0 differences

So Ellers is direct prior art for a neighbouring problem and must be cited
wherever exact transvection lengths are discussed, but it does not settle the
all-transvection numbers used here. Both facts belong in the paper.

SCOPE.  Exhaustive over Sp(4,2) and Sp(4,3): length by full BFS, residue by
rank(g - I), hyperbolicity by testing <v, vF> over every v, set comparisons by
set equality. The primary sources are NOT read here; the q = 2 discrepancy is
reported against a secondhand statement of the theorem and may reflect
hypotheses those sources carry rather than an error. tau_2 is untouched.
"""

import collections
import itertools
import json
import os
import sys

ROOT = r"C:\Repos\Holotrade"


def study(q):
    d = 4

    def mul(A, B):
        return tuple(tuple(sum(A[i][k] * B[k][j] for k in range(d)) % q
                           for j in range(d)) for i in range(d))

    I = tuple(tuple(1 if i == j else 0 for j in range(d)) for i in range(d))

    def form(u, v):
        return (u[0] * v[2] - u[2] * v[0] + u[1] * v[3] - u[3] * v[1]) % q

    E = [tuple(1 if k == j else 0 for k in range(d)) for j in range(d)]

    def tv(vv, lam):
        return tuple(tuple(((1 if i == j else 0)
                            + lam * form(E[j], vv) * vv[i]) % q
                           for j in range(d)) for i in range(d))

    vecs = [v for v in itertools.product(range(q), repeat=d) if any(v)]
    Tall = sorted({tv(v, l) for v in vecs for l in range(1, q)} - {I})
    Tone = sorted({tv(v, 1) for v in vecs} - {I})

    def bfs(gens):
        dist, fr, dia = {I: 0}, [I], 0
        while fr:
            nx = []
            for A in fr:
                for M in gens:
                    C = mul(M, A)
                    if C not in dist:
                        dist[C] = dia + 1
                        nx.append(C)
            fr = nx
            if nx:
                dia += 1
        return dist

    dall, done = bfs(Tall), bfs(Tone)

    def rk(A):
        M = [[(A[i][j] - (1 if i == j else 0)) % q for j in range(d)]
             for i in range(d)]
        r = 0
        for c in range(d):
            p = next((i for i in range(r, d) if M[i][c] % q), None)
            if p is None:
                continue
            M[r], M[p] = M[p], M[r]
            iv = pow(M[r][c], -1, q)
            M[r] = [(x * iv) % q for x in M[r]]
            for i in range(d):
                if i != r and M[i][c] % q:
                    f = M[i][c]
                    M[i] = [(M[i][j] - f * M[r][j]) % q for j in range(d)]
            r += 1
        return r

    def act(A, v):
        return tuple(sum(A[i][k] * v[k] for k in range(d)) % q
                     for i in range(d))

    def is_hyp(A):
        return all(form(v, act(A, v)) % q == 0 for v in vecs)

    anom = {A for A, L in dall.items() if L > rk(A)}
    hyp = {A for A in dall if A != I and is_hyp(A)}

    # the induction diagnostic
    induction = collections.Counter()
    for A, L in dall.items():
        if A == I:
            continue
        r = rk(A)
        if is_hyp(A):
            induction[(r, L, "hyperbolic")] += 1
            continue
        good = 0
        for x in vecs:
            if form(x, act(A, x)) % q == 0:
                continue
            v = tuple((x[k] + act(A, x)[k]) % q for k in range(d))
            if not any(v):
                continue
            B = mul(A, tv(v, 1))
            if rk(B) == r - 1 and not is_hyp(B):
                good += 1
        induction[(r, L, "clean step exists" if good
                   else "every drop lands hyperbolic")] += 1

    differ = sum(1 for A in dall if done[A] != dall[A])
    return {
        "q": q, "order": len(dall),
        "allTransvections": len(Tall), "allDiameter": max(dall.values()),
        "oneClassTransvections": len(Tone), "oneClassDiameter":
            max(done.values()),
        "lengthsDifferOn": differ,
        "anomalies": len(anom), "hyperbolicMaps": len(hyp),
        "anomaliesEqualHyperbolic": anom == hyp,
        "hyperbolicIsSubset": hyp.issubset(anom),
        "induction": {"%d,%d,%s" % k: v
                      for k, v in sorted(induction.items())},
    }


def main():
    b = study(3)
    a = study(2)

    print("THE LENGTH LAW IS O'MEARA'S, AND THE DOILY BREAKS ITS INDUCTION")
    print("=" * 72)
    print("  RETRACTION: ba7ac5a's 'law' is the classical hyperbolic-map")
    print("  theorem (O'Meara 1978; Callan 1976).")
    print()
    print("     q = 3   anomalies %d, hyperbolic maps %d, equal as SETS: %s"
          % (b["anomalies"], b["hyperbolicMaps"],
             b["anomaliesEqualHyperbolic"]))
    print("     q = 2   anomalies %d, hyperbolic maps %d, equal as SETS: %s"
          % (a["anomalies"], a["hyperbolicMaps"],
             a["anomaliesEqualHyperbolic"]))
    print("             hyperbolic is a strict SUBSET: %s"
          % (a["hyperbolicIsSubset"] and not a["anomaliesEqualHyperbolic"]))
    print()
    print("  So the criterion is exact at q = 3 and fails at q = 2, where %d"
          % (a["anomalies"] - a["hyperbolicMaps"]))
    print("  non-hyperbolic elements still cost residue + 1. The induction:")
    for k in sorted(a["induction"]):
        r, L, tag = k.split(",")
        if int(L) > int(r):
            print("     res %s, len %s  %4d   %s" % (r, L, a["induction"][k],
                                                     tag.upper()))
    print()
    print("  -> a CASCADE: 15 hyperbolic elements poison every escape route")
    print("     out of the 90 at residue 3, which are the only exits for the")
    print("     120 at residue 4. At q = 3 nothing propagates -- 80")
    print("     transvections leave escape routes that 15 do not.")
    print()
    print("  SEPARATE METRIC (the parallel track's literature correction):")
    print("     q=3  all transvections %d, diameter %d"
          % (b["allTransvections"], b["allDiameter"]))
    print("          one class         %d, diameter %d"
          % (b["oneClassTransvections"], b["oneClassDiameter"]))
    print("          lengths differ on %d of %d elements"
          % (b["lengthsDifferOn"], b["order"]))
    print("     q=2  the two coincide exactly, %d differences"
          % a["lengthsDifferOn"])
    print("     -> Ellers' 1994 lambda-length is a NEIGHBOURING problem:")
    print("        direct prior art to cite, but it does not settle these.")
    print()
    print("  WHAT SURVIVES AS OURS: 3f93821's bijection onto the 90 hyperbolic")
    print("  LINES of PG(3,3) and the co-location with the sentinel code's")
    print("  minimum-weight words. That is about this substrate, not about")
    print("  symplectic groups, and the literature sharpens it rather than")
    print("  superseding it.")

    ok = (b["anomalies"] == 91 and b["hyperbolicMaps"] == 91
          and b["anomaliesEqualHyperbolic"]
          and a["anomalies"] == 225 and a["hyperbolicMaps"] == 15
          and not a["anomaliesEqualHyperbolic"] and a["hyperbolicIsSubset"]
          and a["induction"].get("3,4,every drop lands hyperbolic") == 90
          and a["induction"].get("4,5,clean step exists") == 120
          and b["lengthsDifferOn"] == 38264 and a["lengthsDifferOn"] == 0
          and b["oneClassDiameter"] == 6 and b["allDiameter"] == 5)

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "the_length_law_is_omeara.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.length-law-is-omeara.v1",
                "valid": bool(ok),
                "retraction": ("ba7ac5a stated as new that length > residue in "
                               "Sp(4,3) exactly for elements acting as -1 on a "
                               "nondegenerate U and +1 on U^perp; that is the "
                               "classical hyperbolic-map theorem, and at q = 3 "
                               "the anomaly set equals the set of O'Meara "
                               "hyperbolic maps exactly (91 = 91, as sets). The "
                               "novelty claim is withdrawn"),
                "sources": [
                    ("O'Meara, Symplectic Groups, AMS Mathematical Surveys 16, "
                     "1978"),
                    ("Callan, The generation of Sp(F_2) by transvections, "
                     "J. Algebra 42 (1976) 378-390"),
                    ("Pllaha, Volanto, Tirkkonen, Decomposition of Clifford "
                     "Gates, arXiv:2102.11380 -- where the theorem is quoted in "
                     "this form, and the only one of the three actually read "
                     "here"),
                    ("Ellers 1994, one-conjugacy-class lambda-length -- a "
                     "NEIGHBOURING metric, flagged by the parallel track"),
                ],
                "myCharacterisationIsQOddOnly": ("'-1 on a nondegenerate U' "
                                                 "coincides with hyperbolicity "
                                                 "at q = 3 but is empty at q = 2 "
                                                 "where 15 hyperbolic maps "
                                                 "exist; the general criterion "
                                                 "is O'Meara's"),
                "terminologyTrap": ("'hyperbolic map' (<v, vF> = 0 for all v) "
                                    "and 'hyperbolic line' (a 2-space of "
                                    "PG(3,3) on which the form is "
                                    "nondegenerate) are unrelated notions both "
                                    "appearing here, with counts 91 and 90 at "
                                    "q = 3 -- one apart. Do not conflate them"),
                "whatSurvivesAsOurs": ("3f93821's bijection g -> im(g-1) from "
                                       "the 90 residue-2 anomalies onto the 90 "
                                       "hyperbolic LINES, whose polar pairs are "
                                       "BT810's 45 tritangent planes = the "
                                       "sentinel code's 45 minimum-weight "
                                       "words; that co-location is about this "
                                       "substrate, not about symplectic groups, "
                                       "and the literature sharpens it rather "
                                       "than superseding it"),
                "cases": {"q3": b, "q2": a},
                "theDoilyBreaksTheInduction": ("at q = 2 hyperbolicity is a "
                                               "strict subset: 225 anomalies "
                                               "against 15 hyperbolic maps. The "
                                               "classical residue-dropping step "
                                               "succeeds on all of them, but "
                                               "the induction needs it to land "
                                               "non-hyperbolic, and for the 90 "
                                               "at (res 3, len 4) EVERY drop "
                                               "lands hyperbolic; the 120 at "
                                               "(res 4, len 5) then have those "
                                               "as their only exits. The anomaly "
                                               "is a CASCADE from 15 seeds, not "
                                               "225 independent exceptions, and "
                                               "at q = 3 nothing propagates "
                                               "because 80 transvections leave "
                                               "escape routes that 15 do not"),
                "separateMetric": ("Ellers' lambda-length counts transvections "
                                   "from one conjugacy class; at q = 3 that is "
                                   "40 generators with diameter 6 against 80 "
                                   "with diameter 5, and the two lengths differ "
                                   "on 38,264 of 51,840 elements, while at "
                                   "q = 2 they coincide exactly. Prior art to "
                                   "cite, but it does not settle the "
                                   "all-transvection numbers used here"),
                "boundary": ("exhaustive over Sp(4,2) and Sp(4,3): length by "
                             "full BFS, residue by rank(g - I), hyperbolicity "
                             "by testing <v, vF> over every v, comparisons by "
                             "set equality. The primary sources are NOT read "
                             "here -- only the secondhand statement in "
                             "arXiv:2102.11380 -- so the q = 2 discrepancy may "
                             "reflect hypotheses those sources carry rather "
                             "than an error in them. tau_2 is untouched"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
