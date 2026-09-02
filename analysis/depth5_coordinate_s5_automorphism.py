#!/usr/bin/env python3
"""Prove residual S5 coordinate symmetry of the exact depth-five cover problem.

The 6,129 diagonal-PSp tile orbits are not all distinct as set-cover rows:
different tile orbits can have identical sets of covering leaf orbits.  The
previous audit incorrectly required all row supports to be unique.  This
version works at the mathematically relevant level: the family of DISTINCT
cover constraints.  Duplicate constraints are logically identical and may be
removed exactly.

For the four adjacent coordinate transpositions we:
  * permute every concrete representative of the 5,294 leaf orbits;
  * recanonicalize to obtain exact column permutations;
  * prove each column map is an involutive permutation;
  * prove every distinct row support is carried to another distinct support;
  * prove the induced maps on support classes satisfy the Coxeter S5 relations.

Thus coordinate S5 is an exact automorphism of the Boolean cover instance,
with duplicate-row elimination performed before any symmetry breaking.
"""
from __future__ import annotations

import collections
import itertools
import json
import random
from array import array
from collections import deque
from pathlib import Path

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
    labP,trP,repsP=bfs(GP,4);labL,trL,repsL=bfs(GL,4)
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
        _loc,szs,first=soP[o4];d=digits(r,4)
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

    raw=[frozenset(map(int,A.indices[A.indptr[r]:A.indptr[r+1]])) for r in range(A.shape[0])]
    mult=collections.Counter(raw)
    rowsets=sorted(mult,key=lambda S:(len(S),tuple(sorted(S))))
    lookup={S:i for i,S in enumerate(rowsets)}
    assert len(lookup)==len(rowsets)
    duplicate_hist={str(k):v for k,v in sorted(collections.Counter(mult.values()).items())}

    col_gens=[];row_gens=[];records=[]
    for k in range(4):
        cg=[]
        for r in leaf_reps:
            q=list(r);q[k],q[k+1]=q[k+1],q[k];cg.append(leaf_id(tuple(q)))
        cg=tuple(cg);assert sorted(cg)==list(range(5294));assert comp(cg,cg)==tuple(range(5294))
        rg=[]
        for S in rowsets:
            T=frozenset(cg[j] for j in S);assert T in lookup;rg.append(lookup[T])
        rg=tuple(rg);assert sorted(rg)==list(range(len(rowsets)));assert comp(rg,rg)==tuple(range(len(rowsets)))
        # Recheck all 6,129 original constraints, duplicates included.
        assert all(frozenset(cg[j] for j in S) in lookup for S in raw)
        col_gens.append(cg);row_gens.append(rg)
        records.append({'generator':f's{k}{k+1}',
                        'fixedLeafOrbits':sum(cg[i]==i for i in range(5294)),
                        'fixedConstraintClasses':sum(rg[i]==i for i in range(len(rowsets)))})

    Ic=tuple(range(5294));Ir=tuple(range(len(rowsets)))
    for i in range(4):
        assert comp(col_gens[i],col_gens[i])==Ic and comp(row_gens[i],row_gens[i])==Ir
    for i in range(4):
        for j in range(i+1,4):
            c=comp(col_gens[i],col_gens[j]);r=comp(row_gens[i],row_gens[j])
            if abs(i-j)==1:
                assert comp(c,comp(c,c))==Ic and comp(r,comp(r,r))==Ir
            else:
                assert comp(c,c)==Ic and comp(r,r)==Ir
    Gc=closure(col_gens,5294);Gr=closure(row_gens,len(rowsets));assert len(Gc)==len(Gr)==120

    lp=orbit_profile(Gc,5294);rp=orbit_profile(Gr,len(rowsets))
    out={'schema':'holotrade.depth5-coordinate-s5-automorphism.v2','valid':True,
         'originalMatrixShape':[6129,5294],
         'distinctConstraintRows':len(rowsets),
         'duplicateConstraintRowsRemoved':6129-len(rowsets),
         'constraintMultiplicityHistogram':duplicate_hist,
         'coordinateGroup':'S5','groupOrder':120,'generators':records,
         'leafOrbitSizeProfileUnderS5':lp,'constraintOrbitSizeProfileUnderS5':rp,
         'leafS5OrbitCount':sum(lp.values()),'constraintS5OrbitCount':sum(rp.values()),
         'coxeterRelationsVerified':True,'exactConstraintFamilyAutomorphismVerified':True,
         'theorem':('After exact deletion of duplicate set-cover rows, the four adjacent permutations of the five product coordinates descend to simultaneous automorphisms of the 5,294 leaf-orbit variables and the complete family of distinct depth-five cover constraints. They generate S5 of order 120. Hence S5 symmetry breaking is theorem-safe for K=13.'),
         'boundary':('Distinct tile orbits may yield identical cover constraints, so no permutation action on the 6,129 tile-orbit labels is inferred from support equality. The theorem concerns the exact Boolean cover instance and removes only logically duplicate constraints.')}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'valid':True,'order':120,'distinctRows':len(rowsets),
                      'duplicateRows':6129-len(rowsets),'leafS5Orbits':out['leafS5OrbitCount'],
                      'constraintS5Orbits':out['constraintS5OrbitCount'],'gens':records},sort_keys=True))

if __name__=='__main__':main()
