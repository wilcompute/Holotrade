#!/usr/bin/env python3
"""
Globally: two non-collinear points of W(3,q) lie on exactly ONE octet, two
collinear points on exactly q, and two octets meet in 0 or 2 points -- never 1,
never more.

WHERE THIS FITS.  aa8691a proved the LOCAL statement: at each point c the q^2
octets through c and the q(q+1) neighbours of c form an affine plane of order q,
with the pencil as its parallelism. That describes one point's neighbourhood. It
says nothing about how two points see each other, and the point-octet geometry
as a whole was never measured. This measures it.

THE PARAMETERS, with the octet count quoted not re-derived.  The point-octet
incidence structure has

    v = (q+1)(q^2+1)   points        b = q^2(q^2+1)/2   octets
    k = 2(q+1)         per octet     r = q^2            per point

and v r = b k. The octet count is the middle orbit of the O(5,q) census
(q+1)(q^2+1) / q^2(q^2+1)/2 / q^2(q^2-1)/2 already in this track -- the 40/45/36
split at q = 3 -- and |C_m| = 2(q+1) and r = q^2 are from
the_minimum_blocker_labels_are_octets.py. None of that is re-derived here.

IT IS NOT A 2-DESIGN, and that is the interesting part.  A 2-design would need
lambda = r(k-1)/(v-1) = q(2q+1)/(q^2+q+1), which is not an integer at q = 3.
The pair degree is not constant -- it splits exactly on collinearity, and both
values are as clean as they could be:

    two NON-COLLINEAR points lie on exactly  1  octet
    two COLLINEAR     points lie on exactly  q  octets

verified over ALL pairs at q = 3, 5, 7. The counts close against r(k-1):
q(q+1) collinear neighbours contributing q each, plus q^3 non-collinear
contributing 1 each, is q^2(q+1) + q^3 = 2q^3 + q^2 = q^2(2q+1) = r(k-1).

WHERE EACH LAW ACTUALLY COMES FROM -- and one of them is much cheaper than it
first looked.

The COLLINEAR law is the local theorem in disguise. In the affine plane at x the
neighbour y is a LINE, and the octets through x containing y are exactly the
plane points lying on it. So "two collinear points lie on q octets" is precisely
the axiom that every line of AG(2,q) carries q points, and aa8691a proved it.

The NON-COLLINEAR law was first written up here as new -- "the octets form a
linear space on the non-collinearity graph" -- and that was an OVER-READ of a
fact this track already owned. the_cost_anomalies_are_the_tritangent_structure.py
(3f93821, 2026-09-02) records that PG(3,3)'s 130 lines split into 40 isotropic
and 90 hyperbolic and that the 45 octets are exactly L u L^perp for L
hyperbolic. Given that, the law is one line: two non-collinear points are
non-perpendicular, so the line they span is hyperbolic, and a hyperbolic line L
determines the single octet L u L^perp. Nothing about linear spaces is needed
and no new content is involved. The framing is withdrawn.

WHAT DOES SURVIVE from that direction is the q-GENERALISATION. The corpus states
L u L^perp at q = 3, with the count 90. Verified here at q = 3, 5 and 7: the two
sides of every octet's K(q+1,q+1) are exactly the HYPERBOLIC LINES of PG(3,q),
all q^2(q^2+1) of them -- 90, 650, 2450 -- matching
(q^2+1)(q^2+q+1) - (q+1)(q^2+1) = q^2(q^2+1) exactly. So an octet is a polarity
pair of hyperbolic lines at every odd q tested, not only at q = 3.

AND THE BLOCKS MEET IN 0 OR 2.  Two distinct octets share 0 or 2 points at every
q tested, never 1 and never more, and when they share 2 those two are COLLINEAR.
The collinearity half is forced rather than observed: a shared non-collinear
pair would lie on two octets, contradicting the law that it lies on one. What is
measured, and not derived here, is that the intersection never exceeds 2.

SCOPE.  Exhaustive over all C(v,2) point pairs and all C(b,2) octet pairs at
q = 3, 5, 7 -- 780, 12090 and 79800 point pairs, 990, 52650 and 749700 octet
pairs. Nothing sampled. q = 9 and beyond are not run and even q is untouched.
tau_2 is untouched and stays open in [111, 115].
"""

