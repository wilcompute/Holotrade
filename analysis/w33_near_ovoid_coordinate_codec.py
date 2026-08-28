#!/usr/bin/env python3
"""Operational codec for all 2,880 optimal W33 near-ovoids.

W33-Theory now supplies canonical coordinates

    (a,c,m),  a~c,  m in O_c \ O_a,

where a is the defect centre, c is the parent minimum-blocker centre and m is a
point of the 45-state GQ(4,2) minimum-vector carrier.  This file rebuilds that
labeling from Holotrade's frozen 360x8 adversarial corpus and asks which pieces
of the coordinate triple the current level-1 line scheduler can actually see.

Results:
* each minimum blocker is uniquely (c,m), with m in O_c;
* its eight legal near-ovoid removals are exactly Adj(c) \ C_m, where
  C_m={x:m in O_x} is an eight-point K4,4 from the W33/GQ design;
* each optimal near-ovoid is uniquely (a,c,m), giving 40*12*6=2880 states;
* for fixed (a,c), all six m states have the SAME three free line placements:
      Pencil(a) minus the hinge line ac;
  hence the level-1 four-node line scheduler has 480 availability classes of
  size six, not 2,880 distinct availability states;
* m is nevertheless a real microstate: the six busy 10-sets are distinct;
* one additional busy point has the universal remaining-placement histogram
      0 free:1 point, 2 free:9 points, 3 free:20 points;
* releasing one busy point gives 6 free lines for six choices and 7 for four.

The result is an operational quotient, not a stronger placement guarantee.
"""
from __future__ import annotations
import itertools,json,hashlib
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CORPUS=ROOT/'data/w33_near_ovoid_adversarial_corpus.json'
OUT=ROOT/'data/w33_near_ovoid_coordinate_codec.json'
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
    return sorted(lines)

