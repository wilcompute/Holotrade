#!/usr/bin/env python3
"""Exhaustive failure-recovery evaluator for the 2,880 W33 near-ovoids.

Two-node mode ranges over every pair of the 30 idle points for every start.
Triple mode first counts all C(30,3) initial outage patterns and then simulates
the worst class: triples whose outage kills all three initial free lines.

This is intentionally an explicit research sweep rather than a default unit test.
The policy semantics match scheduler/w33-migration-policy.js: legacy minimises
rays/hops then labels; topology-aware additionally maximises line headroom.
"""
from __future__ import annotations
import itertools,json
from collections import Counter

# The geometry/corpus reconstruction is kept dependency-free so the sweep can be
# run on a clean checkout.  It mirrors analysis/w33_near_ovoid_adversarial_corpus.py.
Q=3; ALL=(1<<40)-1

def norm(v):
    i=next(k for k,x in enumerate(v) if x%3);z=pow(v[i]%3,-1,3)
    return tuple((z*x)%3 for x in v)
def form(u,v):return (u[0]*v[1]-u[1]*v[0]+u[2]*v[3]-u[3]*v[2])%3

def geometry():
    pts=sorted({norm(v) for v in itertools.product(range(3),repeat=4) if any(v)});idx={v:i for i,v in enumerate(pts)};lines=set()
    for a,b in itertools.combinations(range(40),2):
        if form(pts[a],pts[b]):continue
        S=set()
        for s,t in itertools.product(range(3),repeat=2):
            if s==t==0:continue
            S.add(idx[norm(tuple((s*pts[a][k]+t*pts[b][k])%3 for k in range(4)))])
        if len(S)==4:lines.add(tuple(sorted(S)))
    lines=sorted(lines);pls=[[] for _ in range(40)];adj=[set() for _ in range(40)]
    for li,L in enumerate(lines):
        for p in L:pls[p].append(li)
        for x,y in itertools.combinations(L,2):adj[x].add(y);adj[y].add(x)
    return lines,pls,adj

def solve(lines,pls,target):
    allowed={p for p in range(40) if all(target[l]>0 for l in pls[p])};cand=[[p for p in L if p in allowed] for L in lines]
    cnt=[0]*40;ch=[];inside=[False]*40;sol=set()
    def rec():
        if len(ch)>10:return
        unmet=[]
        for l,t in enumerate(target):
            if cnt[l]>t:return
            need=t-cnt[l]
            if need:
                F=[p for p in cand[l] if not inside[p] and all(cnt[j]<target[j] for j in pls[p])]
                if len(F)<need:return
                unmet.append((len(F),-need,l,F))
        if not unmet:
            if len(ch)==10:sol.add(tuple(sorted(ch)))
            return
        _,ng,_,F=min(unmet);need=-ng
        for sub in itertools.combinations(F,need):
            d=Counter()
            for p in sub:
                for j in pls[p]:d[j]+=1
            if any(cnt[j]+z>target[j] for j,z in d.items()):continue
            for p in sub:ch.append(p);inside[p]=True
            for j,z in d.items():cnt[j]+=z
            rec()
            for j,z in d.items():cnt[j]-=z
            for _ in sub:inside[ch.pop()]=False
    rec();return sorted(sol)

def starts_and_high(lines,pls,adj):
    out=[]
    for a in range(40):
      for b in sorted(adj[a]):
        h=next(iter(set(pls[a])&set(pls[b])));target=[1]*40
        for l in set(pls[a])-{h}:target[l]=0
        for l in set(pls[b])-{h}:target[l]=2
        for S in solve(lines,pls,target):
            B=set(S);free=lambda T:sum(not(T&set(L)) for L in lines)
            high=tuple(sorted(p for p in S if free(B-{p})==7))
            out.append((tuple(S),high,a))
    # Each near-ovoid occurs once for its unique oriented defect pair.
    uniq={S:(S,H,a) for S,H,a in out};assert len(uniq)==2880
    return list(uniq.values())

