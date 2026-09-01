#!/usr/bin/env python3
"""Break the canonical depth-five regulus witness below the order-960 chart
stabilizer, then induce every resulting valid cover inequality back to the
5,294-variable full-PSp model.

This is deliberately stricter than quoting a subgroup optimum as a global
lower bound.  If H<=G and a full G leaf-orbit O is selected, all relevant
H-orbits contained in O are selected.  Therefore a restricted H-cover bound k
induces the valid weighted inequality

    sum_O (# relevant H-orbits inside O) x_O >= k.

We test three nested symmetry scales: chart+packet (192), chart+unordered
packet-edge/regulus (96), and chart+W33-line (24), and then resolve the full LP
with all induced rows.
"""
from __future__ import annotations

import collections
import itertools
import json
import math
import os
import random
from array import array
from collections import deque

import numpy as np
from scipy.optimize import Bounds,LinearConstraint,linprog,milp
from scipy.sparse import coo_matrix,csr_matrix,vstack

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'data','depth5_induced_subgroup_cuts.json')
Q=3;N=40


def nm(v):
    i=next(k for k,x in enumerate(v) if x%Q);z=pow(v[i]%Q,-1,Q)
    return tuple((z*x)%Q for x in v)

def form(u,v):return (u[0]*v[1]-u[1]*v[0]+u[2]*v[3]-u[3]*v[2])%Q

def comp(p,q):return tuple(p[q[i]] for i in range(len(q)))

def geometry():
    pts=sorted({nm(v) for v in itertools.product(range(Q),repeat=4) if any(v)});idx={v:i for i,v in enumerate(pts)}
    all_lines=set()
    for a,b in itertools.combinations(range(40),2):
        L=set()
        for s,t in itertools.product(range(Q),repeat=2):
            if s==t==0:continue
            L.add(idx[nm(tuple((s*pts[a][k]+t*pts[b][k])%Q for k in range(4)))])
        if len(L)==4:all_lines.add(tuple(sorted(L)))
    iso=sorted(L for L in all_lines if all(form(pts[a],pts[b])==0 for a,b in itertools.combinations(L,2)))
    assert len(iso)==40
    hyp=sorted(set(all_lines)-set(iso));assert len(hyp)==90
    def perp(L):
        a,b=L[0],L[1]
        return tuple(sorted(i for i,p in enumerate(pts) if form(p,pts[a])==0 and form(p,pts[b])==0))
    pairs=sorted({tuple(sorted((L,perp(L)))) for L in hyp});assert len(pairs)==45
    supports=[frozenset(set(a)|set(b)) for a,b in pairs]
    adj=[set() for _ in range(45)]
    for i,j in itertools.combinations(range(45),2):
        if supports[i].isdisjoint(supports[j]):adj[i].add(j);adj[j].add(i)
    charts=[C for C in itertools.combinations(range(45),5) if all(v in adj[u] for u,v in itertools.combinations(C,2))]
    assert len(charts)==27
    edge_reg={}
    for i,j in itertools.combinations(range(45),2):
        if j not in adj[i]:continue
        opposite=set(pairs[i])|set(pairs[j]);R=tuple(k for k,L in enumerate(iso) if all(set(L)&set(H) for H in opposite))
        assert len(R)==4;edge_reg[(i,j)]=tuple(sorted(R))
    return pts,idx,iso,supports,charts,edge_reg


def transvection_generators(pts,idx,supports):
    gs=[]
    for v in pts:
        for alpha in (1,2):
            p=[]
            for x in pts:
                z=alpha*form(x,v)%Q;y=nm(tuple((x[k]+z*v[k])%Q for k in range(4)));p.append(idx[y])
            gs.append(tuple(p))
    si={S:i for i,S in enumerate(supports)}
    g45=[tuple(si[frozenset(p[x] for x in S)] for S in supports) for p in gs]
    chosen=(18,62,77,10)
    return [gs[i] for i in chosen],[g45[i] for i in chosen]


