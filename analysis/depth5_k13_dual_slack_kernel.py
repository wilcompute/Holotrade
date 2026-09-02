#!/usr/bin/env python3
"""Outside-the-box exact K=13 kernel from LP-dual slack.

Let y>=0 be ANY exact feasible dual packing for the set-cover LP,

    A^T y <= 1,   Y=sum(y)>12.

If S is a cover with |S|<=13 then weak duality forces |S|=13.  Writing
l_j=sum_{r covered by j} y_r and m_r for the multiplicity with which row r is
covered,

    sum_{j in S} l_j = sum_r y_r m_r >= Y.

Hence

    sum_{j in S} (1-l_j) <= 13-Y = delta.

All terms are nonnegative, so EVERY column in a hypothetical 13-cover must
individually satisfy 1-l_j <= delta, equivalently l_j >= Y-12.  Columns below
that threshold are impossible in any 13-cover and can be deleted exactly.

We obtain a good floating dual from HiGHS, round every coordinate DOWN to a
fixed rational denominator, and then verify A^T y<=1 using integer arithmetic.
Thus the certificate does not trust floating-point feasibility.  The resulting
exact slack budget is also inserted as a pseudo-Boolean constraint in CP-SAT.
Duplicate rows and rows implied by a stronger subset row are removed exactly.
"""
from __future__ import annotations

import collections
import json
import math
import time
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

import depth5_induced_subgroup_cuts as old

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/depth5_k13_dual_slack_kernel.json'
D=10_000_000
K=13


def exact_column_loads(C,yint):
    loads=[]
    for j in range(C.shape[1]):
        rows=C.indices[C.indptr[j]:C.indptr[j+1]]
        loads.append(sum(int(yint[int(r)]) for r in rows))
    return loads


def minimal_row_antichain(rowsets):
    """Keep only inclusion-minimal row supports; supersets are weaker."""
    unique=sorted(set(rowsets),key=lambda S:(len(S),tuple(sorted(S))))
    kept=[];bits=[]
    for S in unique:
        b=0
        for j in S:b|=1<<int(j)
        # If T subset S is already kept, S is redundant.
        redundant=False
        for tb in bits:
            if tb & ~b == 0:
                redundant=True;break
        if not redundant:
            kept.append(S);bits.append(b)
    return kept,len(unique)


