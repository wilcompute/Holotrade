#!/usr/bin/env python3
"""Classify centre-fibre geometry and omitted-pencil defect pricing.

The first version of this variation audit assumed that every repeated fibre of
minimum-shadow centres is contained in a unique W33 pencil.  That was true for
the deterministic order-6 and order-12 witnesses, but a later order-5 solver
witness exposed a repeated fibre with no common pencil point.  This version
turns that failed assertion into evidence.

For deterministic symmetry orders 6, 12, and 5 it records on both axes:
  * the complete shadow-size / defect budget F,D with F+D=4r;
  * centre multiplicities of minimum (size-11) shadows;
  * whether each repeated centre fibre is concurrent;
  * disjoint line pairs inside nonconcurrent fibres;
  * omitted-pencil pricing only where a unique concurrency pencil exists.

This separates two statements that must not be conflated:
  (A) a global all-defect concurrency law -- falsified by counterexample here;
  (B) the r=1 clean-core closure theorem after deleting the dirty pencils --
      untouched by this high-defect counterexample.
"""
from __future__ import annotations

import collections
import itertools
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/defect_omitted_pencil_cost_variation.json'
Q = 3
N = 40


def nm(v):
    i = next(k for k, x in enumerate(v) if x % Q)
    z = pow(v[i] % Q, -1, Q)
    return tuple((z * x) % Q for x in v)


def form(u, v):
    return (u[0] * v[1] - u[1] * v[0] + u[2] * v[3] - u[3] * v[2]) % Q


def porder(g):
    I = tuple(range(N))
    h = g
    o = 1
    while h != I:
        h = tuple(g[i] for i in h)
        o += 1
    return o