def paired_group(gp,g45):
    I=(tuple(range(40)),tuple(range(45)));L=[I];seen={I:0};D=deque([I])
    while D:
        a,b=D.popleft()
        for p,q in zip(gp,g45):
            z=(comp(p,a),comp(q,b))
            if z not in seen:seen[z]=len(L);L.append(z);D.append(z)
    assert len(L)==25920
    return L


def canonical_codes(leaves,HP,chunk=256):
    weights=np.array([1,40,1600,64000,2560000],dtype=np.int64);out=np.empty(len(leaves),dtype=np.int64)
    for s in range(0,len(leaves),chunk):
        B=leaves[s:s+chunk];images=HP[:,B];codes=(images.astype(np.int64)*weights).sum(axis=2);out[s:s+len(B)]=codes.min(axis=0)
    return out


def full_orbit_machine(pts,iso):
    # Reuse the exact recursive orbit method of depth_five_is_reachable_but_undecided.py.
    idx={v:i for i,v in enumerate(pts)};lidx={L:i for i,L in enumerate(iso)}
    e=[tuple(1 if k==i else 0 for k in range(4)) for i in range(4)]
    def is_sp(A):
        for i,j in itertools.combinations(range(4),2):
            u=tuple(sum(A[r][k]*e[i][k] for k in range(4))%Q for r in range(4));v=tuple(sum(A[r][k]*e[j][k] for k in range(4))%Q for r in range(4))
            if form(u,v)!=form(e[i],e[j]):return False
        return True
    def act(A,v):return nm(tuple(sum(A[i][k]*v[k] for k in range(4))%Q for i in range(4)))
    rng=random.Random(11);gp=[]
    while len(gp)<3:
        A=tuple(tuple(rng.randrange(Q) for _ in range(4)) for _ in range(4))
        if is_sp(A):gp.append(tuple(idx[act(A,pts[p])] for p in range(N)))
    ident=tuple(range(N));GP=[ident];gpid={ident:0};fr=[ident]
    while fr:
        nx=[]
        for a in fr:
            for g in gp:
                c=tuple(a[g[i]] for i in range(N))
                if c not in gpid:gpid[c]=len(GP);GP.append(c);nx.append(c)
        fr=nx
    assert len(GP)==25920
    GL=[tuple(lidx[tuple(sorted(a[p] for p in L))] for L in iso) for a in GP]
    inv=[gpid[tuple(sorted(range(N),key=lambda i:a[i]))] for a in GP];gpidx=[gpid[g] for g in gp]
    rmul=[[gpid[tuple(GP[a][GP[inv[j]][i]] for i in range(N))] for j in gpidx] for a in range(len(GP))]
    def bfs(perm,depth):
        M=N**depth;lab=array('i',[-1])*M;tr=array('i',[0])*M;reps=[]
        for start in range(M):
            if lab[start]>=0:continue
            oid=len(reps);reps.append(start);lab[start]=oid;stack=[start]
            while stack:
                v=stack.pop();tv=tr[v]
                for jj,gi in enumerate(gpidx):
                    g=perm[gi];w=0;x=v;mul=1
                    for _ in range(depth):w+=g[x%N]*mul;mul*=N;x//=N
                    if lab[w]<0:lab[w]=oid;tr[w]=rmul[tv][jj];stack.append(w)
        return lab,tr,reps
    def digits(v,d):
        o=[]
        for _ in range(d):o.append(v%N);v//=N
        return o
    labP,trP,repsP=bfs(GP,4);labL,trL,repsL=bfs(GL,4);sz4=collections.Counter(labP)
    def stab_orbits(reps,perm):
        out=[]
        for r in reps:
            d=digits(r,4);St=[a for a in range(len(GP)) if all(perm[a][d[i]]==d[i] for i in range(4))];loc=[-1]*N;szs=[]
            for x in range(N):
                if loc[x]>=0:continue
                oid=len(szs);loc[x]=oid;stack=[x];cnt=1
                while stack:
                    u=stack.pop()
                    for a in St:
                        w=perm[a][u]
                        if loc[w]<0:loc[w]=oid;stack.append(w);cnt+=1
                szs.append(cnt)
            out.append((loc,szs))
        return out
    soP=stab_orbits(repsP,GP);soL=stab_orbits(repsL,GL)
    lid={};lsize={}
    for o4 in range(len(repsP)):
        loc,szs=soP[o4]
        for j in range(len(szs)):lid[(o4,j)]=len(lid);lsize[len(lid)-1]=sz4[o4]*szs[j]
    tiles=[]
    for o4 in range(len(repsL)):
        loc,szs=soL[o4];first={}
        for x in range(N):first.setdefault(loc[x],x)
        for j in sorted(first):tiles.append((repsL[o4],first[j]))
    assert (len(lid),len(tiles))==(5294,6129)
    P4=[N**i for i in range(4)]
    def leaf_id(leaf):
        v4=sum(int(leaf[i])*P4[i] for i in range(4));o4=labP[v4];g=GP[trP[v4]]
        return lid[(o4,soP[o4][0][g[int(leaf[4])]])]
    # full coverage sparse matrix rows=tile orbits, cols=leaf orbits
    rows=[];cols=[]
    for ti,(T4,M5) in enumerate(tiles):
        Ls=[iso[x] for x in digits(T4,4)]+[iso[M5]];seen=set()
        for leaf in itertools.product(*Ls):seen.add(leaf_id(leaf))
        for o in seen:rows.append(ti);cols.append(o)
    A=coo_matrix((np.ones(len(rows)),(rows,cols)),shape=(len(tiles),len(lid))).tocsr()
    return leaf_id,A