def main():
    from ortools.sat.python import cp_model

    pts,_idx,iso,_supports,_charts,_edge=old.geometry();_leaf,A=old.full_orbit_machine(pts,iso)
    assert A.shape==(6129,5294)
    C=A.tocsc()

    # Numerical search only; theorem certificate is the integer vector below.
    res=linprog(-np.ones(A.shape[0]),A_ub=A.T,b_ub=np.ones(A.shape[1]),
                bounds=(0,None),method='highs')
    assert res.success
    y=np.maximum(np.asarray(res.x,dtype=float),0.0)
    yint=np.floor(y*D).astype(np.int64)
    loads=exact_column_loads(C,yint);mx=max(loads)
    if mx>D:
        # Uniform downward rescaling preserves nonnegativity and is then
        # reverified exactly.  Usually this branch is unnecessary.
        yint=(yint*(D-1)//mx).astype(np.int64)
        loads=exact_column_loads(C,yint);mx=max(loads)
    assert min(yint)>=0 and mx<=D
    Y=int(yint.sum());assert Y>12*D
    delta=13*D-Y
    threshold=Y-12*D
    assert delta>=0

    candidates=[j for j,L in enumerate(loads) if L>=threshold]
    impossible=[j for j,L in enumerate(loads) if L<threshold]
    cpos={j:i for i,j in enumerate(candidates)}

    raw=[]
    empty_original=[]
    for r in range(A.shape[0]):
        S=frozenset(cpos[int(j)] for j in A.indices[A.indptr[r]:A.indptr[r+1]] if int(j) in cpos)
        if not S:empty_original.append(r)
        raw.append(S)

    immediate=bool(empty_original)
    if immediate:
        rowsets=[];distinct=0
    else:
        rowsets,distinct=minimal_row_antichain(raw)

    rec={'engine':'CP-SAT','status':'SKIPPED_EMPTY_ROW' if immediate else 'NOT_RUN'}
    result='K13_INFEASIBLE' if immediate else 'UNKNOWN'
    if not immediate:
        M=cp_model.CpModel();x=[M.NewBoolVar(f'x{q}') for q in range(len(candidates))]
        for S in rowsets:M.AddBoolOr([x[q] for q in S])
        M.Add(sum(x)==13)
        slacks=[D-loads[j] for j in candidates]
        M.Add(sum(int(slacks[q])*x[q] for q in range(len(candidates)))<=delta)
        S=cp_model.CpSolver();S.parameters.max_time_in_seconds=1800;S.parameters.num_search_workers=8
        S.parameters.symmetry_level=3;S.parameters.cp_model_presolve=True;S.parameters.linearization_level=2
        S.parameters.log_search_progress=True
        t=time.time();st=S.Solve(M);elapsed=time.time()-t;name=S.StatusName(st)
        rec={'engine':'CP-SAT','status':name,'elapsedSeconds':elapsed,
             'branches':int(S.NumBranches()),'conflicts':int(S.NumConflicts())}
        if name in ('OPTIMAL','FEASIBLE'):
            pick=[candidates[q] for q in range(len(candidates)) if S.Value(x[q])]
            assert len(pick)==13
            assert all(any(j in A.indices[A.indptr[r]:A.indptr[r+1]] for j in pick) for r in range(A.shape[0]))
            assert sum(D-loads[j] for j in pick)<=delta
            rec['witnessOriginalLeafOrbitIndices']=pick;rec['witnessSize']=13
            result='K13_FEASIBLE'
        elif name=='INFEASIBLE':result='K13_INFEASIBLE'

    cert_pairs=[[int(r),int(v)] for r,v in enumerate(yint) if v]
    out={'schema':'holotrade.depth5-k13-dual-slack-kernel.v1','valid':True,
         'original':{'tileOrbitRows':6129,'leafOrbitColumns':5294,'K':13},
         'exactDualCertificate':{
             'denominator':D,'nonzeroWeights':cert_pairs,'objectiveNumerator':Y,
             'objective':Y/D,'maxColumnLoadNumerator':mx,
             'verifiedATyLeOneByIntegerArithmetic':True,
             'deltaNumerator':delta,'delta':delta/D,
             'requiredColumnLoadNumerator':threshold,'requiredColumnLoad':threshold/D},
         'dualSlackKernel':{
             'candidateColumns':len(candidates),'impossibleColumns':len(impossible),
             'candidateOriginalLeafOrbitIndices':candidates,
             'emptyRowsAfterPruning':empty_original,
             'distinctRowsBeforeSubsetReduction':distinct,
             'minimalRowsAfterSubsetReduction':len(rowsets),
             'rowSupersetReductionExact':True},
         'solver':rec,'result':result,
         'newCertifiedLowerBound':14 if result=='K13_INFEASIBLE' else 13,
         'theorem':('For the frozen exact rational dual y, every cover of size at most 13 must have size exactly 13 and can use only columns j with dual load l_j >= Y-12; furthermore its total dual slack sum_j(1-l_j) is at most 13-Y. The candidate deletion and pseudo-Boolean slack budget therefore preserve every possible 13-cover. INFEASIBLE certifies depth-five cover number at least 14.'),
         'boundary':('HiGHS is used only to discover a dual vector. The stored integer numerator vector is rounded downward/rescaled and A^T y<=1 is verified exactly by integer arithmetic before any theorem is inferred. UNKNOWN changes no bound.')}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'valid':True,'dual':Y/D,'delta':delta/D,'candidates':len(candidates),
                      'impossible':len(impossible),'minimalRows':len(rowsets),'emptyRows':len(empty_original),
                      'result':result,'status':rec['status']},sort_keys=True))

if __name__=='__main__':main()
