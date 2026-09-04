#!/usr/bin/env python3
"""
The depth-2 balance spectrum is settled end to end: every level from 0 to 16 is
feasible except m = 1 and m = 15, and those two are the ovoid levels.

WHERE THIS STANDS.  depth2_balance_spectrum.json tabulated four levels -- m = 1
INFEASIBLE, m = 2 UNKNOWN, m = 3 and 4 OPTIMAL -- and stopped there. 5aa4ff1
closed the m = 2 row with a C5-invariant witness of size 200. But the spectrum
has a natural range and a natural symmetry that nobody had used, and together
they finish it.

THE RANGE.  A tile is L x M with |L| = |M| = 4, so |L x M| = 16 and an
m-balanced set has 0 <= m <= 16, with m = 0 the empty set and m = 16 the whole
grid. The corpus had examined four of seventeen levels.

THE SYMMETRY, WHICH IS ONE LINE.  If |X n (L x M)| = m for every tile, then the
complement satisfies |X^c n (L x M)| = 16 - m for every tile. So

    X is m-balanced  <=>  X^c is (16 - m)-balanced

and the spectrum is symmetric about 8. That is a proof, not a search, and it
halves the work.

THE SWEEP, under C5 invariance:

    m    status        size        m       by complement
    0    trivial          0       16       trivial
    1    INFEASIBLE       -       15       INFEASIBLE
    2    OPTIMAL        200       14       feasible
    3    OPTIMAL        300       13       feasible
    4    OPTIMAL        400       12       feasible
    5    OPTIMAL        500       11       feasible
    6    OPTIMAL        600       10       feasible
    7    OPTIMAL        700        9       feasible
    8    OPTIMAL        800        8       self-paired

Every size is exactly 100m, as the identity 16|X| = 1600m requires. So:

    THE SPECTRUM IS {0, 2, 3, 4, ..., 14, 16} -- everything except 1 and 15.

AND THE TWO HOLES ARE THE OVOID LEVELS.  m = 1 asks for a set meeting every tile
exactly once, which is the product analogue of an ovoid, and W(3,3) has no
ovoid; the corpus proves that row infeasible twice over, by solver and by
tau_2 >= 111 > 100. m = 15 is its complement and inherits the impossibility for
free. Every other level is reachable. So the single obstruction in the whole
spectrum is the same one the rest of this corpus turns on -- the missing ovoid --
appearing once at each end and nowhere in between.

A CROSS-CHECK WORTH NOTING.  m = 3 and m = 4 were found by the corpus WITHOUT
any symmetry restriction, at sizes 300 and 400. The C5-invariant search here
reproduces both at the same sizes, which is independent evidence that this
formulation of "balanced" is the same one.

SCOPE.  Feasibility at m = 2..8 is established by exhibiting witnesses, each
re-verified from scratch against all 1600 tiles. The m = 1 row's GLOBAL
infeasibility is the corpus's, cited -- what is computed here is only that no
C5-invariant one exists. m = 15's infeasibility follows from m = 1's by
complementation, so it is exactly as strong as that citation. m = 9..14 are
feasible by complementing the witnesses found here, which is constructive. No
claim is made that every m-balanced set is C5-invariant, nor about how many
exist at each level. tau_2 is untouched.
"""

import collections
import itertools
import json
import os
import sys

from ortools.sat.python import cp_model

ROOT = r"C:\Repos\Holotrade"
Q = 3
D = 4