def solve_local(tiles,uniq,inv,offset,H,leaf_id):
    HP=np.asarray([a for a,_b in H],dtype=np.int16);canon=canonical_codes(uniq,HP);ids=sorted(set(map(int,canon)));iid={z:i for i,z in enumerate(ids)}
    leaf_oid=canon[inv];tile_sets=[]
    for t in range(240):tile_sets.append(set(iid[int(z)] for z in leaf_oid[offset[t]:offset[t+1]]))
    relevant=sorted(set().union(*tile_sets));rmap={o:i for i,o in enumerate(relevant)}
    rr=[];cc=[]
    for t,S in enumerate(tile_sets):
        for o in S:rr.append(t);cc.append(rmap[o])
    A=coo_matrix((np.ones(len(rr)),(rr,cc)),shape=(240,len(relevant))).tocsr()
    lp=linprog(np.ones(len(relevant)),A_ub=-A,b_ub=-np.ones(240),bounds=(0,1),method='highs')
    assert lp.success
    mi=milp(np.ones(len(relevant)),integrality=np.ones(len(relevant)),bounds=Bounds(0,1),constraints=LinearConstraint(A,1,np.inf),options={'time_limit':600})
    assert mi.success
    # Representative unique leaf for each H orbit, then containing full-G orbit.
    first={}
    for i,z in enumerate(canon):first.setdefault(iid[int(z)],i)
    full_of={o:leaf_id(uniq[first[o]]) for o in relevant}
    coeff=collections.Counter(full_of.values())
    return {'order':len(H),'HLeafOrbits':len(ids),'relevantHLeafOrbits':len(relevant),
            'tileOrbitCount':len({tuple(sorted(S)) for S in tile_sets}),
            'fractionalOptimum':float(lp.fun),'integerOptimum':int(round(mi.fun)),
            'cutCoefficients':dict(coeff)},coeff,int(round(mi.fun))


