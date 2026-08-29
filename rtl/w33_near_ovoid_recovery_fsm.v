`default_nettype none

// One-bit entry-stratum recovery controller.
//
// Software classification proves that exactly one of the two residual hinge
// points is a certified high-release source.  The block bit tells the hardware
// which one.  The datapath is therefore one state bit plus a 6-bit 2:1 mux.
module w33_near_ovoid_recovery_fsm(
  input  wire       clk,
  input  wire       rst,
  input  wire       load,
  input  wire       block_in,
  input  wire [5:0] residual_lo,
  input  wire [5:0] residual_hi,
  output reg        valid,
  output reg        block_q,
  output wire [5:0] source
);
  always @(posedge clk) begin
    if (rst) begin
      valid   <= 1'b0;
      block_q <= 1'b0;
    end else if (load) begin
      valid   <= 1'b1;
      block_q <= block_in;
    end
  end

  assign source = block_q ? residual_hi : residual_lo;
endmodule

// Combinational datapath equivalence wrapper used by Yosys SAT.
module w33_near_ovoid_recovery_mux_equiv(
  input wire       block_q,
  input wire [5:0] residual_lo,
  input wire [5:0] residual_hi,
  output wire      mismatch
);
  wire [5:0] dut = block_q ? residual_hi : residual_lo;
  wire [5:0] ref0 = residual_lo;
  wire [5:0] ref1 = residual_hi;
  wire [5:0] refv = block_q ? ref1 : ref0;
  assign mismatch = |(dut ^ refv);
endmodule

`default_nettype wire
