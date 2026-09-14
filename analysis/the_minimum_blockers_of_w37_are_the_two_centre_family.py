#!/usr/bin/env python3
"""
The 1,274,000 minimum blockers of W(3,7) are exactly the two-centre octet
family, and therefore tau_2(W(3,7) x W(3,7)) >= 50 * 55 + 1 = 2751.

INPUTS, CERTIFIED ELSEWHERE.
  * tau_1(W(3,7)) = 55                         tau1_of_w37_is_55.py (9d5751e)
  * the two-centre octet family B(u,v,S), its excess a pencil(u) + b pencil(v)
    with a + b = q-2, and the conditional tight-case theorem for odd q
                                               the_two_centre_octet_family_is_q_general.py (7efd439)
  * pencil lemmas: x <= 3 (5b6a9b1), x = 4 (9d5751e), x = 5 with max weight <= 4
                                               the_w37_pencil_lemma_at_five.py (aa744e3)
  * the 39 unordered Sp(4,7)-orbits of 4-sets (tau1_of_w37_is_55.py) and the
    orbits of each 4-set stabiliser on the remaining 396 points, computed in GAP
    (w37_four_set_extension_orbits.g -> data/w37_four_set_extensions.json;
    group order 138,297,600 and every orbit partition summing to 396 re-checked here).

THE CLASSIFICATION.  Let B be a 55-point blocker, delta = 5, e its line excess,
so A_L e = 6e + 5.1 and e <= 5.

 CASE A: SOME LINE L0 MEETS B IN 6 POINTS.  Lines off L0 carry no excess and the
   triangle-free argument gives e = N^T y with y on L0, sum 5; PGL(2,7) is
   3-transitive on L0 so its two points outside B are fixed. Of the 792 weight
   patterns, exactly SIX are realisable, and all put the whole weight on those
   two points: y = a u + b v, a + b = 5, u, v collinear -- the family's pattern.

 CASE B: EVERY LINE MEETS B AT MOST 5 TIMES.  The pencil lemmas give e = N^T y,
   y >= 0, sum 5, with no line of y-weight 5 (that would be Case A). Every
   pattern is decided with every line count fixed and the octet identities
   |B n H| + |B n H^perp| = 2 + y(H u H^perp) added:
      at most 3 distinct points   (Witt classes)                  all excluded or INFEASIBLE
      2p + q + r + s              (39 4-set orbits x 4 heavy choices)  all excluded or INFEASIBLE
      p + q + r + s + t           (3,467 extensions of the 39 orbits)  all excluded or INFEASIBLE
   So Case B is EMPTY.

 THE CENSUS.  Fix collinear u != v. For y = 5u the octet blockers centred at u
   are forbidden, for y = 4u + v the 21 and for 3u + 2v the 35 family members;
   each query is INFEASIBLE, and each control -- forbidding all but one -- must
   recover the one left. PSp(4,7) is transitive on points and on collinear
   pairs, so the minimum blockers are exactly the family:
        19,600 octet kind + 1,254,400 two-centre kind = 1,274,000.

THE CONSEQUENCE.  For every minimum blocker the heavier centre carries weight
a >= 3 and the lighter b <= 2, so thresholding the tile excess at 3 recovers
u_L in M <=> u'_M in L at the tight size 50 * 55 = 2750. By the conditional
theorem of 7efd439 (centre reciprocity -> ovoid or duality of W(3,7), neither
existing), no tight blocker exists:

        tau_2(W(3,7) x W(3,7))  >=  2751,      and <= 55^2 = 3025.

The odd-q tight-case theorem now holds at q = 3, 5, 7.

SCOPE.  Exact solver verdicts with controls throughout; the group data is GAP
output re-checked for consistency; the reductions are argued in the cited files.
Runtime is dominated by the 3,467 five-point patterns (about an hour).
"""

import argparse
import importlib.util
import itertools
import json
import os
import time
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Q = 7


