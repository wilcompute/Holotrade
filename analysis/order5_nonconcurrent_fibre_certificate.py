#!/usr/bin/env python3
"""Reconstruct the previously observed order-5 nonconcurrent centre fibre.

A prior variation run produced the exact diagnostic

    blocker centre 23, row-line fibre [18,22,34], common pencil points []

but failed before freezing the witness.  A later order-5 solve found a different
fully concurrent optimum, so nonconcurrency is solution-dependent and must not
be inferred from the symmetry class alone.

This script makes the old observation reproducible.  It uses the same
deterministic order-5 PSp(4,3) element and asks CP-SAT for a symmetry-invariant
product blocker with at most 125 leaves such that row shadows 18,22,34 are the
SAME minimum W(3,3) blocker centred at point 23.  Since those three W33 lines
have no common point, any feasible solution is an exact counterexample to the
global claim that repeated centre fibres must be contained in a pencil.

The certificate records the witness, all tile checks, the common shadow, and
both exact defect decompositions F+D=4r.  It does not touch the separate r=1
clean-core theorem obtained after deleting the dirty pencils.
"""
from __future__ import annotations
import itertools, json, random
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/order5_nonconcurrent_fibre_certificate.json'
Q=3; N=40
TARGET_LINES=(18,22,34); TARGET_CENTRE=23; CAP=125


def nm(v):
    i=next(k for k,x in enumerate(v) if x%Q); z=pow(v[i]%Q,-1,Q)
    return tuple((z*x)%Q for x in v)

def form(u,v): return (u[0]*v[1]-u[1]*v[0]+u[2]*v[3]-u[3]*v[2])%Q

def porder(g):
    I=tuple(range(N)); h=g; o=1
    while h!=I: h=tuple(g[i] for i in h); o+=1
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
    common=set(TARGET_LINES)
    cps=[p for p in range(N) if set(TARGET_LINES)<=set(thru[p])]
    assert cps==[],cps

    e=[tuple(1 if k==i else 0 for k in range(4)) for i in range(4)]
    def is_sp(A):
        for i,j in itertools.combinations(range(4),2):
            u=tuple(sum(A[r][k]*e[i][k] for k in range(4))%Q for r in range(4))
            v=tuple(sum(A[r][k]*e[j][k] for k in range(4))%Q for r in range(4))
            if form(u,v)!=form(e[i],e[j]): return False
        return True
    def act(A,v): return nm(tuple(sum(A[i][k]*v[k] for k in range(4))%Q for i in range(4)))
    rng=random.Random(3); g=None
    for _ in range(200000):
        A=tuple(tuple(rng.randrange(Q) for _ in range(4)) for _ in range(4))
        if not is_sp(A): continue
        h=tuple(idx[act(A,pts[p])] for p in range(N))
        if porder(h)==5: g=h; break
    assert g is not None

    mark=[False]*(N*N); orb=[]
    for v in range(N*N):
        if mark[v]: continue
        cur=v; cyc=[]
        while not mark[cur]:
            mark[cur]=True;cyc.append(cur);cur=g[cur//N]*N+g[cur%N]
        orb.append(cyc)
    inorb=[0]*(N*N)
    for i,C in enumerate(orb):
        for v in C: inorb[v]=i

    m=cp_model.CpModel(); y=[m.NewBoolVar(f'y{i}') for i in range(len(orb))]
    for L in lines:
        for M in lines:
            m.AddBoolOr([y[inorb[p*N+q]] for p in L for q in M])
    size=sum(len(C)*y[i] for i,C in enumerate(orb)); m.Add(size<=CAP)

    # Exact shadow OR indicators for the three row lines.
    z=[]
    for li in TARGET_LINES:
        row=[]
        for q in range(N):
            ids=sorted({inorb[p*N+q] for p in lines[li]})
            b=m.NewBoolVar(f'z_{li}_{q}')
            m.AddMaxEquality(b,[y[o] for o in ids])
            row.append(b)
        z.append(row)
    for a in (1,2):
        for q in range(N): m.Add(z[a][q]==z[0][q])
    m.Add(sum(z[0])==11)
    for mi,M in enumerate(lines):
        m.Add(sum(z[0][q] for q in M)==(2 if TARGET_CENTRE in M else 1))

    # Find the smallest symmetry-invariant counterexample within the known cap.
    m.Minimize(size)
    s=cp_model.CpSolver();s.parameters.max_time_in_seconds=900;s.parameters.num_search_workers=8;s.parameters.random_seed=17
    st=s.Solve(m); name=s.StatusName(st)
    assert name in ('OPTIMAL','FEASIBLE'),name
    X={(v//N,v%N) for i,C in enumerate(orb) if s.Value(y[i]) for v in C}
    assert len(X)<=CAP
    assert all(any((p,q) in X for p in L for q in M) for L in lines for M in lines)

    def shadows(axis):
        sh=[]; raw=[]
        if axis=='row': fibres=[{q for a,q in X if a==p} for p in range(N)]
        else: fibres=[{p for p,b in X if b==q} for q in range(N)]
        for L in lines:
            S=set().union(*(fibres[p] for p in L));sh.append(S);raw.append(sum(len(fibres[p]) for p in L))
        F=sum(max(0,len(S)-11) for S in sh);D=sum(a-len(S) for a,S in zip(raw,sh))
        return sh,F,D
    r=len(X)-110
    row,Frow,Drow=shadows('row');col,Fcol,Dcol=shadows('col')
    assert Frow+Drow==Fcol+Dcol==4*r
    B=row[TARGET_LINES[0]]
    assert len(B)==11 and all(row[li]==B for li in TARGET_LINES)
    ints={mi:len(B&M) for mi,M in enumerate(LS)}
    assert all(v==(2 if TARGET_CENTRE in LS[mi] else 1) for mi,v in ints.items())

    out={
      'schema':'holotrade.order5-nonconcurrent-fibre.v1','valid':True,
      'solverStatus':name,'symmetryOrder':5,'leaves':len(X),'r':r,'cap':CAP,
      'forcedCentre':TARGET_CENTRE,'forcedFibreLines':list(TARGET_LINES),'commonPencilPoints':cps,
      'commonMinimumShadow':sorted(B),
      'rowDefect':{'F':Frow,'D':Drow,'sum':Frow+Drow},
      'columnDefect':{'F':Fcol,'D':Dcol,'sum':Fcol+Dcol},
      'conservation':{'fourR':4*r,'bothAxesEqualFourR':True},
      'witnessCellsFlat':sorted(p*N+q for p,q in X),
      'all1600TilesBlocked':True,
      'theorem':('There exists an order-5-invariant W(3,3)^2 blocker whose row lines 18,22,34 have the same minimum shadow centred at point 23 although those three row lines have no common point. Hence the global repeated-centre-fibre-is-a-pencil law is false in the defect regime.'),
      'boundary':('This is an existence counterexample at the recorded defect r; it does not imply every order-5 optimum is nonconcurrent, and it does not contradict the separate r=1 clean-core closure theorem after deleting dirty pencils.')
    }
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'valid':True,'status':name,'leaves':len(X),'r':r,'rowFD':[Frow,Drow],'colFD':[Fcol,Dcol]},sort_keys=True))

if __name__=='__main__':main()
