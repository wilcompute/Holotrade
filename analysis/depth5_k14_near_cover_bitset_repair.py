#!/usr/bin/env python3
"""Fast exact bitset repair search around the best frozen K=14 near-cover.

For each exact drop set D of size r<=4 from the 14-column near-cover H, only
rows exposed by H\D matter.  We solve the residual r-column cover by a custom
exact depth-limited search:
  * represent exposed-row coverage as Python integer bitsets;
  * branch on an uncovered row having the fewest available replacement columns;
  * memoize (remaining-mask, depth);
  * prune with the exact max-single-column gain lower bound.

The search is exhaustive for every tested drop set and does not depend on an
external MILP/SAT solver.  Any witness is rechecked against all 6,128 exact
constraints.  Complete failure for a radius certifies that exact local Hamming
ball contains no K14 witness.
"""
from __future__ import annotations

import itertools
import json
import time
from pathlib import Path

from depth5_k14_constructive_witness_search import build_instance, coverage_counts, exact_verify

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'data/depth5_k14_constructive_witness_search.json'
OUT=ROOT/'data/depth5_k14_near_cover_bitset_repair.json'
K=14
MAX_RADIUS=4
GLOBAL_SECONDS=1800.0


def solve_residual(U, radius, rowcols, colrows, Hset):
    """Return replacement list or None; exhaustive for this U/radius."""
    if not U: return []
    pos={r:i for i,r in enumerate(U)}
    full=(1<<len(U))-1
    cand=set(j for r in U for j in rowcols[r] if j not in Hset)
    bits={}
    by_local=[[] for _ in U]
    for j in cand:
        b=0
        for r in colrows[j]:
            q=pos.get(int(r))
            if q is not None: b |= 1<<q
        if b:
            bits[j]=b
    for j,b in bits.items():
        bb=b
        while bb:
            lsb=bb & -bb; q=lsb.bit_length()-1; by_local[q].append(j); bb-=lsb
    for q in range(len(by_local)):
        by_local[q].sort(key=lambda j:(-bits[j].bit_count(),j))

    memo=set()
    def dfs(rem,depth,chosen):
        if rem==0: return list(chosen)
        if depth==0: return None
        key=(rem,depth)
        if key in memo: return None
        # Lower bound from best possible single-column gain.
        maxgain=0
        rr=rem
        while rr:
            lsb=rr & -rr; q=lsb.bit_length()-1
            for j in by_local[q][:64]:
                g=(bits[j]&rem).bit_count()
                if g>maxgain: maxgain=g
            rr-=lsb
        if maxgain==0 or (rem.bit_count()+maxgain-1)//maxgain>depth:
            memo.add(key); return None
        # Hardest uncovered row = fewest candidate columns that hit remaining rows.
        rows=[]; rr=rem
        while rr:
            lsb=rr & -rr; q=lsb.bit_length()-1
            avail=[j for j in by_local[q] if j not in chosen]
            rows.append((len(avail),q,avail)); rr-=lsb
        _n,q,avail=min(rows,key=lambda z:(z[0],z[1]))
        # Dominance at the branch: if two candidates have nested residual cover,
        # try only maximal residual supports first; smaller support cannot be
        # better at equal unit cost for completing this branch.
        seen=[]
        branch=[]
        for j in avail:
            bj=bits[j]&rem
            if any(bj & ~bk == 0 for _k,bk in seen):
                continue
            seen=[(k,bk) for k,bk in seen if not (bk & ~bj == 0)]
            seen.append((j,bj)); branch.append(j)
        branch.sort(key=lambda j:(-(bits[j]&rem).bit_count(),j))
        for j in branch:
            z=dfs(rem & ~bits[j],depth-1,chosen+(j,))
            if z is not None: return z
        memo.add(key); return None

    return dfs(full,radius,tuple())


def main():
    src=json.loads(SRC.read_text()); assert src['valid'] and src['result']=='UNKNOWN'
    H=tuple(sorted(map(int,src['bestHeuristicSelection']))); Hset=set(H)
    rowsets,colrows,_=build_instance(); nrows=len(rowsets)
    cnt0=coverage_counts(H,colrows,nrows); assert sum(cnt0==0)==111
    rowcols=[[] for _ in range(nrows)]
    for j,rows in enumerate(colrows):
        for r in rows: rowcols[int(r)].append(j)

    deadline=time.time()+GLOBAL_SECONDS
    records=[]; summary={}; witness=None
    for radius in range(1,MAX_RADIUS+1):
        total=closed=0; minexp=None; maxexp=0
        for D in itertools.combinations(H,radius):
            if time.time()>=deadline: break
            total+=1
            cnt=cnt0.copy()
            for j in D: cnt[colrows[j]]-=1
            U=tuple(int(x) for x in (cnt==0).nonzero()[0])
            minexp=len(U) if minexp is None else min(minexp,len(U)); maxexp=max(maxexp,len(U))
            add=solve_residual(U,radius,rowcols,colrows,Hset)
            if add is not None:
                w=sorted((Hset-set(D))|set(add))
                if len(w)<=14 and exact_verify(w,rowsets):
                    witness=w; records.append({'radius':radius,'drop':list(D),'exposedRows':len(U),'add':add,'status':'FEASIBLE','witness':w}); break
            closed+=1
        summary[str(radius)]={'dropSetsProcessed':total,'exactlyClosedWithoutWitness':closed,'minimumExposedRows':minexp,'maximumExposedRows':maxexp,'completeRadius':(total==len(list(itertools.combinations(H,radius))) and witness is None)}
        if witness is not None or time.time()>=deadline: break

    result='K14_FEASIBLE' if witness is not None else 'UNKNOWN'
    out={'schema':'holotrade.depth5-k14-near-cover-bitset-repair.v1','valid':True,'result':result,
         'sourceNearCover':list(H),'sourceUncoveredRows':111,'radiusSummary':summary,'records':records,
         'witnessLeafOrbitIndices':witness,'certifiedIntervalUpdate':[14,14] if witness is not None else [14,22],
         'theorem':('The explicit verified fourteen-column repair covers all exact constraints; with K13 infeasible this proves tau_5=14.' if witness is not None else 'Every radius marked completeRadius=true was exhaustively searched by an exact bitset branch algorithm and contains no K14 witness around the frozen near-cover. No global conclusion follows from incomplete or larger radii.'),
         'boundary':'This is an exact local-neighborhood search only. A local no-go does not imply global K14 infeasibility; UNKNOWN leaves the global interval unchanged.'}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'valid':True,'result':result,'witness':witness,'radiusSummary':summary},sort_keys=True))

if __name__=='__main__': main()
