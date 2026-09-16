#!/usr/bin/env python3
"""
THE W(3,3) VACUUM HAS THREE-FAMILY WILSON-LINE DEFORMATIONS, AND THE THREE IS THE
NUMBER OF COMPLEX PLANES OF T^6, NOT W(3,3).

Continues fbd2c5f. There the W(3,3) twist of E8 (the A8 shift) turned out to have
one T^6/Z_3 partner, D7 + U1, giving SU(9) x SO(14) x U(1). Here discrete Wilson
lines a_1, a_2, a_3 are switched on, one per A2 torus. The consistency conditions
(Ibanez-Nilles-Quevedo) are
    3 a_i^2 in 2Z,    3 V.a_i in Z,    3 a_i.a_j in Z.
The fixed point n in F_3^3 carries the local shift V + sum n_i a_i. The gauge roots
satisfy P.V in Z and P.a_i in Z. Untwisted matter has P.V = 1/3 mod 1 and
P.a_i in Z, once per complex plane. The twisted massless states at n are
P in Lambda + V_n with P^2/2 + N = 2/3; when a_i = 0 the untouched torus gives a
multiplicity 3.

For every SU(3) x SU(2) pair of gauge factors, the net quark-doublet number
#(3,2) - #(3bar,2) is computed by Weyl-character inversion on the weights. That
count already includes multiplicities from the other gauge factors.

WHAT IS CHECKED (deterministic samples: 1500 SU(3)xSU(2) models per family below).
  1. Consistency. Every sampled model is SU(n)^3 anomaly-free, for all SU(n)
     factors with n >= 3. There are 0 anomalous models, at 1, 2 and 3 Wilson lines,
     in both the W(3,3) vacuum and the control. The anomaly check therefore
     validates the Wilson-line rules and the spectrum builder together.
  2. Localisation law (measured, not proved). Whenever SU(3) x SU(2) survives, the
     net quark-doublet index at every one of the 27 fixed points is 0, although the
     local spectra themselves differ between fixed points. All net (3,2)
     chirality is untwisted. Each complex plane contributes the same index I, so the
     net family number is 3I, observed in {0, +-3, +-6}.
  3. Existence. The W(3,3) vacuum has Wilson-line models with net quark doublets
     exactly 3 (I = 1). A witness is frozen and re-verified: gauge group, anomaly
     freedom, per-plane index 1, and zero index at all 27 fixed points.
  4. Control. The standard embedding E6 x SU(3) x E8 obeys the same law with the
     same values. So the factor 3 belongs to the Z_3 orbifold of T^6, namely its
     three untwisted planes. It does not belong to the W(3,3) twist.

THE TOE READING.  The substrate twist does sit in string vacua with three chiral
quark-doublet families. But in that vacuum "three" is the number of complex
dimensions of the compact space, exactly as in the standard embedding. The
W(3,3) twist neither supplies it nor selects it. A corpus claim that W(3,3)
explains three generations is, in this realisation, an over-read.

OPEN (not built here): a hypercharge U(1)_Y with the Standard Model family
charges, its normalisation k_Y, and the removal of vector-like exotics. Net
(3,2) = 3 is necessary for a Standard Model, not sufficient.

SCOPE.  Z_3 orbifolds with Wilson lines and three-family constructions are
classical (Ibanez-Kim-Nilles-Quevedo 1987; Font-Ibanez-Quevedo-Sierra 1990). The
localisation law is recorded here as a measurement over samples, not as a theorem.
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
spec = importlib.util.spec_from_file_location("het", os.path.join(ROOT, "analysis", "the_w33_twist_is_the_su9_heterotic_embedding.py"))
het = importlib.util.module_from_spec(spec)
spec.loader.exec_module(het)

NAMES = {(2, 1): "A1", (6, 2): "A2", (12, 3): "A3", (20, 4): "A4", (30, 5): "A5", (42, 6): "A6", (56, 7): "A7",
         (72, 8): "A8", (24, 4): "D4", (40, 5): "D5", (60, 6): "D6", (84, 7): "D7", (112, 8): "D8",
         (72, 6): "E6", (126, 7): "E7", (240, 8): "E8"}
# A generic vector must not be orthogonal to any root, or the positive system, and with it
# every Dynkin label, is ill defined. Integer-plus-constant vectors FAIL: 16 of the 480 roots
# are orthogonal to arange(1,17) + pi/10. Square roots of distinct primes are linearly
# independent over Q, so no integer combination of them vanishes. Asserted in main().
GEN = np.sqrt(np.array([2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53], dtype=float))


def cname(C):
    return NAMES.get((len(C), int(np.linalg.matrix_rank(C.astype(float)))), "?")


class Builder:
    def __init__(self):
        R6 = het.e8_roots6()
        Z8 = np.zeros_like(R6)
        self.R16 = np.vstack([np.hstack([R6, Z8]), np.hstack([Z8, R6])])
        self.R6 = R6
        self.U = het.e8_vectors_doubled(8)
        self.lam6 = 3 * het.e8_vectors_doubled(4)

    def shift(self, fixed, a):
        for z in self.U:
            if int(np.sum((self.R6 @ z) % S == 0)) == fixed and int(z @ z // 8) % 3 == a:
                return z

    @staticmethod
    def cvp6(x):
        y = x / 6.0
        best = None
        for off in (0.0, 0.5):
            z = y - off
            r = np.round(z)
            if int(r.sum()) % 2:
                k = np.argmax(np.abs(z - r))
                r[k] += 1.0 if z[k] > r[k] else -1.0
            p = r + off
            dd = np.sum((y - p) ** 2)
            if best is None or dd < best[0]:
                best = (dd, p)
        return np.round(best[1] * 6).astype(np.int64)

    def coset(self, Vi):
        Vi = Vi - self.cvp6(Vi)
        W = self.lam6 + Vi
        hN = np.sum(W ** 2, axis=1)
        k = hN <= 48
        return W[k], hN[k]

    def line(self, rng, V, others):
        U = self.U
        while True:
            a = np.concatenate([U[rng.randrange(len(U))], U[rng.randrange(len(U))]])
            if int(a @ a) % 24 == 0 and int(V @ a) % 12 == 0 and all(int(a @ b) % 12 == 0 for b in others):
                return a

    def model(self, V, lines):
        d = self.R16 @ V
        ok = np.ones(len(self.R16), bool)
        for a in lines:
            ok &= (self.R16 @ a) % S == 0
        gauge = self.R16[ok & (d % S == 0)]
        untw = self.R16[ok & ((d % S) == 12)]
        fps = {}
        for ns in itertools.product(range(3), repeat=3):
            Vf = V + sum(k * a for k, a in zip(ns, lines + [0 * V] * (3 - len(lines))))
            W1, h1 = self.coset(Vf[:8])
            W2, h2 = self.coset(Vf[8:])
            st = []
            for tot, m in ((48, 1), (24, 3), (0, 9)):
                ii = np.nonzero((h1[:, None] + h2[None, :]) == tot)
                if len(ii[0]):
                    st.append((np.hstack([W1[ii[0]], W2[ii[1]]]), m))
            fps[ns] = st
        return gauge, untw, fps


def simple_roots(C):
    assert np.min(np.abs(C @ GEN)) > 1e-9, "generic vector is orthogonal to a root"
    pos = [r for r in C if r @ GEN > 0]
    ps = {tuple(r) for r in pos}
    sr = [r for r in pos if not any(tuple(r - s) in ps for s in pos if not np.array_equal(s, r))]
    assert len(sr) == int(np.linalg.matrix_rank(C.astype(float))), "simple system has the wrong size"
    for x, y in itertools.combinations(sr, 2):             # simple roots pair at -1, never +1
        assert int(x @ y) // S <= 0, "not a simple system"
    return sr


def quark_index(c3, c2, states):
    a, b = simple_roots(c3)
    beta = c2[0] if c2[0] @ GEN > 0 else c2[1]
    M = {}
    for P, m in states:
        L = np.stack([P @ a, P @ b, P @ beta], axis=1) // S
        for row, cnt in zip(*np.unique(L, axis=0, return_counts=True)):
            k = tuple(int(x) for x in row)
            M[k] = M.get(k, 0) + m * int(cnt)

    def N(lam):
        x0 = (lam[0] + 1, lam[1] + 1)
        orb, fr = {x0: 1}, [x0]
        while fr:
            nf = []
            for (p, q) in fr:
                for y in ((-p, p + q), (p + q, -q)):
                    if y not in orb:
                        orb[y] = -orb[(p, q)]
                        nf.append(y)
            fr = nf
        return sum(sg * sg2 * M.get((p - 1, q - 1, r - 1), 0)
                   for (p, q), sg in orb.items() for r, sg2 in ((lam[2] + 1, 1), (-(lam[2] + 1), -1)))
    return N((1, 0, 1)) - N((0, 1, 1))


def triplet_index(c3, states):
    """#3 - #3bar of SU(3) (teeth: the same inversion must see twisted triplets)."""
    a, b = simple_roots(c3)
    M = {}
    for P, m in states:
        L = np.stack([P @ a, P @ b], axis=1) // S
        for row, cnt in zip(*np.unique(L, axis=0, return_counts=True)):
            k = tuple(int(x) for x in row)
            M[k] = M.get(k, 0) + m * int(cnt)

    def N(lam):
        x0 = (lam[0] + 1, lam[1] + 1)
        orb, fr = {x0: 1}, [x0]
        while fr:
            nf = []
            for (p, q) in fr:
                for y in ((-p, p + q), (p + q, -q)):
                    if y not in orb:
                        orb[y] = -orb[(p, q)]
                        nf.append(y)
            fr = nf
        return sum(sg * M.get((p - 1, q - 1), 0) for (p, q), sg in orb.items())
    return N((1, 0)) - N((0, 1))


