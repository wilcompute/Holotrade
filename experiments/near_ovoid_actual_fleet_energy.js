#!/usr/bin/env node
"use strict";

// Seeded-fleet check of where energy can actually enter migration decisions.
// Fleet addresses are [dc.prefix, cell, W33-point].  A level-1 migration keeps
// the prefix+cell fixed, so all destinations in that W33 cell belong to the
// same datacenter and have the same site energy index.  Energy can therefore
// only discriminate cross-cell / cross-subtree candidates, not level-1 point
// choices inside one cell.

const S=require("../js/substrate.js");
const {Fleet}=require("../js/fleet.js");
const catalog=require("../data/catalog.js");

function cellKey(node){return node.addr.slice(0,-1).join(".");}
function energyIndex(dc){return dc.baseEnergy*dc.pue;}
function runExperiment({seeds=64,size=320}={}){
  let cells=0,nodes=0,multiNodeCells=0,adjacentOccupiedPairs=0;
  const dcSeen={};
  for(let i=0;i<seeds;i++){
    const fleet=new Fleet({datacenters:catalog.DATACENTERS,hardware:catalog.HARDWARE,workloads:catalog.WORKLOADS,operators:catalog.OPERATORS,size,seed:`near-ovoid-actual-fleet-${String(i+1).padStart(3,"0")}`});
    const groups=new Map();
    for(const node of fleet.nodes){const k=cellKey(node);if(!groups.has(k))groups.set(k,[]);groups.get(k).push(node);nodes++;}
    for(const xs of groups.values()){
      cells++;if(xs.length>1)multiNodeCells++;
      const dcs=new Set(xs.map((x)=>x.dcId));if(dcs.size!==1)throw new Error("one W33 cell crossed datacenter subtrees");
      const dc=catalog.DATACENTERS.find((d)=>d.id===xs[0].dcId),scores=new Set(xs.map(()=>energyIndex(dc)));
      if(scores.size!==1)throw new Error("within-cell energy score was not invariant");
      dcSeen[dc.id]=(dcSeen[dc.id]||0)+1;
      for(let a=0;a<xs.length;a++)for(let b=a+1;b<xs.length;b++)if(S.isAdjacent(xs[a].cellPoint,xs[b].cellPoint)){
        adjacentOccupiedPairs++;if(xs[a].dcId!==xs[b].dcId)throw new Error("level-1 adjacent pair crossed datacenters");
      }
    }
  }
  return {
    schema:"holotrade.near-ovoid-actual-fleet-energy.v1",evidence:"SEEDED FLEET VERIFICATION + ADDRESS-CONSTRUCTION INVARIANT",
    design:{seeds,size,addressShape:"[dc.prefix, cell, W33-point]"},observed:{nodes,cells,multiNodeCells,adjacentOccupiedPairs,cellsByDatacenter:dcSeen},
    theorem:{withinLevel1CellSingleDatacenter:true,withinLevel1CellEnergyIndexConstant:true,level1LocalityCostForChosenMigration:"3 rays / 1 hop",energyCanBreakLevel1PointTie:false},
    reading:"The actual Holotrade fleet model assigns a whole W33 cell to one datacenter subtree. Energy cannot rank destinations inside that cell; it becomes meaningful only when routing candidates span cells or datacenter prefixes.",
    supersedesInterpretation:"data/near_ovoid_secondary_costs.json remains a synthetic point-to-site sensitivity field, not an actual seeded-fleet level-1 energy result.",
    boundary:"Catalog energy values are prototype seed data, not live telemetry. This artifact establishes model topology, not physical energy savings."
  };
}
if(require.main===module)process.stdout.write(JSON.stringify(runExperiment(),null,2)+"\n");
module.exports={runExperiment,cellKey,energyIndex};
