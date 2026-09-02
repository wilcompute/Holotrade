#!/usr/bin/env python3
"""Exact local-branching repair around the best frozen K=14 near-cover.

The construction-first search froze a 14-column set missing only 111 of the
6,128 distinct exact cover constraints.  Instead of restarting CP-SAT in the
full symmetric space, solve exact Hamming neighborhoods around that near-cover:

    sum_{j in H} x_j >= 14-r,   r = 2,3,4,5,
    sum_j x_j = 14,
    A x >= 1.

The candidate universe remains all 5,294 columns and every one of the 6,128
constraints is enforced.  Hence FEASIBLE is a certified K14 witness after an
independent exact verification.  INFEASIBLE certifies that entire local
neighborhood contains no 14-cover.  UNKNOWN has no theorem consequence.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from depth5_k14_constructive_witness_search import build_instance, exact_verify

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'data/depth5_k14_constructive_witness_search.json'
OUT = ROOT / 'data/depth5_k14_near_cover_local_branching.json'
K = 14
RADII = (2, 3, 4, 5)
SECONDS = (180.0, 240.0, 360.0, 480.0)


def main():
    from ortools.sat.python import cp_model

    src = json.loads(SRC.read_text())
    assert src['valid'] and src['result'] == 'UNKNOWN'
    H = sorted(map(int, src['bestHeuristicSelection']))
    assert len(H) == K and src['bestHeuristicUncoveredRows'] == 111

    rowsets, _colrows, _reps = build_instance()
    ncols = 5294
    assert len(rowsets) == 6128

    records = []
    witness = None
    t0 = time.time()
    for radius, seconds in zip(RADII, SECONDS):
        M = cp_model.CpModel()
        x = [M.NewBoolVar(f'x{j}') for j in range(ncols)]
        for R in rowsets:
            M.AddBoolOr([x[j] for j in R])
        M.Add(sum(x) == K)
        M.Add(sum(x[j] for j in H) >= K - radius)
        for j in range(ncols):
            M.AddHint(x[j], 1 if j in H else 0)

        S = cp_model.CpSolver()
        S.parameters.max_time_in_seconds = seconds
        S.parameters.num_search_workers = 8
        S.parameters.cp_model_presolve = True
        S.parameters.symmetry_level = 3
        S.parameters.linearization_level = 2
        S.parameters.randomize_search = True
        S.parameters.random_seed = 20260902 + radius
        st = S.Solve(M)
        name = S.StatusName(st)
        rec = {
            'radius': radius,
            'minimumNearCoverColumnsRetained': K - radius,
            'status': name,
            'branches': int(S.NumBranches()),
            'conflicts': int(S.NumConflicts()),
            'wallSeconds': float(S.WallTime()),
        }
        if name in ('OPTIMAL', 'FEASIBLE'):
            w = [j for j in range(ncols) if S.Value(x[j])]
            assert len(w) == K
            assert len(set(w) & set(H)) >= K - radius
            assert exact_verify(w, rowsets)
            witness = sorted(w)
            rec['witness'] = witness
            records.append(rec)
            break
        records.append(rec)
        print(json.dumps(rec, sort_keys=True), flush=True)

    result = 'K14_FEASIBLE' if witness is not None else 'UNKNOWN'
    out = {
        'schema': 'holotrade.depth5-k14-near-cover-local-branching.v1',
        'valid': True,
        'sourceNearCover': H,
        'sourceUncoveredRows': 111,
        'records': records,
        'result': result,
        'witnessLeafOrbitIndices': witness,
        'certifiedIntervalUpdate': [14, 14] if witness is not None else [14, 22],
        'elapsedSeconds': time.time() - t0,
        'theorem': (
            'The listed fourteen columns cover all 6,128 distinct exact depth-five constraints; together with the frozen K13 infeasibility certificate this proves tau_5=14.'
            if witness is not None else
            'No certified 14-cover was found in the executed exact Hamming neighborhoods around the best frozen near-cover. INFEASIBLE neighborhood records are exact local no-go results; UNKNOWN records do not alter the global interval.'
        ),
        'boundary': 'Local branching preserves the full column universe and all exact constraints. Only an independently verified explicit 14-witness changes the global upper bound; UNKNOWN never does.',
    }
    OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'valid': True, 'result': result, 'witness': witness, 'records': records}, sort_keys=True))


if __name__ == '__main__':
    main()
