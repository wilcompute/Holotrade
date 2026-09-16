#!/usr/bin/env python3
"""
THE W(3,3) VACUUM NEVER COMPLETES A STANDARD MODEL FAMILY: THE ANTI-FIVE SURVIVES
WHOLE, THE TEN ALWAYS LOSES u^c AND e^c.

Continues 35eb923, which found three complete GUT families in Wilson-line
deformations of the vacuum forced by the W(3,3) twist (fbd2c5f): SU(5) with
n10 = n5bar = 3 and SO(10) with n16 = 3. Three chiral families is necessary for a
Standard Model, not sufficient, so this file breaks those GUTs the rest of the way
and counts Standard Model matter.

HYPERCHARGE IS NOT SEARCHED, IT IS FORCED. Breaking the GUT factor with a further
Z_3 Wilson line leaves U(1)s inside the GUT factor, so hypercharge is canonically
embedded and its normalisation is fixed, not chosen:
  - inside SU(5), the direction orthogonal to the surviving SU(3) x SU(2) is unique
    up to scale and sign; the scale is set by the 5 carrying {-1/3 x3, +1/2 x2} and
    the sign by the same condition;
  - inside SO(10), the plane orthogonal to SU(3) x SU(2)_L is two-dimensional, and
    hypercharge is the direction whose values on a 16 are exactly the Standard
    Model family charges {1/6 x6, -2/3 x3, 1/3 x3, -1/2 x2, 1, 0}.
Both give k_Y = 5/3, which is checked, not assumed.

CONTROLS (the machinery must see a complete family when one is there).
  A. The UNBROKEN three-family SU(5) model, decomposed under an SU(3) x SU(2) x U(1)
     inside it, returns (Q, u^c, d^c, L, e^c) = (3,3,3,3,3) with k_Y = 5/3 and zero
     fractionally charged colour singlets. It must: 3 x (10 + 5bar) IS three families.
  B. The unbroken three-family SO(10) model likewise returns (3,3,3,3,3).
  C. Teeth: with the hypercharge orientation flipped, control A returns
     (0,0,0,-3,-3) instead. The orientation is therefore fixed by the 5's charges,
     not chosen to make an answer come out.

WHAT IS MEASURED. Over deterministic samples of Wilson-line breakings:
  1. No model has a complete Standard Model family. The best achieved is three of
     the five species, never five.
  2. The law behind it, exact on every sampled model with chiral quark doublets:
        Q != 0  =>  u^c = e^c = 0  and  d^c = L.
     In SU(5) terms 10 = Q + u^c + e^c and 5bar = d^c + L, so the anti-five survives
     whole while the ten always pairs off its up-type and charged-lepton singlets.
     The surviving chiral content is 3 x (Q + d^c + L).
  3. Q is always a multiple of 3, which is ade6ba9's rule: quark doublets carry no
     index at any fixed point, so they come only from the three untwisted planes.
     With three Wilson lines the OTHER species can be 1 or 2, so the multiple of
     three is special to the doublets.
  4. Breaking SO(10) two ways gives the same obstruction, with the 16 fragmenting
     into {Q}, {u^c, d^c}, {L, e^c} and exactly one fragment chiral per model.
  5. No sampled model is free of fractionally charged colour singlets.

READING. The vacuum that the W(3,3) twist forces carries three chiral GUT families,
and canonical hypercharge, and still does not contain the Standard Model: the up
quark and the electron never become chiral together with the quark doublets. This
bounds the physics programme from inside rather than by taste.

SCOPE. A negative over deterministic samples plus an exact conditional law on those
samples, not a theorem: it says no sampled breaking, not no breaking. Z_3 orbifold
model building is classical (Ibanez-Kim-Nilles-Quevedo 1987; Font-Ibanez-Quevedo-
Sierra 1990; Casas-Munoz).
"""

import argparse
import importlib.util
import itertools
import json
import os
import random
from fractions import Fraction as Fr

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = 36
SM16 = sorted([Fr(1, 6)] * 6 + [Fr(-2, 3)] * 3 + [Fr(1, 3)] * 3 + [Fr(-1, 2)] * 2 + [Fr(1)] + [Fr(0)])
SM5 = sorted([Fr(-1, 3)] * 3 + [Fr(1, 2)] * 2)


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, "analysis", name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gut = _load("does_the_w33_vacuum_contain_a_three_family_gut")
fam, het = gut.fam, gut.het


