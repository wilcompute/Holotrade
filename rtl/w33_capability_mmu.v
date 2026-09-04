`default_nettype none

// W33 capability-address MMU gate.
//
// The Merkle proof itself is verified outside this small gate; root_match is the
// authenticated result presented to the MMU.  A dereference is admitted only if
// every authority component agrees: tag, snapshot root, bounds, rights, epoch,
// carrier and evidence floor.  The explicit tag bit models a hardware capability
// tag; this module does not claim a particular SRAM/BRAM tag-storage technology.
module w33_capability_mmu(
    input  wire        cap_valid,
    input  wire        cap_tag,
    input  wire        sealed,
    input  wire        root_match,
    input  wire [31:0] base_addr,
    input  wire [31:0] end_addr_exclusive,
    input  wire [31:0] cursor,
    input  wire [2:0]  rights,          // bit0=read bit1=write bit2=execute
    input  wire [1:0]  requested_op,    // 0=read 1=write 2=execute, 3=invalid
    input  wire [15:0] cap_epoch,
    input  wire [15:0] current_epoch,
    input  wire [1:0]  cap_carrier,
    input  wire [1:0]  current_carrier,
    input  wire [1:0]  evidence_floor,
    input  wire [1:0]  current_evidence,
    output wire        allow,
    output wire [8:0]  fault
);
    wire bounds_ok = (base_addr <= cursor) && (cursor < end_addr_exclusive);
    wire epoch_ok = (cap_epoch == current_epoch);
    wire carrier_ok = (cap_carrier == current_carrier);
    wire evidence_ok = (current_evidence >= evidence_floor);
    wire op_valid = (requested_op != 2'b11);
    wire right_ok = (requested_op == 2'b00) ? rights[0] :
                    (requested_op == 2'b01) ? rights[1] :
                    (requested_op == 2'b10) ? rights[2] : 1'b0;

    assign fault[0] = !cap_valid;
    assign fault[1] = !cap_tag;
    assign fault[2] = sealed;
    assign fault[3] = !root_match;
    assign fault[4] = !bounds_ok;
    assign fault[5] = !(op_valid && right_ok);
    assign fault[6] = !epoch_ok;
    assign fault[7] = !carrier_ok;
    assign fault[8] = !evidence_ok;
    assign allow = ~(|fault);
endmodule

// Monotone capability derivation gate.  Child authority may narrow bounds and
// rights and may raise (never lower) the evidence floor.  The tag propagates
// only from an already tagged parent and only across an accepted derivation.
module w33_capability_derive(
    input  wire        parent_tag,
    input  wire [31:0] parent_base,
    input  wire [31:0] parent_end,
    input  wire [2:0]  parent_rights,
    input  wire [1:0]  parent_evidence_floor,
    input  wire [31:0] child_base,
    input  wire [31:0] child_end,
    input  wire [2:0]  child_rights,
    input  wire [1:0]  child_evidence_floor,
    output wire        derivation_ok,
    output wire        child_tag
);
    wire ordered = (child_base <= child_end);
    wire bounds_narrow = (parent_base <= child_base) && (child_end <= parent_end);
    wire rights_narrow = ((child_rights & ~parent_rights) == 3'b000);
    wire evidence_monotone = (child_evidence_floor >= parent_evidence_floor);
    assign derivation_ok = parent_tag && ordered && bounds_narrow && rights_narrow && evidence_monotone;
    assign child_tag = parent_tag && derivation_ok;
endmodule

// Independent reference equations used only by the formal top.  A mismatch is
// a combinational counterexample target for Yosys SAT.
module w33_capability_mmu_formal(
    input wire cap_valid,input wire cap_tag,input wire sealed,input wire root_match,
    input wire [31:0] base_addr,input wire [31:0] end_addr_exclusive,input wire [31:0] cursor,
    input wire [2:0] rights,input wire [1:0] requested_op,
    input wire [15:0] cap_epoch,input wire [15:0] current_epoch,
    input wire [1:0] cap_carrier,input wire [1:0] current_carrier,
    input wire [1:0] evidence_floor,input wire [1:0] current_evidence,
    input wire [31:0] child_base,input wire [31:0] child_end,input wire [2:0] child_rights,
    input wire [1:0] child_evidence_floor,
    output wire mismatch
);
    wire allow; wire [8:0] fault;
    w33_capability_mmu dut(
      cap_valid,cap_tag,sealed,root_match,base_addr,end_addr_exclusive,cursor,rights,requested_op,
      cap_epoch,current_epoch,cap_carrier,current_carrier,evidence_floor,current_evidence,allow,fault);

    wire requested_right = (requested_op==0) ? rights[0] :
                           (requested_op==1) ? rights[1] :
                           (requested_op==2) ? rights[2] : 1'b0;
    wire expected_allow = cap_valid && cap_tag && !sealed && root_match &&
                          (base_addr <= cursor) && (cursor < end_addr_exclusive) &&
                          (requested_op != 3) && requested_right &&
                          (cap_epoch == current_epoch) &&
                          (cap_carrier == current_carrier) &&
                          (current_evidence >= evidence_floor);

    wire derive_ok; wire derived_tag;
    w33_capability_derive drv(
      cap_tag,base_addr,end_addr_exclusive,rights,evidence_floor,
      child_base,child_end,child_rights,child_evidence_floor,derive_ok,derived_tag);
    wire expected_derive = cap_tag && (child_base <= child_end) &&
                           (base_addr <= child_base) && (child_end <= end_addr_exclusive) &&
                           ((child_rights & ~rights) == 0) &&
                           (child_evidence_floor >= evidence_floor);
    wire forged_tag = derived_tag && !cap_tag;
    assign mismatch = (allow ^ expected_allow) || (derive_ok ^ expected_derive) || forged_tag;
endmodule

`default_nettype wire
