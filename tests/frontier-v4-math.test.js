// ======================================================================
// HoloTrade backend math frontier v4: five requested continuations +
// three outside-the-box exact probes.
// ======================================================================
const test=require("node:test");const assert=require("node:assert/strict");const path=require("node:path");
global.window=global;const root=path.resolve(__dirname,"..");
require(path.join(root,"js/substrate.js"));require(path.join(root,"js/uor.js"));
const W=require(path.join(root,"js/w33-scheduler.js"));require(path.join(root,"js/evidence.js"));
const V=require(path.join(root,"js/spread-venue-market.js"));
const O=require(path.join(root,"js/spread-obstruction.js"));
const H=require(path.join(root,"js/spread-harmonics.js"));
const T=require(path.join(root,"js/tensor-sharding.js"));
const B=require(path.join(root,"js/chart-spread-bridge.js"));

test("anti-Latin spread certificate closes omega=4 alpha=5 chi=8 and yields eight conflict-free batches",()=>{const c=O.certificate();assert.equal(c.valid,true);assert.equal(c.omega,4);assert.equal(c.alpha,5);assert.equal(c.chromaticNumber,8);assert.equal(c.latinSquareGraphOrder6,false);assert.deepEqual(c.colorClassSizes,[5,5,5,5,5,5,4,2]);assert.equal(c.batches.length,8);const a=O.adjacency();for(const batch of c.batches)for(let i=0;i<batch.length;i++)for(let j=i+1;j<batch.length;j++)assert.equal(a[batch[i]][batch[j]],false);});

test("spread Seidel algebra gives exact complementary 15/21 projectors and 1+15+20 resolution",()=>{const c=H.certificate();assert.equal(c.valid,true);assert.deepEqual(c.ranks,{constant:1,harmonic15:15,harmonic20:20});assert.equal(c.etf.vectors,36);assert.equal(c.etf.dimension,15);assert.deepEqual(c.etf.coherence,{numerator:1,denominator:5});assert.equal(c.theorem.seidelQuadratic,true);assert.equal(c.theorem.resolutionOfIdentity,true);});

test("36-vector spread ETF is equiangular and tight using integer Gram arithmetic only",()=>{const c=H.certificate(),G=c.etf.gramNumerator;for(let i=0;i<36;i++){assert.equal(G[i][i],5);for(let j=0;j<36;j++)if(i!==j)assert.equal(Math.abs(G[i][j]),1);}assert.equal(c.theorem.etfTight,true);});

test("tensor product line family has rigorous 110..121 depth-2 blocking interval",()=>{const c=T.depth2Certificate();assert.equal(c.valid,true);assert.equal(c.bounds.lower,110);assert.equal(c.bounds.upper,121);assert.equal(c.openGap,11);assert.equal(c.exactTau,null);assert.equal(c.upperWitness.length,121);});

test("recursive tensor lower amplification exactly matches the lift/tile capacity ratio",()=>{for(let d=1;d<=5;d++){const c=T.recursiveCapacity(d);assert.equal(c.identityHolds,true);assert.equal(c.capacityRatio,Math.pow(10,d-1));assert.equal(c.lowerAmplificationVsLift,c.capacityRatio);}});

test("two spreads furnish ten disjoint 4x4 tensor tiles at exactly the 160-leaf lift capacity",()=>{const c=T.pairedSpreadShard(0,1);assert.equal(c.valid,true);assert.equal(c.tiles.length,10);assert.equal(c.leaves.length,160);assert.equal(c.comparison.standardLineLiftLeaves,160);assert.equal(c.comparison.tensorTileLeaves,16);assert.equal(c.comparison.tilesPerEqualCapacity,10);});

test("540 Q3 skew-line charts are in exact bijection with the 540 triangles of the 36-spread graph",()=>{const c=B.incidenceCertificate();assert.equal(c.valid,true);assert.deepEqual(c.counts,{charts:540,spreadTriangles:540,flags:1620});assert.equal(c.theorem.triangleBijection,true);assert.equal(c.theorem.gram45Iplus6A,true);assert.deepEqual(c.gramSpectrum,{constant:135,multiplicityConstant:1,harmonic15:63,multiplicity15:15,harmonic20:27,multiplicity20:20,rank:36});});

test("strong chart-adjacency/spread-incidence intertwiner is rejected by an exact nonzero residual",()=>{const c=B.intertwinerObstruction();assert.equal(c.valid,true);assert.equal(c.theorem.chartWebDegree6,true);assert.equal(c.theorem.normalEquationsSatisfied,true);assert.notEqual(c.witness.residual,0);assert.match(c.conclusion,/does not preserve/);});

test("spread graph base census remains 36 venues with 270 four-line and 360 one-line pairs",()=>{const c=V.globalCertificate();assert.equal(W.spreads().length,36);assert.equal(c.valid,true);assert.deepEqual(c.pairHistogram,{oneLine:360,fourLines:270});});
