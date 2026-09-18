#!/usr/bin/env python3
"""Selection-rule search around the exact T2/T4 D-flat singlet pair.

Let
  a = T2(-s), with R=(-1/3,-2/3,0), gamma=-1,
  b = T4(+s), with R=(-2/3,-1/3,0), gamma=+1.
Their full E8 gauge momenta are opposite.

1. Pair-only monomials:
Gauge invariance forces equal powers a^n b^n.  Every such monomial has R3=0,
while a superpotential coupling requires sum R3=-1 mod2.  Therefore no
pair-only superpotential monomial exists at any degree.

2. First neutral-U3 insertion:
Take a gauge-neutral untwisted U3 modulus u with R=(0,0,-1).
For u(a b)^n the R rules are
  -n = -1 mod6,
  -n = -1 mod3,
  -1 = -1 mod2,
so n=1 mod6.  The cubic n=1 is excluded by the G2 gamma rule because it has
exactly one nontrivial gamma eigenstate.  The next solution is n=7, degree 15.
It has seven nontrivial T2 gamma eigenstates, so it is not excluded by the
single-nontrivial-gamma prohibition; point-group sum is 7(2+4)=42=0 mod6 and
the pair gauge momenta cancel exactly.

This proves all-order absence of pair-only self-couplings and identifies the
first standard-selection-rule candidate involving a neutral U3 modulus.
It does NOT prove that the degree-15 CFT coefficient is nonzero, nor that a
modulus insertion should be interpreted as an ordinary polynomial coupling
rather than moduli dependence of an instanton amplitude.
"""
from __future__ import annotations
import json
from fractions import Fraction as F
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/w33_z6ii_singlet_pair_superpotential_search.json'

Ra=(F(-1,3),F(-2,3),F(0))
Rb=(F(-2,3),F(-1,3),F(0))
Ru=(F(0),F(0),F(-1))

def r_allowed(R):
    return ((R[0]+1)/6).denominator==1 and ((R[1]+1)/3).denominator==1 and ((R[2]+1)/2).denominator==1

def main(write=True):
    pair_only=[]
    for n in range(1,61):
        R=tuple(n*(Ra[i]+Rb[i]) for i in range(3))
        if r_allowed(R):pair_only.append(n)
    assert pair_only==[]
    cand=[]
    for n in range(1,61):
        R=tuple(Ru[i]+n*(Ra[i]+Rb[i]) for i in range(3))
        if not r_allowed(R):continue
        point_group=(n*(2+4))%6
        # G2 rule from Buchmueller et al. Eq.(4.12): with only T2/T4 content,
        # exactly one nontrivial gamma among otherwise trivial eigenstates is forbidden.
        gamma_forbidden=(n==1)
        cand.append({'pair_power_n':n,'degree':2*n+1,'R':[str(x) for x in R],
                     'point_group_mod6':point_group,'single_nontrivial_gamma_forbidden':gamma_forbidden})
    assert cand[0]['pair_power_n']==1 and cand[0]['single_nontrivial_gamma_forbidden']
    first=next(x for x in cand if not x['single_nontrivial_gamma_forbidden'])
    assert first['pair_power_n']==7 and first['degree']==15
    out={'schema':'w33.z6ii_singlet_pair_superpotential_search.v1',
      'status':'PASS_PAIR_SELFCOUPLING_NO_GO__DEG15_EXTERNAL_LIFT_CANDIDATE',
      'pair':{
        'a':'T2(-s), R=(-1/3,-2/3,0), gamma=-1',
        'b':'T4(+s), R=(-2/3,-1/3,0), gamma=+1',
        'gauge_momenta':'exact opposites'},
      'all_order_pair_only':{
        'gauge_invariant_form':'(a b)^n',
        'R3':'0 for every n',
        'required_superpotential_R3':'-1 mod2',
        'allowed_positive_n':[],
        'conclusion':'no pair-only superpotential self-coupling at any order'},
      'neutral_U3_search':{
        'assumed_field':'gauge-neutral untwisted U3 modulus with R=(0,0,-1)',
        'R_solution':'n=1 mod6 for u(ab)^n',
        'n1_degree3':'forbidden by G2 gamma selection: exactly one nontrivial T2 gamma eigenstate',
        'first_not_forbidden_by_standard_rules':first,
        'operator':'U3 * [T2(-s) T4(s)]^7'},
      'interpretation':'The D-flat pair is protected against self-couplings to all orders. Standard discrete rules first permit an external neutral-U3 lifting candidate at degree 15.',
      'boundary':'No nonzero degree-15 CFT coefficient is claimed. The complete singlet ledger can contain other external fields and lower-degree lifting operators; hidden-E8/U(1)^5 charges still need enumeration.',
      'literature_basis':'Buchmueller et al. Eq.(4.8) discrete R rules and Eq.(4.12) G2 gamma/space-group rule.'}
    if write:OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2));return out
if __name__=='__main__':main(True)
