#!/usr/bin/env python3
"""Native SAT attack on the exact depth-five K=14 frontier.

The quotient is already Boolean: each of 6,128 distinct rows is one covering
clause, and a K14 cover is a truth assignment with at most fourteen selected
columns.  CP-SAT/MIP have struggled, so this pass uses an independent SAT
backend (PySAT Minicard) with native cardinality constraints.

K13 strong fixing proves any cover must contain one of 88 S5 column types. For
each type we normalize one selected column to its orbit representative, delete
rows it covers, reapply its stored exact rational dual fixing to eliminate
impossible second columns, then solve the residual SAT instance with native
AtMost(13).

SAT yields an explicit independently verified <=14 cover. If all 88 normalized
branches are UNSAT, no K14 cover exists and tau_5>=15. UNKNOWN/timeouts never
improve the theorem.
"""
from __future__ import annotations

import json
import signal
import time
from pathlib import Path

import numpy as np

import depth5_induced_subgroup_cuts as old
import depth5_coordinate_s5_automorphism as s5

ROOT=Path(__file__).resolve().parents[1]
K13=ROOT/'data/depth5_k13_strong_dual_fixing.json'
OUT=ROOT/'data/depth5_k14_native_sat_attack.json'
D=10_000_000
GLOBAL_SECONDS=4800.0
PER_BRANCH_SECONDS=150.0


def make_orbits(gens,n):
    G=s5.closure(gens,n); assert len(G)==120
    unseen=set(range(n)); out=[]
    while unseen:
        j=min(unseen); O=sorted({g[j] for g in G}); unseen.difference_update(O); out.append(O)
    assert len(out)==94
    return G,out


def verify(sel,rowsets):
    S=set(map(int,sel)); return len(S)<=14 and all(bool(R&S) for R in rowsets)


def main():
    from pysat.solvers import Minicard

    k13=json.loads(K13.read_text()); assert k13['valid'] and k13['result']=='K13_INFEASIBLE'
    pts,_idx,iso,_supports,_charts,_edge=old.geometry()
    leaf_id,reps=s5.build_orbit_machine(pts,iso)
    _leaf,A=old.full_orbit_machine(pts,iso); assert A.shape==(6129,5294)
    raw=[frozenset(map(int,A.indices[A.indptr[r]:A.indptr[r+1]])) for r in range(A.shape[0])]
    rowsets=sorted(set(raw),key=lambda S:(len(S),tuple(sorted(S)))); assert len(rowsets)==6128

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
    # Hardest duals first; they typically leave the smallest active column set.
    fixed.sort(key=lambda oi:(-sum(int(w) for _r,w in certs[oi]['weights']),oi))

    deadline=time.time()+GLOBAL_SECONDS
    records=[]; unsat=[]; witness=None
    for oi in fixed:
        if time.time()>=deadline: break
        first=int(orbits[oi][0])
        rows=[r for r,S in enumerate(rowsets) if first not in S]
        cert=certs[oi]; y=np.zeros(6128,dtype=np.int64)
        for r,w in cert['weights']: y[int(r)]=int(w)
        score=int(y.sum()); loads=np.asarray(B.T.dot(y),dtype=np.int64).reshape(-1)
        forbidden={j for j in range(5294) if j!=first and score-int(loads[j])>12*D}
        active=[j for j in range(5294) if j!=first and j not in forbidden]
        active_set=set(active)

        # Project and exact row-dominance reduce before SAT encoding.
        projected=[]; empty=[]
        for r in rows:
            S=frozenset(rowsets[r]&active_set)
            if not S: empty.append(r)
            else: projected.append(S)
        rec={'orbitIndex':oi,'representativeColumn':first,'dualValue':score/D,
             'dualForbiddenColumns':len(forbidden),'activeColumns':len(active),'residualRows':len(rows)}
        if empty:
            rec['status']='UNSAT_EMPTY_ROW'; rec['emptyRows']=empty[:16]; records.append(rec); unsat.append(oi); continue
        uniq=sorted(set(projected),key=lambda S:(len(S),tuple(sorted(S))))
        minimal=[]
        for S in uniq:
            if any(T.issubset(S) for T in minimal): continue
            minimal.append(S)
        rec['minimalClauses']=len(minimal)

        # SAT variable q+1 corresponds to active[q].
        pos={j:q+1 for q,j in enumerate(active)}
        clauses=[[pos[j] for j in S] for S in minimal]
        solver=Minicard(bootstrap_with=clauses)
        solver.add_atmost(list(range(1,len(active)+1)),13)

        timed_out={'v':False}
        def alarm(_sig,_frame):
            timed_out['v']=True
            try: solver.interrupt()
            except Exception: pass
        oldh=signal.signal(signal.SIGALRM,alarm)
        seconds=int(min(PER_BRANCH_SECONDS,max(1.0,deadline-time.time())))
        signal.alarm(seconds)
        t=time.time()
        try:
            sat=solver.solve_limited(expect_interrupt=True)
        finally:
            signal.alarm(0); signal.signal(signal.SIGALRM,oldh)
        rec['wallSeconds']=time.time()-t
        if sat is True:
            model=set(x for x in solver.get_model() if x>0 and x<=len(active))
            add=[active[q-1] for q in model]
            cand=sorted([first]+add)
            assert len(cand)<=14 and verify(cand,rowsets)
            witness=cand; rec['status']='SAT'; rec['witness']=cand; records.append(rec); solver.delete(); break
        elif sat is False and not timed_out['v']:
            rec['status']='UNSAT'; unsat.append(oi)
        else:
            rec['status']='UNKNOWN_TIMEOUT' if timed_out['v'] else 'UNKNOWN'
        records.append(rec); solver.delete()
        print(json.dumps(rec,sort_keys=True),flush=True)

    all_closed=(witness is None and len(set(unsat))==len(fixed))
    result='K14_FEASIBLE' if witness is not None else ('K14_INFEASIBLE' if all_closed else 'UNKNOWN')
    out={'schema':'holotrade.depth5-k14-native-sat.v1','valid':True,'result':result,
         'branchCount':len(fixed),'branchesProcessed':len(records),'unsatBranchCount':len(set(unsat)),
         'witnessLeafOrbitIndices':witness,
         'certifiedIntervalUpdate':[14,14] if witness is not None else ([15,22] if all_closed else [14,22]),
         'records':records,
         'theorem':('The explicit SAT model gives a verified <=14 cover; with K13 impossible, tau_5=14.' if witness is not None else ('All 88 exhaustive normalized branches are UNSAT in an independent native-cardinality SAT solver, so no 14-cover exists and tau_5>=15.' if all_closed else 'Native SAT did not decide every normalized K14 branch; UNKNOWN leaves the interval unchanged.')),
         'boundary':'The SAT backend is independent of CP-SAT/MIP, but only SAT with an independently verified witness or exhaustive UNSAT over all 88 normalized first-column branches changes the theorem.'}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'valid':True,'result':result,'processed':len(records),'unsat':len(set(unsat)),'witness':witness,'interval':out['certifiedIntervalUpdate']},sort_keys=True))

if __name__=='__main__': main()
