#!/usr/bin/env python3
"""Use the 360x8 near-ovoid/blocker cover inside the depth-2 tensor frontier.

At a tight 110-leaf blocker X, every first-coordinate line L has a row shadow
B_L of size exactly 11, hence one of the 360 minimum W33 line blockers.  For
each second-coordinate point q define

    H_q = { L : q in B_L }.

The old two-sided model used only the necessary degree identity
|H_q|=4|C_q| and alpha<=7, where C_q={p:(p,q) in X}.  Tightness gives much
more.  C_q is independent, so the four-line pencils Pencil(p), p in C_q, are
disjoint and

    H_q = disjoint union_{p in C_q} Pencil(p).

Conversely, this condition is sufficient.  Given 40 minimum blockers B_L such
that every H_q is the union of full pencils centred at an independent set C_q,
define X={(p,q):p in C_q}.  For each L its row shadow is exactly B_L, so every
L x M tile is met because B_L blocks every M.  Moreover
sum_q |C_q| = (1/4) sum_L |B_L| = 110.

Therefore tau_2=110 iff this 40-label minimum-blocker assignment exists.  This
is an exact shadow-only CSP: 40 variables ranging over 360 blockers, with a
40-point pencil-union code constraint.  It removes all 1,600 leaf variables
and the second blocker-selector family.

The 360x8 near-ovoid correspondence supplies the critical boundary states.
Every minimum B_L has eight shell points whose deletion gives an optimal
near-ovoid.  Thus a tight 110 solution would carry 40*8=320 labelled
near-ovoid predecessor incidences on each axis.  More generally a size
110+s blocker must have at least 40-4s minimum shadows on each axis, hence at
least 8(40-4s) such predecessor incidences.
"""
from __future__ import annotations
import itertools,json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/tensor_near_ovoid_shadow_closure.json'
Q=3;N=40

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
    lines=sorted(lines);assert len(lines)==40
    adj=[set() for _ in range(40)];pls=[[] for _ in range(40)]
    for li,L in enumerate(lines):
        for p in L:pls[p].append(li)
        for a,b in itertools.combinations(L,2):adj[a].add(b);adj[b].add(a)
    assert {len(x) for x in adj}=={12} and {len(x) for x in pls}=={4}
    return lines,adj,pls

def independent_sets(adj):
    out=[]
    def rec(chosen,candidates):
        out.append(tuple(chosen))
        for p in sorted(candidates):
            rec(chosen+[p],{q for q in candidates if q>p and q not in adj[p]})
    rec([],set(range(40)));return out

def blocks_lines(B,lines):
    S=set(B);return all(S&set(L) for L in lines)
def shadow_stats(X,lines):
    S=set(X);row=[];col=[];occ=[]
    for L in lines:
        row.append(len({q for p in L for q in range(40) if p*40+q in S}))
    for M in lines:
        col.append(len({p for q in M for p in range(40) if p*40+q in S}))
    for L in lines:
        for M in lines:
            occ.append(sum(p*40+q in S for p in L for q in M))
    return Counter(row),Counter(col),Counter(occ)

