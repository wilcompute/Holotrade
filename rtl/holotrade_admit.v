// ======================================================================
// HOLOTRADE ADMISSION AND ROUTING PRIMITIVE
//
// The exchange's hot path, in hardware.
//
// Every quote needs a locality term; every locality term needs the
// fabric distance; every fabric distance is a symplectic inner product
// over F_3. Every fill then needs an admission decision. On a venue
// that reprices its whole fleet every second, these two operations run
// more often than anything else in the system, so they are the part
// worth putting on silicon.
//
// The claim made concrete here is narrower: ADDRESS DETERMINES DIRECT
// ADJACENCY. A complete physical router still needs link state,
// congestion handling and relay selection. The exact level-1 predicate is:
//
//     <u,v>  =  u0*v1 - u1*v0 + u2*v3 - u3*v2   (mod 3)
//     adjacent  <=>  <u,v> == 0
//
// which this module computes combinationally without a route-table RAM.
//
// ----------------------------------------------------------------------
// ENCODING
//
// A W(3,3) address is a canonical representative of a point of
// PG(3,F_3): four coordinates in {0,1,2}, two bits each, eight bits per
// address, nonzero, with first nonzero coordinate equal to 1. The form
// datapath is total and normalises 2'b11 to zero, but the admission gate
// rejects every illegal/noncanonical address with R_BAD_ADDR. Without
// that gate, 2'b11 would silently alias a legal zero coordinate.
//
// ----------------------------------------------------------------------
// SCOPE
//
// `npm run verify:rtl` proves every output equivalent to an independent
// behavioural model by SAT over all 2^25 complete-module inputs;
// `npm run synth:rtl` reports technology mapping. Cryptographic
// signature verification and generation of policy predicates are outside
// this module. Timing is not reported because it has not been placed or
// routed on a named part.
// ======================================================================

