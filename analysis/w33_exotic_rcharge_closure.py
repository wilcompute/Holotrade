#!/usr/bin/env python3
"""R-charge closure for the frozen W33 SU(5) exotic mass candidates.

The preceding certificate w33_exotic_quartic_selection.json found 972 operators
5_T 5bar_U S_T S_T that pass gauge, point-group and space-group rules, but the
old spectrum builder had discarded right-moving/H-momentum labels.  For this
specific witness no reconstruction ambiguity remains: the twisted 5 and all
singlets used by those operators occur in multiplicity-one (N_L=0) twisted
shells, while the untwisted multiplicity three is the three complex-plane
copies U_i.

For T^6/Z3 with v=(1/3,1/3,-2/3), represented with positive fractional
components, an oscillatorless k=1 twisted scalar has
    R_T=(1/3,1/3,1/3).
The untwisted scalar U_i has R_{U_i}=e_i.  The standard picture-independent
orbifold rule is sum R^i = 1 mod 3 in each complex plane.  Hence every quartic
T U_i T T has sum R=(2,1,1) up to permutation and is forbidden.

The same arithmetic gives a stronger all-orders statement: point-group
invariance forces the number of k=1 twisted fields to be 3m.  A coupling with
exactly one U_i and otherwise oscillatorless k=1 twisted fields would require
simultaneously m=1 mod3 in the two other planes and m=0 mod3 in plane i, which
is impossible.
"""
from __future__ import annotations
import json
from fractions import Fraction
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'data'/'w33_exotic_quartic_selection.json'
OUT=ROOT/'data'/'w33_exotic_rcharge_closure.json'

RT=(Fraction(1,3),)*3
U=((Fraction(1),0,0),(0,Fraction(1),0),(0,0,Fraction(1)))

def add(*vs): return tuple(sum(v[i] for v in vs) for i in range(3))
def allowed(R):
    # With fractional normalization used in the heterotic-orbifold literature,
    # the condition is sum R^i = 1 mod 3 plane by plane.
    return all((x-Fraction(1))/3 == int((x-Fraction(1))/3) for x in R)

def main(write=True):
    parent=json.loads(SRC.read_text())
    assert parent['status']=='PASS'
    assert parent['gauge_and_space_group']['candidate_quartic_monomials']==972
    quartic=[]
    for i in range(3):
        R=add(RT,RT,RT,U[i])
        quartic.append({'untwisted_plane':i,'R_sum':[str(x) for x in R],
                        'allowed':allowed(R)})
    assert not any(x['allowed'] for x in quartic)

    # All-orders no-go for exactly one untwisted field and 3m oscillatorless
    # k=1 twisted fields.  Checking one full period in m proves the congruence.
    all_orders=[]
    for m in range(3):
        for i in range(3):
            R=tuple(Fraction(m)+U[i][j] for j in range(3))
            all_orders.append((m,i,allowed(R)))
    assert not any(z for _,_,z in all_orders)

    out={
      'schema':'holotrade.w33_exotic_rcharge_closure.v1','status':'PASS',
      'headline':'All 972 gauge/space-group-allowed quartic exotic-mass candidates are forbidden by the exact Z3 R-charge rule. The twisted 5 and singlets are oscillatorless with R=(1/3,1/3,1/3), while an untwisted plane copy has R=e_i; therefore T U_i T T has R=(2,1,1) up to permutation rather than (1,1,1).',
      'parent_certificate':'data/w33_exotic_quartic_selection.json',
      'quantum_numbers':{
        'orbifold_twist':'(1/3,1/3,-2/3) ~ (1/3,1/3,1/3) mod 1',
        'twisted_k1_oscillatorless_R':['1/3','1/3','1/3'],
        'untwisted_plane_R':[['1','0','0'],['0','1','0'],['0','0','1']],
        'selection_rule':'sum_alpha R_alpha^i = 1 mod 3 in every plane'
      },
      'quartic_plane_cases':quartic,
      'candidate_quartics_before_R':972,
      'candidate_quartics_after_R':0,
      'necessary_rule_mass_matrix_rank_after_R':0,
      'all_orders_corollary':'With exactly one untwisted U_i and otherwise oscillatorless k=1 twisted fields, point-group invariance requires 3m twisted insertions. R conservation would demand m=1 mod3 in the two planes other than i but m=0 mod3 in plane i, so no such operator exists at any order.',
      'scope':'This closes the 972 previously enumerated channels and the stated oscillatorless all-orders family. It does not exclude operators involving additional untwisted singlets or twisted oscillator excitations not present in those 972 channels.',
      'sources':['Kobayashi-Parameswaran-Ramos-Sanchez-Zavala, arXiv:1107.2137, eqs. (2.19)-(2.20)'],
      'checks':{'parent_972':True,'all_three_quartic_plane_cases_forbidden':True,
                'quartic_rank_zero_after_R':True,'all_orders_congruence_no_solution':True}
    }
    if write: OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2)); return out
if __name__=='__main__': main(True)
