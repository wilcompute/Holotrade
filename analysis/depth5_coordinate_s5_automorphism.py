#!/usr/bin/env python3
"""Prove the full residual S5 coordinate symmetry of the depth-five quotient.

After quotienting W(3,3)^5 by the diagonal PSp4(3) action, the five product
coordinates can still be permuted.  This should descend to automorphisms of the
exact 6129-by-5294 tile-vs-seed incidence matrix, but we verify it objectwise
instead of assuming it.

We replay the orbit construction from depth5_induced_subgroup_cuts while also
retaining one concrete five-point leaf representative for every one of the
5,294 diagonal-PSp leaf orbits.  For the four adjacent coordinate
transpositions (01),(12),(23),(34) we:
  * permute every concrete representative and recanonicalize with leaf_id;
  * prove the resulting map is a permutation of all 5,294 leaf orbits;
  * apply that column permutation to all 6,129 row support sets;
  * identify every transformed row with a unique existing row support;
  * prove the induced row map is a permutation and exact matrix automorphism.

The four involutions are then closed as permutations on leaf and tile orbit
sets; the generated group must have order 120 and satisfy the Coxeter S5
relations.  The certificate also freezes orbit-size/fixed-point profiles needed
for safe symmetry breaking of the K=13 exact cover search.
"""
from __future__ import annotations

import collections
import itertools
import json
import random
from array import array
from collections import deque
from pathlib import Path

import numpy as np

import depth5_induced_subgroup_cuts as old

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/depth5_coordinate_s5_automorphism.json'
Q=3;N=40


def comp(p,q): return tuple(p[q[i]] for i in range(len(q)))

def closure(gens,n):
    I=tuple(range(n)); G={I};D=deque([I])
    while D:
        a=D.popleft()
        for g in gens:
            z=comp(g,a)
            if z not in G:G.add(z);D.append(z)
    return list(G)


def orbit_profile(G,n):
    unseen=set(range(n)); sizes=[]
    while unseen:
        x=min(unseen);O={g[x] for g in G};unseen-=O;sizes.append(len(O))
    return {str(k):v for k,v in sorted(collections.Counter(sizes).items())}


def build_orbit_machine(pts,iso):
    idx={v:i for i,v in enumerate(pts)};lidx={L:i for i,L in enumerate(iso)}
    e=[tuple(1 if k==i else 0 for k in range(4)) for i in range(4)]
    def is_sp(A):
        for i,j in itertools.combinations(range(4),2):
            u=tuple(sum(A[r][k]*e[i][k] for k in range(4))%Q for r in range(4))
            v=tuple(sum(A[r][k]*e[j][k] for k in range(4))%Q for r in range(4))
            if old.form(u,v)!=old.form(e[i],e[j]):return False
        return True
    def act(A,v):return old.nm(tuple(sum(A[i][k]*v[k] for k in range(4))%Q for i in range(4)))
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
    inv=[gpid[tuple(sorted(range(N),key=lambda i:a[i]))] for a in GP]
    gpidx=[gpid[g] for g in gp]
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
            d=digits(r,4);St=[a for a in range(len(GP)) if all(perm[a][d[i]]==d[i] for i in range(4))]
            loc=[-1]*N;szs=[];first=[]
            for x in range(N):
                if loc[x]>=0:continue
                oid=len(szs);loc[x]=oid;stack=[x];cnt=1;first.append(x)
                while stack:
                    u=stack.pop()
                    for a in St:
                        w=perm[a][u]
                        if loc[w]<0:loc[w]=oid;stack.append(w);cnt+=1
                szs.append(cnt)
            out.append((loc,szs,first))
        return out
    soP=stab_orbits(repsP,GP);soL=stab_orbits(repsL,GL)
    lid={};leaf_reps=[]
    for o4,r in enumerate(repsP):
        _loc,szs,first=soP[o4]
        d=digits(r,4)
        for j in range(len(szs)):
            lid[(o4,j)]=len(lid);leaf_reps.append(tuple(d+[first[j]]))
    tiles=[]
    for o4,r in enumerate(repsL):
        _loc,_szs,first=soL[o4]
        for x in first:tiles.append((r,x))
    assert (len(lid),len(tiles),len(leaf_reps))==(5294,6129,5294)
    P4=[N**i for i in range(4)]
    def leaf_id(leaf):
        v4=sum(int(leaf[i])*P4[i] for i in range(4));o4=labP[v4];g=GP[trP[v4]]
        return lid[(o4,soP[o4][0][g[int(leaf[4])]])]
    return leaf_id,leaf_reps


