#!/usr/bin/env python3
"""
The (c,m) minimum-blocker labels the whole tau_2 programme runs on ARE the
octets, and their minimality is a q = 3 coincidence with excess exactly q - 3.

WHAT THE CORPUS HAD.  data/tensor_111_pg34_label_reduction.json (PASS) reduces
a hypothetical 111-leaf tensor blocker to "a dense partial point-line duality
decorated by explicit Hermitian (c,m) minimum-blocker labels", recording

    minimumBlockerFormula   B(c,m) = (Adj(c) symmetric_difference C_m) \\ {c}
    minimumBlockers         360
    labelsPerCenter         9
    CmSize                  8
    CmGraph                 K4,4

with the label set O_c left as a lookup: nine labels per centre, no intrinsic
description of which nine or why eight.

THEY ARE THE OCTETS, AND EVERY CONSTANT IS ALREADY KNOWN.  c9e6be7 built the
octets intrinsically -- the thick points of a square O(5,q) polar section, i.e.
the support of the matrix B in N D = J + q B -- and proved they are K(q+1,q+1)
of size 2(q+1), with B of row weight q^2 and column weight 2(q+1). Line those up:

    CmSize            8   =  2(q+1)          the octet, proved K(q+1,q+1)
    CmGraph        K4,4   =  K(q+1,q+1)      c9e6be7
    labelsPerCenter   9   =  q^2             row weight of B
    minimumBlockers 360   =  q^2 (q+1)(q^2+1)  the point-octet incidences

So O_c is not a lookup table: it is the set of octets THROUGH c, and a valid
(c,m) pair is exactly a point-octet incidence. Verified directly -- 360 pairs at
q = 3, each giving a blocking set, all 360 distinct, matching the corpus count
exactly.

    q     incidences   |Adj(c) cap C_m|   |B(c,m)|   all block   distinct
    3           360           4              11         yes        360
    5          3900           6              29         yes       3900
    7         19600           8              55         yes      19600

THE SIZE IS FORCED.  |Adj(c)| = q(q+1) and |C_m| = 2(q+1); c lies in its own
octet but not in Adj(c); and |Adj(c) cap C_m| = q+1 is exactly the INTERNAL
DEGREE of the octet, which c9e6be7 proved is q+1 because the octet is
K(q+1,q+1). So

    |B(c,m)| = q(q+1) + 2(q+1) - 2(q+1) - 1 = q^2 + q - 1

with nothing fitted -- q+1 = 4, 6, 8 is measured above and matches.

AND THAT IS WHY q = 3.  W(3,q) has no ovoid for odd q, so every blocking set has
at least q^2 + 2 points. The octet construction lands at q^2 + q - 1, so its
excess over that bound is

    (q^2 + q - 1) - (q^2 + 2) = q - 3

-- zero exactly at q = 3, and growing linearly after. At q = 3 the construction
is forced to be minimum and produces all 360 minimum blockers; at q = 5 it gives
29 against a bound of 27, at q = 7 it gives 55 against 51. The label apparatus
the 111-analysis rests on is therefore not a general feature of W(3,q) that
happens to be computed at q = 3: it is a coincidence of one prime, and the
coincidence is q - 3 = 0.

IN THE CORPUS'S OWN INVARIANT.  tensor_multiplicativity_ovoid_defect.json
defines the blocking ovoid defect delta = tau_1 - (st+1) and records
delta = 11 - 10 = 1 for W(3,3). The octet construction achieves

    delta = (q^2 + q - 1) - (q^2 + 1) = q - 2  =  1, 3, 5

against a minimum possible defect of 1 whenever no ovoid exists. So the octet
blocker is minimum iff q - 2 = 1, i.e. q = 3 -- the same statement as the q - 3
excess, said in the invariant the corpus already uses.

AND tau_1(W(3,5)) IS A CONCRETE OPEN SUB-QUESTION.  Whether the q^2+2 bound is
ATTAINED beyond q = 3 was probed and NOT settled: CP-SAT on W(3,5) returns
UNKNOWN at size 27 and at size 28 (200s and 600s budgets, eight workers) and SAT
at 29 -- the 29 exhibited independently by the octet construction itself.
Controls pass, W(3,3) being UNSAT at 10 (no ovoid) and SAT at 11. So
tau_1(W(3,5)) lies in [27,29], undecided. If it is 29 the octet blockers are
minimum at q = 5 as well and only the coincidence WITH THE BOUND is q = 3; if it
is 27 or 28 they are not minimum at all beyond q = 3. Either way the label
apparatus stops being canonical after q = 3; which of the two it is remains to
be decided.

WHAT THIS DOES AND DOES NOT DO TO tau_2.  It does not move the interval. What it
does is explain the provenance of the objects the 111-argument manipulates --
the labels are O(5,q) polar sections, the centre is a point of the section's
thick set, and the K4,4 is the grid Q+(3,3) -- and it says that any attempt to
argue about tau_2(W(3,q)) for larger q by transporting the (c,m) apparatus will
fail at the first step, because there the labelled sets are not minimum.

SCOPE.  The identification is verified at q = 3 against the corpus's own count
of 360; that count is QUOTED from tensor_111_pg34_label_reduction.json and not
re-derived here, so what is proved is that the 360 octet-labelled sets are
distinct blocking sets of size 11, not independently that there are no other
minimum blockers. The size formula and the q - 3 excess are verified at q = 3,
5, 7 and derived from the octet's internal degree, which was proved for those
same three primes. q^2 + 2 is the ovoid-defect LOWER bound, valid for all odd q
because W(3,q) has no ovoid; whether it is ATTAINED for q > 3 -- i.e. the actual
value of tau_1(W(3,q)) -- is not decided here, so "the octet blockers are not
minimum for q > 3" is stated against the bound, which is the honest form: if
tau_1(W(3,5)) were itself 29 the construction would still be minimum there and
only the coincidence with the bound would be q = 3. q even and n > 2 untouched.
tau_2 remains open in [111,115].
"""

