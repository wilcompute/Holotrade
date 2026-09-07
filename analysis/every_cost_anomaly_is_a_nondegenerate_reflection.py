#!/usr/bin/env python3
"""
One law covers all 91 cost anomalies of Sp(4,3), and it corrects the dichotomy
I published one commit earlier.

WHAT 3f93821 GOT RIGHT AND WHAT IT OVER-READ.  It established, by set equality,
that g -> im(g - 1) is a bijection from the 90 residue-2 length-3 anomalies onto
the 90 hyperbolic lines of PG(3,3). That stands. But it closed with a dichotomy
-- "the 130 lines split into the cheap generators (40 isotropic) and the
expensive anomalies (90 hyperbolic), and nothing else" -- and that is an
over-read. Breaking the residue-2 elements down properly:

    image ISOTROPIC    length 2 :  720      length 3 :   0
    image HYPERBOLIC   length 2 : 1260      length 3 :  90
                                                 total 2070

So a hyperbolic image is NECESSARY for the anomaly and nowhere near sufficient:
each hyperbolic line carries fifteen residue-2 elements and the profile is the
same on every one of the ninety,

    {length 2 : 14,  length 3 : 1}    on all 90 lines,

so the bijection holds because each line contributes exactly ONE distinguished
element, not because hyperbolic lines are expensive as a class. Fourteen
fifteenths of them are cheap.

THE DISTINGUISHED ELEMENT IS THE LOCAL CENTRE, AND THAT IS THE WHOLE LAW.  The
one expensive element on a hyperbolic line L acts as -1 on L and +1 on L^perp:
it is the centre of the SL(2,3) = Sp(L) acting there. And Sp(4,3)'s other
anomaly, the single length-5 element, is -I, the centre of Sp(4,3) itself. Both
are the same shape, so state it once and test it:

    g has length > residue  <=>  g is -1 on a nondegenerate U and +1 on U^perp,
                                 for some nondegenerate U =/= 0.

    nondegenerate U of dim 2 (the hyperbolic lines)     90
    U = V                                                1
    predicted set                                       91
    anomaly set                                         91
    predicted == anomaly, as SETS                      yes

dim U = 1 and 3 contribute nothing because a symplectic space has no
odd-dimensional nondegenerate subspace. So the count 91 = 90 + 1 is not two
facts, it is one fact evaluated at the two available dimensions.

AND IT EXPLAINS THE ISOTROPIC CASE MECHANICALLY.  If L is totally isotropic then
L is contained in L^perp, so "-1 on L and +1 on L^perp" is self-contradictory and
the anomalous element simply does not exist there. The 720 isotropic-image
elements are not cheap by luck or by counting; they are cheap because the
expensive shape cannot be built on an isotropic line at all.

THE LAW IS PROVABLY q-ODD.  At q = 2, -1 = +1, so the predicted set is empty --
yet Sp(4,2) has 225 anomalies. The characterisation therefore fails completely
at q = 2 rather than degrading, which is independent support for 6bb8975's
reading: the doily's anomalies come from somewhere else, and its lack of a
centre is the same absence seen one level down.

WHAT SURVIVES FOR THE ARCHITECTURE.  The co-location claim survives, in a
sharper form. The extra instruction is not charged to the hyperbolic lines as a
class; it is charged to one canonical involution per line, and those ninety
involutions are indexed by the ninety lines whose polar pairs are the sentinel
code's minimum words. The ISA overpays on exactly one element per
minimum-weight object, and on the centre.

SCOPE.  Exhaustive over all 51,840 elements: length by full BFS, residue by
rank(g - I), image type by the form. The iff is set equality against a set built
independently from nondegenerate subspaces, not a count match. Verified at q = 3;
shown to FAIL at q = 2, and not tested at any other q. tau_2 is untouched.
"""

import collections
import itertools
import json
import os
import sys

ROOT = r"C:\Repos\Holotrade"