def weights_of(parent, node):
    """every weight of the irrep of this factor with highest weight omega_node."""
    sr, A, _ = gut.diagram(parent)
    omega = np.linalg.inv(np.array(A, float)) @ np.array(sr, float)
    srm = np.array(sr, float)
    W, frontier = {tuple(np.round(omega[node] * 12).astype(int))}, [omega[node]]
    while frontier:
        nf = []
        for w in frontier:
            for al in srm:
                if int(round(float(w @ al) / S)) > 0:
                    w2 = w - al
                    k = tuple(np.round(w2 * 12).astype(int))
                    if k not in W:
                        W.add(k)
                        nf.append(w2)
        frontier = nf
    return np.array([np.array(k, float) / 12 for k in W])


def hypercharge(parent, su3, su2, flip=False):
    """the canonically embedded hypercharge inside the GUT factor, or None."""
    basis = np.array(parent, float)
    _, sv, vt = np.linalg.svd(basis)
    Bs = vt[:int(np.sum(sv > 1e-8))]
    M = np.array(list(su3) + list(su2), float)
    Mb = M @ Bs.T
    _, _, vt2 = np.linalg.svd(Mb)
    null = [Bs.T @ vt2[i] for i in range(vt2.shape[0]) if np.linalg.norm(Mb @ vt2[i]) < 1e-7]
    _, _, info = gut.diagram(parent)
    if len(null) == 1:                                     # SU(5): scale by the 5, orient by the 5
        y = null[0]
        five = weights_of(parent, info["path"][0])
        if len(five) != 5:
            return None
        cross = [r for r in parent if abs(float(r @ y)) > 1e-9]
        if not cross:
            return None
        y = y * ((5.0 / 6.0) / (abs(float(cross[0] @ y)) / S))
        for cand in (y, -y):
            if sorted(Fr(int(round(float(w @ cand) / S * 6)), 6) for w in five) == SM5:
                return -cand if flip else cand
        return None
    if len(null) == 2:                                     # SO(10): fix by the 16's Standard Model charges
        sixteen = weights_of(parent, info["branches"][0][0])
        if len(sixteen) != 16:
            return None
        srs = list(gut.diagram(np.array(su3))[0]) + list(gut.diagram(np.array(su2))[0])
        lab = [[int(round(float(w @ a) / S)) for a in srs] for w in sixteen]
        q32 = [i for i in range(16) if tuple(lab[i]) == (1, 0, 1)]
        q31 = [i for i in range(16) if lab[i][0] == 0 and lab[i][1] == 1 and lab[i][2] == 0]
        if not q32 or not q31:
            return None
        for uc in (Fr(-2, 3), Fr(1, 3)):
            A2 = np.array([[float(sixteen[q32[0]] @ n) / S, float(sixteen[q31[0]] @ n) / S] for n in null]).T
            try:
                coef = np.linalg.solve(A2, np.array([1 / 6, float(uc)]))
            except np.linalg.LinAlgError:
                continue
            cand = coef[0] * null[0] + coef[1] * null[1]
            if sorted(Fr(int(round(float(w @ cand) / S * 6)), 6) for w in sixteen) == SM16:
                return -cand if flip else cand
    return None


