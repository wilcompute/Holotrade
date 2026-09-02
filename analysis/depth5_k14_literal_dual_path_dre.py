#!/usr/bin/env python3
"""Literal simplex dual-path fixing + exact DRE for the depth-five K=14 frontier.

This pass follows the 2026 Yamagishi--Fampa--Lee dual-path-fixing idea more
literally than our SciPy cloud approximation.  We formulate the residual
set-cover dual

    max 1^T y    subject to A^T y <= 1, y >= 0

in GLPK, start primal simplex from the all-slack feasible basis y=0, advance
one pivot at a time, and harvest every primal-feasible dual iterate.  Every
floating iterate is rounded DOWN to denominator 10^7 and independently
rechecked by integer arithmetic before it may fix a column.

For a residual cutoff of b columns, any dual-feasible y proves that a candidate
column k cannot occur in a <=b cover when

    1 + y^T(1-A_k) > b,

i.e. score(y)-load_y(k) > b-1.  This is a cutoff infeasibility statement and
does not require that a b-column incumbent already be known.

After each dual path we apply exact dominated-row elimination plus the second
DRE rule emphasized in the SEA 2026 paper: a singleton row forces its unique
column to 1.  Forced columns reduce the residual budget and covered rows are
removed.  We iterate DPF+DRE, then give the theorem-safe kernel to CP-SAT.

UNKNOWN never improves the theorem.  Only an independently verified <=14
witness or exhaustive closure of all 88 S5 first-column branches changes the
certified interval.

Reference: P.M.F. Yamagishi, M. Fampa, J. Lee, SEA 2026,
DOI 10.4230/LIPIcs.SEA.2026.28.
"""
from __future__ import annotations

import json
import time
from collections import deque
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix

import depth5_induced_subgroup_cuts as old
import depth5_coordinate_s5_automorphism as s5

ROOT = Path(__file__).resolve().parents[1]
K13 = ROOT / 'data/depth5_k13_strong_dual_fixing.json'
K14 = ROOT / 'data/depth5_k14_recycled_dual_pair_kernel.json'
OUT = ROOT / 'data/depth5_k14_literal_dual_path_dre.json'
D = 10_000_000
MAX_DPF_ROUNDS = 3
MAX_SIMPLEX_PIVOTS = 360
GLOBAL_SECONDS = 2100.0
CP_SAT_SECONDS = 90.0


def make_orbits(gens, n):
    G = s5.closure(gens, n)
    assert len(G) == 120
    unseen = set(range(n)); out = []
    while unseen:
        j = min(unseen); O = sorted({g[j] for g in G}); unseen.difference_update(O); out.append(O)
    assert len(out) == 94
    return G, out


def exact_dual(R, yf):
    """Round down and exactly verify R.T*y <= D."""
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


def reduce_rows_and_force(row_ids, rowsets, active_cols, budget, forced):
    """Iterated duplicate/dominated-row elimination and singleton forcing."""
    active_cols = set(active_cols); row_ids = list(row_ids); forced = list(forced)
    trace = []
    while True:
        active = active_cols
        uniq = {}
        empty = []
        for r in row_ids:
            S = frozenset(rowsets[r] & active)
            if not S: empty.append(r)
            else: uniq.setdefault(S, r)
        if empty:
            return row_ids, active_cols, budget, forced, trace, empty

        ordered = sorted(uniq.items(), key=lambda kv: (len(kv[0]), tuple(sorted(kv[0]))))
        kept_ids = []; kept_sets = []
        for S, r in ordered:
            if any(T.issubset(S) for T in kept_sets):
                continue
            kept_sets.append(S); kept_ids.append(r)
        trace.append({'rowsBefore': len(row_ids), 'distinctRows': len(uniq), 'rowsAfterDominance': len(kept_ids)})
        row_ids = kept_ids

        singles = sorted((next(iter(S)), r) for S, r in zip(kept_sets, kept_ids) if len(S) == 1)
        if not singles:
            return row_ids, active_cols, budget, forced, trace, []

        k, _r = singles[0]
        forced.append(int(k)); budget -= 1
        if budget < 0:
            return row_ids, active_cols, budget, forced, trace, [-1]
        # The selected forced column satisfies every row it covers.
        row_ids = [r for r in row_ids if k not in rowsets[r]]
        active_cols.discard(k)
        trace[-1]['forcedColumn'] = int(k)
        trace[-1]['budgetAfterForce'] = int(budget)
        if not row_ids:
            return row_ids, active_cols, budget, forced, trace, []


