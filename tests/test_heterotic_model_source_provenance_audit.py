from __future__ import annotations
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load():
    p=ROOT/'analysis/heterotic_model_source_provenance_audit.py'
    s=importlib.util.spec_from_file_location('prov',p); assert s and s.loader
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def test_heterotic_model_source_provenance():
    o=load().main(False)
    assert o['status']=='PASS_RECOVERABLE_VECTOR_LEDGER_FROZEN_BULK_SP_CORPUS_CONFIRMED_ABSENT_FROM_INSPECTED_GIT_TREES'
    assert o['recoverable_set_count']==5
    assert len(o['historical_tree_audit'])==3
    assert all(all(v==0 for v in h['required_path_hits'].values()) for h in o['historical_tree_audit'])
    assert 'sp1/' in o['missing_bulk_inputs']['paths']
    assert 'sp2/' in o['missing_bulk_inputs']['paths']
    assert 'unbroken2.py' in o['missing_bulk_inputs']['paths']
    assert all(o['checks'].values())
