// ======================================================================
// HOLOTRADE CATALOG
// Seed data: the datacentres the fleet lives in, the hardware classes
// a node can be, and the workload classes a buyer can bid for.
//
// Every number here is a plausible public figure used to make the
// simulation legible. None of it is a live feed. Wire a real grid-price
// API, a real DCIM telemetry stream, and a real hardware inventory in
// place of this file and the engines above it do not change.
// ======================================================================

const DATACENTERS = [
  {
    id: "PDX-1",
    name: "Columbia Basin",
    region: "US-Pacific NW",
    grid: "BPA",
    // $/MWh: hydro-dominated, cheap and stable, mild seasonal swing
    baseEnergy: 34,
    energyVol: 0.16,
    carbon: 92,       // gCO2e/kWh
    pue: 1.09,
    tz: -8,
    cooling: "free-air + evaporative",
    ambient: 289,     // K, annual mean intake
    prefix: [3],      // fabric address prefix
  },
  {
    id: "DFW-2",
    name: "North Texas",
    region: "US-Central",
    grid: "ERCOT",
    // ERCOT is the volatile one: negative at 3am, four figures in a heat dome
    baseEnergy: 41,
    energyVol: 0.74,
    carbon: 396,
    pue: 1.31,
    tz: -6,
    cooling: "mechanical + rear-door",
    ambient: 303,
    prefix: [11],
  },
  {
    id: "ARN-1",
    name: "Stockholm North",
    region: "EU-Nordic",
    grid: "Nord Pool SE3",
    baseEnergy: 52,
    energyVol: 0.38,
    carbon: 41,
    pue: 1.07,
    tz: 1,
    cooling: "free-air + district heat recovery",
    ambient: 282,
    prefix: [19],
  },
  {
    id: "DUB-3",
    name: "Dublin West",
    region: "EU-West",
    grid: "SEM",
    baseEnergy: 96,
    energyVol: 0.44,
    carbon: 296,
    pue: 1.22,
    tz: 0,
    cooling: "mechanical",
    ambient: 285,
    prefix: [24],
  },
  {
    id: "SIN-2",
    name: "Jurong",
    region: "APAC-SE",
    grid: "EMC",
    baseEnergy: 118,
    energyVol: 0.29,
    carbon: 408,
    pue: 1.42,
    tz: 8,
    cooling: "chilled water",
    ambient: 305,
    prefix: [31],
  },
  {
    id: "REY-1",
    name: "Reykjanes",
    region: "Iceland",
    grid: "Landsnet",
    baseEnergy: 28,
    energyVol: 0.11,
    carbon: 28,
    pue: 1.04,
    tz: 0,
    cooling: "free-air",
    ambient: 278,
    prefix: [37],
  },
];

// ----------------------------------------------------------------------
// Hardware classes. `baseRate` is the floor price in $/node-hour before
// any of the six multipliers are applied.
//
// `magicCapable` marks the photonic substrate leaves -- the only nodes
// that can serve a job with a non-zero magic budget t. Everything else
// runs the Clifford layer, which is polynomial-time classical and
// therefore portable to literally any machine on the exchange.
// ----------------------------------------------------------------------
const HARDWARE = [
  {
    class: "GX-H",
    name: "GPU / 8x HBM3 accelerator",
    kind: "gpu",
    tflops: 7916,
    memGB: 640,
    memBW: 26.8,
    tdp: 10200,
    baseRate: 31.4,
    lifeHours: 43800,     // ~5 years
    joulesPerOp: 1.2e-15,
    magicCapable: false,
    thermalSensitivity: 1.0,
  },
  {
    class: "GX-B",
    name: "GPU / next-gen dual-die accelerator",
    kind: "gpu",
    tflops: 17800,
    memGB: 1440,
    memBW: 64.0,
    tdp: 14300,
    baseRate: 58.9,
    lifeHours: 39000,
    joulesPerOp: 7.4e-16,
    magicCapable: false,
    thermalSensitivity: 1.35,
  },
  {
    class: "GX-M",
    name: "GPU / open-accelerator module",
    kind: "gpu",
    tflops: 5230,
    memGB: 1536,
    memBW: 42.4,
    tdp: 8800,
    baseRate: 22.8,
    lifeHours: 43800,
    joulesPerOp: 1.6e-15,
    magicCapable: false,
    thermalSensitivity: 0.95,
  },
  {
    class: "CX-E",
    name: "CPU / 2x 128-core",
    kind: "cpu",
    tflops: 84,
    memGB: 3072,
    memBW: 0.92,
    tdp: 1400,
    baseRate: 3.9,
    lifeHours: 61320,     // ~7 years
    joulesPerOp: 9.0e-15,
    magicCapable: false,
    thermalSensitivity: 0.6,
  },
  {
    class: "CX-A",
    name: "CPU / 192-core ARM",
    kind: "cpu",
    tflops: 61,
    memGB: 2304,
    memBW: 0.77,
    tdp: 900,
    baseRate: 2.7,
    lifeHours: 61320,
    joulesPerOp: 6.1e-15,
    magicCapable: false,
    thermalSensitivity: 0.5,
  },
  {
    class: "FX-1",
    name: "FPGA / reconfigurable fabric",
    kind: "fpga",
    tflops: 340,
    memGB: 128,
    memBW: 3.6,
    tdp: 640,
    baseRate: 6.4,
    lifeHours: 78840,     // ~9 years, no moving thermal cycling
    joulesPerOp: 2.2e-15,
    magicCapable: false,
    thermalSensitivity: 0.45,
  },
  {
    class: "NX-1",
    name: "Neuromorphic / event-driven cores",
    kind: "neuro",
    tflops: 96,
    memGB: 64,
    memBW: 1.1,
    tdp: 180,
    baseRate: 4.1,
    lifeHours: 70080,
    joulesPerOp: 4.0e-17,
    magicCapable: false,
    thermalSensitivity: 0.3,
  },
  {
    class: "W33-L1",
    name: "Photonic substrate leaf / W(3,3) cell",
    kind: "photonic",
    tflops: 210,          // classical-equivalent; the point is the magic sector
    memGB: 8,             // [[66,8,3]]_3 protected memory, not DRAM
    memBW: 0.4,
    tdp: 240,             // room temperature, no cryostat
    baseRate: 74.0,       // scarce: it is the only thing that serves t > 0
    lifeHours: 96360,     // ~11 years; optics do not wear like silicon
    joulesPerOp: 3.1e-18,
    magicCapable: true,
    thermalSensitivity: 0.2,
  },
];