def cubic_free(comps, states, rng):
    for c in comps:
        if not cname(c).startswith("A") or len(c) <= 2:
            continue
        for _ in range(2):
            x = sum(rng.randint(-4, 4) * r for r in c[rng.sample(range(len(c)), min(len(c), 8))])
            if sum(m * int(np.sum((P @ x).astype(object) ** 3)) for P, m in states if len(P)) != 0:
                return False
    return True


def analyse(B, V, lines, rng):
    gauge, untw, fps = B.model(V, lines)
    comps = het.root_components(gauge)
    mult_fp = 3 ** (3 - len(lines))
    all_states = [(untw, 3)] + [(P, m * mult_fp) for ns, st in fps.items() if all(ns[i] == 0 for i in range(len(lines), 3))
                                for P, m in st]
    anomaly_free = cubic_free(comps, all_states, rng)
    A2 = [c for c in comps if cname(c) == "A2"]
    A1 = [c for c in comps if cname(c) == "A1"]
    pairs = []
    for c3 in A2:
        for c2 in A1:
            Iu = quark_index(c3, c2, [(untw, 1)])
            loc = [quark_index(c3, c2, st) for ns, st in fps.items() if all(ns[i] == 0 for i in range(len(lines), 3))]
            total = 3 * Iu + mult_fp * sum(loc)
            pairs.append({"planeIndex": Iu, "fixedPointIndices": sorted(set(loc)), "net": total,
                          "localSpectraDiffer": len({sum(len(P) * m for P, m in st) for ns, st in fps.items()
                                                     if all(ns[i] == 0 for i in range(len(lines), 3))}) > 1})
    return {"gauge": sorted(cname(c) for c in comps), "anomalyFree": anomaly_free, "pairs": pairs}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--target", type=int, default=1500)
    args = ap.parse_args()
    B = Builder()
    assert np.min(np.abs(B.R16 @ GEN)) > 1e-9              # no root is orthogonal to the generic vector
    V_w33 = np.concatenate([B.shift(72, 1), B.shift(84, 2)])
    V_std = np.concatenate([B.shift(78, 0), np.zeros(8, dtype=np.int64)])
    checks, families, witness = {}, {}, None
    for label, V in (("w33", V_w33), ("standard", V_std)):
        for nl in (1, 2, 3):
            rng = random.Random(1000 * nl + (7 if label == "w33" else 13))
            sampled = anomalous = with_pairs = 0
            nets, planes, locals_, differ = {}, {}, set(), 0
            while with_pairs < args.target and sampled < (3000 if nl == 1 else 60 * args.target):
                lines = []
                for _ in range(nl):
                    lines.append(B.line(rng, V, lines))
                sampled += 1
                gauge_ok = True
                d = B.R16 @ V
                ok = np.ones(len(B.R16), bool)
                for a in lines:
                    ok &= (B.R16 @ a) % S == 0
                comps = het.root_components(B.R16[ok & (d % S == 0)])
                names = [cname(c) for c in comps]
                if not ("A2" in names and "A1" in names):
                    if sampled % 25 == 0:          # spot-check anomaly freedom on models without the pair too
                        res = analyse(B, V, lines, rng)
                        anomalous += not res["anomalyFree"]
                    continue
                res = analyse(B, V, lines, rng)
                with_pairs += 1
                anomalous += not res["anomalyFree"]
                for p in res["pairs"]:
                    nets[p["net"]] = nets.get(p["net"], 0) + 1
                    planes[p["planeIndex"]] = planes.get(p["planeIndex"], 0) + 1
                    locals_.update(p["fixedPointIndices"])
                    differ += p["localSpectraDiffer"]
                    if label == "w33" and nl == 3 and witness is None and abs(p["net"]) == 3 and p["localSpectraDiffer"] \
                            and len(res["gauge"]) <= 5:
                        witness = {"lines": [[int(x) for x in a] for a in lines], "gauge": res["gauge"]}
            key = "%s_%dlines" % (label, nl)
            families[key] = {"sampled": sampled, "withSU3xSU2": with_pairs, "anomalous": anomalous,
                             "nets": {str(k): v for k, v in sorted(nets.items())},
                             "planeIndex": {str(k): v for k, v in sorted(planes.items())},
                             "fixedPointIndexValues": sorted(locals_), "pairsWithDifferingLocalSpectra": differ}
            print("  %-16s sampled %6d  SU3xSU2 models %5d  anomalous %d  nets %s  fixed-point index values %s  "
                  "(pairs with differing local spectra: %d)" % (key, sampled, with_pairs, anomalous, dict(sorted(nets.items())),
                                                               sorted(locals_), differ), flush=True)
    # teeth: the index machinery sees twisted chirality when it is there
    gauge, untw, fps = B.model(V_std, [])
    a2 = next(c for c in het.root_components(gauge) if cname(c) == "A2")
    tw_triplets = triplet_index(a2, fps[(0, 0, 0)])
    un_triplets = triplet_index(a2, [(untw, 1)])
    print("  teeth: standard embedding, no lines: SU(3) triplet index per fixed point", tw_triplets, "per plane", un_triplets)
    checks["teeth_twisted_triplets_seen"] = abs(tw_triplets) == 3 and abs(un_triplets) == 27 and tw_triplets * un_triplets < 0
    checks["no_anomalous_model"] = all(f["anomalous"] == 0 for f in families.values())
    fam_pairs = [f for k, f in families.items() if not k.endswith("1lines")]
    checks["fixed_point_quark_index_always_zero"] = all(f["fixedPointIndexValues"] in ([0], []) for f in families.values())
    checks["net_is_three_times_plane_index"] = all(
        sorted(int(k) for k in f["nets"]) == sorted(3 * int(k) for k in f["planeIndex"]) for f in families.values())
    checks["local_spectra_do_differ"] = families["w33_3lines"]["pairsWithDifferingLocalSpectra"] > 0
    checks["w33_has_three_family_models"] = any(k in ("3", "-3") for k in families["w33_2lines"]["nets"]) and \
        any(k in ("3", "-3") for k in families["w33_3lines"]["nets"])
    checks["standard_control_same_law"] = any(k in ("3", "-3") for k in families["standard_2lines"]["nets"]) and \
        families["standard_3lines"]["fixedPointIndexValues"] in ([0], [])
    checks["enough_su3su2_models"] = all(f["withSU3xSU2"] >= 100 for f in fam_pairs)
    # witness re-verification
    if witness:
        lines = [np.array(a, dtype=np.int64) for a in witness["lines"]]
        res = analyse(B, V_w33, lines, random.Random(99))
        conds = all(int(a @ a) % 24 == 0 and int(V_w33 @ a) % 12 == 0 for a in lines) and \
            all(int(a @ b) % 12 == 0 for a, b in itertools.combinations(lines, 2))
        wp = [p for p in res["pairs"] if abs(p["net"]) == 3]
        witness.update({"conditions": conds, "anomalyFree": res["anomalyFree"], "pairs": res["pairs"]})
        checks["witness_verified"] = conds and res["anomalyFree"] and bool(wp) and \
            all(p["fixedPointIndices"] == [0] and abs(p["planeIndex"]) == 1 for p in wp)
        print("  witness gauge", witness["gauge"], "pairs", res["pairs"])
    else:
        checks["witness_verified"] = False
    for k, v in checks.items():
        print("  %-42s %s" % (k, v))
    valid = all(checks.values())
    print("VALID:", valid)
    if args.write:
        out = {"claim": "In the W(3,3)-twist heterotic vacuum (fbd2c5f) with Z3 Wilson lines, all sampled models are "
                        "SU(n)^3-free; whenever SU(3)xSU(2) survives, net quark doublets are 3x the untwisted per-plane index "
                        "(fixed-point index always 0), and net = 3 occurs. The same holds for the standard embedding, so the "
                        "three is the three complex planes of T^6, not W(3,3). Hypercharge/exotics OPEN.",
               "families": families, "witness": witness, "checks": checks, "valid": valid,
               "status": "measurement over deterministic samples; localisation law not proved",
               "sources": ["Holotrade fbd2c5f", "Ibanez-Nilles-Quevedo Wilson-line conditions; Ibanez-Kim-Nilles-Quevedo; "
                                                "Font-Ibanez-Quevedo-Sierra"]}
        with open(os.path.join(ROOT, "data", "w33_vacuum_wilson_line_families.json"), "w") as f:
            json.dump(out, f, indent=1)
        print("written")


if __name__ == "__main__":
    main()
