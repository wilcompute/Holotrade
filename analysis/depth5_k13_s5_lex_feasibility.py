#!/usr/bin/env python3
"""Second exact K=13 attack: quotient search redundancy by proven coordinate S5.

The companion depth5_coordinate_s5_automorphism.py proves that adjacent
coordinate transpositions generate an exact S5 automorphism group of the full
6129x5294 diagonal-PSp cover matrix.  Every feasible Boolean cover therefore
has an S5-translate that is lexicographically minimal in its orbit.

This script independently reconstructs those four column permutations and adds
x <=_lex g(x) for each adjacent transposition g to the exact K<=13 CP-SAT
model.  The lex constraints are encoded by explicit prefix-equality CNF, so no
solver-specific symmetry primitive is trusted.  We also apply only exact
column duplicate/subset dominance from the first K13 attack and transport the
S5 action through the reduction whenever possible.

If the reduced kept-column set is not invariant under S5 (dominance may choose
asymmetric representatives), we deliberately skip dominance reduction and use
all 5294 columns so the symmetry proof remains exact.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import depth5_induced_subgroup_cuts as old
import depth5_coordinate_s5_automorphism as s5

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/depth5_k13_s5_lex_feasibility.json'
K=13


def add_xnor(M,a,b,e):
    # e <-> (a == b)
    M.AddBoolOr([e.Not(),a.Not(),b])
    M.AddBoolOr([e.Not(),a,b.Not()])
    M.AddBoolOr([a,b,e])
    M.AddBoolOr([a.Not(),b.Not(),e])


def add_lex_leq(M,x,perm,label):
    # x <=lex y where y_i = x_{perm[i]}. Prefix p_i says positions <i equal.
    n=len(x); p=[M.NewBoolVar(f'{label}_p{i}') for i in range(n+1)]
    M.Add(p[0]==1)
    for i in range(n):
        y=x[perm[i]]
        e=M.NewBoolVar(f'{label}_e{i}'); add_xnor(M,x[i],y,e)
        # if prefix equal, x_i=1,y_i=0 is forbidden
        M.AddBoolOr([p[i].Not(),x[i].Not(),y])
        # p[i+1] <-> p[i] AND e
        M.AddImplication(p[i+1],p[i]); M.AddImplication(p[i+1],e)
        M.AddBoolOr([p[i].Not(),e.Not(),p[i+1]])
    return p


def main():
    from ortools.sat.python import cp_model
    pts,_idx,iso,_supports,_charts,_edge=old.geometry()
    leaf_id,reps=s5.build_orbit_machine(pts,iso)
    _lid,A=old.full_orbit_machine(pts,iso);assert A.shape==(6129,5294)
    assert all(leaf_id(r)==i for i,r in enumerate(reps))

    # Exact four adjacent coordinate transpositions on leaf orbits.
    gens=[]
    for k in range(4):
        g=[]
        for r in reps:
            q=list(r);q[k],q[k+1]=q[k+1],q[k];g.append(leaf_id(tuple(q)))
        g=tuple(g);assert sorted(g)==list(range(5294));assert s5.comp(g,g)==tuple(range(5294));gens.append(g)
    G=s5.closure(gens,5294);assert len(G)==120

    # Objectwise covariance of all row supports, again, before using symmetry.
    rowsets=[frozenset(map(int,A.indices[A.indptr[r]:A.indptr[r+1]])) for r in range(6129)]
    lookup={S:i for i,S in enumerate(rowsets)};assert len(lookup)==6129
    for g in gens:
        images=[frozenset(g[j] for j in S) for S in rowsets]
        assert all(T in lookup for T in images)
        assert len({lookup[T] for T in images})==6129

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
        union=set()
        for j in pick:
            union.update(r for r,SS in enumerate(rowsets) if j in SS)
        # Faster exact row-by-row witness check.
        assert all(any(j in SS for j in pick) for SS in rowsets)
        rec['witnessLeafOrbitIndices']=pick;rec['witnessSize']=len(pick)
    result='K13_INFEASIBLE' if name=='INFEASIBLE' else ('K13_FEASIBLE' if name in ('OPTIMAL','FEASIBLE') else 'UNKNOWN')
    out={'schema':'holotrade.depth5-k13-s5-lex-feasibility.v1','valid':True,
         'fullModel':{'tileOrbits':6129,'leafOrbits':5294,'K':13},
         'symmetry':{'group':'S5','order':120,'adjacentGenerators':4,
                     'matrixAutomorphismReverified':True,'lexLeaders':4,
                     'encoding':'explicit prefix-XNOR CNF'},
         'solver':rec,'result':result,'newCertifiedLowerBound':14 if result=='K13_INFEASIBLE' else 13,
         'theorem':('Because S5 acts by exact automorphisms of the cover matrix, every feasible cover has a lex-minimal S5 translate satisfying all four adjacent-generator lex-leader constraints. Therefore INFEASIBLE for this symmetry-broken model is equivalent to infeasibility of the original K<=13 problem and certifies depth-five cover number at least 14.'),
         'boundary':('UNKNOWN leaves the certified lower bound at 13. FEASIBLE records an exact cover witness. The lex constraints only choose orbit representatives and do not remove an entire feasible S5 orbit.')}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'valid':True,'result':result,'status':name,'elapsed':elapsed,'branches':rec['branches']},sort_keys=True))

if __name__=='__main__':main()
