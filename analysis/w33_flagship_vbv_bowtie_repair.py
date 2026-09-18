#!/usr/bin/env python3
"""Exact bow-tie reduction of the flagship v/bv exotic-mass problem.

Parent:
  data/w33_flagship_exotics_decouple.json
  data/w33_flagship_vbv_hall_obstruction.json

The 18x18 support through the currently committed low-order search has rank 13.

The obstruction is more structured than a single Hall star.

LEFT STAR:
  S = rows {0,2,4,6,8,10}
  Every row in S has the identical support {10}.

RIGHT STAR (in the 12-row complement):
  R = columns {1,3,5,7,9,13}
  Every column in R is supported only by row 14.

Thus the support contains two opposite six-leaf stars:
       S(6 leaves) --> c10
       r14 --> R(6 leaves)

Delete S, row14, c10, and R.  The remaining 11x11 core has a perfect matching.

Therefore, IF future higher-order couplings only add edges from S to R (leaving
the already-known support untouched), the entire 18x18 matrix has full
structural rank iff the new 6x6 cross-block S x R has matching number at least 5.

Proof:
  * necessity: one row of S can use c10, so the other five S rows need five
    distinct columns in R; row14 can consume the one remaining R column.
  * sufficiency: any size-five matching S->R, together with one remaining
    S->c10 edge, row14->the remaining R column, and the fixed perfect matching
    on the 11x11 core gives an 18-edge perfect matching.

This reduces the unresolved higher-order coupling search from 324 matrix entries
to 36 targeted entries plus a matching-number test.

At q=3, |S|=|R|=6=q(q-1) and the required bridge size is 5=2q-1.
This arithmetic is recorded but NOT identified with a physical qutrit/CZ
subspace until field labels are transported into the SU(9)/Pauli basis.

Order-provenance caveat:
  the parent source comments say the coupling engine was searched through total
  order five (AB n^k with k<=3), while its prose says 'through order four' and
  leaves order five open.  This file does not resolve that provenance conflict;
  its graph theorem applies exactly to the committed support matrix regardless
  of whether the highest tested total order was four or five.
"""
from __future__ import annotations
import itertools,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/w33_flagship_vbv_bowtie_repair.json'

ROWS=[
"000000000030000000","300000000040004000","000000000030000000",
"003000000040004000","000000000030000000","000030000040004000",
"000000000030000000","000000300040004000","000000000030000000",
"000000003040004000","000000000030000000","000000000044404400",
"000000000000004044","000000000000004044","040404040404440400",
"000000000004400400","303030303044404444","303030303044404444"]
A=[[int(x) for x in r] for r in ROWS]
S=[0,2,4,6,8,10]
R=[1,3,5,7,9,13]
LHUB=10
RHUB=14

def maxmatch(rows,cols,extra=frozenset()):
    match={}
    def dfs(r,seen):
        for c in cols:
            if (A[r][c] or (r,c) in extra) and c not in seen:
                seen.add(c)
                if c not in match or dfs(match[c],seen):
                    match[c]=r
                    return True
        return False
    n=0
    for r in rows:
        if dfs(r,set()): n+=1
    return n,{r:c for c,r in match.items()}

