#!/usr/bin/env python3
"""Iterated multi-dual kernelization for any unresolved exact depth-five K=14 branches.

This is a theorem-safe adaptation of dual-path fixing (Yamagishi--Fampa--Lee,
SEA 2026, DOI 10.4230/LIPIcs.SEA.2026.28) to the exact W33 set-cover frontier.
The paper's literal implementation harvests dual-simplex iterates.  SciPy/HiGHS
does not expose that iterate stream here, so we do NOT claim to reproduce that
algorithm.  Instead we exploit the same theorem: *any* dual-feasible point may
fix a set-cover variable.

For each unresolved S5-normalized K14 branch (first column j already selected):

  residual integer cover budget = 13 columns.

For any exactly verified dual-feasible y of the current reduced residual model,
a candidate column k is impossible in a <=13 residual cover whenever

    1 + y^T(1-A_k) > 13,

or equivalently

    sum(y) - load_y(k) > 12.

We generate a small deterministic cloud of dual-feasible points per round:
  * the max-sum dual;
  * near-optimal duals maximizing several independent row directions while
    constrained to retain essentially the same dual lower bound.
Every floating point is rounded DOWN to denominator 10^7 and reverified by
integer arithmetic before use.  All columns fixed by any point are deleted,
dominated/duplicate rows are eliminated exactly, and the process repeats.  No
per-column strong-fixing LP is solved.

After kernelization, a residual CP-SAT check is used only as an exact integer
closure attempt.  It never upgrades a theorem from UNKNOWN unless it returns
INFEASIBLE or an explicit verified 14-cover.
"""
from __future__ import annotations

import collections
import json
import math
import time
from pathlib import Path

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix, vstack

import depth5_induced_subgroup_cuts as old
import depth5_coordinate_s5_automorphism as s5

ROOT = Path(__file__).resolve().parents[1]
K13 = ROOT / 'data/depth5_k13_strong_dual_fixing.json'
K14 = ROOT / 'data/depth5_k14_recycled_dual_pair_kernel.json'
OUT = ROOT / 'data/depth5_k14_iterated_dual_path_kernel.json'
D = 10_000_000
TARGET_RESIDUAL_UB = 13
FIX_THRESHOLD = 12 * D
MAX_ROUNDS = 3
DIRECTION_COUNT = 5


def make_orbits(gens, n):
    G = s5.closure(gens, n)
    assert len(G) == 120
    unseen = set(range(n)); out = []
    while unseen:
        j = min(unseen); O = sorted({g[j] for g in G}); unseen.difference_update(O); out.append(O)
    assert len(out) == 94
    return G, out


