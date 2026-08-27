#!/usr/bin/env python3
"""
A cyclotomic bridge between the two tracks, built and then killed at q=5.

THE TEMPTATION.  The other track's Pass 10605-10612 proves the 3-5-7 harmonic
factorization is an arithmetic fingerprint of q=3, and the three primes are
cyclotomic values there:

    q = 3,      Phi_4(3)/2 = (q^2+1)/2 = 5,      Phi_6(3) = q^2-q+1 = 7,
    3 * 5 * 7 = 105.

Both of those cyclotomic values already live in this repository's W(3,3) work,
and they land on exactly the two quantities the ovoid-defect story is about:

    ovoid size of W(3,q)          = st + 1 = q^2 + 1 = Phi_4(q),   = 10 at q=3
    independence number alpha     = 7                              = Phi_6(3)
    coclique deficit              = 10 - 7 = 3                     = q

That is a beautiful fit.  alpha = Phi_6(q), the deficit is exactly q, and the
seven in their harmonic cube would be the SAME seven as W(3,3)'s independence
number -- the very quantity that makes the quadrangle ovoid-free and opens the
depth-2 blocking interval.  It would tie the two tracks together through the
cyclotomic arithmetic rather than through a numerical coincidence.

IT IS FALSE.  The prediction at the next odd prime is alpha(W(3,5)) = Phi_6(5)
= 21, with deficit q = 5 against the ovoid size Phi_4(5) = 26.  Computing it:

    alpha(W(3,5)) = 18,      not 21.
    coclique deficit = 26 - 18 = 8,     not 5.

So alpha = Phi_6(q) is an accident at q = 3 and nothing more.  The two sevens
stay unrelated, exactly as the earlier no-go said, and now with evidence
rather than only caution behind it.

HOW alpha(W(3,5)) = 18 IS ESTABLISHED, since it is the load-bearing number.
W(3,5) is built from scratch: the 156 points of PG(3,5) normalised by leading
coordinate, adjacency by vanishing of the symplectic form
u0v1 - u1v0 + u2v3 - u3v2 over F_5.  The graph is confirmed to be
SRG(156, 30, 4, 6) = SRG((q+1)(q^2+1), q(q+1), q-1, q+1).  Then:

  * an explicit 18-point set is produced and checked FROM THE FORM directly --
    all 153 pairs have non-vanishing symplectic form, and all 18 points are
    projectively distinct -- so alpha >= 18 independently of any solver;
  * size 19 is proved INFEASIBLE, so alpha <= 18.

A note on trusting recollection over computation.  A Tallini-type bound of
(q^2+q+2)/2 came to mind while writing this, which would give 16 at q=5 and
forbid the answer.  It matches at q=3 (giving 7) and fails here.  The explicit
witness above is verified against the defining form, so the computation stands
and the half-remembered bound does not apply to this object.  Recording that
rather than quietly deferring to the vaguer memory.

WHAT SURVIVES.  Only the q=3 facts, which were already ours: alpha(W(3,3)) = 7
against a Hoffman bound of 10, a coclique deficit of 3, and a blocking ovoid
defect of 1.  Their 3-5-7 cube remains a q=3 phenomenon on their side, and the
Lagrange obstruction still says no C7 acts on W(3,3) at all.  Two different
q=3 exceptionalities meeting at the number seven is weaker evidence of a
shared object, not stronger: many things are special at q = 3.
"""

import itertools
import json
import os
import sys

try:
    from ortools.sat.python import cp_model
except ImportError:
    sys.exit("needs ortools:  py -3 -m pip install ortools")

ROOT = r"C:\Repos\Holotrade"


def phi(n, q):
    return {1: q - 1, 2: q + 1, 3: q * q + q + 1,
            4: q * q + 1, 6: q * q - q + 1}[n]


def build_w3q(q):
    """Points of PG(3,q) and the symplectic collinearity graph of W(3,q)."""
    pts = []
    for v in itertools.product(range(q), repeat=4):
        if not any(v):
            continue
        i = next(k for k in range(4) if v[k])
        if v[i] != 1:
            continue
        pts.append(v)

    def form(u, v):
        return (u[0] * v[1] - u[1] * v[0] + u[2] * v[3] - u[3] * v[2]) % q

    assert all(form(p, p) == 0 for p in pts), "the form must be alternating"
    n = len(pts)
    adj = [[False] * n for _ in range(n)]
    for i, j in itertools.combinations(range(n), 2):
        if form(pts[i], pts[j]) == 0:
            adj[i][j] = adj[j][i] = True
    return pts, adj, form


def srg_params(adj):
    n = len(adj)
    deg = {sum(r) for r in adj}
    lam, mu = set(), set()
    for i, j in itertools.combinations(range(n), 2):
        c = sum(1 for k in range(n) if adj[i][k] and adj[j][k])
        (lam if adj[i][j] else mu).add(c)
    return n, sorted(deg), sorted(lam), sorted(mu)


def alpha(adj, seconds=90):
    n = len(adj)
    m = cp_model.CpModel()
    x = [m.NewBoolVar("") for _ in range(n)]
    for i, j in itertools.combinations(range(n), 2):
        if adj[i][j]:
            m.AddAtMostOne([x[i], x[j]])
    m.Maximize(sum(x))
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = float(seconds)
    s.parameters.num_search_workers = 8
    st = s.Solve(m)
    return (int(s.ObjectiveValue()), s.StatusName(st),
            [i for i in range(n) if s.Value(x[i])])