def main():
    pts,idx,iso,supports,charts,edge_reg=geometry();gp,g45=transvection_generators(pts,idx,supports);G=paired_group(gp,g45)
    cidx={frozenset(C):i for i,C in enumerate(charts)};lidx={frozenset(L):i for i,L in enumerate(iso)}
    def chart_of(b):return cidx[frozenset(b[x] for x in charts[0])]
    H960=[z for z in G if chart_of(z[1])==0];assert len(H960)==960
    p0,p1=charts[0][0],charts[0][1]
    H192=[z for z in H960 if z[1][p0]==p0];assert len(H192)==192
    H96=[z for z in H960 if {z[1][p0],z[1][p1]}=={p0,p1}];assert len(H96)==96
    ell0=0
    H24=[]
    for z in H960:
        pl=lidx[frozenset(z[0][x] for x in iso[ell0])]
        if pl==ell0:H24.append(z)
    assert len(H24)==24

    regs=[edge_reg[tuple(sorted((i,j)))] for i,j in itertools.combinations(charts[0],2)];assert sorted(x for R in regs for x in R)==list(range(40));byline={x:R for R in regs for x in R}
    tiles=[]
    for ell in range(40):
        bad=tuple(x for x in byline[ell] if x!=ell)
        for p in itertools.permutations(bad):tiles.append(tuple(p)+(ell,ell))
    blocks=[];offset=[0]
    for T in tiles:
        A=np.asarray(list(itertools.product(*(iso[x] for x in T))),dtype=np.int16);blocks.append(A);offset.append(offset[-1]+1024)
    all_leaves=np.vstack(blocks);uniq,inv=np.unique(all_leaves,axis=0,return_inverse=True);assert len(uniq)==243600

    leaf_id,Afull=full_orbit_machine(pts,iso)
    base=linprog(np.ones(5294),A_ub=-Afull,b_ub=-np.ones(6129),bounds=(0,1),method='highs');assert base.success
    cuts=[];records=[]
    for name,H in [('chartPacket192',H192),('chartEdge96',H96),('chartLine24',H24)]:
        rec,coef,k=solve_local(tiles,uniq,inv,offset,H,leaf_id);rec['name']=name;records.append(rec)
        row=np.zeros(5294)
        for o,v in coef.items():row[int(o)]=int(v)
        cuts.append((row,k))
    C=csr_matrix(np.stack([r for r,k in cuts]));rhs=np.array([k for r,k in cuts],dtype=float)
    Aaug=vstack([Afull,C]).tocsr();baug=np.concatenate([np.ones(6129),rhs])
    aug=linprog(np.ones(5294),A_ub=-Aaug,b_ub=-baug,bounds=(0,1),method='highs');assert aug.success

    out={'schema':'holotrade.depth5-induced-subgroup-cuts.v1','valid':True,
      'ambient':{'group':'PSp(4,3)','order':25920,'leafOrbits':5294,'tileOrbits':6129},
      'restrictedCuts':records,
      'fullLP':{'baseline':float(base.fun),'baselineCeiling':int(math.ceil(base.fun-1e-9)),
                'withAllInducedCuts':float(aug.fun),'newCeiling':int(math.ceil(aug.fun-1e-9)),
                'strictlyImproved':bool(aug.fun>base.fun+1e-8)},
      'theorem':'Each subgroup cover is induced to a valid weighted inequality on the full 5,294 PSp leaf-orbit variables by counting relevant H-orbits inside each G-orbit. The reported LP change is therefore a full-group statement, unlike the raw subgroup optima.',
      'boundary':'A subgroup integer optimum is never quoted directly as the global seed lower bound. Only the induced weighted rows are added to the full LP; CP-SAT upper bound 22 is untouched.'}
    if '--write' in __import__('sys').argv:
        with open(OUT,'w') as f:json.dump(out,f,indent=2,sort_keys=True)
    print(json.dumps({'status':'PASS','local':[(r['name'],r['fractionalOptimum'],r['integerOptimum'],r['tileOrbitCount']) for r in records],
                      'LP':[base.fun,aug.fun],'ceil':[out['fullLP']['baselineCeiling'],out['fullLP']['newCeiling']]},sort_keys=True))

if __name__=='__main__':main()
