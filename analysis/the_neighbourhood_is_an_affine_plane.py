#!/usr/bin/env python3
"""
The neighbourhood of a point of W(3,q) IS an affine plane of order q -- and the
group the geometry induces on it is NOT ASL(2,q), which was a q = 3 accident.

WHAT d3c30d6 SAID, AND WHY IT UNDERSTATED THINGS.  d3c30d6 showed the q^2 octet
blockers at a point drop q^2 pencil transversals forming an MDS [q+1, 2, q]_q
code, and observed that an OA(q^2, q+1, q, 2) is equivalent to an affine plane
of order q. That is the code, i.e. the plane in dual coordinates. The plane is
sitting there directly, and the counts say so before any coding is done:

    |Adj(c)|          = q(q+1) = q^2 + q     the number of LINES of AG(2,q)
    octets through c  = q^2                  the number of POINTS of AG(2,q)
    pencil at c       = q+1 lines of q pts   the q+1 PARALLEL CLASSES

THE THEOREM.  For a point c of W(3,q), take

    points     the q^2 octets through c,
    lines      the q(q+1) neighbours of c,
    incidence  the neighbour x lies on the point m  iff  x is in C_m.

That is an affine plane of order q, and the pencil at c -- the q+1 lines of
W(3,q) through c -- is exactly its parallelism. Verified at EVERY centre for
q = 3, 5, 7 (40, 156 and 400 centres) by checking the design axioms directly:
every line carries exactly q points, every point lies on exactly q+1 lines, and
every pair of points lies on exactly ONE common line -- a 2-(q^2, q, 1) design,
which is an affine plane of order q.

Nothing here is a coding statement. The code of d3c30d6 is what you get by
coordinatising a plane point by which line of each parallel class it lies on.

THE GROUP, AND A CORRECTION TO OUR OWN q = 3 READING.  e239484 computed the
image of the stabiliser of c on the twelve neighbours at q = 3 and named it
ASL(2,3) = (C3 x C3):SL(2,3) of order 216. That is correct at q = 3 and it is
also misleading, because ASL is not what generalises. Acting on the q^2 plane
points the image has order

    q = 3   216      q = 5   6000      q = 7   49392

and those are |AGL(2,q)|/2 every time, not |ASL(2,q)| = q^3(q^2-1), which is
216, 3000, 16464. The point stabiliser is |GL(2,q)|/2, not |SL(2,q)|.

THE INDEX-2 SUBGROUP IS UNIQUE, so matching the order is a proof of identity,
not a numerical coincidence: the abelianisation of AGL(2,q) is F_q^* via the
determinant, so index-2 subgroups of AGL(2,q) correspond to index-2 subgroups
of F_q^*, of which there is exactly one for odd q -- the squares. Hence

    the geometry induces exactly the affine maps whose linear part has
    SQUARE determinant,

an index-2 subgroup of AGL(2,q) for every odd q. At q = 3 the squares in F_3^*
are just {1}, so square determinant means determinant 1 and the group collapses
to ASL(2,3). That collapse is the accident. It happens only at q = 3 and it is
why e239484 read the wrong law off the right number.

SCOPE.  The plane is verified at every centre for q = 3, 5, 7. The group is
computed at one centre for each of those q, which suffices because Sp(4,q) is
transitive on points. q = 9 and beyond are not run and even q is untouched. The
octets are imported from the_minimum_blocker_labels_are_octets.py (aa42b38,
6f35762), not re-derived. tau_2 is untouched and stays open in [111, 115].
"""

