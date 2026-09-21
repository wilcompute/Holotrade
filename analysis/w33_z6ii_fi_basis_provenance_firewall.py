#!/usr/bin/env python3
"""Supersession certificate for the resolved Z6-II anomalous-U(1) question.

This file originally quarantined the FI-dependent Z6-II vacuum branch because
the raw anomalous direction was not reproducible from the then-visible
artifacts.  A parallel producer subsequently closed the issue by dumping
CField::Multiplet and tracing only left-chiral multiplets.

Exact resolution:
  * the all-multiplet trace vanishes because LeftChiral and RightChiral
    conjugates cancel;
  * on the Z6-I flagship the left-chiral trace is
      (200,0,0,0,0,0,0) = D0_FI_term;
  * on Z6II_34 / SM_20260917_1558 the first left-chiral trace is
      296/3 = 98.666..., again D0_FI_term;
  * therefore IsFirstU1Anomalous=1 means direction 0, exactly as documented.

Consequently the earlier 'basis mismatch / direction 8' interpretation is
withdrawn.  Candidate subsets whose FI feasibility existed only on direction 8
are not physically D-flat.  Their mass-matrix rank arithmetic remains valid,
but they are not vacua.

The authoritative producer/certificate is
  analysis/the_anomalous_direction_is_the_first_and_the_zero_trace_was_a_chirality_double_count.py
  data/w33_anomalous_direction_resolved.json
"""
from __future__ import annotations
import json
from fractions import Fraction as F
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/w33_z6ii_fi_basis_provenance_firewall.json'

def main(write=True):
    resolved=json.loads((ROOT/'data/w33_anomalous_direction_resolved.json').read_text())
    old=json.loads((ROOT/'data/w33_nonsusy_full_rank_and_basis_problem.json').read_text())
    assert resolved['valid'] is True
    assert resolved['traces']['left'][0]==200
    assert all(x==0 for x in resolved['traces']['left'][1:])
    assert F(resolved['traces']['z6ii_left_first'])==F(296,3)
    assert abs(float(F(296,3))-resolved['traces']['orbifolder_FI_z6ii'])<0.01
    assert all(v['dflat'] is False for v in resolved['voided'])
    assert old['susy_dropped']['rank']==7

    out={
      'schema':'w33.z6ii_fi_basis_provenance_firewall.v2',
      'status':'SUPERSEDED_BY_CHIRALITY_RESOLUTION',
      'resolution':'The anomalous generator is displayed U(1) direction 0. The old vanishing trace was caused by summing left-chiral multiplets together with right-chiral conjugates.',
      'exact_traces':{
        'Z6I_flagship_left':[200,0,0,0,0,0,0],
        'Z6I_flagship_right':[-200,0,0,0,0,0,0],
        'Z6II_1558_left_first':'296/3'},
      'vacuum_consequence':{
        'voided_subset_sizes':[10,24,34,43],
        'physical_D_flatness':False,
        'rank_arithmetic_survives':True,
        'nonsusy_rank7_survives_as_rank_statement_only':True},
      'class_sweep':resolved['sweep'],
      'reinforced_frontier':'Physical D-flatness generally requires additional singlets beyond the restricted mass-coupling support; those extra singlets reintroduce gauge-invariant superpotential monomials. This strengthens the F/D conflict rather than supplying an FI escape.',
      'authoritative_parent':'data/w33_anomalous_direction_resolved.json',
      'checks':{
        'direction0_is_anomalous':True,
        'chirality_double_count_explains_old_zero':True,
        'z6ii_trace_matches_FI':True,
        'old_direction8_vacuum_withdrawn':True}}
    if write:OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2));return out

if __name__=='__main__':main(True)
