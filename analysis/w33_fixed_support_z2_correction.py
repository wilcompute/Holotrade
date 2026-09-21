#!/usr/bin/env python3
"""Correct the legacy fixed-support exact parity test."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/w33_fixed_support_z2_correction.json"

def main(write=True):
    legacy=(ROOT/"analysis/w33_dflat_support_parity_exact.py").read_text()
    sampled=(ROOT/"analysis/w33_bminusl_freedom_search.py").read_text()
    summary=json.loads((ROOT/"data/w33_dflat_needs_a_matter_odd_singlet.json").read_text())
    zero_equation=(
        "3((x0 + N t).Q_s) = 0" in legacy
        and "c = Matrix([-3 * dot" in legacy
        and "t = solve_exact(M, c)" in legacy
    )
    sampled_even=("v.q == 1 and v % 2 == 0" in sampled and "dflat_even" in sampled)
    legacy_count=summary["support"]["exact_shift_succeeds"]
    q3bl=2
    checks={
      "legacy_source_imposes_exact_zero":zero_equation,
      "legacy_summary_count_is_zero":legacy_count==0,
      "sampled_search_uses_even_integrality":sampled_even,
      "even_nonzero_witness_exists":q3bl%2==0 and q3bl!=0
    }
    assert all(checks.values()),checks
    out={
      "schema":"holotrade.w33_fixed_support_z2_correction.v1",
      "status":"CORRECTION_FIXED_SUPPORT_0_OF_24_IS_FULL_U1_NOT_Z2_EVIDENCE",
      "legacy_result":{
        "models":summary["support"]["models"],
        "reported_successes":legacy_count,
        "actual_question":"Does a B-L shift make every support singlet satisfy 3(B-L)=0 exactly?",
        "valid_interpretation":"0/24 exact shifts preserve the full continuous B-L charge on that chosen LP support.",
        "invalid_interpretation":"0/24 exact shifts make the support matter-even."
      },
      "correct_Z2_condition":"For every condensing singlet s, 3(B-L)_s must be an integral even number; even nonzero values are allowed.",
      "toy_separation":{"three_B_minus_L":2,"matter_even":True,"full_U1_neutral":False},
      "what_still_stands":{
        "sampled_search":"The 60-choice-per-model search used integral-even parity, not exact zero, and found 0 matter-even D-flat hits among sampled choices.",
        "scope":"That sampled zero remains controlled evidence, not an exhaustive proof."
      },
      "required_exact_replacement":"Solve the affine congruence/lattice problem 3(x0+Nt).Q_s in 2Z jointly with exact D-flat cone feasibility; enumerate every realizable parity/integrality class and attach Farkas certificates or primal rays.",
      "checks":checks
    }
    if write:OUT.write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps(out,indent=2));return out
if __name__=="__main__":main(True)
