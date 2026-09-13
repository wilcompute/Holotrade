#!/usr/bin/env python3
"""
The two-centre octet blockers exist for EVERY q, and for odd q their two
weights are never equal. That is exactly what the tight-case argument needs,
so the depth-2 tight case dies at every odd q whose minimum blockers are all
of this kind -- proved at q = 3 and 5, and the classification at q = 7 is the
open input.

THE CONSTRUCTION.  Let u != v be collinear points of W(3,q) on the line L0.
The plane v^perp contains u and L0, and its other q lines through u are
hyperbolic: call them h_1, ..., h_q. Each h_i^perp is a hyperbolic line through
v inside u^perp. For any S subset {1..q} with 1 <= |S| <= q-1 put

    B(u,v,S) = (L0 - {u,v})  u  U_{i in S} (h_i - {u})  u  U_{i not in S} (h_i^perp - {v}).

THEOREM (all q).  B(u,v,S) is a blocking set of size q^2+q-1 with line excess

    e  =  a pencil(u) + b pencil(v),     a = q-1-|S|,   b = |S|-1,   a + b = q-2.

PROOF.  The pieces are disjoint: L0 lies in u^perp n v^perp; h_i - {u} lies in
v^perp but off u^perp; h_j^perp - {v} lies in u^perp but off v^perp; distinct
h_i meet only at u, distinct h_j^perp only at v. So |B| = (q-1) + |S|q +
(q-|S|)q = q^2+q-1. Now take a totally isotropic line M.
  * M = L0: q-1 points, excess q-2 = a+b.
  * M through u, M != L0: M lies in u^perp and meets v^perp only at u, so it
    misses every h_i - {u} and L0 - {u,v}; each h_j^perp is a line of the plane
    u^perp not through u, so M meets it in one point, not v. Count q-|S| = 1+a.
  * M through v, M != L0: symmetric, count |S| = 1+b.
  * M through neither, meeting L0 at w: w is in B, and M meets u^perp and v^perp
    only at w, which lies on no h_i or h_j^perp. Count 1.
  * M through neither, missing L0: M meets v^perp in one point m_v, which lies
    on exactly one h_i, and u^perp in one point m_u, on exactly one h_j^perp.
    Since h_i = <u, m_v>, h_i^perp = u^perp n m_v^perp, and m_u is in u^perp and
    collinear with m_v on M, so m_u lies on h_i^perp: j = i. The count is
    [i in S] + [i not in S] = 1.                                          []

|S| = 1 or q-1 gives the octet blockers B(c,L) = (Adj(c) - L^perp) u (L - {c})
of the_blockers_in_closed_form.py; 2 <= |S| <= q-2 gives genuine two-centre
blockers, first appearing at q = 5 (the_q5_tight_case_dies_without_the_centre_property.py).

COUNT.  Octet kind (q+1)(q^2+1) q^2; two-centre kind (q+1)^2 (q^2+1) q (2^q-2q-2)/2:
360 at q = 3, 3,900 + 46,800 = 50,700 at q = 5 (the proved census), and
19,600 + 1,254,400 = 1,274,000 at q = 7.

THE PARITY.  For odd q, a + b = q-2 is odd, so a != b: one centre is strictly
heavier, with weight at least (q-1)/2, and the lighter has at most (q-3)/2. For
even q ties occur -- but W(3,q) then has ovoids and none of this is needed.

CONDITIONAL THEOREM (odd q).  Suppose tau_1(W(3,q)) = q^2+q-1 and every minimum
blocker is a B(u,v,S). Then tau_2(W(3,q)^2) > (q^2+1)(q^2+q-1).
  Proof. At the tight size every row and column shadow is a minimum blocker and
  E[L][M] = a_L[u_L in M] + b_L[v_L in M] = a'_M[u'_M in L] + b'_M[v'_M in L],
  heavier centres u_L, u'_M. Since a >= (q-1)/2 > (q-3)/2 >= b, thresholding at
  (q-1)/2 gives u_L in M <=> u'_M in L: the centre reciprocity. Steps 4-6 of
  gq_tight_case_theorem.py and the mixing lemma of gq_diagonal_theorem.py then
  produce an ovoid or a duality of W(3,q), neither of which exists for q odd. []

STATUS OF THE HYPOTHESIS.
  q = 3   360 minimum blockers, all octet blockers (proved in this repository)
  q = 5   50,700, exactly this family (b9f5d5b)
  q = 7   tau_1 = 55 (9d5751e); family verified; that it is EVERYTHING is being
          checked (all patterns on at most 3 points and all 330+792 line-heavy
          patterns done; 5-point patterns and the x = 5 pencil lemma running)
  q >= 9  open; the construction gives tau_1(W(3,q)) <= q^2+q-1 for all q.

CHECKED HERE.  Every B(u,v,S) through a fixed u is built and verified as a
blocker of the stated size and excess at q = 3, 5, 7 (0 failures), with the
distinct-blocker counts through u matching the formulas.

SCOPE.  The construction and the parity are proofs for all q; the conditional
theorem is a proof from results already in this repository; its hypothesis is
proved at q = 3 and 5 only.
"""