def glpk_dual_path(R, budget, max_pivots=MAX_SIMPLEX_PIVOTS):
    """Harvest exact-safe fixings from one-pivot GLPK primal-simplex iterates."""
    import swiglpk as glp
    nrow, ncol = R.shape
    # Dual variables correspond to residual covering rows; GLPK constraints
    # correspond to residual covering columns.
    lp = glp.glp_create_prob()
    glp.glp_set_obj_dir(lp, glp.GLP_MAX)
    glp.glp_add_rows(lp, ncol)
    for j in range(ncol):
        glp.glp_set_row_bnds(lp, j + 1, glp.GLP_UP, 0.0, 1.0)
    glp.glp_add_cols(lp, nrow)
    for i in range(nrow):
        glp.glp_set_col_bnds(lp, i + 1, glp.GLP_LO, 0.0, 0.0)
        glp.glp_set_obj_coef(lp, i + 1, 1.0)

    T = R.transpose().tocoo()
    nnz = len(T.data)
    ia = glp.intArray(nnz + 1); ja = glp.intArray(nnz + 1); ar = glp.doubleArray(nnz + 1)
    for q, (r, c) in enumerate(zip(T.row, T.col), start=1):
        ia[q] = int(r) + 1; ja[q] = int(c) + 1; ar[q] = 1.0
    glp.glp_load_matrix(lp, nnz, ia, ja, ar)
    glp.glp_std_basis(lp)  # y=0, all auxiliary slacks basic and feasible.

    parm = glp.glp_smcp(); glp.glp_init_smcp(parm)
    parm.msg_lev = glp.GLP_MSG_OFF
    parm.meth = glp.GLP_PRIMAL
    parm.presolve = glp.GLP_OFF
    parm.it_lim = 1

    fixed = set(); seen = set(); records = []
    optimal = False; last_it = glp.glp_get_it_cnt(lp)
    threshold = (budget - 1) * D
    for step in range(max_pivots + 1):
        # y=0 is feasible before the first pivot; thereafter primal simplex
        # retains feasibility.  Harvest only when GLPK explicitly says so.
        pstat = glp.glp_get_prim_stat(lp)
        if pstat == glp.GLP_FEAS:
            yf = np.array([glp.glp_get_col_prim(lp, i + 1) for i in range(nrow)], dtype=float)
            yint, loads, score, mx = exact_dual(R, yf)
            key = yint.tobytes()
            if key not in seen:
                seen.add(key)
                local = np.flatnonzero(score - loads > threshold)
                fixed.update(map(int, local))
                records.append({'simplexIteration': int(glp.glp_get_it_cnt(lp)),
                                'scoreNumerator': score, 'score': score / D,
                                'maxColumnLoadNumerator': mx,
                                'fixedColumnsByIterate': int(len(local)),
                                'cumulativeFixedColumns': int(len(fixed))})
        if glp.glp_get_status(lp) == glp.GLP_OPT:
            optimal = True; break
        if step == max_pivots:
            break
        rc = glp.glp_simplex(lp, parm)
        now = glp.glp_get_it_cnt(lp)
        if rc not in (0, glp.GLP_EITLIM):
            break
        if now == last_it:
            if glp.glp_get_status(lp) == glp.GLP_OPT: optimal = True
            break
        last_it = now

    iters = int(glp.glp_get_it_cnt(lp))
    glp.glp_delete_prob(lp)
    return fixed, {'harvestedDualPoints': len(records), 'simplexIterations': iters,
                   'optimalReached': optimal, 'pathRecords': records}


