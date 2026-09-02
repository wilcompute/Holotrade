#!/usr/bin/env python3
"""Construction-first exact witness search for the depth-five K=14 frontier.

K=13 is already certified impossible, so one explicit 14-column cover closes
this depth completely: tau_5 = 14.  Previous attacks emphasized infeasibility.
This pass deliberately attacks the other side.

The heuristic phase is NOT evidence.  It only manufactures strong starts:
  * adaptive weighted greedy construction of 14 columns;
  * randomized restricted-candidate choices among near-best gains;
  * exact 1-swap local improvement using maintained row coverage counts;
  * multiplicative weights on persistently uncovered rows.

The exact phase uses CP-SAT.  Any reported witness is independently checked
against every one of the 6,128 distinct Boolean cover constraints before the
JSON result may say K14_FEASIBLE.  Failure to find a witness proves nothing.
"""
from __future__ import annotations

import json
import math
import random
import time
from pathlib import Path

import numpy as np
from scipy.sparse import csc_matrix

import depth5_induced_subgroup_cuts as old
import depth5_coordinate_s5_automorphism as s5

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/depth5_k14_constructive_witness_search.json'
K=14
SEED=202609021123


def build_instance():
    pts,_idx,iso,_supports,_charts,_edge=old.geometry()
    leaf_id,reps=s5.build_orbit_machine(pts,iso)
    _leaf,A=old.full_orbit_machine(pts,iso)
    assert A.shape==(6129,5294)
    raw=[frozenset(map(int,A.indices[A.indptr[r]:A.indptr[r+1]])) for r in range(A.shape[0])]
    rowsets=sorted(set(raw),key=lambda S:(len(S),tuple(sorted(S))))
    assert len(rowsets)==6128
    rr=[];cc=[]
    for r,S in enumerate(rowsets):
        for j in S:rr.append(r);cc.append(j)
    from scipy.sparse import csr_matrix
    B=csr_matrix((np.ones(len(rr),dtype=np.int8),(rr,cc)),shape=(6128,5294),dtype=np.int8)
    C=B.tocsc()
    colrows=[np.asarray(C.indices[C.indptr[j]:C.indptr[j+1]],dtype=np.int32) for j in range(C.shape[1])]
    return rowsets,colrows,reps


def coverage_counts(sel,colrows,nrows):
    cnt=np.zeros(nrows,dtype=np.int16)
    for j in sel:cnt[colrows[j]]+=1
    return cnt


def greedy14(colrows,nrows,weights,rng,noise=0.035):
    uncovered=np.ones(nrows,dtype=bool)
    sel=[];used=np.zeros(len(colrows),dtype=bool)
    for step in range(K):
        gains=np.full(len(colrows),-1.0,dtype=float)
        for j,rows in enumerate(colrows):
            if used[j]:continue
            gains[j]=float(weights[rows[uncovered[rows]]].sum())
        best=float(gains.max())
        if best<=0:break
        # Restricted candidate list: randomized among columns within a small
        # fraction of the current best weighted gain.
        thresh=best*(1.0-noise)
        cand=np.flatnonzero(gains>=thresh)
        if len(cand)>48:
            order=np.argpartition(gains[cand],-48)[-48:]
            cand=cand[order]
        vals=gains[cand]
        floor=float(vals.min()); probs=(vals-floor+max(best*1e-6,1e-9))
        probs=probs/probs.sum()
        j=int(rng.choices(cand.tolist(),weights=probs.tolist(),k=1)[0])
        sel.append(j);used[j]=True;uncovered[colrows[j]]=False
    return sel


