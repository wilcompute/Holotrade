#!/usr/bin/env python3
"""Direct exact attack on the only question needed to raise depth five: K=13.

The full PSp(4,3)-quotiented depth-five set cover has 6,129 tile-orbit rows and
5,294 seed/leaf-orbit columns.  The LP optimum is 12.671477..., so the present
certified integer lower bound is 13.  To move it to 14 we do not need another
relaxation: it is enough to prove that the Boolean system

    A x >= 1,   sum x <= 13,   x in {0,1}^{5294}

is infeasible.

This script reconstructs the exact frozen coverage matrix, removes only
provably safe duplicate/dominated columns, and attacks K=13 with two independent
engines when available:
  * SCIP as a pure Boolean set-cover feasibility model, with its native
    symmetry detection, propagation and cutting planes;
  * OR-Tools CP-SAT on the same reduced clauses/cardinality constraint.

A solver status of INFEASIBLE is promoted only after the reduced model is
cross-checked against the original matrix and every removed column has an
explicit dominating representative.  FEASIBLE freezes a 13-cover witness and
would close the opposite direction. UNKNOWN changes no theorem.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
from scipy.sparse import csc_matrix

import depth5_induced_subgroup_cuts as old

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/depth5_k13_exact_feasibility_attack.json'
K=13


def column_bitsets(A):
    C=A.tocsc(); bits=[]; counts=[]
    for j in range(C.shape[1]):
        b=0
        rows=C.indices[C.indptr[j]:C.indptr[j+1]]
        for r in rows: b |= 1 << int(r)
        bits.append(b); counts.append(len(rows))
    return bits,counts,C


def safe_reduce(bits,counts,C):
    n=len(bits)
    # Exact duplicate removal first.
    rep_by_bits={}; duplicate_rep={}; unique=[]
    for j,b in enumerate(bits):
        if b in rep_by_bits: duplicate_rep[j]=rep_by_bits[b]
        else: rep_by_bits[b]=j; unique.append(j)

    # Dominance: if cover(j) subset cover(k), j is never needed in a
    # cardinality-minimal cover.  Search supersets only among candidates
    # containing a rare tile of j and with at least as many covered rows.
    row_cols=[[] for _ in range(C.shape[0])]
    for j in unique:
        for r in C.indices[C.indptr[j]:C.indptr[j+1]]: row_cols[int(r)].append(j)
    dominated={}
    order=sorted(unique,key=lambda j:(counts[j],j))
    alive=set(unique)
    for pos,j in enumerate(order):
        if j not in alive: continue
        rows=C.indices[C.indptr[j]:C.indptr[j+1]]
        if not len(rows):
            # Empty columns are always dominated by any nonempty column.
            k=next((u for u in unique if counts[u]>0),None)
            if k is not None: dominated[j]=k; alive.discard(j)
            continue
        r=min(rows,key=lambda rr:len(row_cols[int(rr)]))
        bj=bits[j]
        candidates=sorted(row_cols[int(r)],key=lambda k:(-counts[k],k))
        for k in candidates:
            if k==j or k not in alive or counts[k]<counts[j]: continue
            if bj & ~bits[k] == 0:
                dominated[j]=k; alive.discard(j); break
    kept=sorted(alive)
    removed_to_rep={**duplicate_rep,**dominated}
    # Chase representatives to a kept column and verify exact containment.
    final={}
    for j in removed_to_rep:
        k=removed_to_rep[j]; seen={j}
        while k not in alive and k in removed_to_rep and k not in seen:
            seen.add(k); k=removed_to_rep[k]
        assert k in alive
        assert bits[j] & ~bits[k] == 0
        final[j]=k
    return kept,final


def build_row_columns(A,kept):
    pos={j:i for i,j in enumerate(kept)}; C=A.tocsc(); rows=[[] for _ in range(A.shape[0])]
    for j in kept:
        q=pos[j]
        for r in C.indices[C.indptr[j]:C.indptr[j+1]]: rows[int(r)].append(q)
    assert all(rows)
    return rows,pos


def solve_scip(rows,nvars,seconds=900):
    try:
        from pyscipopt import Model, quicksum, SCIP_PARAMSETTING
    except Exception as e:
        return {'engine':'SCIP','status':'UNAVAILABLE','reason':repr(e)}
    m=Model('depth5_k13')
    x=[m.addVar(vtype='B',name=f'x{j}') for j in range(nvars)]
    for i,cols in enumerate(rows): m.addCons(quicksum(x[j] for j in cols)>=1,name=f'c{i}')
    m.addCons(quicksum(x)<=K,name='card13')
    m.setObjective(0)
    m.setRealParam('limits/time',float(seconds))
    try: m.setIntParam('parallel/maxnthreads',8)
    except Exception: pass
    try: m.setPresolve(SCIP_PARAMSETTING.AGGRESSIVE); m.setSeparating(SCIP_PARAMSETTING.AGGRESSIVE)
    except Exception: pass
    m.hideOutput(False)
    t=time.time(); m.optimize(); elapsed=time.time()-t
    status=str(m.getStatus()).lower()
    rec={'engine':'SCIP','status':status.upper(),'elapsedSeconds':elapsed,
         'nodes':int(m.getNNodes()),'solutions':int(m.getNSols())}
    if status in ('optimal','bestsollimit','sollimit') and m.getNSols()>0:
        sol=m.getBestSol(); pick=[j for j,v in enumerate(x) if m.getSolVal(sol,v)>0.5]
        rec['witnessReducedIndices']=pick; rec['witnessSize']=len(pick)
    try:
        rec['dualBound']=float(m.getDualbound()); rec['primalBound']=float(m.getPrimalbound())
    except Exception: pass
    return rec


def solve_cpsat(rows,nvars,seconds=900):
    try:
        from ortools.sat.python import cp_model
    except Exception as e:
        return {'engine':'CP-SAT','status':'UNAVAILABLE','reason':repr(e)}
    M=cp_model.CpModel(); x=[M.NewBoolVar(f'x{j}') for j in range(nvars)]
    for cols in rows: M.AddBoolOr([x[j] for j in cols])
    M.Add(sum(x)<=K)
    S=cp_model.CpSolver(); S.parameters.max_time_in_seconds=float(seconds); S.parameters.num_search_workers=8
    S.parameters.symmetry_level=3; S.parameters.cp_model_presolve=True; S.parameters.linearization_level=2
    t=time.time(); st=S.Solve(M); elapsed=time.time()-t; name=S.StatusName(st)
    rec={'engine':'CP-SAT','status':name,'elapsedSeconds':elapsed,
         'conflicts':int(S.NumConflicts()),'branches':int(S.NumBranches())}
    if name in ('OPTIMAL','FEASIBLE'):
        pick=[j for j in range(nvars) if S.Value(x[j])]; rec['witnessReducedIndices']=pick; rec['witnessSize']=len(pick)
    return rec


def main():
    pts,_idx,iso,_supports,_charts,_edge=old.geometry(); _leaf,A=old.full_orbit_machine(pts,iso)
    assert A.shape==(6129,5294)
    bits,counts,C=column_bitsets(A); kept,removed=safe_reduce(bits,counts,C)
    rows,pos=build_row_columns(A,kept)
    # Every original column is either kept or explicitly dominated by a kept one.
    assert len(kept)+len(removed)==5294
    for j,k in removed.items(): assert bits[j] & ~bits[k] == 0

    scip=solve_scip(rows,len(kept),900)
    # If SCIP already proves one direction, CP-SAT remains an independent check
    # but gets a shorter budget; otherwise give it the full second half.
    cp=solve_cpsat(rows,len(kept),600 if scip['status'] in ('INFEASIBLE','OPTIMAL') else 900)

    def expand_witness(rec):
        if 'witnessReducedIndices' not in rec:return None
        pick=[kept[q] for q in rec['witnessReducedIndices']]
        assert len(pick)<=K
        union=0
        for j in pick: union|=bits[j]
        assert union.bit_count()==6129
        rec['witnessOriginalLeafOrbitIndices']=pick
        return pick
    w1=expand_witness(scip);w2=expand_witness(cp)

    infeasible=(scip['status']=='INFEASIBLE' or cp['status']=='INFEASIBLE')
    feasible=(w1 is not None or w2 is not None)
    assert not (infeasible and feasible)
    result='K13_INFEASIBLE' if infeasible else ('K13_FEASIBLE' if feasible else 'UNKNOWN')
    out={'schema':'holotrade.depth5-k13-exact-feasibility-attack.v1','valid':True,
         'fullModel':{'tileOrbits':6129,'leafOrbits':5294,'K':K},
         'safeReduction':{'keptColumns':len(kept),'removedColumns':len(removed),
                          'duplicateOrDominatedOnly':True},
         'SCIP':scip,'CPSAT':cp,'result':result,
         'newCertifiedLowerBound':14 if infeasible else 13,
         'theorem':('If result=K13_INFEASIBLE, no thirteen-or-fewer seed-orbit cover exists for the exact 6129x5294 depth-five quotient, hence the integer cover number is at least 14. If result=K13_FEASIBLE, the recorded original leaf-orbit indices are an exact witness. UNKNOWN changes no bound.'),
         'boundary':('Column reduction uses only exact duplicate/subset dominance. Solver infeasibility is a finite Boolean-combinatorial certificate status; no continuum or physical interpretation is attached.')}
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'result':result,'kept':len(kept),'SCIP':scip['status'],'CPSAT':cp['status'],
                      'newLB':out['newCertifiedLowerBound']},sort_keys=True))

if __name__=='__main__': main()