import argparse
import itertools
import json
import os
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def check(q):
    def nm(v):
        i = next(k for k, x in enumerate(v) if x % q)
        z = pow(v[i] % q, -1, q)
        return tuple((z * x) % q for x in v)
    pts = sorted({nm(v) for v in itertools.product(range(q), repeat=4) if any(v)})
    idx = {p: i for i, p in enumerate(pts)}
    n = len(pts)

    def sf(a, b):
        return (pts[a][0] * pts[b][2] - pts[a][2] * pts[b][0] + pts[a][1] * pts[b][3] - pts[a][3] * pts[b][1]) % q

    def span(a, b):
        return frozenset(idx[nm(tuple((x * pts[a][k] + y * pts[b][k]) % q for k in range(4)))]
                         for x in range(q) for y in range(q) if x or y)
    perp = [frozenset(j for j in range(n) if sf(i, j) == 0) for i in range(n)]
    lines = list({span(a, b) for a in range(n) for b in perp[a] if b > a})
    assert len(lines) == n

    def lperp(L):
        return frozenset.intersection(*[perp[i] for i in L])
    u = 0
    built, failures = {}, 0
    for v in sorted(perp[u] - {u}):
        L0 = span(u, v)
        hs = sorted({span(u, w) for w in perp[v] - L0}, key=sorted)
        assert len(hs) == q
        for s in range(1, q):
            for S in itertools.combinations(range(q), s):
                B = set(L0 - {u, v})
                for i in range(q):
                    B |= (hs[i] - {u}) if i in S else (lperp(hs[i]) - {v})
                B = frozenset(B)
                a, b = q - 1 - s, s - 1
                if not (len(B) == q * q + q - 1
                        and all(len(B & L) == 1 + a * (u in L) + b * (v in L) for L in lines)):
                    failures += 1
                built.setdefault(B, (a, b))
    kinds = Counter()
    for B, (a, b) in built.items():
        kinds["octet" if min(a, b) == 0 else "twoCentre"] += 1
    return {"q": q, "points": n, "failures": failures, "distinctThroughU": len(built),
            "octetKindThroughU": kinds["octet"], "twoCentreThroughU": kinds["twoCentre"],
            "octetTotal": (q + 1) * (q * q + 1) * q * q,
            "twoCentreTotal": (q + 1) ** 2 * (q * q + 1) * q * (2 ** q - 2 * q - 2) // 2}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    rows = [check(q) for q in (3, 5, 7)]
    print("THE TWO-CENTRE OCTET FAMILY IS q-GENERAL")
    print("=" * 74)
    for r in rows:
        q = r["q"]
        print("  q=%d: failures %d; distinct through u %d (octet kind %d, two-centre %d); totals %d + %d = %d"
              % (q, r["failures"], r["distinctThroughU"], r["octetKindThroughU"], r["twoCentreThroughU"],
                 r["octetTotal"], r["twoCentreTotal"], r["octetTotal"] + r["twoCentreTotal"]))
    # through a fixed u: octets centred at u (q^2) + for each of the q(q+1) neighbours v the q octets
    # centred at v whose hyperbolic line lies in u^perp; two-centre with u a centre: q(q+1) x (2^q-2q-2)
    ok = all(r["failures"] == 0 for r in rows)
    for r in rows:
        q = r["q"]
        ok = ok and r["octetKindThroughU"] == q * q * (q + 2) \
            and r["twoCentreThroughU"] == q * (q + 1) * (2 ** q - 2 * q - 2)
    ok = ok and rows[0]["octetTotal"] + rows[0]["twoCentreTotal"] == 360 \
        and rows[1]["octetTotal"] + rows[1]["twoCentreTotal"] == 50700
    print()
    print("VALID: %s" % ok)

    if args.write:
        assert ok, "checks failed -- refusing to write"
        rec = {
            "schema": "holotrade.two-centre-octet-family.v1",
            "valid": True,
            "checks": rows,
            "construction": (
                "for collinear u != v on L0, the q hyperbolic lines h_i through u in v^perp, and 1 <= |S| <= q-1: "
                "B = (L0 - {u,v}) u U_{i in S}(h_i - {u}) u U_{i not in S}(h_i^perp - {v})."),
            "theorem": (
                "for every q, B is a blocking set of size q^2+q-1 with excess (q-1-|S|) pencil(u) + (|S|-1) pencil(v); "
                "the key case is a line M missing L0, whose points in v^perp and u^perp lie on h_i and h_i^perp for "
                "the SAME i because h_i^perp = u^perp n m_v^perp."),
            "counts": "octet kind (q+1)(q^2+1)q^2; two-centre (q+1)^2(q^2+1)q(2^q-2q-2)/2; 360, 50700, 1274000",
            "parity": "for odd q the weights sum to q-2, odd, so they are never equal",
            "conditionalTheorem": (
                "if tau_1(W(3,q)) = q^2+q-1 and every minimum blocker is in the family, q odd, then "
                "tau_2(W(3,q)^2) > (q^2+1)(q^2+q-1): thresholding the tile excess at (q-1)/2 recovers the heavier "
                "centres, gives centre reciprocity, and forces an ovoid or a duality."),
            "hypothesisStatus": (
                "proved at q = 3 (360 octet blockers) and q = 5 (b9f5d5b); q = 7 has tau_1 = 55 (9d5751e) and the "
                "completeness check is running; open for q >= 9. The construction gives tau_1 <= q^2+q-1 for all q."),
            "boundary": (
                "construction and parity proved for all q and verified at q = 3, 5, 7 with 0 failures; conditional "
                "theorem proved from repository results; hypothesis proved only at q = 3 and 5."),
        }
        p = os.path.join(ROOT, "data", "two_centre_octet_family.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=2)
        print("written: %s" % p)


if __name__ == "__main__":
    main()
