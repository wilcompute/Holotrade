#!/usr/bin/env python3
"""
THE W(3,3)-TWIST VACUUM CONTAINS THREE-FAMILY GUTS: SU(5) WITH THREE COMPLETE
10 + 5bar FAMILIES, AND SO(10) WITH THREE 16s.

Continues fbd2c5f (the W(3,3) twist of E8 is the A8 shift; its unique T^6/Z_3
partner is D7 + U1, giving SU(9) x SO(14) x U(1)) and ade6ba9 (Z_3 Wilson lines on
that vacuum give net quark doublets equal to 3 x the untwisted plane index, with
zero index at every fixed point). Net (3,2) = 3 is necessary for a Standard Model
but not sufficient, so this file asks the sharper question: does any Wilson-line
deformation of the forced vacuum carry three complete GUT families?

It does.

MACHINERY. For every simple factor of the unbroken gauge group, the massless
left-chiral weights are decomposed into irreducible representations by
Weyl-character inversion,
    N(lambda) = sum_{w in W} sign(w) * mult(w(lambda + rho) - rho),
over that factor's own Weyl group, in its own Dynkin labels. Net family indices:
    SU(5):   n10 = N(Lambda^2 5) - N(conjugate),   n5bar = N(5bar) - N(5)
    SO(10):  n16 = N(16) - N(16bar)
    E6:      n27 = N(27) - N(27bar)
Label orientation is a convention, so only relative signs carry meaning.

WHAT IS MEASURED (deterministic samples).
  1. SU(5) factors occur with (n10, n5bar) = (3,3), (-3,-3), (6,6), (-6,-6) and
     (0,0). The tens and anti-fives always arrive together in equal numbers, so the
     chiral SU(5) content is always complete families: three families occur.
  2. SO(10) factors occur with n16 = +-3: three sixteens, i.e. three complete
     families including right-handed neutrinos.
  3. Every index is a multiple of three, matching ade6ba9's rule that chirality
     comes from the three untwisted planes.
  4. n10 = n5bar in every sampled model. That is exactly SU(5)^3 anomaly
     cancellation (A(10) = A(5) = 1), so the Weyl-inversion indices and the
     independent cubic-anomaly check agree on every model. No sampled model is
     anomalous.

CONTROLS AND TEETH.
  - The standard embedding with no Wilson lines returns n27 = 36 through this
    generic code: the classical Z_3 generation count.
  - Full decomposition: for the frozen witnesses and a sample of models, the
    multiplicities N(lambda) over ALL dominant weights satisfy
    sum_lambda N(lambda) * dim(lambda) = number of weights, with no negative
    multiplicity. A broken inversion fails this immediately.
  - Witnesses for SU(5) (3,3) and SO(10) 3 are frozen with their Wilson lines and
    re-verified from scratch.

NOTE ON A CORRECTED RUN. An earlier version of this file used the generic vector
arange(1,17) + pi/10 to pick positive roots. It is orthogonal to 16 of the 480
roots, which silently corrupted Dynkin labels and produced the opposite (negative)
answer. Fixed in 64c226c; the generic vector is now the square roots of the first
16 primes, which are linearly independent over Q.

READING. The substrate-forced vacuum does not merely have the family NUMBER three
(ade6ba9); it has three complete GUT families. The three still comes from the three
complex planes of T^6, as ade6ba9's standard-embedding control shows, so W(3,3)
supplies the vacuum, not the counting.

OPEN. A Standard Model needs more than three chiral families: a hypercharge U(1)_Y
with the right normalisation k_Y, the breaking of SU(5)/SO(10) at level 1 (no
adjoint Higgs is available), and the removal of vector-like exotics. None of that is
built here.

SCOPE. Z_3 orbifold model building is classical (Ibanez-Kim-Nilles-Quevedo 1987;
Font-Ibanez-Quevedo-Sierra 1990; Casas-Munoz). What is new to the corpus is the
question asked of the vacuum that the W(3,3) twist forces, and the answer.
"""

import argparse
import importlib.util
import itertools
import json
import os
import random

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = 36


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, "analysis", name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


fam = _load("the_w33_vacuum_families_live_on_the_untwisted_planes")
het = _load("the_w33_twist_is_the_su9_heterotic_embedding")