def exact_dual(R, yf):
    """Round down and exactly reverify R.T y <= 1 on denominator D."""
    yint = np.floor(np.maximum(np.asarray(yf, dtype=float), 0.0) * D).astype(np.int64)
    loads = np.asarray(R.T.dot(yint), dtype=np.int64).reshape(-1)
    mx = int(loads.max()) if len(loads) else 0
    if mx > D:
        yint = (yint * (D - 1) // mx).astype(np.int64)
        loads = np.asarray(R.T.dot(yint), dtype=np.int64).reshape(-1)
        mx = int(loads.max()) if len(loads) else 0
    assert (int(yint.min()) if len(yint) else 0) >= 0
    assert mx <= D
    return yint, loads, int(yint.sum()), mx


def minimal_rows(row_ids, rowsets, active_cols):
    """Exact duplicate + dominated-row elimination on projected supports."""
    active = set(active_cols)
    uniq = {}
    empty = []
    for r in row_ids:
        S = frozenset(rowsets[r] & active)
        if not S:
            empty.append(r)
        else:
            uniq.setdefault(S, r)
    if empty:
        return [], empty, {'before': len(row_ids), 'distinct': len(uniq), 'afterDominance': 0}
    ordered = sorted(uniq.items(), key=lambda kv: (len(kv[0]), tuple(sorted(kv[0]))))
    kept = []
    kept_sets = []
    for S, r in ordered:
        # A smaller support row dominates a larger support row.
        if any(T.issubset(S) for T in kept_sets):
            continue
        kept.append(r); kept_sets.append(S)
    return kept, [], {'before': len(row_ids), 'distinct': len(uniq), 'afterDominance': len(kept)}


def direction_vector(row_ids, rowsets, active_cols, t):
    active = set(active_cols)
    deg = np.array([len(rowsets[r] & active) for r in row_ids], dtype=float)
    if t == 0:
        # Emphasize currently hard / low-degree rows.
        inv = 1.0 / np.maximum(deg, 1.0)
        return inv / max(float(inv.max()), 1.0)
    if t == 1:
        # Complementary high-degree direction.
        return deg / max(float(deg.max()), 1.0)
    # Three deterministic hash directions in [0,1].
    prime = 104729
    a = [7919, 15401, 31337][t - 2]
    b = [17, 101, 1009][t - 2]
    return np.array([((a * int(r) + b) % prime) / (prime - 1) for r in row_ids], dtype=float)


def solve_cloud(R, row_ids, rowsets, active_cols, round_index):
    """Return exact feasible dual points: max-sum plus near-optimal directions."""
    nrow = R.shape[0]
    if nrow == 0:
        return []
    one = np.ones(nrow, dtype=float)
    base = linprog(-one, A_ub=R.T, b_ub=np.ones(R.shape[1]), bounds=(0, None), method='highs')
    assert base.success
    y0, loads0, score0, mx0 = exact_dual(R, base.x)
    points = [{
        'kind': 'max-sum', 'floatingObjective': float(-base.fun), 'scoreNumerator': score0,
        'score': score0 / D, 'maxColumnLoadNumerator': mx0, 'y': y0, 'loads': loads0,
    }]

    # Keep alternate points on a near-optimal slice.  The exact max-sum point
    # itself proves feasibility of a threshold slightly below its rounded score.
    threshold = max(0.0, score0 / D - 2.0 / D)
    near_row = csr_matrix((-np.ones(nrow), (np.zeros(nrow, dtype=int), np.arange(nrow))), shape=(1, nrow))
    Aub = vstack([R.T, near_row], format='csr')
    bub = np.concatenate([np.ones(R.shape[1]), np.array([-threshold])])
    for t in range(DIRECTION_COUNT):
        d = direction_vector(row_ids, rowsets, active_cols, t)
        # Tiny deterministic tie breaker keeps runs reproducible.
        objective = d + (round_index + 1) * 1e-9 * np.arange(nrow)
        lp = linprog(-objective, A_ub=Aub, b_ub=bub, bounds=(0, None), method='highs')
        if not lp.success:
            continue
        yi, loads, score, mx = exact_dual(R, lp.x)
        points.append({
            'kind': f'near-opt-direction-{t}', 'floatingObjective': float(-lp.fun),
            'scoreNumerator': score, 'score': score / D, 'maxColumnLoadNumerator': mx,
            'y': yi, 'loads': loads,
        })
    return points


def main():
    from ortools.sat.python import cp_model

    if not K14.exists():
        raise FileNotFoundError('K14 recycled-dual certificate must be frozen before this pass')
    k13 = json.loads(K13.read_text()); k14 = json.loads(K14.read_text())
    assert k13['valid'] and k13['result'] == 'K13_INFEASIBLE'
    assert k14['valid'] and k14['fixedOrbitBranchCount'] == 88

    # If the preceding exact attack already decided K14, record that DPF has no
    # unresolved branch to process rather than pretending to improve a closed case.
    if k14['result'] in ('K14_FEASIBLE', 'K14_INFEASIBLE'):
        out = {
            'schema': 'holotrade.depth5-k14-iterated-dual-path-kernel.v1', 'valid': True,
            'inputResult': k14['result'], 'result': k14['result'], 'unresolvedBranchesProcessed': 0,
            'status': 'SKIPPED_ALREADY_DECIDED', 'certifiedIntervalUpdate': k14['certifiedIntervalUpdate'],
            'theorem': 'The preceding exact K14 branch certificate already decided the frontier; no unresolved K14 branch remains for dual-path kernelization.',
            'methodBoundary': 'No claim about dual-path performance is made when the input frontier is already closed.',
        }
        OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
        print(json.dumps(out, sort_keys=True)); return

    assert k14['result'] == 'UNKNOWN'

    pts, _idx, iso, _supports, _charts, _edge = old.geometry()
    leaf_id, reps = s5.build_orbit_machine(pts, iso)
    _leaf, A = old.full_orbit_machine(pts, iso); assert A.shape == (6129, 5294)
    raw = [frozenset(map(int, A.indices[A.indptr[r]:A.indptr[r+1]])) for r in range(A.shape[0])]
    rowsets = sorted(set(raw), key=lambda S: (len(S), tuple(sorted(S))))
    assert len(rowsets) == 6128
    rr=[]; cc=[]
    for i,S in enumerate(rowsets):
        for j in S: rr.append(i); cc.append(j)
    B = csr_matrix((np.ones(len(rr),dtype=np.int8),(rr,cc)),shape=(6128,5294),dtype=np.int64)

    gens=[]
    for q in range(4):
        g=[]
        for r in reps:
            z=list(r); z[q],z[q+1]=z[q+1],z[q]; g.append(leaf_id(tuple(z)))
        gens.append(tuple(g))
    _G, orbits = make_orbits(gens, 5294)

    pair_by_oi = {int(r['orbitIndex']): r for r in k14['pairKernelRecords']}
    prev_solver = {int(r['orbitIndex']): r for r in k14.get('solverRecords', [])}
    fixed_ois = [int(x) for x in k13['strongFixing']['fixedOrbitIndices']]
    cert_by_oi = {int(c['orbitIndex']): c for c in k13['exactDualCertificates']}

    # Branches already closed by empty pair-kernel rows or exact CP-SAT INFEASIBLE.
    closed = set()
    for oi in fixed_ois:
        if pair_by_oi[oi]['emptyRowCount'] > 0:
            closed.add(oi)
        elif prev_solver.get(oi,{}).get('status') == 'INFEASIBLE':
            closed.add(oi)
    unresolved = [oi for oi in fixed_ois if oi not in closed]

    records=[]; witnessed=None; newly_closed=set(); solver_records=[]
    global_deadline = time.time() + 1500.0

    for oi in unresolved:
        if time.time() >= global_deadline:
            break
        j = orbits[oi][0]
        assert pair_by_oi[oi]['representativeColumn'] == j
        active_cols = set(range(5294)); active_cols.remove(j)
        row_ids = [r for r,S in enumerate(rowsets) if j not in S]
        branch = {'orbitIndex': oi, 'representativeColumn': j, 'rounds': [],
                  'initialColumns': len(active_cols), 'initialRows': len(row_ids)}

        # Seed round zero with every theorem-safe fixing from the frozen dual.
        cert = cert_by_oi[oi]
        y = np.zeros(6128,dtype=np.int64)
        for r,w in cert['weights']: y[int(r)] = int(w)
        score = int(y.sum()); loads_all = np.asarray(B.T.dot(y),dtype=np.int64).reshape(-1)
        seed_fixed = {k for k in active_cols if score - int(loads_all[k]) > FIX_THRESHOLD}
        active_cols -= seed_fixed
        row_ids, empty, dre = minimal_rows(row_ids, rowsets, active_cols)
        branch['seed'] = {'score': score/D, 'fixedColumns': len(seed_fixed), 'DRE': dre,
                          'emptyRows': empty[:32], 'emptyRowCount': len(empty)}
        if empty:
            branch['result']='INFEASIBLE_EMPTY_ROW_AFTER_SEED'; newly_closed.add(oi); records.append(branch); continue

        for rnd in range(MAX_ROUNDS):
            cols = sorted(active_cols)
            R = B[row_ids,:][:,cols].tocsr()
            points = solve_cloud(R, row_ids, rowsets, cols, rnd)
            fixed_this=set(); point_meta=[]
            for p in points:
                loads = p.pop('loads'); p.pop('y')
                local_fixed = [cols[q] for q in range(len(cols)) if p['scoreNumerator'] - int(loads[q]) > FIX_THRESHOLD]
                fixed_this.update(local_fixed)
                point_meta.append({**p, 'fixedColumnsByPoint': len(local_fixed)})
            new_fixed = fixed_this & active_cols
            active_cols -= new_fixed
            before_rows=len(row_ids)
            row_ids, empty, dre = minimal_rows(row_ids, rowsets, active_cols)
            branch['rounds'].append({'round':rnd,'dualPoints':point_meta,'newFixedColumns':len(new_fixed),
                                     'remainingColumns':len(active_cols),'rowsBeforeDRE':before_rows,
                                     'DRE':dre,'emptyRows':empty[:32],'emptyRowCount':len(empty)})
            if empty:
                branch['result']='INFEASIBLE_EMPTY_ROW_AFTER_DPF'; newly_closed.add(oi); break
            if not new_fixed:
                branch['result']='KERNEL_STABLE'; break
        if oi in newly_closed:
            records.append(branch); continue

        # Exact residual integer closure attempt on the DPF+DRE kernel.
        cols=sorted(active_cols); pos={k:q for q,k in enumerate(cols)}
        supports=[]; impossible=False
        for r in row_ids:
            S=frozenset(pos[k] for k in rowsets[r] if k in pos)
            if not S: impossible=True; break
            supports.append(S)
        if impossible:
            branch['result']='INFEASIBLE_EMPTY_ROW_PRE_SAT'; newly_closed.add(oi); records.append(branch); continue
        uniq=sorted(set(supports),key=lambda S:(len(S),tuple(sorted(S))))
        minimal=[];bits=[]
        for S in uniq:
            b=0
            for q in S:b|=1<<q
            if any(tb & ~b == 0 for tb in bits):continue
            minimal.append(S);bits.append(b)
        remain=max(1.0,global_deadline-time.time())
        model=cp_model.CpModel();x=[model.NewBoolVar(f'x{q}') for q in range(len(cols))]
        for S in minimal:model.AddBoolOr([x[q] for q in S])
        model.Add(sum(x)==13)
        solver=cp_model.CpSolver();solver.parameters.max_time_in_seconds=min(120.0,remain)
        solver.parameters.num_search_workers=8;solver.parameters.symmetry_level=3
        solver.parameters.cp_model_presolve=True;solver.parameters.linearization_level=2
        t0=time.time();st=solver.Solve(model);name=solver.StatusName(st)
        sr={'orbitIndex':oi,'status':name,'remainingColumns':len(cols),'minimalRows':len(minimal),
            'elapsedSeconds':time.time()-t0,'branches':int(solver.NumBranches()),'conflicts':int(solver.NumConflicts())}
        solver_records.append(sr);branch['solver']=sr
        if name=='INFEASIBLE':
            branch['result']='INFEASIBLE_CP_SAT';newly_closed.add(oi)
        elif name in ('OPTIMAL','FEASIBLE'):
            pick=[cols[q] for q in range(len(cols)) if solver.Value(x[q])]
            full=[j]+pick
            assert len(full)==14 and len(set(full))==14
            assert all(any(k in S for k in full) for S in rowsets)
            branch['result']='K14_FEASIBLE';branch['witnessLeafOrbitIndices']=full;witnessed=full
            records.append(branch);break
        else:
            branch['result']='UNKNOWN_AFTER_DPF'
        records.append(branch)

    all_closed = len(closed | newly_closed) == len(fixed_ois)
    if witnessed is not None:
        result='K14_FEASIBLE'; interval=[14,14]
    elif all_closed:
        result='K14_INFEASIBLE'; interval=[15,22]
    else:
        result='UNKNOWN'; interval=[14,22]

    out={
        'schema':'holotrade.depth5-k14-iterated-dual-path-kernel.v1','valid':True,'status':'PASS',
        'literatureAnchor':{'doi':'10.4230/LIPIcs.SEA.2026.28','method':'dual-path fixing for set cover',
                            'implementationBoundary':'This pass uses multiple exactly verified dual-feasible points, but not the literal hidden dual-simplex iterate stream from the paper.'},
        'inputResult':k14['result'],'initialClosedBranches':len(closed),'initialUnresolvedBranches':len(unresolved),
        'unresolvedBranchesProcessed':len(records),'newlyClosedBranches':len(newly_closed),
        'branchRecords':records,'solverRecords':solver_records,'result':result,
        'witnessLeafOrbitIndices':witnessed,'certifiedIntervalUpdate':interval,
        'exactness':{'dualDenominator':D,'integerDualFeasibilityReverified':True,
                     'strictFixingTest':'sum(y)-load(k) > 12','dominatedRowEliminationExact':True},
        'theorem':('Every DPF deletion follows from an explicitly integer-verified feasible dual of the current reduced residual set-cover model and the exact UB=13 fixing inequality. Deleted columns are therefore impossible in that normalized K14 branch. Dominated-row elimination preserves the feasible cover set. A branch is promoted to infeasible only by an empty exact row or CP-SAT INFEASIBLE; a K14 witness is accepted only after direct coverage verification.'),
        'boundary':('Floating HiGHS points are discovery aids. Failure to fix a column is not evidence it belongs to a 14-cover. UNKNOWN CP-SAT branches do not improve the certified lower bound.')}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'valid':True,'result':result,'initialUnresolved':len(unresolved),'processed':len(records),
                      'newlyClosed':len(newly_closed),'interval':interval},sort_keys=True))


if __name__=='__main__':main()