def run():
    lines,pls,adj=geometry();LM=[sum(1<<p for p in L) for L in lines];PM=[sum(1<<l for l in pls[p]) for p in range(40)];AM=[sum(1<<q for q in adj[p]) for p in range(40)]
    def mask(S):return sum(1<<p for p in S)
    def freebits(B,F):return sum(1<<l for l,m in enumerate(LM) if not((B|F)&m))
    def choose(B,F,sources,aware):
        idle=ALL&~B&~F;zero=freebits(B,F);occ=[(B&m).bit_count() for m in LM];single=sum(1<<l for l,x in enumerate(occ) if x==1)
        best=None
        for fr in sources:
            dest=AM[fr]&idle
            if not dest:dest=idle
            rel=zero|(PM[fr]&single)
            while dest:
                q=(dest&-dest).bit_length()-1;dest&=dest-1
                fin=rel.bit_count()-(rel&PM[q]).bit_count()
                row=(((-fin,-rel.bit_count(),fr,q) if aware else (fr,q)),fr,q,fin)
                if best is None or row[0]<best[0]:best=row
        _,fr,q,fin=best;return (B&~(1<<fr))|(1<<q),fin
    def firstreach(heads,t):
        return next((i for i,x in enumerate(heads) if x>=t),None)

    starts=starts_and_high(lines,pls,adj);targets=(3,6,9,12)
    two={"cases":0,"initialFree":Counter(),"legacy":{t:Counter() for t in targets},"aware":{t:Counter() for t in targets}}
    triple_initial=Counter();triple_zero={"cases":0,"includesDefectCenter":0,"threeDistinctFreeLineHits":0,"legacy":{t:Counter() for t in targets},"aware":{t:Counter() for t in targets}}
    for S,H,a in starts:
        B0=mask(S);idle=[p for p in range(40) if not(B0>>p)&1]
        for fs in itertools.combinations(idle,2):
            F=mask(fs);init=freebits(B0,F).bit_count();two["cases"]+=1;two["initialFree"][init]+=1
            for name,aware in (("legacy",False),("aware",True)):
                B=B0;heads=[init]
                for step in range(1,7):
                    src=H if aware and step==1 else [p for p in range(40) if(B>>p)&1]
                    B,h=choose(B,F,src,aware);heads.append(h)
                for t in targets:two[name][t][firstreach(heads,t)]=two[name][t].get(firstreach(heads,t),0)+1
        for fs in itertools.combinations(idle,3):
            F=mask(fs);init=freebits(B0,F).bit_count();triple_initial[init]+=1
            if init:continue
            triple_zero["cases"]+=1
            if a in fs:triple_zero["includesDefectCenter"]+=1
            else:triple_zero["threeDistinctFreeLineHits"]+=1
            for name,aware in (("legacy",False),("aware",True)):
                B=B0;heads=[0]
                for step in range(1,7):
                    src=H if aware and step==1 else [p for p in range(40) if(B>>p)&1]
                    B,h=choose(B,F,src,aware);heads.append(h)
                for t in targets:triple_zero[name][t][firstreach(heads,t)]=triple_zero[name][t].get(firstreach(heads,t),0)+1
    def clean(x):
        if isinstance(x,Counter):return {str(k if k is not None else "unreached"):v for k,v in sorted(x.items(),key=lambda z:(z[0] is None,z[0] or 99))}
        if isinstance(x,dict):return {str(k):clean(v) for k,v in x.items()}
        return x
    return clean({"schema":"holotrade.w33-multi-failure-recovery.v1","status":"PASS","twoFailures":two,"tripleInitialFree":triple_initial,"worstTriples":triple_zero,
      "boundary":"Exact finite level-1 policy experiment. Triple recovery is exhausted only for the worst zero-initial-placement class, while the initial-free histogram covers all triples."})
if __name__=="__main__":print(json.dumps(run(),indent=2,sort_keys=True))
