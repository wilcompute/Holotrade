#!/usr/bin/env python3
"""Provenance firewall for FI-dependent Z6-II vacuum claims.

The current Z6-II vacuum arc (model Z6II_34 / SM_20260917_1558) reports that
only displayed U(1) direction 8 can absorb the D-term residue, while
IsFirstU1Anomalous=1.  It then interprets this as a basis mismatch.

That interpretation is NOT reproducible from the committed artifacts:

* the Z6-II scripts preserve only summary booleans/indices; they do not archive
  the actual U(1) generator matrix, the singlet charge matrix used by the LP,
  or the code/output that produced Tr Q = Tr Q^3 = 0;
* the repository's fresh Z6-I exporter analysis/flagship_fi_weight_dump.cpp
  prints GaugeGroup.u1directions directly and its audit verifies
      IsFirstU1Anomalous = 1,
      anomalous generator = u1directions[0],
      norm(t_A)^2 = 50/3,
      Tr Q_A = D0_FI_term = 200.
  Thus the statement that AnalyseModel leaves the displayed U(1)s in another
  basis is not established as a general Orbifolder behavior;
* an anomaly trace must use the appropriate chiral spectrum; the missing
  Z6-II trace calculation cannot be audited for this selection.

Consequently the rank-7 statement after dropping SUSY is independent and may
stand, but every statement that the corresponding point is D-flat via the FI
term is quarantined until the exact Z6-II generator and charge matrix are
dumped in one run.

This is a provenance theorem, not a replacement spectrum calculation.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/w33_z6ii_fi_basis_provenance_firewall.json'

def main(write=True):
    nonsusy=json.loads((ROOT/'data/w33_nonsusy_full_rank_and_basis_problem.json').read_text())
    assert nonsusy['model']=='Z6II_34 / SM_20260917_1558'
    assert nonsusy['susy_dropped']['rank']==7
    assert nonsusy['basis_problem']['grown_feasible_dirs']==[8]
    assert nonsusy['basis_problem']['orbifolder_says_first_is_anomalous'] is True

    src=(ROOT/'analysis/flagship_fi_weight_dump.cpp').read_text()
    audit=(ROOT/'analysis/flagship_full_cartan_fi_audit.py').read_text()
    assert 'GaugeGroup.u1directions[a][j]' in src
    assert 'IsFirstU1Anomalous' in src and 'D0_FI_term' in src
    assert "t=generators[0]" in audit
    assert "header[1]=='1'" in audit
    assert "t.dot(t)==s.Rational(50,3)" in audit

    required=[
      'model identifier and exact orbifolder input',
      'IsFirstU1Anomalous and D0_FI_term',
      'all GaugeGroup.u1directions in printed order',
      'every singlet label used by the D-flat LP and its charge under every printed generator',
      'the exact LP matrix with row/column labels',
      'the exact chiral-state set used for Tr Q and Tr Q^3',
      'a check that LP direction 0 is the printed anomalous generator']
    out={
      'schema':'w33.z6ii_fi_basis_provenance_firewall.v1',
      'status':'PASS_QUARANTINE_FI_DEPENDENT_Z6II_VACUUM',
      'model':'Z6II_34 / SM_20260917_1558',
      'independent_result_that_survives':{
        'dropping_SUSY_triplet_rank':7,
        'needed_rank':7,
        'reason':'mass-matrix rank is independent of which U(1) is anomalous'},
      'conditional_results':[
        'the 10-singlet candidate is D-flat via an FI term',
        'the grown 24-singlet set is D-flat via an FI term',
        'the nonsupersymmetric rank-7 point is approximately D-flat'],
      'conflict':{
        'reported_only_feasible_displayed_direction':8,
        'reported_IsFirstU1Anomalous':True,
        'reported_direction0_feasible':False,
        'reported_direct_traces_zero':'stored only as summary values; reproducer absent'},
      'committed_control':{
        'producer':'analysis/flagship_fi_weight_dump.cpp',
        'audit':'analysis/flagship_full_cartan_fi_audit.py',
        'fact':'for the fresh Z6-I export, u1directions[0] is explicitly used as the anomalous generator when IsFirstU1Anomalous=1',
        'norm_squared':'50/3',
        'FI_trace':200},
      'repository_manifest':{
        'raw_z6ii_model_file_committed':False,
        'raw_z6ii_u1_generators_committed':False,
        'raw_z6ii_lp_charge_matrix_committed':False,
        'raw_z6ii_trace_reproducer_committed':False},
      'minimum_reproduction_contract':required,
      'decision':'Do not treat direction 8 as the physical anomalous U(1) and do not promote any FI-dependent Z6-II vacuum statement until a single raw export satisfies the reproduction contract.',
      'possible_failure_modes_to_distinguish':[
        'the LP charge columns are not in GaugeGroup.u1directions order',
        'the LP uses a transformed/non-orthogonal charge basis',
        'the zero-trace diagnostic summed the wrong state set rather than the massless left-chiral spectrum',
        'a genuine model/export convention difference exists'],
      'parents':[
        'data/w33_nonsusy_full_rank_and_basis_problem.json',
        'analysis/flagship_fi_weight_dump.cpp',
        'analysis/flagship_full_cartan_fi_audit.py'],
      'checks':{
        'rank7_parent_loaded':True,
        'direction8_conflict_loaded':True,
        'fresh_exporter_prints_u1directions':True,
        'fresh_audit_uses_first_as_anomalous':True,
        'z6ii_fi_claim_is_not_reproducible_from_committed_raw_data':True}}
    if write:OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2));return out

if __name__=='__main__':main(True)