def verify_witness(sel, rowsets):
    S = set(map(int, sel))
    return len(S) <= 14 and all(bool(R & S) for R in rowsets)


def main():
    from ortools.sat.python import cp_model

    k13 = json.loads(K13.read_text()); k14 = json.loads(K14.read_text())
    assert k13['valid'] and k13['result'] == 'K13_INFEASIBLE'
    assert k14['valid'] and k14['result'] == 'UNKNOWN'

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
    fixed_ois = [int(x) for x in k13['strongFixing']['fixedOrbitIndices']]
    cert_by_oi = {int(c['orbitIndex']): c for c in k13['exactDualCertificates']}
    prior_solver = {int(r['orbitIndex']): r for r in k14.get('solverRecords', [])}

    already_closed = set()
    for oi in fixed_ois:
        if pair_by_oi[oi]['emptyRowCount'] > 0 or prior_solver.get(oi, {}).get('status') == 'INFEASIBLE':
            already_closed.add(oi)
    unresolved = [oi for oi in fixed_ois if oi not in already_closed]
    unresolved.sort(key=lambda oi: (pair_by_oi[oi]['allowedSecondColumns'], oi))

    deadline = time.time() + GLOBAL_SECONDS
    records=[]; newly_closed=set(); witness=None
    for oi in unresolved:
        if time.time() >= deadline: break
        first = int(orbits[oi][0])
        active = set(range(5294)); active.remove(first)
        rows = [r for r,S in enumerate(rowsets) if first not in S]
        budget = 13; forced=[]
        branch={'orbitIndex':oi,'representativeColumn':first,'pairKernelAllowedSecondColumns':pair_by_oi[oi]['allowedSecondColumns'],
                'rounds':[],'initialRows':len(rows),'initialColumns':len(active)}

        # Reapply the frozen exact seed certificate before literal DPF.
        cert=cert_by_oi[oi]; y=np.zeros(6128,dtype=np.int64)
        for r,w in cert['weights']: y[int(r)]=int(w)
        score=int(y.sum()); loads=np.asarray(B.T.dot(y),dtype=np.int64).reshape(-1)
        seed_fixed={k for k in active if score-int(loads[k])>(budget-1)*D}
        active-=seed_fixed
        rows,active,budget,forced,dre,empty=reduce_rows_and_force(rows,rowsets,active,budget,forced)
        branch['seed']={'fixedColumns':len(seed_fixed),'budget':budget,'forcedColumns':list(forced),'DRE':dre,'emptyRows':empty[:16]}
        if empty or budget < 0:
            branch['result']='INFEASIBLE_AFTER_EXACT_SEED_DRE';newly_closed.add(oi);records.append(branch);continue
        if not rows:
            cand=[first]+forced
            assert verify_witness(cand,rowsets)
            witness=sorted(cand);branch['result']='FEASIBLE_DRE';records.append(branch);break

        for rnd in range(MAX_DPF_ROUNDS):
            cols=sorted(active); R=B[rows,:][:,cols].tocsr()
            fixed_local,meta=glpk_dual_path(R,budget)
            fixed_global={cols[q] for q in fixed_local}
            active-=fixed_global
            before_forced=len(forced)
            rows,active,budget,forced,dre,empty=reduce_rows_and_force(rows,rowsets,active,budget,forced)
            branch['rounds'].append({'round':rnd,'literalDualPath':meta,'fixedColumns':len(fixed_global),
                                     'remainingColumns':len(active),'remainingRows':len(rows),'budget':budget,
                                     'newForcedColumns':forced[before_forced:],'DRE':dre,'emptyRows':empty[:16]})
            if empty or budget < 0:
                branch['result']='INFEASIBLE_AFTER_DPF_DRE';newly_closed.add(oi);break
            if not rows:
                cand=[first]+forced
                assert verify_witness(cand,rowsets)
                witness=sorted(cand);branch['result']='FEASIBLE_DPF_DRE';break
            if not fixed_global and len(forced)==before_forced:
                branch['result']='DPF_DRE_STABLE';break
        if witness is not None:
            records.append(branch);break
        if oi in newly_closed:
            records.append(branch);continue

        # Exact integer closure on the theorem-safe kernel.
        cols=sorted(active); pos={j:q for q,j in enumerate(cols)}
        supports=[]; impossible=False
        for r in rows:
            S=[pos[j] for j in rowsets[r] if j in pos]
            if not S: impossible=True;break
            supports.append(frozenset(S))
        if impossible:
            branch['result']='INFEASIBLE_EMPTY_PRE_SAT';newly_closed.add(oi);records.append(branch);continue
        uniq=sorted(set(supports),key=lambda S:(len(S),tuple(sorted(S))))
        minimal=[]
        for S in uniq:
            if any(T.issubset(S) for T in minimal):continue
            minimal.append(S)
        M=cp_model.CpModel();x=[M.NewBoolVar(f'x{q}') for q in range(len(cols))]
        for S in minimal:M.AddBoolOr([x[q] for q in S])
        M.Add(sum(x)<=budget)
        solver=cp_model.CpSolver();solver.parameters.max_time_in_seconds=min(CP_SAT_SECONDS,max(1.0,deadline-time.time()))
        solver.parameters.num_search_workers=8;solver.parameters.symmetry_level=3;solver.parameters.cp_model_presolve=True
        st=solver.Solve(M);name=solver.StatusName(st)
        branch['solver']={'status':name,'columns':len(cols),'minimalRows':len(minimal),'budget':budget,
                          'branches':int(solver.NumBranches()),'conflicts':int(solver.NumConflicts())}
        if name=='INFEASIBLE':
            branch['result']='INFEASIBLE_CP_SAT';newly_closed.add(oi)
        elif name in ('OPTIMAL','FEASIBLE'):
            pick=[cols[q] for q in range(len(cols)) if solver.Value(x[q])]
            cand=[first]+forced+pick
            assert verify_witness(cand,rowsets)
            witness=sorted(cand);branch['result']='K14_FEASIBLE'
        else:
            branch['result']='UNKNOWN'
        records.append(branch)
        if witness is not None:break

    all_closed = len(already_closed | newly_closed) == len(fixed_ois)
    if witness is not None:
        result='K14_FEASIBLE'; interval=[14,14]
    elif all_closed:
        result='K14_INFEASIBLE'; interval=[15,22]
    else:
        result='UNKNOWN'; interval=[14,22]

    out={
      'schema':'holotrade.depth5-k14-literal-dual-path-dre.v1','valid':True,
      'method':'literal GLPK primal-simplex dual path, exact downward rationalization, iterated DPF+DRE with singleton forcing',
      'sourceReference':'Yamagishi-Fampa-Lee, SEA 2026, DOI 10.4230/LIPIcs.SEA.2026.28',
      'firstColumnOrbitCount':len(fixed_ois),'alreadyClosedBranches':len(already_closed),
      'branchesAttempted':len(records),'newlyClosedBranches':len(newly_closed),
      'allBranchesClosed':all_closed,'result':result,'witnessLeafOrbitIndices':witness,
      'certifiedIntervalUpdate':interval,'branchRecords':records,
      'theorem':('An explicit <=14 cover was independently verified against all 6,128 exact constraints; with the frozen K13 infeasibility theorem this proves tau_5=14.' if witness is not None else
                 ('All exact S5-normalized K14 first-column branches are closed by theorem-safe fixing/DRE/CP-SAT, so no 14-cover exists and tau_5>=15.' if all_closed else
                  'Literal dual-path fixing and exact DRE close only the listed branches. Remaining UNKNOWN branches leave the certified interval unchanged.')),
      'boundary':'Floating simplex iterates are discovery inputs only. Every fixing uses a denominator-10^7 dual rounded downward and reverified by integer arithmetic. UNKNOWN and unprocessed branches are non-evidence.'
    }
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'valid':True,'result':result,'attempted':len(records),'newlyClosed':len(newly_closed),'allClosed':all_closed,
                      'witness':witness,'interval':interval},sort_keys=True))

if __name__=='__main__':main()
