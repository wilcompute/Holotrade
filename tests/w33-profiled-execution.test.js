const assert = require("node:assert/strict");
const test = require("node:test");
const path = require("node:path");

global.window = global;
const root = path.resolve(__dirname, "..");
const { ExecutionPlan } = require(path.join(root, "js/execution.js"));
const P = require(path.join(root, "js/w33-execution-profile.js"));
const X = require(path.join(root, "js/w33-profiled-execution.js"));

function plan() {
  return new ExecutionPlan({
    name: "w33-profiled",
    workloadId: "llm-train",
    requestedSeconds: 10,
    artifacts: [{ name: "img", digest: "sha256:demo" }],
  });
}

function fixture() {
  const nodes = [{ id: "n81" }, { id: "n64" }, { id: "alias" }, { id: "plain" }];
  const base = {
    place: () => nodes.map((node) => ({ node, score: 1 })),
    launch: (_plan, node) => ({ ok: true, vm: { id: `vm-${node.id}` }, node }),
  };
  const registry = new X.W33HostRegistry();
  registry.register("n81", P.MACHINE_TYPE.CIRCUIT_ST81);
  registry.register("n64", P.MACHINE_TYPE.PAIR_ST64);
  registry.register("alias", P.MACHINE_TYPE.CIRCUIT_ST81, {
    cliffordLift: "same-namespace",
    projectiveWeyl: "same-namespace",
  });
  return { nodes, engine: new X.ProfiledExecutionEngine(base, registry) };
}

test("scheduler placement filters to the exact construction-time carrier", () => {
  const p = plan();
  const { engine } = fixture();
  const profile = P.bind(p, P.MACHINE_TYPE.CIRCUIT_ST81);
  assert.deepEqual(engine.place(p, profile).map((x) => x.node.id), ["n81"]);
});

test("launch fails closed on untyped, wrong-carrier and namespace-alias hosts", () => {
  const p = plan();
  const { engine, nodes } = fixture();
  const profile = P.bind(p, P.MACHINE_TYPE.CIRCUIT_ST81);
  assert.equal(engine.launch(p, profile, nodes[3]).code, "W33_HOST_UNTYPED");
  assert.equal(engine.launch(p, profile, nodes[1]).code, "W33_MACHINE_TYPE_MISMATCH");
  assert.equal(engine.launch(p, profile, nodes[2]).code, "W33_NAMESPACE_ALIAS");
});

test("successful launch carries immutable W33 identity into the VM", () => {
  const p = plan();
  const { engine, nodes } = fixture();
  const profile = P.bind(p, P.MACHINE_TYPE.CIRCUIT_ST81);
  const r = engine.launch(p, profile, nodes[0]);
  assert.ok(r.ok);
  assert.equal(r.vm.w33ProfileDigest, profile.digest);
  assert.equal(r.vm.w33MachineType, P.MACHINE_TYPE.CIRCUIT_ST81);
  assert.equal(r.vm.w33LogicalDimension, 81);
  assert.notEqual(r.vm.w33SymmetryNamespaces.cliffordLift, r.vm.w33SymmetryNamespaces.projectiveWeyl);
});

test("GoMicroVM deployment commitment includes machine profile and changes across the fork", () => {
  const p = plan();
  const { engine } = fixture();
  const c81 = engine.compileGoMicroVM(p, P.bind(p, P.MACHINE_TYPE.CIRCUIT_ST81));
  const c64 = engine.compileGoMicroVM(p, P.bind(p, P.MACHINE_TYPE.PAIR_ST64));
  assert.equal(c81.w33.logicalDimension, 81);
  assert.equal(c64.w33.logicalDimension, 64);
  assert.equal(c81.w33.runtimeRetype, "FORBIDDEN");
  assert.notEqual(c81.deploymentDigest, c64.deploymentDigest);
  assert.notEqual(c81.w33.symmetryNamespaces.cliffordLift, c81.w33.symmetryNamespaces.projectiveWeyl);
});

test("plan tampering invalidates placement and deployment compilation", () => {
  const p = plan();
  const { engine } = fixture();
  const profile = P.bind(p, P.MACHINE_TYPE.CIRCUIT_ST81);
  p.requestedSeconds = 999;
  assert.equal(p.verify(), false);
  assert.deepEqual(engine.place(p, profile), []);
  assert.throws(() => engine.compileGoMicroVM(p, profile), /invalid W33 execution profile/);
});
