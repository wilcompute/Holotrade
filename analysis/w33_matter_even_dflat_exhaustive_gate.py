#!/usr/bin/env python3
"""Exhaustive matter-even D-flat cone: source-data/proof gate.

This file executes the fifth target as far as the committed repository permits.

The existing matter-parity/D-flat analyses depend on raw model dumps
    sp1/*.sp, sp2/*.sp
and the parser/linear-algebra owner
    unbroken2.py.
Those objects are not present in the current Git tree.  Therefore the committed
summary counts cannot be promoted into an exhaustive theorem without silently
reconstructing data that GitHub does not contain.

When the exact inputs are later committed, this gate is intentionally shaped
so the next producer can consume a normalized rational ledger rather than
repeat the old sampled B-L search.

Required per-model normalized ledger:
  * exact rational U(1) charge matrix for every left-chiral field;
  * field identifier/base class and nonabelian dimensions/adjoint flags;
  * verified anomalous-U(1) index and FI sign/control;
  * exact hypercharge vector or enough labeled SM rows to solve it;
  * exact B-L constraint rows for q,u^c,d^c,e^c;
  * the complete candidate singlet set.

The exhaustive algorithm is then finite/algebraic:
  1. solve the affine B-L space x=x0+Nt over Q;
  2. derive all parity walls 3(x.Q_s) in 2Z for each singlet;
  3. enumerate the induced finite mod-2 affine parity classes (with exact
     integrality checks; fractional 3(B-L) is a third, inadmissible state);
  4. for each class solve the exact D-flat cone on its even singlets;
  5. store a primal ray if feasible, otherwise an exact Farkas dual witness.

Until those model matrices are committed, status must remain BLOCKED rather
than converting a 60-sample search into a proof.
"""
from __future__ import annotations
import argparse, glob, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/w33_matter_even_dflat_exhaustive_gate.json"

REQUIRED_SUMMARIES=[
    ROOT/"data/w33_matter_parity_z2_correction.json",
    ROOT/"data/w33_dflat_needs_a_matter_odd_singlet.json",
]
RAW_GLOBS=("sp1/*.sp","sp2/*.sp")
PARSER=ROOT/"unbroken2.py"

