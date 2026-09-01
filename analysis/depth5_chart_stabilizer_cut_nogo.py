#!/usr/bin/env python3
"""Exact no-go for the first chart-stabilizer depth-five cut family.

The full-PSp depth-five solver has 5,294 leaf orbits and 6,129 tile orbits,
with LP lower bound 13.  The 27x40 obstruction factorization suggested that
full-group compression might be erasing a useful completion-chart coordinate.
This witness breaks symmetry to one completion-chart stabilizer H of order 960
and tests the canonical 40 regulus coordinates before the full quotient.

For each W33 line ell, the fixed completion chart has a unique four-line
all-isotropic regulus containing ell.  Delete ell to get its bad triple and
embed it at depth five as

    (bad line 1, bad line 2, bad line 3, ell, ell).

All six orders of the bad triple are included, giving 240 ordered witness
tiles.  Those 240 tiles form one H-orbit.  Exhausting their 245,760 leaves and
quotienting only by H produces exactly 269 relevant H-leaf orbits.  Every one
of the 269 intersects every one of the 240 witness tiles.  Hence the restricted
fractional and integer cover optima are both one without invoking a solver.

Conclusion: even the chart stabilizer still erases this 40-coordinate cut.
To affect the global lower bound 13 one must break symmetry below the chart
stabilizer (packet/line/flag level) or use a genuinely different nonlinear
witness family.
"""
from __future__ import annotations

import itertools
import json
import os
from collections import defaultdict, deque

import numpy as np

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'data','depth5_chart_stabilizer_cut_nogo.json')
Q=3


def norm(v):
    i=next(k for k,x in enumerate(v) if x%Q);z=pow(v[i]%Q,-1,Q)
    return tuple((z*x)%Q for x in v)


def form(u,v):
    return (u[0]*v[1]-u[1]*v[0]+u[2]*v[3]-u[3]*v[2])%Q


def compose(p,q):return tuple(p[q[i]] for i in range(len(q)))


def closure_paired(g40s,g45s):
    e40=tuple(range(40));e45=tuple(range(45));G={(e40,e45)};D=deque([(e40,e45)])
    while D:
        a,b=D.popleft()
        for g,h in zip(g40s,g45s):
            z=(compose(g,a),compose(h,b))
            if z not in G:G.add(z);D.append(z)
    return list(G)


def geometry():
    pts=sorted({norm(v) for v in itertools.product(range(Q),repeat=4) if any(v)})
    idx={v:i for i,v in enumerate(pts)}
    all_lines=set()
    for a,b in itertools.combinations(range(40),2):
        L=set()
        for s,t in itertools.product(range(Q),repeat=2):
            if s==t==0:continue
            L.add(idx[norm(tuple((s*pts[a][k]+t*pts[b][k])%Q for k in range(4)))])
        if len(L)==4:all_lines.add(tuple(sorted(L)))
    assert len(all_lines)==130
    iso=sorted(L for L in all_lines
               if all(form(pts[a],pts[b])==0 for a,b in itertools.combinations(L,2)))
    hyp=sorted(set(all_lines)-set(iso));assert (len(iso),len(hyp))==(40,90)

    def perp(L):
        a,b=L[0],L[1]
        return tuple(sorted(i for i,p in enumerate(pts)
                            if form(p,pts[a])==0 and form(p,pts[b])==0))
    pairs=sorted({tuple(sorted((L,perp(L)))) for L in hyp});assert len(pairs)==45
    supports=[frozenset(set(a)|set(b)) for a,b in pairs]
    adj=[set() for _ in range(45)]
    for i,j in itertools.combinations(range(45),2):
        if supports[i].isdisjoint(supports[j]):adj[i].add(j);adj[j].add(i)
    charts=[C for C in itertools.combinations(range(45),5)
            if all(v in adj[u] for u,v in itertools.combinations(C,2))]
    assert len(charts)==27
    edge_reg={}
    for i,j in itertools.combinations(range(45),2):
        if j not in adj[i]:continue
        opposite=set(pairs[i])|set(pairs[j]);assert len(opposite)==4
        R=tuple(k for k,L in enumerate(iso)
                if all(set(L)&set(H) for H in opposite))
        assert len(R)==4;edge_reg[(i,j)]=tuple(sorted(R))
    return pts,idx,iso,supports,charts,edge_reg


