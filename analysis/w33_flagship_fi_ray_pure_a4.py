#!/usr/bin/env python3
"""Exact FI-ray / hypercharge-A4 organizer bridge for the flagship.

Inputs already certified in this repository:
  * analysis/flagship_full_cartan_fi_audit.json:
      physical anomalous generator t_A in the full E8 x E8 Cartan,
      ||t_A||^2=50/3, Tr Q_A=200;
  * data/w33_flagship_a5_hypercharge_organizer.json:
      the rank-five Abelian complement is A5,
      hypercharge Y=-omega1(A5),
      and the integral Y-orthogonal sector is A4=<alpha2,...,alpha5>.

Take the eight components of t_A on the A5-organizer E8 factor.  Exact rational
linear algebra gives

    t_A^(A5 factor) . Y = 0

and

    t_A^(A5 factor)
      = -5/3 alpha2 -2/3 alpha3 -1/3 alpha4 -2 alpha5.

Thus the physical FI ray has NO hypercharge component on this factor.  Its
A5-organizer projection is entirely inside the four-dimensional A4 sector
that a hypercharge-preserving vacuum must Higgs.

The coefficients are primitive after multiplying by three:
    3 c = (-5,-2,-1,-6).

In the repository's S6-duad model of the A5 weight lattice, use standard A5
coordinates e1,...,e6 with alpha_i=e_i-e_{i+1}.  Since there is no alpha1
component, the A4 vector has coordinates

    x=(0,-5/3,1,1/3,-5/3,2),  sum x_i=0.

The five duads through the distinguished hypercharge vertex therefore carry
Psi(x)_{1j}=x_j/2.  Multiplying by six gives the primitive zero-sum star
pattern
    (-5,3,1,-5,6), sum=0.

This is exactly the type of A4 zero-sum fluctuation identified independently
as the four-dimensional part of the five-dimensional neutral bracket cokernel
Y(1)+A4(4).

Boundary:
  t_A also has a nonzero component in the other E8 factor.  This theorem says
  that its projection onto the flagship A5/hypercharge organizer has zero Y
  component and a nonzero A4 component.  It does not by itself construct a
  D/F-flat vacuum or identify the full FI generator with the W33 bracket
  cokernel.
"""
from __future__ import annotations
import json, math
from fractions import Fraction as F
from pathlib import Path
import sympy as s

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/w33_flagship_fi_ray_pure_a4.json'

def q(x): return s.Rational(str(x))

def main(write=True):
    fi=json.loads((ROOT/'analysis/flagship_full_cartan_fi_audit.json').read_text())
    org=json.loads((ROOT/'data/w33_flagship_a5_hypercharge_organizer.json').read_text())
    assert fi['status']=='PASS'
    assert org['status']=='PASS_A5_HYPERCHARGE_ORGANIZER'

    t=s.Matrix([s.Rational(x) for x in fi['anomalous_generator']])
    assert len(t)==16 and (t.dot(t)==s.Rational(50,3))
    ta=t[8:16,:]
    Y=s.Matrix([s.Rational(x) for x in org['hypercharge']['Y']])
    assert ta.dot(Y)==0

    roots=[s.Matrix([s.Rational(x) for x in r]) for r in org['A5']['simple_roots_E8']]
    A4=s.Matrix.hstack(*roots[1:])
    sol=s.linsolve((A4,ta))
    coeff=next(iter(sol))
    expected=(s.Rational(-5,3),s.Rational(-2,3),s.Rational(-1,3),s.Rational(-2))
    assert tuple(coeff)==expected
    assert A4*s.Matrix(coeff)==ta

    # Pairings reproduce the independently stored four organizer projections.
    cartan=s.Matrix([[2,-1,0,0],[-1,2,-1,0],[0,-1,2,-1],[0,0,-1,2]])
    pair=cartan*s.Matrix(coeff)
    stored=s.Matrix([s.Rational(x) for x in fi['FI_projection_on_four_organizer_roots']])
    assert pair==stored

    # Standard A5 coordinates for sum c_i alpha_i with c1=0.
    c2,c3,c4,c5=coeff
    x=s.Matrix([0,c2,-c2+c3,-c3+c4,-c4+c5,-c5])
    assert sum(x)==0
    star=[v/2 for v in x[1:]]
    sixstar=[6*v for v in star]
    assert sixstar==[-5,3,1,-5,6]
    assert sum(sixstar)==0

    other=t[:8,:]
    assert other.dot(other)==6
    assert ta.dot(ta)==s.Rational(32,3)
    assert other.dot(other)+ta.dot(ta)==t.dot(t)

    out={
      'schema':'w33.flagship_fi_ray_pure_a4.v1',
      'status':'PASS_EXACT_FI_RAY_ORTHOGONAL_TO_HYPERCHARGE',
      'headline':'The physical anomalous-U(1) generator of the flagship has exactly zero component along canonical hypercharge on the A5-organizer E8 factor. Its organizer projection is entirely A4: t_A=-5/3 alpha2-2/3 alpha3-1/3 alpha4-2 alpha5. In the S6-duad realization this is the primitive zero-sum star fluctuation six*Psi_star=(-5,3,1,-5,6). Thus the FI instability pushes the extra-U(1) A4 sector while leaving Y unshifted.',
      'FI':{
        'trace':fi['FI_trace'],
        'full_norm_squared':fi['generator_norm_squared'],
        'other_E8_norm_squared':'6',
        'A5_organizer_factor_norm_squared':'32/3'},
      'hypercharge':{
        'dot_tA_Y':'0',
        'Y_norm_squared':org['hypercharge']['norm2'],
        'kY':org['hypercharge']['kY']},
      'A4':{
        'simple_root_basis':['alpha2','alpha3','alpha4','alpha5'],
        'coefficients':[str(v) for v in coeff],
        'primitive_three_times_coefficients':[-5,-2,-1,-6],
        'pairings_with_A4_simples':[str(v) for v in pair],
        'reproduces_stored_FI_projection':True},
      'A5_standard_coordinates':[str(v) for v in x],
      'duad_star':{
        'Psi_star_coordinates':[str(v) for v in star],
        'six_times_star':sixstar,
        'zero_sum':True},
      'physical_reading':'Within the flagship A5 Abelian organizer, the FI ray is hypercharge-preserving and points purely into the four extra U(1) directions. A viable vacuum must still cancel the full D term with singlet VEVs and satisfy non-Abelian D terms and F terms.',
      'cross_repo_target':'W33-Theory data/w33_hypercharge_duad_center_cokernel.json independently refines the neutral 5-dimensional bracket cokernel as Y(1)+A4(4); this file supplies the physical FI vector inside that A4 factor.',
      'boundary':'The anomalous generator also has norm-squared 6 in the other E8 factor. No full FI-ray equals bracket-cokernel identification or vacuum existence is claimed.',
      'parents':['analysis/flagship_full_cartan_fi_audit.json','data/w33_flagship_a5_hypercharge_organizer.json'],
      'checks':{
        'physical_FI_generator_loaded':True,
        'tA_dot_Y_zero':True,
        'tA_A5_projection_in_A4_exactly':True,
        'A4_coefficients_exact':True,
        'stored_simple_pairings_reproduced':True,
        'duad_star_zero_sum':True,
        'norm_decomposition_6_plus_32over3_equals_50over3':True}}
    if write:OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2));return out

if __name__=='__main__':main(True)