def analyse(q):
    d = 4

    def mul(A, B):
        return tuple(tuple(sum(A[i][k] * B[k][j] for k in range(d)) % q
                           for j in range(d)) for i in range(d))

    I = tuple(tuple(1 if i == j else 0 for j in range(d)) for i in range(d))

    def form(u, v):
        return (u[0] * v[2] - u[2] * v[0] + u[1] * v[3] - u[3] * v[1]) % q

    E = [tuple(1 if k == j else 0 for k in range(d)) for j in range(d)]
    T = set()
    for vv in itertools.product(range(q), repeat=d):
        if not any(vv):
            continue
        for lam in range(1, q):
            M = tuple(tuple(((1 if i == j else 0)
                             + lam * form(E[j], vv) * vv[i]) % q
                            for j in range(d)) for i in range(d))
            if M != I:
                T.add(M)
    T = sorted(T)
    dist, fr, dia = {I: 0}, [I], 0
    while fr:
        nx = []
        for A in fr:
            for M in T:
                C = mul(M, A)
                if C not in dist:
                    dist[C] = dia + 1
                    nx.append(C)
        fr = nx
        if nx:
            dia += 1

    def rk(rows):
        R = [list(x) for x in rows]
        r = 0
        for c in range(d):
            p = next((i for i in range(r, len(R)) if R[i][c] % q), None)
            if p is None:
                continue
            R[r], R[p] = R[p], R[r]
            iv = pow(R[r][c], -1, q)
            R[r] = [(x * iv) % q for x in R[r]]
            for i in range(len(R)):
                if i != r and R[i][c] % q:
                    f = R[i][c]
                    R[i] = [(R[i][j] - f * R[r][j]) % q for j in range(d)]
            r += 1
        return r

    def imgbasis(A):
        M = [[(A[i][j] - (1 if i == j else 0)) % q for j in range(d)]
             for i in range(d)]
        cols = [tuple(M[i][j] for i in range(d)) for j in range(d)]
        b = []
        for c in cols:
            if rk(b + [c]) == len(b) + 1:
                b.append(c)
        return b

    anom = {A for A, L in dist.items() if L > len(imgbasis(A))}

    def nmv(v):
        i = next(k for k, x in enumerate(v) if x % q)
        z = pow(v[i] % q, -1, q)
        return tuple((z * x) % q for x in v)

    def spanpts(b):
        S = set()
        for co in itertools.product(range(q), repeat=len(b)):
            if not any(co):
                continue
            w = tuple(sum(co[i] * b[i][k] for i in range(len(b))) % q
                      for k in range(d))
            if any(w):
                S.add(nmv(w))
        return frozenset(S)

    split = collections.Counter()
    perline = collections.defaultdict(collections.Counter)
    for A, L in dist.items():
        b = imgbasis(A)
        if len(b) != 2:
            continue
        iso = form(b[0], b[1]) % q == 0
        split[("isotropic" if iso else "hyperbolic", L)] += 1
        if not iso:
            perline[spanpts(b)][L] += 1
    profiles = collections.Counter(tuple(sorted(c.items()))
                                   for c in perline.values())

    # the predicted set: -1 on a nondegenerate U, +1 on U^perp
    vecs = [v for v in itertools.product(range(q), repeat=d) if any(v)]
    pred, seen = set(), set()
    for a, b in itertools.combinations(vecs, 2):
        if form(a, b) % q == 0:
            continue
        S = spanpts([a, b])
        if S in seen:
            continue
        seen.add(S)
        P = [v for v in vecs if form(v, a) % q == 0 and form(v, b) % q == 0]
        pb = []
        for v in P:
            if rk(pb + [v]) == len(pb) + 1:
                pb.append(v)
        B = [a, b] + pb
        Mb = tuple(tuple(B[j][i] for j in range(d)) for i in range(d))
        Aug = [[Mb[i][j] for j in range(d)]
               + [1 if i == j else 0 for j in range(d)] for i in range(d)]
        r = 0
        for c in range(d):
            p = next((i for i in range(r, d) if Aug[i][c] % q), None)
            Aug[r], Aug[p] = Aug[p], Aug[r]
            iv = pow(Aug[r][c], -1, q)
            Aug[r] = [(x * iv) % q for x in Aug[r]]
            for i in range(d):
                if i != r and Aug[i][c] % q:
                    f = Aug[i][c]
                    Aug[i] = [(Aug[i][j] - f * Aug[r][j]) % q
                              for j in range(2 * d)]
            r += 1
        Minv = tuple(tuple(Aug[i][d + j] for j in range(d)) for i in range(d))
        D = tuple(tuple(((-1) % q if (i == j and i < 2)
                         else (1 if i == j else 0)) for j in range(d))
                  for i in range(d))
        g = mul(Mb, mul(D, Minv))
        if g != I:
            pred.add(g)
    nondeg2 = len(seen)
    minusI = tuple(tuple((-1 if i == j else 0) % q for j in range(d))
                   for i in range(d))
    if minusI != I:
        pred.add(minusI)

    return {
        "q": q, "order": len(dist), "matrixDiameter": dia,
        "anomalies": len(anom),
        "residue2Split": {"%s,%d" % k: v for k, v in sorted(split.items())},
        "perHyperbolicLineProfiles": {str(dict(s)): n
                                      for s, n in profiles.items()},
        "nondegenerate2Spaces": nondeg2,
        "predictedSetSize": len(pred),
        "predictedEqualsAnomalySet": pred == anom,
        "allPredictedAreInGroup": all(g in dist for g in pred),
    }


