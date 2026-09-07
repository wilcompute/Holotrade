#!/usr/bin/env python3
"""
The octet blockers in closed form. Three results, all ours, composed into one
line -- and most of the q = 3 blocker thread becomes trivial.

NOTHING HERE IS NEW.  This file discovers nothing. It composes three statements
this repository already contains, none of which had been put next to the others:

  (a)  B(c,m) = (Adj(c) sym-diff C_m) \\ {c}
       -- data/tensor_111_pg34_label_reduction.json, corpus
  (b)  O_c, the label set at c, is the set of OCTETS THROUGH c
       -- the_minimum_blocker_labels_are_octets.py (aa42b38, 6f35762)
  (c)  an octet is L u L^perp for L a HYPERBOLIC line of PG(3,q)
       -- the_cost_anomalies_are_the_tritangent_structure.py (3f93821)

3a1e30d already used (c) to reclassify the local affine plane. Substituting it
into (a) and (b) does more than that: it makes the blocker itself explicit.

THE COMPOSITION.  Let c be a point and m an octet through c, so C_m = L u
L^perp with L hyperbolic. Since c is in the octet and L, L^perp are disjoint,
say c is on L. Then:

  * L is hyperbolic and passes through c, so L is not inside c^perp, and
    L n c^perp = {c} exactly.
  * c is on L, so L^perp is inside c^perp; and c is not on L^perp, since that
    would force L inside c^perp.

So Adj(c) n C_m = L^perp and C_m \\ Adj(c) \\ {c} = L \\ {c}, and (a) becomes

        B(c,m) = ( Adj(c) \\ L^perp )  u  ( L \\ {c} )

    keep every neighbour of c except the q+1 lying on L^perp,
    then add the other q points of the hyperbolic line L.

with sizes (q^2 - 1) + q = q^2 + q - 1, which is the known blocker size.
Verified at EVERY centre for q = 3, 5, 7 against the corpus formula, as sets.

WHAT THIS MAKES TRIVIAL, all of it ours and all of it still true:

  * "the near part is the neighbours minus a TRANSVERSAL of the pencil" --
    the removed set is L^perp, a line of the projective plane c^perp missing
    c, and such a line meets every line through c exactly once. That is the
    transversal, with no computation.
  * "the far part is q pairwise non-collinear points" -- it is L \\ {c}, and a
    hyperbolic line has all its points pairwise non-perpendicular.
  * "the q^2 far-parts PARTITION the q^3 points off c^perp" -- they are the
    q^2 hyperbolic lines through c, minus c, and lines through a point
    partition the points off c^perp. every_minimum_blocker_is_a_point_and_a_
    triple.py called this partition canonical without a reason; 4a45d15 gave
    the reason as "the smallest orbit of the centre stabiliser", which is true
    but roundabout. This is the reason.
  * 4a45d15's FOOT-COLLAPSE SELECTOR -- "T extends to a blocker at c iff the 12
    lines through T meet c^perp in only 4 points" -- is equivalent to the far
    simpler "T is a hyperbolic line through c, minus c", and is therefore a
    corollary rather than a criterion that had to be found.

WHAT IS STILL NOT IMPLIED BY ANY OF THIS.  The closed form says what the
blockers ARE. It does not say which subgroup of the affine plane's automorphism
group the geometry induces -- that is the square-determinant index-2 subgroup of
AGL(2,q), computed in aa8691a and unaffected. Nor does it decide tau_2, which
stays open in [111, 115]. And it says nothing about MINIMALITY: the octet
blockers are minimum blockers only at q = 3, where the excess q - 3 vanishes,
which is exactly why the q = 3 classification results do not generalise even
though this closed form does.

SCOPE.  Verified as sets at every centre for q = 3, 5, 7 -- 40, 156 and 400
centres -- against the corpus's own formula, with the two containment facts
(L n c^perp = {c}, L^perp inside c^perp) checked rather than assumed. The
derivation itself is general and uses only that L is hyperbolic. tau_2 is
untouched.
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

    def sf(u, v):
        return (u[0] * v[2] - u[2] * v[0] + u[1] * v[3] - u[3] * v[1]) % q

    closed_form = containments = far_ok = partition = sizes_ok = True
    for c in range(n):
        perp = {p for p in range(n) if sf(P3[c], P3[p]) % q == 0}
        far = set(range(n)) - perp
        triples = []
        for C in [C for C in octs if c in C]:
            Lh = frozenset([c] + [y for y in C if y != c and y not in adj[c]])
            Lp = frozenset(C) - Lh
            if len(Lh) != q + 1 or len(Lp) != q + 1:
                closed_form = False
                continue
            # the two containment facts the derivation rests on
            if len(Lh & perp) != 1 or not (Lp <= perp):
                containments = False
            corpus = (adj[c] ^ frozenset(C)) - {c}
            derived = (adj[c] - Lp) | (Lh - {c})
            if frozenset(derived) != frozenset(corpus):
                closed_form = False
            if len(corpus) != q * q + q - 1:
                sizes_ok = False
            if not (Lh - {c}) <= far:
                far_ok = False
            triples.append(frozenset(Lh - {c}))
        if (len(triples) != q * q or len(far) != q ** 3
                or frozenset().union(*triples) != frozenset(far)
                or sum(len(t) for t in triples) != q ** 3):
            partition = False

    return {
        "q": q,
        "centres": n,
        "closedFormHoldsEverywhere": closed_form,
        "containmentFactsHold": containments,
        "farPartIsOffCPerp": far_ok,
        "farPartsPartitionTheFarPoints": partition,
        "blockerSize": q * q + q - 1,
        "nearSize": q * q - 1,
        "farSize": q,
        "sizesCorrect": sizes_ok,
        "octetsThroughC": q * q,
        "farPointCount": q ** 3,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--qs", type=int, nargs="+", default=[3, 5, 7])
    args = ap.parse_args()

    mod = octet_module()
    rows = [check(q, mod) for q in args.qs]

    print("THE OCTET BLOCKERS IN CLOSED FORM")
    print("=" * 74)
    print("    B(c,m) = ( Adj(c) \\ L^perp )  u  ( L \\ {c} )")
    print("    keep every neighbour of c except the q+1 on L^perp,")
    print("    then add the other q points of the hyperbolic line L.")
    print()
    for x in rows:
        print("  q=%d (%d centres): closed form holds everywhere: %s"
              % (x["q"], x["centres"], x["closedFormHoldsEverywhere"]))
        print("        L n c-perp = {c} and L-perp inside c-perp: %s"
              % x["containmentFactsHold"])
        print("        far part = L \\ {c}, off c-perp: %s   sizes %d + %d = %d: %s"
              % (x["farPartIsOffCPerp"], x["nearSize"], x["farSize"],
                 x["blockerSize"], x["sizesCorrect"]))
        print("        the %d far-parts partition the %d far points: %s"
              % (x["octetsThroughC"], x["farPointCount"],
                 x["farPartsPartitionTheFarPoints"]))
    print()
    print("  NOTHING HERE IS NEW. It composes (a) the corpus's B(c,m) formula,")
    print("  (b) O_c = octets through c (aa42b38), and (c) octet = L u L^perp")
    print("  (3f93821). What it makes trivial: the near part being a pencil")
    print("  transversal, the far part being pairwise non-collinear, the")
    print("  canonical partition, and 4a45d15's foot-collapse selector.")
    print("  NOT implied: the induced group (aa8691a), minimality (q=3 only),")
    print("  or tau_2.")

    ok = all(x["closedFormHoldsEverywhere"] and x["containmentFactsHold"]
             and x["farPartIsOffCPerp"] and x["farPartsPartitionTheFarPoints"]
             and x["sizesCorrect"] for x in rows)
    print()
    print("VALID: %s" % ok)

    if args.write:
        assert ok, "checks failed -- refusing to write"
        rec = {
            "schema": "holotrade.blockers-in-closed-form.v1",
            "valid": True,
            "qs": args.qs,
            "perQ": rows,
            "theClosedForm": (
                "B(c,m) = (Adj(c) minus L^perp) union (L minus {c}), where the "
                "octet is C_m = L u L^perp with L the hyperbolic line through c: "
                "keep every neighbour of c except the q+1 lying on L^perp, then "
                "add the other q points of L. Sizes (q^2-1) + q = q^2+q-1."),
            "theDerivation": (
                "L is hyperbolic and passes through c, so L is not inside c^perp "
                "and L n c^perp = {c} exactly; and c on L puts L^perp inside "
                "c^perp, with c not on L^perp since that would force L inside "
                "c^perp. Hence Adj(c) n C_m = L^perp and C_m minus Adj(c) minus "
                "{c} = L minus {c}, and the corpus's symmetric-difference formula "
                "collapses to the closed form."),
            "nothingHereIsNew": (
                "this file discovers nothing. It composes three statements the "
                "repository already contained, none of which had been put beside "
                "the others: the corpus's B(c,m) = (Adj(c) sym-diff C_m) minus "
                "{c} from tensor_111_pg34_label_reduction.json; O_c = the octets "
                "through c from the_minimum_blocker_labels_are_octets.py "
                "(aa42b38, 6f35762); and octet = L u L^perp from "
                "the_cost_anomalies_are_the_tritangent_structure.py (3f93821)."),
            "whatItMakesTrivial": (
                "the near part being 'the neighbours minus a TRANSVERSAL of the "
                "pencil' -- the removed set is L^perp, a line of the projective "
                "plane c^perp missing c, and such a line meets every line through "
                "c exactly once. The far part being q pairwise non-collinear "
                "points -- it is L minus {c} and a hyperbolic line has all its "
                "points pairwise non-perpendicular. The q^2 far-parts PARTITIONING "
                "the q^3 points off c^perp -- they are the hyperbolic lines "
                "through c minus c, and lines through a point partition the points "
                "off c^perp; every_minimum_blocker_is_a_point_and_a_triple.py "
                "called that partition canonical without a reason and 4a45d15 gave "
                "the reason as 'the smallest orbit of the centre stabiliser', true "
                "but roundabout -- this is the reason. And 4a45d15's foot-collapse "
                "selector, 'T extends to a blocker iff its 12 lines meet c^perp in "
                "only 4 points', is equivalent to the far simpler 'T is a "
                "hyperbolic line through c minus c', so it is a corollary rather "
                "than a criterion that had to be found."),
            "whatIsStillNotImplied": (
                "the closed form says what the blockers ARE. It does not say which "
                "subgroup of the affine plane's automorphism group the geometry "
                "induces -- the square-determinant index-2 subgroup of AGL(2,q), "
                "computed in aa8691a and unaffected. It does not decide tau_2, "
                "which stays open in [111, 115]. And it says nothing about "
                "MINIMALITY: the octet blockers are minimum only at q = 3 where "
                "the excess q-3 vanishes, which is exactly why the q = 3 "
                "classification results do not generalise even though this closed "
                "form does."),
            "boundary": (
                "verified as SETS at every centre for q = 3, 5, 7 -- 40, 156 and "
                "400 centres -- against the corpus's own symmetric-difference "
                "formula, with the two containment facts (L n c^perp = {c}, "
                "L^perp inside c^perp) checked rather than assumed. The derivation "
                "is general and uses only that L is hyperbolic. tau_2 is untouched "
                "and stays open in [111, 115]."),
        }
        p = os.path.join(ROOT, "data", "blockers_in_closed_form.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=2)
        print("written: %s" % p)


if __name__ == "__main__":
    main()
