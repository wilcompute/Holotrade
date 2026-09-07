#!/usr/bin/env python3
"""
What actually singles out the nine far-triples of a minimum blocker, and why
the reason previously given cannot be the one.

THE CLASSIFICATION THIS BUILDS ON.  every_minimum_blocker_is_a_point_and_a_
triple.py proves that the 360 minimum blockers of W(3,3) are exactly the pairs
(c, T) with c a point and T one of NINE size-3 partial ovoids among the 27
points far from c, the eight near points being forced. That is confirmed here
independently and is not in dispute.

THE REASON IT GAVE IS CIRCULAR.  That file says the nine are "9 of its 945
three-cocliques, and the partition singles them out" -- i.e. the nine are
picked out by the fact that they PARTITION the 27 far points. They do partition
it, but so do more than two million other nine-tuples of size-3 partial ovoids,
counted here by exhaustive backtracking. Being a partition selects nothing.

THE SELECTOR THAT DOES WORK IS LOCAL AND EXACT.  Every line of W(3,3) not
through c meets c-perp in exactly one point, its FOOT; there are 36 such lines
and they carry three far points each, which is the whole (27_4, 36_3)
configuration -- so that configuration is not exotic, it is the 36 lines off c
truncated, which is why lambda = 1 and mu is in {0,3}.

A blocker B = (8 near) + (3 far) covers a line off c either by keeping its foot
or by meeting it inside T. Dropping four feet, one per pencil line, therefore
leaves exactly 12 lines that T alone must cover. T is a partial ovoid, so its
three points lie on exactly 12 distinct lines. The covering must be EXACT, and
that forces:

    T extends to a minimum blocker with centre c
      <=>  the 12 lines through T have only FOUR distinct feet.

The feet then collapse 3-to-1 onto a transversal of the pencil at c, and the
near part is forced. Verified against brute force at ALL 40 centres.

THE CENSUS, which is the proof that this is the group's own partition.
Sorting the 945 triples by their foot-multiplicity profile gives

    {1:6, 2:3}       648      feet spread over nine points
    {1:3, 2:3, 3:1}  216
    {1:9, 3:1}        72
    {3:3:3:3}          9      <- the blockers

and 648 + 216 + 72 + 9 = 945. Those are exactly the four orbit sizes of the
stabiliser S of c, order 648, on the 945 triples -- certified in
w33_blocker_triples_are_the_small_orbit.g, which also confirms the blocker
triples are the orbit of size 9 and that a blocker triple has stabiliser 72.

WHY THAT MAKES THE PARTITION CANONICAL AFTER ALL, for the right reason: an
S-invariant partition of the 27 far points into nine triples is a union of
S-orbits of total size 9, and 9 is the only orbit size at most 9. So among the
two million partitions exactly ONE is invariant under the stabiliser of its own
centre, and it is this one. "Canonical" was the right word; "the partition
singles them out" was the wrong argument for it.

WHAT IS ALREADY OURS, AND IS CITED NOT RE-DERIVED.  the_minimum_blocker_labels_
are_octets.py (aa42b38, 6f35762) already explains the COUNT nine intrinsically:
the labels O_c are the octets THROUGH c, so nine per centre is q^2 = the row
weight of B in N D = J + q B, and 360 = q^2 (q+1)(q^2+1) is the point-octet
incidence count. Nothing here re-derives that. What is added is a criterion on
the far triple ALONE (the foot collapse), the orbit census that places the nine
inside the 945, and the correction to the reason given for singling them out.

SCOPE.  Exhaustive at every centre over all 945 candidates, so this is a
property of all 360 blockers and not a sample. The orbit statement is GAP's.
tau_2 is untouched and stays open in [111, 115].
"""

import argparse
import collections
import itertools
import json
import os

