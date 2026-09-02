#!/usr/bin/env python3
"""Test whether omitted pencil lines are paid for by oversized shadows.

The corrected 115-leaf witness has a stronger relation than mere concurrency:
for every multiplicity-three centre fibre, the missing fourth line of the
fibre's concurrency pencil is an oversized shadow, and the distinct omitted
line set equals the oversized-shadow set.

That relation would directly connect centre collisions to the defect budget F,
so it is worth varying before using it.  We recreate symmetry-restricted
blockers for deterministic order 6, 12 and 5 symmetries and, on both axes,
measure every fibre of multiplicity >=2:
  * its unique concurrency point p;
  * the 4-m omitted lines of the pencil through p;
  * whether each omitted line has an oversized (>11) shadow;
  * whether the distinct omitted set equals or is contained in the oversized set.

No optimality claim for tau_2 is made; counterexamples are decisive, positives
are only evidence for a possible lemma.
"""
from __future__ import annotations

import collections
import itertools
import json
import random
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/defect_omitted_pencil_cost_variation.json'
Q=3; N=40


def nm(v):
    i=next(k for k,x in enumerate(v) if x%Q); z=pow(v[i]%Q,-1,Q)
    return tuple((z*x)%Q for x in v)

def form(u,v):
    return (u[0]*v[1]-u[1]*v[0]+u[2]*v[3]-u[3]*v[2])%Q

def porder(g):
    I=tuple(range(N)); h=g; o=1
    while h!=I:
        h=tuple(g[i] for i in h); o+=1
    return o


