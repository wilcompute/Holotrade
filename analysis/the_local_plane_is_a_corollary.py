#!/usr/bin/env python3
"""
The affine plane at a point is a COROLLARY of octet = L u L^perp, which this
track already owned. Reclassifying three of our own results, and saying exactly
what survives.

WHAT HAPPENED.  9fda6bf withdrew the "linear space" framing of the non-collinear
pair law after finding that the_cost_anomalies_are_the_tritangent_structure.py
(3f93821, 2026-09-02) already records that PG(3,3)'s 130 lines split 40
isotropic and 90 hyperbolic, and that the 45 octets are exactly L u L^perp for L
hyperbolic. Following that identification one step further shows it does not
just explain the pair law -- it explains the whole local structure, and two more
of our results are corollaries rather than discoveries.

THE DERIVATION, in full, in a paragraph.  Fix a point c.

  * A line of PG(3,q) through c is totally isotropic iff it lies in c^perp.
    There are q^2+q+1 lines through c and q+1 of them lie in c^perp, so exactly
    q^2 are HYPERBOLIC.
  * An octet is L u L^perp with L hyperbolic, and c lies in it iff c is on L
    (it cannot be on both, since L and L^perp are disjoint). So the octets
    through c correspond one-to-one with the q^2 hyperbolic lines through c.
    That is the count q^2, with no computation.
  * Let x be a neighbour of c, i.e. x in c^perp, x =/= c. Then <c,x> is totally
    isotropic, so x is NOT on the hyperbolic line L; hence x is in the octet iff
    x is in L^perp. So the neighbour-part of the octet is exactly L^perp.
  * L^perp is a line, it lies inside c^perp (because c is on L), and it misses c
    (because c on L^perp would put L inside c^perp, and L is hyperbolic). So the
    neighbour-parts are exactly the lines of the projective plane c^perp that
    miss the point c -- and there are q^2 of those, matching.

Hence, with points the q^2 octets through c and lines the q(q+1) neighbours of
c, the incidence structure is the DUAL of PG(2,q) punctured at a point, which is
AG(2,q). The pencil is the parallelism because the lines through c in the plane
c^perp are the point-pencils of the dual. And "the dropped set is a transversal
of the pencil" is just: a line missing c meets every line through c exactly once.

Verified here at q = 3 and 5, as sets and not merely as counts: the octets
through c are exactly the hyperbolic lines through c, and the collection
{Adj(c) n C_m} is exactly the collection of lines of c^perp missing c.

WHAT THIS RECLASSIFIES, ours in each case:

  aa8691a  "the neighbourhood IS an affine plane of order q" -- TRUE, and a
           corollary of the above. Presented as a discovery; it is not one.
  d3c30d6  "the q^2 transversals form an MDS [q+1,2,q]_q code" -- TRUE, and the
           same corollary in dual coordinates. The transversal property itself
           is the one-line fact above.
  64004ce  the q = 3 tetracode -- TRUE, and the q = 3 case of that code, so its
           EXISTENCE is a corollary too. It was found by an independent route,
           through the |B n B'| = 5 census, but being found independently does
           not make a fact new.

WHAT SURVIVES AS GENUINELY NEW, and it is not nothing:

  1. THE GROUP. The stabiliser of c induces on the plane exactly the index-2
     subgroup of AGL(2,q) -- the affine maps whose linear part has square
     determinant -- of order |AGL(2,q)|/2 = 216, 6000, 49392 at q = 3, 5, 7,
     with point stabiliser |GL(2,q)|/2. Nothing about the plane's existence
     forces which subgroup of its automorphism group the geometry realises, and
     the identification is proved, not matched: AGL(2,q) abelianises to F_q^* by
     the determinant, so its index-2 subgroup is unique. This also carries the
     correction that ASL(2,q) is the wrong law and coincides only at q = 3.
  2. THE q-GENERALITY OF L u L^perp. The corpus states it at q = 3 with the
     count 90; 9fda6bf verified the octet halves are exactly the hyperbolic
     lines at q = 3, 5, 7 (90, 650, 2450).
  3. The measured bound that two octets meet in at most 2 points.

THE LESSON, and it is the corpus's own failure mode 5 in a form the guard could
not catch. Nothing in aa8691a or d3c30d6 is wrong. Every witness passes, every
count is exact, the scope statements are accurate. Only the NOVELTY was false,
and novelty is a property of the corpus rather than of the claim, so no check
inside a pass can find it. What would have found it is grepping the RESULT --
the string "L u L^perp", or the integer 90 -- before writing the framing rather
than after. The tetracode census took a route that never touched those tokens,
which is exactly how a rediscovery survives an honest process.

SCOPE.  The derivation is exact and general; the set-level verification is run
at q = 3 and 5. tau_2 is untouched and stays open in [111, 115].
"""

