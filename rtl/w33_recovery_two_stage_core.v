`default_nettype none
module w33_recovery_two_stage_core(
 input wire clk,input wire rst,input wire load_entry,input wire advance,
 input wire block_in,input wire [5:0] residual_lo,input wire [5:0] residual_hi,
 input wire [39:0] busy,
 output reg valid,output reg entry_q,output reg block_q,
 output reg [5:0] from,output reg [5:0] to,output reg [5:0] free_after);
reg [39:0] zero_lines,single_lines; reg [2:0] occv; integer p,q;
reg [39:0] pm,qm,shared; integer F,s1,z,refill,after,release; reg best_valid; integer best_after,best_release,best_from,best_to;
wire [5:0] entry_source = block_q ? residual_hi : residual_lo;
function [39:0] plmask; input [5:0] x; begin case(x)
6'd0: plmask=40'h000000000f;
6'd1: plmask=40'h00000000f0;
6'd2: plmask=40'h0000000f00;
6'd3: plmask=40'h000000f000;
6'd4: plmask=40'h0000001111;
6'd5: plmask=40'h0000070001;
6'd6: plmask=40'h0000380001;
6'd7: plmask=40'h0001c00010;
6'd8: plmask=40'h000e000100;
6'd9: plmask=40'h0070001000;
6'd10: plmask=40'h0380000010;
6'd11: plmask=40'h1c00001000;
6'd12: plmask=40'he000000100;
6'd13: plmask=40'h0000002222;
6'd14: plmask=40'h0012400002;
6'd15: plmask=40'h2480000002;
6'd16: plmask=40'h4020080020;
6'd17: plmask=40'h0800900200;
6'd18: plmask=40'h0104202000;
6'd19: plmask=40'h1008010020;
6'd20: plmask=40'h8001022000;
6'd21: plmask=40'h0240040200;
6'd22: plmask=40'h0000004444;
6'd23: plmask=40'h0049000004;
6'd24: plmask=40'h4900000004;
6'd25: plmask=40'h8010100040;
6'd26: plmask=40'h1000600400;
6'd27: plmask=40'h0202084000;
6'd28: plmask=40'h0404040040;
6'd29: plmask=40'h2000814000;
6'd30: plmask=40'h00a0020400;
6'd31: plmask=40'h0000008888;
6'd32: plmask=40'h0024800008;
6'd33: plmask=40'h9200000008;
6'd34: plmask=40'h2040200080;
6'd35: plmask=40'h0401080800;
6'd36: plmask=40'h0088108000;
6'd37: plmask=40'h0802020080;
6'd38: plmask=40'h4000448000;
6'd39: plmask=40'h0110010800;
default: plmask=40'b0; endcase end endfunction
function integer pop40; input [39:0] x; integer j; begin pop40=0; for(j=0;j<40;j=j+1) pop40=pop40+x[j]; end endfunction
always @* begin zero_lines=0; single_lines=0;
occv=busy[0]+busy[4]+busy[5]+busy[6]; zero_lines[0]=(occv==0); single_lines[0]=(occv==1);
occv=busy[0]+busy[13]+busy[14]+busy[15]; zero_lines[1]=(occv==0); single_lines[1]=(occv==1);
occv=busy[0]+busy[22]+busy[23]+busy[24]; zero_lines[2]=(occv==0); single_lines[2]=(occv==1);
occv=busy[0]+busy[31]+busy[32]+busy[33]; zero_lines[3]=(occv==0); single_lines[3]=(occv==1);
occv=busy[1]+busy[4]+busy[7]+busy[10]; zero_lines[4]=(occv==0); single_lines[4]=(occv==1);
occv=busy[1]+busy[13]+busy[16]+busy[19]; zero_lines[5]=(occv==0); single_lines[5]=(occv==1);
occv=busy[1]+busy[22]+busy[25]+busy[28]; zero_lines[6]=(occv==0); single_lines[6]=(occv==1);
occv=busy[1]+busy[31]+busy[34]+busy[37]; zero_lines[7]=(occv==0); single_lines[7]=(occv==1);
occv=busy[2]+busy[4]+busy[8]+busy[12]; zero_lines[8]=(occv==0); single_lines[8]=(occv==1);
occv=busy[2]+busy[13]+busy[17]+busy[21]; zero_lines[9]=(occv==0); single_lines[9]=(occv==1);
occv=busy[2]+busy[22]+busy[26]+busy[30]; zero_lines[10]=(occv==0); single_lines[10]=(occv==1);
occv=busy[2]+busy[31]+busy[35]+busy[39]; zero_lines[11]=(occv==0); single_lines[11]=(occv==1);
occv=busy[3]+busy[4]+busy[9]+busy[11]; zero_lines[12]=(occv==0); single_lines[12]=(occv==1);
occv=busy[3]+busy[13]+busy[18]+busy[20]; zero_lines[13]=(occv==0); single_lines[13]=(occv==1);
occv=busy[3]+busy[22]+busy[27]+busy[29]; zero_lines[14]=(occv==0); single_lines[14]=(occv==1);
occv=busy[3]+busy[31]+busy[36]+busy[38]; zero_lines[15]=(occv==0); single_lines[15]=(occv==1);
occv=busy[5]+busy[19]+busy[29]+busy[39]; zero_lines[16]=(occv==0); single_lines[16]=(occv==1);
occv=busy[5]+busy[20]+busy[30]+busy[37]; zero_lines[17]=(occv==0); single_lines[17]=(occv==1);
occv=busy[5]+busy[21]+busy[28]+busy[38]; zero_lines[18]=(occv==0); single_lines[18]=(occv==1);
occv=busy[6]+busy[16]+busy[27]+busy[35]; zero_lines[19]=(occv==0); single_lines[19]=(occv==1);
occv=busy[6]+busy[17]+busy[25]+busy[36]; zero_lines[20]=(occv==0); single_lines[20]=(occv==1);
occv=busy[6]+busy[18]+busy[26]+busy[34]; zero_lines[21]=(occv==0); single_lines[21]=(occv==1);
occv=busy[7]+busy[14]+busy[26]+busy[38]; zero_lines[22]=(occv==0); single_lines[22]=(occv==1);
occv=busy[7]+busy[17]+busy[29]+busy[32]; zero_lines[23]=(occv==0); single_lines[23]=(occv==1);
occv=busy[7]+busy[20]+busy[23]+busy[35]; zero_lines[24]=(occv==0); single_lines[24]=(occv==1);
occv=busy[8]+busy[14]+busy[27]+busy[37]; zero_lines[25]=(occv==0); single_lines[25]=(occv==1);
occv=busy[8]+busy[18]+busy[28]+busy[32]; zero_lines[26]=(occv==0); single_lines[26]=(occv==1);
occv=busy[8]+busy[19]+busy[23]+busy[36]; zero_lines[27]=(occv==0); single_lines[27]=(occv==1);
occv=busy[9]+busy[14]+busy[25]+busy[39]; zero_lines[28]=(occv==0); single_lines[28]=(occv==1);
occv=busy[9]+busy[16]+busy[30]+busy[32]; zero_lines[29]=(occv==0); single_lines[29]=(occv==1);
occv=busy[9]+busy[21]+busy[23]+busy[34]; zero_lines[30]=(occv==0); single_lines[30]=(occv==1);
occv=busy[10]+busy[15]+busy[30]+busy[36]; zero_lines[31]=(occv==0); single_lines[31]=(occv==1);
occv=busy[10]+busy[18]+busy[24]+busy[39]; zero_lines[32]=(occv==0); single_lines[32]=(occv==1);
occv=busy[10]+busy[21]+busy[27]+busy[33]; zero_lines[33]=(occv==0); single_lines[33]=(occv==1);
occv=busy[11]+busy[15]+busy[28]+busy[35]; zero_lines[34]=(occv==0); single_lines[34]=(occv==1);
occv=busy[11]+busy[17]+busy[24]+busy[37]; zero_lines[35]=(occv==0); single_lines[35]=(occv==1);
occv=busy[11]+busy[19]+busy[26]+busy[33]; zero_lines[36]=(occv==0); single_lines[36]=(occv==1);
occv=busy[12]+busy[15]+busy[29]+busy[34]; zero_lines[37]=(occv==0); single_lines[37]=(occv==1);
occv=busy[12]+busy[16]+busy[24]+busy[38]; zero_lines[38]=(occv==0); single_lines[38]=(occv==1);
occv=busy[12]+busy[20]+busy[25]+busy[33]; zero_lines[39]=(occv==0); single_lines[39]=(occv==1);
end
always @* begin from=0;to=0;free_after=0;best_valid=0;best_after=-1;best_release=-1;best_from=63;best_to=63;F=pop40(zero_lines);
for(p=0;p<40;p=p+1) begin pm=plmask(p); s1=pop40(single_lines & pm);
 for(q=0;q<40;q=q+1) begin qm=plmask(q); shared=pm & qm;
  if(busy[p] && !busy[q] && (|shared) && (!entry_q || p==entry_source)) begin
   z=pop40(zero_lines & qm); refill=|(single_lines & shared); after=F+s1-z-refill; release=F+s1;
   if(!best_valid || after>best_after || (after==best_after && (release>best_release || (release==best_release && (p<best_from || (p==best_from && q<best_to)))))) begin
    best_valid=1;best_after=after;best_release=release;best_from=p;best_to=q; end
  end end end
if(best_valid) begin from=best_from[5:0];to=best_to[5:0];free_after=best_after[5:0];end end
always @(posedge clk) begin if(rst) begin valid<=0;entry_q<=0;block_q<=0; end else begin if(load_entry) begin valid<=1;entry_q<=1;block_q<=block_in; end else if(advance && valid) entry_q<=0; end end
endmodule
`default_nettype wire
