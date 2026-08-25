// ======================================================================
// HOLOTRADE Q4 CONTROLLER / HYPERCUBE CERTIFICATE
//
// Exact role only: Q4 is the 16-state toroidal-knight / Gray / e-cube
// controller.  Recent W33-Theory work rules out identifying a 16-point W33
// induced graph with Q4.  The exact W33 bridge instead passes through Q4
// face-edge incidence modulo antipodal translation, yielding Reye 12_4 16_3.
// ======================================================================
(function (root) {
  "use strict";
  const E = root.HolotradeEvidence || (typeof require !== "undefined" ? require("./evidence.js") : null);
  if (!E) throw new Error("hypercube requires evidence.js");
  const SCHEMA = "holotrade.q4-controller.v1";
  const VERTICES = Object.freeze([...Array(16).keys()]);
  const popcount = (x) => x.toString(2).split("1").length - 1;
  const hamming = (a, b) => popcount((a ^ b) & 15);

  const EDGES = Object.freeze(VERTICES.flatMap((v) => [...Array(4).keys()]
    .map((d) => [v, v ^ (1 << d)].sort((a,b)=>a-b))
    .filter(([a,b]) => a === v)));

  function key(xs) { return [...xs].sort((a,b)=>a-b).join(","); }
  const faceMap = new Map();
  for (const a of VERTICES) for (let i=0;i<4;i++) for (let j=i+1;j<4;j++) {
    const f = [a, a^(1<<i), a^(1<<j), a^(1<<i)^(1<<j)];
    faceMap.set(key(f), Object.freeze(f.sort((x,y)=>x-y)));
  }
  const FACES = Object.freeze([...faceMap.values()].sort((a,b)=>key(a).localeCompare(key(b))));
  const antipode = (v) => v ^ 15;
  function antipodalClass(items) {
    const itemByKey = new Map(items.map((x) => [key(x), x]));
    const seen = new Set(), classes = [];
    for (const item of items) {
      const k = key(item); if (seen.has(k)) continue;
      const anti = item.map(antipode).sort((a,b)=>a-b), ak = key(anti);
      seen.add(k); seen.add(ak);
      classes.push(Object.freeze([itemByKey.get(k), itemByKey.get(ak)]));
    }
    return Object.freeze(classes);
  }
  const EDGE_CLASSES = antipodalClass(EDGES);
  const FACE_CLASSES = antipodalClass(FACES);

  function classContains(cls, edgeOrFace) { return cls.some((x) => key(x) === key(edgeOrFace)); }
  function reyeIncidences() {
    const rows = [];
    for (let ei=0; ei<EDGE_CLASSES.length; ei++) for (let fi=0; fi<FACE_CLASSES.length; fi++) {
      let incident = false;
      for (const e of EDGE_CLASSES[ei]) for (const f of FACE_CLASSES[fi]) {
        if (e.every((v) => f.includes(v))) incident = true;
      }
      if (incident) rows.push(Object.freeze({ edgeClass: ei, faceClass: fi }));
    }
    return Object.freeze(rows);
  }

  function grayCycle() {
    return Object.freeze(VERTICES.map((i) => i ^ (i >> 1)));
  }
  function eCubeRoute(from, to, order = [0,1,2,3]) {
    if (!VERTICES.includes(from) || !VERTICES.includes(to)) throw new RangeError("Q4 endpoint out of range");
    const dims = [...order];
    if (new Set(dims).size !== 4 || dims.some((d)=>!Number.isInteger(d)||d<0||d>3)) throw new TypeError("order must permute Q4 dimensions 0..3");
    const hops=[from]; let cur=from;
    for (const d of dims) if (((cur^to)>>d)&1) { cur ^= 1<<d; hops.push(cur); }
    return Object.freeze({ from, to, hops:Object.freeze(hops), distance:hops.length-1, shortest:(hops.length-1)===hamming(from,to) });
  }

  function sectorOverlay(anchorLines) {
    if (!Array.isArray(anchorLines) || anchorLines.length !== 4 || new Set(anchorLines).size !== 4) throw new TypeError("exactly four distinct W33 anchor lines are required");
    const ordered=[...anchorLines].sort((a,b)=>a-b);
    const dimensions=Object.fromEntries(ordered.map((lineId,d)=>[lineId,d]));
    return Object.freeze({
      schema:"holotrade.q4-w33-sector-overlay.v1",
      anchorLines:Object.freeze(ordered), dimensions:Object.freeze(dimensions),
      canonical:false,
      boundary:"A chosen bijection between four W33 anchor-line sectors and four Q4 controller dimensions. It is an execution overlay, not an isomorphism of the W33 spread graph with Q4.",
    });
  }

  function certificate() {
    const inc=reyeIncidences();
    const edeg=Array(EDGE_CLASSES.length).fill(0), fdeg=Array(FACE_CLASSES.length).fill(0);
    for (const r of inc) { edeg[r.edgeClass]++; fdeg[r.faceClass]++; }
    const gray=grayCycle();
    const grayClosed=gray.every((v,i)=>hamming(v,gray[(i+1)%gray.length])===1);
    const theorem={
      q4Vertices16:VERTICES.length===16,
      q4Edges32:EDGES.length===32,
      q4Faces24:FACES.length===24,
      degree4:VERTICES.every((v)=>EDGES.filter((e)=>e.includes(v)).length===4),
      diameter4:Math.max(...VERTICES.flatMap((a)=>VERTICES.map((b)=>hamming(a,b))))===4,
      grayHamiltonCycle:grayClosed && new Set(gray).size===16,
      antipodalEdgeClasses16:EDGE_CLASSES.length===16,
      antipodalFaceClasses12:FACE_CLASSES.length===12,
      reyeFlags48:inc.length===48,
      reye16SideDegree3:edeg.every((x)=>x===3),
      reye12SideDegree4:fdeg.every((x)=>x===4),
    };
    const body={schema:SCHEMA,theorem,valid:Object.values(theorem).every(Boolean),
      counts:{vertices:16,edges:32,faces:24,edgeClasses:EDGE_CLASSES.length,faceClasses:FACE_CLASSES.length,incidences:inc.length},
      evidenceBoundary:"Exact Q4 combinatorics and its antipodal face-edge Reye incidence. W33-Theory independently proves this incidence structure occurs twice inside W(3,3); this module does not reproduce that graph-isomorphism search."};
    return Object.freeze({...body,digest:E.demoDigest(body)});
  }

  const API={SCHEMA,VERTICES,EDGES,FACES,EDGE_CLASSES,FACE_CLASSES,popcount,hamming,antipode,reyeIncidences,grayCycle,eCubeRoute,sectorOverlay,certificate};
  root.HolotradeHypercube=API;
  if (typeof module!=="undefined"&&module.exports) module.exports=API;
})(typeof window!=="undefined"?window:globalThis);
