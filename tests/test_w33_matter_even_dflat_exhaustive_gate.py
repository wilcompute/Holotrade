from __future__ import annotations
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"analysis/w33_matter_even_dflat_exhaustive_gate.py"
def load():
    s=importlib.util.spec_from_file_location("dflatgate",SRC);assert s and s.loader
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def test_current_repo_blocks_exhaustive_claim_without_sources_and_withdraws_bad_exact_z2_claim():
    o=load().main(False)
    assert o["schema"]=="holotrade.w33_matter_even_dflat_exhaustive_gate.v2"
    assert o["status"]=="BLOCKED_EXHAUSTIVE_CLASS_PROOF_SOURCE_DATA_NOT_COMMITTED"
    assert o["current_git_inputs"]["raw_model_files"]==0
    assert o["current_git_inputs"]["parser_present"] is False
    assert o["current_evidence"]["is_exhaustive_proof"] is False
    assert o["current_evidence"]["sampled_even_singlet_Dflat_hits"]==0
    assert o["current_evidence"]["sampled_test_uses_correct_Z2_condition"] is True
    assert o["current_evidence"]["fixed_support_exact_Z2_result"] is None
    assert "WITHDRAWN_AS_Z2_EVIDENCE" in o["current_evidence"]["legacy_fixed_support_result_grade"]
    assert o["checks"]["proof_refused_without_sources"] is True
