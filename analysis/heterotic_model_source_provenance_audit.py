#!/usr/bin/env python3
"""Freeze the recoverable heterotic model-vector corpus and the missing-source boundary.

This audit distinguishes:
  (A) model-defining vectors that are still committed and can be replayed;
  (B) historical flatness calculations that referenced local/uncommitted
      sp1/, sp2/, and unbroken2.py inputs which are absent from the inspected
      Git trees.

The historical Git tree SHAs were inspected through the GitHub API on
2026-09-21 and are frozen in the certificate.  Runtime checks below validate
that every recoverable vector set is still present in committed repository
sources and has the expected dimension/order role.

No missing spectrum rows are reconstructed or invented.
"""
from __future__ import annotations
import importlib.util,json,sys
from fractions import Fraction as F
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/heterotic_model_source_provenance_audit.json"

def load(path,name):
    s=importlib.util.spec_from_file_location(name,path); assert s and s.loader
    m=importlib.util.module_from_spec(s); sys.modules[name]=m; s.loader.exec_module(m); return m

def vec(s):
    return [F(x.strip()) for part in s.split("|") for x in part.split(",") if x.strip()]

def main(write=True):
    # Z6-I flagship: complete 16D V and W3 are committed in the model writer.
    flagship=load(ROOT/"analysis/w33_flagship_orbifolder_model.py","flagship_model")
    Vflag=list(flagship.V); W3flag=list(flagship.W3); Z16=[F(0)]*16
    assert len(Vflag)==len(W3flag)==16

    # Z6-II constructive model and flagship from the committed census artifact.
    z6ii=json.loads((ROOT/"data/w33_twist_hosts_sm_in_even_order_orbifold.json").read_text())
    z6ii_model=z6ii["model"]; z6i_flag=z6ii["flagship"]
    modelV=vec(z6ii_model["V"]); modelW3=vec(z6ii_model["W3"]); modelW2=vec(z6ii_model["W2"])
    assert all(len(x)==16 for x in (modelV,modelW3,modelW2))
    assert vec(z6i_flag["V"])==Vflag and vec(z6i_flag["W3"])==W3flag

    # Explicit first-E8 Z6-II gauge embedding.
    shape=json.loads((ROOT/"data/w33_z6ii_sm_shape_builder.json").read_text())
    emb=shape["embedding"]
    V6=[F(x) for x in emb["V6"]]; W2=[F(x) for x in emb["W2"]]; W3=[F(x) for x in emb["W3"]]
    assert len(V6)==len(W2)==len(W3)==8

    # Published and corrected/shipped BHLR representatives.
    bhlr=load(ROOT/"analysis/the_w33_standard_models_have_a_renormalisable_top_yukawa.py","bhlr_vectors")
    pub={k:vec(v) for k,v in bhlr.THEIR.items()}
    shipped={k:vec(v) for k,v in bhlr.SHIPPED.items()}
    assert all(len(pub[k])==len(shipped[k])==16 for k in ("V","W2","W3"))
    assert all(bhlr.in_e8xe8([a-b for a,b in zip(pub[k],shipped[k])]) for k in ("V","W2","W3"))

    history=[
      {
        "label":"hidden_raw_branch",
        "ref":"copilot/raw-z6-ii-model-corpus",
        "commit_sha":"21f1dbf324cf03067fc8c2eba281478c05080027",
        "tree_sha":"6f6a888af0773c8e2310d7924c44f3ea8e5ecf65",
        "tree_entries":1479,
        "required_path_hits":{"sp1/":0,"sp2/":0,"unbroken2.py":0}
      },
      {
        "label":"dflat_history_28620b4",
        "commit_sha":"28620b4bec5d467bc36087dccf177e99996de4b7",
        "tree_sha":"a5a4c448d1125f0863e8bd9ef4850150861fa0f6",
        "tree_entries":1448,
        "required_path_hits":{"sp1/":0,"sp2/":0,"unbroken2.py":0}
      },
      {
        "label":"dflat_history_3e655d0",
        "commit_sha":"3e655d045cf0e0503014f47b1d3e7418a86c3ec6",
        "tree_sha":"1dfa5d2daa0c81a47c8a77ec10ef95fb78efd1de",
        "tree_entries":1402,
        "required_path_hits":{"sp1/":0,"sp2/":0,"unbroken2.py":0}
      }
    ]
    assert all(all(v==0 for v in h["required_path_hits"].values()) for h in history)

    recovered=[
      {
        "id":"SM_20260917_3_Z6I_flagship",
        "orbifold":"Z6-I",
        "source":"analysis/w33_flagship_orbifolder_model.py + data/w33_twist_hosts_sm_in_even_order_orbifold.json",
        "V":[str(x) for x in Vflag],
        "W2":[str(x) for x in Z16],
        "W3":[str(x) for x in W3flag],
        "note":"complete 16D gauge data; the committed model writer places W3 in the historical geometric pair 45"
      },
      {
        "id":"SM_20260917_1383_Z6II",
        "orbifold":"Z6-II",
        "source":"data/w33_twist_hosts_sm_in_even_order_orbifold.json",
        "V":[str(x) for x in modelV],
        "W2":[str(x) for x in modelW2],
        "W3":[str(x) for x in modelW3],
        "note":"complete committed 16D Standard-Model witness"
      },
      {
        "id":"explicit_Z6II_first_E8_gauge_embedding",
        "orbifold":"Z6-II",
        "source":"data/w33_z6ii_sm_shape_builder.json",
        "V_first_E8":[str(x) for x in V6],
        "W2_first_E8":[str(x) for x in W2],
        "W3_first_E8":[str(x) for x in W3],
        "second_E8":"untouched/zero in this witness",
        "note":"gauge-embedding witness, not a full-spectrum MSSM vacuum"
      },
      {
        "id":"BHLR_published_representatives",
        "orbifold":"Z6-II benchmark",
        "source":"analysis/z6ii_buchmuller2007_benchmark_regression.py",
        "V":[str(x) for x in pub["V"]],
        "W2":[str(x) for x in pub["W2"]],
        "W3":[str(x) for x in pub["W3"]],
        "note":"published representatives; exact root/coset checks are representative-invariant, but these representatives fail some modular-invariance tests verbatim"
      },
      {
        "id":"BHLR_orbifolder_shipped_representatives",
        "orbifold":"Z6-II benchmark",
        "source":"analysis/the_w33_standard_models_have_a_renormalisable_top_yukawa.py",
        "V":[str(x) for x in shipped["V"]],
        "W2":[str(x) for x in shipped["W2"]],
        "W3":[str(x) for x in shipped["W3"]],
        "note":"lattice-equivalent corrected representatives shipped with the orbifolder benchmark"
      }
    ]

    out={
      "schema":"holotrade.heterotic_model_source_provenance_audit.v1",
      "status":"PASS_RECOVERABLE_VECTOR_LEDGER_FROZEN_BULK_SP_CORPUS_CONFIRMED_ABSENT_FROM_INSPECTED_GIT_TREES",
      "headline":"Holotrade preserves several complete model-defining vector sets, but the historical 215-model flatness pipeline depended on local/uncommitted sp1/, sp2/, and unbroken2.py inputs. The hidden raw-z6-ii-model-corpus branch and both inspected D-flat-era trees contain none of those paths. This certificate freezes every explicitly recovered model/vector witness used by the present exact frontier without fabricating the missing spectrum corpus.",
      "historical_tree_audit":history,
      "recoverable_vector_sets":recovered,
      "recoverable_set_count":len(recovered),
      "missing_bulk_inputs":{
        "paths":["sp1/","sp2/","unbroken2.py"],
        "verdict":"absent from all three inspected historical trees, including copilot/raw-z6-ii-model-corpus",
        "consequence":"class-wide 215-model D/F-flatness cannot be exactly replayed from Git alone; regenerate models from defining vectors where available or recover the external raw corpus"
      },
      "provenance_boundary":{
        "safe_to_replay":["Z6-I flagship gauge model","Z6-II explicit model witness","Z6-II gauge-embedding witness","BHLR benchmark representatives"],
        "not_safe_to_claim_from_git_alone":["complete 215-model raw spectrum corpus","class-wide exact matter-even D/F-flat vacuum census"]
      },
      "checks":{
        "flagship_vectors_recovered":True,
        "z6ii_model_vectors_recovered":True,
        "z6ii_shape_vectors_recovered":True,
        "bhlr_published_and_shipped_representatives_recovered":True,
        "bhlr_representatives_lattice_equivalent":True,
        "hidden_branch_checked":True,
        "two_dflat_history_trees_checked":True,
        "missing_sp1_sp2_unbroken2_confirmed_for_inspected_trees":True
      }
    }
    if write: OUT.write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps(out,indent=2))
    return out

if __name__=="__main__": main(True)