import argparse
import collections
import importlib.util
import itertools
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


def halves_are_hyperbolic_lines(q, octs, adj):
    """The two sides of each octet's K(q+1,q+1), against the hyperbolic lines
    of PG(3,q) built independently from the form."""
    def nm(v):
        i = next(k for k, x in enumerate(v) if x % q)
        z = pow(v[i] % q, -1, q)
        return tuple((z * x) % q for x in v)

    P3 = sorted({nm(v) for v in itertools.product(range(q), repeat=4)
                 if any(v)})
    i3 = {p: i for i, p in enumerate(P3)}

    def sf(u, v):
        return (u[0] * v[2] - u[2] * v[0] + u[1] * v[3] - u[3] * v[1]) % q

    alllines = set()
    for a, b in itertools.combinations(P3, 2):
        S = set()
        for x in range(q):
            for y in range(q):
                if x or y:
                    w = tuple((x * a[k] + y * b[k]) % q for k in range(4))
                    if any(w):
                        S.add(i3[nm(w)])
        alllines.add(frozenset(S))
    hyp = {L for L in alllines
           if all(sf(P3[x], P3[y]) % q
                  for x, y in itertools.combinations(sorted(L), 2))}

    halves = set()
    for C in octs:
        cs = sorted(C)
        seen, comp = set(), []
        for p in cs:
            if p in seen:
                continue
            side = frozenset([p] + [y for y in cs
                                    if y != p and y not in adj[p]])
            comp.append(side)
            seen |= side
        if len(comp) != 2 or {len(x) for x in comp} != {q + 1}:
            return None
        halves |= set(comp)
    return {
        "allLines": len(alllines),
        "totallyIsotropic": (q + 1) * (q * q + 1),
        "hyperbolic": len(hyp),
        "hyperbolicClosedForm": q * q * (q * q + 1),
        "octetHalves": len(halves),
        "halvesAreExactlyTheHyperbolicLines": halves == hyp,
    }