def sm_content(B, V, lines, parent, su3, su2, flip=False):
    """Standard Model species counts and fractionally charged colour singlets."""
    y = hypercharge(parent, su3, su2, flip)
    if y is None:
        return None
    _, states = gut.model_states(B, V, list(lines))
    srs = list(gut.diagram(np.array(su3))[0]) + list(gut.diagram(np.array(su2))[0])
    AA = [[int(x @ z) // S for z in srs] for x in srs]
    byY = {}
    for P, m in states:
        if not len(P):
            continue
        Ys = (P @ y) / S
        L = np.stack([P @ a for a in srs], axis=1) // S
        for row, yy in zip(L, Ys):
            k = Fr(int(round(yy * 6)), 6)
            byY.setdefault(k, {})
            key = tuple(int(x) for x in row)
            byY[k][key] = byY[k].get(key, 0) + m
    reps = {"Q": ((1, 0, 1), Fr(1, 6)), "uc": ((0, 1, 0), Fr(-2, 3)), "dc": ((0, 1, 0), Fr(1, 3)),
            "L": ((0, 0, 1), Fr(-1, 2)), "ec": ((0, 0, 0), Fr(1))}
    conj = {"Q": ((0, 1, 1), Fr(-1, 6)), "uc": ((1, 0, 0), Fr(2, 3)), "dc": ((1, 0, 0), Fr(-1, 3)),
            "L": ((0, 0, 1), Fr(1, 2)), "ec": ((0, 0, 0), Fr(-1))}
    counts = {k: gut.N(byY.get(reps[k][1], {}), AA, list(reps[k][0])) - gut.N(byY.get(conj[k][1], {}), AA, list(conj[k][0]))
              for k in reps}
    exotic = sum(m for Yv, MM in byY.items() for lb, m in MM.items()
                 if (lb[0] - lb[1]) % 3 == 0 and (Yv + Fr(lb[2], 2)).denominator != 1)
    return {"kY": round(2 * float(y @ y) / S, 9), "counts": counts, "exotics": exotic}


def su3su2_inside(parent, kind):
    """a canonical SU(3) x SU(2) inside the unbroken GUT factor (for the controls)."""
    sr, _, info = gut.diagram(parent)
    if kind == "A4":
        p = info["path"]
        a, b, d = sr[p[0]], sr[p[1]], sr[p[3]]
    else:
        br = info["branches"]
        nodes = list(reversed(br[2])) + [info["fork"]] + [br[0][0], br[1][0]]
        a, b, d = sr[nodes[0]], sr[nodes[1]], sr[nodes[3]]
    return [a, b, a + b, -a, -b, -(a + b)], [d, -d]


def gauge(B, V, lines):
    ok = (B.R16 @ V) % S == 0
    for a in lines:
        ok &= (B.R16 @ a) % S == 0
    return B.R16[ok]


def three_family_parents(B, V, rng, kind, n, tries=400000):
    out = []
    for _ in range(tries):
        if len(out) >= n:
            break
        a = B.line(rng, V, [])
        comps = het.root_components(gauge(B, V, [a]))
        if not any(fam.cname(c) == kind for c in comps):
            continue
        _, st = gut.model_states(B, V, [a])
        for c in comps:
            if fam.cname(c) != kind:
                continue
            fi = gut.family_indices(c, st)
            if kind == "A4" and abs(fi["n10"]) == 3 and fi["n5bar"] == fi["n10"]:
                out.append((a, c))
                break
            if kind == "D5" and abs(fi["n16"]) == 3:
                out.append((a, c))
                break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--budget", type=int, default=4000, help="breakings sampled per family")
    args = ap.parse_args()
    B = fam.Builder()
    V = np.concatenate([B.shift(72, 1), B.shift(84, 2)])
    checks, out = {}, {}
    rng = random.Random(20260915)

    # controls: the unbroken three-family GUTs must decompose into three complete families
    for kind, tag in (("A4", "SU(5)"), ("D5", "SO(10)")):
        ps = three_family_parents(B, V, rng, kind, 1)
        assert ps, kind
        a1, c = ps[0]
        su3, su2 = su3su2_inside(c, kind)
        res = sm_content(B, V, [a1], c, su3, su2)
        vals = [res["counts"][k] for k in ("Q", "uc", "dc", "L", "ec")]
        print("  control %-6s unbroken three-family GUT -> %s  k_Y = %s  fractional singlets %d" % (
            tag, vals, res["kY"], res["exotics"]))
        checks["control_%s_three_complete_families" % tag[:5]] = len(set(vals)) == 1 and abs(vals[0]) == 3
        checks["control_%s_kY_five_thirds" % tag[:5]] = abs(res["kY"] - 5 / 3) < 1e-9
        out["control_" + tag] = {"counts": res["counts"], "kY": res["kY"], "exotics": res["exotics"]}
        if kind == "A4":
            flipped = sm_content(B, V, [a1], c, su3, su2, flip=True)
            fv = [flipped["counts"][k] for k in ("Q", "uc", "dc", "L", "ec")]
            print("  teeth: hypercharge orientation flipped ->", fv)
            checks["teeth_flipped_hypercharge_breaks_control"] = not (len(set(fv)) == 1 and abs(fv[0]) == 3)
            out["flippedControl"] = fv
            su5_parent = (a1, c)

    # scans: break the GUT the rest of the way with further Wilson lines
    scans = {}
    for kind, tag in (("A4", "SU(5)"), ("D5", "SO(10)")):
        ps = three_family_parents(B, V, rng, kind, 8)
        for nl in (2, 3):
            models, cond, dist, best, exotic_free = 0, {}, {}, (0, None), 0
            complete = []
            while models < args.budget:
                a1, c = ps[rng.randrange(len(ps))]
                lines = [a1]
                for _ in range(nl - 1):
                    lines.append(B.line(rng, V, lines))
                inside = np.array([r for r in gauge(B, V, lines) if tuple(r) in {tuple(x) for x in c}], dtype=np.int64)
                if not len(inside):
                    continue
                comps = het.root_components(inside)
                a2s = [x for x in comps if fam.cname(x) == "A2"]
                a1s = [x for x in comps if fam.cname(x) == "A1"]
                if len(a2s) != 1 or not a1s or len(a2s) + len(a1s) != len(comps):
                    continue
                res = None
                for c2 in a1s:
                    res = sm_content(B, V, lines, c, a2s[0], c2)
                    if res:
                        break
                if res is None:
                    continue
                models += 1
                exotic_free += res["exotics"] == 0
                v = [res["counts"][k] for k in ("Q", "uc", "dc", "L", "ec")]
                sgn = 1 if sum(v) >= 0 else -1
                score = sum(1 for x in v if x == 3 * sgn)
                best = max(best, (score, v), key=lambda z: z[0])
                dist[tuple(v)] = dist.get(tuple(v), 0) + 1
                if abs(v[0]) == 3:
                    cond[tuple(v[1:])] = cond.get(tuple(v[1:]), 0) + 1
                if score == 5:
                    complete.append({"lines": [[int(x) for x in a] for a in lines], "counts": res["counts"]})
            withQ = sum(cond.values())
            law = all(k[0] == 0 and k[3] == 0 and k[1] == k[2] for k in cond)
            scans["%s_%dlines" % (tag, nl)] = {
                "models": models, "withChiralQ": withQ, "exoticFree": exotic_free,
                "bestSpeciesMatched": best[0], "bestCounts": best[1], "completeFamilies": len(complete),
                "lawHolds": law, "qMultipleOfThree": all(k[0] % 3 == 0 for k in dist),
                "topCounts": {str(k): v for k, v in sorted(dist.items(), key=lambda kv: -kv[1])[:8]}}
            print("  %-6s %d lines: %5d breakings, %4d with chiral Q, best %d of 5 %s, complete families %d, "
                  "exotic-free %d, law %s" % (tag, nl, models, withQ, best[0], best[1], len(complete), exotic_free, law))
    out["scans"] = scans
    checks["no_complete_standard_model_family"] = all(s["completeFamilies"] == 0 for s in scans.values())
    checks["law_uc_ec_vectorlike_when_Q_chiral"] = all(s["lawHolds"] for s in scans.values() if s["withChiralQ"])
    checks["quark_doublets_multiple_of_three"] = all(s["qMultipleOfThree"] for s in scans.values())
    checks["best_is_three_of_five_species"] = max(s["bestSpeciesMatched"] for s in scans.values()) == 3
    checks["never_exotic_free"] = all(s["exoticFree"] == 0 for s in scans.values())
    checks["enough_breakings_with_chiral_Q"] = sum(s["withChiralQ"] for s in scans.values()) >= 500
    for k, v in checks.items():
        print("  %-46s %s" % (k, v))
    valid = all(checks.values())
    print("VALID:", valid)
    if args.write:
        payload = {"claim": "In the W(3,3)-twist vacuum (fbd2c5f, 35eb923), Wilson-line breakings of the three-family SU(5) "
                            "and SO(10) models never complete a Standard Model family. With canonical hypercharge (k_Y = 5/3, "
                            "checked) the exact law on every sampled breaking with chiral quark doublets is: Q != 0 implies "
                            "u^c = e^c = 0 and d^c = L, so the anti-five survives whole and the ten loses its up-type and "
                            "charged-lepton singlets. Controls: the unbroken three-family SU(5) and SO(10) models do decompose "
                            "into (3,3,3,3,3), and flipping the hypercharge orientation breaks that control.",
                   "controls": {k: v for k, v in out.items() if k.startswith("control") or k == "flippedControl"},
                   "scans": scans, "checks": checks, "valid": valid,
                   "status": "negative over deterministic samples with an exact conditional law; not a theorem",
                   "sources": ["Holotrade fbd2c5f", "Holotrade ade6ba9", "Holotrade 35eb923",
                               "classical Z3 model building: IKNQ 1987; FIQS 1990; Casas-Munoz"]}
        with open(os.path.join(ROOT, "data", "w33_vacuum_no_standard_model_family.json"), "w") as f:
            json.dump(payload, f, indent=1)
        print("written")


if __name__ == "__main__":
    main()
