#!/usr/bin/env python3
"""Holotrade integration for the exact W33 optimal near-ovoid classification.

W33-Theory owns the theorem/proof.  This file is intentionally smaller: it
rebuilds enough q=3 incidence algebra to check the structural payload locally,
reconciles it with Holotrade's pre-existing CP-SAT deficiency certificate, and
publishes an integration-safe namespace.

Source theorem commits in W33-Theory:
  dd770350d39b22d0a50c3586feb7283eebaac4ea  executable proof
  7b71c98cb181b73f7fa9464f543cb0b51615af20  frozen certificate
  51761470746215b9d885d1507e9a25455d153d7d  theorem note

No scheduler/control semantic is changed by this file.  In particular, the
six exact completions of one defect dipole are NOT identified with any other
six-state carrier without an explicit intertwiner.
"""
from __future__ import annotations

import itertools
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "w33_ovoid_defect_dipole_integration.json"
OLD = ROOT / "data" / "w33_ovoid_deficiency.json"
Q=3


def norm(v):
    i=next(k for k,x in enumerate(v) if x%Q)
    z=pow(v[i]%Q,-1,Q)
    return tuple((z*x)%Q for x in v)


def form(u,v):
    return (u[0]*v[1]-u[1]*v[0]+u[2]*v[3]-u[3]*v[2])%Q


def geometry():
    pts=sorted({norm(v) for v in itertools.product(range(Q),repeat=4) if any(v)})
    idx={v:i for i,v in enumerate(pts)}
    lines=set()
    for ia,ib in itertools.combinations(range(40),2):
        a,b=pts[ia],pts[ib]
        if form(a,b): continue
        span=set()
        for s,t in itertools.product(range(Q),repeat=2):
            if s==t==0: continue
            w=tuple((s*a[k]+t*b[k])%Q for k in range(4))
            span.add(idx[norm(w)])
        if len(span)==4: lines.add(tuple(sorted(span)))
    lines=sorted(lines)
    assert len(pts)==len(lines)==40
    return pts,lines


def matmul(A,B):
    return [[sum(A[i][k]*B[k][j] for k in range(len(B)))
             for j in range(len(B[0]))] for i in range(len(A))]


def signature_columns(lines):
    # Line graph is SRG(40,12,2,4); K=(A-12I)(A-2I)=96E_-4.
    A=[[0]*40 for _ in range(40)]
    for i,j in itertools.combinations(range(40),2):
        if set(lines[i]) & set(lines[j]): A[i][j]=A[j][i]=1
    assert {sum(r) for r in A}=={12}
    A2=matmul(A,A)
    assert {A2[i][j] for i,j in itertools.combinations(range(40),2) if A[i][j]}=={2}
    assert {A2[i][j] for i,j in itertools.combinations(range(40),2) if not A[i][j]}=={4}
    B=[[A[i][j]-(12 if i==j else 0) for j in range(40)] for i in range(40)]
    C=[[A[i][j]-(2 if i==j else 0) for j in range(40)] for i in range(40)]
    K=matmul(B,C)
    cols=[tuple(K[r][c] for r in range(40)) for c in range(40)]
    return cols


def exact_solutions(lines, target):
    point_lines=[[] for _ in range(40)]
    for li,L in enumerate(lines):
        for p in L: point_lines[p].append(li)
    allowed=[p for p in range(40) if all(target[li]>0 for li in point_lines[p])]
    cand=[[p for p in L if p in allowed] for L in lines]
    counts=[0]*40; chosen=[]; sols=set()
    def rec():
        if len(chosen)>10: return
        unmet=[]
        for li,t in enumerate(target):
            if counts[li]>t: return
            need=t-counts[li]
            if need:
                feasible=[p for p in cand[li] if p not in chosen and
                          all(counts[lj]<target[lj] for lj in point_lines[p])]
                if len(feasible)<need: return
                unmet.append((len(feasible),-need,li,feasible))
        if not unmet:
            if len(chosen)==10: sols.add(tuple(sorted(chosen)))
            return
        _,negneed,_,feasible=min(unmet); need=-negneed
        for sub in itertools.combinations(feasible,need):
            d=Counter()
            for p in sub:
                for lj in point_lines[p]: d[lj]+=1
            if any(counts[lj]+x>target[lj] for lj,x in d.items()): continue
            chosen.extend(sub)
            for lj,x in d.items(): counts[lj]+=x
            rec()
            for lj,x in d.items(): counts[lj]-=x
            del chosen[-len(sub):]
    rec()
    return sorted(sols)


