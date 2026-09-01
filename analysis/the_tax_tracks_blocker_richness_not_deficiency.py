#!/usr/bin/env python3
"""
The composition tax tracks the RICHNESS of the minimum-blocker family, and
richness is the t-versus-s trichotomy. W(3,3) is rich because it is diagonal.

THE QUESTION THIS ANSWERS.  the_open_configuration_has_a_smaller_instance.py
found two instances of the open configuration -- W(3,3)^2 and GQ(2,4)^2, both
ovoid-free, both of deficiency exactly 1 -- behaving differently: W(3,3)^2
beats its product bound (115 < 121) and GQ(2,4)^2 was never seen below it
(100 = 100). It concluded the tax is not a function of the deficiency alone
and left the obvious follow-up unanswered: then what is it a function of?

IT IS NOT THE CENTRE THEOREM.  For W(3,3), a minimum blocker has 11 points,
meets 36 lines once and 4 twice, and the four doubled lines form a PENCIL.
That centre theorem is the spine of the whole tight-case analysis. GQ(2,4) has
the same shape -- 10 points, 50 incidences over 45 lines, so 40 lines once and
5 twice, and a pencil in GQ(2,4) has exactly 5 lines -- and the property
HOLDS, on every one of its minimum blockers. So the difference is not there.

IT IS THE COUNT.

    GQ(2,4)   t = 4 > s = 2     27 minimum blockers   1.00 per point
    W(3,3)    s = t = 3        360 minimum blockers   9.00 per point

Nine times as rich, and 9 = q^2. Every one of GQ(2,4)'s 27 is the punctured
perp c^perp minus {c}, one for each of its 27 points; not one of W(3,3)'s 360 is a
perp at all.

AND THE CAUSE IS ALREADY PROVED HERE.  gq_perp_blockers_and_h44.py shows the
minimum blockers of a GQ are exactly the point-perps when t > s, of size
s(t+1), and names W(3,3) as the exception: there s = t, and
tau_1 = 11 < s(t+1) = 12, so the perps are not minimal and something else has
to be. That trichotomy is the whole story.

  * t > s  ->  blockers ARE the perps: one per point, maximally rigid.
  * s = t  ->  the diagonal case, perps are too big, and the blocker family
               opens up. gq_diagonal_theorem.py already shows this case is
               provably beyond counting.

So the chain closes: the tax is a function of blocker richness, richness is
the trichotomy, and W(3,3) is hard because it sits on the diagonal. The
deficiency is 1 in both cases and never had anything to do with it.

WHY RICHNESS SHOULD MATTER, stated as the reading it is. A product of two
minimum blockers always blocks, at cost tau_1 * tau_1. To do better, the row
shadows must be blocking sets that SHARE structure across rows -- and with one
blocker per centre there is nothing to choose. With nine there is. That is
consistent with both instances and is an explanation, not a theorem.

THE PREDICTION IT MAKES.  Any ovoid-free GQ with t > s should have
tau(G x G) = tau_1^2 exactly, and the difficulty should be confined to the
diagonal s = t. That is falsifiable on the next such quadrangle anyone can
compute, and it is not tested here.

SCOPE.  Both blocker enumerations are complete within budget and their counts
are consistent with transitivity (27 = 27 x 1, 360 = 40 x 9). The centre-theorem
and perp checks are exhaustive over those families. The link from richness to
the product behaviour is an explanation consistent with two instances, not a
proof, and the prediction is untested. tau_2 is untouched and stays open in
[111, 115].
"""

import collections
import itertools
import json
import os
import sys

ROOT = r"C:\Repos\Holotrade"
Q = 3
N = 40


