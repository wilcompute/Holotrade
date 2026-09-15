#!/usr/bin/env python3
"""
THE GAUSSIAN (d = 4) RUNGS OF K12 AND THE LEECH LATTICE EXIST AND ARE UNIFORM.

W33-Theory's Pass 7293 tower table ("the arithmetic maps the tower before any of
it is built") recorded two rows as untested:
    K12    d=4  quotient 64, 63 nonzero classes, 12 vectors/class, "untested"
    Leech  d=4  quotient 4096, "all of PG(11,2)", 48 vectors/class, "untested"
The d = 9 Leech row was refuted in e680b23. This file tests the two d = 4 rows.

THE STRUCTURE.  An isometry g with g^2 = -1 makes L a Z[i]-module; pi = 1 + i.
The inverse different of Z[i] is (1/2), and delta = 2 = -i(1+i)^2. The scaled
Hermitian form reduces mod pi to
    B(x, y) = <x, y> + <x, g y>  (mod 2),
which is alternating: <x, g x> = 0, and L is even. It is nondegenerate on L/piL
whenever L is unimodular at 2 -- true for Leech, and for K12 since det 3^6 is odd.

RESULTS (exact checks below).
  * Leech: an element of class 4a (g^2 = -1) is found by random words in Conway's
    generators. Leech/piL = F_2^12 carries an alternating form, and all 4095
    nonzero classes contain minimal vectors, exactly 48 each. The row is
    CONFIRMED as predicted, uniform over all of PG(11,2).
  * K12: Aut(K12) = 6_1.U4(3).2^2. The complex reflection group G34 = 6_1.U4(3).2_2
    has NO element with g^2 = -1 (GAP CTblLib: no order-4 class squaring to the
    central -1 in any faithful 6-dim character). The index-2 extension 6_1.U4(3).2_1
    does: classes 4d and 4e (trace 0 on its rational 12-dim character), together
    1/1440 of the group. Such an element is built here as (complex conjugation
    with a coordinate swap) times an element of G34. So K12's Z[i]-structure is
    ANTILINEAR. K12/piK12 = F_2^6 carries an alternating form, and all 63 classes
    hold exactly 12 minimal vectors. The row is CONFIRMED, uniform over PG(5,2).
  * Control: E8 at d=4 gives W(3,2) with 16 roots per class.

With e680b23 (Leech d = 3, 5, 7, 13 rungs; d = 9 empty) and a0ed473 (K12 mod theta
and mod 2), every row of Pass 7293's table is now tested.

SCOPE.  Finite exact checks; the lattices and groups are classical. New relative to
the corpus: the test of the two rows, and the observation that K12's Gaussian
structure needs the antilinear half of Aut(K12). No physics.
"""

import argparse
import importlib.util
import itertools
import json
import os
import random
from collections import Counter

import numpy as np
import sympy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, "analysis", name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def classes_mod_pi(X, bas, form, m):
    Gm = np.array([[form(a[None, :], b)[0] for b in bas] for a in bas])
    Gi = np.array(sympy.Matrix(Gm.tolist()).inv_mod(2).tolist(), dtype=np.int64)
    P = np.stack([form(X, b) for b in bas], axis=1)
    C = (P @ Gi) % 2
    cnt = Counter(tuple(r) for r in C.tolist())
    zero = cnt.pop(tuple([0] * m), 0)
    alt = all(Gm[i, i] == 0 for i in range(m)) and (Gm == Gm.T).all()
    return Gm, zero, cnt, alt


def pick_basis(X, form, m, rng):
    while True:
        bas = [X[rng.randrange(len(X))] for _ in range(m)]
        Gm = np.array([[form(a[None, :], b)[0] for b in bas] for a in bas])
        if int(round(np.linalg.det(Gm))) % 2 == 1:
            return bas


