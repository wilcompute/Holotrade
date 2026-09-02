#!/usr/bin/env python3
"""Strong-fixing attack on the exact depth-five K=13 set-cover frontier.

For a fixed selected leaf-orbit column j, the rows already covered by j vanish
and j itself cannot be selected again.  The residual problem must therefore be
covered by at most 12 other columns.  Its LP dual is

    maximize 1^T y
    subject B_j^T y <= 1, y >= 0,

where B_j is the incidence matrix restricted to rows NOT covered by j and to
columns k != j.  If any exactly verified feasible dual has value > 12, then
no 13-cover can contain j.

The exact coordinate-S5 theorem reduces 5,294 columns to 94 column orbits, so
we solve at most 94 such residual duals.  Each numerical HiGHS solution is
rounded DOWN to a fixed rational grid and its dual feasibility is reverified
with integer arithmetic before it can fix an orbit.  Whole S5 orbits are fixed
at once.

If all 94 orbits are fixed, K=13 is impossible and the certified depth-five
lower bound rises to 14 without integer branch-and-bound.  Otherwise the
surviving orbit union is passed to an exact CP-SAT residual model as a second
line of attack.
"""
from __future__ import annotations

import collections
import json
import time
from pathlib import Path

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix

import depth5_induced_subgroup_cuts as old
import depth5_coordinate_s5_automorphism as s5

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/depth5_k13_strong_dual_fixing.json'
D=10_000_000
K=13


def exact_loads_for_residual(R, yint):
    C=R.tocsc(); out=[]
    for j in range(C.shape[1]):
        rr=C.indices[C.indptr[j]:C.indptr[j+1]]
        out.append(sum(int(yint[int(r)]) for r in rr))
    return out


def make_s5_orbits(gens,n):
    G=s5.closure(gens,n);assert len(G)==120
    unseen=set(range(n));orbits=[]
    while unseen:
        j=min(unseen);O=sorted({g[j] for g in G});unseen.difference_update(O);orbits.append(O)
    assert len(orbits)==94
    return G,orbits


