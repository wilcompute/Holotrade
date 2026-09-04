`default_nettype none

// Four-register architectural shell around w33_capability_mmu.
//
// Opcodes mirror the software ISA:
//   0 CINC, 1 CSETBOUNDS, 2 CANDPERM, 3 CREQUIRE,
//   4 CSEAL, 5 CLOAD, 6 CSTORE, 7 invalid.
//
// A privileged loader is the only way to mint a fresh tag. User-visible
// derivations can only copy/narrow a tagged source capability. Persistent
// CSTORE does not silently retarget the capability: the content-addressed
// backend must return a new authenticated root through commit_root_valid.
module w33_capability_machine(
    input  wire         clk,
    input  wire         rst,

    input  wire         priv_load,
    input  wire [1:0]   priv_rd,
    input  wire         priv_tag,
    input  wire [127:0] priv_root,
    input  wire [31:0]  priv_base,
    input  wire [31:0]  priv_end,
    input  wire [31:0]  priv_cursor,
    input  wire [2:0]   priv_rights,
    input  wire [15:0]  priv_epoch,
    input  wire [1:0]   priv_carrier,
    input  wire [1:0]   priv_evidence_floor,
    input  wire         priv_sealed,

    input  wire         commit_root_valid,
    input  wire [1:0]   commit_reg,
    input  wire [127:0] commit_root,

    input  wire         op_valid,
    input  wire [2:0]   opcode,
    input  wire [1:0]   rd,
    input  wire [1:0]   rs,
    input  wire [31:0]  imm,
    input  wire         imm_sub,
    input  wire [31:0]  bound_base_imm,
    input  wire [31:0]  bound_end_imm,
    input  wire [2:0]   rights_imm,
    input  wire [1:0]   evidence_imm,

    input  wire [127:0] current_root,
    input  wire [15:0]  current_epoch,
    input  wire [1:0]   current_carrier,
    input  wire [1:0]   current_evidence,

    input  wire [31:0]  store_data,
    input  wire [31:0]  memory_read_data,
    input  wire         memory_ready,

    output wire         memory_request,
    output wire         memory_write,
    output wire [31:0]  memory_address,
    output wire [31:0]  memory_write_data,
    output wire         load_result_valid,
    output wire [31:0]  load_result,
    output wire         op_fault,
    output wire [8:0]   mmu_fault,

    // Debug/readback port for synthesis and integration tests.
    input  wire [1:0]   inspect_reg,
    output wire         inspect_tag,
    output wire [127:0] inspect_root,
    output wire [31:0]  inspect_base,
    output wire [31:0]  inspect_end,
    output wire [31:0]  inspect_cursor,
    output wire [2:0]   inspect_rights,
    output wire [15:0]  inspect_epoch,
    output wire [1:0]   inspect_carrier,
    output wire [1:0]   inspect_evidence_floor,
    output wire         inspect_sealed
);
    reg tag [0:3];
    reg [127:0] root [0:3];
    reg [31:0] base_addr [0:3];
    reg [31:0] end_addr [0:3];
    reg [31:0] cursor [0:3];
    reg [2:0] rights [0:3];
    reg [15:0] epoch [0:3];
    reg [1:0] carrier [0:3];
    reg [1:0] evidence_floor [0:3];
    reg sealed [0:3];

    integer i;
    wire root_match = (root[rs] == current_root);
    wire [1:0] requested_op = (opcode == 3'd5) ? 2'd0 :
                              (opcode == 3'd6) ? 2'd1 : 2'd3;
    wire mmu_allow;
    w33_capability_mmu mmu(
      .cap_valid(op_valid && ((opcode == 3'd5) || (opcode == 3'd6))),
      .cap_tag(tag[rs]), .sealed(sealed[rs]), .root_match(root_match),
      .base_addr(base_addr[rs]), .end_addr_exclusive(end_addr[rs]), .cursor(cursor[rs]),
      .rights(rights[rs]), .requested_op(requested_op),
      .cap_epoch(epoch[rs]), .current_epoch(current_epoch),
      .cap_carrier(carrier[rs]), .current_carrier(current_carrier),
      .evidence_floor(evidence_floor[rs]), .current_evidence(current_evidence),
      .allow(mmu_allow), .fault(mmu_fault));

    wire [31:0] add_cursor = cursor[rs] + imm;
    wire [31:0] sub_cursor = cursor[rs] - imm;
    wire add_no_wrap = (add_cursor >= cursor[rs]);
    wire sub_no_wrap = (imm <= cursor[rs]);
    wire [31:0] next_cursor = imm_sub ? sub_cursor : add_cursor;
    wire cursor_arith_ok = imm_sub ? sub_no_wrap : add_no_wrap;
    wire cursor_bounds_ok = cursor_arith_ok && (base_addr[rs] <= next_cursor) && (next_cursor < end_addr[rs]);

    wire bounds_narrow_ok = tag[rs] && (base_addr[rs] <= bound_base_imm) &&
                            (bound_base_imm <= bound_end_imm) &&
                            (bound_end_imm <= end_addr[rs]) &&
                            (bound_base_imm <= cursor[rs]) && (cursor[rs] < bound_end_imm);
    wire rights_narrow_ok = tag[rs] && ((rights_imm & ~rights[rs]) == 3'b000);
    wire evidence_raise_ok = tag[rs] && (evidence_imm >= evidence_floor[rs]);
    wire source_derivable = tag[rs] && !sealed[rs];

    wire derivation_fault = op_valid && (
      ((opcode == 3'd0) && !(source_derivable && cursor_bounds_ok)) ||
      ((opcode == 3'd1) && !(source_derivable && bounds_narrow_ok)) ||
      ((opcode == 3'd2) && !(source_derivable && rights_narrow_ok)) ||
      ((opcode == 3'd3) && !(source_derivable && evidence_raise_ok)) ||
      ((opcode == 3'd4) && !source_derivable) ||
      (opcode == 3'd7));

    assign memory_request = op_valid && ((opcode == 3'd5) || (opcode == 3'd6)) && mmu_allow;
    assign memory_write = memory_request && (opcode == 3'd6);
    assign memory_address = cursor[rs];
    assign memory_write_data = store_data;
    assign load_result_valid = memory_request && !memory_write && memory_ready;
    assign load_result = memory_read_data;
    assign op_fault = derivation_fault ||
                      (op_valid && ((opcode == 3'd5) || (opcode == 3'd6)) && !mmu_allow);

    always @(posedge clk) begin
      if (rst) begin
        for (i = 0; i < 4; i = i + 1) begin
          tag[i] <= 1'b0;
          root[i] <= 128'b0;
          base_addr[i] <= 32'b0;
          end_addr[i] <= 32'b0;
          cursor[i] <= 32'b0;
          rights[i] <= 3'b0;
          epoch[i] <= 16'b0;
          carrier[i] <= 2'b0;
          evidence_floor[i] <= 2'b0;
          sealed[i] <= 1'b0;
        end
      end else begin
        // Authenticated backend root-rebind is not a mint operation: it may
        // update only an already tagged, unsealed register.
        if (commit_root_valid && tag[commit_reg] && !sealed[commit_reg])
          root[commit_reg] <= commit_root;

        // Privileged loader/mint path. Integration is responsible for binding
        // this port to the trusted capability authority, never guest logic.
        if (priv_load) begin
          tag[priv_rd] <= priv_tag;
          root[priv_rd] <= priv_root;
          base_addr[priv_rd] <= priv_base;
          end_addr[priv_rd] <= priv_end;
          cursor[priv_rd] <= priv_cursor;
          rights[priv_rd] <= priv_rights;
          epoch[priv_rd] <= priv_epoch;
          carrier[priv_rd] <= priv_carrier;
          evidence_floor[priv_rd] <= priv_evidence_floor;
          sealed[priv_rd] <= priv_sealed;
        end else if (op_valid && !derivation_fault) begin
          if (opcode <= 3'd4) begin
            // Every derivation copies the tagged source first, then narrows one
            // component. No guest operation contains a literal tag=1 assignment.
            tag[rd] <= tag[rs];
            root[rd] <= root[rs];
            base_addr[rd] <= base_addr[rs];
            end_addr[rd] <= end_addr[rs];
            cursor[rd] <= cursor[rs];
            rights[rd] <= rights[rs];
            epoch[rd] <= epoch[rs];
            carrier[rd] <= carrier[rs];
            evidence_floor[rd] <= evidence_floor[rs];
            sealed[rd] <= sealed[rs];
            case (opcode)
              3'd0: cursor[rd] <= next_cursor;
              3'd1: begin base_addr[rd] <= bound_base_imm; end_addr[rd] <= bound_end_imm; end
              3'd2: rights[rd] <= rights_imm;
              3'd3: evidence_floor[rd] <= evidence_imm;
              3'd4: sealed[rd] <= 1'b1;
              default: ;
            endcase
          end
        end
      end
    end

    assign inspect_tag = tag[inspect_reg];
    assign inspect_root = root[inspect_reg];
    assign inspect_base = base_addr[inspect_reg];
    assign inspect_end = end_addr[inspect_reg];
    assign inspect_cursor = cursor[inspect_reg];
    assign inspect_rights = rights[inspect_reg];
    assign inspect_epoch = epoch[inspect_reg];
    assign inspect_carrier = carrier[inspect_reg];
    assign inspect_evidence_floor = evidence_floor[inspect_reg];
    assign inspect_sealed = sealed[inspect_reg];
endmodule

`default_nettype wire
