"use strict";
// Exact one-step integer decoder witness. BigInt rationals; no solver or floats.
const abs=x=>x<0n?-x:x;
function gcd(a,b){a=abs(a);b=abs(b);while(b){[a,b]=[b,a%b];}return a;}
function rat(n,d=1n){if(d===0n)throw new Error('zero rational denominator');if(d<0n){n=-n;d=-d;}const g=gcd(n,d);return [n/g,d/g];}
function parse(x){if(typeof x!=='string'||x.length>128||!/^[-+]?\d+(\/\d+)?$/.test(x))throw new TypeError('rational string required');const [a,b='1']=x.split('/');return rat(BigInt(a),BigInt(b));}
const add=(a,b)=>rat(a[0]*b[1]+b[0]*a[1],a[1]*b[1]);
const scale=(a,b)=>rat(a[0]*b,a[1]);
const eq=(a,b)=>a[0]*b[1]===b[0]*a[1];
function vector(v){if(!Array.isArray(v)||v.length!==40||v.some(x=>!Number.isSafeInteger(x)))throw new TypeError('40 safe integer coordinates required');return v.map(BigInt);}
const neg=v=>v.reduce((s,x)=>s+(x<0n?-x:0n),0n);
function verifyDualWitness(w,policy,receipt,hash){
  if(!w||typeof w!=='object')throw new TypeError('dual witness required');
  const {lines}=w;
  if(!Array.isArray(lines)||lines.length!==40||lines.some(L=>!Array.isArray(L)||L.length!==4||new Set(L).size!==4||L.some(p=>!Number.isInteger(p)||p<0||p>=40)))throw new TypeError('40 four-point lines required');
  if(new Set(lines.map(L=>[...L].sort((a,b)=>a-b).join(','))).size!==40)throw new Error('duplicate geometry lines');
  if(Array.from({length:40},(_,p)=>lines.filter(L=>L.includes(p)).length).some(n=>n!==4))throw new Error('geometry degree mismatch');
  if(hash(lines)!==policy.geometryDigest)throw new Error('geometry identity mismatch');
  const start=vector(w.start),end=vector(w.end),move=vector(w.move),e=vector(w.lineImage);
  if(hash(w.start)!==policy.inputPreimageDigest||hash(w.lineImage)!==policy.fiberDigest||hash(w.end)!==receipt.finalPreimageDigest)throw new Error('witness vector identity mismatch');
  if(!Array.isArray(w.dual)||w.dual.length!==40)throw new TypeError('40 dual coordinates required');
  const y=w.dual.map(parse);
  if(!start.every((x,i)=>x+move[i]===end[i]))throw new Error('witness transition mismatch');
  for(let j=0;j<40;j++){
    if(lines[j].reduce((s,p)=>s+start[p],0n)!==e[j]||lines[j].reduce((s,p)=>s+end[p],0n)!==e[j])throw new Error('witness fiber mismatch');
  }
  const h=Array.from({length:40},(_,p)=>lines.reduce((s,L,j)=>L.includes(p)?add(s,y[j]):s,rat(0n)));
  if(h.some(([n,d])=>abs(n)>d))throw new Error('dual infeasible');
  const gamma=y.reduce((s,a,j)=>add(s,scale(a,e[j])),rat(0n));
  if(!eq(gamma,rat(end.reduce((s,x)=>s+abs(x),0n))))throw new Error('nonzero duality gap');
  const initial=neg(start),final=neg(end);
  if(initial!==BigInt(receipt.initialNegativeMass)||final!==BigInt(receipt.finalNegativeMass)||final!==BigInt(policy.certifiedExactDepth)||final>=initial)throw new Error('actual negativity mismatch');
  const moveDigest=hash(w.move);
  if(w.moveDigest!==moveDigest)throw new Error('witness move digest mismatch');
  if(receipt.steps.length!==1||receipt.steps[0].kind!=='circuit'||receipt.steps[0].moveDigest!==moveDigest||!policy.permittedMoveDigests.includes(moveDigest))throw new Error('unapproved one-step circuit');
  // Four-regular incidence fixes sum(x); equality in the feasible l1 dual
  // therefore certifies minimal negative mass in this entire integer fibre.
  return Object.freeze({dualVerified:true,dualWitnessDigest:hash(w)});
}
module.exports={verifyDualWitness};