def main():
    from ortools.sat.python import cp_model

    pts,_idx,iso,_supports,_charts,_edge=old.geometry()
    leaf_id,reps=s5.build_orbit_machine(pts,iso)
    _leaf,A=old.full_orbit_machine(pts,iso);assert A.shape==(6129,5294)
    assert all(leaf_id(r)==i for i,r in enumerate(reps))

    # Exact logical row family: remove the one known duplicate constraint.
    raw=[frozenset(map(int,A.indices[A.indptr[r]:A.indptr[r+1]])) for r in range(A.shape[0])]
    rowsets=sorted(set(raw),key=lambda S:(len(S),tuple(sorted(S))))
    assert len(rowsets)==6128
    rr=[];cc=[]
    for i,S in enumerate(rowsets):
        for j in S:rr.append(i);cc.append(j)
    B=csr_matrix((np.ones(len(rr),dtype=np.int8),(rr,cc)),shape=(len(rowsets),5294))

    # Reconstruct exact coordinate S5 on columns and verify covariance again.
    gens=[]
    for q in range(4):
        g=[]
        for r in reps:
            z=list(r);z[q],z[q+1]=z[q+1],z[q];g.append(leaf_id(tuple(z)))
        g=tuple(g);assert sorted(g)==list(range(5294));assert s5.comp(g,g)==tuple(range(5294));gens.append(g)
    G,orbits=make_s5_orbits(gens,5294)
    lookup=set(rowsets)
    for g in gens:assert all(frozenset(g[j] for j in S) in lookup for S in rowsets)

    fixed_orbits=[];surviving_orbits=[];records=[];certificates=[]
    t_all=time.time()
    allcols=np.arange(5294,dtype=np.int32)
    for oi,O in enumerate(orbits):
        j=O[0]
        covered=np.fromiter((j in S for S in rowsets),dtype=bool,count=len(rowsets))
        uncovered=np.flatnonzero(~covered)
        keepcols=allcols[allcols!=j]
        R=B[uncovered,:][:,keepcols].tocsr()
        # Maximize sum y == minimize -sum y.
        lp=linprog(-np.ones(len(uncovered)),A_ub=R.T,b_ub=np.ones(len(keepcols)),
                   bounds=(0,None),method='highs')
        assert lp.success
        yf=np.maximum(np.asarray(lp.x,dtype=float),0.0)
        yint=np.floor(yf*D).astype(np.int64)
        loads=exact_loads_for_residual(R,yint);mx=max(loads) if loads else 0
        if mx>D:
            # Uniform exact downward scaling; reverify after scaling.
            yint=(yint*(D-1)//mx).astype(np.int64)
            loads=exact_loads_for_residual(R,yint);mx=max(loads) if loads else 0
        assert min(yint,default=0)>=0 and mx<=D
        score=int(yint.sum())
        fixed=score>12*D
        rec={'orbitIndex':oi,'representativeColumn':j,'orbitSize':len(O),
             'coveredRowsByRepresentative':int(covered.sum()),'residualRows':len(uncovered),
             'floatingResidualLP':float(-lp.fun),'exactDualNumerator':score,
             'exactDualValue':score/D,'maxResidualColumnLoadNumerator':mx,
             'fixedForK13':fixed}
        records.append(rec)
        if fixed:
            fixed_orbits.append(oi)
            # Store only nonzero residual weights, indexed by original distinct-row id.
            nz=np.flatnonzero(yint)
            certificates.append({'orbitIndex':oi,'representativeColumn':j,
                                 'weights':[[int(uncovered[t]),int(yint[t])] for t in nz]})
        else:
            surviving_orbits.append(oi)
        print(json.dumps({'orbit':oi,'rep':j,'size':len(O),'dual':score/D,'fixed':fixed,
                          'fixedCount':len(fixed_orbits),'survivors':len(surviving_orbits)},sort_keys=True),flush=True)

    surviving_columns=sorted(j for oi in surviving_orbits for j in orbits[oi])
    fixed_columns=5294-len(surviving_columns)
    result='UNKNOWN';solver={'status':'NOT_RUN'}
    if not surviving_columns:
        result='K13_INFEASIBLE'
        solver={'status':'SKIPPED_ALL_COLUMNS_STRONGLY_FIXED'}
    else:
        # Exact residual SAT after theorem-safe strong fixing.
        pos={j:q for q,j in enumerate(surviving_columns)}
        projected=[];empty=[]
        for i,S in enumerate(rowsets):
            T=frozenset(pos[j] for j in S if j in pos)
            if not T:empty.append(i)
            projected.append(T)
        if empty:
            result='K13_INFEASIBLE';solver={'status':'SKIPPED_EMPTY_ROW_AFTER_STRONG_FIXING','emptyRows':empty}
        else:
            # Delete duplicate and weaker superset constraints exactly.
            uniq=sorted(set(projected),key=lambda S:(len(S),tuple(sorted(S))))
            minimal=[];bits=[]
            for S in uniq:
                b=0
                for q in S:b|=1<<q
                if any(tb & ~b == 0 for tb in bits):continue
                minimal.append(S);bits.append(b)
            M=cp_model.CpModel();x=[M.NewBoolVar(f'x{q}') for q in range(len(surviving_columns))]
            for S in minimal:M.AddBoolOr([x[q] for q in S])
            M.Add(sum(x)==13)
            C=cp_model.CpSolver();C.parameters.max_time_in_seconds=1500;C.parameters.num_search_workers=8
            C.parameters.symmetry_level=3;C.parameters.cp_model_presolve=True;C.parameters.linearization_level=2
            C.parameters.log_search_progress=True
            t=time.time();st=C.Solve(M);name=C.StatusName(st)
            solver={'status':name,'elapsedSeconds':time.time()-t,'branches':int(C.NumBranches()),
                    'conflicts':int(C.NumConflicts()),'minimalResidualRows':len(minimal)}
            if name=='INFEASIBLE':result='K13_INFEASIBLE'
            elif name in ('OPTIMAL','FEASIBLE'):
                pick=[surviving_columns[q] for q in range(len(x)) if C.Value(x[q])]
                assert len(pick)==13 and all(any(j in S for j in pick) for S in rowsets)
                solver['witnessLeafOrbitIndices']=pick;result='K13_FEASIBLE'

    out={'schema':'holotrade.depth5-k13-strong-dual-fixing.v1','valid':True,
         'original':{'tileOrbitRows':6129,'distinctConstraintRows':6128,'leafOrbitColumns':5294,'K':13},
         'symmetry':{'group':'S5','order':120,'columnOrbitCount':94,
                     'wholeOrbitFixingVerifiedByCovariance':True},
         'certificateDenominator':D,'orbitRecords':records,'exactDualCertificates':certificates,
         'strongFixing':{'fixedOrbitCount':len(fixed_orbits),'survivingOrbitCount':len(surviving_orbits),
                         'fixedColumnCount':fixed_columns,'survivingColumnCount':len(surviving_columns),
                         'fixedOrbitIndices':fixed_orbits,'survivingOrbitIndices':surviving_orbits,
                         'survivingOriginalLeafOrbitIndices':surviving_columns},
         'solver':solver,'result':result,'newCertifiedLowerBound':14 if result=='K13_INFEASIBLE' else 13,
         'elapsedTotalSeconds':time.time()-t_all,
         'theorem':('For each strongly fixed S5 orbit representative j, the stored nonnegative rational vector is an exact feasible dual for the residual set-cover problem obtained after selecting j: rows already covered by j are deleted and column j is unavailable. Its objective exceeds 12, so every cover containing j has size at least 14. Exact S5 covariance transfers this exclusion to the whole orbit. If no orbit survives, or if the exact residual model is infeasible, no 13-cover exists.'),
         'boundary':('Floating HiGHS solutions are discovery aids only. Every fixing certificate is rounded downward and residual dual feasibility is verified with integer arithmetic. Any orbit with certified dual <=12 is left alive; that is not evidence of a 13-cover.')}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'valid':True,'result':result,'fixedOrbits':len(fixed_orbits),
                      'survivingOrbits':len(surviving_orbits),'fixedColumns':fixed_columns,
                      'survivingColumns':len(surviving_columns),'solver':solver['status']},sort_keys=True),flush=True)

if __name__=='__main__':main()