def main():
    lines,adj,pls=geometry()
    corpus=json.loads((ROOT/'data/w33_near_ovoid_adversarial_corpus.json').read_text())
    records=corpus['records'];assert len(records)==360 and all(len(r['removals'])==8 for r in records)
    blockers=sorted(tuple(r['blocker']) for r in records);assert len(set(blockers))==360
    assert all(len(B)==11 and blocks_lines(B,lines) for B in blockers)

    # The exact pencil-union code.
    ind=independent_sets(adj);dist=Counter(map(len,ind))
    assert dist==Counter({0:1,1:40,2:540,3:3240,4:9450,5:13824,6:10080,7:2880})
    pencil=[sum(1<<l for l in pls[p]) for p in range(40)]
    dec={}
    for C in ind:
        mask=0
        for p in C:mask|=pencil[p]
        dec.setdefault(mask,[]).append(C)
        assert mask.bit_count()==4*len(C)
    multiplicities=Counter(map(len,dec.values()))
    assert len(ind)==40055 and len(dec)==37850 and multiplicities==Counter({1:35645,2:2205})

    # Strict negative control: the old aggregate conditions can all pass while
    # the new exact line-level pencil-union condition fails.
    expected=[
      (0,1,2,5,7,9,11,12,18,27,36),
      (0,3,8,10,16,21,25,26,29,35,37),
      (2,3,6,7,14,19,24,28,30,33,34)]
    assert [blockers[i] for i in (0,69,173)]==expected
    assign=[blockers[0]]*16+[blockers[69]]*12+[blockers[173]]*12
    H=[]
    for q in range(40):
        m=0
        for l,B in enumerate(assign):
            if q in B:m|=1<<l
        H.append(m)
    deg=[m.bit_count() for m in H]
    assert Counter(deg)==Counter({0:11,12:17,16:8,24:1,28:3})
    assert all(d%4==0 and d<=28 for d in deg) and sum(d//4 for d in deg)==110
    invalid=[q for q,m in enumerate(H) if m and m not in dec]
    assert len(invalid)==21

    slack={}
    for n in range(110,116):
        s=n-110;minimum=max(0,40-4*s)
        slack[str(n)]={'minimum_shadows_per_axis':minimum,
                       'near_ovoid_predecessor_incidences_per_axis':8*minimum}
    assert [slack[str(n)]['minimum_shadows_per_axis'] for n in range(110,116)]==[40,36,32,28,24,20]

    # The present 115 witness is heavily concentrated on minimum shadows.
    old=json.loads((ROOT/'data/tensor_symmetric_blocker.json').read_text())
    X=old['witness'];assert len(X)==115 and old['witnessBlocksAll1600']
    rd,cd,td=shadow_stats(X,lines)
    assert rd==Counter({11:33,12:4,13:3})
    assert cd==Counter({11:33,12:3,13:3,14:1})
    assert td==Counter({1:1389,2:192,3:11,4:7,6:1})

    # At tight 110 each of 40 minimum row blockers has 36 singleton-hit lines.
    # Eight shell/removable blocker points each own three of them; the other
    # three blocker points each own four.
    singleton={'total':40*36,'near_ovoid_shell_type':40*8*3,'deep_type':40*3*4}
    assert singleton=={'total':1440,'near_ovoid_shell_type':960,'deep_type':480}

    out={
      'schema':'holotrade.tensor-near-ovoid-shadow-closure.v1','valid':True,
      'tight110_equivalence':{
        'statement':'tau_2=110 iff 40 minimum blockers B_L can be assigned to the 40 line labels such that H_q={L:q in B_L} is a union of full four-line pencils centered at an independent W33 set C_q for every q',
        'reconstruction':'X={(p,q):p in C_q}; then row shadow(L)=B_L and |X|=(1/4)sum_L|B_L|=110',
        'leaf_variables_needed':False,'second_shadow_selector_family_needed':False},
      'pencil_union_code':{
        'independent_center_sets':len(ind),'independent_set_size_distribution':dict(sorted(dist.items())),
        'distinct_line_masks':len(dec),'mask_decomposition_multiplicity':dict(sorted(multiplicities.items()))},
      'strictness_negative_control':{
        'blocker_indices':[0,69,173],'line_label_multiplicities':[16,12,12],
        'H_size_distribution':dict(sorted(Counter(deg).items())),
        'old_degree_conditions_pass':True,'decoded_total_leaf_count':110,'max_decoded_fibre_size':7,
        'nonempty_Hq':sum(d>0 for d in deg),'pencil_union_failures':len(invalid),
        'new_line_level_condition_fires':True},
      'near_ovoid_cover':{
        'minimum_blockers':360,'near_ovoid_deletions_per_minimum_blocker':8,
        'tight110_predecessor_incidences_per_axis':320,
        'tight110_singleton_tiles':singleton,
        'slack_110_to_115':slack,
        'proof':'if |X|=110+s and m shadows have size 11 while the rest have size at least 12, then 11m+12(40-m)<=4|X|, so m>=40-4s'},
      'incumbent115_audit':{
        'row_shadow_size_distribution':dict(sorted(rd.items())),
        'column_shadow_size_distribution':dict(sorted(cd.items())),
        'minimum_row_shadows':rd[11],'minimum_column_shadows':cd[11],
        'near_ovoid_predecessor_incidences_each_axis':8*33,
        'tile_occupancy_distribution':dict(sorted(td.items()))},
      'theorem':'The depth-2 lower-bound equality problem is exactly a 40-variable minimum-blocker labeling problem with a 37,850-word pencil-union shadow code. The new constraint is strictly stronger than the old divisibility/alpha relaxation. The 360x8 near-ovoid cover supplies 320 critical predecessor incidences per axis at equality and at least 8(40-4s) per axis at size 110+s.',
      'boundary':'This is an exact equivalent reformulation of the 110 case and a certified structural audit of the 115 witness. It does not prove the shadow-label CSP infeasible or feasible; tau_2 remains open in [110,115].'}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':'PASS','shadow_code_masks':len(dec),'negative_failures':len(invalid),'incumbent_min_shadows':[rd[11],cd[11]],'tau2':[110,115]}))
if __name__=='__main__':main()