def chart_stabilizer(pts,idx,iso,supports,charts):
    gens40=[]
    for v in pts:
        for alpha in (1,2):
            p=[]
            for x in pts:
                z=alpha*form(x,v)%Q
                y=norm(tuple((x[k]+z*v[k])%Q for k in range(4)))
                p.append(idx[y])
            gens40.append(tuple(p))
    si={S:i for i,S in enumerate(supports)}
    gens45=[tuple(si[frozenset(p[x] for x in S)] for S in supports)
            for p in gens40]
    G=closure_paired([gens40[i] for i in (18,62,77,10)],
                     [gens45[i] for i in (18,62,77,10)])
    assert len(G)==25920
    cidx={frozenset(C):i for i,C in enumerate(charts)}
    H=[p40 for p40,p45 in G
       if cidx[frozenset(p45[x] for x in charts[0])]==0]
    assert len(H)==960
    lidx={frozenset(L):i for i,L in enumerate(iso)}
    HP=np.asarray(H,dtype=np.int16)
    HL=np.asarray([[lidx[frozenset(p[x] for x in L)] for L in iso] for p in H],
                  dtype=np.int16)
    return HP,HL


def canonical_codes(leaves,HP,chunk=256):
    weights=np.array([1,40,1600,64000,2560000],dtype=np.int64)
    out=np.empty(len(leaves),dtype=np.int64)
    for s in range(0,len(leaves),chunk):
        B=leaves[s:s+chunk]
        images=HP[:,B]
        codes=(images.astype(np.int64)*weights).sum(axis=2)
        out[s:s+len(B)]=codes.min(axis=0)
    return out


def main():
    pts,idx,iso,supports,charts,edge_reg=geometry()
    HP,HL=chart_stabilizer(pts,idx,iso,supports,charts)
    regs=[edge_reg[tuple(sorted((i,j)))] for i,j in itertools.combinations(charts[0],2)]
    assert len(regs)==10 and sorted(x for R in regs for x in R)==list(range(40))
    byline={ell:R for R in regs for ell in R};assert len(byline)==40

    tiles=[]
    for ell in range(40):
        bad=tuple(x for x in byline[ell] if x!=ell)
        for p in itertools.permutations(bad):tiles.append(tuple(p)+(ell,ell))
    assert len(tiles)==240
    tindex={T:i for i,T in enumerate(tiles)}
    orbit={tindex[tuple(int(HL[h,x]) for x in tiles[0])] for h in range(960)}
    assert len(orbit)==240

    blocks=[];offset=[0]
    for T in tiles:
        A=np.asarray(list(itertools.product(*(iso[x] for x in T))),dtype=np.int16)
        assert A.shape==(1024,5);blocks.append(A);offset.append(offset[-1]+1024)
    all_leaves=np.vstack(blocks)
    uniq,inv=np.unique(all_leaves,axis=0,return_inverse=True)
    assert len(uniq)==243600
    canon=canonical_codes(uniq,HP)
    ids=sorted(set(map(int,canon)));iid={z:i for i,z in enumerate(ids)}
    assert len(ids)==269
    leaf_oid=canon[inv]
    tile_sets=[]
    for t in range(240):
        S=frozenset(iid[int(z)] for z in leaf_oid[offset[t]:offset[t+1]])
        tile_sets.append(S)
    assert {len(S) for S in tile_sets}=={269}
    assert len(set(tile_sets))==1

    out={
      'schema':'holotrade.depth5-chart-stabilizer-cut-nogo.v1','valid':True,
      'group':{'ambient':'PSp(4,3)','ambientOrder':25920,
               'fixedCompletionChartStabilizerOrder':960},
      'witnessFamily':{
        'reguliInFixedChart':10,'W33LineCoordinates':40,
        'orderedWitnessTiles':240,'witnessTileOrbitCountUnderChartStabilizer':1,
        'leavesEnumerated':245760,'distinctLeaves':243600,
        'relevantChartStabilizerLeafOrbits':269},
      'coverage':{
        'leafOrbitCountSeenByEveryWitnessTile':269,
        'allWitnessTilesHaveIdenticalLeafOrbitSet':True,
        'restrictedFractionalCoverOptimum':1,
        'restrictedIntegerCoverOptimum':1},
      'theorem':'Breaking PSp(4,3) only to a completion-chart stabilizer does not recover a useful linear cut from the 40 regulus coordinates. The 240 oriented bad-triple-plus-omitted-line-twice witnesses are one H-orbit, and every relevant H-leaf orbit covers every witness.',
      'consequence':'This witness family cannot raise the depth-five LP lower bound 13. A successful chart-aware cut must break below the chart stabilizer or use additional nonlinear/integer structure.',
      'boundary':'No claim is made about all possible chart-stabilizer inequalities; this closes the canonical 40-coordinate regulus witness family only.'}
    if '--write' in __import__('sys').argv:
        with open(OUT,'w') as f:json.dump(out,f,indent=2,sort_keys=True)
    print(json.dumps({'status':'PASS','H':960,'tiles':240,'leafOrbits':269,
                      'restrictedOptimum':1},sort_keys=True))

if __name__=='__main__':main()