def main():
    b = analyse(3)
    a = analyse(2)

    print("EVERY COST ANOMALY IS A NONDEGENERATE REFLECTION")
    print("=" * 72)
    print("  residue-2 elements of Sp(4,3), by image type and length:")
    for k in sorted(b["residue2Split"]):
        t, L = k.split(",")
        print("     %-11s length %s : %5d" % (t, L, b["residue2Split"][k]))
    print("     -> isotropic image is NEVER anomalous; hyperbolic is")
    print("        necessary and far from sufficient")
    print()
    print("  per hyperbolic line, the length profile of its 15 residue-2")
    print("  elements: %s" % b["perHyperbolicLineProfiles"])
    print("     -> exactly ONE distinguished element per line, uniformly")
    print()
    print("  THE LAW: length > residue <=> g is -1 on a nondegenerate U")
    print("           and +1 on U^perp, for some nondegenerate U =/= 0")
    print()
    print("     nondegenerate 2-spaces (hyperbolic lines) %4d"
          % b["nondegenerate2Spaces"])
    print("     plus U = V                                   1")
    print("     predicted set                             %4d"
          % b["predictedSetSize"])
    print("     anomaly set                               %4d" % b["anomalies"])
    print("     predicted == anomaly, as SETS:            %s"
          % b["predictedEqualsAnomalySet"])
    print()
    print("  dim U = 1 and 3 contribute nothing: a symplectic space has no")
    print("  odd-dimensional nondegenerate subspace. And if L is isotropic")
    print("  then L <= L^perp, so '-1 on L, +1 on L^perp' is contradictory --")
    print("  the expensive shape cannot be built there at all.")
    print()
    print("  AT q = 2 THE LAW FAILS COMPLETELY: -1 = +1, so the predicted set")
    print("  has %d elements, while Sp(4,2) has %d anomalies. Independent"
          % (a["predictedSetSize"], a["anomalies"]))
    print("  support for 6bb8975: the doily's anomalies come from elsewhere,")
    print("  and its missing centre is the same absence one level down.")
    print()
    print("  CORRECTION to 3f93821: its closing dichotomy -- 40 isotropic")
    print("  cheap, 90 hyperbolic expensive, nothing else -- is an over-read.")
    print("  The bijection stands; the class-level dichotomy does not.")

    ok = (b["anomalies"] == 91 and b["predictedSetSize"] == 91
          and b["predictedEqualsAnomalySet"] and b["allPredictedAreInGroup"]
          and b["nondegenerate2Spaces"] == 90
          and b["residue2Split"].get("isotropic,3", 0) == 0
          and b["residue2Split"]["isotropic,2"] == 720
          and b["residue2Split"]["hyperbolic,2"] == 1260
          and b["residue2Split"]["hyperbolic,3"] == 90
          and len(b["perHyperbolicLineProfiles"]) == 1
          and a["predictedSetSize"] == 0 and a["anomalies"] == 225
          and not a["predictedEqualsAnomalySet"])

    if "--write" in sys.argv:
        p = os.path.join(
            ROOT, "data",
            "every_cost_anomaly_is_a_nondegenerate_reflection.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.anomaly-is-nondegenerate-reflection.v1",
                "valid": bool(ok),
                "theLaw": ("g in Sp(4,3) has transvection length > residue(g) "
                           "if and only if g acts as -1 on a nondegenerate "
                           "subspace U =/= 0 and +1 on U^perp"),
                "cases": {"q3": b, "q2": a},
                "whyTheCountIsOneFact": ("dim U = 2 gives the 90 hyperbolic "
                                         "lines and dim U = 4 gives -I; dim 1 "
                                         "and 3 contribute nothing because a "
                                         "symplectic space has no "
                                         "odd-dimensional nondegenerate "
                                         "subspace, so 91 = 90 + 1 is one fact "
                                         "evaluated at the two available "
                                         "dimensions, not two facts"),
                "whyIsotropicIsAlwaysCheap": ("a totally isotropic L satisfies "
                                              "L <= L^perp, so '-1 on L and +1 "
                                              "on L^perp' is self-contradictory "
                                              "and the anomalous element does "
                                              "not exist there; the 720 "
                                              "isotropic-image elements are "
                                              "cheap because the expensive "
                                              "shape cannot be built, not by "
                                              "counting"),
                "correctionToMyPriorCommit": ("3f93821's bijection onto the 90 "
                                              "hyperbolic lines stands, but its "
                                              "closing dichotomy -- 40 isotropic "
                                              "cheap, 90 hyperbolic expensive, "
                                              "nothing else -- is an over-read: "
                                              "each hyperbolic line carries 15 "
                                              "residue-2 elements with profile "
                                              "{2:14, 3:1}, so 14/15 of them are "
                                              "cheap and the dichotomy is not a "
                                              "class-level fact"),
                "qOddOnly": ("at q = 2, -1 = +1 so the predicted set is empty "
                             "while Sp(4,2) has 225 anomalies; the "
                             "characterisation fails completely rather than "
                             "degrading, which independently supports 6bb8975's "
                             "reading that the doily's anomalies have another "
                             "source and its missing centre is the same absence "
                             "one level down"),
                "architecturalReading": ("the co-location claim survives in a "
                                         "sharper form: the extra instruction is "
                                         "charged not to the hyperbolic lines as "
                                         "a class but to one canonical "
                                         "involution per line, and those ninety "
                                         "involutions are indexed by the ninety "
                                         "lines whose polar pairs are the "
                                         "sentinel code's minimum words -- the "
                                         "ISA overpays on exactly one element "
                                         "per minimum-weight object, and on the "
                                         "centre"),
                "boundary": ("exhaustive over all 51,840 elements: length by "
                             "full BFS, residue by rank(g - I), image type by "
                             "the form. The iff is set equality against a set "
                             "built independently from nondegenerate subspaces, "
                             "not a count match. Verified at q = 3, shown to "
                             "FAIL at q = 2, untested at any other q. tau_2 is "
                             "untouched"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