def main():
    from ortools.sat.python import cp_model

    def nm(v):
        i = next(k for k, x in enumerate(v) if x % Q)
        z = pow(v[i] % Q, -1, Q)
        return tuple((z * x) % Q for x in v)

    def form(u, v):
        return (u[0] * v[1] - u[1] * v[0] + u[2] * v[3] - u[3] * v[2]) % Q

    pts = sorted({nm(v) for v in itertools.product(range(Q), repeat=4)
                  if any(v)})
    idx = {v: i for i, v in enumerate(pts)}

    def span(a, b):
        S = set()
        for x in range(Q):
            for y in range(Q):
                if x == y == 0:
                    continue
                w = tuple((x * pts[a][k] + y * pts[b][k]) % Q for k in range(4))
                if any(w):
                    S.add(idx[nm(w)])
        return tuple(sorted(S))

    alll = sorted({span(a, b) for a, b in itertools.combinations(range(N), 2)
                   if len(span(a, b)) == 4})
    S = [set(L) for L in alll]
    isof = [all(form(pts[x], pts[y]) == 0
                for x, y in itertools.combinations(L, 2)) for L in alll]
    iso = [i for i in range(len(alll)) if isof[i]]
    W_lines = [tuple(sorted(alll[i])) for i in iso]
    hyp = [i for i in range(len(alll)) if not isof[i]]
    lut = {L: i for i, L in enumerate(alll)}

    def perp(li):
        return lut[tuple(sorted(p for p in range(N)
                                if all(form(pts[p], pts[u]) == 0
                                       for u in alll[li])))]

    pm = {i: perp(i) for i in range(len(alll))}
    polar = sorted({frozenset((i, pm[i])) for i in hyp}, key=sorted)
    pid = {}
    for n_, P in enumerate(polar):
        for x in P:
            pid[x] = n_
    edges = set()
    for t in itertools.combinations(iso, 3):
        if (S[t[0]] & S[t[1]]) or (S[t[0]] & S[t[2]]) or (S[t[1]] & S[t[2]]):
            continue
        tr = [m for m in range(len(alll)) if all(S[m] & S[x] for x in t)]
        if any(isof[m] for m in tr):
            continue
        edges.add(frozenset(pid[m] for m in tr))
    adj = collections.defaultdict(set)
    for e in edges:
        a, b = tuple(e)
        adj[a].add(b)
        adj[b].add(a)
    out = []

    def cl(R, P, X):
        if not P and not X:
            out.append(frozenset(R))
            return
        piv = max(P | X, key=lambda u: len(adj[u] & P))
        for v in list(P - adj[piv]):
            cl(R | {v}, P & adj[v], X & adj[v])
            P = P - {v}
            X = X | {v}

    cl(set(), set(range(45)), set())
    K5 = [c for c in out if len(c) == 5]
    gq24 = [tuple(sorted(i for i, c in enumerate(K5) if v in c))
            for v in range(45)]

    def study(n, L, size, label, s_, t_):
        thru = [[li for li, Ln in enumerate(L) if p in Ln] for p in range(n)]
        m = cp_model.CpModel()
        x = [m.NewBoolVar("") for _ in range(n)]
        for Ln in L:
            m.AddBoolOr([x[p] for p in Ln])
        m.Add(sum(x) == size)
        got = []

        class C(cp_model.CpSolverSolutionCallback):
            def __init__(s2, v):
                super().__init__()
                s2.v = v

            def on_solution_callback(s2):
                got.append(frozenset(i for i in range(n) if s2.Value(s2.v[i])))

        sv = cp_model.CpSolver()
        sv.parameters.enumerate_all_solutions = True
        sv.parameters.max_time_in_seconds = 900
        st = sv.Solve(m, C(x))
        centre, perps = 0, 0
        for B in got:
            dbl = [li for li, Ln in enumerate(L) if len(B & set(Ln)) == 2]
            if any(set(dbl) == set(thru[p]) for p in range(n)):
                centre += 1
            for p in range(n):
                nb = set()
                for li in thru[p]:
                    nb |= set(L[li])
                if B == nb - {p}:
                    perps += 1
                    break
        return {"label": label, "s": s_, "t": t_, "points": n, "lines": len(L),
                "tau1": size, "blockers": len(got),
                "perLine": None, "perPoint": len(got) / n,
                "centreTheoremHolds": centre == len(got),
                "puncturedPerps": perps,
                "sTimesTPlus1": s_ * (t_ + 1),
                "enumerationStatus": sv.StatusName(st)}

    print("THE TAX TRACKS BLOCKER RICHNESS, NOT DEFICIENCY")
    print("=" * 72)
    a = study(len(K5), gq24, 10, "GQ(2,4)", 2, 4)
    b = study(N, W_lines, 11, "W(3,3)", 3, 3)
    for r in (a, b):
        print("  %-8s s=%d t=%d  tau_1=%2d  s(t+1)=%2d  blockers %3d"
              "  per point %.2f"
              % (r["label"], r["s"], r["t"], r["tau1"], r["sTimesTPlus1"],
                 r["blockers"], r["perPoint"]))
        print("           centre theorem on all of them: %s ; punctured"
              " perps: %d ; enumeration %s"
              % (r["centreTheoremHolds"], r["puncturedPerps"],
                 r["enumerationStatus"]))
    ratio = b["perPoint"] / a["perPoint"]
    print()
    print("  RICHNESS RATIO: W(3,3) is %.1fx richer per point, and %d = q^2."
          % (ratio, int(ratio)))
    print()
    print("  NOT the centre theorem -- it holds on every blocker of both.")
    print("  The cause is gq_perp_blockers_and_h44.py's trichotomy: minimum")
    print("  blockers ARE the point-perps when t > s, of size s(t+1). GQ(2,4)")
    print("  has t=4 > s=2, so all 27 are perps, one per point, maximally")
    print("  rigid. W(3,3) has s = t = 3 and tau_1 = 11 < s(t+1) = 12, so the")
    print("  perps are not minimal, none of the 360 is one, and the family")
    print("  opens up. gq_diagonal_theorem.py already shows the diagonal case")
    print("  is provably beyond counting.")
    print()
    print("  So the tax is a function of blocker RICHNESS, richness is the")
    print("  trichotomy, and W(3,3) is hard because it sits on the diagonal.")
    print("  The deficiency is 1 in both and never had anything to do with it.")
    print()
    print("  PREDICTION: any ovoid-free GQ with t > s has tau(G x G) = tau_1^2")
    print("  exactly, and the difficulty is confined to s = t. Untested here.")

    ok = (a["blockers"] == 27 and a["perPoint"] == 1.0
          and a["puncturedPerps"] == 27 and a["centreTheoremHolds"]
          and b["blockers"] == 360 and b["perPoint"] == 9.0
          and b["puncturedPerps"] == 0 and b["centreTheoremHolds"]
          and a["tau1"] == a["sTimesTPlus1"] and b["tau1"] < b["sTimesTPlus1"])

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data",
                         "the_tax_tracks_blocker_richness_not_deficiency.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.tax-tracks-blocker-richness.v1",
                "valid": bool(ok),
                "question": ("the_open_configuration_has_a_smaller_instance.py "
                             "showed the tax is not a function of the ovoid "
                             "deficiency, which is 1 for both; this answers "
                             "what it IS a function of"),
                "notTheCentreTheorem": ("a minimum blocker of either quadrangle "
                                        "meets a pencil's worth of lines twice "
                                        "and the rest once, and the property "
                                        "holds on every blocker of both, so it "
                                        "is not the difference"),
                "families": [a, b],
                "richnessRatio": ratio,
                "ratioIsQSquared": int(ratio) == 9,
                "cause": {
                    "file": "gq_perp_blockers_and_h44.py",
                    "theorem": ("minimum blockers of a GQ are exactly the "
                                "point-perps when t > s, of size s(t+1)"),
                    "exception": ("W(3,3) has s = t and tau_1 = 11 < s(t+1) = "
                                  "12, so its perps are not minimal"),
                    "tGreaterThanS": ("blockers are the perps: one per point, "
                                      "maximally rigid"),
                    "diagonal": ("perps are too big and the family opens up; "
                                 "gq_diagonal_theorem.py shows this case is "
                                 "provably beyond counting"),
                },
                "reading": ("a product of two minimum blockers always blocks at "
                            "cost tau_1^2; to beat it the row shadows must be "
                            "blocking sets sharing structure across rows, and "
                            "with one blocker per centre there is nothing to "
                            "choose, while with nine there is -- consistent "
                            "with both instances, and an explanation rather "
                            "than a theorem"),
                "prediction": ("any ovoid-free GQ with t > s has "
                               "tau(G x G) = tau_1^2 exactly, and the "
                               "difficulty is confined to the diagonal s = t; "
                               "falsifiable on the next such quadrangle and "
                               "not tested here"),
                "boundary": ("both enumerations are complete within budget and "
                             "their counts are consistent with transitivity "
                             "(27 = 27 x 1, 360 = 40 x 9); the centre-theorem "
                             "and perp checks are exhaustive over those "
                             "families; the link from richness to product "
                             "behaviour is an explanation, not a proof, and the "
                             "prediction is untested. tau_2 is untouched and "
                             "stays open in [111, 115]"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