def main(write=True):
    allr=list(range(18));allc=list(range(18))
    # left star exact
    assert all({c for c,v in enumerate(A[r]) if v}=={LHUB} for r in S)
    # right star exact after excluding S: each R column sees only RHUB
    comp=[r for r in allr if r not in S]
    for c in R:
        assert [r for r in comp if A[r][c]]==[RHUB]

    core_r=[r for r in allr if r not in S and r!=RHUB]
    core_c=[c for c in allc if c not in R and c!=LHUB]
    assert len(core_r)==len(core_c)==11
    core_rank,core_match=maxmatch(core_r,core_c)
    assert core_rank==11

    # Exhaust every 5-column reserve set: exactly choose 5 of R.
    good_reserves=[]
    for C in itertools.combinations([c for c in allc if c!=LHUB],5):
        avail=[c for c in allc if c not in C and c!=LHUB]
        rk,_=maxmatch(comp,avail)
        if rk==12:good_reserves.append(tuple(C))
    expected=set(itertools.combinations(R,5))
    assert set(good_reserves)==expected and len(good_reserves)==6

    # Verify every size-5 matching in SxR is sufficient (choose any 5 rows,
    # any 5 columns, any bijection); 6*6*120 = 4320 cases.
    tested=0
    for rows5 in itertools.combinations(S,5):
        spare_row=next(r for r in S if r not in rows5)
        for cols5 in itertools.combinations(R,5):
            spare_col=next(c for c in R if c not in cols5)
            for perm in itertools.permutations(cols5):
                extra=frozenset(zip(rows5,perm))
                rk,_=maxmatch(allr,allc,extra)
                assert rk==18
                tested+=1
    assert tested==4320

    # Necessity under SxR-only additions: exhaust all edge subsets by matching
    # number abstractly; a cross-block matching of <=4 can raise global rank by
    # at most 4, so rank <=17. Demonstrate representatives for m=0..4.
    necessity={}
    for m in range(5):
        extra=frozenset((S[i],R[i]) for i in range(m))
        rk,_=maxmatch(allr,allc,extra)
        assert rk==13+m
        necessity[str(m)]=rk

    parent=json.loads((ROOT/'data/w33_flagship_exotics_decouple.json').read_text())
    hall=json.loads((ROOT/'data/w33_flagship_vbv_hall_obstruction.json').read_text())
    assert parent['sectors']['v/bv']['structural_rank']==13
    assert hall['status']=='PASS'

    out={
      'schema':'w33.flagship_vbv_bowtie_repair.v1',
      'status':'PASS',
      'headline':'The unresolved 18x18 v/bv mass problem reduces exactly to a 6x6 higher-order cross-block. Six rows S={0,2,4,6,8,10} feed only c10, while six columns R={1,3,5,7,9,13} are fed only by r14 in the matched complement. The residual 11x11 core is perfectly matchable. If future edges are added only in SxR, full rank 18 is equivalent to matching number >=5 in that 6x6 cross-block.',
      'stars':{
        'left':{'leaves_rows':S,'hub_column':LHUB,'leaf_count':6},
        'right':{'hub_row':RHUB,'leaves_columns':R,'leaf_count':6}},
      'core':{
        'rows':core_r,'columns':core_c,'shape':[11,11],
        'structural_rank':core_rank,
        'perfect_matching':{str(r):c for r,c in sorted(core_match.items())}},
      'repair_theorem':{
        'target_cross_block':'S x R',
        'candidate_entries':36,
        'necessary_and_sufficient_condition_under_cross_block_only_updates':'matching_number(SxR) >= 5',
        'minimum_new_edges':5,
        'all_size5_bijection_completions_tested':tested,
        'good_five_column_reserves':[list(x) for x in good_reserves],
        'rank_with_diagonal_cross_matching_size_0_to_4':necessity},
      'computational_reduction':{
        'old_search_entries':324,
        'target_entries':36,
        'reduction_factor':9},
      'q3_arithmetic':{
        'six_leaves':'q(q-1)',
        'five_bridge_edges':'2q-1',
        'boundary':'Arithmetic only; no field-to-CZ basis map has been established.'},
      'order_provenance_caveat':'The parent code comments say searched through total order five (AB n^k, k<=3), while its prose says through order four. This theorem uses the committed support only and does not resolve that provenance mismatch.',
      'checks':{
        'left_star_exact':True,'right_star_exact':True,
        '11x11_core_perfect':True,'exactly_six_good_column_reserves':True,
        'all_4320_size5_cross_matchings_close_rank':True,
        'size0_to4_cross_matchings_insufficient':True}}
    if write:OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2));return out

if __name__=='__main__':main(True)