def study(q, mod):
    n, LSET, adj, B = mod.build(q)
    octs = [frozenset(i for i in range(n) if B[i, c])
            for c in range(B.shape[1])]
    v, b = n, len(octs)
    k = {len(C) for C in octs}
    r = {sum(1 for C in octs if p in C) for p in range(n)}

    through = [[] for _ in range(n)]
    for j, C in enumerate(octs):
        for p in C:
            through[p].append(j)

    coll, noncoll = collections.Counter(), collections.Counter()
    for x in range(n):
        sx = set(through[x])
        for y in range(x + 1, n):
            c = len(sx & set(through[y]))
            (coll if y in adj[x] else noncoll)[c] += 1

    inter = collections.Counter()
    two_are_collinear = True
    for i, j in itertools.combinations(range(b), 2):
        s = octs[i] & octs[j]
        inter[len(s)] += 1
        if len(s) == 2:
            a, bb = sorted(s)
            if bb not in adj[a]:
                two_are_collinear = False

    return {
        "q": q,
        "v": v, "b": b,
        "k": sorted(k), "r": sorted(r),
        "vrEqualsBk": v * max(r) == b * max(k),
        "bClosedForm": q * q * (q * q + 1) // 2,
        "bMatchesClosedForm": b == q * q * (q * q + 1) // 2,
        "collinearPairDegrees": dict(coll),
        "nonCollinearPairDegrees": dict(noncoll),
        "collinearLambda": (sorted(coll)[0] if len(coll) == 1 else None),
        "nonCollinearLambda": (sorted(noncoll)[0] if len(noncoll) == 1
                               else None),
        "collinearPairs": sum(coll.values()),
        "nonCollinearPairs": sum(noncoll.values()),
        "blockIntersections": dict(sorted(inter.items())),
        "intersectionsAreZeroOrTwo": set(inter) <= {0, 2},
        "sharedPairsAreCollinear": two_are_collinear,
        # r(k-1) split: q(q+1) neighbours at q each, q^3 non-neighbours at 1
        "countingIdentity": (q * (q + 1) * q + q ** 3
                             == q * q * (2 * q + 1)),
        "notATwoDesign": (q * q * (2 * q + 1)) % (v - 1) != 0,
        "hyperbolic": halves_are_hyperbolic_lines(q, octs, adj),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--qs", type=int, nargs="+", default=[3, 5, 7])
    args = ap.parse_args()

    mod = octet_module()
    rows = [study(q, mod) for q in args.qs]

    print("THE OCTET PAIR LAWS ARE q-GENERAL")
    print("=" * 74)
    print("   q      v      b   k   r   vr=bk   lambda(non-coll)  lambda(coll)"
          "   blocks meet in")
    for x in rows:
        print("  %2d  %5d  %5d  %2d  %3d   %5s   %14s  %11s   %s"
              % (x["q"], x["v"], x["b"], x["k"][0], x["r"][0],
                 x["vrEqualsBk"], x["nonCollinearLambda"],
                 x["collinearLambda"],
                 sorted(x["blockIntersections"])))
    print()
    print("  two NON-COLLINEAR points lie on exactly 1 octet;")
    print("  two COLLINEAR points lie on exactly q; blocks meet in 0 or 2.")
    print()
    print("  the collinear law is the LOCAL theorem in disguise: in the affine")
    print("  plane at x the neighbour y is a LINE, and the octets through x")
    print("  containing y are the plane points on it -- so 'q octets' is just")
    print("  'every line of AG(2,q) has q points', already proved in aa8691a.")
    print("  The NON-COLLINEAR law is NOT new: octet = L u L^perp is already")
    print("  ours (3f93821), and two non-collinear points span a unique")
    print("  hyperbolic line, which names the octet. Framing withdrawn.")
    print("  What survives is that the octet HALVES are exactly the hyperbolic")
    print("  lines of PG(3,q) at q = 3, 5, 7 -- 90, 650, 2450 = q^2(q^2+1) --")
    print("  so the L u L^perp reading is q-general, not q = 3 only.")
    print()
    print("  counting closes: q(q+1) neighbours at q each plus q^3")
    print("  non-neighbours at 1 each = 2q^3+q^2 = q^2(2q+1) = r(k-1).")

    print()
    for x in rows:
        h = x["hyperbolic"]
        print("  q=%d: PG(3,q) has %d lines = %d isotropic + %d hyperbolic"
              "  (q^2(q^2+1)=%d);  octet halves = %d;  HALVES ARE THE"
              " HYPERBOLIC LINES: %s"
              % (x["q"], h["allLines"], h["totallyIsotropic"], h["hyperbolic"],
                 h["hyperbolicClosedForm"], h["octetHalves"],
                 h["halvesAreExactlyTheHyperbolicLines"]))

    ok = all(x["hyperbolic"]["halvesAreExactlyTheHyperbolicLines"]
             and x["hyperbolic"]["hyperbolic"] == x["hyperbolic"]["hyperbolicClosedForm"]
             and x["nonCollinearLambda"] == 1 and x["collinearLambda"] == x["q"]
             and x["intersectionsAreZeroOrTwo"] and x["sharedPairsAreCollinear"]
             and x["vrEqualsBk"] and x["bMatchesClosedForm"]
             and x["countingIdentity"] and x["k"] == [2 * (x["q"] + 1)]
             and x["r"] == [x["q"] ** 2]
             for x in rows)
    print()
    print("VALID: %s" % ok)

    if args.write:
        assert ok, "checks failed -- refusing to write"
        rec = {
            "schema": "holotrade.octet-pair-laws-q-general.v1",
            "valid": True,
            "qs": args.qs,
            "perQ": rows,
            "theLaws": (
                "in the point-octet geometry of W(3,q): two NON-COLLINEAR points "
                "lie on exactly ONE common octet; two COLLINEAR points lie on "
                "exactly q; and two distinct octets meet in 0 or 2 points, never "
                "1 and never more. Verified over all point pairs and all octet "
                "pairs at q = 3, 5, 7."),
            "notATwoDesign": (
                "the structure is NOT a 2-design and that is the point. A 2-design "
                "would need lambda = r(k-1)/(v-1) = q(2q+1)/(q^2+q+1), not an "
                "integer at q = 3. The pair degree instead splits exactly on "
                "collinearity, and both values are as clean as possible."),
            "theNonCollinearLawIsAnOverReadWithdrawn": (
                "this file first presented the non-collinear law as new content, "
                "saying the octets form a LINEAR SPACE on the non-collinearity "
                "graph. That is an over-read of a fact this track already owned. "
                "the_cost_anomalies_are_the_tritangent_structure.py (3f93821, "
                "2026-09-02) records that PG(3,3)'s 130 lines split 40 isotropic "
                "and 90 hyperbolic and that the 45 octets are exactly L u L^perp "
                "for L hyperbolic. Given that, the law is one line: two "
                "non-collinear points are non-perpendicular, so the line they "
                "span is hyperbolic, and a hyperbolic line L determines the "
                "single octet L u L^perp. The linear-space framing is WITHDRAWN "
                "and the law is retained as a consequence, not a discovery."),
            "whatSurvivesIsTheQGeneralisation": (
                "the corpus states octet = L u L^perp at q = 3, with the count 90. "
                "Verified here at q = 3, 5, 7: the two sides of every octet's "
                "K(q+1,q+1) are exactly the HYPERBOLIC LINES of PG(3,q), all "
                "q^2(q^2+1) of them -- 90, 650, 2450 -- matching "
                "(q^2+1)(q^2+q+1) - (q+1)(q^2+1) = q^2(q^2+1). So an octet is a "
                "polarity pair of hyperbolic lines at every odd q tested, not only "
                "at q = 3. That generalisation, the collinear law's derivation "
                "from the local plane, and the measured bound that two octets meet "
                "in at most 2 points are what this file actually contributes."),
            "halfOfItIsTheLocalTheorem": (
                "in the affine plane at x proved in aa8691a, the neighbour y is a "
                "LINE and the octets through x that contain y are exactly the "
                "plane points lying on it. So 'two collinear points lie on q "
                "octets' is precisely the axiom that every line of AG(2,q) carries "
                "q points, and is already proved. The non-collinear law is the "
                "consequence of octet = L u L^perp, which this track already "
                "owned -- see theNonCollinearLawIsAnOverReadWithdrawn."),
            "theCollinearityOfSharedPairsIsForced": (
                "when two octets share 2 points those points are collinear, but "
                "that half is FORCED, not observed: a shared non-collinear pair "
                "would lie on two octets, contradicting the law that it lies on "
                "exactly one. What is measured and not derived here is that the "
                "intersection never exceeds 2."),
            "countingCloses": (
                "r(k-1) = q^2(2q+1) splits as q(q+1) collinear neighbours "
                "contributing q each plus q^3 non-collinear contributing 1 each: "
                "q^2(q+1) + q^3 = 2q^3 + q^2. The two laws are therefore "
                "consistent with the incidence count, which they would not be if "
                "either constant were wrong."),
            "priorArtQuotedNotRederived": (
                "the octet count b = q^2(q^2+1)/2 is the middle orbit of the "
                "O(5,q) census (q+1)(q^2+1) / q^2(q^2+1)/2 / q^2(q^2-1)/2 already "
                "in this track -- the 40/45/36 split at q = 3, recorded in "
                "the_polar_apparatus_is_rank_two_only.py -- and |C_m| = 2(q+1) "
                "with q^2 octets through each point are from "
                "the_minimum_blocker_labels_are_octets.py (aa42b38, 6f35762). The "
                "local affine plane is aa8691a. This file calls that module's own "
                "build() and adds only the pair laws."),
            "boundary": (
                "exhaustive over ALL point pairs and ALL octet pairs at q = 3, 5, "
                "7 -- 780, 12090 and 79800 point pairs and 990, 52650 and 749700 "
                "octet pairs -- with nothing sampled and nothing transported by "
                "the group. q = 9 and beyond are not run; even q is untouched. The "
                "bound that two octets meet in at most 2 points is measured at "
                "these three q and is not proved in general. tau_2 is untouched "
                "and stays open in [111, 115]."),
        }
        p = os.path.join(ROOT, "data", "octet_pair_laws_q_general.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=2)
        print("written: %s" % p)


if __name__ == "__main__":
    main()
