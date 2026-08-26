// ======================================================================
// HOLOTRADE W33 FRONTIER CERTIFICATES
// Exact finite certificates only: spread clique homology, Q4/Reye binary
// incidence code, all-anchor spread shells, and fixed-line ternary schedule.
// ======================================================================
(function(root){
  "use strict";
  const V=root.HolotradeSpreadVenueMarket||(typeof require!=="undefined"?require("./spread-venue-market.js"):null);
  const Q=root.HolotradeHypercube||(typeof require!=="undefined"?require("./hypercube.js"):null);
  const E=root.HolotradeEvidence||(typeof require!=="undefined"?require("./evidence.js"):null);
  if(!V||!Q||!E)throw new Error("w33-frontier-certificates requires spread-venue-market, hypercube, evidence");

  const popcount=(x)=>{let n=0;for(let y=BigInt(x);y;y>>=1n)n+=Number(y&1n);return n;};
  function gf2Rank(vectors){
    const piv=new Map();let rank=0;
    for(const raw of vectors){let x=BigInt(raw);while(x){const p=x.toString(2).length-1;if(piv.has(p))x^=piv.get(p);else{piv.set(p,x);rank++;break;}}}
    return rank;
  }
  function adjacency(){return Array.from({length:36},(_,i)=>Array.from({length:36},(_,j)=>i!==j&&V.overlap(i,j)===4));}
  function spreadCliques(){
    const A=adjacency(),edges=[],triangles=[],tetrahedra=[];
    for(let i=0;i<36;i++)for(let j=i+1;j<36;j++)if(A[i][j])edges.push([i,j]);
    for(let i=0;i<36;i++)for(let j=i+1;j<36;j++)if(A[i][j])for(let k=j+1;k<36;k++)if(A[i][k]&&A[j][k])triangles.push([i,j,k]);
    for(const t of triangles){const [i,j,k]=t;for(let l=k+1;l<36;l++)if(A[i][l]&&A[j][l]&&A[k][l])tetrahedra.push([i,j,k,l]);}
    return {vertices:Array.from({length:36},(_,i)=>[i]),edges,triangles,tetrahedra};
  }
  function boundaryRank(upper,lower){
    const key=(x)=>x.join(","),index=new Map(lower.map((x,i)=>[key(x),i]));
    const faceSize=upper[0].length-1;
    const cols=upper.map((simplex)=>{let bits=0n;for(let skip=0;skip<simplex.length;skip++){const face=simplex.filter((_,i)=>i!==skip);bits^=1n<<BigInt(index.get(key(face)));}return bits;});
    return gf2Rank(cols);
  }
  function spreadCliqueHomology(){
    const C=spreadCliques();
    const r1=boundaryRank(C.edges,C.vertices),r2=boundaryRank(C.triangles,C.edges),r3=boundaryRank(C.tetrahedra,C.triangles);
    const betti=[C.vertices.length-r1,C.edges.length-r1-r2,C.triangles.length-r2-r3,C.tetrahedra.length-r3];
    const theorem={fVector:C.vertices.length===36&&C.edges.length===270&&C.triangles.length===540&&C.tetrahedra.length===135,boundaryRanks:r1===35&&r2===235&&r3===135,betti:betti.join(",")==="1,0,170,0",euler:C.vertices.length-C.edges.length+C.triangles.length-C.tetrahedra.length===171};
    return Object.freeze({schema:"holotrade.w33-spread-clique-homology-gf2.v1",valid:Object.values(theorem).every(Boolean),theorem,fVector:[36,270,540,135],boundaryRanks:[r1,r2,r3],betti,eulerCharacteristic:171,evidenceBoundary:"Exact GF(2) clique-complex homology of the four-line-overlap spread graph. No physical topological phase is inferred."});
  }
  function reyeRows(){
    const rows=Array(12).fill(0n);for(const x of Q.reyeIncidences())rows[x.faceClass]|=1n<<BigInt(x.edgeClass);return rows;
  }
  function rowSpace(rows){
    const basis=[];const piv=new Map();for(const raw of rows){let x=raw;while(x){const p=x.toString(2).length-1;if(piv.has(p))x^=piv.get(p);else{piv.set(p,x);basis.push(x);break;}}}
    const out=[];for(let m=0;m<(1<<basis.length);m++){let x=0n;for(let i=0;i<basis.length;i++)if((m>>i)&1)x^=basis[i];out.push(x);}return out;
  }
  function weightEnumerator(words){const h={};for(const x of words){const w=popcount(x);h[w]=(h[w]||0)+1;}return Object.fromEntries(Object.entries(h).sort((a,b)=>Number(a[0])-Number(b[0])));}
  function reyeCode(){
    const rows=reyeRows(),rank=gf2Rank(rows),kernel=[];for(let x=0;x<65536;x++){const b=BigInt(x);if(rows.every(r=>popcount(r&b)%2===0))kernel.push(b);}
    const weights=weightEnumerator(kernel),d=Math.min(...Object.keys(weights).map(Number).filter(Boolean));
    const rs=rowSpace(rows),rsSet=new Set(rs.map(String)),inter=kernel.filter(x=>rsSet.has(String(x)));
    const theorem={flags48:rows.reduce((s,r)=>s+popcount(r),0)===48,rowWeight4:rows.every(r=>popcount(r)===4),rank8:rank===8,nullity8:kernel.length===256,distance4:d===4,weightEnumerator:JSON.stringify(weights)===JSON.stringify({0:1,4:12,6:64,8:102,10:64,12:12,16:1}),rowCodeSameEnumerator:JSON.stringify(weightEnumerator(rs))===JSON.stringify(weights),intersectionDimension6:inter.length===64,notSelfDual:inter.length!==kernel.length};
    return Object.freeze({schema:"holotrade.q4-reye-binary-code.v1",valid:Object.values(theorem).every(Boolean),theorem,length:16,rank,nullity:16-rank,minimumKernelWeight:d,kernelWeightEnumerator:weights,rowCodeWeightEnumerator:weightEnumerator(rs),rowCodeKernelIntersectionSize:inter.length,rowCodeKernelIntersectionDimension:Math.log2(inter.length),evidenceBoundary:"Exact GF(2) incidence-code invariant of the Q4 antipodal Reye quotient. This is not a physical quantum error-correcting-code claim."});
  }
  function allAnchorCertificate(){
    const anchors=Array.from({length:36},(_,i)=>V.anchorCertificate(i));
    const theorem={anchors36:anchors.length===36,everyNear15:anchors.every(a=>a.near.length===15),everyRemote20:anchors.every(a=>a.remote.length===20),everyTenAntipodes:anchors.every(a=>a.hedges.length===10&&a.hedges.every(h=>h.remoteDistance===3&&h.legs.length===2)),allValid:anchors.every(a=>a.valid)};
    return Object.freeze({schema:"holotrade.w33-all-anchor-johnson-shell.v1",valid:Object.values(theorem).every(Boolean),theorem,labelBoundary:"The local J(6,3) coordinatization is canonical only up to the anchor stabilizer/S6 frame unless an additional frame is supplied."});
  }
  function lineFiberSchedule(lineId){
    const c=V.lineFiberCertificate(lineId);const groups=c.oneLineTriangles.map((g,i)=>Object.freeze({group:i,spreads:Object.freeze([...g])}));
    const theorem={fiber9:c.fiber.length===9,threeGroups:groups.length===3&&groups.every(g=>g.spreads.length===3),partitions:new Set(groups.flatMap(g=>g.spreads)).size===9,certificateValid:c.valid};
    return Object.freeze({schema:"holotrade.w33-fixed-line-ternary-schedule.v1",lineId,valid:Object.values(theorem).every(Boolean),theorem,groups,boundary:"The three groups are exact structural classes in the spread fiber; they are not asserted to be statistically or physically independent failure domains."});
  }
  function certificate(){const homology=spreadCliqueHomology(),reye=reyeCode(),anchors=allAnchorCertificate();const lineSchedules=Array.from({length:40},(_,i)=>lineFiberSchedule(i));const theorem={homology:homology.valid,reye:reye.valid,anchors:anchors.valid,allLineSchedules:lineSchedules.every(x=>x.valid)};const body={schema:"holotrade.w33-frontier-certificates.v1",valid:Object.values(theorem).every(Boolean),theorem,homology,reye,anchors,lineSchedules};return Object.freeze({...body,digest:E.demoDigest(body)});}
  const API={gf2Rank,spreadCliques,spreadCliqueHomology,reyeCode,allAnchorCertificate,lineFiberSchedule,certificate};root.HolotradeW33FrontierCertificates=API;if(typeof module!=="undefined"&&module.exports)module.exports=API;
})(typeof window!=="undefined"?window:globalThis);
