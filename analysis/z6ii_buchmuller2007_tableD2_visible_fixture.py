#!/usr/bin/env python3
"""Row-level visible-spectrum fixture from Buchmueller et al. Appendix D.

Source: arXiv:hep-th/0606187v3, Table D.2 (printed pp.58-60), cross-checked
against aggregate Table 5.1.

This fixture materializes every visible non-singlet label in Table D.2 by
sector family.  It is deliberately independent of our spectrum generator:
the generator must reproduce this immutable target.

The fixture verifies exactly:
  3 Q, 3 u^c, 7 d^c, 4 d, 5 Lbar, 8 L, 8 m, 3 e^c,
  16 s+, 16 s-.
Neutral SM singlets s_i and hidden h/f/w states live in Table D.3 and remain a
separate charge-ledger regression.
"""
import json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/z6ii_buchmuller2007_tableD2_visible_fixture.json'

ROWS=[
# name, sector k, species
('ebar1',0,'ec'),('ubar1',0,'uc'),('q1',0,'Q'),('l1',0,'L'),('lbar1',0,'Lbar'),
('ebar2',1,'ec'),('l2',1,'L'),('ubar2',1,'uc'),('dbar1',1,'dc'),('q2',1,'Q'),
('ebar3',1,'ec'),('l3',1,'L'),('ubar3',1,'uc'),('dbar2',1,'dc'),('q3',1,'Q'),
('s1-',1,'s-'),('s1+',1,'s+'),('m1',1,'m'),
('s2-',1,'s-'),('s2+',1,'s+'),('m2',1,'m'),
('s3-',1,'s-'),('s3+',1,'s+'),('m3',1,'m'),
('s4-',1,'s-'),('s4+',1,'s+'),('m4',1,'m'),
('s5-',1,'s-'),('s6-',1,'s-'),('s5+',1,'s+'),('s6+',1,'s+'),('m5',1,'m'),('m6',1,'m'),
('s7-',1,'s-'),('s8-',1,'s-'),('s7+',1,'s+'),('s8+',1,'s+'),('m7',1,'m'),('m8',1,'m'),
('dbar3',2,'dc'),('d1',2,'d'),('l4',2,'L'),
('lbar2',2,'Lbar'),('l5',2,'L'),('lbar3',2,'Lbar'),
('dbar4',2,'dc'),('dbar5',2,'dc'),('lbar4',2,'Lbar'),
('s9-',3,'s-'),('s9+',3,'s+'),('s10-',3,'s-'),('s10+',3,'s+'),
('s11-',3,'s-'),('s11+',3,'s+'),('s12-',3,'s-'),('s12+',3,'s+'),
('s13-',3,'s-'),('s13+',3,'s+'),('s14-',3,'s-'),('s14+',3,'s+'),
('s15-',3,'s-'),('s15+',3,'s+'),('s16-',3,'s-'),('s16+',3,'s+'),
('dbar6',4,'dc'),('d2',4,'d'),('dbar7',4,'dc'),('d3',4,'d'),
('l6',4,'L'),('lbar5',4,'Lbar'),('l7',4,'L'),('l8',4,'L'),('d4',4,'d'),
]
TARGET={'Q':3,'uc':3,'dc':7,'d':4,'Lbar':5,'L':8,'m':8,'ec':3,'s-':16,'s+':16}

def main(write=True):
    c=Counter(r[2] for r in ROWS)
    assert dict(c)==TARGET
    sector=Counter(r[1] for r in ROWS)
    out={
      'schema':'holotrade.z6ii_buchmuller2007_tableD2_visible_fixture.v1',
      'status':'PASS_PUBLISHED_ROW_FIXTURE',
      'source':'Buchmueller et al. hep-th/0606187v3 Table D.2, printed pp.58-60; aggregate Table 5.1',
      'rows':[{'name':n,'k':k,'species':s} for n,k,s in ROWS],
      'aggregate':dict(c),
      'published_target':TARGET,
      'sector_row_counts':{str(k):v for k,v in sorted(sector.items())},
      'checks':{
        'row_level_visible_labels_materialized':True,
        'aggregate_equals_table_5_1':True,
        'three_families_Q_uc_ec':c['Q']==c['uc']==c['ec']==3,
        'vectorlike_down_excess':'7 dbar versus 4 d',
        'vectorlike_doublet_excess':'5 Lbar versus 8 L plus 8 neutral m'},
      'remaining_external_regression':'Table D.3 neutral/hidden singlet charge rows q2...q9 still need machine-readable transcription and generated-state reproduction.'
    }
    if write:OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))
    return out
if __name__=='__main__':main(True)
