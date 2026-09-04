"use strict";

const assert=require("node:assert/strict");
const crypto=require("node:crypto");
const fs=require("node:fs");
const path=require("node:path");
const test=require("node:test");
const atlas=require("../analysis/w33_f20_payne_five_state_atlas.js");
const {canonical}=require("../analysis/w33_five_front_breakthrough.js");
const {F20PayneCodec,bootCheck}=require("../js/w33-f20-payne-codec.js");

const ROOT=path.resolve(__dirname,"..");
const packet=require("../data/w33_f20_payne_five_state_atlas.json");
const shaFile=(rel)=>`sha256:${crypto.createHash("sha256").update(
  fs.readFileSync(path.join(ROOT,rel),"utf8").replace(/\r\n/g,"\n")
).digest("hex")}`;

test("GAP regenerates the F20 Payne five-state atlas byte-for-object",()=>{
  assert.equal(canonical(atlas.build()),canonical(packet));
  assert.equal(packet.status,"PASS");
  for(const [key,rel] of Object.entries({
    rom:"data/the_45_slot_rom_bijection.json",
    payne:"data/slow_path_is_payne_derivative.json",
    f20Qutrit:"data/w33_f20_qutrit_block_bridge.json",
    gap:"analysis/w33_f20_payne_five_state_atlas.g",
    gapInput:"analysis/w33_f20_payne_five_state_input.g",
  }))assert.equal(packet.sourceHashes[key],shaFile(rel));
});

test("the protected five sites are the inner five-target circuit, not a ROM bank",()=>{
  const c=packet.fiveStateAtlas.circuit;
  assert.deepEqual(c.fibreF20SlowOrbits,[5,10,10,20]);
  assert.deepEqual(c.fibreF20LineOrbits,[2,5,10,10]);
  assert.equal(c.slowTargets.length,5);
  assert.equal(c.inducedEdges,0);
  assert.equal(c.setStabilizerOrder,120);
  assert.equal(c.setStabilizerImage,"S5");
  assert.equal(c.carrierOrbit,216);
  assert.equal(c.mapCount,1);
  assert.deepEqual(new Set(c.qutritSiteToSlowTarget),new Set(c.slowTargets));
});

test("a ROM line realizes the bare-to-completed chain as D10 below F20",()=>{
  const line=packet.fiveStateAtlas.romLine;
  assert.deepEqual(line.innerLineStabilizer,{order:960,kernelOrder:16,image:"A5"});
  assert.deepEqual(line.fullLineStabilizer,{order:1920,kernelOrder:16,image:"S5"});
  assert.equal(line.outerF20.order,20);
  assert.equal(line.outerF20.structure,"C5 : C4");
  assert.equal(line.outerF20.complementClasses,1);
  assert.deepEqual(line.innerIntersection,{order:10,structure:"D10"});
  assert.equal(new Set(line.qutritSiteToRomLinePoint).size,5);
});

test("address-to-Payne transport exists but the stronger site-fibre weld does not",()=>{
  const bridge=packet.addressToPayne;
  assert.deepEqual(bridge.addressActionOrbits,[20,20]);
  assert.deepEqual(bridge.w33AxisActionOrbits,[20,20]);
  assert.equal(bridge.equivariantBijections,800);
  assert.equal(new Set(bridge.addressToW33Axis).size,40);
  assert.equal(bridge.compiler.length,40);
  for(const row of bridge.compiler){
    assert.equal(row.payneSlowCover.length,9);
    assert.equal(row.w33Axis,bridge.addressToW33Axis[row.address]);
  }
  assert.deepEqual(packet.incidenceCompatibilityNoGo,{
    presentationCompatibleF20Isomorphisms:20,
    equivariantMapCandidates:16000,
    coherentMaps:0,
    overlapCensus:packet.incidenceCompatibilityNoGo.overlapCensus,
    conditionTested:packet.incidenceCompatibilityNoGo.conditionTested,
    theorem:packet.incidenceCompatibilityNoGo.theorem,
  });
  assert.deepEqual(packet.incidenceCompatibilityNoGo.overlapCensus,{
    selectedGaugePerSite:[0,0,0,0,0],
    selectedGaugeMatchedAddresses:0,
    maximumMatchedAddresses:20,
    bestSortedPerSiteProfiles:[[4,4,4,4,4]],
    matchedAddressHistogram:{0:9600,20:6400},
    sortedPerSiteProfileHistogram:{"0,0,0,0,0":9600,"4,4,4,4,4":6400},
  });
  assert.deepEqual(packet.oneHopRepair.selectedGaugeDistanceHistogram,{1:40});
  assert.equal(packet.oneHopRepair.selectedGaugeAllExactlyOneHop,true);
  assert.match(packet.boundary,/excludes only the stated F20-equivariant/);
});

test("the README, paper, and live evidence panel publish the atlas and no-go",()=>{
  const read=(rel)=>fs.readFileSync(path.join(ROOT,rel),"utf8");
  assert.match(read("README.md"),/Payne five-state atlas/);
  assert.match(read("README.md"),/9,600 candidates match no address at any site/);
  assert.match(read("README.md"),/6,400 match exactly four/);
  assert.match(read("docs/holotrade.tex"),/One \$F_\{20\}\$, two five-state geometries/);
  assert.match(read("docs/holotrade.tex"),/symmetry alone does not weld them/);
  assert.match(read("js/app.js"),/w33_f20_payne_five_state_atlas\.json/);
  assert.match(read("js/app.js"),/9,600 zero-incidence/);
  assert.match(read("js/app.js"),/6,400 uniform half-incidence/);
  assert.match(read("holotrade.html"),/Payne five-state atlas/);
});

test("the runtime codec fails closed and preserves the selected gauge boundary",()=>{
  assert.deepEqual(bootCheck(),{ok:true,errors:[]});
  const codec=new F20PayneCodec();
  assert.equal(codec.equivariantChoices,800);
  for(let address=0;address<40;address+=1){
    const row=codec.compile(address);
    assert.equal(row.dispatchable,false);
    assert.equal(row.payneSlowCover.length,9);
    assert.equal(row.matchedCircuitTarget,codec.circuitTargetForSite(row.site));
    assert.equal(row.coverContainsMatchedTarget,false);
    assert.equal(row.oneHopRepair.routeDistance,1);
    assert.equal(row.oneHopRepair.dispatchable,false);
    assert.ok(codec.catalogue.coverForAxis(row.oneHopRepair.chosenAxis).includes(row.matchedCircuitTarget));
    assert.match(row.boundary,/neither is a fault-tolerant recode/);
  }
  assert.throws(()=>codec.compile(40),/address must be 0\.\.39/);
  assert.throws(()=>codec.circuitTargetForSite(-1),/site must be 0\.\.4/);
});