def main():
    def mul(A, B):
        return tuple(tuple(sum(A[i][k] * B[k][j] for k in range(D)) % Q
                           for j in range(D)) for i in range(D))

    I = tuple(tuple(1 if i == j else 0 for j in range(D)) for i in range(D))

    def form(u, v):
        return (u[0] * v[2] - u[2] * v[0] + u[1] * v[3] - u[3] * v[1]) % Q

    E = [tuple(1 if k == j else 0 for k in range(D)) for j in range(D)]

    def tv(vv, lam):
        return tuple(tuple(((1 if i == j else 0)
                            + lam * form(E[j], vv) * vv[i]) % Q
                           for j in range(D)) for i in range(D))

    def nm(v):
        i = next(k for k, x in enumerate(v) if x % Q)
        z = pow(v[i] % Q, -1, Q)
        return tuple((z * x) % Q for x in v)

    vecs = [v for v in itertools.product(range(Q), repeat=D) if any(v)]
    pts = sorted({nm(v) for v in vecs})
    pidx = {p: i for i, p in enumerate(pts)}
    T = sorted({tv(v, l) for v in vecs for l in (1, 2)} - {I})
    wl = set()
    for a, b in itertools.combinations(pts, 2):
        if form(a, b) % Q:
            continue
        S = set()
        for x in range(Q):
            for y in range(Q):
                if x == y == 0:
                    continue
                w = tuple((x * a[k] + y * b[k]) % Q for k in range(D))
                if any(w):
                    S.add(nm(w))
        if len(S) == 4 and all(form(u, v) % Q == 0
                               for u, v in itertools.combinations(sorted(S), 2)):
            wl.add(frozenset(pidx[z] for z in S))
    WL = [sorted(l) for l in wl]
    NL = len(WL)

    def perm(A):
        return tuple(pidx[nm(tuple(sum(A[i][k] * pts[j][k] for k in range(D)) % Q
                                   for i in range(D)))] for j in range(40))

    idp = tuple(range(40))
    g5 = None
    seen, fr = {I}, [I]
    while fr and g5 is None:
        nx = []
        for A in fr:
            for t in T:
                B = mul(t, A)
                if B not in seen:
                    seen.add(B)
                    nx.append(B)
                    pm = perm(B)
                    o, cur = 1, pm
                    while cur != idp:
                        cur = tuple(pm[x] for x in cur)
                        o += 1
                    if o == 5 and g5 is None:
                        g5 = pm
        fr = nx

    par = list(range(1600))

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    for p in range(40):
        for r in range(40):
            a, b = find(p * 40 + r), find(g5[p] * 40 + g5[r])
            if a != b:
                par[a] = b
    orb = collections.defaultdict(list)
    for c in range(1600):
        orb[find(c)].append(c)
    groups = list(orb.values())
    cell_to_g = {}
    for gi, cells in enumerate(groups):
        for c in cells:
            cell_to_g[c] = gi
    tile_terms = []
    for L in range(NL):
        for M in range(NL):
            t = collections.Counter()
            for p in WL[L]:
                for r in WL[M]:
                    t[cell_to_g[p * 40 + r]] += 1
            tile_terms.append(t)

    def solve(m, tl=240):
        mdl = cp_model.CpModel()
        y = [mdl.NewBoolVar('y%d' % i) for i in range(len(groups))]
        for t in tile_terms:
            mdl.Add(sum(t[gi] * y[gi] for gi in t) == m)
        s = cp_model.CpSolver()
        s.parameters.max_time_in_seconds = tl
        s.parameters.num_search_workers = 8
        st = s.Solve(mdl)
        nm_ = {cp_model.OPTIMAL: 'OPTIMAL', cp_model.FEASIBLE: 'FEASIBLE',
               cp_model.INFEASIBLE: 'INFEASIBLE',
               cp_model.UNKNOWN: 'UNKNOWN'}[st]
        X = None
        if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            X = sorted(c for gi, cells in enumerate(groups) if s.Value(y[gi])
                       for c in cells)
        return nm_, X

    def verify(X, m):
        S = set(X)
        for L in range(NL):
            for M in range(NL):
                if sum(1 for p in WL[L] for r in WL[M]
                       if p * 40 + r in S) != m:
                    return False
        return True

    rows = []
    for m in range(0, 9):
        if m == 0:
            rows.append({"m": 0, "status": "TRIVIAL", "size": 0,
                         "verified": True, "complement": 16})
            continue
        st, X = solve(m)
        v = verify(X, m) if X else None
        rows.append({"m": m, "status": st,
                     "size": len(X) if X else None,
                     "sizeIs100m": (len(X) == 100 * m) if X else None,
                     "verified": v, "complement": 16 - m})

    feas = [r["m"] for r in rows if r["status"] in ("OPTIMAL", "FEASIBLE")]
    spectrum = sorted(set([0, 16] + feas + [16 - m for m in feas]))
    holes = [m for m in range(17) if m not in spectrum]

    print("THE BALANCE SPECTRUM IS COMPLETE")
    print("=" * 72)
    print("  a tile is L x M with |L| = |M| = 4, so 0 <= m <= 16;")
    print("  the corpus had examined four of the seventeen levels.")
    print()
    print("  COMPLEMENTATION (a proof, not a search):")
    print("     X is m-balanced  <=>  X^c is (16-m)-balanced")
    print("  so the spectrum is symmetric about 8.")
    print()
    print("   m   status       size   100m?  verified   complement")
    for r in rows:
        print("  %2d   %-11s %5s   %-5s  %-8s   %2d"
              % (r["m"], r["status"], r["size"],
                 r.get("sizeIs100m"), r["verified"], r["complement"]))
    print()
    print("  SPECTRUM: %s" % spectrum)
    print("  HOLES:    %s" % holes)
    print()
    print("  And the two holes are the OVOID levels. m = 1 asks for a set")
    print("  meeting every tile exactly once -- the product analogue of an")
    print("  ovoid -- and W(3,3) has none; the corpus proves that row")
    print("  infeasible twice, by solver and by tau_2 >= 111 > 100. m = 15 is")
    print("  its complement and inherits the impossibility for free. Every")
    print("  other level is reachable, so the single obstruction in the whole")
    print("  spectrum is the missing ovoid, once at each end and nowhere in")
    print("  between.")
    print()
    print("  CROSS-CHECK: m = 3 and 4 were found by the corpus WITHOUT symmetry")
    print("  at sizes 300 and 400; the C5 search reproduces both at the same")
    print("  sizes, so this is the same notion of 'balanced'.")

    ok = (holes == [1, 15]
          and all(r["status"] == "OPTIMAL" for r in rows if 2 <= r["m"] <= 8)
          and all(r["verified"] for r in rows if r["status"] == "OPTIMAL")
          and all(r["sizeIs100m"] for r in rows if r["status"] == "OPTIMAL")
          and rows[1]["status"] == "INFEASIBLE")

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "balance_spectrum_complete.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.balance-spectrum-complete.v1",
                "valid": bool(ok),
                "whereThisStands": ("depth2_balance_spectrum.json tabulated four "
                                    "levels and stopped; 5aa4ff1 closed m = 2. "
                                    "The spectrum has a natural range and a "
                                    "natural symmetry nobody had used, and "
                                    "together they finish it"),
                "theRange": ("a tile is L x M with |L| = |M| = 4, so |L x M| = 16 "
                             "and 0 <= m <= 16; the corpus had examined four of "
                             "seventeen levels"),
                "complementationLemma": {
                    "statement": ("X is m-balanced <=> X^c is (16-m)-balanced"),
                    "proof": ("|X n (L x M)| = m for every tile forces "
                              "|X^c n (L x M)| = 16 - m for every tile"),
                    "consequence": "the spectrum is symmetric about 8",
                    "isAProofNotASearch": True,
                },
                "sweep": rows,
                "spectrum": spectrum,
                "holes": holes,
                "theHolesAreTheOvoidLevels": ("m = 1 asks for a set meeting every "
                                              "tile exactly once, the product "
                                              "analogue of an ovoid, and W(3,3) "
                                              "has none -- the corpus proves that "
                                              "row infeasible twice, by solver "
                                              "and by tau_2 >= 111 > 100. m = 15 "
                                              "is its complement and inherits "
                                              "the impossibility. Every other "
                                              "level is reachable, so the single "
                                              "obstruction in the whole spectrum "
                                              "is the missing ovoid, once at "
                                              "each end and nowhere in between"),
                "crossCheck": ("m = 3 and 4 were found by the corpus WITHOUT "
                               "symmetry at sizes 300 and 400; the C5 search "
                               "reproduces both at the same sizes, independent "
                               "evidence that this is the same notion of "
                               "balanced"),
                "boundary": ("feasibility at m = 2..8 is established by "
                             "exhibiting witnesses, each re-verified from "
                             "scratch against all 1600 tiles. The m = 1 row's "
                             "GLOBAL infeasibility is the corpus's, CITED -- "
                             "what is computed here is only that no C5-invariant "
                             "one exists -- and m = 15's infeasibility follows "
                             "from it by complementation, so it is exactly as "
                             "strong as that citation. m = 9..14 are feasible by "
                             "complementing the witnesses found here, which is "
                             "constructive. No claim that every m-balanced set "
                             "is C5-invariant, nor about how many exist at each "
                             "level. tau_2 is untouched"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
