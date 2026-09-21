#!/usr/bin/env python3
"""Exhaustive matter-even D-flat cone: corrected source-data/proof gate."""
from __future__ import annotations
import argparse,glob,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/w33_matter_even_dflat_exhaustive_gate.json"

def build():
    mp=json.loads((ROOT/"data/w33_matter_parity_z2_correction.json").read_text())
    df=json.loads((ROOT/"data/w33_dflat_needs_a_matter_odd_singlet.json").read_text())
    corr=json.loads((ROOT/"data/w33_fixed_support_z2_correction.json").read_text())
    sampled=(ROOT/"analysis/w33_bminusl_freedom_search.py").read_text()
    raw={pat:sorted(str(Path(p).relative_to(ROOT)) for p in glob.glob(str(ROOT/pat)))
         for pat in ("sp1/*.sp","sp2/*.sp")}
    nraw=sum(len(v) for v in raw.values())
    parser=(ROOT/"unbroken2.py").exists()
    executable=nraw>0 and parser
    status=("READY_FOR_EXHAUSTIVE_PARITY_CONE_ENUMERATION" if executable
            else "BLOCKED_EXHAUSTIVE_CLASS_PROOF_SOURCE_DATA_NOT_COMMITTED")
    assert mp["bl"]["with_BL"]==88
    assert df["freedom"]["samples_per_model"]==60
    assert df["freedom"]["dflat_even"]==0
    assert corr["status"]=="CORRECTION_FIXED_SUPPORT_0_OF_24_IS_FULL_U1_NOT_Z2_EVIDENCE"
    assert "v.q == 1 and v % 2 == 0" in sampled
    return {
      "schema":"holotrade.w33_matter_even_dflat_exhaustive_gate.v2",
      "status":status,
      "headline":"The class-wide exact Z2 D-flat verdict remains blocked by missing raw charge ledgers. The old fixed-support 0/24 result is removed from Z2 evidence because it solved exact neutrality 3(B-L)=0 rather than even integrality.",
      "current_git_inputs":{
        "raw_globs":raw,"raw_model_files":nraw,
        "parser_path":"unbroken2.py","parser_present":parser,
        "classwide_exact_enumeration_executable":executable
      },
      "current_evidence":{
        "models_with_BL":88,
        "B_minus_L_nullspace_dims":mp["bl"]["nullspace_dims"],
        "sampled_choices_per_model":60,
        "sampled_even_singlet_Dflat_hits":0,
        "sampled_test_uses_correct_Z2_condition":True,
        "fixed_Dflat_support_models":df["support"]["models"],
        "legacy_fixed_support_zero_charge_shift_successes":df["support"]["exact_shift_succeeds"],
        "legacy_fixed_support_result_grade":"VALID_FULL_U1_NEUTRALITY_ONLY_WITHDRAWN_AS_Z2_EVIDENCE",
        "fixed_support_exact_Z2_result":None,
        "is_exhaustive_proof":False
      },
      "exact_problem":{
        "affine_BL":"x=x0+Nt over Q",
        "parity_condition":"3(x.Q_s) is an integral even number",
        "fractional_condition":"fractional 3(B-L) is inadmissible, not even/odd",
        "enumeration":"enumerate every realizable affine parity/integrality class",
        "cone":"solve D-flatness exactly on each class even singlets",
        "certificate":"exact primal ray if feasible; exact Farkas dual witness if infeasible"
      },
      "proof_acceptance_rule":"Promote a class-wide no-go only after every realizable parity class in every B-L model has an exact infeasibility witness; any exact primal witness refutes it.",
      "boundary":"Strong sampled evidence remains. There is currently no exact fixed-support Z2 result and no exhaustive class-wide proof.",
      "checks":{
        "summaries_present":True,
        "legacy_fixed_support_Z2_claim_withdrawn":True,
        "sampled_search_correctly_tests_even_integrality":True,
        "raw_model_dumps_missing":nraw==0,
        "parser_missing":not parser,
        "proof_refused_without_sources":not executable
      }
    }

def main(write=True):
    out=build()
    if write:OUT.write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps(out,indent=2));return out

if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--check",action="store_true");a=ap.parse_args()
    main(not a.check)
