#!/usr/bin/env python3
"""Matter parity and the E6 cubic become incidence predicates on 27 two-qutrit frames.

Parents:
  analysis/the_27_factorisation_frames_carry_the_so10_weights.py
  data/twenty_seven_frames_so10_weights.json
  data/w33_matter_parity_is_the_16.json
  data/w33_matter_parity_e8_crossrepo_closure.json

Choose one complete factorisation frame F0 among the 27.  The old exact frame
theorem realizes the classical E6->SO10 branching objectwise:
  1  = F0 itself;
  10 = frames sharing one factorisation with F0;
  16 = frames sharing none.

The heterotic measurement now says matter parity is exactly 16-membership.
Therefore P_M=-1 iff a frame is disjoint from F0, equivalently iff it is a
neighbor of F0 in the Schlaefli complement.

Each of the 45 factorisation octets lies in exactly three complete frames and
is a tritangent/cubic triple.  Direct enumeration proves the exact type split:
  5  x (1,10,10)
  40 x (10,16,16).
This is objectwise identical to the two Qpsi cubic patterns
  5  x (4,-2,-2)
  40 x (-2,1,1),
and every cubic contains 0 or 2 matter-odd states.

No Standard Model field is assigned to an individual frame here.  The theorem
is an exact incidence/Weyl/representation bridge plus the already-measured
field-level statement that 16-membership is matter parity.
"""
from __future__ import annotations
import importlib.util
import itertools
import json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/w33_qutrit_frame_matter_parity_cubic_bridge.json"

def load_parent():
    path=ROOT/"analysis/the_27_factorisation_frames_carry_the_so10_weights.py"
    spec=importlib.util.spec_from_file_location("frames27",path)
    assert spec and spec.loader
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod

def enumerate_frames(mod):
    _,_,_,_,_,octs,_=mod.geometry()
    disj=[[not(octs[i]&octs[j]) for j in range(45)] for i in range(45)]
    frames=[]
    def ext(cur,start):
        if len(cur)==5:
            frames.append(tuple(cur));return
        for j in range(start,45):
            if all(disj[j][i] for i in cur):ext(cur+[j],j+1)
    ext([],0)
    assert len(frames)==27
    return octs,frames