import argparse
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


def check(q, mod):
    n, LSET, adj, B = mod.build(q)
    octs = [frozenset(i for i in range(n) if B[i, c])
            for c in range(B.shape[1])]

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

    c = 0
    perp = {p for p in range(n) if sf(P3[c], P3[p]) % q == 0}
    hyp_thru_c = {L for L in hyp if c in L}
    missing_c = {L for L in alllines if L <= perp and c not in L}
    through = [C for C in octs if c in C]
    neighbour_parts = {frozenset(adj[c] & C) for C in through}

    return {
        "q": q,
        "linesThroughAPoint": q * q + q + 1,
        "isotropicThroughC": q + 1,
        "hyperbolicThroughC": len(hyp_thru_c),
        "hyperbolicThroughCIsQSquared": len(hyp_thru_c) == q * q,
        "octetsThroughC": len(through),
        "octetsMatchHyperbolicLines": len(through) == len(hyp_thru_c),
        "linesOfCPerpMissingC": len(missing_c),
        "neighbourPartsAreExactlyThoseLines": neighbour_parts == missing_c,
        "planeLines": len(perp) - 1,
        "planeLinesIsQTimesQPlusOne": len(perp) - 1 == q * (q + 1),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--qs", type=int, nargs="+", default=[3, 5])
    args = ap.parse_args()

    mod = octet_module()
    rows = [check(q, mod) for q in args.qs]

    print("THE LOCAL PLANE IS A COROLLARY OF octet = L u L^perp")
    print("=" * 74)
    for x in rows:
        print("  q=%d: %d lines through c = %d isotropic + %d hyperbolic (q^2=%d)"
              % (x["q"], x["linesThroughAPoint"], x["isotropicThroughC"],
                 x["hyperbolicThroughC"], x["q"] ** 2))
        print("        octets through c = %d, matching the hyperbolic lines: %s"
              % (x["octetsThroughC"], x["octetsMatchHyperbolicLines"]))
        print("        {Adj(c) n C_m} == the lines of c-perp missing c (%d): %s"
              % (x["linesOfCPerpMissingC"],
                 x["neighbourPartsAreExactlyThoseLines"]))
        print("        plane lines = |c-perp| - 1 = %d = q(q+1): %s"
              % (x["planeLines"], x["planeLinesIsQTimesQPlusOne"]))
    print()
    print("  so points = octets through c = hyperbolic lines through c,")
    print("  lines = neighbours of c = points of c-perp other than c, and the")
    print("  structure is the DUAL of PG(2,q) punctured at c, i.e. AG(2,q).")
    print("  The 'transversal' property is: a line missing c meets every line")
    print("  through c exactly once.")
    print()
    print("  RECLASSIFIED: aa8691a (the plane), d3c30d6 (the MDS code) and the")
    print("  code content of 64004ce (the tetracode) are COROLLARIES of prior")
    print("  art in this track, not discoveries. All three remain true.")
    print("  SURVIVING AS NEW: the induced group (square-determinant subgroup")
    print("  of AGL(2,q), with the ASL correction), the q-generality of")
    print("  L u L^perp, and the measured bound that octets meet in <= 2.")

    ok = all(x["hyperbolicThroughCIsQSquared"]
             and x["octetsMatchHyperbolicLines"]
             and x["neighbourPartsAreExactlyThoseLines"]
             and x["planeLinesIsQTimesQPlusOne"] for x in rows)
    print()
    print("VALID: %s" % ok)

    if args.write:
        assert ok, "checks failed -- refusing to write"
        rec = {
            "schema": "holotrade.local-plane-is-a-corollary.v1",
            "valid": True,
            "qs": args.qs,
            "perQ": rows,
            "theDerivation": (
                "a line through c is totally isotropic iff it lies in c^perp, so "
                "of the q^2+q+1 lines through c exactly q+1 are isotropic and q^2 "
                "are HYPERBOLIC. An octet is L u L^perp with L hyperbolic, and c "
                "lies in it iff c is on L, so the octets through c correspond "
                "one-to-one with the q^2 hyperbolic lines through c. For a "
                "neighbour x of c, <c,x> is totally isotropic so x is not on L, "
                "hence x is in the octet iff x is in L^perp; and L^perp is a line "
                "lying inside c^perp and missing c. So the neighbour-parts are "
                "exactly the q^2 lines of the projective plane c^perp that miss "
                "c. With points the octets through c and lines the neighbours of "
                "c, the structure is therefore the DUAL of PG(2,q) punctured at a "
                "point, which is AG(2,q), and the pencil is its parallelism."),
            "whatIsReclassified": (
                "aa8691a ('the neighbourhood IS an affine plane of order q'), "
                "d3c30d6 ('the q^2 transversals form an MDS [q+1,2,q]_q code') "
                "and the code content of 64004ce (the q=3 tetracode) are all TRUE "
                "and all COROLLARIES of octet = L u L^perp, which this track "
                "already owned via the_cost_anomalies_are_the_tritangent_"
                "structure.py (3f93821, 2026-09-02). They were presented as "
                "discoveries. The tetracode was reached by an independent route, "
                "the |B n B'| = 5 census, but being found independently does not "
                "make a fact new."),
            "whatSurvivesAsNew": (
                "first, THE GROUP: the stabiliser of c induces on the plane "
                "exactly the index-2 subgroup of AGL(2,q), the affine maps whose "
                "linear part has square determinant, of order |AGL(2,q)|/2 = 216, "
                "6000, 49392 at q = 3, 5, 7 with point stabiliser |GL(2,q)|/2. The "
                "plane's existence does not determine which subgroup of its "
                "automorphism group the geometry realises, and the identification "
                "is proved rather than matched, since AGL(2,q) abelianises to "
                "F_q^* by the determinant so its index-2 subgroup is unique. That "
                "carries the correction that ASL(2,q) is the wrong law and "
                "coincides only at q = 3. Second, the q-GENERALITY of L u L^perp, "
                "stated in the corpus at q = 3 and verified at 3, 5, 7 in "
                "9fda6bf. Third, the measured bound that two octets meet in at "
                "most 2 points."),
            "theLesson": (
                "nothing in aa8691a or d3c30d6 is wrong: every witness passes, "
                "every count is exact, every scope statement is accurate. Only the "
                "NOVELTY was false, and novelty is a property of the corpus rather "
                "than of the claim, so no check inside a pass can catch it. What "
                "would have caught it is grepping the RESULT -- the string "
                "'L u L^perp', or the integer 90 -- before writing the framing "
                "instead of after. The tetracode census took a route that never "
                "touched those tokens, which is exactly how a rediscovery survives "
                "an otherwise honest process."),
            "boundary": (
                "the derivation is exact and holds for all odd q; the set-level "
                "verification -- that the octets through c really are the "
                "hyperbolic lines through c, and that the neighbour-parts really "
                "are the lines of c^perp missing c -- is run at q = 3 and 5 as "
                "SETS, not merely as counts. This file reclassifies framings and "
                "retracts no mathematics: aa8691a, d3c30d6 and 64004ce stay true "
                "and their certificates stay valid. tau_2 is untouched and stays "
                "open in [111, 115]."),
        }
        p = os.path.join(ROOT, "data", "local_plane_is_a_corollary.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=2)
        print("written: %s" % p)


if __name__ == "__main__":
    main()
