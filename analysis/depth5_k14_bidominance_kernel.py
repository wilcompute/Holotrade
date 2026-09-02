#!/usr/bin/env python3
"""Exact row/column bi-dominance kernel for the depth-five K=14 frontier.

Earlier exact passes used duplicate/dominated ROW elimination but did not exploit
the dual unweighted set-cover rule on columns:

  if residual support C_a is a subset of C_b, then column a is dominated by b
  and may be deleted.

For each of the 88 exhaustive S5-normalized first-column branches from the K13
strong-fixing theorem, this pass:
  1. selects the normalized first column;
  2. reapplies its frozen exact rational dual certificate;
  3. alternates duplicate/dominated row elimination, exact column dominance,
     and singleton-row forcing;
  4. gives the theorem-safe kernel to CP-SAT.

All columns have unit cost, so column dominance is exact. UNKNOWN has no theorem
consequence.  An explicit verified 14-cover proves tau_5=14; exhaustive closure
of all 88 first-column branches proves tau_5>=15.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

import depth5_induced_subgroup_cuts as old
import depth5_coordinate_s5_automorphism as s5

ROOT=Path(__file__).resolve().parents[1]
K13=ROOT/'data/depth5_k13_strong_dual_fixing.json'
OUT=ROOT/'data/depth5_k14_bidominance_kernel.json'
D=10_000_000
GLOBAL_SECONDS=4200.0
SAT_SECONDS=75.0
MAX_ROUNDS=4


def make_orbits(gens,n):
    G=s5.closure(gens,n); assert len(G)==120
    unseen=set(range(n)); out=[]
    while unseen:
        j=min(unseen); O=sorted({g[j] for g in G}); unseen.difference_update(O); out.append(O)
    assert len(out)==94
    return G,out


def minimal_rows(row_ids,rowsets,active):
    active=set(active); uniq={}; empty=[]
    for r in row_ids:
        S=frozenset(rowsets[r]&active)
        if not S: empty.append(r)
        else: uniq.setdefault(S,r)
    if empty: return [],empty,{'before':len(row_ids),'distinct':len(uniq),'after':0}
    ordered=sorted(uniq.items(),key=lambda z:(len(z[0]),tuple(sorted(z[0]))))
    kept=[]; kept_sets=[]
    for S,r in ordered:
        if any(T.issubset(S) for T in kept_sets): continue
        kept_sets.append(S); kept.append(r)
    return kept,[],{'before':len(row_ids),'distinct':len(uniq),'after':len(kept)}


def dominated_columns(row_ids,rowsets,active):
    """Return exact dominated/duplicate columns using Python-int row bitsets."""
    active=set(active); m=len(row_ids)
    bits={j:0 for j in active}
    for q,r in enumerate(row_ids):
        b=1<<q
        for j in rowsets[r]&active: bits[j] |= b

    empty={j for j,v in bits.items() if v==0}
    active-=empty
    # Identical supports: keep the least index, all others are dominated copies.
    sig={}; duplicates=set()
    for j in sorted(active):
        v=bits[j]
        if v in sig: duplicates.add(j)
        else: sig[v]=j
    active-=duplicates

    # Process large supports first. For a candidate S, any dominator has already
    # been retained. Index retained supersets by rows they contain and test only
    # the shortest anchor list.
    order=sorted(active,key=lambda j:(-bits[j].bit_count(),j))
    kept=[]; by_row=[[] for _ in range(m)]; dom=set()
    for j in order:
        v=bits[j]
        # choose a covered row with the fewest existing retained supersets
        vv=v; anchors=[]
        while vv:
            lsb=vv & -vv; q=lsb.bit_length()-1; anchors.append(q); vv-=lsb
        candidates=[] if not anchors else by_row[min(anchors,key=lambda q:len(by_row[q]))]
        hit=False
        for k in candidates:
            vk=bits[k]
            if v & ~vk == 0:
                dom.add(j); hit=True; break
        if hit: continue
        kept.append(j)
        for q in anchors: by_row[q].append(j)
    return set(kept), {'before':len(bits),'empty':len(empty),'duplicates':len(duplicates),'properDominated':len(dom),'after':len(kept)}


def force_singletons(row_ids,rowsets,active,budget,forced):
    active=set(active); row_ids=list(row_ids); forced=list(forced); made=[]
    while True:
        singles=[]
        for r in row_ids:
            S=rowsets[r]&active
            if not S: return row_ids,active,budget,forced,made,[r]
            if len(S)==1: singles.append((next(iter(S)),r))
        if not singles: return row_ids,active,budget,forced,made,[]
        j,_r=min(singles)
        forced.append(j); made.append(j); budget-=1
        if budget<0: return row_ids,active,budget,forced,made,[-1]
        row_ids=[r for r in row_ids if j not in rowsets[r]]
        active.discard(j)
        if not row_ids: return row_ids,active,budget,forced,made,[]


def verify(sel,rowsets):
    S=set(map(int,sel)); return len(S)<=14 and all(bool(R&S) for R in rowsets)


def main():
    from ortools.sat.python import cp_model

    k13=json.loads(K13.read_text()); assert k13['valid'] and k13['result']=='K13_INFEASIBLE'
    pts,_idx,iso,_supports,_charts,_edge=old.geometry()
    leaf_id,reps=s5.build_orbit_machine(pts,iso)
    _leaf,A=old.full_orbit_machine(pts,iso); assert A.shape==(6129,5294)
    raw=[frozenset(map(int,A.indices[A.indptr[r]:A.indptr[r+1]])) for r in range(A.shape[0])]
    rowsets=sorted(set(raw),key=lambda S:(len(S),tuple(sorted(S)))); assert len(rowsets)==6128

    # Sparse column rows for exact frozen-dual loads.
    rr=[];cc=[]
    for r,S in enumerate(rowsets):
        for j in S: rr.append(r);cc.append(j)
    from scipy.sparse import csr_matrix
    B=csr_matrix((np.ones(len(rr),dtype=np.int8),(rr,cc)),shape=(6128,5294),dtype=np.int64)

    gens=[]
    for q in range(4):
        g=[]
        for r in reps:
            z=list(r); z[q],z[q+1]=z[q+1],z[q]; g.append(leaf_id(tuple(z)))
        gens.append(tuple(g))
    _G,orbits=make_orbits(gens,5294)

    fixed=[int(x) for x in k13['strongFixing']['fixedOrbitIndices']]
    certs={int(c['orbitIndex']):c for c in k13['exactDualCertificates']}
    deadline=time.time()+GLOBAL_SECONDS
    records=[]; closed=[]; witness=None

    # Start with branches expected to kernelize most: large frozen dual objective.
    fixed.sort(key=lambda oi:(-float(certs[oi]['objective']),oi))
    for oi in fixed:
        if time.time()>=deadline: break
        first=int(orbits[oi][0]); budget=13; forced=[]
        rows=[r for r,S in enumerate(rowsets) if first not in S]
        active=set(range(5294)); active.remove(first)

        cert=certs[oi]; y=np.zeros(6128,dtype=np.int64)
        for r,w in cert['weights']: y[int(r)]=int(w)
        score=int(y.sum()); loads=np.asarray(B.T.dot(y),dtype=np.int64).reshape(-1)
        dual_fixed={j for j in active if score-int(loads[j])>12*D}
        active-=dual_fixed
        rec={'orbitIndex':oi,'representativeColumn':first,'initialResidualRows':len(rows),
             'dualFixedColumns':len(dual_fixed),'rounds':[]}

        infeas=False
        for rnd in range(MAX_ROUNDS):
            rows,empty,rmeta=minimal_rows(rows,rowsets,active)
            if empty: rec['emptyRows']=empty[:16]; infeas=True; break
            active,cmeta=dominated_columns(rows,rowsets,active)
            rows,active,budget,forced,newforce,empty=force_singletons(rows,rowsets,active,budget,forced)
            rec['rounds'].append({'round':rnd,'rows':rmeta,'columns':cmeta,'newForced':newforce,
                                  'remainingRows':len(rows),'remainingColumns':len(active),'budget':budget})
            if empty or budget<0: rec['emptyRows']=empty[:16]; infeas=True; break
            if not rows:
                cand=[first]+forced
                assert verify(cand,rowsets); witness=sorted(cand); rec['result']='FEASIBLE_BY_FORCING'; break
            # stop when a full round changes neither side nor forces anything
            if rmeta['before']==rmeta['after'] and cmeta['before']==cmeta['after'] and not newforce: break
        if witness is not None:
            records.append(rec); break
        if infeas:
            rec['result']='INFEASIBLE_KERNEL'; closed.append(oi); records.append(rec); continue

        # Exact integer closure attempt on the bidominance kernel.
        cols=sorted(active); pos={j:q for q,j in enumerate(cols)}
        supports=[]; impossible=False
        for r in rows:
            S=[pos[j] for j in rowsets[r] if j in pos]
            if not S: impossible=True; break
            supports.append(frozenset(S))
        if impossible:
            rec['result']='INFEASIBLE_EMPTY_PRE_SAT'; closed.append(oi); records.append(rec); continue
        M=cp_model.CpModel(); x=[M.NewBoolVar(f'x{q}') for q in range(len(cols))]
        for S in supports: M.AddBoolOr([x[q] for q in S])
        M.Add(sum(x)<=budget)
        C=cp_model.CpSolver(); C.parameters.max_time_in_seconds=min(SAT_SECONDS,max(1.0,deadline-time.time()))
        C.parameters.num_search_workers=8; C.parameters.cp_model_presolve=True; C.parameters.symmetry_level=3; C.parameters.linearization_level=2
        st=C.Solve(M); name=C.StatusName(st)
        rec['solver']={'status':name,'columns':len(cols),'rows':len(rows),'budget':budget,
                       'branches':int(C.NumBranches()),'conflicts':int(C.NumConflicts()),'wallSeconds':float(C.WallTime())}
        if name in ('OPTIMAL','FEASIBLE'):
            add=[cols[q] for q in range(len(cols)) if C.Value(x[q])]
            cand=[first]+forced+add; assert verify(cand,rowsets); witness=sorted(cand); rec['result']='K14_FEASIBLE'
        elif name=='INFEASIBLE': rec['result']='INFEASIBLE_SAT'; closed.append(oi)
        else: rec['result']='UNKNOWN'
        records.append(rec)
        if witness is not None: break

    all_closed=(witness is None and len(set(closed))==len(fixed))
    result='K14_FEASIBLE' if witness is not None else ('K14_INFEASIBLE' if all_closed else 'UNKNOWN')
    out={'schema':'holotrade.depth5-k14-bidominance-kernel.v1','valid':True,'result':result,
         'branchCount':len(fixed),'branchesProcessed':len(records),'closedBranchCount':len(set(closed)),
         'witnessLeafOrbitIndices':witness,
         'certifiedIntervalUpdate':([14,14] if witness is not None else ([15,22] if all_closed else [14,22])),
         'records':records,
         'theorem':('The explicit verified cover proves tau_5=14.' if witness is not None else ('All 88 exhaustive S5-normalized first-column branches are exactly closed, so no 14-cover exists and tau_5>=15.' if all_closed else 'Bi-dominance produced theorem-safe branch kernels but did not globally decide K14.')),
         'boundary':'Row dominance, column dominance, duplicate elimination and singleton forcing are exact for unit-cost set cover. UNKNOWN solver records never improve the theorem.'}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'valid':True,'result':result,'processed':len(records),'closed':len(set(closed)),'witness':witness,'interval':out['certifiedIntervalUpdate']},sort_keys=True))

if __name__=='__main__': main()