def main():
    from ortools.sat.python import cp_model

    pts = sorted({nm(v) for v in itertools.product(range(Q), repeat=4) if any(v)})
    idx = {v: i for i, v in enumerate(pts)}
    lines = set()
    for a, b in itertools.combinations(range(N), 2):
        if form(pts[a], pts[b]):
            continue
        S = set()
        for x, y in itertools.product(range(Q), repeat=2):
            if x == y == 0:
                continue
            S.add(idx[nm(tuple((x * pts[a][k] + y * pts[b][k]) % Q for k in range(4)))])
        if len(S) == 4:
            lines.add(tuple(sorted(S)))
    lines = sorted(lines)
    LS = [set(L) for L in lines]
    assert len(lines) == 40
    thru = [[li for li, L in enumerate(lines) if p in L] for p in range(N)]
    assert {len(x) for x in thru} == {4}

    e = [tuple(1 if k == i else 0 for k in range(4)) for i in range(4)]

    def is_sp(A):
        for i, j in itertools.combinations(range(4), 2):
            u = tuple(sum(A[r][k] * e[i][k] for k in range(4)) % Q for r in range(4))
            v = tuple(sum(A[r][k] * e[j][k] for k in range(4)) % Q for r in range(4))
            if form(u, v) != form(e[i], e[j]):
                return False
        return True

    def act(A, v):
        return nm(tuple(sum(A[i][k] * v[k] for k in range(4)) % Q for i in range(4)))

    rng = random.Random(3)
    candidates = {}
    tries = 0
    while len(candidates) < 3 and tries < 200000:
        tries += 1
        A = tuple(tuple(rng.randrange(Q) for _ in range(4)) for _ in range(4))
        if not is_sp(A):
            continue
        g = tuple(idx[act(A, pts[p])] for p in range(N))
        o = porder(g)
        if o in (5, 6, 12) and o not in candidates:
            candidates[o] = g
    assert set(candidates) == {5, 6, 12}

    def centre(S):
        dbl = [li for li, L in enumerate(LS) if len(S & L) == 2]
        for p in range(N):
            if set(dbl) == set(thru[p]):
                return p
        return None

    def make_witness(g):
        mark = [False] * (N * N)
        orb = []
        for v in range(N * N):
            if mark[v]:
                continue
            cur = v
            cyc = []
            while not mark[cur]:
                mark[cur] = True
                cyc.append(cur)
                cur = g[cur // N] * N + g[cur % N]
            orb.append(cyc)
        inorb = [0] * (N * N)
        for i, C in enumerate(orb):
            for v in C:
                inorb[v] = i
        m = cp_model.CpModel()
        y = [m.NewBoolVar(f'y{i}') for i in range(len(orb))]
        for L in lines:
            for M in lines:
                m.AddBoolOr([y[inorb[p * N + q]] for p in L for q in M])
        m.Minimize(sum(len(C) * y[i] for i, C in enumerate(orb)))
        s = cp_model.CpSolver()
        s.parameters.max_time_in_seconds = 240
        s.parameters.num_search_workers = 8
        s.parameters.random_seed = 3
        st = s.Solve(m)
        name = s.StatusName(st)
        assert name in ('OPTIMAL', 'FEASIBLE'), name
        X = {(v // N, v % N) for i, C in enumerate(orb) if s.Value(y[i]) for v in C}
        assert all(any((p, q) in X for p in L for q in M) for L in lines for M in lines)
        return X, name

    def analyse_axis(X, axis):
        sh = []
        raw = []
        if axis == 'row':
            fibres = [{q for a, q in X if a == p} for p in range(N)]
        else:
            fibres = [{p for p, b in X if b == q} for q in range(N)]
        for L in lines:
            S = set().union(*(fibres[p] for p in L))
            sh.append(S)
            raw.append(sum(len(fibres[p]) for p in L))

        by = collections.defaultdict(list)
        for li, S in enumerate(sh):
            if len(S) == 11:
                c = centre(S)
                assert c is not None
                by[c].append(li)

        oversized = {li for li, S in enumerate(sh) if len(S) > 11}
        F = sum(len(S) - 11 for S in sh)
        D = sum(a - len(S) for a, S in zip(raw, sh))
        r = len(X) - 110
        assert F + D == 4 * r

        repeated = []
        all_omitted = []
        nonconcurrent = []
        for c, fibre in sorted(by.items()):
            if len(fibre) < 2:
                continue
            ps = [p for p in range(N) if set(fibre) <= set(thru[p])]
            pair_data = []
            for a, b in itertools.combinations(fibre, 2):
                inter = sorted(LS[a] & LS[b])
                pair_data.append({'lines': [a, b], 'intersectionPoints': inter, 'disjoint': not inter})
            entry = {
                'blockerCentre': c,
                'lines': list(fibre),
                'multiplicity': len(fibre),
                'commonPencilPoints': ps,
                'disjointPairCount': sum(x['disjoint'] for x in pair_data),
                'pairGeometry': pair_data,
            }
            if len(ps) == 1:
                p = ps[0]
                omitted = sorted(set(thru[p]) - set(fibre))
                all_omitted.extend(omitted)
                entry.update({
                    'geometry': 'concurrent',
                    'concurrencyPoint': p,
                    'omittedLines': omitted,
                    'allOmittedOversized': all(x in oversized for x in omitted),
                })
            else:
                entry.update({'geometry': 'nonconcurrent', 'concurrencyPoint': None, 'omittedLines': []})
                nonconcurrent.append(entry)
            repeated.append(entry)

        omset = set(all_omitted)
        concurrent = [x for x in repeated if x['geometry'] == 'concurrent']
        return {
            'shadowSizes': dict(sorted(collections.Counter(map(len, sh)).items())),
            'F': F,
            'D': D,
            'FplusD': F + D,
            'fourR': 4 * r,
            'minimumShadows': sum(len(S) == 11 for S in sh),
            'oversizedLines': sorted(oversized),
            'centreMultiplicityProfile': dict(sorted(collections.Counter(map(len, by.values())).items())),
            'repeatedFibres': repeated,
            'concurrentRepeatedFibres': len(concurrent),
            'nonconcurrentRepeatedFibres': len(nonconcurrent),
            'nonconcurrentExamples': nonconcurrent,
            'allRepeatedFibresConcurrent': len(nonconcurrent) == 0,
            'omittedOccurrencesOnConcurrentFibres': len(all_omitted),
            'distinctOmittedLines': len(omset),
            'allConcurrentOmittedOccurrencesAreOversized': all(x in oversized for x in all_omitted),
            'concurrentOmittedSetContainedInOversized': omset <= oversized,
            'concurrentOmittedSetEqualsOversized': omset == oversized,
            'oversizedNotExplainedByConcurrentOmissions': sorted(oversized - omset),
        }

    records = []
    for o in (6, 12, 5):
        X, status = make_witness(candidates[o])
        rec = {
            'symmetryOrder': o,
            'leaves': len(X),
            'r': len(X) - 110,
            'solverStatus': status,
            'row': analyse_axis(X, 'row'),
            'col': analyse_axis(X, 'col'),
        }
        records.append(rec)
        print(json.dumps({
            'order': o,
            'leaves': len(X),
            'r': len(X) - 110,
            'rowConcurrent': rec['row']['allRepeatedFibresConcurrent'],
            'colConcurrent': rec['col']['allRepeatedFibresConcurrent'],
            'rowF': rec['row']['F'], 'rowD': rec['row']['D'],
            'colF': rec['col']['F'], 'colD': rec['col']['D'],
            'rowNonconcurrent': rec['row']['nonconcurrentRepeatedFibres'],
            'colNonconcurrent': rec['col']['nonconcurrentRepeatedFibres'],
        }, sort_keys=True))

    counterexamples = []
    for rec in records:
        for axis in ('row', 'col'):
            for ex in rec[axis]['nonconcurrentExamples']:
                counterexamples.append({
                    'symmetryOrder': rec['symmetryOrder'],
                    'leaves': rec['leaves'],
                    'r': rec['r'],
                    'axis': axis,
                    'F': rec[axis]['F'],
                    'D': rec[axis]['D'],
                    'FplusD': rec[axis]['FplusD'],
                    **ex,
                })

    out = {
        'schema': 'holotrade.defect-omitted-pencil-cost-variation.v2',
        'valid': True,
        'witnesses': records,
        'globalConcurrencyLawSurvivesSample': len(counterexamples) == 0,
        'globalConcurrencyCounterexamples': counterexamples,
        'minimumObservedRWithNonconcurrentFibre': min((x['r'] for x in counterexamples), default=None),
        'minimumObservedDefectBudgetFplusDWithNonconcurrentFibre': min((x['FplusD'] for x in counterexamples), default=None),
        'reading': (
            'A nonconcurrent repeated centre fibre is a decisive counterexample to the previously sampled global concurrency law. '
            'Its F+D=4r value is the exact defect budget of that witness, not a lower bound on the cost of nonconcurrency. '
            'The r=1 clean-core theorem after deleting dirty pencils is a different statement and is not contradicted by a high-defect witness.'
        ),
        'boundary': (
            'These are symmetry-restricted upper-bound witnesses. A counterexample falsifies the global law, but the smallest sampled r is not a theorem about the minimum defect required. tau_2 remains in [111,115].'
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
    print(json.dumps({
        'valid': True,
        'counterexamples': len(counterexamples),
        'minObservedR': out['minimumObservedRWithNonconcurrentFibre'],
        'minObservedBudget': out['minimumObservedDefectBudgetFplusDWithNonconcurrentFibre'],
    }, sort_keys=True))


if __name__ == '__main__':
    main()