def main():
    lines=geometry();assert len(lines)==40
    pls=[[] for _ in range(40)];adj=[set() for _ in range(40)]
    N=[[0]*40 for _ in range(40)]
    for li,L in enumerate(lines):
        for p in L:pls[p].append(li);N[li][p]=1
        for a,b in itertools.combinations(L,2):adj[a].add(b);adj[b].add(a)
    assert {len(x) for x in adj}=={12}

    corpus=json.loads(CORPUS.read_text());records=corpus['records'];assert len(records)==360
    byc=defaultdict(list)
    for r in records:byc[r['center']].append(tuple(r['blocker']))
    assert Counter(map(len,byc.values()))==Counter({9:40})

    # Canonical 45 minimum-vector lines from four-column incidence collisions.
    cols=[tuple(N[l][p] for l in range(40)) for p in range(40)];sig=defaultdict(list)
    for S in itertools.combinations(range(40),4):
        z=tuple(sum(cols[p][l] for p in S) for l in range(40));sig[z].append(S)
    pairs=sorted(tuple(sorted((tuple(v[0]),tuple(v[1])))) for v in sig.values() if len(v)==2)
    assert len(pairs)==45
    mins=[tuple(1 if i in b else -1 if i in a else 0 for i in range(40)) for a,b in pairs]
    signed=[]
    for i,v in enumerate(mins):signed += [(i,v),(i,tuple(-z for z in v))]
    sumedge={}
    for ia,va in signed:
        for ib,vb in signed:
            if ia>=ib:continue
            s=tuple(va[k]+vb[k] for k in range(40))
            if sum(z*z for z in s)==12:sumedge[s]=(ia,ib)
    assert len(sumedge)==1440

    # Label each of the nine blockers at centre c by the common endpoint of its
    # eight pairwise trade edges.
    label={};O=[]
    for c in range(40):
        bs=sorted(byc[c]);labs=[]
        for i,B in enumerate(bs):
            SB=set(B);edges=[]
            for j,C in enumerate(bs):
                if i==j:continue
                SC=set(C);d=tuple(int(k in SC)-int(k in SB) for k in range(40))
                edges.append(sumedge[d])
            common=set(edges[0])
            for e in edges[1:]:common&=set(e)
            assert len(common)==1;m=next(iter(common));label[(c,B)]=m;labs.append(m)
        assert len(set(labs))==9;O.append(frozenset(labs))
    assert len(set(O))==40
    Cm=[{c for c in range(40) if m in O[c]} for m in range(45)]
    assert all(len(C)==8 for C in Cm)

    coords=[];opclasses=defaultdict(list);mcount=Counter();parentcount=Counter()
    add_hists=Counter();release_hists=Counter();induced_edges=Counter()
    for r in records:
        B=tuple(r['blocker']);SB=set(B);c=r['center'];m=label[(c,B)]
        predicted=adj[c]-Cm[m]
        assert set(r['removals'])==predicted and len(predicted)==8
        parentcount[(c,m)]+=len(r['removals'])
        for a in r['removals']:
            assert a in adj[c] and m in O[c] and m not in O[a]
            S=SB-{a};free={li for li,L in enumerate(lines) if not (S&set(L))}
            hinge=next(iter(set(pls[a])&set(pls[c])))
            expected=set(pls[a])-{hinge};assert free==expected and len(free)==3

            # One additional failure among the 30 currently idle points.
            ah=Counter()
            for x in set(range(40))-S:
                ah[sum(x not in lines[l] for l in free)]+=1
            assert ah==Counter({3:20,2:9,0:1});add_hists[tuple(sorted(ah.items()))]+=1

            # One busy point released/migrated away.
            rh=Counter()
            for y in S:
                SS=S-{y};rh[sum(not (SS&set(L)) for L in lines)]+=1
            assert rh==Counter({6:6,7:4});release_hists[tuple(sorted(rh.items()))]+=1

            e=sum(1 for u,v in itertools.combinations(S,2) if v in adj[u]);assert e==3
            induced_edges[e]+=1
            t=(a,c,m);coords.append(t);opclasses[(a,c)].append((m,tuple(sorted(S)),tuple(sorted(free))))
            mcount[m]+=1

    assert len(coords)==len(set(coords))==2880
    assert len(opclasses)==480 and set(map(len,opclasses.values()))=={6}
    assert mcount==Counter({m:64 for m in range(45)})
    assert parentcount==Counter({(c,m):8 for c in range(40) for m in O[c]})
    for ac,states in opclasses.items():
        assert len({x[0] for x in states})==6
        assert len({x[1] for x in states})==6       # six genuinely different busy sets
        assert len({x[2] for x in states})==1       # but one availability state
    assert len(add_hists)==len(release_hists)==1 and induced_edges==Counter({3:2880})

    canon=json.dumps(sorted(coords),separators=(',',':'));sha=hashlib.sha256(canon.encode()).hexdigest()
    out={
      'schema':'holotrade.w33-near-ovoid-coordinate-codec.v1','valid':True,
      'coordinates':{'form':'(a,c,m), a~c, m in O_c\\O_a','states':2880,
        'orientedDefectPairs':480,'microstatesPerPair':6,'carrierLabels':45,
        'statesPerCarrierLabel':64,'sha256':sha},
      'parentBlockerCodec':{'form':'(c,m), m in O_c','parents':360,'nearOvoidsPerParent':8,
        'legalRemovals':'Adj(c) \\ C_m, where C_m={x:m in O_x}','CmSize':8,'CmGraph':'K4,4'},
      'schedulerFactorization':{'currentReservation':'four-node W33 line','availabilityDependsOn':['a','c'],
        'availabilityIndependentOf':'m','availabilityClasses':480,'classSize':6,
        'freeLines':'Pencil(a) minus the hinge line ac'},
      'oneAdditionalBusyPoint':{'idlePoints':30,'remainingFreeLineHistogram':{'0':1,'2':9,'3':20}},
      'oneReleasedBusyPoint':{'busyPoints':10,'resultingFreeLineHistogram':{'6':6,'7':4}},
      'shapeInvariant':{'inducedBusyEdges':3,'count':2880},
      'reading':'m is a genuine adversarial microstate but is invisible to the current level-1 line-availability decision once (a,c) is known. The exact operational state space for that decision is therefore 480 classes of six.',
      'boundary':'This is a state-space/diagnostic reduction. It does not strengthen the proved blocking number tau_1=11 or the depth-2 tensor guarantee.'}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':'PASS','states':2880,'availability_classes':480,'class_size':6,'m_fibre':64,'sha256':sha}))
if __name__=='__main__':main()