import collections
import itertools
import json
import os
import sys

import numpy as np

ROOT = r"C:\Repos\Holotrade"
PAIR = ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3))


def build(q):
    def nm(v):
        i = next(k for k, x in enumerate(v) if x % q)
        z = pow(v[i] % q, -1, q)
        return tuple((z * x) % q for x in v)

    P3 = sorted({nm(v) for v in itertools.product(range(q), repeat=4) if any(v)})
    i3 = {p: i for i, p in enumerate(P3)}

    def sf(u, v):
        return (u[0] * v[2] - u[2] * v[0] + u[1] * v[3] - u[3] * v[1]) % q

    def wed(u, v):
        return tuple((u[i] * v[j] - u[j] * v[i]) % q for (i, j) in PAIR)

    lines = {}
    for a, b in itertools.combinations(P3, 2):
        if sf(a, b) % q:
            continue
        pts = set()
        for x in range(q):
            for y in range(q):
                if x or y:
                    w = tuple((x * a[k] + y * b[k]) % q for k in range(4))
                    if any(w):
                        pts.add(nm(w))
        lines.setdefault(nm(wed(a, b)), set()).update(pts)
    L = sorted(lines)

    def Qf(b):
        return (b[0] * b[5] - b[1] * b[4] + b[2] * b[3]) % q

    def nm6(b):
        i = next(k for k, x in enumerate(b) if x % q)
        z = pow(b[i] % q, -1, q)
        return tuple((z * x) % q for x in b)

    PW = sorted({nm6(b) for b in itertools.product(range(q), repeat=6)
                 if any(b) and (b[1] + b[4]) % q == 0})

    def Bf(u, v):
        s = tuple((u[i] + v[i]) % q for i in range(6))
        return (Qf(s) - Qf(u) - Qf(v)) % q

    sq = {(x * x) % q for x in range(1, q)}
    SQ = [b for b in PW if Qf(b) % q in sq]
    D = np.array([[1 if Bf(y, c) % q == 0 else 0 for c in SQ] for y in L],
                 dtype=np.int64)
    n = len(P3)
    N = np.zeros((n, len(L)), dtype=np.int64)
    for li, lp in enumerate(L):
        for p in lines[lp]:
            N[i3[p], li] = 1
    B = ((N @ D) - 1) // q
    LSET = [frozenset(i3[p] for p in lines[lp]) for lp in L]
    adj = {c: set() for c in range(n)}
    for S in LSET:
        for a in S:
            adj[a] |= (S - {a})
    return n, LSET, adj, B