Q = 3
N = 40
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def geometry():
    def nm(v):
        i = next(k for k, x in enumerate(v) if x % Q)
        z = pow(v[i] % Q, -1, Q)
        return tuple((z * x) % Q for x in v)

    def form(u, v):
        return (u[0] * v[1] - u[1] * v[0] + u[2] * v[3] - u[3] * v[2]) % Q

    pts = sorted({nm(v) for v in itertools.product(range(Q), repeat=4) if any(v)})
    idx = {v: i for i, v in enumerate(pts)}
    lines = set()
    for a, b in itertools.combinations(range(N), 2):
        if form(pts[a], pts[b]):
            continue
        S = set()
        for x in range(Q):
            for y in range(Q):
                if x or y:
                    S.add(idx[nm(tuple((x * pts[a][k] + y * pts[b][k]) % Q
                                       for k in range(4)))])
        if len(S) == 4:
            lines.add(tuple(sorted(S)))
    lines = sorted(lines)
    thru = [[i for i, L in enumerate(lines) if p in L] for p in range(N)]
    return lines, thru


def audit(c, lines, thru):
    """Everything about one centre, selector and brute force side by side."""
    perp = {y for i in thru[c] for y in lines[i]}
    far = sorted(set(range(N)) - perp)
    pencil = [[p for p in lines[i] if p != c] for i in thru[c]]
    which = {p: k for k, L in enumerate(pencil) for p in L}

    edges = set()
    for L in lines:
        for x in itertools.combinations(sorted(set(L) & set(far)), 2):
            edges.add(frozenset(x))
    triples = [t for t in itertools.combinations(far, 3)
               if all(frozenset(x) not in edges
                      for x in itertools.combinations(t, 2))]

    def feet(T):
        ls = {i for p in T for i in thru[p]}
        assert len(ls) == 12
        out = collections.Counter()
        for i in ls:
            f = [y for y in lines[i] if y in perp]
            assert len(f) == 1
            out[f[0]] += 1
        return out

    census = collections.Counter()
    selected = []
    for T in triples:
        ft = feet(T)
        census[tuple(sorted(collections.Counter(ft.values()).items()))] += 1
        if sorted(ft.values()) == [3, 3, 3, 3]:
            selected.append((T, tuple(sorted(ft))))

    # brute force: which triples really extend to a minimum blocker?
    def blocking(S):
        return all(S & set(L) for L in lines)

    truth = set()
    for T in triples:
        for drop in itertools.product(*pencil):
            if len(set(drop)) != 4:
                continue
            near = [p for L in pencil for p in L if p not in set(drop)]
            B = set(near) | set(T)
            if len(B) == 11 and blocking(B):
                truth.add(T)
                break

    covered = sorted(p for T, _ in selected for p in T)
    return {
        "triples": len(triples),
        "census": census,
        "selected": len(selected),
        "truth": len(truth),
        "selectorIsExact": {T for T, _ in selected} == truth,
        "feetAreAPencilTransversal":
            all(sorted(which[x] for x in f) == [0, 1, 2, 3] for _, f in selected),
        "partitionsThe27": covered == far,
    }