def build():
    assert all(p.exists() for p in REQUIRED_SUMMARIES)
    mp=json.loads(REQUIRED_SUMMARIES[0].read_text())
    df=json.loads(REQUIRED_SUMMARIES[1].read_text())

    raw={pat:sorted(str(Path(p).relative_to(ROOT)) for p in glob.glob(str(ROOT/pat)))
         for pat in RAW_GLOBS}
    nraw=sum(len(v) for v in raw.values())
    parser=PARSER.exists()

    # Lock the present evidentiary frontier to the published summaries.
    assert mp["bl"]["with_BL"]==88
    assert mp["bl"]["nullspace_dims"]=={"2":18,"3":30,"4":34,"5":3,"6":3}
    assert df["freedom"]["models"]==88
    assert df["freedom"]["samples_per_model"]==60
    assert df["freedom"]["dflat_even"]==0
    assert df["limits"]["is_a_proof"] is False
    assert df["limits"]["freedom_sampled_not_exhausted"] is True

    executable=(nraw>0 and parser)
    # Current repository state is intentionally frozen by the regression test.
    status=("READY_FOR_EXHAUSTIVE_PARITY_CONE_ENUMERATION" if executable else
            "BLOCKED_EXHAUSTIVE_CLASS_PROOF_SOURCE_DATA_NOT_COMMITTED")

    required_schema={
      "model_id":"string",
      "u1_count":"positive integer",
      "anomalous_u1_index":"integer",
      "fi_sign":"-1 or +1 with trace-control provenance",
      "fields":[{
        "id":"string",
        "left_chiral":"true",
        "base_class":"q|bu|bd|be|l|bl|n|...",
        "u1_charges":"list of exact rationals, length u1_count",
        "nonabelian_dimensions":"integer list",
        "adjoint_flags":"boolean list"
      }],
      "hypercharge":{
        "vector":"exact rational list, or null if solved from labeled rows",
        "constraint_source":"field ids / standard labels"
      },
      "B_minus_L_constraints":{
        "q":"1/3","bu":"-1/3","bd":"-1/3","be":"1"
      }
    }

    algorithm=[
      "Solve A_BL x=b_BL exactly over Q; obtain x0 and a rational nullspace basis N.",
      "For every candidate singlet s, form 3(x0+N t).Q_s exactly.",
      "Partition parameter space by the finite parity/integrality data of those affine forms; do not treat fractional 3(B-L) as even or odd.",
      "For every realizable parity class, restrict to singlets with integral even 3(B-L) and solve the exact D-term cone including the verified anomalous FI sign.",
      "For every infeasible cone store y with A^T y >= 0 and b^T y < 0 (Farkas); for every feasible cone store an exact nonnegative primal ray.",
      "A class-wide no-go is certified only when every realizable parity class of every B-L model has an exact infeasibility witness."
    ]

    return {
      "schema":"holotrade.w33_matter_even_dflat_exhaustive_gate.v1",
      "status":status,
      "headline":(
        "The requested exhaustive matter-even D-flat proof cannot be regenerated from the current Git snapshot: "
        "the analyses that produced the 88-model summaries require sp1/*.sp, sp2/*.sp and unbroken2.py, and none "
        "is committed. The present evidence remains 0 successes in 60 sampled B-L choices per model plus exact "
        "fixed-support tests, explicitly not a proof. This gate freezes the missing-data condition and the exact "
        "rational/SNF-Farkas interface required for a future exhaustive enumeration."
      ),
      "current_git_inputs":{
        "raw_globs":raw,
        "raw_model_files":nraw,
        "parser_path":"unbroken2.py",
        "parser_present":parser,
        "classwide_exact_enumeration_executable":executable,
        "flagship_raw_weight_dump_present":(ROOT/"analysis/flagship_fi_weights.txt").exists(),
        "flagship_note":"The committed flagship FI weight dump is useful for one-model Cartan/FI audits but is not the missing 88-model B-L charge ledger."
      },
      "current_evidence":{
        "models_with_BL":mp["bl"]["with_BL"],
        "B_minus_L_nullspace_dims":mp["bl"]["nullspace_dims"],
        "sampled_choices_per_model":df["freedom"]["samples_per_model"],
        "sampled_even_singlet_Dflat_hits":df["freedom"]["dflat_even"],
        "fixed_Dflat_support_models":df["support"]["models"],
        "fixed_support_exact_shift_successes":df["support"]["exact_shift_succeeds"],
        "published_scope":df["scope"],
        "is_exhaustive_proof":False
      },
      "required_normalized_ledger_schema":required_schema,
      "exhaustive_algorithm":algorithm,
      "proof_acceptance_rule":"No-go may be promoted only after every realizable parity class in every one of the 88 B-L models has an exact Farkas certificate; any exact primal witness refutes the no-go.",
      "boundary":"This gate is itself exact about repository provenance. It neither weakens the current controlled evidence nor upgrades it into a theorem.",
      "checks":{
        "summaries_present":True,
        "summary_says_not_proof":True,
        "sample_count_locked_60":True,
        "raw_model_dumps_missing":nraw==0,
        "parser_missing":not parser,
        "proof_refused_without_sources":not executable
      }
    }

def main(write=True):
    out=build()
    if write: OUT.write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps({
      "status":out["status"],
      "raw_model_files":out["current_git_inputs"]["raw_model_files"],
      "parser_present":out["current_git_inputs"]["parser_present"],
      "is_exhaustive_proof":out["current_evidence"]["is_exhaustive_proof"]
    },indent=2))
    return out

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--check",action="store_true")
    args=ap.parse_args()
    main(not args.check)
