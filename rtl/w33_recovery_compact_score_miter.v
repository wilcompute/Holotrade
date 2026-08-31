`default_nettype none
// Small bit-vector miter for the only arithmetic transformation in the compact
// recovery chooser. Geometry/candidate-set equality and the sequential block
// are certified independently by w33_recovery_compact_structural_equivalence.js.
module w33_recovery_compact_score_miter(
  input wire [5:0] F,
  input wire [2:0] s1_a, input wire [2:0] z_a, input wire refill_a,
  input wire [2:0] s1_b, input wire [2:0] z_b, input wire refill_b,
  input wire [5:0] p_a, input wire [5:0] q_a,
  input wire [5:0] p_b, input wire [5:0] q_b,
  output wire failure
);
integer Fi,s1ai,zai,rai,s1bi,zbi,rbi;
integer after_a,release_a,delta_a,after_b,release_b,delta_b;
integer compact_free_a,compact_free_b;
reg base_a_better,compact_a_better;
wire valid_inputs = (F<=6'd40) && (s1_a<=3'd4) && (z_a<=3'd4) &&
                    (s1_b<=3'd4) && (z_b<=3'd4) &&
                    (p_a<6'd40) && (q_a<6'd40) &&
                    (p_b<6'd40) && (q_b<6'd40);
always @* begin
  Fi=F; s1ai=s1_a; zai=z_a; rai=refill_a;
  s1bi=s1_b; zbi=z_b; rbi=refill_b;
  after_a=Fi+s1ai-zai-rai; release_a=Fi+s1ai; delta_a=s1ai-zai-rai;
  after_b=Fi+s1bi-zbi-rbi; release_b=Fi+s1bi; delta_b=s1bi-zbi-rbi;
  compact_free_a=Fi+delta_a; compact_free_b=Fi+delta_b;
  base_a_better = (after_a>after_b) ||
                  ((after_a==after_b) && ((release_a>release_b) ||
                   ((release_a==release_b) && ((p_a<p_b) ||
                    ((p_a==p_b) && (q_a<q_b))))));
  compact_a_better = (delta_a>delta_b) ||
                     ((delta_a==delta_b) && ((s1ai>s1bi) ||
                      ((s1ai==s1bi) && ((p_a<p_b) ||
                       ((p_a==p_b) && (q_a<q_b))))));
end
wire order_mismatch = base_a_better != compact_a_better;
wire free_a_mismatch = after_a[5:0] != compact_free_a[5:0];
wire free_b_mismatch = after_b[5:0] != compact_free_b[5:0];
assign failure = valid_inputs && (order_mismatch || free_a_mismatch || free_b_mismatch);
endmodule
`default_nettype wire
