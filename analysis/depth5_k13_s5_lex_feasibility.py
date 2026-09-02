#!/usr/bin/env python3
"""Exact K=13 attack with theorem-safe coordinate S5 lex leaders.

Distinct PSp tile orbits can induce identical set-cover rows.  Duplicate rows
are removed exactly before solving.  The companion S5 audit proves coordinate
S5 on this distinct constraint family; this script independently rechecks the
same covariance before adding explicit lex leaders.
"""
from __future__ import annotations

import collections
import json
import time
from pathlib import Path

import depth5_induced_subgroup_cuts as old
import depth5_coordinate_s5_automorphism as s5

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/depth5_k13_s5_lex_feasibility.json'
K=13


def add_xnor(M,a,b,e):
    M.AddBoolOr([e.Not(),a.Not(),b])
    M.AddBoolOr([e.Not(),a,b.Not()])
    M.AddBoolOr([a,b,e])
    M.AddBoolOr([a.Not(),b.Not(),e])


def add_lex_leq(M,x,perm,label):
    n=len(x);p=[M.NewBoolVar(f'{label}_p{i}') for i in range(n+1)];M.Add(p[0]==1)
    for i in range(n):
        y=x[perm[i]];e=M.NewBoolVar(f'{label}_e{i}');add_xnor(M,x[i],y,e)
        M.AddBoolOr([p[i].Not(),x[i].Not(),y])
        M.AddImplication(p[i+1],p[i]);M.AddImplication(p[i+1],e)
        M.AddBoolOr([p[i].Not(),e.Not(),p[i+1]])


def main():
    from ortools.sat.python import cp_model
    pts,_idx,iso,_supports,_charts,_edge=old.geometry()
    leaf_id,reps=s5.build_orbit_machine(pts,iso)
    _lid,A=old.full_orbit_machine(pts,iso);assert A.shape==(6129,5294)
    assert all(leaf_id(r)==i for i,r in enumerate(reps))

    gens=[]
    for k in range(4):
        g=[]
        for r in reps:
            q=list(r);q[k],q[k+1]=q[k+1],q[k];g.append(leaf_id(tuple(q)))
        g=tuple(g);assert sorted(g)==list(range(5294));assert s5.comp(g,g)==tuple(range(5294));gens.append(g)
    G=s5.closure(gens,5294);assert len(G)==120

    raw=[frozenset(map(int,A.indices[A.indptr[r]:A.indptr[r+1]])) for r in range(6129)]
    mult=collections.Counter(raw)
    rowsets=sorted(mult,key=lambda S:(len(S),tuple(sorted(S))))
    lookup=set(rowsets)
    for g in gens:
        assert all(frozenset(g[j] for j in S) in lookup for S in rowsets)

    M=cp_model.CpModel();x=[M.NewBoolVar(f'x{j}') for j in range(5294)]
    for S in rowsets:M.AddBoolOr([x[j] for j in S])
    M.Add(sum(x)<=K)
    for k,g in enumerate(gens):add_lex_leq(M,x,g,f's{k}{k+1}')

    S=cp_model.CpSolver();S.parameters.max_time_in_seconds=1500;S.parameters.num_search_workers=8
    S.parameters.symmetry_level=3;S.parameters.cp_model_presolve=True;S.parameters.linearization_level=2
    S.parameters.log_search_progress=True
    t=time.time();st=S.Solve(M);elapsed=time.time()-t;name=S.StatusName(st)
    rec={'engine':'CP-SAT','status':name,'elapsedSeconds':elapsed,'conflicts':int(S.NumConflicts()),
         'branches':int(S.NumBranches())}
    if name in ('OPTIMAL','FEASIBLE'):
        pick=[j for j in range(5294) if S.Value(x[j])];assert len(pick)<=K
        assert all(any(j in SS for j in pick) for SS in rowsets)
        rec['witnessLeafOrbitIndices']=pick;rec['witnessSize']=len(pick)
    result='K13_INFEASIBLE' if name=='INFEASIBLE' else ('K13_FEASIBLE' if name in ('OPTIMAL','FEASIBLE') else 'UNKNOWN')
    out={'schema':'holotrade.depth5-k13-s5-lex-feasibility.v2','valid':True,
         'fullModel':{'originalTileOrbits':6129,'distinctConstraintRows':len(rowsets),
                      'duplicateRowsRemoved':6129-len(rowsets),'leafOrbits':5294,'K':13},
         'constraintMultiplicityHistogram':{str(k):v for k,v in sorted(collections.Counter(mult.values()).items())},
         'symmetry':{'group':'S5','order':120,'adjacentGenerators':4,
                     'constraintFamilyAutomorphismReverified':True,'lexLeaders':4,
                     'encoding':'explicit prefix-XNOR CNF'},
         'solver':rec,'result':result,'newCertifiedLowerBound':14 if result=='K13_INFEASIBLE' else 13,
         'theorem':('Duplicate cover rows are logically redundant. Coordinate S5 acts exactly on the remaining constraint family, and every feasible cover has an S5 translate satisfying the explicit lex leaders. Therefore INFEASIBLE is equivalent to infeasibility of the original K<=13 cover problem and certifies a lower bound of 14.'),
         'boundary':('UNKNOWN leaves the lower bound at 13. FEASIBLE records an exact witness. No tile-orbit-label permutation is inferred from duplicate row supports.')}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'valid':True,'result':result,'status':name,'distinctRows':len(rowsets),
                      'duplicateRows':6129-len(rowsets),'elapsed':elapsed,'branches':rec['branches']},sort_keys=True))

if __name__=='__main__':main()
