"use strict";

const SCHEMA="w33.ledger.stress-suite.v1";
const STATUS="PASS_WITH_TWO_LEDGER_CORRECTIONS";

function req(x,msg){if(!x) throw new Error(msg);}
function verifyLedgerStressBundle(b){
  req(b&&typeof b==="object","bundle required");
  const {suite,modular,mirror,audit,monopole,dark}=b;
  req(suite?.schema===SCHEMA&&suite?.status===STATUS,"W33 Ledger suite mismatch");
  req(modular?.status==="PASS_LITERAL_CHARACTER_WITH_THREE_QUTRITS","modular-character certificate mismatch");
  req(modular.audit.max_abs_im_chi.overlap>1e-4,"overlap phase missing");
  req(modular.audit.max_abs_im_chi.disjoint<1e-10,"disjoint phase unexpectedly nonzero");
  req(modular.audit.max_order_reversal_conjugation_error<1e-10,"order-reversal conjugation failed");
  req(mirror?.status==="PASS_GEOMETRIC_MIRROR_DOUBLE_COVER","mirror certificate mismatch");
  req(mirror.mirror_generated_group.order===51840,"mirror extension order mismatch");
  req(mirror.even_mirror_products.order===25920&&mirror.even_mirror_products.equals_psp_permutation_group===true,"even mirror core mismatch");
  req(mirror.mirror_conjugacy_class.size===540,"mirror class mismatch");
  req(audit?.status==="CORRECTION_DEPTH2_FAILS_Q3_DEPTH3_CLOSES","audit correction missing");
  req(audit.controls.n3_q2.rank_depth2===64,"three-qubit control failed");
  req(audit.qutrit_trials.length===5,"qutrit witness count mismatch");
  req(audit.qutrit_trials.every(x=>x.rank_depth2===649&&x.rank_depth3===729&&x.max_commutator_rank===27),"qutrit correction witness mismatch");
  req(monopole?.status==="PASS_W33_H2_ZERO_GLOBAL_EXACTNESS","monopole certificate mismatch");
  req(monopole.cohomology.F3.H2_dim===0&&monopole.betti_numbers["3"][2]===0,"W33 H2 must vanish");
  req(dark?.status==="NO_GO_H4_PRODUCT_HAMILTONIAN_AS_WRITTEN","dark-bond no-go missing");
  req(dark.numerical_certificate.max_entropy_drift<1e-12,"dark-bond entropy drift invariant failed");
  req(dark.numerical_certificate.gibbs_factorization_error<1e-12,"dark-bond Gibbs factorization failed");
  req(Math.abs(dark.minimal_escape_witness.biased_R_effective_action_coefficients.Z)>0.1,"interaction escape witness missing");
  return Object.freeze({
    schema:"holotrade.w33-ledger-stress-verdict.v1",
    validFiniteProgram:true,
    claimAdmission:false,
    admitted:Object.freeze([
      "literal finite modular-character overlap phase",
      "geometric mirror double-cover pattern",
      "W33-specific H2=0 closed-to-exact statement"
    ]),
    blocked:Object.freeze([
      "Tomita=geometric-mirror identification",
      "universal no-monopole theorem from dF=0 alone",
      "qutrit depth-two audit completeness",
      "H.4 dynamic dark bond under a product Hamiltonian"
    ]),
    repair:Object.freeze({qutritAudit:"depth three closes 729/729 in five exact witnesses",darkBond:"requires interaction or a new nonfactorizing algebraic mechanism"})
  });
}

function enforceClaimPolicy(requested={}){
  const forbidden=["ledgerUniversalLaw","tomitaEqualsGeometricMirror","universalNoMonopoles","qutritDepth2Completeness","darkBondH4AsWritten"];
  const hit=forbidden.filter(k=>requested[k]===true);
  if(hit.length) throw new Error("Ledger claim firewall rejected: "+hit.join(","));
  return true;
}

module.exports=Object.freeze({SCHEMA,STATUS,verifyLedgerStressBundle,enforceClaimPolicy});
