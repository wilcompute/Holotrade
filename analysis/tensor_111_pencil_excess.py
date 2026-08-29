#!/usr/bin/env python3
"""Exact marginal obstruction for a hypothetical 111-leaf W33 tensor blocker.

If X has 111 leaves, let r_p be its first-coordinate point multiplicities and
x_L=sum_{p in L} r_p the 40 row-line loads.  Every row shadow is a W33 line
blocker, hence x_L>=11.  Since sum_L x_L=4|X|=444,

    x = 11*1 + s,   s>=0,   sum s=4.

Because x lies in the incidence image and 1 lies in that image, s must be
orthogonal to the -4 eigenspace of the W33 line graph.  This script exhausts
all 123,410 nonnegative mass-four multisets and proves that the only survivors
are the 40 complete line pencils.  The same argument applies to columns.
"""
from __future__ import annotations
import itertools,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/tensor_111_pencil_excess.json'

def norm(v):
    i=next(k for k,x in enumerate(v) if x%3);z=pow(v[i]%3,-1,3)
    return tuple((z*x)%3 for x in v)
def form(u,v):return (u[0]*v[1]-u[1]*v[0]+u[2]*v[3]-u[3]*v[2])%3

def main():
    pts=sorted({norm(v) for v in itertools.product(range(3),repeat=4) if any(v)})
    idx={v:i for i,v in enumerate(pts)};lines=set()
    for a,b in itertools.combinations(range(40),2):
        if form(pts[a],pts[b]):continue
        S=set()
        for u,v in itertools.product(range(3),repeat=2):
            if u==v==0:continue
            S.add(idx[norm(tuple((u*pts[a][k]+v*pts[b][k])%3 for k in range(4)))])
        if len(S)==4:lines.add(tuple(sorted(S)))
    lines=sorted(lines);assert len(lines)==40
    pls=[[] for _ in range(40)]
    for li,L in enumerate(lines):
        for p in L:pls[p].append(li)
    A=[[0]*40 for _ in range(40)]
    for i,j in itertools.combinations(range(40),2):
        if set(lines[i])&set(lines[j]):A[i][j]=A[j][i]=1
    # K=(A-12I)(A-2I), scaled projector onto the -4 eigenspace.
    K=[[sum((A[i][k]-(12 if i==k else 0))*(A[k][j]-(2 if k==j else 0)) for k in range(40)) for j in range(40)] for i in range(40)]
    surviving=[];total=0
    for ms in itertools.combinations_with_replacement(range(40),4):
        total+=1;s=[0]*40
        for l in ms:s[l]+=1
        if all(sum(K[i][j]*s[j] for j in range(40))==0 for i in range(40)):
            surviving.append(tuple(s))
    assert total==123410 and len(surviving)==40
    pencils={tuple(1 if l in pls[p] else 0 for l in range(40)):p for p in range(40)}
    assert set(surviving)==set(pencils)
    assert all(set(s)=={0,1} for s in surviving)
    out={
      'schema':'holotrade.tensor-111-pencil-excess.v1','status':'PASS',
      'candidateLeaves':111,'lineLoads':'x=N r=11*1+s','massOfExcess':4,
      'massFourMultisetsTested':total,'projectorSurvivors':40,
      'survivors':'exactly the 40 incidence vectors of complete four-line pencils',
      'consequence':{
        'dirtyRowLines':4,'dirtyRowsForm':'one complete pencil','dirtyRowLoad':12,'cleanRowLines':36,'cleanRowLoad':11,
        'dirtyColumnLines':4,'dirtyColumnsForm':'one complete pencil','dirtyColumnLoad':12,'cleanColumnLines':36,'cleanColumnLoad':11,
        'cleanCleanDoubledTileLowerBound':112},
      'theorem':'Any 111-leaf tensor blocker must have exactly 36 clean row lines and four dirty row lines forming one point-pencil, and independently the same 36+4 pencil pattern on columns.',
      'boundary':'This is necessary, not sufficient. It does not yet decide whether a 111-leaf blocker exists.'}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':'PASS','tested':total,'survivors':40,'shape':'pencil','cleanPerAxis':36}))
if __name__=='__main__':main()
