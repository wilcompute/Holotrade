#!/usr/bin/env python3
"""
tau_1(W(3,7)) = 55. No blocking set of W(3,7) has 54 points, so the octet
construction is optimal and the conjecture tau_1(W(3,q)) = q^2 + q - 1 holds at
the third odd prime.

WHERE THIS STANDS.  tau1_of_w37_is_at_least_54.py (5b6a9b1) proved [54, 55].
the_minimality_fence_was_wrong.py records 55 = q^2+q-1 as the octet
construction's size, and gq_diagonal_theorem.py (972e5cd) conjectured
tau_1(W(3,q)) = q^2+q-1 for odd q on the data 11 and 29. This file decides 54.

THE ARGUMENT.  Let B be a blocker of size 54 = q^2 + 1 + 4, so delta = 4, and
let e(L) = |B n L| - 1. By the counting identity of the >= 54 file,
A_L e = 6e + 4.1 and e <= 4.

 CASE A: SOME LINE L0 MEETS B IN 5 POINTS (e(L0) = 4).  The lines disjoint from
     L0 carry q(delta - e(L0)) = 0 excess. For a point p of L0 and a line
     M != L0 through p, the lines disjoint from M that carry excess are exactly
     the lines through the OTHER points of L0 (a line through another point of
     L0 meeting M would close a triangle), so the identity pins e(M) to a value
     y_p depending only on p: e = N^T y with y supported on L0 and sum y = 4.
     The stabiliser of L0 induces PGL(2,7) on it, 3-transitive, so the three
     points of L0 outside B are fixed WLOG. All C(11,4) = 330 weight patterns,
     each fixing every line count, are INFEASIBLE; a control (the octet, size 55)
     is feasible.

 CASE B: EVERY LINE MEETS B IN AT MOST 4 POINTS (e <= 3).
   THE PENCIL LEMMA AT x = 4.  Every integer 0 <= e <= 3 with A_L e = 6e + 4.1
     contains a full pencil. Split by the maximum weight w, with line 0 taking
     it (Sp(4,7) is transitive on lines): w = 3, 2, 1 each INFEASIBLE without a
     pencil, each with a feasible control. Subtracting the pencil leaves a
     3-tight set, and the x <= 3 lemma of the >= 54 file finishes the
     induction: e = N^T y, y >= 0 integer, sum y = 4, and no line has
     sum_{p in L} y_p = 4.
   THE PATTERNS.  4p is excluded (its lines have weight 4). 3p+q and 2p+2q are
     excluded when q is collinear with p and INFEASIBLE otherwise. 2p+q+r splits
     by Witt's theorem into 4 + 7 classes (one excluded, the rest INFEASIBLE).
     p+q+r+s splits into 39 UNORDERED Sp(4,7)-orbits of 4-sets -- found by
     running over ordered classes and keying each 4-set by the minimum of its
     ordered Witt keys over all 24 orderings, and checked complete on random
     4-sets. Every representative is excluded or INFEASIBLE.

 THE OCTET IDENTITY, which is what made the patterns decidable.  Once y is fixed,
     every line count c_L = 1 + sum_{p in L} y_p is known. For a hyperbolic line
     H with perp H', the (q+1)^2 totally isotropic lines joining H to H' partition
     the points off H u H'. A point off H u H' lies on exactly one grid line and a
     point of H u H' on q+1 of them, so summing c_L over the grid gives
            (q+1)^2 + delta + q y(H u H')  =  |B| - a - b + (q+1)(a + b),
     with a = |B n H| and b = |B n H'|. With |B| = q^2+1+delta this is
            |B n H| + |B n H'|  =  2 + y(H u H')
     for every one of the q^2(q^2+1)/2 = 1225 octets. It is a consequence of the
     line counts, so adding it changes no answer -- but it is a 16-variable
     equality the solver otherwise only sees through 400 long constraints. On the
     hardest pattern it cut CP-SAT from 2748 s to under 3 s. A control (the octet
     blocker at 55) confirms the identities do not exclude a real blocker.

 So no 54-point blocker exists, blocking is upward closed, and with the octet
 construction:
                        tau_1(W(3,7)) = 55 = 7^2 + 7 - 1.

WHAT IT MEANS.  The odd-q conjecture now stands on three primes, 3, 5 and 7, and
at all three the lower bound is proved by the same mechanism: the excess of a
blocker is a weighted tight set of lines, small tight sets are sums of pencils,
and every sum of pencils below q - 2 fails to be realised. At q = 5 the value
q - 2 = 3 is realised by two kinds (octet and two-centre); at q = 7 only the
octet is known at 5. The mechanism is computational at each q, not a proof for
all odd q.

RUNTIME.  About 45 minutes on 8 cores (2553 s for the committed certificate),
dominated by the x = 4 pencil-lemma instances, which are statements about tight
sets where the octet identity does not apply; the same instances took up to
3539 s in an earlier run under different load. The test reads the certificate.

SCOPE.  The counting identities, the Case-A reduction and the induction are
argued; the lemma instances, all pattern verdicts and the controls are exact
CP-SAT results; the octet identity is argued above and checked harmless on a
feasible control; the orbit classifications rest on Witt's extension theorem and
the transitivity of PGL(2,7), with class sizes and random-sample completeness
checked. Nothing is claimed for q >= 9.
"""