def main():
    from ortools.sat.python import cp_model

    pts=sorted({nm(v) for v in itertools.product(range(Q),repeat=4) if any(v)})
    idx={v:i for i,v in enumerate(pts)}
    lines=set()
    for a,b in itertools.combinations(range(N),2):
        if form(pts[a],pts[b]): continue
        S=set()
        for x,y in itertools.product(range(Q),repeat=2):
            if x==y==0: continue
            S.add(idx[nm(tuple((x*pts[a][k]+y*pts[b][k])%Q for k in range(4)))])
        if len(S)==4: lines.add(tuple(sorted(S)))
    lines=sorted(lines); LS=[set(L) for L in lines]
    assert len(lines)==40
    thru=[[li for li,L in enumerate(lines) if p in L] for p in range(N)]
    assert {len(x) for x in thru}=={4}

    e=[tuple(1 if k==i else 0 for k in range(4)) for i in range(4)]
    def is_sp(A):
        for i,j in itertools.combinations(range(4),2):
            u=tuple(sum(A[r][k]*e[i][k] for k in range(4))%Q for r in range(4))
            v=tuple(sum(A[r][k]*e[j][k] for k in range(4))%Q for r in range(4))
            if form(u,v)!=form(e[i],e[j]): return False
        return True
    def act(A,v):
        return nm(tuple(sum(A[i][k]*v[k] for k in range(4))%Q for i in range(4)))

    rng=random.Random(3); candidates={}
    tries=0
    while len(candidates)<3 and tries<200000:
        tries+=1
        A=tuple(tuple(rng.randrange(Q) for _ in range(4)) for _ in range(4))
        if not is_sp(A): continue
        g=tuple(idx[act(A,pts[p])] for p in range(N)); o=porder(g)
        if o in (5,6,12) and o not in candidates: candidates[o]=g
    assert set(candidates)=={5,6,12}

    def centre(S):
        dbl=[li for li,L in enumerate(LS) if len(S&L)==2]
        for p in range(N):
            if set(dbl)==set(thru[p]): return p
        return None

    def make_witness(g):
        mark=[False]*(N*N); orb=[]
        for v in range(N*N):
            if mark[v]: continue
            cur=v; cyc=[]
            while not mark[cur]:
                mark[cur]=True; cyc.append(cur); cur=g[cur//N]*N+g[cur%N]
            orb.append(cyc)
        inorb=[0]*(N*N)
        for i,C in enumerate(orb):
            for v in C: inorb[v]=i
        m=cp_model.CpModel(); y=[m.NewBoolVar(f'y{i}') for i in range(len(orb))]
        for L in lines:
            for M in lines:
                m.AddBoolOr([y[inorb[p*N+q]] for p in L for q in M])
        m.Minimize(sum(len(C)*y[i] for i,C in enumerate(orb)))
        s=cp_model.CpSolver(); s.parameters.max_time_in_seconds=240; s.parameters.num_search_workers=8; s.parameters.random_seed=3
        st=s.Solve(m); name=s.StatusName(st)
        assert name in ('OPTIMAL','FEASIBLE'),name
        X={(v//N,v%N) for i,C in enumerate(orb) if s.Value(y[i]) for v in C}
        assert all(any((p,q) in X for p in L for q in M) for L in lines for M in lines)
        return X,name

    def analyse_axis(X,axis):
        sh=[]
        for L in lines:
            S=set()
            if axis=='row':
                for p in L: S|={q for a,q in X if a==p}
            else:
                for q in L: S|={p for p,b in X if b==q}
            sh.append(S)
        by=collections.defaultdict(list)
        for li,S in enumerate(sh):
            if len(S)==11:
                c=centre(S); assert c is not None; by[c].append(li)
        oversized={li for li,S in enumerate(sh) if len(S)>11}
        F=sum(max(0,len(S)-11) for S in sh)
        collision=[]; all_omitted=[]
        for c,fibre in sorted(by.items()):
            if len(fibre)<2: continue
            ps=[p for p in range(N) if set(fibre)<=set(thru[p])]
            assert len(ps)==1,(c,fibre,ps)
            p=ps[0]; omitted=sorted(set(thru[p])-set(fibre))
            all_omitted.extend(omitted)
            collision.append({'blockerCentre':c,'multiplicity':len(fibre),'concurrencyPoint':p,
                              'omittedLines':omitted,
                              'allOmittedOversized':all(x in oversized for x in omitted)})
        omset=set(all_omitted)
        return {
          'shadowSizes':dict(sorted(collections.Counter(map(len,sh)).items())),
          'F':F,'minimumShadows':sum(len(S)==11 for S in sh),'oversizedLines':sorted(oversized),
          'centreMultiplicityProfile':dict(sorted(collections.Counter(map(len,by.values())).items())),
          'collisionFibres':collision,'omittedOccurrences':len(all_omitted),'distinctOmittedLines':len(omset),
          'allOmittedOccurrencesAreOversized':all(x in oversized for x in all_omitted),
          'omittedSetContainedInOversized':omset<=oversized,
          'omittedSetEqualsOversized':omset==oversized,
          'oversizedNotExplainedByOmissions':sorted(oversized-omset),
        }

    records=[]
    for o in (6,12,5):
        X,status=make_witness(candidates[o])
        rec={'symmetryOrder':o,'leaves':len(X),'r':len(X)-110,'solverStatus':status,
             'row':analyse_axis(X,'row'),'col':analyse_axis(X,'col')}
        records.append(rec)
        print(json.dumps({'order':o,'leaves':len(X),
          'rowAll':rec['row']['allOmittedOccurrencesAreOversized'],'rowEq':rec['row']['omittedSetEqualsOversized'],
          'colAll':rec['col']['allOmittedOccurrencesAreOversized'],'colEq':rec['col']['omittedSetEqualsOversized']},sort_keys=True))

    all_paid=all(rec[a]['allOmittedOccurrencesAreOversized'] for rec in records for a in ('row','col'))
    all_contained=all(rec[a]['omittedSetContainedInOversized'] for rec in records for a in ('row','col'))
    all_equal=all(rec[a]['omittedSetEqualsOversized'] for rec in records for a in ('row','col'))
    out={'schema':'holotrade.defect-omitted-pencil-cost-variation.v1','valid':True,
      'witnesses':records,
      'allOmittedOccurrencesAreOversizedAcrossSample':all_paid,
      'omittedSetContainedInOversizedAcrossSample':all_contained,
      'omittedSetEqualsOversizedAcrossSample':all_equal,
      'reading':('If allOmittedOccurrencesAreOversizedAcrossSample is true, the observed collision defects are paid for by oversized shadows: every line missing from a concurrent minimum-shadow fibre lies among the >11 shadows. This is evidence for a defect-budget lemma, not a proof. If false, the certificate is a counterexample and the proposed pricing law is rejected.'),
      'boundary':'Three symmetry-restricted witnesses are a variation test, not a universal theorem and not an improvement of tau_2 in [111,115].'}
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'valid':True,'allPaid':all_paid,'allContained':all_contained,'allEqual':all_equal},sort_keys=True))

if __name__=='__main__': main()
