#!/usr/bin/env python3
"""Test whether the tight-case centre theorem survives the first unit of slack.

For GQ(2,4), all 27 minimum blockers are the punctured perps B_c of size 10.
At |X|=91 in GQ(2,4)^2, every one of the 45 row and 45 column shadows is a
blocking set.  Also

    sum_L |shadow_L| <= 5 |X| = 455,

while the minimum total is 45*10=450.  Hence every shadow has size at most 15.

The first stage proves or refutes the missing local stability statement:
for each k=11,...,15, is there a size-k blocker that contains NONE of the 27
minimum blockers?  If all five models are infeasible, every shadow at target
91 contains a canonical punctured-perp centre even with slack.

The second stage then puts that theorem back into the full 27x27 product model:
every row/column shadow must select a contained punctured perp.  FEASIBLE at 91
would prove tau_2=91; INFEASIBLE would raise the floor to 92.  UNKNOWN is
recorded as a solver non-result, while the local stability theorem remains
independent and exact.
"""
from __future__ import annotations

import itertools,json,os,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/gq24_slack_center_lift_91.json'


def build_gq24():
    def Qf(v):return (v[0]*v[1]+v[2]*v[3]+v[4]*v[4]+v[4]*v[5]+v[5]*v[5])%2
    def Bf(u,v):return (Qf(tuple(u[i]^v[i] for i in range(6)))^Qf(u)^Qf(v))%2
    pts=[v for v in itertools.product([0,1],repeat=6) if any(v) and Qf(v)==0]
    idx={v:i for i,v in enumerate(pts)};lines=set()
    for a,b in itertools.combinations(pts,2):
        if Bf(a,b)==0:
            c=tuple(a[i]^b[i] for i in range(6))
            if any(c) and Qf(c)==0:lines.add(tuple(sorted(idx[x] for x in (a,b,c))))
    lines=sorted(lines);assert (len(pts),len(lines))==(27,45)
    nb=[set() for _ in range(27)]
    for L in lines:
        for p in L:nb[p].update(set(L)-{p})
    mins=[frozenset(nb[c]) for c in range(27)]
    assert {len(B) for B in mins}=={10} and len(set(mins))==27
    assert all(all(set(L)&set(B) for L in lines) for B in mins)
    return pts,lines,mins


def blocker_stability(lines,mins):
    from ortools.sat.python import cp_model
    rec=[];all_infeasible=True
    for k in range(11,16):
        m=cp_model.CpModel();x=[m.NewBoolVar(f'x{p}') for p in range(27)]
        for L in lines:m.Add(sum(x[p] for p in L)>=1)
        m.Add(sum(x)==k)
        for B in mins:m.Add(sum(x[p] for p in B)<=9)
        s=cp_model.CpSolver();s.parameters.max_time_in_seconds=120;s.parameters.num_search_workers=8
        st=s.StatusName(s.Solve(m));all_infeasible &= (st=='INFEASIBLE')
        witness=[] if st!='OPTIMAL' and st!='FEASIBLE' else [p for p in range(27) if s.Value(x[p])]
        rec.append({'size':k,'status':st,'counterexampleAvoidingAllMinimumBlockers':witness})
    return rec,all_infeasible


def solve91(lines,mins,enabled):
    from ortools.sat.python import cp_model
    if not enabled:return {'status':'SKIPPED','reason':'local blocker stability through size 15 was not proved'}
    m=cp_model.CpModel()
    x=[[m.NewBoolVar(f'x_{p}_{q}') for q in range(27)] for p in range(27)]
    y=[[m.NewBoolVar(f'y_{l}_{q}') for q in range(27)] for l in range(45)]
    z=[[m.NewBoolVar(f'z_{p}_{l}') for l in range(45)] for p in range(27)]
    for l,L in enumerate(lines):
        for q in range(27):m.AddMaxEquality(y[l][q],[x[p][q] for p in L])
    for p in range(27):
        for l,L in enumerate(lines):m.AddMaxEquality(z[p][l],[x[p][q] for q in L])
    # Each row and column shadow blocks the opposite quadrangle.
    for l in range(45):
        for M in lines:m.Add(sum(y[l][q] for q in M)>=1)
    for p in range(27):
        # z[p,*] is not a column shadow; build actual column-line shadows below.
        pass
    # Column shadows indexed by a second-axis line M: set of first-axis points.
    w=[[m.NewBoolVar(f'w_{M}_{p}') for p in range(27)] for M in range(45)]
    for M,L2 in enumerate(lines):
        for p in range(27):m.AddMaxEquality(w[M][p],[x[p][q] for q in L2])
    for M in range(45):
        for L1 in lines:m.Add(sum(w[M][p] for p in L1)>=1)

    m.Add(sum(x[p][q] for p in range(27) for q in range(27))==91)
    m.Add(sum(y[l][q] for l in range(45) for q in range(27))<=455)
    m.Add(sum(w[M][p] for M in range(45) for p in range(27))<=455)
    for l in range(45):
        m.Add(sum(y[l])>=10);m.Add(sum(y[l])<=15)
    for M in range(45):
        m.Add(sum(w[M])>=10);m.Add(sum(w[M])<=15)

    cr=[[m.NewBoolVar(f'cr_{l}_{c}') for c in range(27)] for l in range(45)]
    cc=[[m.NewBoolVar(f'cc_{M}_{c}') for c in range(27)] for M in range(45)]
    for l in range(45):
        m.Add(sum(cr[l])==1)
        for c,B in enumerate(mins):
            for q in B:m.Add(y[l][q]>=cr[l][c])
    for M in range(45):
        m.Add(sum(cc[M])==1)
        for c,B in enumerate(mins):
            for p in B:m.Add(w[M][p]>=cc[M][c])

    s=cp_model.CpSolver();s.parameters.max_time_in_seconds=5400;s.parameters.num_search_workers=8
    st=s.StatusName(s.Solve(m));out={'status':st,'wallTimeSeconds':s.WallTime(),'bestObjectiveBound':None}
    if st in ('OPTIMAL','FEASIBLE'):
        cells=[[p,q] for p in range(27) for q in range(27) if s.Value(x[p][q])]
        out['witnessCells']=cells;out['witnessSize']=len(cells)
    return out


def main():
    _pts,lines,mins=build_gq24();stab,ok=blocker_stability(lines,mins);prod=solve91(lines,mins,ok)
    floor=91
    if prod['status']=='INFEASIBLE':floor=92
    exact=(prod['status'] in ('OPTIMAL','FEASIBLE'))
    out={'schema':'holotrade.gq24-slack-center-lift-91.v1','valid':True,
      'localStability':{'sizesTested':[11,12,13,14,15],'records':stab,
                        'everyBlockerThrough15ContainsMinimumBlocker':ok},
      'target91':prod,
      'consequence':({'tau2Exact':91} if exact else {'certifiedLowerBound':floor,'knownUpperBound':100}),
      'theorem':('If every size-11 through size-15 blocker contains a punctured perp, then every row and column shadow of a 91-cell product blocker has a selectable canonical centre because total shadow excess is at most five on each axis. The target-91 CP-SAT model encodes exactly that valid consequence.'),
      'boundary':('Only INFEASIBLE raises the lower bound and only FEASIBLE/OPTIMAL supplies an upper witness. UNKNOWN is not evidence. The local size<=15 stability result is independent of the product solver outcome.')}
    if '--write' in sys.argv:OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':'PASS','stableThrough15':ok,'target91':prod['status'],'floor':floor,'exact91':exact},sort_keys=True))

if __name__=='__main__':main()