def infeasible_at(adj, target, seconds=60):
    n = len(adj)
    m = cp_model.CpModel()
    x = [m.NewBoolVar("") for _ in range(n)]
    for i, j in itertools.combinations(range(n), 2):
        if adj[i][j]:
            m.AddAtMostOne([x[i], x[j]])
    m.Add(sum(x) == target)
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = float(seconds)
    s.parameters.num_search_workers = 8
    return s.StatusName(s.Solve(m))


def main():
    print("A CYCLOTOMIC BRIDGE, BUILT AND THEN KILLED")
    print("=" * 70)
    print("  their 3-5-7 is cyclotomic at q=3:")
    print("    q = 3,  Phi_4(3)/2 = %d,  Phi_6(3) = %d,  product = %d"
          % (phi(4, 3) // 2, phi(6, 3), 3 * (phi(4, 3) // 2) * phi(6, 3)))
    print("  and both land on W(3,3) quantities:")
    print("    ovoid size = st+1 = Phi_4(3) = %d" % phi(4, 3))
    print("    alpha(W(3,3))               = 7  = Phi_6(3) = %d" % phi(6, 3))
    print("    coclique deficit            = %d = q" % (phi(4, 3) - 7))
    print()
    print("  PREDICTION at q=5: alpha = Phi_6(5) = %d, deficit = q = 5"
          % phi(6, 5))
    print()

    rows = []
    for q, known in ((3, 7), (5, None)):
        pts, adj, form = build_w3q(q)
        n, deg, lam, mu = srg_params(adj)
        exp = (( q + 1) * (q * q + 1), [q * (q + 1)], [q - 1], [q + 1])
        is_w = (n, deg, lam, mu) == exp
        a, status, S = alpha(adj, 90 if q > 3 else 30)
        # first-principles check of the witness, straight from the form
        bad = sum(1 for i, j in itertools.combinations(S, 2)
                  if form(pts[i], pts[j]) == 0)
        distinct = len({pts[i] for i in S}) == len(S)
        nxt = infeasible_at(adj, a + 1, 60 if q > 3 else 20)
        pred = phi(6, q)
        rows.append({
            "q": q, "points": n, "srgConfirmed": is_w,
            "ovoidSize": phi(4, q), "alpha": a, "alphaStatus": status,
            "witnessCollinearPairs": bad, "witnessDistinct": distinct,
            "nextSizeStatus": nxt,
            "phi6": pred, "alphaEqualsPhi6": a == pred,
            "cocliqueDeficit": phi(4, q) - a,
            "deficitEqualsQ": phi(4, q) - a == q,
        })
        print("  W(3,%d): %d points, SRG confirmed %s" % (q, n, is_w))
        print("    alpha = %d (%s); size %d is %s" % (a, status, a + 1, nxt))
        print("    witness: %d collinear pairs, all distinct %s"
              % (bad, distinct))
        print("    Phi_6(%d) = %d -> alpha = Phi_6? %s" % (q, pred, a == pred))
        print("    deficit = %d - %d = %d -> equals q? %s"
              % (phi(4, q), a, phi(4, q) - a, phi(4, q) - a == q))
        print()

    held = rows[0]["alphaEqualsPhi6"]
    broke = not rows[1]["alphaEqualsPhi6"]
    print("  ==> the identification holds at q=3 and FAILS at q=5.")
    print("      alpha = Phi_6(q) is an accident at q=3, not a pattern.")
    print("      The two sevens stay unrelated -- now with evidence behind it,")
    print("      not only caution.")

    ok = (held and broke and rows[1]["alpha"] == 18
          and rows[1]["nextSizeStatus"] == "INFEASIBLE"
          and rows[1]["witnessCollinearPairs"] == 0
          and all(r["srgConfirmed"] for r in rows))

    if "--write" in sys.argv:
        out = os.path.join(ROOT, "data", "w33_cyclotomic_bridge_killed.json")
        with open(out, "w") as fh:
            json.dump({
                "schema": "holotrade.w33-cyclotomic-bridge-killed.v1",
                "valid": ok,
                "temptation": ("their 3-5-7 is cyclotomic at q=3, and "
                               "Phi_4(3)=10 is W(3,3)'s ovoid size while "
                               "Phi_6(3)=7 is its independence number, with "
                               "coclique deficit exactly q"),
                "prediction": "alpha(W(3,q)) = Phi_6(q), deficit = q",
                "instances": rows,
                "verdict": "FALSE -- holds at q=3, fails at q=5",
                "alphaW35": 18,
                "alphaW35Establishment": ("explicit 18-point set checked "
                                          "against the symplectic form itself "
                                          "(zero collinear pairs, all "
                                          "projectively distinct), plus size 19 "
                                          "proved INFEASIBLE"),
                "recollectionNote": ("a Tallini-type bound (q^2+q+2)/2 came to "
                                     "mind, giving 16 at q=5 and forbidding "
                                     "this; it matches at q=3 and fails here. "
                                     "The witness is verified against the "
                                     "defining form, so the computation stands "
                                     "and the recollection does not apply"),
                "whatSurvives": ("only the q=3 facts, already ours: alpha = 7 "
                                 "against Hoffman 10, coclique deficit 3, "
                                 "blocking ovoid defect 1"),
                "boundary": ("two different q=3 exceptionalities meeting at the "
                             "number seven is weaker evidence of a shared "
                             "object, not stronger; many things are special at "
                             "q=3, and the Lagrange obstruction still says no "
                             "C7 acts on W(3,3) at all"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(out, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
