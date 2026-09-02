#!/usr/bin/env python3
"""Exact K=14 attack recycling the frozen K=13 strong-fixing duals.

The K=13 certificate strongly fixes 88/94 S5 column orbits and leaves 105
columns, but those 105 columns miss at least one exact cover row.  Hence every
cover of any size must contain a column from one of the 88 fixed S5 orbits.
By S5 covariance, for a K=14 cover we may move such a selected column to the
stored representative j of its orbit.

For that representative the frozen certificate is an exact feasible residual
dual y_j with score Y_j > 12 after selecting j.  If a second selected column k
covers dual weight w_j(k), the same dual restricted to rows uncovered by both
j and k remains feasible with score Y_j-w_j(k).  A 14-cover has only 12 columns
left after j,k, so necessarily

    Y_j - w_j(k) <= 12.

Thus k is theorem-safely forbidden in the j-branch whenever the strict reverse
inequality holds.  This produces 88 exact pair-compatibility kernels without
solving any new LP.  Empty-row kernels prove a branch impossible immediately;
remaining branches are handed to CP-SAT only after all exact reductions.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix

import depth5_induced_subgroup_cuts as old
import depth5_coordinate_s5_automorphism as s5

ROOT=Path(__file__).resolve().parents[1]
IN=ROOT/'data/depth5_k13_strong_dual_fixing.json'
OUT=ROOT/'data/depth5_k14_recycled_dual_pair_kernel.json'
D=10_000_000
K=14


def make_orbits(gens,n):
    G=s5.closure(gens,n); assert len(G)==120
    unseen=set(range(n)); out=[]
    while unseen:
        j=min(unseen); O=sorted({g[j] for g in G}); unseen.difference_update(O); out.append(O)
    assert len(out)==94
    return G,out


def main():
    from ortools.sat.python import cp_model

    frozen=json.loads(IN.read_text())
    assert frozen['valid'] is True and frozen['result']=='K13_INFEASIBLE'
    assert frozen['certificateDenominator']==D
    sf=frozen['strongFixing']
    assert sf['fixedOrbitCount']==88 and sf['survivingOrbitCount']==6
    assert sf['fixedColumnCount']==5189 and sf['survivingColumnCount']==105
    assert frozen['solver']['status']=='SKIPPED_EMPTY_ROW_AFTER_STRONG_FIXING'

    pts,_idx,iso,_supports,_charts,_edge=old.geometry()
    leaf_id,reps=s5.build_orbit_machine(pts,iso)
    _leaf,A=old.full_orbit_machine(pts,iso); assert A.shape==(6129,5294)
    assert all(leaf_id(r)==i for i,r in enumerate(reps))

    raw=[frozenset(map(int,A.indices[A.indptr[r]:A.indptr[r+1]])) for r in range(A.shape[0])]
    rowsets=sorted(set(raw),key=lambda S:(len(S),tuple(sorted(S))))
    assert len(rowsets)==6128
    rr=[]; cc=[]
    for i,S in enumerate(rowsets):
        for j in S: rr.append(i); cc.append(j)
    B=csr_matrix((np.ones(len(rr),dtype=np.int8),(rr,cc)),shape=(6128,5294),dtype=np.int64)

    gens=[]
    for q in range(4):
        g=[]
        for r in reps:
            z=list(r); z[q],z[q+1]=z[q+1],z[q]; g.append(leaf_id(tuple(z)))
        g=tuple(g); assert sorted(g)==list(range(5294)); gens.append(g)
    G,orbits=make_orbits(gens,5294)
    assert [len(O) for O in orbits]==[r['orbitSize'] for r in frozen['orbitRecords']]

    # The survivor-only family cannot cover even a single exact row, so every
    # K=14 cover contains a strongly-fixed type and is represented by one of
    # the 88 branches below.
    survivor_cols=set(sf['survivingOriginalLeafOrbitIndices'])
    survivor_empty=[i for i,S in enumerate(rowsets) if not (S & survivor_cols)]
    assert survivor_empty

    cert_by_oi={c['orbitIndex']:c for c in frozen['exactDualCertificates']}
    rec_by_oi={r['orbitIndex']:r for r in frozen['orbitRecords']}
    fixed_ois=list(sf['fixedOrbitIndices'])
    assert set(fixed_ois)==set(cert_by_oi)

    branch_records=[]
    candidates=[]
    for oi in fixed_ois:
        O=orbits[oi]; j=O[0]; rec=rec_by_oi[oi]; cert=cert_by_oi[oi]
        assert rec['representativeColumn']==j and cert['representativeColumn']==j
        score=int(rec['exactDualNumerator']); assert score>12*D
        y=np.zeros(6128,dtype=np.int64)
        for r,w in cert['weights']: y[int(r)]=int(w)
        assert int(y.sum())==score
        loads=np.asarray(B.T.dot(y),dtype=np.int64).reshape(-1)
        # j covers none of the residual-dual support by construction.
        assert int(loads[j])==0
        need=score-12*D
        allowed=np.flatnonzero(loads>=need).astype(int).tolist()
        allowed=[k for k in allowed if k!=j]
        aset=set(allowed)
        uncovered_rows=[r for r,S in enumerate(rowsets) if j not in S]
        empty=[r for r in uncovered_rows if not (rowsets[r] & aset)]
        br={'orbitIndex':oi,'representativeColumn':j,'orbitSize':len(O),
            'dualNumerator':score,'dualValue':score/D,
            'requiredSecondColumnDualMassNumerator':need,
            'allowedSecondColumns':len(allowed),'forbiddenSecondColumns':5293-len(allowed),
            'residualRowsAfterFirst':len(uncovered_rows),'emptyRowsAfterPairKernel':empty[:32],
            'emptyRowCount':len(empty)}
        branch_records.append(br)
        if not empty and len(allowed)>=13:
            candidates.append((len(allowed),oi,j,allowed,uncovered_rows))
        print(json.dumps({'orbit':oi,'rep':j,'allowed':len(allowed),'emptyRows':len(empty)},sort_keys=True),flush=True)

    candidates.sort()
    result='UNKNOWN'
    solver_records=[]
    witness=None
    if not candidates:
        result='K14_INFEASIBLE'
    else:
        # Search smallest exact kernels first.  A feasible branch immediately
        # proves tau5=14 because K=13 is already certified impossible.
        deadline=time.time()+1500.0
        for _,oi,j,allowed,uncovered_rows in candidates:
            remain=max(1.0,deadline-time.time())
            if remain<=1.0: break
            pos={k:q for q,k in enumerate(allowed)}
            projected=[]; impossible=False
            for r in uncovered_rows:
                S=[pos[k] for k in rowsets[r] if k in pos]
                if not S: impossible=True; break
                projected.append(frozenset(S))
            if impossible: continue
            # Deduplicate and remove weaker supersets.
            uniq=sorted(set(projected),key=lambda S:(len(S),tuple(sorted(S))))
            minimal=[]; bits=[]
            for S in uniq:
                b=0
                for q in S: b|=1<<q
                if any(tb & ~b == 0 for tb in bits): continue
                minimal.append(S); bits.append(b)
            M=cp_model.CpModel(); x=[M.NewBoolVar(f'x{q}') for q in range(len(allowed))]
            for S in minimal: M.AddBoolOr([x[q] for q in S])
            M.Add(sum(x)==13)
            C=cp_model.CpSolver(); C.parameters.max_time_in_seconds=min(180.0,remain)
            C.parameters.num_search_workers=8; C.parameters.symmetry_level=3
            C.parameters.cp_model_presolve=True; C.parameters.linearization_level=2
            t=time.time(); st=C.Solve(M); name=C.StatusName(st)
            sr={'orbitIndex':oi,'representativeColumn':j,'allowedColumns':len(allowed),
                'minimalResidualRows':len(minimal),'status':name,'elapsedSeconds':time.time()-t,
                'branches':int(C.NumBranches()),'conflicts':int(C.NumConflicts())}
            solver_records.append(sr)
            print(json.dumps(sr,sort_keys=True),flush=True)
            if name in ('OPTIMAL','FEASIBLE'):
                pick=[allowed[q] for q in range(len(x)) if C.Value(x[q])]
                full=[j]+pick
                assert len(full)==14 and len(set(full))==14
                assert all(any(k in S for k in full) for S in rowsets)
                witness=full; result='K14_FEASIBLE'; break
        else:
            if len(solver_records)==len(candidates) and all(r['status']=='INFEASIBLE' for r in solver_records):
                result='K14_INFEASIBLE'

    out={'schema':'holotrade.depth5-k14-recycled-dual-pair-kernel.v1','valid':True,
         'basisCertificate':{'path':'data/depth5_k13_strong_dual_fixing.json',
                             'k13Result':'K13_INFEASIBLE','k13CertifiedLowerBound':14},
         'symmetry':{'group':'S5','order':120,'columnOrbitCount':94},
         'survivorOnlyEmptyRows':survivor_empty,
         'fixedOrbitBranchCount':len(fixed_ois),'pairKernelRecords':branch_records,
         'branchesNeedingIntegerSearch':len(candidates),'solverRecords':solver_records,
         'result':result,'witnessLeafOrbitIndices':witness,
         'certifiedIntervalUpdate':([14,14] if result=='K14_FEASIBLE' else ([15,22] if result=='K14_INFEASIBLE' else [14,22])),
         'theorem':('Every cover must use one of the 88 K13-strongly-fixed S5 orbit types because the 105 K13 survivors leave exact rows uncovered. Move such a selected column to its orbit representative j. For the stored exact residual dual y_j, a second selected column k must remove at least Y_j-12 dual mass; otherwise the same restricted dual proves that the remaining residual needs at least 13 columns, forcing total cover size at least 15. Therefore every pair-kernel deletion is exact.'),
         'boundary':('The recycled-dual pair test is necessary, not sufficient, for a K14 cover. UNKNOWN solver branches do not improve the lower bound beyond 14. Only an explicit verified 14-cover or exhaustive infeasibility of all exact S5 branches closes K14.')}
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'valid':True,'result':result,'candidateBranches':len(candidates),
                      'solverBranchesRun':len(solver_records),'interval':out['certifiedIntervalUpdate']},sort_keys=True),flush=True)

if __name__=='__main__': main()