def leech_rung():
    lr = load("the_leech_rungs_are_the_suzuki_chain")
    code, octads, M, gens = lr.leech()
    key = {tuple(v): i for i, v in enumerate(M)}
    I = np.eye(24)
    rng = random.Random(4)

    def rnd(A):
        return np.round(A * 8) / 8
    g = None
    while g is None:
        A = I
        for _ in range(rng.randint(6, 30)):
            A = rnd(A @ gens[rng.randrange(len(gens))])
        C, o = A.copy(), None
        for k in range(1, 121):
            if np.allclose(C, I, atol=1e-6):
                o = k
                break
            C = rnd(C @ A)
        if o and o % 4 == 0:
            h = rnd(np.linalg.matrix_power(A, o // 4))
            if np.allclose(rnd(h @ h), -I) and lr.preserves(M, key, h):
                g = h
    W = I + g

    def form(X, y):
        num = np.round(X @ (W @ y)).astype(np.int64)
        assert (num % 8 == 0).all()
        return (num // 8) % 2
    bas = pick_basis(M, form, 12, rng)
    Gm, zero, cnt, alt = classes_mod_pi(M, bas, form, 12)
    return {"gSquaredMinusOne": True, "trace": int(round(np.trace(g))), "alternating": bool(alt),
            "zeroClass": zero, "classesHit": len(cnt), "histogram": sorted(Counter(cnt.values()).items())}


def k12_rung():
    ct = load("the_coxeter_todd_rung_is_locally_the_cubic_surface")
    code = ct.hexacode()
    elems = sorted(((a, b) for a in range(-3, 4) for b in range(-3, 4) if ct.nrm((a, b)) <= 4), key=ct.nrm)
    mins = []

    def rec(prefix, budget):
        if len(prefix) == 6:
            if budget == 0 and tuple((x[0] % 2) + 2 * (x[1] % 2) for x in prefix) in code:
                mins.append(tuple(prefix))
            return
        for x in elems:
            if ct.nrm(x) > budget:
                break
            rec(prefix + [x], budget - ct.nrm(x))
    rec([], 4)
    assert len(mins) == 756
    lines, seen = [], set()
    for v in mins:
        if v not in seen:
            seen |= {tuple(ct.mul(u, x) for x in v) for u in ct.UNITS}
            lines.append(v)
    RM = np.array([[c for x in v for c in x] for v in mins], dtype=float)
    key = {tuple(np.round(r * 2).astype(int)) for r in RM}

    def real_reflection(v):
        R = np.zeros((12, 12))
        for j in range(12):
            e = [(0, 0)] * 6
            e[j // 2] = (1, 0) if j % 2 == 0 else (0, 1)
            hv = ct.h(e, v)
            s = (hv[0] / 2.0, hv[1] / 2.0)
            img = [(e[t][0] - (s[0] * v[t][0] - s[1] * v[t][1]),
                    e[t][1] - (s[0] * v[t][1] + s[1] * v[t][0] - s[1] * v[t][1])) for t in range(6)]
            R[:, j] = [c for x in img for c in x]
        return R
    RG = [real_reflection(v) for v in lines]
    Cc = np.zeros((12, 12))
    perm = [0, 1, 2, 3, 5, 4]
    for i in range(6):
        t = perm[i]
        Cc[2 * t, 2 * i] = 1
        Cc[2 * t, 2 * i + 1] = -1
        Cc[2 * t + 1, 2 * i + 1] = -1

    def preserves(A):
        img = RM @ A.T
        return np.allclose(img * 2, np.round(img * 2)) and all(tuple(np.round(r * 2).astype(int)) in key for r in img)
    assert preserves(Cc) and all(preserves(R) for R in RG[:5])
    I12 = np.eye(12)

    def rnd(A):
        return np.round(A * 2) / 2
    # G34 has no g^2 = -1 (character table); sample it as a control
    rng = random.Random(1)
    x = I12
    linear_hits = 0
    for _ in range(20000):
        x = rnd(x @ RG[rng.randrange(len(RG))])
        if np.allclose(rnd(x @ x), -I12):
            linear_hits += 1
    g, steps = None, 0
    x = I12
    while g is None:
        steps += 1
        x = rnd(x @ RG[rng.randrange(len(RG))])
        cand = rnd(Cc @ x)
        if np.allclose(rnd(cand @ cand), -I12) and preserves(cand):
            g = cand
    Q = np.zeros((12, 12))
    for i in range(6):
        Q[2 * i:2 * i + 2, 2 * i:2 * i + 2] = [[1, -0.5], [-0.5, 1]]

    def form(X, y):
        val = X @ Q @ (y + g @ y)
        assert np.allclose(val, np.round(val))
        return np.round(val).astype(np.int64) % 2
    bas = pick_basis(RM, form, 6, rng)
    Gm, zero, cnt, alt = classes_mod_pi(RM, bas, form, 6)
    return {"antilinear": True, "linearG34SampleHits": linear_hits, "stepsToFind": steps,
            "trace": int(round(np.trace(g))), "alternating": bool(alt), "zeroClass": zero,
            "classesHit": len(cnt), "histogram": sorted(Counter(cnt.values()).items())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    leech = leech_rung()
    print("Leech d=4:", leech, flush=True)
    k12 = k12_rung()
    print("K12 d=4:", k12, flush=True)
    checks = {
        "leech_uniform_48_over_PG11_2": leech["alternating"] and leech["zeroClass"] == 0
        and leech["classesHit"] == 4095 and leech["histogram"] == [(48, 4095)],
        "k12_uniform_12_over_PG5_2": k12["alternating"] and k12["zeroClass"] == 0
        and k12["classesHit"] == 63 and k12["histogram"] == [(12, 63)] and k12["trace"] == 0,
        "k12_gaussian_structure_is_antilinear": k12["linearG34SampleHits"] == 0,
    }
    ok = all(checks.values())
    for k, v in checks.items():
        print("  %-40s %s" % (k, v))
    print("VALID: %s" % ok)
    if args.write:
        assert ok
        rec = {"schema": "holotrade.gaussian-rungs-k12-leech.v1", "valid": True, "checks": checks,
               "leech": {k: (list(map(list, v)) if k == "histogram" else v) for k, v in leech.items()},
               "k12": {k: (list(map(list, v)) if k == "histogram" else v) for k, v in k12.items()},
               "gap": {"G34 = 6_1.U4(3).2_2": "no order-4 class with g^2 = -1",
                       "6_1.U4(3).2_1": "classes 4d, 4e: g^2 = -1, trace 0 on the rational 12-dim character, proportion 1/2880 each"},
               "closes": "W33-Theory Pass 7293 table rows K12 d=4 and Leech d=4 (untested)",
               "boundary": "finite exact checks; classical lattices and groups; no physics"}
        with open(os.path.join(ROOT, "data", "gaussian_rungs_k12_leech.json"), "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=2)
        print("written")


if __name__ == "__main__":
    main()