def local_1swap(sel,colrows,nrows,weights,rng,max_steps=180):
    sel=list(sel);chosen=set(sel);cnt=coverage_counts(sel,colrows,nrows)
    def loss_of(a):
        rows=colrows[a];mask=(cnt[rows]==1)
        return float(weights[rows[mask]].sum())
    for _ in range(max_steps):
        unc=np.flatnonzero(cnt==0)
        if not len(unc):return sel,cnt
        # Candidate additions concentrate on several currently uncovered rows.
        sampled=unc if len(unc)<=24 else np.asarray(rng.sample(unc.tolist(),24),dtype=int)
        cand=set()
        # Reverse lookup lazily by scan is too costly; gain all columns once.
        gain=np.zeros(len(colrows),dtype=float)
        umask=(cnt==0)
        for j,rows in enumerate(colrows):
            if j in chosen:continue
            gain[j]=float(weights[rows[umask[rows]]].sum())
        top=np.argpartition(gain,-min(80,len(gain)))[-min(80,len(gain)):]
        cand.update(int(x) for x in top if gain[x]>0)
        if not cand:break
        removals=sorted(sel,key=loss_of)[:min(10,len(sel))]
        best_delta=0.0;best_pair=None
        current_unc=float(weights[unc].sum())
        for a in removals:
            # remove a virtually, then measure uncovered mass after candidate b
            ca=cnt.copy();ca[colrows[a]]-=1
            base_unc=(ca==0)
            base_mass=float(weights[base_unc].sum())
            for b in cand:
                if b in chosen:continue
                rescued=float(weights[colrows[b][base_unc[colrows[b]]]].sum())
                new_mass=base_mass-rescued
                delta=current_unc-new_mass
                if delta>best_delta+1e-12:
                    best_delta=delta;best_pair=(a,b)
        if best_pair is None:
            # random diversification swap preserving 14 columns
            a=rng.choice(sel); b=int(rng.randrange(len(colrows)))
            if b in chosen:continue
        else:a,b=best_pair
        cnt[colrows[a]]-=1;chosen.remove(a);sel.remove(a)
        cnt[colrows[b]]+=1;chosen.add(b);sel.append(b)
    return sel,cnt


def exact_verify(sel,rowsets):
    S=set(map(int,sel))
    return len(S)==K and all(bool(R&S) for R in rowsets)


