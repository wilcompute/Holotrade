"use strict";
const STATUS="PASS_FIVE_CONTINUATION_WITH_THREE_THEOREMS_ONE_FIREWALL_ONE_CANDIDATE_UPGRADE";
function req(x,msg){if(!x)throw new Error(msg);}
function byN(xs,n){const x=xs.find(v=>v.n===n);req(x,"missing n="+n);return x;}
function byQ(xs,q){const x=xs.find(v=>v.q===q);req(x,"missing q="+q);return x;}

function verifyContinuationBundle(b){
  const {aggregate,depth3,flow,homotopy,winding,aux}=b||{};
  req(aggregate?.schema==="w33.ledger.continuation-2026-09-21.v1"&&aggregate?.status===STATUS,"aggregate mismatch");

  req(depth3?.status==="THEOREM_DEPTH3_EXISTS_FOR_ALL_N_GE_3_Q_GE_3","n-party depth3 theorem missing");
  for(const n of [3,4,5,10]){
    const c=byN(depth3.phase_rank_certificates,n);
    req(c.rank===c.phase_dimension,"n="+n+" phase span not full");
  }
  req(depth3.checks.zero_partial_trace_witnesses===true&&depth3.checks.nondegenerate_regional_spectra===true,"regional compatibility witness failed");

  req(flow?.status==="NO_GO_NONTRIVIAL_CONTINUOUS_MODULAR_FLOW_INSIDE_W33_AUTOMORPHISMS","modular-flow firewall missing");
  req(flow.numerical_nontracial_witness.every(x=>x.min_projective_pauli_distance>1e-3),"nontracial modular flow did not leave Pauli rays");

  req(homotopy?.status==="THEOREM_W3Q_CLIQUE_SIMPLE_HOMOTOPY_WEDGE_Q4_CIRCLES","simple-homotopy certificate missing");
  const h3=byQ(homotopy.examples,3),h5=byQ(homotopy.examples,5);
  req(h3.free_rank===81&&h3.total_elementary_collapses===160,"q3 collapse control mismatch");
  req(h5.free_rank===625,"q5 q^4 free rank mismatch");
  req(typeof homotopy.prior_art_boundary==="string"&&homotopy.prior_art_boundary.length>20,"prior-art boundary missing");

  req(winding?.status==="TOPOLOGY_SUPPLIES_Q4_WINDING_GENERATORS_NOT_A_UNIQUE_MATTER_SPECTRUM","winding firewall missing");
  const w3=byQ(winding.examples,3);
  req(w3.free_rank===81&&w3.flat_U1_moduli_dimension===81,"W33 winding rank mismatch");
  req(w3.Zq_flat_sector_count==="443426488243037769948249630619149892803","3^81 sector count mismatch");

  req(aux?.status==="AUXILIARY_CONTACT_REMOVES_HEAVY_POLE_THRESHOLD_UV_COMPLETION_STILL_OPEN","auxiliary firewall missing");
  req(aux.classification.includes("UV completion remains OPEN"),"auxiliary UV firewall missing");
  req(aux.examples.every(x=>x.C5_GeV_inv>0),"auxiliary contact missing");

  return Object.freeze({
    schema:"holotrade.w33-ledger-continuation-verdict.v1",
    valid:true,
    admitted:Object.freeze([
      "all-n existence of depth-three audit-complete families",
      "finite-W33 modular-flow no-go",
      "constructive all-q bouquet/simple-homotopy proof with prior ownership preserved",
      "exact 81-generator winding carrier"
    ]),
    candidates:Object.freeze(["auxiliary Weinberg contact: EFT-radiative-safe through cited order, UV open"]),
    blocked:Object.freeze([
      "universal depth-three claim for every state",
      "modular time inside finite W33 automorphisms",
      "winding alone selects matter",
      "auxiliary contact proves UV Higgs naturalness"
    ])
  });
}

function enforceClaimPolicy(requested={}){
  const forbidden=["allStatesDepth3","modularTimeInsideW33","windingUniquelySelectsMatter","auxiliaryUVSolved","bouquetClaimNew"];
  const hit=forbidden.filter(k=>requested[k]===true);
  if(hit.length)throw new Error("Ledger continuation claim firewall rejected: "+hit.join(","));
  return true;
}
module.exports=Object.freeze({STATUS,verifyContinuationBundle,enforceClaimPolicy});
