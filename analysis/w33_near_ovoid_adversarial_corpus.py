#!/usr/bin/env python3
"""Complete one-step-below-cliff adversarial corpus for Holotrade W33 placement.

The 2880 optimal ten-point near-ovoids are compressed as 360 minimum
11-point line blockers, each with eight removable shell points. For each record
(B, b, removals):
  * B is a minimum 11-point blocker centered at b;
  * every a in removals is one of B's eight points collinear with b;
  * S=B\\{a} is an optimal near-ovoid;
  * S leaves exactly the three non-hinge lines through a free;
  * adding a back makes B and blocks all 40 lines.

Therefore the corpus is a complete set of adversarial states exactly one busy
node below the scheduler's proved m=4 line-placement cliff (tau=11).

Default execution verifies and hashes the complete corpus without touching the
working tree. Pass --write to materialize the expanded 360-record encoding.
"""
from __future__ import annotations
import itertools,json,hashlib,sys
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data"/"w33_near_ovoid_adversarial_corpus.json"
Q=3

def norm(v):
    i=next(k for k,x in enumerate(v) if x%3);z=pow(v[i]%3,-1,3)
    return tuple((z*x)%3 for x in v)
def form(u,v):return (u[0]*v[1]-u[1]*v[0]+u[2]*v[3]-u[3]*v[2])%3
def geometry():
    pts=sorted({norm(v) for v in itertools.product(range(3),repeat=4) if any(v)})
    idx={v:i for i,v in enumerate(pts)};lines=set()
    for a,b in itertools.combinations(range(40),2):
        if form(pts[a],pts[b]):continue
        S=set()
        for s,t in itertools.product(range(3),repeat=2):
            if s==t==0:continue
            S.add(idx[norm(tuple((s*pts[a][k]+t*pts[b][k])%3 for k in range(4)))])
        if len(S)==4:lines.add(tuple(sorted(S)))
    return pts,sorted(lines)
def solve(lines,pls,target):
    allowed={p for p in range(40) if all(target[l]>0 for l in pls[p])}
    cand=[[p for p in L if p in allowed] for L in lines];cnt=[0]*40;ch=[];sol=set()
    def rec():
        if len(ch)>10:return
        unmet=[]
        for l,t in enumerate(target):
            if cnt[l]>t:return
            need=t-cnt[l]
            if need:
                F=[p for p in cand[l] if p not in ch and all(cnt[j]<target[j] for j in pls[p])]
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
            ch.extend(sub)
            for j,z in d.items():cnt[j]+=z
            rec()
            for j,z in d.items():cnt[j]-=z
            del ch[-len(sub):]
    rec();return sorted(sol)

def main():
    _,lines=geometry();pls=[[] for _ in range(40)]
    for li,L in enumerate(lines):
        for p in L:pls[p].append(li)
    blockers=defaultdict(lambda:{"removals":set(),"centers":set(),"near":set()})
    near=set()
    for a in range(40):
        for b in range(40):
            if a==b:continue
            H=set(pls[a])&set(pls[b])
            if len(H)!=1:continue
            h=next(iter(H));target=[1]*40
            for l in set(pls[a])-{h}:target[l]=0
            for l in set(pls[b])-{h}:target[l]=2
            sols=solve(lines,pls,target);assert len(sols)==6
            for S in sols:
                assert a not in S and b not in S
                near.add(S)
                B=tuple(sorted(S+(a,)))
                assert all(set(B)&set(L) for L in lines)
                occ=[len(set(B)&set(L)) for L in lines]
                assert Counter(occ)==Counter({1:36,2:4})
                doubled={i for i,x in enumerate(occ) if x==2}
                assert doubled==set(pls[b])
                z=blockers[B];z["removals"].add(a);z["centers"].add(b);z["near"].add(S)
    assert len(near)==2880 and len(blockers)==360
    records=[]
    for B,z in sorted(blockers.items()):
        assert len(z["centers"])==1 and len(z["removals"])==8 and len(z["near"])==8
        b=next(iter(z["centers"]));removals=sorted(z["removals"])
        shell=[p for p in B if len(set(pls[p])&set(pls[b]))==1]
        assert sorted(shell)==removals
        for a in removals:
            S=set(B)-{a};free=[li for li,L in enumerate(lines) if not (S&set(L))]
            h=next(iter(set(pls[a])&set(pls[b])))
            assert set(free)==set(pls[a])-{h} and len(free)==3
        records.append({"blocker":list(B),"center":b,"removals":removals})
    assert Counter(r["center"] for r in records)==Counter({i:9 for i in range(40)})
    canon=json.dumps(records,sort_keys=True,separators=(",",":"))
    sha=hashlib.sha256(canon.encode()).hexdigest()
    assert sha=="d3f014837e77471087f70516bd372e6b8da9f543896d63ecda805f6adfb06d39"
    out={
      "schema":"holotrade.w33-near-ovoid-adversarial-corpus.v1",
      "valid":True,
      "encoding":"360 minimum blockers; each record's eight removals expand to the 2880 near-ovoids B\\{a}",
      "counts":{"minimumBlockers":360,"removalsPerBlocker":8,"nearOvoids":2880,
                "blockersPerCenter":9,"freeLinesPerNearOvoid":3},
      "placementCliff":{"reservationSize":4,"busyStateSize":10,"blockingNumber":11,
                        "busyTolerated":10,"freeLinePlacementsAtState":3,
                        "oneAddedPointDefeatsAllPlacements":True},
      "coverTheorem":"The 2880 optimal near-ovoids form an 8-fold cover of the 360 minimum line blockers. B\\{a} is a near-ovoid for each of the eight shell-1 blocker points a; adding a back recovers B.",
      "recordsSha256":sha,
      "records":records,
      "boundary":"This corpus exercises the exact level-1 four-node line-reservation cliff. It does not change the proved guarantee tau=11 and does not by itself imply anything about the open depth-2 tensor blocking interval."
    }
    if "--write" in sys.argv:
        OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":"PASS","blockers":360,"near":2880,"cover":8,"sha256":sha,"written":"--write" in sys.argv}))
    return out
if __name__=="__main__":main()
