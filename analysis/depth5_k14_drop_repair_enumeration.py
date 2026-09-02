#!/usr/bin/env python3
"""Exact drop/repair decomposition around the best frozen 14-column near-cover.

Let H be the frozen near-cover.  For a drop set D subset H of size r, every row
still hit by H\D is permanently satisfied.  Only the exposed rows U(D) need to
be repaired.  Therefore a 14-cover at Hamming radius r exists iff there are r
columns outside H covering all U(D).  This turns the full 6,128-row problem
into many tiny residual set-cover instances.

We enumerate every drop set for r<=4 and the most promising r=5 drop sets
ordered by |U(D)|.  FEASIBLE is independently checked against all 6,128 exact
constraints.  INFEASIBLE records are exact local no-go certificates; UNKNOWN
never changes the global theorem.
"""
from __future__ import annotations

import itertools
import json
import time
from pathlib import Path

import numpy as np

from depth5_k14_constructive_witness_search import build_instance, coverage_counts, exact_verify

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'data/depth5_k14_constructive_witness_search.json'
OUT=ROOT/'data/depth5_k14_drop_repair_enumeration.json'
K=14
GLOBAL_SECONDS=1500.0
PER_MODEL_SECONDS=0.75
R5_LIMIT=500


def main():
    from ortools.sat.python import cp_model

    src=json.loads(SRC.read_text())
    assert src['valid'] and src['result']=='UNKNOWN'
    H=tuple(sorted(map(int,src['bestHeuristicSelection'])))
    assert len(H)==K and src['bestHeuristicUncoveredRows']==111
    Hset=set(H)

    rowsets,colrows,_reps=build_instance()
    nrows=len(rowsets); ncols=len(colrows)
    assert nrows==6128 and ncols==5294
    basecnt=coverage_counts(H,colrows,nrows)
    assert int(np.count_nonzero(basecnt==0))==111

    # Reverse lookup from exposed row to all non-H columns covering it.
    rowcols=[[] for _ in range(nrows)]
    for j,rows in enumerate(colrows):
        if j in Hset: continue
        for r in rows: rowcols[int(r)].append(j)

    deadline=time.time()+GLOBAL_SECONDS
    records=[]; witness=None
    by_radius={}

    for radius in range(1,6):
        drops=list(itertools.combinations(H,radius))
        scored=[]
        for D in drops:
            cnt=basecnt.copy()
            for j in D: cnt[colrows[j]]-=1
            U=np.flatnonzero(cnt==0)
            scored.append((len(U),D,tuple(map(int,U))))
        scored.sort(key=lambda z:(z[0],z[1]))
        if radius==5: scored=scored[:R5_LIMIT]

        summary={'radius':radius,'dropSetsConsidered':len(scored),'feasible':0,'infeasible':0,'unknown':0,
                 'minimumExposedRows':int(scored[0][0]) if scored else None,
                 'maximumExposedRows':int(scored[-1][0]) if scored else None}
        by_radius[str(radius)]=summary

        for exposed,D,U in scored:
            if time.time()>=deadline: break
            # Columns irrelevant to U can never help this residual repair.
            cand=sorted(set(j for r in U for j in rowcols[r]))
            if not cand:
                summary['infeasible']+=1
                records.append({'radius':radius,'drop':list(D),'exposedRows':exposed,'candidateColumns':0,'status':'INFEASIBLE_EMPTY'})
                continue
            pos={j:q for q,j in enumerate(cand)}
            M=cp_model.CpModel(); x=[M.NewBoolVar(f'x{q}') for q in range(len(cand))]
            impossible=False
            for r in U:
                qs=[pos[j] for j in rowcols[r] if j in pos]
                if not qs:
                    impossible=True; break
                M.AddBoolOr([x[q] for q in qs])
            if impossible:
                summary['infeasible']+=1
                records.append({'radius':radius,'drop':list(D),'exposedRows':exposed,'candidateColumns':len(cand),'status':'INFEASIBLE_ROW'})
                continue
            M.Add(sum(x)==radius)
            S=cp_model.CpSolver(); S.parameters.max_time_in_seconds=PER_MODEL_SECONDS
            S.parameters.num_search_workers=8; S.parameters.cp_model_presolve=True
            S.parameters.symmetry_level=3; S.parameters.linearization_level=2
            st=S.Solve(M); name=S.StatusName(st)
            rec={'radius':radius,'drop':list(D),'exposedRows':exposed,'candidateColumns':len(cand),
                 'status':name,'branches':int(S.NumBranches()),'conflicts':int(S.NumConflicts()),'wallSeconds':float(S.WallTime())}
            if name in ('OPTIMAL','FEASIBLE'):
                add=[cand[q] for q in range(len(cand)) if S.Value(x[q])]
                assert len(add)==radius
                w=sorted((Hset-set(D))|set(add))
                assert len(w)==K and exact_verify(w,rowsets)
                rec['add']=add; rec['witness']=w
                records.append(rec); summary['feasible']+=1; witness=w; break
            elif name=='INFEASIBLE':
                summary['infeasible']+=1
            else:
                summary['unknown']+=1
            records.append(rec)
        if witness is not None or time.time()>=deadline: break

    result='K14_FEASIBLE' if witness is not None else 'UNKNOWN'
    out={
        'schema':'holotrade.depth5-k14-drop-repair-enumeration.v1','valid':True,
        'sourceNearCover':list(H),'sourceUncoveredRows':111,
        'radiusSummary':by_radius,'records':records,'result':result,
        'witnessLeafOrbitIndices':witness,
        'certifiedIntervalUpdate':[14,14] if witness is not None else [14,22],
        'elapsedSeconds':GLOBAL_SECONDS-max(0.0,deadline-time.time()),
        'theorem':(
            'The listed fourteen columns cover every one of the 6,128 exact depth-five constraints; with K13 already impossible, tau_5=14.'
            if witness is not None else
            'No globally certified K14 witness was produced. Every record marked INFEASIBLE exactly excludes that drop/repair neighborhood; UNKNOWN records have no theorem consequence.'),
        'boundary':'The decomposition is exact for each tested drop set because H\\D satisfies every row outside U(D). Only an independently verified explicit witness changes the global interval.'
    }
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'valid':True,'result':result,'witness':witness,'radiusSummary':by_radius},sort_keys=True))

if __name__=='__main__': main()