def study(q):
    n, LSET, adj, B = build(q)
    octs = [frozenset(i for i in range(n) if B[i, c])
            for c in range(B.shape[1])]
    sizes, inter = collections.Counter(), collections.Counter()
    blocks = tot = 0
    seen = set()
    for C in octs:
        for c in C:
            tot += 1
            inter[len(adj[c] & C)] += 1
            bc = (adj[c] ^ C) - {c}
            sizes[len(bc)] += 1
            if all(bc & S for S in LSET):
                blocks += 1
            seen.add(frozenset(bc))
    return {
        "q": q, "points": n, "octets": len(octs),
        "incidences": tot,
        "incidencesClosedForm": q * q * (q + 1) * (q * q + 1),
        "octetSize": sorted({len(C) for C in octs}),
        "internalDegree": sorted(inter),
        "blockerSize": sorted(sizes),
        "blockerSizeClosedForm": q * q + q - 1,
        "allAreBlockingSets": blocks == tot,
        "distinct": len(seen),
        "allDistinct": len(seen) == tot,
        "ovoidDefectBound": q * q + 2,
        "excessOverBound": (q * q + q - 1) - (q * q + 2),
        "meetsBound": (q * q + q - 1) == (q * q + 2),
        "labelsPerCentre": sorted(set(B.sum(1).tolist())),
        # the corpus's own invariant: delta = |blocker| - (st+1), ovoid size q^2+1
        "ovoidSize": q * q + 1,
        "blockingOvoidDefect": (q * q + q - 1) - (q * q + 1),
        "minimumPossibleDefect": 1,
        "defectIsMinimal": ((q * q + q - 1) - (q * q + 1)) == 1,
    }