def main():
    _,lines=geometry()
    pencils=[[] for _ in range(40)]
    for li,L in enumerate(lines):
        for p in L: pencils[p].append(li)
    cols=signature_columns(lines)
    groups=defaultdict(list)
    for T in itertools.combinations(range(40),3):
        sig=tuple(sum(cols[c][r] for c in T) for r in range(40))
        groups[sig].append(T)
    hist=Counter(map(len,groups.values()))
    assert hist==Counter({1:9720,4:40})

    # Every fourfold collision is exactly a line's four punctured pencils.
    observed=sorted(tuple(sorted(tuple(sorted(T)) for T in C))
                    for C in groups.values() if len(C)==4)
    expected=[]
    for li,L in enumerate(lines):
        expected.append(tuple(sorted(tuple(sorted(set(pencils[p])-{li})) for p in L)))
    assert observed==sorted(expected)

    # One oriented dipole; exact local completion count is six.
    C=list(C for C in groups.values() if len(C)==4)[0]
    miss,double=sorted(C)[:2]
    target=[1]*40
    for li in miss: target[li]=0
    for li in double: target[li]=2
    sols=exact_solutions(lines,target)
    assert len(sols)==6
    assert all(Counter(sum(p in S for p in L) for L in lines)==
               Counter({1:34,0:3,2:3}) for S in sols)

    # Holotrade's older solver certificate must agree if present.
    prior_ok=None
    if OLD.exists():
        old=json.loads(OLD.read_text())
        q3=next(x for x in old["instances"] if x["q"]==3)
        prior_ok=(q3["status"]=="OPTIMAL" and q3["deficiency"]==3 and
                  q3["profile"]=={"0":3,"1":34,"2":3})
        assert prior_ok

    out={
      "schema":"holotrade.w33-ovoid-defect-dipole-integration.v1",
      "valid":True,
      "sourceOfTruth":{
        "repository":"wilcompute/W33-Theory",
        "proofCommit":"dd770350d39b22d0a50c3586feb7283eebaac4ea",
        "certificateCommit":"7b71c98cb181b73f7fa9464f543cb0b51615af20",
        "noteCommit":"51761470746215b9d885d1507e9a25455d153d7d"},
      "reconcilesHolotradeOvoidDeficiency":prior_ok,
      "localChecks":{
        "tripleSignatureHistogram":{"singleton":9720,"size4":40},
        "size4ClassesArePuncturedPencilClasses":True,
        "representativeCompletions":6,
        "representativeProfile":{"0":3,"1":34,"2":3}},
      "integrationNamespace":{
        "coarseDefectDipoles":480,
        "exactCompletionsPerDipole":6,
        "optimalNearOvoids":2880,
        "interpretation":"480 oriented collinear defect channels, each with six exact completion states"},
      "safeUse":"regression/fuzz namespace for W33 placement and evidence-path tests; theorem remains owned by W33-Theory",
      "notAuthorized":"Do not identify the local six completions with P1(F9), HJ10, G2, S3 control, or any other six-state carrier without an explicit intertwiner. Do not change scheduler guarantees from this classification alone."
    }
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"valid":True,"dipoles":480,"perDipole":6,"optima":2880,
                      "priorReconciled":prior_ok},sort_keys=True))

if __name__=="__main__": main()