def main():
    pts,_idx,iso,_supports,_charts,_edge=old.geometry()
    leaf_id,leaf_reps=build_orbit_machine(pts,iso)
    _leaf_id_ref,A=old.full_orbit_machine(pts,iso);assert A.shape==(6129,5294)
    assert all(leaf_id(r)==i for i,r in enumerate(leaf_reps))

    rowsets=[frozenset(map(int,A.indices[A.indptr[r]:A.indptr[r+1]])) for r in range(A.shape[0])]
    row_lookup={S:i for i,S in enumerate(rowsets)};assert len(row_lookup)==6129
    col_gens=[];row_gens=[];records=[]
    for k in range(4):
        cg=[]
        for r in leaf_reps:
            q=list(r);q[k],q[k+1]=q[k+1],q[k];cg.append(leaf_id(tuple(q)))
        cg=tuple(cg);assert sorted(cg)==list(range(5294));assert comp(cg,cg)==tuple(range(5294))
        rg=[]
        for S in rowsets:
            T=frozenset(cg[j] for j in S);assert T in row_lookup;rg.append(row_lookup[T])
        rg=tuple(rg);assert sorted(rg)==list(range(6129));assert comp(rg,rg)==tuple(range(6129))
        # Exact support-set covariance.
        for r in range(6129):assert frozenset(cg[j] for j in rowsets[r])==rowsets[rg[r]]
        col_gens.append(cg);row_gens.append(rg)
        records.append({'generator':f's{k}{k+1}',
                        'fixedLeafOrbits':sum(cg[i]==i for i in range(5294)),
                        'fixedTileOrbits':sum(rg[i]==i for i in range(6129))})
    # Coxeter S5 relations.
    Ic=tuple(range(5294));Ir=tuple(range(6129))
    for i in range(4):
        assert comp(col_gens[i],col_gens[i])==Ic and comp(row_gens[i],row_gens[i])==Ir
    for i in range(4):
        for j in range(i+1,4):
            c=comp(col_gens[i],col_gens[j]);r=comp(row_gens[i],row_gens[j])
            if abs(i-j)==1:
                assert comp(c,comp(c,c))==Ic and comp(r,comp(r,r))==Ir
            else:
                assert comp(c,c)==Ic and comp(r,r)==Ir
    Gc=closure(col_gens,5294);Gr=closure(row_gens,6129);assert len(Gc)==len(Gr)==120

    out={'schema':'holotrade.depth5-coordinate-s5-automorphism.v1','valid':True,
         'matrixShape':[6129,5294],'coordinateGroup':'S5','groupOrder':120,
         'generators':records,
         'leafOrbitSizeProfileUnderS5':orbit_profile(Gc,5294),
         'tileOrbitSizeProfileUnderS5':orbit_profile(Gr,6129),
         'leafS5OrbitCount':sum(orbit_profile(Gc,5294).values()),
         'tileS5OrbitCount':sum(orbit_profile(Gr,6129).values()),
         'coxeterRelationsVerified':True,'exactMatrixAutomorphismVerified':True,
         'theorem':('The four adjacent permutations of the five product coordinates descend to exact simultaneous row/column automorphisms of the full 6129x5294 diagonal-PSp depth-five cover matrix. They generate S5 of order 120 on both orbit sets. Thus S5 lex-leader or orbit-based symmetry breaking is theorem-safe for the exact K=13 feasibility problem.'),
         'boundary':('This symmetry reduces search redundancy only. It does not change the cover problem or by itself strengthen the lower bound.')}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'valid':True,'order':120,'leafOrbits':out['leafS5OrbitCount'],
                      'tileOrbits':out['tileS5OrbitCount'],'gens':records},sort_keys=True))

if __name__=='__main__':main()
