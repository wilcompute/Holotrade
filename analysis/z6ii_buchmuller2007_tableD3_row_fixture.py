#!/usr/bin/env python3
"""Row-identity fixture for Buchmueller et al. Table D.3.

Source: arXiv:hep-th/0606187v3, printed pp.60-63.
This fixture freezes every SM-singlet/hidden-state field label and its orbifold
sector, independently of our spectrum generator.

Published row partition:
  U : s1-s3, fbar1-fbar2
  T1: s4-s29, h1-h4, w1-w2
  T2: s30-s48, h5-h6, fbar3, f1-f2, w3
  T3: s49-s52, h7-h10
  T4: s53-s69, h11-h14, f3-f4, fbar4, w4-w5

Totals:
  69 s, 14 h, 4 f, 4 fbar, 5 w,
matching Table 5.1.

Boundary: this is the complete row-identity/sector fixture. The q2...q9 charge
columns and R/gamma data still need generated-state reproduction.
"""
import json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/z6ii_buchmuller2007_tableD3_row_fixture.json'

def rng(prefix,a,b,sector):return [(f'{prefix}{i}',sector,prefix) for i in range(a,b+1)]
ROWS=[]
ROWS += rng('s',1,3,0)+[('fbar1',0,'fbar'),('fbar2',0,'fbar')]
ROWS += rng('s',4,29,1)+rng('h',1,4,1)+rng('w',1,2,1)
ROWS += rng('s',30,48,2)+rng('h',5,6,2)+[('fbar3',2,'fbar')]+rng('f',1,2,2)+[('w3',2,'w')]
ROWS += rng('s',49,52,3)+rng('h',7,10,3)
ROWS += rng('s',53,69,4)+rng('h',11,14,4)+rng('f',3,4,4)+[('fbar4',4,'fbar')]+rng('w',4,5,4)

def main(write=True):
    names=[r[0] for r in ROWS];assert len(names)==len(set(names))==96
    kind=Counter(r[2] for r in ROWS);sector=Counter(r[1] for r in ROWS)
    assert kind==Counter({'s':69,'h':14,'f':4,'fbar':4,'w':5})
    assert all(f's{i}' in names for i in range(1,70))
    assert all(f'h{i}' in names for i in range(1,15))
    out={'schema':'holotrade.z6ii_buchmuller2007_tableD3_row_fixture.v1',
      'status':'PASS_COMPLETE_ROW_IDENTITY_FIXTURE',
      'source':'Buchmueller et al. hep-th/0606187v3 Table D.3, printed pp.60-63; totals cross-check Table 5.1',
      'rows':[{'name':n,'k':k,'kind':kind} for n,k,kind in ROWS],
      'totals':dict(kind),
      'sector_row_counts':{str(k):v for k,v in sorted(sector.items())},
      'checks':{'all_96_rows_unique':True,'s1_through_s69_complete':True,'h1_through_h14_complete':True,'totals_match_table5_1':True},
      'remaining_regression':'Machine-reproduce each row charge vector q2...q9, R_i, gamma and hidden irrep; row identities/sectors are now immutable targets.'}
    if write:OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2));return out
if __name__=='__main__':main(True)