def main(write=True):
    geom=json.loads((ROOT/"data/twenty_seven_frames_so10_weights.json").read_text())
    mp=json.loads((ROOT/"data/w33_matter_parity_is_the_16.json").read_text())
    cross=json.loads((ROOT/"data/w33_matter_parity_e8_crossrepo_closure.json").read_text())
    assert geom["valid"] and geom["frames"]==27 and geom["nearFrames"]==10 and geom["farFrames"]==16
    assert mp["valid"] is True
    assert cross["status"]=="PASS_CROSSREPO_MATTER_PARITY_E8_CLOSURE"

    mod=load_parent();octs,frames=enumerate_frames(mod)
    F0=set(frames[0])
    overlap=[len(set(f)&F0) for f in frames]
    assert Counter(overlap)==Counter({0:16,1:10,5:1})
    assert all(x in (0,1,5) for x in overlap)

    role=[]
    parity=[]
    qpsi=[]
    for i,x in enumerate(overlap):
        if i==0:
            assert x==5
            role.append("1");parity.append(0);qpsi.append(4)
        elif x==1:
            role.append("10");parity.append(0);qpsi.append(-2)
        else:
            assert x==0
            role.append("16");parity.append(1);qpsi.append(1)
    assert Counter(role)==Counter({"1":1,"10":10,"16":16})
    assert Counter(parity)==Counter({1:16,0:11})

    # The 27-frame collinearity graph: two frames share one octet.
    adj=[[False]*27 for _ in range(27)]
    for i,j in itertools.combinations(range(27),2):
        z=len(set(frames[i])&set(frames[j]))
        assert z in (0,1)
        if z==1:adj[i][j]=adj[j][i]=True
    deg=[sum(r) for r in adj]
    assert set(deg)=={10}
    # Matter-odd sector is exactly the 16 non-neighbors of F0.
    assert all(parity[j]==(0 if j==0 or adj[0][j] else 1) for j in range(27))

    # Every octet lies in exactly 3 frames: the 45 tritangents/cubic triples.
    inc={o:[] for o in range(45)}
    for fi,f in enumerate(frames):
        for o in f:inc[o].append(fi)
    assert all(len(v)==3 for v in inc.values())
    triad_roles=Counter()
    triad_qpsi=Counter()
    triad_odd=Counter()
    records=[]
    for o,tri in sorted(inc.items()):
        rr=tuple(sorted((role[i] for i in tri),key={"1":0,"10":1,"16":2}.get))
        qq=tuple(sorted(qpsi[i] for i in tri))
        oo=sum(parity[i] for i in tri)
        triad_roles[rr]+=1;triad_qpsi[qq]+=1;triad_odd[oo]+=1
        records.append({"factorisation_octet":o,"frames":tri,"roles":list(rr),
                        "Qpsi":list(qq),"odd_count":oo})
    assert triad_roles==Counter({("10","16","16"):40,("1","10","10"):5})
    assert triad_qpsi==Counter({(-2,1,1):40,(-2,-2,4):5})
    assert triad_odd==Counter({2:40,0:5})
    assert all(sum(r["Qpsi"])==0 for r in records)
    assert all(r["odd_count"]%2==0 for r in records)

    # Cross-check the separately certified E6 cubic counts.
    pats={(tuple(x["Qpsi"]),x["count"]) for x in cross["E6_cubic"]["patterns"]}
    assert ((-2,1,1),40) in pats and ((-2,-2,4),5) in pats

    out={
      "schema":"holotrade.w33_qutrit_frame_matter_parity_cubic_bridge.v1",
      "status":"PASS_OBJECTWISE_QUTRIT_MATTER_PARITY_AND_CUBIC_BRIDGE",
      "headline":"On the 27 complete two-qutrit factorisation frames, choose one reference frame F0. The E6->SO10 decomposition is objectwise 1=F0, 10=frames sharing one factorisation with F0, 16=frames sharing none. Since measured heterotic matter parity is exactly 16-membership, P_M=-1 iff a complete frame is disjoint from F0, equivalently a Schlaefli-complement neighbor. The 45 tritangent/cubic triples split exactly as 5*(1,10,10)+40*(10,16,16), matching the exact Qpsi patterns 5*(4,-2,-2)+40*(-2,1,1); every cubic contains zero or two matter-odd states.",
      "frame_partition":{
        "reference":1,"share_one_factorisation":10,"share_none":16,
        "matter_even":11,"matter_odd":16,
        "predicate":"matter-odd iff overlap(frame,F0)=0",
        "graph_predicate":"matter-odd iff frame is noncollinear with F0 in GQ(2,4), equivalently adjacent to F0 in the Schlaefli graph"},
      "Qpsi_assignment":{"1":4,"10":-2,"16":1,"matter_parity":"(-1)^Qpsi"},
      "tritangent_cubic_census":{
        "total":45,
        "by_SO10_roles":{"1+10+10":5,"10+16+16":40},
        "by_Qpsi":{"-2,-2,4":5,"-2,1,1":40},
        "by_matter_odd_count":{"0":5,"2":40},
        "all_Qpsi_conserving":True,"all_matter_parity_even":True},
      "operational_reading":"A proton-protecting Z2 on the 27-weight carrier can be tested without field labels: relative to the chosen complete factorisation frame, it is the binary incidence test 'shares at least one tensor factorisation' versus 'shares none'.",
      "records":records,
      "parents":[
        "data/twenty_seven_frames_so10_weights.json",
        "data/w33_matter_parity_is_the_16.json",
        "data/w33_matter_parity_e8_crossrepo_closure.json"],
      "boundary":"Exact incidence/Weyl/representation theorem plus the independently measured field-level 16=odd rule. It does not assign a specific Standard Model particle to a particular frame, prove a vacuum, or claim the chosen reference frame is canonical without the physical SO(10) embedding.",
      "checks":{
        "27_partition_1_10_16":True,"matter_odd_is_disjointness":True,
        "45_tritangents":True,"tritangent_roles_5_and_40":True,
        "Qpsi_patterns_match":True,"every_cubic_parity_even":True}}
    if write:OUT.write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps({k:out[k] for k in ("status","frame_partition","tritangent_cubic_census")},indent=2))
    return out

if __name__=="__main__":main(True)
