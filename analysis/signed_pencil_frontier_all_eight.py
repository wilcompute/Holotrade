#!/usr/bin/env python3
"""Execute the signed-pencil half of the eight-frontier pass.

This is deliberately scoped to exact finite W(3,3) load-excess geometry.
It does NOT turn signed sampling overhead into physical energy, blocker
feasibility, quantum magic, or hardware advantage.
"""
from __future__ import annotations

from collections import Counter, deque
from fractions import Fraction as F
import hashlib
import importlib.util
import json
from pathlib import Path

import signed_pencil_sampling_witness as sp

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "analysis" / filename)
    if spec is None or spec.loader is None:
        raise RuntimeError(filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


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


def negmass(x):
    return sum(-v for v in x if v < 0)


def addv(a, b, sign=1):
    return tuple(x + sign*y for x, y in zip(a, b))


def exact_child_depth(e, parent_x, parent_depth, pencil, pencils, cover):
    child = addv(e, pencil)
    child_x = list(parent_x)
    c = pencils.index(pencil)
    child_x[c] += 1
    child_x = tuple(child_x)
    assert tuple(sum(child_x[p] for p in L) for L in sp.build_geometry()[0]) == child
    upper = negmass(child_x)
    assert upper <= parent_depth
    if cover(child) is not None:
        return child, child_x, 0
    one = sp.depth_at_most_one(child, pencils, cover)
    if one is not None:
        return child, child_x, 1
    # A carried parent witness proves the upper bound. Since depth 0 and 1
    # were excluded exhaustively, any remaining child of a depth-2 parent is 2.
    assert upper == parent_depth == 2
    return child, child_x, 2


def kernel_gauge_generators(lines):
    kg = load_module("octet_kernel_frontier", "the_kernel_is_spanned_by_octet_differences.py")
    pts, sf, iso, hyp, perp = kg.geometry()
    assert tuple(tuple(L) for L in iso) == tuple(tuple(L) for L in lines)
    octets = {frozenset((frozenset(L), frozenset(perp(L)))) for L in hyp}
    rows = []
    for pair in sorted(octets, key=lambda z: sorted(sorted(x) for x in z)):
        A, B = sorted(pair, key=lambda z: tuple(sorted(z)))
        g = [0] * 40
        for p in A:
            g[p] += 1
        for p in B:
            g[p] -= 1
        g = tuple(g)
        assert all(sum(g[p] for p in L) == 0 for L in lines)
        rows.append(g)
    assert len(rows) == 45
    return tuple(rows)


def perturb_and_decode(x, gauges, target):
    # First drive a certified optimum away from the nonnegative cone while
    # staying in the exact kernel coset.
    cur = tuple(x)
    for _ in range(6):
        moves = [addv(cur, g, s) for g in gauges for s in (1, -1)]
        nxt = max(moves, key=lambda z: (negmass(z), z))
        cur = nxt
    start = cur

    # Deterministic one-move descent, with a two-move escape from local minima.
    moves = tuple((g, s) for g in gauges for s in (1, -1))
    steps = 0
    while negmass(cur) > target and steps < 80:
        n0 = negmass(cur)
        best = cur
        for g, s in moves:
            y = addv(cur, g, s)
            if negmass(y) < negmass(best):
                best = y
        if negmass(best) < n0:
            cur = best
            steps += 1
            continue
        pair_best = cur
        for g, s in moves:
            y = addv(cur, g, s)
            for h, t in moves:
                z = addv(y, h, t)
                if negmass(z) < negmass(pair_best):
                    pair_best = z
        if negmass(pair_best) >= n0:
            break
        cur = pair_best
        steps += 2
    assert negmass(cur) >= target
    return dict(start_negative_mass=negmass(start), final_negative_mass=negmass(cur),
                exact_depth=target, reached_exact_depth=negmass(cur) == target,
                gauge_moves=steps)


def main():
    lines, thru, pencils = sp.build_geometry()
    cover = sp.cover_solver(lines, thru)
    (e12, x12, d12), (e16new, x16new, d16new) = sp.discover(lines, thru, pencils, cover)
    assert d12 == 1 and d16new == 2

    m12 = load_module("mass12_frontier", "the_mass12_census_is_complete_and_has_one_exception.py")
    pts, idx, sf, group_lines = m12.geometry()
    assert tuple(tuple(L) for L in group_lines) == tuple(tuple(L) for L in lines)
    gens, gorder = m12.line_action_generators(pts, idx, sf, group_lines)
    assert gorder == 25920
    pencil_set = set(pencils)
    # This executable check is what licenses the 40 relative-position seeds:
    # every generator permutes the point-pencil family.
    assert all(act(p, g) in pencil_set for g in gens for p in pencils)

    # Mass-12 orbit and its +pencil descendants.  A fixed representative plus
    # all 40 pencils is complete up to G: g(e+p)=g(e)+g(p).
    o12 = orbit(e12, gens)
    assert len(o12) == 1440
    orbit_owner = {}
    inherited = {}
    local_repair = 0
    local_preserve = 0
    for c, pen in enumerate(pencils):
        child = addv(e12, pen)
        x = list(x12); x[c] += 1; x = tuple(x)
        if cover(child) is not None:
            local_repair += 1
            continue
        assert sp.depth_at_most_one(child, pencils, cover)[0] == 1
        local_preserve += 1
        if child in orbit_owner:
            key = orbit_owner[child]
        else:
            ob = orbit(child, gens)
            key = min(ob)
            for z in ob:
                orbit_owner[z] = key
            inherited.setdefault(key, dict(excess=child, x=x, orbit=len(ob), source_pencil=c))
    assert local_repair + local_preserve == 40
    assert len(inherited) == 6
    assert sorted(r["orbit"] for r in inherited.values()) == [720, 1440, 8640, 8640, 12960, 12960]

    new_orbit = orbit(e16new, gens)
    assert len(new_orbit) == 1080
    assert min(new_orbit) not in inherited

    parents = []
    for r in inherited.values():
        parents.append(dict(kind="inherited", depth=1, **r))
    parents.append(dict(kind="new", depth=2, excess=e16new, x=x16new,
                        orbit=len(new_orbit), source_pencil=None))
    parents.sort(key=lambda r: (r["orbit"], r["kind"], r["excess"]))

    # Frontier 1 + frontier 8: exact rational primal/dual l1 certificates for
    # all seven exceptional mass-16 classes and exact signed-sampling factors.
    exact_rows = []
    for r in parents:
        a = sp.audit(r["excess"], r["x"], r["depth"], lines, thru, pencils, cover)
        k = a["mass"] // 4
        gamma = F(a["fractional"]["l1"])
        delta = (gamma - k) / 2
        amp = gamma / k
        exact_rows.append(dict(
            kind=r["kind"], orbit_size=r["orbit"], representative_digest=digest(r["excess"]),
            integer_depth=r["depth"], gamma_real=str(gamma), delta_real=str(delta),
            delta_real_equals_integer_depth=(delta == r["depth"]),
            signed_sampling_amplification=str(amp), second_moment_factor=str(amp*amp),
            certificate=a))
    all_equal = all(r["delta_real_equals_integer_depth"] for r in exact_rows)

    # Frontier 3: composition calculus.  The general inequalities are proved by
    # adding feasible preimages; here every concrete mass12->16 edge is also
    # checked against the exact depth classification above.
    assert all(F(r["gamma_real"]) in (6, 8) for r in exact_rows)
    composition = dict(
        triangle="gamma_R(e1+e2) <= gamma_R(e1)+gamma_R(e2), by x1+x2 feasibility and the l1 triangle inequality",
        delta_subadditive="when masses add, delta_R(e1+e2) <= delta_R(e1)+delta_R(e2)",
        positive_pencil="gamma_R(e+p)<=gamma_R(e)+1, hence delta_R(e+p)<=delta_R(e)",
        integer_positive_pencil="d(e+p)<=d(e), by x -> x+1_p",
        fixed_mass12_representative_edges=40,
        fixed_rep_depth_1_to_0_repairs=local_repair,
        fixed_rep_depth_1_to_1_preservations=local_preserve,
        note="The 40 fixed-representative edges are a complete set of relative pencil positions; global unique-vector repair counts belong to e62261f and are not re-counted here.")

    # Frontier 5 + outside-box 6: complete one-pencil mass20 descendant probe
    # up to G, using 40 relative positions for each of the seven parent orbits.
    mass20 = []
    depth_hist = Counter()
    parent_summaries = []
    for i, r in enumerate(parents):
        ph = Counter()
        witness_bound_ok = True
        for c, pen in enumerate(pencils):
            child, child_x, d = exact_child_depth(r["excess"], r["x"], r["depth"], pen, pencils, cover)
            # Explicit l1 witness gives the real-positive-pencil upper bound too.
            witness_bound_ok &= (sum(map(abs, child_x)) <= sum(map(abs, r["x"])) + 1)
            ph[d] += 1; depth_hist[d] += 1
            mass20.append(dict(parent=i, parent_orbit=r["orbit"], parent_depth=r["depth"],
                               pencil=c, child_depth=d, child_digest=digest(child)))
        assert witness_bound_ok and sum(ph.values()) == 40
        parent_summaries.append(dict(parent=i, orbit_size=r["orbit"], depth=r["depth"],
                                     child_depth_counts={str(k): v for k, v in sorted(ph.items())}))
    assert len(mass20) == 280
    no_depth3 = not any(e["child_depth"] >= 3 for e in mass20)
    assert no_depth3

    # Outside-box 7: use the 45 saturated octet kernel generators as gauge
    # moves and see whether a local decoder can return deliberately perturbed
    # preimages to the exact known negativity depth.
    gauges = kernel_gauge_generators(lines)
    gauge_rows = []
    for r in parents:
        dec = perturb_and_decode(r["x"], gauges, r["depth"])
        dec.update(orbit_size=r["orbit"], kind=r["kind"])
        gauge_rows.append(dec)
    gauge_successes = sum(r["reached_exact_depth"] for r in gauge_rows)

    result = dict(
        schema="holotrade.signed-pencil-frontier-all-eight.v1",
        status="PASS",
        group_order=gorder,
        mass12_exception_orbit_size=len(o12),
        mass16_exceptional_orbit_sizes=sorted(r["orbit"] for r in parents),
        real_l1=dict(all_seven_certified=len(exact_rows) == 7,
                     delta_real_equals_integer_depth_on_all_seven=all_equal,
                     rows=exact_rows),
        composition=composition,
        mass20_descendant_frontier=dict(
            completeness="For each mass16 orbit representative, all 40 pencils are tested; because the group permutes the pencil family, these cover every one-pencil descendant up to group action.",
            relative_position_edges=len(mass20),
            exact_integer_depth_counts={str(k): v for k, v in sorted(depth_hist.items())},
            any_depth_three=no_depth3 is False,
            no_depth_three=no_depth3,
            parents=parent_summaries,
            edges=mass20),
        extension_graph=dict(
            law="depth (integer and real) cannot increase along +pencil edges",
            interpretation="Inherited mass growth can preserve or dilute negativity; a higher-depth class cannot be born as a +pencil descendant of a shallower parent.",
            mass12_local_edges=dict(repair=local_repair, preserve=local_preserve),
            mass16_to_mass20_parent_summaries=parent_summaries),
        kernel_gauge_decoder=dict(generators=45, exact_lattice_owner="461f57d", successes=gauge_successes,
                                  total=len(gauge_rows), rows=gauge_rows,
                                  boundary="Heuristic one/two-move decoder benchmark; failure would be a local-minimum result, not a failure of lattice generation."),
        signed_sampling_resource=dict(
            theorem="For q_p=|x_p|/gamma and |f|<=1, the normalized signed estimator has |Z|<=A=gamma/k and E[Z^2]<=A^2.",
            factors=[dict(orbit_size=r["orbit_size"], depth=r["integer_depth"],
                          A=r["signed_sampling_amplification"], A2=r["second_moment_factor"])
                     for r in exact_rows],
            boundary="Estimator/sampling amplification only; not physical energy, blocker feasibility, or generic quantum magic."),
        boundary="Exact finite load-excess and signed-representation statements. Mass20 is the complete one-pencil descendant frontier of the seven known mass16 exceptional orbits, not a complete census of all admissible mass20 excesses."
    )
    out = Path(__file__).with_name("signed_pencil_frontier_all_eight_certificate.json")
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(dict(
        status=result["status"],
        all_seven_delta_real_equals_d=all_equal,
        mass16_orbits=result["mass16_exceptional_orbit_sizes"],
        mass12_edge_depths={"repair": local_repair, "preserve": local_preserve},
        mass20_depth_counts=result["mass20_descendant_frontier"]["exact_integer_depth_counts"],
        mass20_depth3=not no_depth3,
        gauge_decoder=f"{gauge_successes}/{len(gauge_rows)}",
        sampling_factors=result["signed_sampling_resource"]["factors"],
        certificate=str(out)), indent=2))


if __name__ == "__main__":
    main()