def diagram(C):
    """simple roots, Cartan matrix, and the Dynkin diagram's paths/branches."""
    sr = fam.simple_roots(C)
    n = len(sr)
    A = [[int(x @ y) // S for y in sr] for x in sr]
    adj = {i: [j for j in range(n) if j != i and A[i][j]] for i in range(n)}
    forks = [i for i in adj if len(adj[i]) == 3]
    assert all(len(adj[i]) <= 3 for i in adj) and len(forks) <= 1, "not an ADE diagram"
    info = {"n": n, "adj": adj, "fork": forks[0] if forks else None}
    if not forks:                                          # a path: order it end to end
        start = next(i for i in adj if len(adj[i]) <= 1)
        order, prev = [start], None
        while len(order) < n:
            nxt = [j for j in adj[order[-1]] if j != prev]
            prev = order[-1]
            order.append(nxt[0])
        info["path"] = order
    else:
        branches = []
        for j in adj[forks[0]]:
            br, prev, cur = [j], forks[0], j
            while len(br) <= n:
                nxt = [k for k in adj[cur] if k != prev]
                if not nxt:
                    break
                prev, cur = cur, nxt[0]
                br.append(cur)
            assert len(br) <= n, "diagram walk did not terminate"
            branches.append(br)
        info["branches"] = sorted(branches, key=len)
    return sr, A, info


def labels(states, sr):
    M = {}
    for P, m in states:
        if not len(P):
            continue
        L = np.stack([P @ a for a in sr], axis=1) // S
        for row, cnt in zip(*np.unique(L, axis=0, return_counts=True)):
            k = tuple(int(x) for x in row)
            M[k] = M.get(k, 0) + m * int(cnt)
    return M


_ORBITS = {}


def weyl_orbit(A, lam):
    key = (tuple(map(tuple, A)), tuple(lam))
    if key in _ORBITS:
        return _ORBITS[key]
    n = len(A)
    x0 = tuple(l + 1 for l in lam)                         # rho-shifted
    orb, fr = {x0: 1}, [x0]
    while fr:
        nxt = []
        for x in fr:
            for i in range(n):
                y = tuple(x[j] - x[i] * A[i][j] for j in range(n))
                if y not in orb:
                    orb[y] = -orb[x]
                    nxt.append(y)
        fr = nxt
    _ORBITS[key] = orb
    return orb


def N(M, A, lam):
    return sum(sg * M.get(tuple(v - 1 for v in x), 0) for x, sg in weyl_orbit(A, lam).items())


def full_decomposition(C, states):
    """decompose every weight of this factor into irreps; teeth for the Weyl inversion."""
    sr, A, _ = diagram(C)
    n = len(sr)
    M = labels(states, sr)
    Ainv = np.linalg.inv(np.array(A, dtype=float))
    srm = np.array(sr, dtype=float)
    omega = Ainv @ srm                                     # fundamental weights in x6 coordinates
    rho = omega.sum(axis=0)
    pos = [r for r in C if r @ fam.GEN > 0]

    def dim(lam):
        lv = np.array(lam, dtype=float) @ omega
        num = den = 1.0
        for al in pos:
            num *= float((lv + rho) @ al)
            den *= float(rho @ al)
        return int(round(num / den))
    total = sum(M.values())
    acc, mults = 0, {}
    for lam in [k for k in M if all(x >= 0 for x in k)]:
        m = N(M, A, list(lam))
        if m:
            mults[lam] = m
            acc += m * dim(list(lam))
    return {"weights": total, "fromIrreps": acc, "exact": acc == total,
            "noNegativeMultiplicity": all(m > 0 for m in mults.values()), "irreps": len(mults)}


def family_indices(C, states):
    """net GUT family indices for this simple factor, or None if it is not A4/D5/E6."""
    name = fam.cname(C)
    if name not in ("A4", "D5", "E6"):
        return None
    sr, A, info = diagram(C)
    n = len(sr)
    M = labels(states, sr)

    def one(node):
        v = [0] * n
        v[node] = 1
        return v
    if name == "A4":                                       # SU(5): 5 at an end, 10 = Lambda^2 next to it
        p = info["path"]
        return {"group": "SU(5)",
                "n10": N(M, A, one(p[1])) - N(M, A, one(p[2])),
                "n5bar": N(M, A, one(p[3])) - N(M, A, one(p[0]))}
    if name == "D5":                                       # SO(10): the two length-1 branches are the spinor nodes
        br = info["branches"]
        assert [len(b) for b in br] == [1, 1, 2], [len(b) for b in br]
        return {"group": "SO(10)", "n16": N(M, A, one(br[0][0])) - N(M, A, one(br[1][0]))}
    br = info["branches"]                                  # E6: arms of length 2 carry 27 and 27bar
    assert [len(b) for b in br] == [1, 2, 2], [len(b) for b in br]
    return {"group": "E6", "n27": N(M, A, one(br[1][-1])) - N(M, A, one(br[2][-1]))}


def model_states(B, V, lines):
    gauge, untw, fps = B.model(V, lines)
    mult_fp = 3 ** (3 - len(lines))
    states = [(untw, 3)] + [(P, m * mult_fp) for ns, st in fps.items()
                            if all(ns[i] == 0 for i in range(len(lines), 3)) for P, m in st]
    return gauge, states


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--target", type=int, default=400)
    args = ap.parse_args()
    B = fam.Builder()
    V_w33 = np.concatenate([B.shift(72, 1), B.shift(84, 2)])
    V_std = np.concatenate([B.shift(78, 0), np.zeros(8, dtype=np.int64)])
    checks, out = {}, {}

    # control: the standard embedding with no Wilson lines must give 36 generations of 27
    gauge, states = model_states(B, V_std, [])
    e6 = next(c for c in het.root_components(gauge) if fam.cname(c) == "E6")
    ctrl = family_indices(e6, states)
    print("  control: standard embedding, no Wilson lines, E6 net 27s =", abs(ctrl["n27"]))
    checks["control_e6_36_generations"] = abs(ctrl["n27"]) == 36
    out["control"] = {"n27": ctrl["n27"]}

    ctrl_dec = full_decomposition(e6, states)
    print("  control decomposition:", ctrl_dec)
    checks["control_decomposition_exact"] = ctrl_dec["exact"] and ctrl_dec["noNegativeMultiplicity"]
    out["controlDecomposition"] = ctrl_dec

    rng = random.Random(4242)
    tally = {}
    examples = {}
    decomp_ok = []
    for nl in (1, 2, 3):
        found = sampled = anomalous = 0
        stats = {}
        while found < args.target and sampled < 200 * args.target:
            lines = [B.line(rng, V_w33, []) for _ in range(nl)]
            for i in range(1, nl):                          # enforce the cross conditions
                lines[i] = B.line(rng, V_w33, lines[:i])
            sampled += 1
            d = B.R16 @ V_w33                              # cheap pre-filter: gauge roots only
            ok = np.ones(len(B.R16), bool)
            for a in lines:
                ok &= (B.R16 @ a) % S == 0
            comps = het.root_components(B.R16[ok & (d % S == 0)])
            if not any(fam.cname(c) in ("A4", "D5", "E6") for c in comps):
                continue
            gauge, states = model_states(B, V_w33, lines)
            hits = [(c, family_indices(c, states)) for c in comps if fam.cname(c) in ("A4", "D5", "E6")]
            found += 1
            if not fam.cubic_free(comps, states, rng):
                anomalous += 1
            for c, fi in hits:
                if fi["group"] == "SU(5)":
                    k = ("SU(5)", fi["n10"], fi["n5bar"])
                elif fi["group"] == "SO(10)":
                    k = ("SO(10)", fi["n16"])
                else:
                    k = ("E6", fi["n27"])
                stats[k] = stats.get(k, 0) + 1
                tag = None
                if k[0] == "SU(5)" and abs(k[1]) == 3 and abs(k[2]) == 3:
                    tag = "su5_three_families"
                elif k[0] == "SO(10)" and abs(k[1]) == 3:
                    tag = "so10_three_families"
                if tag and tag not in examples:
                    examples[tag] = {"lines": [[int(x) for x in a] for a in lines],
                                     "gauge": sorted(fam.cname(cc) for cc in comps), "indices": fi,
                                     "decomposition": full_decomposition(c, states)}
            if found <= 20:                                 # teeth: full decomposition on a sample
                for c, _ in hits:
                    dec = full_decomposition(c, states)
                    decomp_ok.append(dec["exact"] and dec["noNegativeMultiplicity"])
        tally["%dlines" % nl] = {"sampled": sampled, "withGutFactor": found, "anomalous": anomalous,
                                 "indices": {repr(k): v for k, v in sorted(stats.items(), key=lambda kv: str(kv[0]))}}
        print("  %d Wilson line(s): sampled %5d, models with SU(5)/SO(10)/E6 factor %4d, anomalous %d" % (
            nl, sampled, found, anomalous))
        for k, v in sorted(stats.items(), key=lambda kv: str(kv[0])):
            print("      %-28s %d models" % (str(k), v))
    out["tally"] = tally
    out["examples"] = examples

    allk = [eval(k) for f in tally.values() for k in f["indices"]]
    su5 = [k for k in allk if k[0] == "SU(5)"]
    so10 = [k for k in allk if k[0] == "SO(10)"]
    checks["su5_factors_occur"] = len(su5) > 0
    checks["su5_three_complete_families_occur"] = any(abs(k[1]) == 3 and k[2] == k[1] for k in su5)
    checks["su5_tens_and_antifives_always_match"] = all(k[1] == k[2] for k in su5)
    checks["so10_three_families_occur"] = any(abs(k[1]) == 3 for k in so10)
    checks["all_indices_multiples_of_three"] = all(all(x % 3 == 0 for x in k[1:]) for k in allk)
    checks["no_anomalous_model"] = all(f["anomalous"] == 0 for f in tally.values())
    checks["sampled_decompositions_exact"] = bool(decomp_ok) and all(decomp_ok)

    # witnesses: rebuild from the frozen Wilson lines and re-verify
    wit_ok = {}
    for tag, w in examples.items():
        lines = [np.array(a, dtype=np.int64) for a in w["lines"]]
        conds = all(int(a @ a) % 24 == 0 and int(V_w33 @ a) % 12 == 0 for a in lines) and \
            all(int(a @ b) % 12 == 0 for a, b in itertools.combinations(lines, 2))
        gauge, states = model_states(B, V_w33, lines)
        comps = het.root_components(gauge)
        want = "A4" if tag.startswith("su5") else "D5"
        c = next(cc for cc in comps if fam.cname(cc) == want)
        fi = family_indices(c, states)
        dec = full_decomposition(c, states)
        idx = [abs(v) for k_, v in fi.items() if k_ != "group"]
        wit_ok[tag] = conds and fam.cubic_free(comps, states, rng) and dec["exact"] and \
            dec["noNegativeMultiplicity"] and idx == [3] * len(idx)
        w["reverified"] = wit_ok[tag]
        w["decomposition"] = dec
        print("  witness %-20s gauge %s indices %s decomposition %s -> %s" % (
            tag, "x".join(w["gauge"]), fi, dec["exact"], wit_ok[tag]))
    checks["witnesses_reverified"] = bool(wit_ok) and all(wit_ok.values()) and len(wit_ok) == 2
    for k, v in checks.items():
        print("  %-38s %s" % (k, v))
    valid = all(checks.values())
    print("VALID:", valid)
    if args.write:
        payload = {"claim": "In Wilson-line deformations of the W(3,3)-twist vacuum (fbd2c5f, ade6ba9), SU(5) factors carry "
                            "equal net tens and anti-fives (SU(5)^3 anomaly freedom), and three complete families occur: "
                            "n10 = n5bar = 3. SO(10) factors occur with three 16s. Every index is a multiple of three, as "
                            "ade6ba9's untwisted-plane rule requires. Two witnesses are frozen and re-verified, with exact "
                            "full weight decompositions. OPEN: hypercharge and its normalisation, level-1 GUT breaking "
                            "(no adjoint Higgs), and vector-like exotics.",
                   "control": out["control"], "tally": tally, "examples": examples, "checks": checks, "valid": valid,
                   "status": "positive existence over deterministic samples; the completeness pattern is measured, not proved",
                   "sources": ["Holotrade fbd2c5f", "Holotrade ade6ba9",
                               "classical Z3 orbifold model building: IKNQ 1987; FIQS 1990; Casas-Munoz"]}
        with open(os.path.join(ROOT, "data", "w33_vacuum_three_family_gut.json"), "w") as f:
            json.dump(payload, f, indent=1)
        print("written")


if __name__ == "__main__":
    main()
