#!/usr/bin/env python3
"""Exact target-91 model using the size-11 rigidity theorem.

The preceding slack audit proves a sharper statement than its failed global
hypothesis:

  * every size-11 blocker of GQ(2,4) contains one of the 27 minimum blockers
    (punctured perps);
  * centerless blockers first occur at size 12.

For a 91-cell blocker X in GQ(2,4)^2, every axis has 45 blocking shadows and

    sum shadow sizes <= 5|X| = 455 = 45*10 + 5.

Thus a centerless shadow consumes at least two units of the five-unit excess.
Consequently each axis has at most TWO centerless shadows and at least 43
shadows containing a canonical punctured perp.  This script encodes that exact
consequence without assuming any reciprocity for the exceptional shadows.

INFEASIBLE proves tau_2 >= 92. FEASIBLE/OPTIMAL gives tau_2=91. UNKNOWN remains
a solver non-result.
"""
from __future__ import annotations

import itertools,json,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/gq24_91_two_exception_center_model.json'


def build():
    def Q(v):return (v[0]*v[1]+v[2]*v[3]+v[4]*v[4]+v[4]*v[5]+v[5]*v[5])%2
    def B(u,v):return (Q(tuple(u[i]^v[i] for i in range(6)))^Q(u)^Q(v))%2
    pts=[v for v in itertools.product([0,1],repeat=6) if any(v) and Q(v)==0]
    idx={v:i for i,v in enumerate(pts)};lines=set()
    for a,b in itertools.combinations(pts,2):
        if B(a,b)==0:
            c=tuple(a[i]^b[i] for i in range(6))
            if any(c) and Q(c)==0:lines.add(tuple(sorted(idx[x] for x in (a,b,c))))
    lines=sorted(lines);assert (len(pts),len(lines))==(27,45)
    nb=[set() for _ in range(27)]
    for L in lines:
        for p in L:nb[p].update(set(L)-{p})
    mins=[frozenset(nb[c]) for c in range(27)]
    assert len(set(mins))==27 and {len(B) for B in mins}=={10}
    return lines,mins


def reconfirm_size11(lines,mins):
    from ortools.sat.python import cp_model
    m=cp_model.CpModel();x=[m.NewBoolVar(f'x{p}') for p in range(27)]
    for L in lines:m.Add(sum(x[p] for p in L)>=1)
    m.Add(sum(x)==11)
    for B in mins:m.Add(sum(x[p] for p in B)<=9)
    s=cp_model.CpSolver();s.parameters.max_time_in_seconds=300;s.parameters.num_search_workers=8
    st=s.StatusName(s.Solve(m));return st


def solve(lines,mins):
    from ortools.sat.python import cp_model
    m=cp_model.CpModel()
    x=[[m.NewBoolVar(f'x_{p}_{q}') for q in range(27)] for p in range(27)]
    row=[[m.NewBoolVar(f'r_{l}_{q}') for q in range(27)] for l in range(45)]
    col=[[m.NewBoolVar(f'c_{M}_{p}') for p in range(27)] for M in range(45)]
    for l,L in enumerate(lines):
        for q in range(27):m.AddMaxEquality(row[l][q],[x[p][q] for p in L])
    for M,L in enumerate(lines):
        for p in range(27):m.AddMaxEquality(col[M][p],[x[p][q] for q in L])
    for l in range(45):
        for L in lines:m.Add(sum(row[l][q] for q in L)>=1)
    for M in range(45):
        for L in lines:m.Add(sum(col[M][p] for p in L)>=1)
    m.Add(sum(x[p][q] for p in range(27) for q in range(27))==91)
    m.Add(sum(row[l][q] for l in range(45) for q in range(27))<=455)
    m.Add(sum(col[M][p] for M in range(45) for p in range(27))<=455)
    for l in range(45):m.Add(sum(row[l])>=10)
    for M in range(45):m.Add(sum(col[M])>=10)

    badr=[m.NewBoolVar(f'bad_r_{l}') for l in range(45)]
    badc=[m.NewBoolVar(f'bad_c_{M}') for M in range(45)]
    cr=[[m.NewBoolVar(f'cr_{l}_{z}') for z in range(27)] for l in range(45)]
    cc=[[m.NewBoolVar(f'cc_{M}_{z}') for z in range(27)] for M in range(45)]
    for l in range(45):
        m.Add(sum(cr[l])+badr[l]==1)
        # A centerless shadow must have size >=12; this is valid because the
        # size-11 avoiding-minimum model is independently INFEASIBLE.
        m.Add(sum(row[l])>=10+2*badr[l])
        for z,B in enumerate(mins):
            for q in B:m.Add(row[l][q]>=cr[l][z])
    for M in range(45):
        m.Add(sum(cc[M])+badc[M]==1)
        m.Add(sum(col[M])>=10+2*badc[M])
        for z,B in enumerate(mins):
            for p in B:m.Add(col[M][p]>=cc[M][z])
    m.Add(sum(badr)<=2);m.Add(sum(badc)<=2)

    s=cp_model.CpSolver();s.parameters.max_time_in_seconds=7200;s.parameters.num_search_workers=8
    st=s.StatusName(s.Solve(m))
    out={'status':st,'wallTimeSeconds':s.WallTime()}
    if st in ('OPTIMAL','FEASIBLE'):
        cells=[[p,q] for p in range(27) for q in range(27) if s.Value(x[p][q])]
        out.update(witnessCells=cells,witnessSize=len(cells),
                   rowCenterless=[l for l in range(45) if s.Value(badr[l])],
                   colCenterless=[M for M in range(45) if s.Value(badc[M])],
                   rowShadowSizes=[sum(s.Value(v) for v in row[l]) for l in range(45)],
                   colShadowSizes=[sum(s.Value(v) for v in col[M]) for M in range(45)])
    return out


def main():
    lines,mins=build();local=reconfirm_size11(lines,mins);assert local=='INFEASIBLE'
    res=solve(lines,mins)
    consequence=({'tau2Exact':91} if res['status'] in ('OPTIMAL','FEASIBLE') else
                 {'certifiedLowerBound':92,'knownUpperBound':100} if res['status']=='INFEASIBLE' else
                 {'certifiedLowerBound':91,'knownUpperBound':100,'solverResult':'UNKNOWN'})
    out={'schema':'holotrade.gq24-91-two-exception-center-model.v1','valid':True,
      'localTheorem':{'size11CenterlessBlockerStatus':local,
        'statement':'every size-11 blocker contains a 10-point punctured-perp minimum blocker'},
      'excessArgument':{'totalShadowUpperPerAxis':455,'minimumTotal':450,'excessBudget':5,
        'minimumExcessPerCenterlessShadow':2,'maxCenterlessShadowsPerAxis':2,
        'minCenteredShadowsPerAxis':43},
      'target91':res,'consequence':consequence,
      'theorem':('At target 91, size-11 rigidity plus the five-unit total shadow-excess budget implies at most two centerless shadows on each axis. The CP-SAT model imposes only this proved dichotomy: a nonexceptional shadow contains one punctured perp; an exceptional shadow has size at least 12. No slack reciprocity is assumed.'),
      'boundary':'INFEASIBLE alone raises the lower bound; FEASIBLE/OPTIMAL alone proves 91; UNKNOWN is not evidence.'}
    if '--write' in sys.argv:OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':'PASS','local11':local,'target91':res['status'],'consequence':consequence},sort_keys=True))

if __name__=='__main__':main()