`default_nettype none

// ----------------------------------------------------------------------
// Mod-3 primitives.
//
// Two bits per trit, values 0..2. 2'b11 is illegal and is normalised to
// 0 on the way in, so every downstream operator sees a valid F_3
// element and the truth tables below are total.
// ----------------------------------------------------------------------

module f3_norm (input wire [1:0] a, output wire [1:0] y);
  // 3 -> 0; everything else passes through
  assign y = (a == 2'd3) ? 2'd0 : a;
endmodule

module f3_add (input wire [1:0] a, input wire [1:0] b, output wire [1:0] y);
  wire [2:0] s = {1'b0, a} + {1'b0, b};          // 0..4
  assign y = (s >= 3'd3) ? s[1:0] - 2'd3 + 2'd0 : s[1:0];
endmodule

module f3_neg (input wire [1:0] a, output wire [1:0] y);
  // -0 = 0, -1 = 2, -2 = 1
  assign y = (a == 2'd0) ? 2'd0 : (a == 2'd1 ? 2'd2 : 2'd1);
endmodule

module f3_mul (input wire [1:0] a, input wire [1:0] b, output wire [1:0] y);
  // full 3x3 table: anything times zero is zero, 1 is identity, 2*2 = 1
  assign y = (a == 2'd0 || b == 2'd0) ? 2'd0
           : (a == 2'd1)              ? b
           : (b == 2'd1)              ? a
           :                            2'd1;   // 2 * 2 = 4 = 1 mod 3
endmodule

// ----------------------------------------------------------------------
// The symplectic form, and the adjacency test that IS the routing
// decision.
// ----------------------------------------------------------------------

module w33_form (
  input  wire [7:0] u,        // {u3,u2,u1,u0}, two bits each
  input  wire [7:0] v,
  output wire [1:0] form,     // <u,v> mod 3
  output wire       adjacent  // the whole routing decision
);
  wire [1:0] u0, u1, u2, u3, v0, v1, v2, v3;
  f3_norm nu0 (.a(u[1:0]), .y(u0));
  f3_norm nu1 (.a(u[3:2]), .y(u1));
  f3_norm nu2 (.a(u[5:4]), .y(u2));
  f3_norm nu3 (.a(u[7:6]), .y(u3));
  f3_norm nv0 (.a(v[1:0]), .y(v0));
  f3_norm nv1 (.a(v[3:2]), .y(v1));
  f3_norm nv2 (.a(v[5:4]), .y(v2));
  f3_norm nv3 (.a(v[7:6]), .y(v3));

  // u0*v1 - u1*v0 + u2*v3 - u3*v2
  wire [1:0] p0, p1, p2, p3;
  f3_mul m0 (.a(u0), .b(v1), .y(p0));
  f3_mul m1 (.a(u1), .b(v0), .y(p1));
  f3_mul m2 (.a(u2), .b(v3), .y(p2));
  f3_mul m3 (.a(u3), .b(v2), .y(p3));

  wire [1:0] n1, n3;
  f3_neg g1 (.a(p1), .y(n1));
  f3_neg g3 (.a(p3), .y(n3));

  wire [1:0] s0, s1;
  f3_add a0 (.a(p0), .b(n1), .y(s0));
  f3_add a1 (.a(p2), .b(n3), .y(s1));
  f3_add a2 (.a(s0), .b(s1), .y(form));

  // Two nodes are adjacent iff the form vanishes. Note that a point is
  // isotropic for its own form (<x,x> = 0 always), so a node is
  // "adjacent" to itself here; the caller distinguishes identity from
  // collinearity by comparing addresses, which is the rank-3 relation:
  // identity, intersecting, disjoint, and nothing else.
  assign adjacent = (form == 2'd0);
endmodule

// ----------------------------------------------------------------------
// The admission gate.
//
// Eight outcomes (admit plus six policy refusals and BAD_ADDR), checked
// in priority order and reported as a
// code rather than a bare zero. The gate REFUSES rather than degrading:
// there is no best-effort output here, because a silent fallback is how
// a security posture becomes decorative.
//
// `magic_budget` is a declared prototype capability policy. This circuit
// enforces the declaration; it does not establish a universal 9^t cost
// law or verify the physical capability of a node.
// ----------------------------------------------------------------------

module holotrade_admit (
  input  wire [7:0] plan_addr,      // anchor address of the workload
  input  wire [7:0] node_addr,      // candidate node
  input  wire [3:0] magic_budget,   // t, non-Clifford gate count
  input  wire       node_magic,     // node can serve t > 0
  input  wire       sig_ok,         // upstream signature-policy predicate; not verified here
  input  wire       nonce_fresh,    // nonce not in the replay store
  input  wire       in_window,      // inside [validFrom, validUntil]
  input  wire       pins_ok,        // no artefact pin drift
  input  wire       node_in_service,

  output wire       admit,
  output wire [2:0] reason,         // 0 = admitted
  output wire [1:0] form,
  output wire       adjacent,
  output wire [3:0] ray_cost        // migration price law
);
  localparam [2:0] R_OK           = 3'd0;
  localparam [2:0] R_BAD_SIG      = 3'd1;
  localparam [2:0] R_REPLAY       = 3'd2;
  localparam [2:0] R_WINDOW       = 3'd3;
  localparam [2:0] R_PIN_DRIFT    = 3'd4;
  localparam [2:0] R_NO_MAGIC     = 3'd5;
  localparam [2:0] R_IN_SERVICE   = 3'd6;
  localparam [2:0] R_BAD_ADDR     = 3'd7;

  w33_form geom (
    .u(plan_addr), .v(node_addr), .form(form), .adjacent(adjacent)
  );

  wire same_point = (plan_addr == node_addr);
  wire needs_magic = (magic_budget != 4'd0);

  // Canonical projective encoding: legal trits, nonzero vector, and
  // first nonzero coordinate exactly 1. This rejects both illegal 2'b11
  // fields and the scalar-doubled representative 2*x of the same point.
  wire plan_trits_ok = (plan_addr[1:0] != 2'd3) && (plan_addr[3:2] != 2'd3) &&
                       (plan_addr[5:4] != 2'd3) && (plan_addr[7:6] != 2'd3);
  wire node_trits_ok = (node_addr[1:0] != 2'd3) && (node_addr[3:2] != 2'd3) &&
                       (node_addr[5:4] != 2'd3) && (node_addr[7:6] != 2'd3);
  wire plan_canonical = (plan_addr[1:0] == 2'd1) ||
                        ((plan_addr[1:0] == 2'd0) && (plan_addr[3:2] == 2'd1)) ||
                        ((plan_addr[3:0] == 4'd0) && (plan_addr[5:4] == 2'd1)) ||
                        ((plan_addr[5:0] == 6'd0) && (plan_addr[7:6] == 2'd1));
  wire node_canonical = (node_addr[1:0] == 2'd1) ||
                        ((node_addr[1:0] == 2'd0) && (node_addr[3:2] == 2'd1)) ||
                        ((node_addr[3:0] == 4'd0) && (node_addr[5:4] == 2'd1)) ||
                        ((node_addr[5:0] == 6'd0) && (node_addr[7:6] == 2'd1));
  wire addresses_ok = plan_trits_ok && node_trits_ok && plan_canonical && node_canonical;

  assign reason = (!sig_ok)                    ? R_BAD_SIG
                : (!addresses_ok)              ? R_BAD_ADDR
                : (!nonce_fresh)               ? R_REPLAY
                : (!in_window)                 ? R_WINDOW
                : (!pins_ok)                   ? R_PIN_DRIFT
                : (needs_magic && !node_magic) ? R_NO_MAGIC
                : (node_in_service)            ? R_IN_SERVICE
                :                                R_OK;

  assign admit = (reason == R_OK);

  // The migration price law, in three gates:
  //   same point      re-vector in place   6 rays
  //   collinear       cheapest migration   3 rays
  //   non-collinear   two hops             5 rays
  // Moving to a NEIGHBOUR is strictly cheaper than reconfiguring where
  // you already are, which is why the scheduler prefers migration.
  assign ray_cost = same_point ? 4'd6 : (adjacent ? 4'd3 : 4'd5);
endmodule

// ----------------------------------------------------------------------
// Independent behavioural reference for the form.
//
// Deliberately written a different way -- plain integer arithmetic with
// a single modulo at the end, rather than staged F_3 operators -- so
// that proving the two equivalent is evidence about the ENCODING and the
// algebra, not a restatement of the same expression twice.
// ----------------------------------------------------------------------

module w33_form_golden (
  input  wire [7:0] u,
  input  wire [7:0] v,
  output wire [1:0] form,
  output wire       adjacent
);
  function [1:0] nrm(input [1:0] a);
    nrm = (a == 2'd3) ? 2'd0 : a;
  endfunction

  wire [3:0] u0 = {2'b0, nrm(u[1:0])};
  wire [3:0] u1 = {2'b0, nrm(u[3:2])};
  wire [3:0] u2 = {2'b0, nrm(u[5:4])};
  wire [3:0] u3 = {2'b0, nrm(u[7:6])};
  wire [3:0] v0 = {2'b0, nrm(v[1:0])};
  wire [3:0] v1 = {2'b0, nrm(v[3:2])};
  wire [3:0] v2 = {2'b0, nrm(v[5:4])};
  wire [3:0] v3 = {2'b0, nrm(v[7:6])};

  // compute over the integers with a +9 bias so the intermediate never
  // goes negative, then reduce once
  wire [7:0] raw = (u0 * v1) + (u2 * v3) + 8'd9 - (u1 * v0) - (u3 * v2);
  assign form = raw % 8'd3;
  assign adjacent = (form == 2'd0);
endmodule

// ----------------------------------------------------------------------
// Independent behavioural reference for the COMPLETE admission primitive.
// The symplectic form comes from the integer/modulo reference above; policy
// ordering and canonical-address checks are written as direct expressions.
// The formal miter compares every output for all 2^25 input assignments.
// ----------------------------------------------------------------------

module holotrade_admit_golden (
  input  wire [7:0] plan_addr,
  input  wire [7:0] node_addr,
  input  wire [3:0] magic_budget,
  input  wire       node_magic,
  input  wire       sig_ok,
  input  wire       nonce_fresh,
  input  wire       in_window,
  input  wire       pins_ok,
  input  wire       node_in_service,
  output wire       admit,
  output wire [2:0] reason,
  output wire [1:0] form,
  output wire       adjacent,
  output wire [3:0] ray_cost
);
  localparam [2:0] R_OK           = 3'd0;
  localparam [2:0] R_BAD_SIG      = 3'd1;
  localparam [2:0] R_REPLAY       = 3'd2;
  localparam [2:0] R_WINDOW       = 3'd3;
  localparam [2:0] R_PIN_DRIFT    = 3'd4;
  localparam [2:0] R_NO_MAGIC     = 3'd5;
  localparam [2:0] R_IN_SERVICE   = 3'd6;
  localparam [2:0] R_BAD_ADDR     = 3'd7;

  w33_form_golden geom (
    .u(plan_addr), .v(node_addr), .form(form), .adjacent(adjacent)
  );

  wire p_trits = (plan_addr[1:0] != 2'd3) && (plan_addr[3:2] != 2'd3) &&
                  (plan_addr[5:4] != 2'd3) && (plan_addr[7:6] != 2'd3);
  wire n_trits = (node_addr[1:0] != 2'd3) && (node_addr[3:2] != 2'd3) &&
                  (node_addr[5:4] != 2'd3) && (node_addr[7:6] != 2'd3);
  wire p_canon = (plan_addr[1:0] == 2'd1) ||
                 ((plan_addr[1:0] == 2'd0) && (plan_addr[3:2] == 2'd1)) ||
                 ((plan_addr[3:0] == 4'd0) && (plan_addr[5:4] == 2'd1)) ||
                 ((plan_addr[5:0] == 6'd0) && (plan_addr[7:6] == 2'd1));
  wire n_canon = (node_addr[1:0] == 2'd1) ||
                 ((node_addr[1:0] == 2'd0) && (node_addr[3:2] == 2'd1)) ||
                 ((node_addr[3:0] == 4'd0) && (node_addr[5:4] == 2'd1)) ||
                 ((node_addr[5:0] == 6'd0) && (node_addr[7:6] == 2'd1));
  wire addr_ok = p_trits && n_trits && p_canon && n_canon;
  wire needs_magic = |magic_budget;

  assign reason = (!sig_ok)                    ? R_BAD_SIG
                : (!addr_ok)                   ? R_BAD_ADDR
                : (!nonce_fresh)               ? R_REPLAY
                : (!in_window)                 ? R_WINDOW
                : (!pins_ok)                   ? R_PIN_DRIFT
                : (needs_magic && !node_magic) ? R_NO_MAGIC
                : (node_in_service)            ? R_IN_SERVICE
                :                                R_OK;
  assign admit = (reason == R_OK);
  assign ray_cost = (plan_addr == node_addr) ? 4'd6 : (adjacent ? 4'd3 : 4'd5);
endmodule

`default_nettype wire
