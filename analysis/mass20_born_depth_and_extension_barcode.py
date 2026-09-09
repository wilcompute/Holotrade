#!/usr/bin/env python3
"""Search the only place genuinely new mass-20 negativity can be born.

For an admissible mass-4k excess e, subtracting a point pencil preserves the
excess equation and lowers k by one.  Therefore any exceptional mass-20 class
which contains a point pencil descends from an exceptional mass-16 class.  The
complete mass-16 exceptional census has seven PSp(4,3) orbits.  A *born* mass-20
exception must consequently contain no point pencil at all.

This script does two exact/explicit things:

1. CP-SAT enumerates (or, if the time/cap is hit, explicitly PARTIAL-enumerates)
   admissible mass-20 vectors satisfying the no-contained-pencil condition.
   Orbit seeds are deduplicated under the exact 25,920-element PSp(4,3) action.
   Depth <= 0,1,2 is excluded by exact positive-pencil cover search; any survivor
   is sent to an exact integer minimisation of total preimage negativity.

2. Independently of that search, all 40 pencil extensions of each of the seven
   known mass-16 exceptional orbit representatives are orbit-deduplicated.  This
   turns the earlier 280 relative-position edges into a layered extension graph
   and a thresholded *extension-lineage barcode*.  This is a combinatorial
   lineage barcode, not a persistent-homology computation.

Nothing here is a blocker theorem or a claim about tau_2.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict, deque
import hashlib
import itertools
import json
from pathlib import Path
import time

from ortools.sat.python import cp_model
import signed_pencil_sampling_witness as sp
import the_mass12_census_is_complete_and_has_one_exception as m12


def addv(a, b):
    return tuple(x + y for x, y in zip(a, b))


def act(v, g):
    out = [0] * 40
    for i, x in enumerate(v):
        out[g[i]] = x
    return tuple(out)


def orbit(v, gens):
    v = tuple(v)
    seen, q = {v}, deque([v])
    while q:
        x = q.popleft()
        for g in gens:
            y = act(x, g)
            if y not in seen:
                seen.add(y)
                q.append(y)
    return seen


def digest(v):
    return "sha256:" + hashlib.sha256(json.dumps(list(v), separators=(",", ":")).encode()).hexdigest()


def geometry_data():
    lines, thru, pencils = sp.build_geometry()
    pts, idx, sf, lines2 = m12.geometry()
    assert tuple(map(tuple, lines)) == tuple(map(tuple, lines2))
    gens, order = m12.line_action_generators(pts, idx, sf, lines2)
    assert order == 25920
    adj = [[1 if i != j and set(lines[i]) & set(lines[j]) else 0 for j in range(40)] for i in range(40)]
    return lines, thru, pencils, adj, gens, order


def depth_leq_two(e, pencils, cover):
    pos = cover(tuple(e))
    if pos is not None:
        return 0, {"positive": list(pos), "negative": []}
    for p, pen in enumerate(pencils):
        pos = cover(addv(e, pen))
        if pos is not None:
            return 1, {"positive": list(pos), "negative": [p]}
    for p in range(40):
        for q in range(p, 40):
            pos = cover(addv(addv(e, pencils[p]), pencils[q]))
            if pos is not None:
                return 2, {"positive": list(pos), "negative": [p, q]}
    return None, None


def exact_depth(e, lines, *, budget=30.0):
    model = cp_model.CpModel()
    x = [model.NewIntVar(-20, 20, f"x{p}") for p in range(40)]
    neg = []
    for p in range(40):
        d = model.NewIntVar(0, 20, f"n{p}")
        model.Add(d >= -x[p])
        neg.append(d)
    for i, L in enumerate(lines):
        model.Add(sum(x[p] for p in L) == int(e[i]))
    model.Minimize(sum(neg))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(budget)
    solver.parameters.num_workers = 8
    st = solver.Solve(model)
    if st != cp_model.OPTIMAL:
        return None
    witness = tuple(int(solver.Value(z)) for z in x)
    depth = int(round(solver.ObjectiveValue()))
    assert sum(-v for v in witness if v < 0) == depth
    assert all(sum(witness[p] for p in L) == e[i] for i, L in enumerate(lines))
    return depth, witness


def no_pencil_search(lines, thru, adj, gens, pencils, cover, *, budget, cap, depth_budget):
    model = cp_model.CpModel()
    e = [model.NewIntVar(0, 20, f"e{i}") for i in range(40)]
    model.Add(sum(e) == 20)
    for i in range(40):
        model.Add(sum(adj[i][j] * e[j] for j in range(40)) == 2 * e[i] + 5)
    zero = []
    for i in range(40):
        z = model.NewBoolVar(f"z{i}")
        model.Add(e[i] == 0).OnlyEnforceIf(z)
        model.Add(e[i] >= 1).OnlyEnforceIf(z.Not())
        zero.append(z)
    # No point pencil is componentwise <= e: every point has at least one
    # incident line with zero excess.
    for p in range(40):
        model.AddBoolOr([zero[L] for L in thru[p]])

    class Collector(cp_model.CpSolverSolutionCallback):
        def __init__(self):
            super().__init__(); self.rows = set(); self.hit_cap = False
        def on_solution_callback(self):
            self.rows.add(tuple(self.Value(v) for v in e))
            if len(self.rows) >= cap:
                self.hit_cap = True
                self.StopSearch()

    cb = Collector()
    solver = cp_model.CpSolver()
    solver.parameters.enumerate_all_solutions = True
    solver.parameters.num_workers = 1  # required for complete all-solution enumeration
    solver.parameters.max_time_in_seconds = float(budget)
    solver.parameters.random_seed = 20260909
    t0 = time.time(); st = solver.Solve(model, cb); elapsed = time.time() - t0
    complete = st == cp_model.OPTIMAL and not cb.hit_cap

    # Orbit-deduplicate every found seed even when the census is partial.
    remaining = set(cb.rows); orbit_rows = []
    while remaining:
        seed = min(remaining)
        ob = orbit(seed, gens)
        remaining.difference_update(ob)
        rep = min(ob)
        dsmall, witness = depth_leq_two(rep, pencils, cover)
        exact = None
        if dsmall is None:
            exact = exact_depth(rep, lines, budget=depth_budget)
            depth = None if exact is None else exact[0]
            x = None if exact is None else list(exact[1])
        else:
            depth = dsmall; x = None
        orbit_rows.append({
            "representative": list(rep), "representativeDigest": digest(rep),
            "orbitSize": len(ob), "depthAtMostTwo": dsmall,
            "exactDepth": depth, "smallDepthWitness": witness,
            "exactPreimage": x,
        })
    orbit_rows.sort(key=lambda r: (999 if r["exactDepth"] is None else r["exactDepth"], r["orbitSize"], r["representative"]))
    born_depth3 = [r for r in orbit_rows if r["exactDepth"] is not None and r["exactDepth"] >= 3]
    return {
        "solverStatus": solver.StatusName(st), "complete": complete,
        "hitCap": cb.hit_cap, "solutionsFound": len(cb.rows),
        "orbitSeedsFound": len(orbit_rows), "seconds": elapsed,
        "budgetSeconds": budget, "solutionCap": cap,
        "orbits": orbit_rows, "bornDepthAtLeast3": born_depth3,
        "reading": ("complete=true makes this an exhaustive census of mass-20 admissible vectors with no contained point pencil; "
                    "complete=false is only a scoped search. Any exceptional mass-20 orbit not descending from a mass-16 exception must occur here."),
    }


def known_mass16_parents(lines, thru, pencils, gens, cover):
    (e12, x12, d12), (e16new, x16new, d16new) = sp.discover(lines, thru, pencils, cover)
    assert d12 == 1 and d16new == 2
    inherited = {}
    for c, pen in enumerate(pencils):
        child = addv(e12, pen)
        if cover(child) is not None:
            continue
        one = sp.depth_at_most_one(child, pencils, cover)
        assert one is not None and one[0] == 1
        key = min(orbit(child, gens))
        inherited.setdefault(key, {"rep": key, "depth": 1, "kind": "inherited", "orbitSize": len(orbit(key, gens))})
    assert sorted(r["orbitSize"] for r in inherited.values()) == [720, 1440, 8640, 8640, 12960, 12960]
    newkey = min(orbit(e16new, gens))
    inherited[newkey] = {"rep": newkey, "depth": 2, "kind": "born-at-16", "orbitSize": len(orbit(newkey, gens))}
    assert inherited[newkey]["orbitSize"] == 1080 and len(inherited) == 7
    return min(orbit(e12, gens)), inherited


def extension_graph(lines, thru, pencils, gens, cover):
    e12key, parents = known_mass16_parents(lines, thru, pencils, gens, cover)
    nodes = {}
    edges = Counter()
    nid12 = f"m12:{digest(e12key)}"
    nodes[nid12] = {"id": nid12, "mass": 12, "depth": 1, "orbitSize": 1440, "kind": "born-at-12", "rep": list(e12key)}

    # Mass12 -> mass16 obstruction-preserving edges.
    for pen in pencils:
        child = addv(e12key, pen)
        if cover(child) is not None:
            d = 0
        else:
            one = sp.depth_at_most_one(child, pencils, cover)
            assert one is not None; d = 1
        key = min(orbit(child, gens)); oid = len(orbit(key, gens))
        nid = f"m16:{digest(key)}"
        nodes.setdefault(nid, {"id": nid, "mass": 16, "depth": d, "orbitSize": oid,
                               "kind": "repaired" if d == 0 else "inherited", "rep": list(key)})
        edges[(nid12, nid)] += 1

    # Ensure all seven exceptional parents are present, including the one new birth.
    parent_ids = {}
    for key, r in parents.items():
        nid = f"m16:{digest(key)}"; parent_ids[key] = nid
        nodes[nid] = {"id": nid, "mass": 16, "depth": r["depth"], "orbitSize": r["orbitSize"],
                      "kind": r["kind"], "rep": list(key)}

    # Complete relative-position frontier 7*40, orbit-deduplicated at mass 20.
    child_sources = defaultdict(set)
    for key, r in parents.items():
        pid = parent_ids[key]
        for pen in pencils:
            child = addv(key, pen)
            if cover(child) is not None:
                d = 0
            else:
                one = sp.depth_at_most_one(child, pencils, cover)
                if one is not None:
                    d = 1
                else:
                    assert r["depth"] == 2  # +pencil cannot raise depth
                    d = 2
            ckey = min(orbit(child, gens)); oid = len(orbit(ckey, gens))
            cid = f"m20:{digest(ckey)}"
            if cid in nodes:
                assert nodes[cid]["depth"] == d and nodes[cid]["orbitSize"] == oid
            else:
                nodes[cid] = {"id": cid, "mass": 20, "depth": d, "orbitSize": oid,
                              "kind": "descendant", "rep": list(ckey)}
            edges[(pid, cid)] += 1
            child_sources[cid].add(pid)

    # Thresholded connected-component spans. This is deliberately called an
    # extension-lineage barcode rather than persistent homology.
    bars = {}
    for threshold in (1, 2, 3):
        active = {nid for nid, r in nodes.items() if r["depth"] >= threshold}
        graph = {nid: set() for nid in active}
        for (a, b), mult in edges.items():
            if a in active and b in active:
                graph[a].add(b); graph[b].add(a)
        seen = set(); rows = []
        for s in sorted(active):
            if s in seen: continue
            comp = set([s]); q = deque([s]); seen.add(s)
            while q:
                x = q.popleft()
                for y in graph[x]:
                    if y not in seen:
                        seen.add(y); comp.add(y); q.append(y)
            masses = [nodes[x]["mass"] for x in comp]
            rows.append({"threshold": threshold, "birthMass": min(masses), "lastObservedMass": max(masses),
                         "nodeCount": len(comp), "rightCensoredAtMass20": max(masses) == 20,
                         "nodes": sorted(comp)})
        bars[str(threshold)] = sorted(rows, key=lambda r: (r["birthMass"], r["lastObservedMass"], r["nodes"]))

    depth_counts20 = Counter(r["depth"] for r in nodes.values() if r["mass"] == 20)
    return {
        "nodes": sorted(nodes.values(), key=lambda r: (r["mass"], r["depth"], r["orbitSize"], r["id"])),
        "edges": [{"source": a, "target": b, "relativePositionMultiplicity": m} for (a, b), m in sorted(edges.items())],
        "mass20UniqueDescendantOrbitCount": sum(r["mass"] == 20 for r in nodes.values()),
        "mass20UniqueDescendantDepthCounts": {str(k): v for k, v in sorted(depth_counts20.items())},
        "barcode": bars,
        "barcodeDefinition": ("For depth threshold r, keep extension-graph nodes with depth>=r and +pencil edges between adjacent masses; "
                              "each connected lineage yields [birthMass,lastObservedMass], right-censored if it reaches the observed mass-20 frontier. "
                              "This is a combinatorial extension-lineage barcode, not homological persistence."),
    }


def verify(args):
    lines, thru, pencils, adj, gens, order = geometry_data()
    cover = sp.cover_solver(lines, thru)
    ext = extension_graph(lines, thru, pencils, gens, cover)
    born = no_pencil_search(lines, thru, adj, gens, pencils, cover,
                            budget=args.budget, cap=args.cap, depth_budget=args.depth_budget)
    # Structural cross-checks independent of whether the born search completes.
    assert order == 25920
    assert sum(r["mass"] == 16 and r["depth"] > 0 for r in ext["nodes"]) == 7
    assert sum(e["relativePositionMultiplicity"] for e in ext["edges"] if e["source"].startswith("m16:")) == 280
    out = {
        "schema": "holotrade.mass20-born-depth-and-extension-barcode.v1",
        "status": "PASS",
        "groupOrder": order,
        "bornMass20Search": born,
        "extensionGraph": ext,
        "theoremBoundary": ("The seven mass-16 exceptional orbits are exhaustive prior work. Therefore an exceptional mass-20 vector containing a pencil descends from one of them; "
                            "the no-contained-pencil model is exactly where genuinely born exceptional classes must live. Search completeness is promoted only when CP-SAT returns OPTIMAL without a cap."),
        "blockerBoundary": "Load-excess profiles only; no tensor-blocker existence claim and tau_2 remains unchanged.",
    }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=float, default=120.0)
    ap.add_argument("--cap", type=int, default=10000)
    ap.add_argument("--depth-budget", type=float, default=30.0)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    out = verify(args)
    summary = {
        "status": out["status"],
        "bornSearchComplete": out["bornMass20Search"]["complete"],
        "bornSolutionsFound": out["bornMass20Search"]["solutionsFound"],
        "bornOrbitSeedsFound": out["bornMass20Search"]["orbitSeedsFound"],
        "bornDepthAtLeast3": len(out["bornMass20Search"]["bornDepthAtLeast3"]),
        "uniqueMass20DescendantOrbits": out["extensionGraph"]["mass20UniqueDescendantOrbitCount"],
        "uniqueMass20DescendantDepthCounts": out["extensionGraph"]["mass20UniqueDescendantDepthCounts"],
        "barcodeCounts": {k: len(v) for k, v in out["extensionGraph"]["barcode"].items()},
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    if args.write:
        p = Path(__file__).with_name("mass20_born_depth_and_extension_barcode_certificate.json")
        p.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
        print(f"written: {p}")


if __name__ == "__main__":
    main()
