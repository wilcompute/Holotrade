#!/usr/bin/env python3
"""Cross-certificate: anomalous-FI cancellation versus exotic-mass rank.

This integrates two independently frozen fronts of the same SU(5) witness:

* w33_su5_fi_degree12_flatness.json: Tr Q_A=-72 and the two minimal
  FI-cancelling untwisted singlet pairs are U(0,1) and U(2,3), each Q_A=+2;
* w33_exotic_mass_rank_by_condensate.json: the sextic exotic channels use
  exactly those untwisted pairs, but the 9x12 exotic mass rank is controlled by
  the fixed-point profiles of four twisted-singlet types.

The compatibility is therefore exact at charge/VEV-type level, but it does not
by itself prove complete exotic decoupling. Translation-symmetric twisted VEVs
force rank one. A single fixed-point support has rank at most four. Rank nine
is first reachable with support size two and becomes generic in the measured
finite experiment by support size four.

This file deliberately does not manufacture an F-flat nonuniform vacuum.  It
freezes the correct remaining question: find a D- and F-flat assignment in
which the four twisted singlet types have sufficiently nonuniform profiles.
"""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data'/'w33_fi_exotic_condensate_compatibility.json'

def main(write=True):
    fi=json.loads((ROOT/'data'/'w33_su5_fi_degree12_flatness.json').read_text())
    ex=json.loads((ROOT/'data'/'w33_exotic_mass_rank_by_condensate.json').read_text())
    assert fi['status']=='PASS' and ex['valid']
    pairs=[x['U_indices'] for x in fi['FI_cancelling_pairs']]
    assert pairs==[[0,1],[2,3]]
    assert fi['anomalous_U1']['Tr_Q_A']==-72
    assert ex['credited']['untwistedPairsAreTheFIBilinears']
    assert ex['rankByNamedProfile']['translation_invariant']==[1]
    assert ex['rankByNamedProfile']['diagonal_line_of_the_degree12_cube']==[1]
    assert ex['rankBySupportSize']['1']['maxRank']==4
    assert ex['rankBySupportSize']['2']['maxRank']==9
    assert ex['rankBySupportSize']['4']['fractionRank9']==1.0
    out={
      'schema':'holotrade.w33_fi_exotic_condensate_compatibility.v1','status':'PASS',
      'headline':'The anomalous-FI and exotic-decoupling fronts are charge-compatible but vacuum-profile constrained. The two FI-cancelling untwisted bilinears U0U1 and U2U3 are exactly the untwisted pairs entering the sextic exotic operators. However translation-symmetric twisted-singlet VEVs give exotic-mass rank 1; rank 9 requires a sufficiently nonuniform fixed-point profile.',
      'FI':{'Tr_Q_A':fi['anomalous_U1']['Tr_Q_A'],'cancelling_untwisted_pairs':pairs,'pair_Q_A':[x['total_Q_A'] for x in fi['FI_cancelling_pairs']]},
      'operator_compatibility':{'sextic_channels_use_FI_pairs':True,'twisted_pair_per_antifive_type':ex['twistedPairPerAntifiveType']},
      'rank_constraints':{
        'translation_invariant':1,
        'degree12_diagonal_profile':1,
        'single_fixed_point_upper_bound':4,
        'support_size_2_can_reach_rank9':True,
        'support_size_2_measured_fraction_rank9':ex['rankBySupportSize']['2']['fractionRank9'],
        'support_size_3_measured_fraction_rank9':ex['rankBySupportSize']['3']['fractionRank9'],
        'support_size_4_measured_fraction_rank9':ex['rankBySupportSize']['4']['fractionRank9']},
      'physics_consequence':'FI cancellation and the higher-order exotic operators use compatible massless fields, so there is no charge-level obstruction to combining them. Complete exotic decoupling nevertheless requires a D/F-flat vacuum whose four twisted-singlet species are spread nonuniformly over multiple fixed points. No such vacuum is certified here.',
      'correction_to_old_benchmark':'The earlier Vandermonde rank-nine matrix proves that full rank is algebraically possible in an unconstrained coefficient space, but it is not a physical-vacuum certificate because the nine rows are correlated by fixed-point VEV profiles.',
      'open_problem':'Solve the F-term equations on the FI-shifted vacuum moduli including the degree-12 quartic cubes and the sextic/nonic exotic couplings; determine whether a nonuniform rank-nine fixed-point profile survives.',
      'checks':{'TrQ_minus72':True,'FI_pairs_01_23':True,'sextic_uses_FI_pairs':True,'symmetric_rank1':True,'single_point_rank_le4':True,'rank9_reachable_from_support2':True}}
    if write:OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2));return out
if __name__=='__main__':main(True)
