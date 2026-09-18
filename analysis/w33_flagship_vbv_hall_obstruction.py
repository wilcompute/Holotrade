#!/usr/bin/env python3
"""Exact Hall obstruction inside the flagship v/bv exotic mass support.

Parent:
  data/w33_flagship_exotics_decouple.json

The parent certificate records an 18x18 v/bv support matrix with structural
rank 13 through order four.  This file resolves WHY the deficiency is five.

There is a distinguished row set
    S = {0,2,4,6,8,10}
whose six rows are identical and have support on the single column
    N(S) = {10}
at order three.  Hall's theorem therefore gives
    |S|-|N(S)| = 6-1 = 5
unavoidable unmatched rows.

This is the entire deficiency, not just a lower bound: after removing S and
column 10, the remaining 12 rows admit a matching of size 12.  Together with
one match from S to column 10 this gives rank 13, exactly the parent result.

Thus the order<=4 obstruction is one explicit 6->1 star.  Orders 5--8 only
need to add enough support out of these six rows to break that Hall defect;
the rest of the v/bv support already has full row matching.

At q=3 the numbers are 6=q(q-1) and defect 5=2q-1, the same integer as the
CZ_3 zero-phase block dimension.  THIS FILE DOES NOT identify the six v states
with a qutrit off-diagonal sector or the five Hall-defect directions with the
CZ zero-phase SU(5) block, because the parent artifact retains support indices
but not a canonical map from those indices to the SU(9)/Pauli basis.  The
numerical equality is recorded only as a target for a future label-level weld.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/w33_flagship_vbv_hall_obstruction.json'

ROWS=["000000000030000000",
"300000000040004000",
"000000000030000000",
"003000000040004000",
"000000000030000000",
"000030000040004000",
"000000000030000000",
"000000300040004000",
"000000000030000000",
"000000003040004000",
"000000000030000000",
"000000000044404400",
"000000000000004044",
"000000000000004044",
"040404040404440400",
"000000000004400400",
"303030303044404444",
"303030303044404444"]
A=[[int(c) for c in r] for r in ROWS]

def maximum_matching(rows, cols):
    match={}
    def dfs(r,seen):
        for c in cols:
            if A[r][c] and c not in seen:
                seen.add(c)
                if c not in match or dfs(match[c],seen):
                    match[c]=r
                    return True
        return False
    n=0
    for r in rows:
        if dfs(r,set()): n+=1
    return n,{r:c for c,r in match.items()}

def neighbors(rows):
    return {c for r in rows for c,v in enumerate(A[r]) if v}

def main(write=True):
    parent=json.loads((ROOT/'data/w33_flagship_exotics_decouple.json').read_text())
    assert parent['valid']
    assert parent['sectors']['v/bv']['structural_rank']==13

    allr=list(range(18)); allc=list(range(18))
    S=[0,2,4,6,8,10]
    N=neighbors(S)
    assert N=={10}
    assert all(A[r]==A[S[0]] for r in S)
    assert A[S[0]][10]==3 and sum(bool(x) for x in A[S[0]])==1
    hall_defect=len(S)-len(N)
    assert hall_defect==5

    rank,matching=maximum_matching(allr,allc)
    assert rank==13

    remr=[r for r in allr if r not in S]
    remc=[c for c in allc if c not in N]
    remrank,remmatch=maximum_matching(remr,remc)
    assert remrank==12
    assert len(remmatch)==12

    # One explicit full-size matching: one star edge plus all 12 complement rows.
    witness=dict(remmatch)
    witness[S[0]]=10
    assert len(witness)==13
    assert len(set(witness.values()))==13
    assert all(A[r][c] for r,c in witness.items())

    # Removing any five of the six star rows leaves a 13-row support with a perfect row matching.
    # This confirms the deficiency is concentrated on the star.
    concentration=[]
    for keep in S:
        rr=[r for r in allr if r not in S or r==keep]
        rk,_=maximum_matching(rr,allc)
        concentration.append(rk)
        assert rk==13==len(rr)

    q=3
    checks={
      'parent_rank13':rank==13,
      'six_identical_rows':all(A[r]==A[S[0]] for r in S),
      'star_neighbor_set_is_singleton':N=={10},
      'star_edge_is_order3':A[S[0]][10]==3,
      'Hall_defect_is_5':hall_defect==5,
      'complement_12_rows_has_full_matching':remrank==12,
      'one_star_plus_complement_gives_rank13':len(witness)==13,
      'deleting_five_star_rows_removes_all_deficiency':all(x==13 for x in concentration),
      'q3_star_size_is_q_qminus1':len(S)==q*(q-1),
      'q3_defect_equals_2qminus1':hall_defect==2*q-1,
    }
    assert all(checks.values())
    out={
      'schema':'w33.flagship_vbv_hall_obstruction.v1',
      'status':'PASS',
      'headline':'The flagship v/bv rank-13-of-18 defect through order four is caused entirely by one explicit Hall obstruction: six identical rows {0,2,4,6,8,10} couple only to column 10, so 6->1 forces five unmatched rows. Removing that star and its one neighbor leaves 12 rows with a full size-12 matching.',
      'parent':'data/w33_flagship_exotics_decouple.json',
      'support':{
        'shape':[18,18],
        'nonzero_entries':sum(bool(x) for row in A for x in row),
        'structural_rank':rank,
      },
      'Hall_witness':{
        'rows':S,
        'neighbors':sorted(N),
        'common_row_pattern':ROWS[S[0]],
        'common_edge_order':3,
        'defect':hall_defect,
        'formula':'|S|-|N(S)| = 6-1 = 5',
      },
      'complement':{
        'rows':remr,
        'columns_excluding_10':remc,
        'matching_size':remrank,
        'matching':{str(r):c for r,c in sorted(remmatch.items())},
        'reading':'all deficiency is concentrated in the six-to-one star',
      },
      'order5_to_8_target':'To reach maximal rank, higher-order couplings must break the Hall star by supplying at least five additional independent neighbor directions across its six rows (or an equivalent support enlargement).',
      'q3_arithmetic':{
        'star_size_6':'q(q-1)',
        'Hall_defect_5':'2q-1',
        'CZ_zero_phase_dimension_5':'2q-1',
        'boundary':'The equality of the two fives is not yet a basis-level identification; the support artifact lacks the field-to-Pauli/SU9 eigenbasis map.',
      },
      'checks':checks,
    }
    if write: OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))
    return out

if __name__=='__main__': main(True)
