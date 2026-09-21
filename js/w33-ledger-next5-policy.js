"use strict";

const STATUS="PASS_FIVE_EXECUTED_WITH_TWO_THEOREMS_TWO_CORRECTIONS_ONE_OPEN_CANDIDATE";
function req(x,msg){if(!x)throw new Error(msg);}
function byQ(xs,q){const x=xs.find(v=>v.q===q);req(x,"missing q="+q);return x;}

function verifyNext5Bundle(b){
  const {aggregate,audit,tomita,h2,dark,def80}=b||{};
  req(aggregate?.schema==="w33.ledger.next-five-2026-09-21.v1"&&aggregate?.status===STATUS,"aggregate mismatch");

  req(audit?.status==="DEPTH_Q_CONJECTURE_KILLED_DEPTH3_OPEN_FAMILY","audit theorem missing");
  for(const q of [3,4,5]){
    const c=byQ(audit.certificates,q);
    req(c.depth3_labels===c.operator_dimension,"q="+q+" depth3 not full");
    req(c.min_rho_eigenvalue>0,"q="+q+" state not faithful");
  }
  req(byQ(audit.bounds,4).depth2_impossible===true&&byQ(audit.bounds,5).depth2_impossible===true,"q4/q5 depth2 obstruction missing");

  req(tomita?.status==="PASS_TOMITA_TO_W33_MIRROR_AFTER_COMMUTANT_FOLD","Tomita bridge missing");
  req(tomita.w33?.psp_order===25920&&tomita.w33?.clifford_frame_orbit===540,"Tomita mirror orbit mismatch");
  req(tomita.fold?.matrix==="diag(1,1,-1,-1)","Tomita fold matrix mismatch");

  req(h2?.status==="THEOREM_ALL_W3Q_H2_ZERO","all-q H2 theorem missing");
  const q4=byQ(h2.examples,4),q5=byQ(h2.examples,5);
  req(q4.betti["1"]===256&&q5.betti["1"]===625,"all-q q^4 homology mismatch");
  req(Object.entries(q4.betti).filter(([k])=>Number(k)>=2).every(([,v])=>v===0),"q4 higher homology nonzero");

  req(dark?.status==="NO_INTERACTION_FREE_DYNAMIC_BOND_FOUND_AUXILIARY_ROUTE_TREE_LEVEL_ONLY","dark-bond route census mismatch");
  req(dark.modular_only.max_entropy_drift<1e-12&&dark.modular_only.max_schmidt_drift<1e-12,"modular no-go invariant failed");
  req(Math.abs(dark.nonfactorizing_constraint.logical_offdiag)>0.1,"constraint portal witness missing");
  req(dark.algebraic_auxiliary_candidate.C5_y2_over_M>0,"auxiliary contact witness missing");

  req(def80?.status==="DEFICIENCY80_IS_NOT_W33_BUILDING_MODULE","deficiency-80 verdict missing");
  req(def80.audit.A2_rank===649&&def80.audit.deficiency===80,"deficiency dimensions mismatch");
  req(def80.symmetry_test.basis_vectors_outside_A2===564,"Clifford leakage mismatch");
  req(def80.symmetry_test.rank_A2_plus_conjugate_A2===729,"Clifford hull must close full operator space");

  return Object.freeze({
    schema:"holotrade.w33-ledger-next5-verdict.v1",
    valid:true,
    admitted:Object.freeze([
      "q>=4 depth-two impossibility and explicit open depth-three family",
      "folded Tomita-to-W33 anti-symplectic mirror bridge",
      "all-q W(3,q) H2=0 / H1=q^4 theorem"
    ]),
    candidates:Object.freeze(["nondynamical auxiliary Weinberg contact: tree level only"]),
    blocked:Object.freeze([
      "word-depth=q",
      "540 state-dependent Tomita J operators",
      "80-deficiency=W33-building module",
      "interaction-free dynamic dark bond",
      "auxiliary contact implies proven Higgs naturalness"
    ])
  });
}

function enforceClaimPolicy(requested={}){
  const forbidden=["depthEqualsQ","tomitaStateDependent540","deficiency80BuildingModule","interactionFreeDarkBond","auxiliaryHiggsProtectionProven"];
  const hit=forbidden.filter(k=>requested[k]===true);
  if(hit.length)throw new Error("Ledger next5 claim firewall rejected: "+hit.join(","));
  return true;
}
module.exports=Object.freeze({STATUS,verifyNext5Bundle,enforceClaimPolicy});