// ----------------------------------------------------------------------
// Workload classes. A buyer bids for a CLASS, not a machine -- and the
// exchange scores every node's genome against the class it was bid for.
// `magicBudget` is the number of non-Clifford gates the class needs;
// anything above zero can only clear against a magic-capable node and
// is priced at 9^t.
// ----------------------------------------------------------------------
const WORKLOADS = [
  { id: "llm-train", name: "LLM pretraining", magicBudget: 0, memWeight: 0.9, bwWeight: 1.0, burstiness: 0.15, geneEmphasis: ["throughput", "memoryBandwidth", "convergenceRate"] },
  { id: "llm-infer", name: "LLM inference", magicBudget: 0, memWeight: 0.7, bwWeight: 0.8, burstiness: 0.85, geneEmphasis: ["throughput", "faultResilience"] },
  { id: "finetune", name: "Fine-tuning / RLHF", magicBudget: 0, memWeight: 0.6, bwWeight: 0.6, burstiness: 0.4, geneEmphasis: ["convergenceRate", "throughput"] },
  { id: "render", name: "Offline render", magicBudget: 0, memWeight: 0.4, bwWeight: 0.3, burstiness: 0.55, geneEmphasis: ["throughput", "thermalStability"] },
  { id: "genomics", name: "Genomics / alignment", magicBudget: 0, memWeight: 0.8, bwWeight: 0.5, burstiness: 0.3, geneEmphasis: ["memoryBandwidth", "faultResilience"] },
  { id: "cfd", name: "CFD / FEA", magicBudget: 0, memWeight: 0.7, bwWeight: 0.9, burstiness: 0.2, geneEmphasis: ["memoryBandwidth", "thermalStability"] },
  { id: "risk", name: "Monte Carlo risk", magicBudget: 0, memWeight: 0.3, bwWeight: 0.2, burstiness: 0.7, geneEmphasis: ["throughput", "convergenceRate"] },
  { id: "qchem", name: "Quantum chemistry", magicBudget: 6, memWeight: 0.5, bwWeight: 0.4, burstiness: 0.25, geneEmphasis: ["convergenceRate", "faultResilience"] },
  { id: "qopt", name: "Quantum optimisation", magicBudget: 9, memWeight: 0.4, bwWeight: 0.3, burstiness: 0.35, geneEmphasis: ["faultResilience", "convergenceRate"] },
  { id: "qsim", name: "Lattice / QCD simulation", magicBudget: 12, memWeight: 0.6, bwWeight: 0.7, burstiness: 0.1, geneEmphasis: ["throughput", "memoryBandwidth"] },
];

const INSTRUMENTS = [
  {
    id: "spot",
    name: "Spot node-hour",
    tenor: "immediate",
    blurb: "Buy the next hour on a named node at the live clearing price. Settles on the receipt.",
  },
  {
    id: "forward",
    name: "Forward block",
    tenor: "1-90 days",
    blurb: "Lock a price now for node-hours delivered in a future window. This is how you hedge a heat dome on ERCOT.",
  },
  {
    id: "option",
    name: "Burst option",
    tenor: "1-30 days",
    blurb: "Pay a premium for the right, not the obligation, to seize N nodes inside a window. Priced off utilisation vol.",
  },
  {
    id: "lease",
    name: "Genome lease",
    tenor: "7-365 days",
    blurb: "You are not renting FLOPs, you are renting a TRAINED core -- a node whose AI core already carries priors for your workload class. Priced on fitness, not silicon.",
  },
  {
    id: "supply",
    name: "Supply offer",
    tenor: "open",
    blurb: "Lend your own idle nodes into the pool. The exchange prices them, routes work to them, and pays you the clear less the maintenance reserve.",
  },
];

const OPERATORS = [
  "Meridian Compute", "Fjord Systems", "Basin Grid Labs", "Halcyon DC",
  "Northwind Fabric", "Kestrel Infrastructure", "Orbital Substrate",
  "Tessellate Cloud", "Ardent Silicon", "Vantablack Networks",
];

// Publish explicitly rather than relying on top-level `const` reaching the
// global lexical scope. It does in a browser <script>, but not under an
// indirect eval, and the test harness uses one.
(function (root) {
  root.DATACENTERS = DATACENTERS;
  root.HARDWARE = HARDWARE;
  root.WORKLOADS = WORKLOADS;
  root.INSTRUMENTS = INSTRUMENTS;
  root.OPERATORS = OPERATORS;
})(typeof window !== "undefined" ? window : globalThis);

if (typeof module !== "undefined" && module.exports) {
  module.exports = { DATACENTERS, HARDWARE, WORKLOADS, INSTRUMENTS, OPERATORS };
}
