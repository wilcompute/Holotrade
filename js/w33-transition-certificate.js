// ======================================================================
// HOLOTRADE W33/UOR TRANSITION CERTIFICATE
//
// Real SHA-256 content addressing + exact W(3,3) route witnesses for one
// settled Projection -> Execution -> Emission transition.
//
// The shape intentionally mirrors W33-Theory's offline Holonet/UOR bridge:
//   element -> transport_partition -> proof -> trace -> certificate
//
// This is NOT native UOR certification, a signature, remote/hardware
// attestation, transparency proof, or evidence of physical W(3,3) transport.
// ======================================================================

(function (root) {
  "use strict";

  const S = root.Substrate || (typeof require !== "undefined" ? require("./substrate.js") : null);
  const E = root.HolotradeEvidence || (typeof require !== "undefined" ? require("./evidence.js") : null);
  const U = root.HolotradeUOR || (typeof require !== "undefined" ? require("./uor.js") : null);
  const P = root.HolotradeProjection || (typeof require !== "undefined" ? require("./projection.js") : null);
  let crypto = null;
  if (typeof require !== "undefined") {
    try { crypto = require("node:crypto"); } catch (_) { crypto = null; }
  }
  if (!S || !E || !U || !P) throw new Error("W33 transition certificate dependencies missing");

  const SCHEMA = "holotrade.w33_uor_transition_certificate.v1";
  const CERTIFICATE_KIND = "HoloTradeW33TransitionCertificate";
  const PROOF_KIND = "HoloTradeW33TransitionProof";
  const TRACE_KIND = "HoloTradeProjectionComputationTrace";

  function canonicalBytes(value) {
    if (typeof Buffer === "undefined") throw new Error("transition certificates currently require Node.js");
    if (Buffer.isBuffer(value)) return value;
    if (value instanceof Uint8Array) return Buffer.from(value);
    const text = typeof value === "string" ? value : E.canonicalJson(value);
    return Buffer.from(text, "utf8");
  }

  function sha256Hex(value) {
    if (!crypto) throw new Error("transition certificates require node:crypto");
    return crypto.createHash("sha256").update(canonicalBytes(value)).digest("hex");
  }

  function sha256Digest(value) {
    return `sha256:${sha256Hex(value)}`;
  }

  function pointKey(point) {
    if (!Number.isInteger(point) || point < 0 || point >= S.POINTS.length) {
      throw new RangeError(`invalid W(3,3) point: ${String(point)}`);
    }
    return S.POINTS[point].key;
  }

  function addressOf(resource) {
    if (resource && resource.address instanceof U.UORAddress) return resource.address;
    if (resource && typeof resource.address === "string") return U.UORAddress.fromHex(resource.address);
    throw new TypeError("resource is missing a canonical UOR address");
  }

  function routeStep({ id, role, direction, fromPoint, toPoint }) {
    const route = S.route(fromPoint, toPoint);
    return Object.freeze({
      id,
      role,
      direction,
      src: pointKey(fromPoint),
      dst: pointKey(toPoint),
      srcPoint: fromPoint,
      dstPoint: toPoint,
      path: route.hops.map(pointKey),
      pathPoints: [...route.hops],
      hops: route.distance,
      relayAlternates: route.alternates.length,
      relation: route.distance === 0 ? "identity" : route.distance === 1 ? "intersecting" : "disjoint",
      symplectic: S.symplecticForm(S.POINTS[fromPoint].vec, S.POINTS[toPoint].vec),
    });
  }

  function transitionSteps(projection, emission, executionPoint) {
    const inputs = projection.inputs.map((input) => routeStep({
      id: input.id,
      role: input.role,
      direction: "input-to-execution",
      fromPoint: addressOf(input).point,
      toPoint: executionPoint,
    }));
    const output = routeStep({
      id: emission.output.id,
      role: emission.output.role || "output",
      direction: "execution-to-output",
      fromPoint: executionPoint,
      toPoint: U.UORAddress.fromHex(emission.output.address).point,
    });
    return [...inputs, output];
  }

  function partition(steps) {
    const buckets = { units: [], irreducibles: [], reducibles: [], exterior: [] };
    for (const step of steps) {
      if (step.hops === 0) buckets.units.push(step);
      else if (step.hops === 1) buckets.irreducibles.push(step);
      else if (step.hops === 2 && step.relayAlternates === S.CONST.mu - 1) buckets.reducibles.push(step);
      else buckets.exterior.push(step);
    }
    const components = {};
    for (const [name, rows] of Object.entries(buckets)) {
      components[name] = {
        cardinality: rows.length,
        density: steps.length ? `${rows.length}/${steps.length}` : "0/0",
        transition_ids: rows.map((row) => `${row.direction}:${row.id}`),
      };
    }
    const cardinality = Object.values(buckets).reduce((sum, rows) => sum + rows.length, 0);
    return {
      kind: "HoloTradeW33TransportPartition",
      uor_native_boundary:
        "Transport analog of UOR partition/Partition over exact W(3,3) route classes; not a native UOR ring partition.",
      components,
      cardinality_sum: cardinality,
      complete: cardinality === steps.length && buckets.exterior.length === 0,
    };
  }

  function historicalDecision(plan) {
    const d = plan.evidenceDecision;
    if (!d || typeof d !== "object") {
      return {
        present: false,
        ok: (plan.evidencePolicy || E.POLICY.DEMO) === E.POLICY.DEMO,
        digest: null,
        policy: plan.evidencePolicy || E.POLICY.DEMO,
        refs: [...(plan.evidenceRefs || [])],
      };
    }
    return {
      present: true,
      ok: d.ok === true,
      digest: d.digest || null,
      policy: d.policy || plan.evidencePolicy || E.POLICY.DEMO,
      refs: [...(d.refs || plan.evidenceRefs || [])],
    };
  }

  function currentDecision(executionEngine, plan) {
    if (!executionEngine || typeof executionEngine.evidenceDecision !== "function") {
      return { available: false, ok: null, digest: null, blockers: [] };
    }
    const d = executionEngine.evidenceDecision(plan);
    return {
      available: true,
      ok: d.ok,
      digest: d.digest,
      policy: d.policy,
      refs: d.refs,
      blockers: d.blockers,
      warnings: d.warnings,
      resolved: d.resolved,
    };
  }

  function emissionBinds(projection, plan, receipt, emission) {
    return !!(emission && emission.projection && emission.execution && emission.output &&
      emission.projection.id === projection.id &&
      emission.projection.digest === projection.digest &&
      emission.execution.planId === plan.id &&
      emission.execution.planDigest === plan.digest &&
      emission.execution.receiptId === receipt.id &&
      emission.execution.outcome === "settled");
  }

  function buildCertificate({ projection, plan, receipt, emission, executionEngine, projectionEngine } = {}) {
    if (!projection || !plan || !receipt || !emission) {
      throw new TypeError("projection, plan, receipt, and emission are required");
    }
    const node = executionEngine && executionEngine.fleet && typeof executionEngine.fleet.get === "function"
      ? executionEngine.fleet.get(receipt.nodeId)
      : null;
    if (!node || !Number.isInteger(node.cellPoint)) {
      throw new Error("certificate requires the settled execution node with a W(3,3) cellPoint");
    }

    const steps = transitionSteps(projection, emission, node.cellPoint);
    const transport = partition(steps);
    const historical = historicalDecision(plan);
    const current = currentDecision(executionEngine, plan);
    const projectionBinding = projectionEngine && typeof projectionEngine.verifyBinding === "function"
      ? projectionEngine.verifyBinding(projection, plan)
      : { ok: true, reason: "projection engine not supplied; direct emission binding only" };

    const emissionBytes = canonicalBytes(emission);
    const emissionSha = sha256Hex(emissionBytes);
    const routeChecks = steps.map((step) => ({
      transition: `${step.direction}:${step.id}`,
      hops: step.hops,
      ok: step.hops >= 0 && step.hops <= S.CONST.cellDiameter &&
        (step.hops !== 2 || step.relayAlternates === S.CONST.mu - 1),
    }));
    const proofChecks = {
      emission_content_address_roundtrip: emissionSha === sha256Hex(emissionBytes),
      receipt_is_settled: receipt.outcome === "settled",
      plan_status_is_settled: plan.status === "settled",
      receipt_binds_plan: receipt.planId === plan.id && receipt.planDigest === plan.digest,
      emission_binds_transition: emissionBinds(projection, plan, receipt, emission),
      projection_binding_valid: projectionBinding.ok === true,
      historical_evidence_admission: historical.ok === true,
      evidence_envelope_present: !!(receipt.evidenceEnvelope && receipt.evidenceDigest),
      transport_partition_complete: transport.complete,
      diameter_two_routes: routeChecks.every((row) => row.ok),
    };
    const pass = Object.values(proofChecks).every(Boolean);

    const element = {
      digestAlgorithm: "sha256",
      digest: `sha256:${emissionSha}`,
      length: emissionBytes.length,
      canonicalBytesEncoding: "canonical-json/utf8/sorted-object-keys",
      canonicalBytesSha256: emissionSha,
    };
    const trace = {
      kind: TRACE_KIND,
      projection: { id: projection.id, digest: projection.digest },
      execution: {
        planId: plan.id,
        planDigest: plan.digest,
        receiptId: receipt.id,
        receiptEvidenceDigest: receipt.evidenceDigest || null,
        nodeId: receipt.nodeId,
        executionPoint: node.cellPoint,
        executionPointKey: pointKey(node.cellPoint),
        nodeSeconds: receipt.nodeSeconds,
        outcome: receipt.outcome,
      },
      transition_steps: steps,
      observables: {
        transition_count: steps.length,
        max_hops: Math.max(...steps.map((step) => step.hops), 0),
        two_hop_routes: steps.filter((step) => step.hops === 2).length,
        direct_routes: steps.filter((step) => step.hops === 1).length,
        identity_routes: steps.filter((step) => step.hops === 0).length,
      },
    };
    const proof = {
      kind: PROOF_KIND,
      checks: proofChecks,
      route_checks: routeChecks,
      historical_evidence_admission: historical,
      current_evidence_admissibility_at_issue: current,
      correction_semantics:
        "The settled transition and its SHA-256 element remain historical facts. Current admissibility is a snapshot and may later become false under a new evidence-ledger state without modifying this certificate.",
      projection_binding: projectionBinding,
    };
    const certificate = {
      valid: pass,
      attests: [
        "SHA-256 content address of the canonical HoloTrade emission record",
        "settled receipt and plan/emission binding",
        "historical evidence admission captured at execution time",
        "exact W(3,3) diameter-2 route witnesses for input/execution/output transition points",
      ],
      currentAdmissibilityAtIssue: current.available ? current.ok : null,
      boundary:
        "Offline HoloTrade/W33 bridge certificate. It mirrors the W33-Theory Holonet/UOR certificate anatomy and uses real SHA-256 content addressing, but it is not issued by uor.foundation, is not a digital signature or remote attestation, and does not prove physical W(3,3) packet transport.",
    };
    const body = {
      schema: SCHEMA,
      kind: CERTIFICATE_KIND,
      status: pass ? "PASS" : "FAIL",
      source: {
        projectionId: projection.id,
        planId: plan.id,
        receiptId: receipt.id,
        emissionDigest: emission.digest,
      },
      uor_alignment: {
        framework: "Universal Object Reference",
        apiVersionObservedByW33Bridge: "0.3.1",
        addressing: "SHA-256 content address over canonical emission bytes",
        proof: "proof/Proof-style named checks",
        trace: "trace/ComputationTrace-style transition sequence",
        certificate: "cert/Certificate-style offline bridge certificate",
        nativeCertification: false,
      },
      element,
      transport_partition: transport,
      proof,
      trace,
      certificate,
    };
    return Object.freeze({ ...body, certificateDigest: sha256Digest(body) });
  }

  function reevaluateEvidence(cert, executionEngine, plan) {
    if (!cert || cert.schema !== SCHEMA) throw new TypeError("valid HoloTrade W33 transition certificate required");
    const current = currentDecision(executionEngine, plan);
    const result = {
      schema: "holotrade.w33_uor_transition_admissibility.v1",
      certificateDigest: cert.certificateDigest,
      elementDigest: cert.element.digest,
      historicalAdmission: cert.proof.historical_evidence_admission,
      current,
      reusableNow: cert.status === "PASS" && current.available && current.ok === true,
    };
    return Object.freeze({ ...result, digest: sha256Digest(result) });
  }

  function validateShape(cert) {
    const violations = [];
    const need = (obj, key, path) => {
      if (!obj || typeof obj !== "object" || !Object.hasOwn(obj, key)) violations.push(`${path}.${key} missing`);
    };
    for (const key of ["schema", "status", "element", "transport_partition", "proof", "trace", "certificate"])
      need(cert, key, "certificate");
    if (cert.schema !== SCHEMA) violations.push("certificate.schema unsupported");
    if (cert.status !== "PASS") violations.push("certificate.status is not PASS");
    if (!cert.element || cert.element.digestAlgorithm !== "sha256" ||
        !/^sha256:[0-9a-f]{64}$/.test(cert.element.digest || "")) {
      violations.push("certificate.element digest is not canonical SHA-256");
    }
    if (!cert.transport_partition || cert.transport_partition.complete !== true) {
      violations.push("certificate.transport_partition is incomplete");
    }
    if (!cert.proof || cert.proof.kind !== PROOF_KIND ||
        !cert.proof.checks || !Object.values(cert.proof.checks).every(Boolean)) {
      violations.push("certificate.proof checks do not all pass");
    }
    if (!cert.trace || cert.trace.kind !== TRACE_KIND || !Array.isArray(cert.trace.transition_steps)) {
      violations.push("certificate.trace malformed");
    }
    if (!cert.certificate || cert.certificate.valid !== true) violations.push("certificate validity flag is false");
    const body = { ...cert };
    const expected = body.certificateDigest;
    delete body.certificateDigest;
    if (expected !== sha256Digest(body)) violations.push("certificateDigest mismatch");
    return { conforms: violations.length === 0, violations };
  }

  const API = {
    SCHEMA,
    CERTIFICATE_KIND,
    PROOF_KIND,
    TRACE_KIND,
    sha256Hex,
    sha256Digest,
    buildCertificate,
    reevaluateEvidence,
    validateShape,
  };
  root.HolotradeW33TransitionCertificate = API;
  if (typeof module !== "undefined" && module.exports) module.exports = API;
})(typeof window !== "undefined" ? window : globalThis);
