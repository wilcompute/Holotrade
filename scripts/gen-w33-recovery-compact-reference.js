#!/usr/bin/env node
"use strict";

// Independent 480-edge behavioral reference for bit-level proof of the compact
// chooser.  Unlike the optimized core it scores candidates with the legacy
// variables `after=F+s1-z-refill` and `release=F+s1`.  The separate source
// certificate proves that pruning the 1600 labelled pairs to these 480 W33
// directed edges is exact.
const fs=require("node:fs"),path=require("node:path"),S=require("../js/substrate.js");
const root=path.resolve(__dirname,".."),outPath=path.join(root,"rtl/build/w33_recovery_two_stage_core_compact_ref.v");
fs.mkdirSync(path.dirname(outPath),{recursive:true});
const pls=Array.from({length:40},()=>[]);S.LINES.forEach((L,li)=>L.forEach(p=>pls[p].push(li)));for(const x of pls)x.sort((a,b)=>a-b);
const rows=[],edge=[];for(let p=0;p<40;p++){const a=[];for(const li of pls[p])for(const q of S.LINES[li])if(q!==p)a.push([q,li]);a.sort((x,y)=>x[0]-y[0]);if(a.length!==12||new Set(a.map(x=>x[0])).size!==12)throw new Error(`bad row ${p}`);rows.push(a.map(x=>x[0]));edge.push(a.map(x=>x[1]));}
function mask(p){let m=0n;for(const li of pls[p])m|=1n<<BigInt(li);return `40'h${m.toString(16).padStart(10,"0")}`;}
const pointCases=Array.from({length:40},(_,p)=>`6'd${p}: plmask=${mask(p)};`).join("\n"),nbr=[],eline=[];
for(let p=0;p<40;p++)for(let k=0;k<12;k++){const key=p*16+k;nbr.push(`10'd${key}: nbr=6'd${rows[p][k]};`);eline.push(`10'd${key}: edge_line=6'd${edge[p][k]};`);}
const occ=S.LINES.map((L,li)=>`occv=${L.map(p=>`busy[${p}]`).join("+")}; zero_lines[${li}]=(occv==0); single_lines[${li}]=(occv==1);`).join("\n");
const v=`\`default_nettype none
module w33_recovery_two_stage_core_compact_ref(
 input wire clk,input wire rst,input wire load_entry,input wire advance,
 input wire block_in,input wire [5:0] residual_lo,input wire [5:0] residual_hi,input wire [39:0] busy,
 output reg valid,output reg entry_q,output reg block_q,output reg [5:0] from,output reg [5:0] to,output reg [5:0] free_after);
reg [39:0] zero_lines,single_lines;reg [2:0] occv;integer p,k,q,li,F,s1,z,refill,after,release;
reg [39:0] pm,qm;reg best_valid;integer best_after,best_release,best_from,best_to;
wire [5:0] entry_source=block_q?residual_hi:residual_lo;
function [39:0] plmask;input [5:0] x;begin case(x)\n${pointCases}\ndefault:plmask=40'b0;endcase end endfunction
function [5:0] nbr;input [5:0] p0;input [3:0] k0;reg [9:0] key;begin key={p0,k0};case(key)\n${nbr.join("\n")}\ndefault:nbr=6'd0;endcase end endfunction
function [5:0] edge_line;input [5:0] p0;input [3:0] k0;reg [9:0] key;begin key={p0,k0};case(key)\n${eline.join("\n")}\ndefault:edge_line=6'd0;endcase end endfunction
function integer pop40;input [39:0] x;integer j;begin pop40=0;for(j=0;j<40;j=j+1)pop40=pop40+x[j];end endfunction
always @* begin zero_lines=0;single_lines=0;\n${occ}\nend
always @* begin
 from=0;to=0;free_after=0;best_valid=0;best_after=-99;best_release=-99;best_from=63;best_to=63;F=pop40(zero_lines);
 for(p=0;p<40;p=p+1)begin pm=plmask(p);s1=pop40(single_lines&pm);if(busy[p]&&(!entry_q||p==entry_source))begin
  for(k=0;k<12;k=k+1)begin q=nbr(p,k);li=edge_line(p,k);if(!busy[q])begin qm=plmask(q);z=pop40(zero_lines&qm);refill=single_lines[li];after=F+s1-z-refill;release=F+s1;
   if(!best_valid||after>best_after||(after==best_after&&(release>best_release||(release==best_release&&(p<best_from||(p==best_from&&q<best_to))))))begin best_valid=1;best_after=after;best_release=release;best_from=p;best_to=q;end
  end end
 end end
 if(best_valid)begin from=best_from[5:0];to=best_to[5:0];free_after=best_after[5:0];end
end
always @(posedge clk)begin if(rst)begin valid<=0;entry_q<=0;block_q<=0;end else begin if(load_entry)begin valid<=1;entry_q<=1;block_q<=block_in;end else if(advance&&valid)entry_q<=0;end end
endmodule
\`default_nettype wire
`;
fs.writeFileSync(outPath,v);console.log(JSON.stringify({status:"PASS",output:path.relative(root,outPath),directedCandidates:480,score:"legacy after/release"}));