def load(name):
    p = os.path.join(ROOT, "analysis", name)
    spec = importlib.util.spec_from_file_location(name[:-3], p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    from ortools.sat.python import cp_model

    t_all = time.time()
    ge54 = load("tau1_of_w37_is_at_least_54.py")
    eq55 = load("tau1_of_w37_is_55.py")
    pts, n, lines, sf = ge54.geometry()
    pairs = eq55.octet_pairs(pts, n, sf)

    def col(a, b):
        return sf(pts[a], pts[b]) == 0

    def rd(name):
        with open(os.path.join(ROOT, "data", name), encoding="utf-8") as fh:
            return json.load(fh)
    inputs_ok = (rd("tau1_w37_at_least_54.json")["valid"] and rd("tau1_w37_is_55.json")["valid"]
                 and rd("w37_pencil_lemma_x5.json")["valid"] and rd("two_centre_octet_family.json")["valid"])
    ext = rd("w37_four_set_extensions.json")
    ext_ok = (ext["groupOrder"] == 138297600 and len(ext["fourSetOrbitRepresentatives"]) == 39
              and all(sum(l for _, l in r["orbits"]) == 396 for r in ext["fourSetOrbitRepresentatives"]))

    def model(y, fix=None, forbid=(), maxe=5, budget=1800, workers=8):
        m = cp_model.CpModel()
        x = [m.NewBoolVar("") for _ in range(n)]
        m.Add(sum(x) == 55)
        for L in lines:
            ex = sum(y.get(p, 0) for p in L)
            if ex > maxe:
                return "EXCLUDED", None
            m.Add(sum(x[i] for i in L) == 1 + ex)
        eq55.add_octet_identities(m, x, y, pairs)
        for i, v in (fix or {}).items():
            m.Add(x[i] == v)
        for B in forbid:
            m.Add(sum(x[i] for i in B) <= 54)
        sv = cp_model.CpSolver()
        sv.parameters.num_workers = workers
        sv.parameters.max_time_in_seconds = budget
        st = sv.StatusName(sv.Solve(m))
        sol = frozenset(i for i in range(n) if sv.Value(x[i])) if st in ("OPTIMAL", "FEASIBLE") else None
        return st, sol

    # CASE A
    L0 = sorted(lines[0])
    fixA = {p: (1 if t < 6 else 0) for t, p in enumerate(L0)}
    caseA = Counter()
    feasA = []
    for w in itertools.product(range(6), repeat=8):
        if sum(w) != 5:
            continue
        st, _ = model({L0[i]: w[i] for i in range(8) if w[i]}, fix=fixA, budget=900)
        caseA[st] += 1
        if st in ("OPTIMAL", "FEASIBLE"):
            feasA.append(w)
    caseA_ok = (sum(caseA.values()) == 792 and len(feasA) == 6
                and all(sum(w[:6]) == 0 for w in feasA) and set(caseA) <= {"OPTIMAL", "FEASIBLE", "INFEASIBLE"})
    print("  Case A: %s; feasible patterns %s" % (dict(caseA), feasA), flush=True)

    # CASE B
    p = 0
    qc = next(j for j in range(1, n) if col(p, j))
    qn = next(j for j in range(1, n) if not col(p, j))
    small = Counter()
    small[model({p: 5}, maxe=4)[0]] += 1
    for q in (qc, qn):
        for a, b in ((4, 1), (3, 2)):
            small[model({p: a, q: b}, maxe=4)[0]] += 1
        for wts in ((3, 1, 1), (2, 2, 1)):
            cls = {}
            for r in range(n):
                if r not in (p, q):
                    cls.setdefault(eq55.ordered_key(pts, sf, [(p, wts[0]), (q, wts[1]), (r, wts[2])]), []).append(r)
            for mem in cls.values():
                small[model({p: wts[0], q: wts[1], mem[0]: wts[2]}, maxe=4)[0]] += 1
    four = Counter()
    for R in ext["fourSetOrbitRepresentatives"]:
        for heavy in R["set"]:
            four[model({i: (2 if i == heavy else 1) for i in R["set"]}, maxe=4)[0]] += 1
    five = Counter()
    for R in ext["fourSetOrbitRepresentatives"]:
        for t, _ in R["orbits"]:
            five[model({i: 1 for i in R["set"] + [t]}, maxe=4)[0]] += 1
    caseB_ok = all(set(c) <= {"EXCLUDED", "INFEASIBLE"} for c in (small, four, five)) \
        and sum(four.values()) == 156 and sum(five.values()) == 3467
    print("  Case B: small %s; 2p+q+r+s %s; p+q+r+s+t %s" % (dict(small), dict(four), dict(five)), flush=True)

    # CENSUS
    def lperp(L):
        return frozenset.intersection(*[frozenset(j for j in range(n) if sf(pts[i], pts[j]) == 0) for i in L])
    idx = {pt: i for i, pt in enumerate(pts)}

    def nm(v):
        i = next(k for k, x in enumerate(v) if x % Q)
        z = pow(v[i] % Q, -1, Q)
        return tuple((z * x) % Q for x in v)

    def span(a, b):
        return frozenset(idx[nm(tuple((x * pts[a][k] + yy * pts[b][k]) % Q for k in range(4)))]
                         for x in range(Q) for yy in range(Q) if x or yy)
    u, v = p, qc
    U = span(u, v)
    perp_v = frozenset(j for j in range(n) if col(v, j))
    hs = sorted({span(u, w) for w in perp_v - U}, key=sorted)
    assert len(hs) == Q

    def member(S):
        B = set(U - {u, v})
        for i in range(Q):
            B |= (hs[i] - {u}) if i in S else (lperp(hs[i]) - {v})
        return frozenset(B)
    perp_u = frozenset(j for j in range(n) if col(u, j))
    hyp_u = sorted({span(u, w) for w in range(n) if w not in perp_u}, key=sorted)
    octets_u = [frozenset((perp_u - {u} - lperp(H)) | (H - {u})) for H in hyp_u]
    census = {}
    for label, y, fams in (("5u", {u: 5}, octets_u),
                           ("4u+v", {u: 4, v: 1}, [member(S) for S in itertools.combinations(range(Q), 2)]),
                           ("3u+2v", {u: 3, v: 2}, [member(S) for S in itertools.combinations(range(Q), 3)])):
        fams = list(dict.fromkeys(fams))
        st_all, _ = model(y, forbid=fams)
        st_ctl, sol = model(y, forbid=fams[:-1])
        census[label] = {"members": len(fams), "othersExist": st_all,
                         "controlRecoversLast": st_ctl in ("OPTIMAL", "FEASIBLE") and sol == fams[-1]}
    census_ok = (census["5u"]["members"] == 49 and census["4u+v"]["members"] == 21 and census["3u+2v"]["members"] == 35
                 and all(c["othersExist"] == "INFEASIBLE" and c["controlRecoversLast"] for c in census.values()))
    print("  census: %s" % census, flush=True)

    ok = inputs_ok and ext_ok and caseA_ok and caseB_ok and census_ok
    total = 400 * 49 + 400 * 56 * 112 // 2
    print()
    print("  minimum blockers: %d; tau_2(W(3,7)^2) >= 2751  (%.0fs)" % (total, time.time() - t_all))
    print("VALID: %s" % ok)

    if args.write:
        assert ok, "checks failed -- refusing to write"
        rec = {
            "schema": "holotrade.w37-minimum-blockers-two-centre.v1",
            "valid": True,
            "inputsValid": inputs_ok, "extensionDataConsistent": ext_ok,
            "caseA": dict(caseA), "caseAFeasiblePatterns": [list(w) for w in feasA],
            "caseBSmall": dict(small), "caseBTwoOneOneOne": dict(four), "caseBFivePoints": dict(five),
            "census": census,
            "minimumBlockers": total, "octetKind": 19600, "twoCentreKind": 1254400,
            "tau2LowerBound": 2751, "tau2UpperBound": 3025,
            "theorem": (
                "every 55-point blocker of W(3,7) is a two-centre octet blocker B(u,v,S); there are 1,274,000; the "
                "heavier centre has weight >= 3 and the lighter <= 2, so the tight case 2750 forces centre reciprocity "
                "and hence an ovoid or duality of W(3,7). tau_2(W(3,7)^2) >= 2751."),
            "boundary": (
                "exact solver verdicts with controls; GAP orbit data re-checked for consistency; reductions argued "
                "in the cited files (5b6a9b1, 9d5751e, 7efd439, the x = 5 lemma certificate)."),
        }
        pth = os.path.join(ROOT, "data", "w37_minimum_blockers_two_centre.json")
        with open(pth, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=2)
        print("written: %s" % pth)


if __name__ == "__main__":
    main()