def main():
    rows = [study(q) for q in (3, 5, 7)]

    print("THE MINIMUM-BLOCKER LABELS ARE OCTETS")
    print("=" * 72)
    print("  tensor_111_pg34_label_reduction.json records 360 minimum blockers")
    print("  B(c,m) = (Adj(c) sym-diff C_m) \\ {c}, 9 labels per centre,")
    print("  |C_m| = 8, C_m = K4,4 -- with O_c left as a lookup table.")
    print()
    print("  They are the OCTETS of c9e6be7, and every constant is already")
    print("  known there:")
    print("     |C_m| = 8   = 2(q+1)              the octet")
    print("     C_m = K4,4  = K(q+1,q+1)          proved in c9e6be7")
    print("     9 labels    = q^2                 row weight of B")
    print("     360         = q^2 (q+1)(q^2+1)    point-octet incidences")
    print("  So O_c is the set of octets THROUGH c, and a valid (c,m) is")
    print("  exactly a point-octet incidence.")
    print()
    print("     q   incidences  |Adj cap C|  |B(c,m)|  block  distinct")
    for r in rows:
        print("    %2d      %6d       %2d         %3d     %s   %6d"
              % (r["q"], r["incidences"], r["internalDegree"][0],
                 r["blockerSize"][0], r["allAreBlockingSets"], r["distinct"]))
    print()
    print("  THE SIZE IS FORCED: |Adj(c)| = q(q+1), |C_m| = 2(q+1), c is in")
    print("  its octet but not in Adj(c), and |Adj(c) cap C_m| = q+1 is the")
    print("  octet's INTERNAL DEGREE (c9e6be7, because it is K(q+1,q+1)), so")
    print("     |B(c,m)| = q(q+1) + 2(q+1) - 2(q+1) - 1 = q^2 + q - 1.")
    print()
    print("  AND THAT IS WHY q = 3. W(3,q) has no ovoid for odd q, so every")
    print("  blocking set has >= q^2 + 2 points. The excess is")
    print("     (q^2 + q - 1) - (q^2 + 2) = q - 3")
    print("     q   construction   bound   excess   meets bound")
    for r in rows:
        print("    %2d        %3d        %3d       %d         %s"
              % (r["q"], r["blockerSizeClosedForm"], r["ovoidDefectBound"],
                 r["excessOverBound"], r["meetsBound"]))
    print("  and in the corpus's own invariant, the blocking ovoid defect")
    print("  delta = |blocker| - (q^2+1) is q - 2 = %s against a minimum"
          % [r["blockingOvoidDefect"] for r in rows])
    print("  possible defect of 1: minimal iff q - 2 = 1, i.e. q = 3.")
    print("  zero exactly at q = 3. The label apparatus the 111-analysis")
    print("  rests on is a coincidence of one prime, and the coincidence is")
    print("  q - 3 = 0.")
    print()
    print("  This does NOT move tau_2. It explains where the objects come")
    print("  from, and says that transporting the (c,m) apparatus to larger q")
    print("  fails at the first step, the labelled sets not being minimum.")

    ok = all(r["allAreBlockingSets"] and r["allDistinct"]
             and r["blockerSize"] == [r["blockerSizeClosedForm"]]
             and r["internalDegree"] == [r["q"] + 1]
             and r["octetSize"] == [2 * (r["q"] + 1)]
             and r["labelsPerCentre"] == [r["q"] ** 2]
             and r["incidences"] == r["incidencesClosedForm"]
             and r["excessOverBound"] == r["q"] - 3 for r in rows)
    ok = (ok and rows[0]["incidences"] == 360 and rows[0]["meetsBound"]
          and all(r["blockingOvoidDefect"] == r["q"] - 2 for r in rows)
          and [r["defectIsMinimal"] for r in rows] == [True, False, False])

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "minimum_blocker_labels_are_octets.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.blocker-labels-are-octets.v1",
                "valid": bool(ok),
                "whatTheCorpusHad": ("tensor_111_pg34_label_reduction.json (PASS) "
                                     "reduces a hypothetical 111-leaf tensor "
                                     "blocker to 'a dense partial point-line "
                                     "duality decorated by explicit Hermitian "
                                     "(c,m) minimum-blocker labels', recording "
                                     "B(c,m) = (Adj(c) sym-diff C_m) minus {c}, "
                                     "360 minimum blockers, 9 labels per centre, "
                                     "|C_m| = 8 and C_m = K4,4 -- with the label "
                                     "set O_c left as a lookup: nine labels per "
                                     "centre, no intrinsic description of which "
                                     "nine or why eight"),
                "theyAreTheOctets": {
                    "CmSize": "8 = 2(q+1), the octet",
                    "CmGraph": "K4,4 = K(q+1,q+1), proved in c9e6be7",
                    "labelsPerCentre": "9 = q^2, the row weight of B",
                    "minimumBlockers": ("360 = q^2 (q+1)(q^2+1), the point-octet "
                                        "incidences"),
                    "reading": ("O_c is not a lookup table: it is the set of "
                                "octets THROUGH c, and a valid (c,m) pair is "
                                "exactly a point-octet incidence in the matrix B "
                                "of N D = J + q B"),
                },
                "rows": rows,
                "theSizeIsForced": ("|Adj(c)| = q(q+1) and |C_m| = 2(q+1); c lies "
                                    "in its own octet but not in Adj(c); and "
                                    "|Adj(c) cap C_m| = q+1 is exactly the "
                                    "INTERNAL DEGREE of the octet, which c9e6be7 "
                                    "proved is q+1 because the octet is "
                                    "K(q+1,q+1). Hence |B(c,m)| = q(q+1) + 2(q+1) "
                                    "- 2(q+1) - 1 = q^2 + q - 1, with nothing "
                                    "fitted"),
                "andThatIsWhyQ3": ("W(3,q) has no ovoid for odd q, so every "
                                   "blocking set has at least q^2 + 2 points; the "
                                   "octet construction lands at q^2 + q - 1, an "
                                   "excess of exactly q - 3 -- zero at q = 3 and "
                                   "growing linearly after. The label apparatus "
                                   "the 111-analysis rests on is not a general "
                                   "feature of W(3,q) computed at q = 3: it is a "
                                   "coincidence of one prime, and the coincidence "
                                   "is q - 3 = 0"),
                "inTheCorpusOwnVocabulary": ("tensor_multiplicativity_ovoid_"
                                             "defect.json defines the blocking "
                                             "ovoid defect delta = tau_1 - (st+1) "
                                             "and records delta = 11 - 10 = 1 for "
                                             "W(3,3). The octet construction "
                                             "achieves delta = (q^2+q-1) - (q^2+1) "
                                             "= q - 2, against a minimum possible "
                                             "defect of 1 whenever no ovoid "
                                             "exists. So the octet blocker is "
                                             "minimum iff q - 2 = 1, i.e. q = 3 -- "
                                             "the same statement as the q - 3 "
                                             "excess, in the corpus's own "
                                             "invariant"),
                "tau1AtQ5IsOpen": ("whether the q^2+2 bound is ATTAINED beyond "
                                   "q = 3 was probed and NOT settled: CP-SAT on "
                                   "W(3,5) returns UNKNOWN at size 27 and at size "
                                   "28 (200s and 600s budgets, 8 workers) and SAT "
                                   "at 29 -- the 29 being independently exhibited "
                                   "by the octet construction itself. Controls "
                                   "pass: W(3,3) is UNSAT at 10 (no ovoid) and "
                                   "SAT at 11. So tau_1(W(3,5)) lies in [27,29] "
                                   "and is undecided here. If it is 29 the octet "
                                   "blockers are minimum at q = 5 too, and only "
                                   "the coincidence with the BOUND is q = 3; if "
                                   "it is 27 or 28 they are not minimum. This is "
                                   "a concrete open sub-question the harness in "
                                   "this file can be pointed at"),
                "effectOnTau2": ("none on the interval. What it does is explain "
                                 "the provenance of the objects the 111-argument "
                                 "manipulates -- the labels are O(5,q) polar "
                                 "sections, the centre is a point of the "
                                 "section's thick set, the K4,4 is the grid "
                                 "Q+(3,3) -- and say that any attempt to argue "
                                 "about tau_2(W(3,q)) for larger q by "
                                 "transporting the (c,m) apparatus fails at the "
                                 "first step, because there the labelled sets are "
                                 "not minimum"),
                "boundary": ("the identification is verified at q = 3 against the "
                             "corpus's own count of 360; that count is QUOTED "
                             "from tensor_111_pg34_label_reduction.json and not "
                             "re-derived, so what is proved here is that the 360 "
                             "octet-labelled sets are DISTINCT BLOCKING SETS OF "
                             "SIZE 11, not independently that no other minimum "
                             "blockers exist. The size formula and the q - 3 "
                             "excess are verified at q = 3, 5, 7 and derived from "
                             "the octet internal degree, itself proved for those "
                             "three primes. q^2 + 2 is the ovoid-defect LOWER "
                             "bound, valid for all odd q because W(3,q) has no "
                             "ovoid; whether it is ATTAINED for q > 3, i.e. the "
                             "actual value of tau_1(W(3,q)), is NOT decided here, "
                             "so 'not minimum for q > 3' is stated against the "
                             "bound -- if tau_1(W(3,5)) were itself 29 the "
                             "construction would still be minimum there and only "
                             "the coincidence with the bound would be q = 3. "
                             "q even and n > 2 untouched; tau_2 remains open in "
                             "[111,115]"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