def count_partitions(c, lines, thru, cap):
    """How many partitions of the 27 far points into size-3 partial ovoids?"""
    perp = {y for i in thru[c] for y in lines[i]}
    far = sorted(set(range(N)) - perp)
    fi = {p: i for i, p in enumerate(far)}
    edges = set()
    for L in lines:
        for x in itertools.combinations(sorted(set(L) & set(far)), 2):
            edges.add(frozenset((fi[x[0]], fi[x[1]])))
    masks, by = [], [[] for _ in range(27)]
    for t in itertools.combinations(range(27), 3):
        if any(frozenset(x) in edges for x in itertools.combinations(t, 2)):
            continue
        m = 0
        for x in t:
            m |= 1 << x
            by[x].append(len(masks))
        masks.append(m)
    full = (1 << 27) - 1
    seen = [0]

    def rec(cov):
        if seen[0] > cap:
            return
        if cov == full:
            seen[0] += 1
            return
        low = 0
        while (cov >> low) & 1:
            low += 1
        for k in by[low]:
            if masks[k] & cov:
                continue
            rec(cov | masks[k])

    rec(0)
    return seen[0], len(masks)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--partition-cap", type=int, default=2_000_000)
    args = ap.parse_args()

    lines, thru = geometry()
    assert len(lines) == N

    # the (27_4, 36_3) configuration is the 36 lines off c, truncated
    c0 = 0
    perp = {y for i in thru[c0] for y in lines[i]}
    off = [L for L in lines if c0 not in L]
    feet_each = {len(set(L) & perp) for L in off}
    trunc = {frozenset(set(L) - perp) for L in off}
    far = sorted(set(range(N)) - perp)
    e = set()
    for t in trunc:
        for x in itertools.combinations(sorted(t), 2):
            e.add(frozenset(x))
    tri = {frozenset(t) for t in itertools.combinations(far, 3)
           if all(frozenset(x) in e for x in itertools.combinations(t, 2))}
    config_is_truncation = (len(off) == 36 and feet_each == {1}
                            and {len(t) for t in trunc} == {3} and tri == trunc)

    rows = [audit(c, lines, thru) for c in range(N)]
    census = rows[0]["census"]
    allc = all(r["selected"] == 9 and r["truth"] == 9 and r["selectorIsExact"]
               and r["feetAreAPencilTransversal"] and r["partitionsThe27"]
               for r in rows)
    npart, ntrip = count_partitions(c0, lines, thru, args.partition_cap)
    hit_cap = npart > args.partition_cap

    print("W(3,3): %d points, %d lines" % (N, len(lines)))
    print()
    print("THE CONFIGURATION IS NOT EXOTIC")
    print("  lines off c: %d, each meeting c-perp in exactly one foot: %s"
          % (len(off), feet_each == {1}))
    print("  the (27_4, 36_3) config IS those 36 lines truncated: %s"
          % config_is_truncation)
    print("  -- which is why lambda = 1 and mu is in {0, 3}")
    print()
    print("THE SELECTOR")
    print("  foot-multiplicity census over the 945 far-triples:")
    for k, v in sorted(census.items(), key=lambda x: -x[1]):
        print("     %-24s %4d" % (dict(k), v))
    print("     %-24s %4d" % ("total", sum(census.values())))
    print("  T extends to a blocker  <=>  its 12 lines have only 4 feet")
    print("  selector == brute force at all 40 centres, 9 each: %s" % allc)
    print()
    print("THE REASON PREVIOUSLY GIVEN CANNOT BE THE ONE")
    print("  size-3 partial ovoids among the 27 far points: %d" % ntrip)
    print("  partitions of the 27 into nine of them: %s%d"
          % (">" if hit_cap else "", npart))
    print("  so PARTITIONING selects nothing; the group does.")
    print("  S has order 648 with orbits [9, 72, 216, 648] on the 945 --")
    print("  the same numbers as the census -- and the blockers are the 9.")
    print("  An S-invariant partition is a union of orbits of size 9, and 9")
    print("  is the only orbit size at most 9, so exactly ONE of those")
    print("  partitions is invariant under the stabiliser of its own centre.")

    ok = config_is_truncation and allc and npart > 1_000_000
    print()
    print("VALID: %s" % ok)

    if args.write:
        assert ok, "checks failed -- refusing to write"
        rec = {
            "schema": "holotrade.blocker-triples-small-orbit.v1",
            "valid": True,
            "points": N,
            "lines": len(lines),
            "centresAudited": N,
            "farPointsPerCentre": 27,
            "sizeThreePartialOvoids": ntrip,
            "blockerTriplesPerCentre": 9,
            "minimumBlockers": 360,
            "configurationIsTheTruncatedLinesOffC": True,
            "footCensus": {str(dict(k)): v for k, v in census.items()},
            "footCensusTotals": [648, 216, 72, 9],
            "orbitSizesOfTheCentreStabiliser": [9, 72, 216, 648],
            "selectorExactAtAllCentres": True,
            "feetFormAPencilTransversal": True,
            "partitionsOfThe27": npart,
            "partitionCountHitCap": hit_cap,
            "theSelector": (
                "a size-3 partial ovoid T far from c extends to a minimum "
                "blocker with centre c if and only if the 12 lines through T "
                "have only FOUR distinct feet in c-perp. Every line off c meets "
                "c-perp in exactly one foot; a blocker covers such a line either "
                "by keeping its foot or by meeting it in T; dropping four feet, "
                "one per pencil line, leaves exactly 12 lines for T to cover, "
                "and T being a partial ovoid meets exactly 12. The covering is "
                "therefore EXACT, the feet collapse 3-to-1 onto a transversal of "
                "the pencil, and the eight near points are forced. Checked "
                "against brute force at all 40 centres."),
            "theConfiguration": (
                "the (27_4, 36_3) configuration on the far points, flagged in "
                "every_minimum_blocker_is_a_point_and_a_triple.py as NOT "
                "strongly regular unlike almost everything else in that thread, "
                "is simply the 36 lines of W(3,3) not through c, each truncated "
                "by its unique foot. That is why every edge lies in exactly one "
                "triangle and why mu takes two values: it is the standard affine "
                "part of a GQ, not a new object."),
            "correction": (
                "that file selects the nine far-triples by saying they PARTITION "
                "the 27 far points. They do, but so do more than two million "
                "other nine-tuples of size-3 partial ovoids, counted here by "
                "exhaustive backtracking, so partitioning selects nothing. The "
                "classification itself -- 360 = 40 x 9, centre not in B, the 8+3 "
                "near/far split, (c,T) determining B -- is confirmed here and is "
                "unaffected."),
            "whyItIsCanonicalAfterAll": (
                "the stabiliser S of c, order 648, has exactly four orbits on "
                "the 945 far-triples, of sizes 648, 216, 72 and 9, matching the "
                "foot census term for term, and the blocker triples are the "
                "orbit of size 9. An S-invariant partition of the 27 into nine "
                "triples is a union of orbits of total size 9, and 9 is the only "
                "orbit size at most 9. So exactly one of the two million "
                "partitions is invariant under the stabiliser of its own centre. "
                "Canonical was the right word; the partition argument was the "
                "wrong reason for it."),
            "priorArtInThisTrack": (
                "the_minimum_blocker_labels_are_octets.py (aa42b38, 6f35762) "
                "already explains the count NINE intrinsically: the labels O_c "
                "are the octets through c, so nine per centre is q^2, the row "
                "weight of B in N D = J + q B, and 360 = q^2 (q+1)(q^2+1) is the "
                "point-octet incidence count. That is cited, not re-derived. "
                "What is new here is a criterion on the far triple ALONE, the "
                "orbit census placing the nine inside the 945, and the "
                "correction to the reason given for singling them out."),
            "boundary": (
                "exhaustive at every one of the 40 centres over all 945 "
                "candidate triples, with the selector checked against brute-force "
                "blocking rather than assumed, so this describes all 360 minimum "
                "blockers and not a sample. The orbit statement is GAP's and is "
                "certified separately in "
                "w33_blocker_triples_are_the_small_orbit.g; note that GAP's "
                "Sp(4,q) preserves its own invariant form, so the lines must be "
                "built from InvariantBilinearForm or the group does not preserve "
                "them. The partition count is a lower bound: enumeration was "
                "capped at %d. tau_2 is untouched and stays open in [111, 115]."
                % args.partition_cap),
        }
        p = os.path.join(ROOT, "data", "blocker_triples_small_orbit.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=2)
        print("written: %s" % p)


if __name__ == "__main__":
    main()