import argparse
import importlib.util
import itertools
import json
import os
import random
import time
from collections import Counter
from multiprocessing import Pool

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Q = 7


def ge54():
    p = os.path.join(ROOT, "analysis", "tau1_of_w37_is_at_least_54.py")
    spec = importlib.util.spec_from_file_location("ge54", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


INV = {a: pow(a, -1, Q) for a in range(1, Q)}


def kernel(vs):
    k = len(vs)
    M = [[vs[j][r] % Q for j in range(k)] for r in range(4)]
    piv, row = [], 0
    for c in range(k):
        pr = next((r for r in range(row, 4) if M[r][c]), None)
        if pr is None:
            continue
        M[row], M[pr] = M[pr], M[row]
        iv = INV[M[row][c]]
        M[row] = [(t * iv) % Q for t in M[row]]
        for r in range(4):
            if r != row and M[r][c]:
                f = M[r][c]
                M[r] = [(M[r][t] - f * M[row][t]) % Q for t in range(k)]
        piv.append(c)
        row += 1
    basis = []
    for f in (c for c in range(k) if c not in piv):
        x = [0] * k
        x[f] = 1
        for i, c in enumerate(piv):
            x[c] = (-M[i][f]) % Q
        basis.append(x)
    return {tuple(sum(co[b] * basis[b][t] for b in range(len(basis))) % Q for t in range(k))
            for co in itertools.product(range(Q), repeat=len(basis))}


def ordered_key(pts, sf, items):
    vs = [pts[i] for i, _ in items]
    ws = tuple(w for _, w in items)
    K = kernel(vs)
    k = len(vs)
    G0 = [[sf(vs[i], vs[j]) for j in range(k)] for i in range(k)]
    best = None
    for sc in itertools.product(range(1, Q), repeat=k):
        G = tuple((sc[i] * sc[j] * G0[i][j]) % Q for i in range(k) for j in range(i + 1, k))
        if best is not None and (ws, G) > best[:2]:
            continue
        Ks = tuple(sorted(tuple((x[t] * INV[sc[t]]) % Q for t in range(k)) for x in K))
        kk = (ws, G, Ks)
        if best is None or kk < best:
            best = kk
    return best


def octet_pairs(pts, n, sf):
    """the q^2(q^2+1)/2 pairs (H, H^perp) of hyperbolic lines"""
    def nm(v):
        i = next(k for k, x in enumerate(v) if x % Q)
        z = pow(v[i] % Q, -1, Q)
        return tuple((z * x) % Q for x in v)
    idx = {pt: i for i, pt in enumerate(pts)}

    def span(a, b):
        return frozenset(idx[nm(tuple((x * pts[a][k] + y * pts[b][k]) % Q for k in range(4)))]
                         for x in range(Q) for y in range(Q) if x or y)
    perp = [frozenset(j for j in range(n) if sf(pts[i], pts[j]) == 0) for i in range(n)]
    hyp = {span(a, b) for a, b in itertools.combinations(range(n), 2) if sf(pts[a], pts[b])}
    pairs = set()
    for H in hyp:
        Hp = frozenset.intersection(*[perp[i] for i in H])
        assert len(H) == Q + 1 and len(Hp) == Q + 1 and not (H & Hp)
        pairs.add(frozenset([H, Hp]))
    out = [tuple(pq) for pq in pairs]
    assert len(out) == Q * Q * (Q * Q + 1) // 2
    return out


def add_octet_identities(m, x, y, pairs):
    """|B n H| + |B n H^perp| = 2 + y(H u H^perp): a consequence of the fixed line counts (see docstring)"""
    for H, Hp in pairs:
        m.Add(sum(x[i] for i in H) + sum(x[i] for i in Hp) == 2 + sum(y.get(pt, 0) for pt in H | Hp))


def lemma_x4(n, lines, w, budget):
    from ortools.sat.python import cp_model
    thru = [[j for j, L in enumerate(lines) if p in L] for p in range(n)]
    meet = [[k for k, M in enumerate(lines) if k != j and lines[j] & M] for j in range(n)]
    out = {}
    for mode in ("noPencil", "control"):
        m = cp_model.CpModel()
        e = [m.NewIntVar(0, w, "") for _ in range(n)]
        for j in range(n):
            m.Add(sum(e[k] for k in meet[j]) == (Q - 1) * e[j] + 4)
        m.Add(e[0] == w)
        if mode == "noPencil":
            for p in range(n):
                pos = []
                for j in thru[p]:
                    b = m.NewBoolVar("")
                    m.Add(e[j] >= 1).OnlyEnforceIf(b)
                    m.Add(e[j] == 0).OnlyEnforceIf(b.Not())
                    pos.append(b)
                m.Add(sum(pos) <= Q)
        sv = cp_model.CpSolver()
        sv.parameters.num_workers = 8
        sv.parameters.max_time_in_seconds = budget
        t0 = time.time()
        out[mode] = (sv.StatusName(sv.Solve(m)), round(time.time() - t0, 1))
    return out


def case_a(n, lines, pairs, budget):
    from ortools.sat.python import cp_model
    L0 = sorted(lines[0])

    def test(y, size, inB):
        m = cp_model.CpModel()
        x = [m.NewBoolVar("") for _ in range(n)]
        m.Add(sum(x) == size)
        for p in L0:
            m.Add(x[p] == (1 if p in inB else 0))
        for L in lines:
            m.Add(sum(x[i] for i in L) == 1 + sum(y.get(p, 0) for p in L))
        add_octet_identities(m, x, y, pairs)
        sv = cp_model.CpSolver()
        sv.parameters.num_workers = 8
        sv.parameters.max_time_in_seconds = budget
        return sv.StatusName(sv.Solve(m))

    control = test({L0[7]: 5}, 55, set(L0[:6]))
    res = Counter()
    for w in itertools.product(range(5), repeat=8):
        if sum(w) == 4:
            res[test({L0[i]: w[i] for i in range(8) if w[i]}, 54, set(L0[:5]))] += 1
    return control, dict(res)


_G = {}


def _init():
    mod = ge54()
    pts, n, lines, sf = mod.geometry()
    _G.update(mod=mod, n=n, lines=lines, pairs=octet_pairs(pts, n, sf))


def _pattern(args):
    label, y = args
    t0 = time.time()
    n, lines, pairs = _G["n"], _G["lines"], _G["pairs"]
    st = pattern54(n, lines, pairs, {int(k): v for k, v in y.items()}, 3600, workers=2)
    return label, y, st, round(time.time() - t0, 1)


def pattern54(n, lines, pairs, y, budget, workers=8):
    from ortools.sat.python import cp_model
    m = cp_model.CpModel()
    x = [m.NewBoolVar("") for _ in range(n)]
    m.Add(sum(x) == 54)
    for L in lines:
        ex = sum(y.get(p, 0) for p in L)
        if ex > 3:
            return "EXCLUDED"            # a line of weight 4 is Case A
        m.Add(sum(x[i] for i in L) == 1 + ex)
    add_octet_identities(m, x, y, pairs)
    sv = cp_model.CpSolver()
    sv.parameters.num_workers = workers
    sv.parameters.max_time_in_seconds = budget
    return sv.StatusName(sv.Solve(m))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--budget", type=float, default=5400.0)
    args = ap.parse_args()

    mod = ge54()
    pts, n, lines, sf = mod.geometry()

    def col(a, b):
        return sf(pts[a], pts[b]) == 0

    print("tau_1(W(3,7)) = 55")
    print("=" * 74)
    t_all = time.time()

    one_tight, lemma3 = mod.pencil_lemma(n, lines, args.budget)
    print("  x <= 3 lemma: %s" % {k: v[0] for k, v in lemma3.items()})
    lemma3_ok = one_tight and all(lemma3["x%d_noPencil" % x][0] == "INFEASIBLE"
                                  and lemma3["x%d_control" % x][0] in ("OPTIMAL", "FEASIBLE") for x in (1, 2, 3))

    lemma4 = {w: lemma_x4(n, lines, w, args.budget) for w in (3, 2, 1)}
    for w, v in lemma4.items():
        print("  x = 4 lemma, max weight %d: %s" % (w, v))
    lemma4_ok = all(v["noPencil"][0] == "INFEASIBLE" and v["control"][0] in ("OPTIMAL", "FEASIBLE")
                    for v in lemma4.values())

    pairs = octet_pairs(pts, n, sf)
    print("  octet pairs (H, H^perp): %d" % len(pairs))
    a_control, a_res = case_a(n, lines, pairs, 900)
    print("  Case A: control %s, 330 patterns %s" % (a_control, a_res))
    a_ok = a_control in ("OPTIMAL", "FEASIBLE") and a_res == {"INFEASIBLE": 330}

    p = 0
    qc = next(j for j in range(1, n) if col(p, j))
    qn = next(j for j in range(1, n) if not col(p, j))
    small = {"4p": pattern54(n, lines, pairs, {p: 4}, 900),
             "3p+q collinear": pattern54(n, lines, pairs, {p: 3, qc: 1}, 900),
             "3p+q noncollinear": pattern54(n, lines, pairs, {p: 3, qn: 1}, 900),
             "2p+2q collinear": pattern54(n, lines, pairs, {p: 2, qc: 2}, 900),
             "2p+2q noncollinear": pattern54(n, lines, pairs, {p: 2, qn: 2}, 900)}
    two = Counter()
    for q in (qc, qn):
        cls = {}
        for r in range(n):
            if r not in (p, q):
                cls.setdefault(ordered_key(pts, sf, [(p, 2), (q, 1), (r, 1)]), []).append(r)
        for mem in cls.values():
            two[pattern54(n, lines, pairs, {p: 2, q: 1, mem[0]: 1}, 1800)] += 1
    print("  small patterns %s; 2p+q+r classes %s" % (small, dict(two)))
    small_ok = all(v in ("EXCLUDED", "INFEASIBLE") for v in small.values()) and \
        set(two) <= {"EXCLUDED", "INFEASIBLE"} and sum(two.values()) == 11

    jobs = {}
    for q in (qc, qn):
        cls = {}
        for r in range(n):
            if r not in (p, q):
                cls.setdefault(ordered_key(pts, sf, [(p, 1), (q, 1), (r, 1)]), []).append(r)
        for mem in cls.values():
            r = mem[0]
            scls = {}
            for s in range(n):
                if s not in (p, q, r):
                    scls.setdefault(ordered_key(pts, sf, [(p, 1), (q, 1), (r, 1), (s, 1)]), []).append(s)
            for smem in scls.values():
                s = smem[0]
                uk = min(ordered_key(pts, sf, [(i, 1) for i in perm])
                         for perm in itertools.permutations([p, q, r, s]))
                jobs.setdefault(uk, ("r=%d s=%d q=%d" % (r, s, q),
                                     {str(p): 1, str(q): 1, str(r): 1, str(s): 1}))
    rnd = random.Random(2026)
    missing = 0
    for _ in range(300):
        S = rnd.sample(range(n), 4)
        if min(ordered_key(pts, sf, [(i, 1) for i in perm]) for perm in itertools.permutations(S)) not in jobs:
            missing += 1
    print("  p+q+r+s: %d unordered orbit representatives; random 4-sets missing a key: %d" % (len(jobs), missing))
    quads = []
    with Pool(4, initializer=_init) as pool:
        for label, y, st, dt in pool.imap_unordered(_pattern, list(jobs.values())):
            quads.append({"label": label, "status": st, "secs": dt})
            print("      %-22s -> %s %.1fs [%d/%d]" % (label, st, dt, len(quads), len(jobs)), flush=True)
    qstat = dict(Counter(x["status"] for x in quads))
    quads_ok = missing == 0 and set(qstat) <= {"EXCLUDED", "INFEASIBLE"} and len(quads) == len(jobs)

    ok = lemma3_ok and lemma4_ok and a_ok and small_ok and quads_ok
    print()
    print("  total %.0fs" % (time.time() - t_all))
    print("  => no 54-point blocker; with 5b6a9b1 and the octet construction, tau_1(W(3,7)) = 55")
    print()
    print("VALID: %s" % ok)

    if args.write:
        assert ok, "checks failed -- refusing to write"
        rec = {
            "schema": "holotrade.tau1-w37-is-55.v1",
            "valid": True,
            "q": Q, "tau1": 55, "previousInterval": [54, 55],
            "lemmaXle3": {k: v[0] for k, v in lemma3.items()},
            "lemmaX4": {str(w): {k: v[0] for k, v in d.items()} for w, d in lemma4.items()},
            "lemmaX4Seconds": {str(w): {k: v[1] for k, v in d.items()} for w, d in lemma4.items()},
            "caseAControl": a_control, "caseAPatterns": a_res,
            "smallPatterns": small, "twoPQRClasses": dict(two),
            "quadOrbitRepresentatives": len(jobs), "quadRandomMissing": missing,
            "quadStatus": qstat, "octetPairs": len(pairs),
            "caseA": (
                "a line meeting B in 5 points forces zero excess off it and e = N^T y with y on that line, "
                "sum 4; PGL(2,7) is 3-transitive on the line so the three non-B points are fixed; all 330 "
                "patterns INFEASIBLE, octet control at 55 feasible."),
            "caseB": (
                "with every count <= 4 the x = 4 pencil lemma (max weight 3, 2, 1, each INFEASIBLE with a "
                "feasible control) and the x <= 3 lemma give e = N^T y, sum y = 4, no line of weight 4. "
                "Patterns 4p, 3p+q, 2p+2q, 2p+q+r (Witt classes) and p+q+r+s (unordered orbit "
                "representatives, completeness checked on random 4-sets) are all excluded or INFEASIBLE."),
            "theorem": (
                "no blocking set of W(3,7) has 54 points; blocking is upward closed; the octet construction "
                "has 55; so tau_1(W(3,7)) = 55 = q^2+q-1, the conjecture of 972e5cd at its third odd prime."),
            "boundary": (
                "identities, the Case-A reduction and the induction are argued; lemma instances, pattern "
                "verdicts and controls are exact CP-SAT results; orbit classifications rest on Witt's "
                "theorem and PGL(2,7) 3-transitivity with sizes and random completeness checked. Nothing is "
                "claimed for q >= 9."),
        }
        pth = os.path.join(ROOT, "data", "tau1_w37_is_55.json")
        with open(pth, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=2)
        print("written: %s" % pth)


if __name__ == "__main__":
    main()