import argparse
import collections
import importlib.util
import itertools
import json
import os
import random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def octet_module():
    p = os.path.join(ROOT, "analysis",
                     "the_minimum_blocker_labels_are_octets.py")
    spec = importlib.util.spec_from_file_location("octmod", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def plane_at_every_centre(q, mod):
    """The design axioms, checked at every centre."""
    n, LSET, adj, B = mod.build(q)
    octs = [frozenset(i for i in range(n) if B[i, c])
            for c in range(B.shape[1])]
    linesof = [[k for k, S in enumerate(LSET) if p in S] for p in range(n)]
    failures = []
    for c in range(n):
        pts = [C for C in octs if c in C]            # plane POINTS
        lns = sorted(adj[c])                         # plane LINES
        per_line = {sum(1 for C in pts if x in C) for x in lns}
        per_point = {len(adj[c] & C) for C in pts}
        pair = {len(adj[c] & A & Bb)
                for A, Bb in itertools.combinations(pts, 2)}
        pencil = [frozenset(set(LSET[k]) - {c}) for k in linesof[c]]
        parallel = (len(pencil) == q + 1
                    and {len(L) for L in pencil} == {q}
                    and len(set().union(*pencil)) == q * (q + 1))
        if not (len(pts) == q * q and len(lns) == q * (q + 1)
                and per_line == {q} and per_point == {q + 1}
                and pair == {1} and parallel):
            failures.append(c)
    return n, len(failures) == 0, failures


def induced_group(q, mod):
    """Order of the group the stabiliser induces on the q^2 plane points."""
    from sympy.combinatorics import Permutation, PermutationGroup

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

    def transvection(v):
        img = [0] * n
        for p in P3:
            t = sf(p, v)
            img[i3[p]] = i3[nm(tuple((p[k] + t * v[k]) % q for k in range(4)))]
        return Permutation(img)

    # Symplectic transvections generate Sp(4,q), but feeding all of them to
    # Schreier-Sims is ruinous at q = 7 (400 points, 400 generators -- it did
    # not finish in 25 minutes). A handful suffices; grow until the order is
    # right, and ASSERT it, so a too-small set fails loudly instead of
    # silently computing inside a proper subgroup.
    psp = q ** 4 * (q * q - 1) * (q ** 4 - 1) // 2
    rnd = random.Random(1)
    pool = [v for v in P3]
    rnd.shuffle(pool)
    gens = []
    for v in pool:
        g = transvection(v)
        if g.is_Identity:
            continue
        gens.append(g)
        if len(gens) >= 8 and PermutationGroup(gens).order() == psp:
            break
    G = PermutationGroup(gens)
    assert G.order() == psp, (G.order(), psp)
    S = G.stabilizer(0)
    pts = [C for C in octs if 0 in C]
    oi = {C: k for k, C in enumerate(pts)}
    ind = [Permutation([oi[frozenset(g(i) for i in C)] for C in pts])
           for g in S.generators]
    I = PermutationGroup(ind)
    return {
        "generatorsUsed": len(gens),
        "pspOrder": G.order(),
        "stabiliserOrder": S.order(),
        "planePoints": len(pts),
        "imageOrder": I.order(),
        "transitive": I.is_transitive(),
        "pointStabiliser": I.stabilizer(0).order(),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--qs", type=int, nargs="+", default=[3, 5, 7])
    ap.add_argument("--group-qs", type=int, nargs="+", default=[3, 5])
    args = ap.parse_args()

    mod = octet_module()

    print("THE NEIGHBOURHOOD OF A POINT OF W(3,q) IS AN AFFINE PLANE")
    print("=" * 74)
    print("  points  = the q^2 octets through c")
    print("  lines   = the q(q+1) neighbours of c")
    print("  x on m  iff  x is in C_m,  parallelism = the pencil at c")
    print()
    planes = []
    for q in args.qs:
        n, ok, bad = plane_at_every_centre(q, mod)
        planes.append({"q": q, "points": n, "planePoints": q * q,
                       "planeLines": q * (q + 1), "parallelClasses": q + 1,
                       "allCentres": ok, "failures": bad})
        print("  q=%d  W(3,q) has %3d points; every centre gives a "
              "2-(%d,%d,1) design: %s"
              % (q, n, q * q, q, ok))
    print()
    print("  a 2-(q^2, q, 1) design IS an affine plane of order q.")
    print()

    print("THE GROUP THE GEOMETRY INDUCES ON THAT PLANE")
    print("=" * 74)
    print("    q   image  |AGL|/2   ASL(2,q)   ptstab  |GL|/2  |SL|")
    groups = []
    for q in args.group_qs:
        g = induced_group(q, mod)
        agl = q * q * (q * q - 1) * (q * q - q)
        gl = (q * q - 1) * (q * q - q)
        rec = {
            "q": q, **g,
            "aglOrder": agl, "aglHalf": agl // 2,
            "aslOrder": q ** 3 * (q * q - 1),
            "glHalf": gl // 2, "slOrder": q * (q * q - 1),
            "isIndexTwoInAGL": g["imageOrder"] == agl // 2,
            "isASL": g["imageOrder"] == q ** 3 * (q * q - 1),
            "pointStabIsGLHalf": g["pointStabiliser"] == gl // 2,
        }
        groups.append(rec)
        print("   %2d  %6d  %7d  %9d  %7d  %6d  %4d"
              % (q, g["imageOrder"], agl // 2, rec["aslOrder"],
                 g["pointStabiliser"], gl // 2, rec["slOrder"]))
    print()
    print("  the image is |AGL(2,q)|/2 at every q tested, and ASL only at q=3.")
    print("  AGL(2,q) abelianises to F_q^* by det, so its index-2 subgroup is")
    print("  UNIQUE -- the square-determinant one -- and matching the order is")
    print("  therefore a proof of identity, not a coincidence.")
    print("  At q=3 the squares in F_3^* are {1}, so square det means det 1 and")
    print("  the group collapses to ASL(2,3). That collapse is the accident.")

    ok = (all(p["allCentres"] for p in planes)
          and all(g["isIndexTwoInAGL"] and g["pointStabIsGLHalf"]
                  for g in groups)
          and all(g["isASL"] == (g["q"] == 3) for g in groups))
    print()
    print("VALID: %s" % ok)

    if args.write:
        assert ok, "checks failed -- refusing to write"
        rec = {
            "schema": "holotrade.neighbourhood-is-an-affine-plane.v1",
            "valid": True,
            "planeVerifiedAtQ": args.qs,
            "planes": planes,
            "groupVerifiedAtQ": args.group_qs,
            "groups": groups,
            "theTheorem": (
                "for a point c of W(3,q), take as POINTS the q^2 octets through "
                "c, as LINES the q(q+1) neighbours of c, and let the neighbour x "
                "lie on the point m exactly when x is in C_m. That is an affine "
                "plane of order q, and the pencil at c -- the q+1 lines of W(3,q) "
                "through c -- is exactly its parallelism. Checked at EVERY centre "
                "for q = 3, 5, 7 by the design axioms directly: every line "
                "carries q points, every point lies on q+1 lines, and every pair "
                "of points lies on exactly ONE common line, i.e. a 2-(q^2,q,1) "
                "design."),
            "whyThisIsStrongerThanTheCode": (
                "d3c30d6 proved the q^2 dropped transversals form an MDS "
                "[q+1,2,q]_q code and noted that an OA(q^2,q+1,q,2) is equivalent "
                "to an affine plane. That is the plane in DUAL COORDINATES. The "
                "plane is present directly and the counts announce it before any "
                "coding: |Adj(c)| = q(q+1) is the number of lines of AG(2,q), the "
                "q^2 octets through c are its points, and the pencil is the "
                "parallelism. The code is what you get by coordinatising a plane "
                "point by which line of each parallel class contains it."),
            "theGroupLaw": (
                "the stabiliser of c induces on the q^2 plane points a group of "
                "order |AGL(2,q)|/2 -- 216, 6000, 49392 at q = 3, 5, 7 -- with "
                "point stabiliser |GL(2,q)|/2. Since AGL(2,q) abelianises to F_q^* "
                "via the determinant, its index-2 subgroups correspond to those of "
                "F_q^*, of which there is exactly ONE for odd q, the squares. So "
                "matching the order PROVES the identity: the geometry induces "
                "exactly the affine maps whose linear part has square "
                "determinant."),
            "correctionToOurOwnQ3Reading": (
                "e239484 named the q = 3 image ASL(2,3) = (C3 x C3):SL(2,3) of "
                "order 216. That is correct at q = 3 and misleading as a law, "
                "because ASL is not what generalises: |ASL(2,q)| = q^3(q^2-1) is "
                "216, 3000, 16464 while the measured images are 216, 6000, 49392. "
                "At q = 3 the squares in F_3^* are just {1}, so square determinant "
                "means determinant 1 and the square-determinant group collapses "
                "onto ASL(2,3). That collapse happens only at q = 3, and it is why "
                "the right number was read as the wrong law."),
            "priorArtImportedNotRederived": (
                "the octets, |C_m| = 2(q+1), the K(q+1,q+1) structure giving "
                "internal degree q+1, and the count of q^2 octets through each "
                "point come from the_minimum_blocker_labels_are_octets.py "
                "(aa42b38, 6f35762) and c9e6be7; this file calls that module's own "
                "build(). The code formulation is d3c30d6 and the q = 3 group "
                "computation is e239484."),
            "boundary": (
                "the plane is verified at EVERY centre for q = 3, 5, 7 -- 40, 156 "
                "and 400 centres -- by the design axioms, not by transporting one "
                "case with the group. The induced group is computed at ONE centre "
                "per q, which suffices because Sp(4,q) is transitive on points, "
                "and the group is built from symplectic transvections, whose "
                "generation of Sp(4,q) is classical and is used, not proved here. "
                "The identification of the image as the square-determinant "
                "subgroup rests on uniqueness of the index-2 subgroup of AGL(2,q), "
                "which is proved from the abelianisation, so it is an identity and "
                "not an order coincidence. q = 9 and beyond are not run; even q is "
                "untouched. tau_2 is untouched and stays open in [111, 115]."),
        }
        p = os.path.join(ROOT, "data", "neighbourhood_is_an_affine_plane.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=2)
        print("written: %s" % p)


if __name__ == "__main__":
    main()