def main():
    from ortools.sat.python import cp_model
    rowsets,colrows,reps=build_instance();nrows=len(rowsets);ncols=len(colrows)
    rng=random.Random(SEED)
    weights=np.ones(nrows,dtype=float)
    best_sel=None;best_unc=nrows;best_trace=[];pool=set()
    deadline=time.time()+900.0
    starts=0
    while starts<260 and time.time()<deadline:
        noise=0.02+0.12*((starts%13)/12.0)
        sel=greedy14(colrows,nrows,weights,rng,noise)
        if len(sel)<K:
            starts+=1;continue
        sel,cnt=local_1swap(sel,colrows,nrows,weights,rng)
        unc=np.flatnonzero(cnt==0)
        pool.update(sel)
        if len(unc)<best_unc:
            best_unc=len(unc);best_sel=sorted(sel)
            best_trace.append({'start':starts,'uncovered':best_unc,'selected':best_sel})
            print(json.dumps(best_trace[-1],sort_keys=True),flush=True)
        if not len(unc):
            assert exact_verify(sel,rowsets)
            out={'schema':'holotrade.depth5-k14-constructive-witness.v1','valid':True,
                 'result':'K14_FEASIBLE','witnessLeafOrbitIndices':sorted(map(int,sel)),
                 'distinctConstraintCount':6128,'heuristicStarts':starts+1,
                 'certifiedIntervalUpdate':[14,14],
                 'theorem':'The listed fourteen depth-five leaf orbits cover every one of the 6,128 distinct exact PSp-quotient constraints. Since K=13 is independently certified infeasible, tau_5=14.',
                 'boundary':'The heuristic search is not evidence; only the independently verified explicit witness is.'}
            OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'result':'K14_FEASIBLE','witness':out['witnessLeafOrbitIndices']}));return
        # Multiplicative pressure on hard rows. Bound ratios to avoid overflow.
        weights[unc]*=1.035
        weights=np.minimum(weights,50.0)
        if starts%17==16:weights=1.0+0.85*(weights-1.0)
        # Include columns good on currently hardest rows in exact-search pool.
        hard=unc[np.argsort(weights[unc])[-min(len(unc),40):]] if len(unc) else []
        hmask=np.zeros(nrows,dtype=bool);hmask[hard]=True
        scores=[]
        for j,rows in enumerate(colrows):
            scores.append(float(weights[rows[hmask[rows]]].sum()))
        top=np.argpartition(np.asarray(scores),-min(120,ncols))[-min(120,ncols):]
        pool.update(map(int,top))
        starts+=1

    # Exact phase 1: rich candidate pool around every heuristic near-cover.
    if best_sel:pool.update(best_sel)
    # Ensure every row has candidate support; add up to four globally useful
    # columns for any row currently absent from the pool.
    pool=set(pool)
    for r,R in enumerate(rowsets):
        if not (R&pool):
            candidates=sorted(R,key=lambda j:len(colrows[j]),reverse=True)[:4]
            pool.update(candidates)
    candidate_cols=sorted(pool)
    print(json.dumps({'heuristicStarts':starts,'bestUncovered':best_unc,'candidatePool':len(candidate_cols)},sort_keys=True),flush=True)

    def solve(cols,seconds,hint=None):
        pos={j:q for q,j in enumerate(cols)};M=cp_model.CpModel();x=[M.NewBoolVar(f'x{q}') for q in range(len(cols))]
        for R in rowsets:
            qs=[pos[j] for j in R if j in pos]
            if not qs:return 'INFEASIBLE',None,0,0
            M.AddBoolOr([x[q] for q in qs])
        M.Add(sum(x)==K)
        if hint:
            hs=set(hint)
            for q,j in enumerate(cols):M.AddHint(x[q],1 if j in hs else 0)
        C=cp_model.CpSolver();C.parameters.max_time_in_seconds=seconds;C.parameters.num_search_workers=8
        C.parameters.cp_model_presolve=True;C.parameters.symmetry_level=3;C.parameters.linearization_level=2
        C.parameters.random_seed=SEED%2147483647;C.parameters.randomize_search=True
        st=C.Solve(M);name=C.StatusName(st)
        if name in ('OPTIMAL','FEASIBLE'):
            w=[cols[q] for q in range(len(cols)) if C.Value(x[q])]
            assert exact_verify(w,rowsets);return name,sorted(w),int(C.NumBranches()),int(C.NumConflicts())
        return name,None,int(C.NumBranches()),int(C.NumConflicts())

    remaining=max(120.0,1500.0-(time.time()-(deadline-900.0)))
    st,w,br,cf=solve(candidate_cols,min(600.0,remaining),best_sel)
    solver_records=[{'scope':'heuristic-candidate-pool','columns':len(candidate_cols),'status':st,'branches':br,'conflicts':cf}]
    if w is not None:
        result='K14_FEASIBLE'
    else:
        # Exact full instance with the near-cover as a warm hint.  UNKNOWN is
        # explicitly non-evidence; FEASIBLE is independently verified above.
        st2,w2,br2,cf2=solve(list(range(ncols)),min(600.0,max(60.0,remaining-600.0)),best_sel)
        solver_records.append({'scope':'full-5294','columns':ncols,'status':st2,'branches':br2,'conflicts':cf2})
        w=w2;result='K14_FEASIBLE' if w is not None else 'UNKNOWN'

    out={'schema':'holotrade.depth5-k14-constructive-witness.v1','valid':True,'result':result,
         'heuristicStarts':starts,'bestHeuristicUncoveredRows':int(best_unc),
         'bestHeuristicSelection':best_sel,'candidatePoolColumns':len(candidate_cols),
         'solverRecords':solver_records,'witnessLeafOrbitIndices':w,
         'certifiedIntervalUpdate':([14,14] if w is not None else [14,22]),
         'theorem':('The explicit fourteen-column witness covers every one of the 6,128 distinct exact constraints; together with the frozen K13 infeasibility certificate this proves tau_5=14.' if w is not None else 'No 14-cover was found by this construction-first search. UNKNOWN is not an infeasibility certificate and does not improve the certified interval.'),
         'boundary':'Heuristic scores, near-covers, and UNKNOWN CP-SAT searches are discovery information only. Only an explicit witness verified against all exact constraints upgrades the theorem.'}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'valid':True,'result':result,'bestUncovered':best_unc,'pool':len(candidate_cols),'interval':out['certifiedIntervalUpdate']},sort_keys=True))

if __name__=='__main__':main()
