#!/usr/bin/env python3
"""Exact mass-12 / mass-16 incidence-excess classifier for W(3,3).

For every nonnegative integer excess vector e in the real point-line incidence
image with mass s=4k, the SRG identity gives

    A e = 2 e + k 1.

The committed mass-8 theorem proves the k=1,2 cases are respectively one and
two point pencils.  This pass attacks k=3 and k=4 without enumerating all
integer vectors blindly.

A point pencil P is componentwise contained in e exactly when all four lines
through that point have positive excess.  CP-SAT therefore searches for an
admissible e with *no* contained point pencil.  If that model is UNSAT, every e
contains a pencil; subtracting it preserves nonnegativity and changes k -> k-1.
Induction from the certified mass-8 theorem then proves every mass-12 vector is
a sum of three pencils and every mass-16 vector a sum of four pencils.

The finite pencil-generated vector sets are then enumerated exactly and split
into PSp(4,3) orbits using five explicit projective symplectic transvections.
The generated permutation group is independently closed and required to have
order 25,920 on the 40 projective points.

UNKNOWN is never promoted to a theorem.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
import importlib.util
import itertools
import json
from pathlib import Path
import time

from ortools.sat.python import cp_model

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "mass12_mass16_excess_pencil_induction.json"
MASS8_PATH = ROOT / "analysis" / "the_mass_eight_excess_is_two_pencils.py"


def load_base():
    spec = importlib.util.spec_from_file_location("mass8_induction_base", MASS8_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import mass-eight theorem")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    pts, lines, line_index, pencils, adj = mod.geometry()
    return mod, pts, lines, line_index, pencils, adj


def compose(a, b):
    return tuple(a[b[i]] for i in range(len(b)))


def point_perm(mod, pts, v, lam=1):
    pidx = {p: i for i, p in enumerate(pts)}
    out = []
    for x in pts:
        s = mod.form(x, v)
        y = mod.norm(tuple((x[j] + lam * s * v[j]) % 3 for j in range(4)))
        out.append(pidx[y])
    return tuple(out)


def five_psp_generators(mod, pts, lines, line_index):
    seeds = [
        mod.norm((1, 0, 0, 0)),
        mod.norm((0, 1, 0, 0)),
        mod.norm((0, 0, 1, 0)),
        mod.norm((0, 0, 0, 1)),
        mod.norm((1, 1, 0, 0)),
    ]
    pgens, lgens = [], []
    for v in seeds:
        pp = point_perm(mod, pts, v, 1)
        lp = []
        for L in lines:
            image = frozenset(pp[p] for p in L)
            if image not in line_index:
                raise AssertionError("transvection lost W33 line")
            lp.append(line_index[image])
        pgens.append(pp)
        lgens.append(tuple(lp))

    identity = tuple(range(40))
    group = {identity}
    q = deque([identity])
    while q:
        g = q.popleft()
        for h in pgens:
            z = compose(h, g)
            if z not in group:
                group.add(z)
                q.append(z)
                if len(group) > 25920:
                    raise AssertionError("generator closure exceeded PSp(4,3)")
    if len(group) != 25920:
        raise AssertionError(f"five transvections generated {len(group)}, expected 25920")
    return tuple(pgens), tuple(lgens), len(group)


def pencil_free_counterexample(mass, pencils, adj, *, budget, workers):
    k = mass // 4
    model = cp_model.CpModel()
    e = [model.NewIntVar(0, k, f"e{i}") for i in range(40)]
    zero = [model.NewBoolVar(f"z{i}") for i in range(40)]
    model.Add(sum(e) == mass)
    for i in range(40):
        model.Add(sum(e[j] for j in adj[i]) == 2 * e[i] + k)
        model.Add(e[i] == 0).OnlyEnforceIf(zero[i])
        model.Add(e[i] >= 1).OnlyEnforceIf(zero[i].Not())
    # No point pencil may be componentwise contained: every pencil has a zero.
    for P in pencils:
        support = [i for i, x in enumerate(P) if x]
        assert len(support) == 4
        model.Add(sum(zero[i] for i in support) >= 1)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(budget)
    solver.parameters.num_search_workers = int(workers)
    solver.parameters.random_seed = 20260908 + mass
    start = time.time()
    st = solver.Solve(model)
    elapsed = round(time.time() - start, 3)
    status = {
        cp_model.OPTIMAL: "SAT",
        cp_model.FEASIBLE: "SAT",
        cp_model.INFEASIBLE: "UNSAT",
    }.get(st, "UNKNOWN")
    out = {
        "status": status,
        "seconds": elapsed,
        "budgetSeconds": float(budget),
        "workers": int(workers),
        "branches": solver.NumBranches(),
        "conflicts": solver.NumConflicts(),
    }
    if status == "SAT":
        witness = tuple(solver.Value(x) for x in e)
        out["witness"] = list(witness)
        out["witnessHistogram"] = {str(a): b for a, b in sorted(Counter(witness).items())}
    return out


def add_pencils(multiset, pencils):
    out = [0] * 40
    for p in multiset:
        P = pencils[p]
        for i, x in enumerate(P):
            out[i] += x
    return tuple(out)


def generated_vectors(k, pencils, adj):
    counts = Counter()
    first_decomp = {}
    candidates = 0
    for ms in itertools.combinations_with_replacement(range(40), k):
        candidates += 1
        e = add_pencils(ms, pencils)
        assert sum(e) == 4 * k
        assert all(sum(e[j] for j in adj[i]) == 2 * e[i] + k for i in range(40))
        counts[e] += 1
        first_decomp.setdefault(e, ms)
    expected = {3: 11480, 4: 123410}[k]
    assert candidates == expected
    return counts, first_decomp, candidates


def act_vector(e, perm):
    out = [0] * 40
    for i, x in enumerate(e):
        out[perm[i]] = x
    return tuple(out)


def orbit_catalogue(vectors, first_decomp, decomposition_counts, lgens):
    remaining = set(vectors)
    rows = []
    while remaining:
        seed = min(remaining)
        orb = {seed}
        q = deque([seed])
        while q:
            x = q.popleft()
            for g in lgens:
                y = act_vector(x, g)
                if y not in vectors:
                    raise AssertionError("PSp action left pencil-generated set")
                if y not in orb:
                    orb.add(y)
                    q.append(y)
        remaining.difference_update(orb)
        hist = Counter(seed)
        rows.append({
            "orbitSize": len(orb),
            "representative": list(seed),
            "representativeHistogram": {str(a): b for a, b in sorted(hist.items())},
            "supportSize": 40 - hist.get(0, 0),
            "onePencilMultiset": list(first_decomp[seed]),
            "representativeDecompositionMultiplicity": decomposition_counts[seed],
            "orbitDecompositionMultiplicityHistogram": {
                str(a): b for a, b in sorted(Counter(decomposition_counts[x] for x in orb).items())
            },
        })
    rows.sort(key=lambda r: (r["representativeHistogram"].get("0", 0), r["representative"]))
    assert sum(r["orbitSize"] for r in rows) == len(vectors)
    return rows


def classify(k, mod, pencils, adj, lgens, *, budget, workers, prerequisite_ok):
    mass = 4 * k
    no_pencil = pencil_free_counterexample(mass, pencils, adj, budget=budget, workers=workers)
    counts, first, candidates = generated_vectors(k, pencils, adj)
    vectors = set(counts)
    orbits = orbit_catalogue(vectors, first, counts, lgens)
    theorem_ok = prerequisite_ok and no_pencil["status"] == "UNSAT"
    return {
        "mass": mass,
        "k": k,
        "multisetCandidates": candidates,
        "distinctPencilGeneratedVectors": len(vectors),
        "decompositionMultiplicityHistogram": {str(a): b for a, b in sorted(Counter(counts.values()).items())},
        "pencilFreeCounterexampleSearch": no_pencil,
        "allAdmissibleVectorsArePencilSums": theorem_ok,
        "orbitCount": len(orbits),
        "orbits": orbits,
        "theorem": (
            f"Every nonnegative integer mass-{mass} vector satisfying Ae=2e+{k}1 contains a point pencil; "
            f"subtracting it reduces to the certified mass-{mass-4} case. Hence all such vectors are sums of {k} point pencils."
            if theorem_ok else
            f"The complete pencil-generated mass-{mass} family is catalogued, but no global classification theorem is claimed because the pencil-free search was not exact UNSAT or its induction prerequisite was unavailable."
        ),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=float, default=120.0)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    if args.budget <= 0 or args.workers <= 0:
        raise ValueError("positive budget/workers required")

    mod, pts, lines, line_index, pencils, adj = load_base()
    pgens, lgens, group_order = five_psp_generators(mod, pts, lines, line_index)
    # Recheck the already-proved base theorem rather than silently assuming a stale file.
    mass8 = json.loads((ROOT / "data" / "mass_eight_excess_two_pencils.json").read_text())
    base_ok = mass8.get("status") == "PASS" and mass8.get("checks", {}).get("mass_eight_is_exactly_two_pencils") is True

    m12 = classify(3, mod, pencils, adj, lgens, budget=args.budget, workers=args.workers, prerequisite_ok=base_ok)
    m16 = classify(4, mod, pencils, adj, lgens, budget=args.budget, workers=args.workers, prerequisite_ok=m12["allAdmissibleVectorsArePencilSums"])
    checks = {
        "mass8_base_certificate_loaded": base_ok,
        "five_transvections_generate_PSp_25920": group_order == 25920,
        "mass12_pencil_free_model_exact_unsat": m12["pencilFreeCounterexampleSearch"]["status"] == "UNSAT",
        "mass12_all_vectors_are_three_pencils": m12["allAdmissibleVectorsArePencilSums"],
        "mass16_pencil_free_model_exact_unsat": m16["pencilFreeCounterexampleSearch"]["status"] == "UNSAT",
        "mass16_all_vectors_are_four_pencils": m16["allAdmissibleVectorsArePencilSums"],
        "orbit_partitions_complete": sum(x["orbitSize"] for x in m12["orbits"]) == m12["distinctPencilGeneratedVectors"] and sum(x["orbitSize"] for x in m16["orbits"]) == m16["distinctPencilGeneratedVectors"],
    }
    out = {
        "schema": "holotrade.w33-mass12-mass16-pencil-induction.v1",
        "status": "PASS" if all(checks.values()) else "PARTIAL",
        "checks": checks,
        "group": {"action": "PSp(4,3) on 40 W33 points/lines", "order": group_order, "generators": 5},
        "mass12": m12,
        "mass16": m16,
        "application": {
            "size113": "For a 113-leaf blocker, each axis line-load excess over baseline 11 has mass 12, so an exact mass-12 classification reduces its possible load profiles to the listed PSp orbits.",
            "size114": "For a 114-leaf blocker, each axis line-load excess over baseline 11 has mass 16, so an exact mass-16 classification reduces its possible load profiles to the listed PSp orbits."
        },
        "boundary": "This classifies axis line-load excess vectors. It does not itself prove existence or nonexistence of 113/114 leaf blockers; row/column profile pairs still need exact product-line gluing.",
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    if args.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
