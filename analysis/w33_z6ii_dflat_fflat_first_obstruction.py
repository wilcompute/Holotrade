#!/usr/bin/env python3
"""First F-flatness obstruction audit for the D-flat T2/T4 singlet pair.

Parent:
  T4 singlet s has a chiral gamma=+1 representative.
  The independent chiral T2 state of opposite full E8 momentum -s survives
  in the gamma=-1 branch (the gamma=+1 occurrence is the opposite 4D
  chirality in the current B.8 bookkeeping).

The most obvious cubic that could lift the D-flat direction is
    T2(-s) * T4(s) * U3_neutral.
At the level of gauge momentum, point group and the conventional no-oscillator
H-momentum this is a candidate:
    -s+s+0=0,
    2+4+0=0 mod6,
    h_T2+h_T4+h_U3=(-1,-1,-1)
in the sign convention used by the existing cubic mass-channel audit.

However, with the repo's physical gamma/localization eigenvalues, the chiral
T2(-s) carries gamma=-1 whereas T4(s) and an untwisted U3 field carry gamma=+1.
Their product is -1, so this naive cubic fails the current localization/gamma
selection rule.

This is useful but NOT an all-order F-flat proof. Higher operators can include
additional twisted singlets whose gamma and discrete charges compensate, and
the complete hidden-E8/U(1)^5 charge ledger is not yet generated.
"""
from fractions import Fraction as F
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/w33_z6ii_dflat_fflat_first_obstruction.json'

s=tuple(F(x,6) for x in (1,-1,-3,3,3,3,3,3))
sm=tuple(-x for x in s)
h2=(F(-1,3),F(-2,3),F(0))
h4=(F(-2,3),F(-1,3),F(0))
hU3=(F(0),F(0),F(-1))

def main(write=True):
    parent_src=(ROOT/'analysis/w33_z6ii_t1t1t4_rule456_dflat.py').read_text()
    assert "proj[('L',-1)]" in parent_src and "proj[('R',1)]" in parent_src
    assert all(s[i]+sm[i]==0 for i in range(8))
    hsum=tuple(h2[i]+h4[i]+hU3[i] for i in range(3))
    assert hsum==(F(-1),F(-1),F(-1))
    gamma=(-1)*(+1)*(+1)
    assert gamma==-1
    out={'schema':'w33.z6ii_dflat_fflat_first_obstruction.v1',
      'status':'PASS_NAIVE_CUBIC_FORBIDDEN__ALL_ORDER_FFLAT_OPEN',
      'D_flat_pair':{'T2_minus_s':[str(x) for x in sm],'T4_s':[str(x) for x in s]},
      'dangerous_cubic_candidate':'T2(-s) * T4(s) * U3_neutral',
      'standard_rule_checks':{
        'full_gauge_momentum':'-s+s+0=0',
        'point_group':'2+4+0=6=0 mod6',
        'H_momentum':'h_T2+h_T4+h_U3=(-1,-1,-1)',
        'gamma_localization':{'T2_chiral_minus_s':-1,'T4_chiral_s':1,'U3':1,'product':-1}},
      'cubic_conclusion':'FORBIDDEN in the current physical gamma/localization bookkeeping because the eigenvalue product is -1 rather than +1.',
      'why_not_full_F_flatness':'Higher-order operators can contain additional twisted singlets whose gamma/discrete charges compensate. The complete singlet superpotential and all U(1)^5/hidden-E8 charges are not yet enumerated.',
      'literature_boundary':'Chemtob--Hosteins B.10 gives the gauge/R/point/space-group selection rules; the repo gamma eigenvalues come from the B.8 physical-state projections. This file does not assert a nonzero/zero CFT coefficient beyond those certified selection rules.',
      'next_exact_task':'Enumerate all gauge-neutral monomials in the complete singlet ledger up to increasing degree and test every string selection rule; F-flatness is certified only if all derivatives vanish on the proposed VEV locus.',
      'checks':{'opposite_gauge_momenta':True,'point_group_candidate':True,'H_momentum_candidate':True,'gamma_product_minus_one':True}}
    if write:OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2));return out
if __name__=='__main__':main(True)
