"use strict";

// Cache-aware economic overlay for continuation-native scheduling.
//
// A compiled Steinberg control artifact is process-independent, but semantic
// execution is not.  This overlay calls the ordinary scheduler first, then adds
// a separate control compilation/setup quote keyed by the exact W33 artifact
// identity.  Cache hits may reduce only that control quote; they never reduce
// computeUSD, retainedUSD, transferUSD, retainedUnionDeltaBytes, receipt count,
// generation span, or continuation authority.

const S = require("./w33-continuation-scheduler.js");

const SCHEMA = "holotrade.w33-cache-aware-accelerator-quote.v1";

function finiteNonnegative(value, name) {
  const n = Number(value);
  if (!Number.isFinite(n) || n < 0) throw new RangeError(`${name} must be finite nonnegative`);
  return n;
}

function controlArtifactBody(cert) {
  if (!cert) return null;
  return {
    schema: "w33.steinberg-control-artifact.v1",
    machine_type: cert.machineType,
    symplectic_frame_digest: cert.symplecticFrameDigest,
    basis_digest: cert.steinbergBasisDigest,
    action_table_digest: cert.actionTableDigest,
    steinberg_action_digest: cert.steinbergActionDigest,
    executable_time_order: cert.executableTimeOrder,
    calibration_epoch: cert.calibrationEpoch,
  };
}

function controlArtifactId(cert) {
  const body = controlArtifactBody(cert);
  return body == null ? null : S.sha256(body);
}

function cacheEntry(candidate, artifactId, cert) {
  if (!artifactId) return null;
  const table = candidate && candidate.controlArtifactCache;
  if (!table || typeof table !== "object") return null;
  const row = table[artifactId];
  if (!row || row.present !== true) return null;
  if (row.calibrationEpoch !== cert.calibrationEpoch) return null;
  return row;
}

function quoteControl(candidate, artifactId, cert, economics = {}) {
  if (!artifactId) return Object.freeze({ cacheHit: false, controlCompilationUSD: 0, controlSetupUSD: 0, controlTotalUSD: 0 });
  const hit = cacheEntry(candidate, artifactId, cert);
  const compileUSD = finiteNonnegative(
    candidate.controlCompileUSDByArtifact?.[artifactId] ?? candidate.controlCompileUSD ?? economics.defaultControlCompileUSD ?? 0,
    "control compilation USD",
  );
  const coldSetupUSD = finiteNonnegative(
    candidate.controlSetupUSDByArtifact?.[artifactId] ?? candidate.controlSetupUSD ?? economics.defaultControlSetupUSD ?? 0,
    "control setup USD",
  );
  const hotSetupUSD = finiteNonnegative(
    candidate.cachedControlSetupUSDByArtifact?.[artifactId] ?? candidate.cachedControlSetupUSD ?? economics.defaultCachedControlSetupUSD ?? 0,
    "cached control setup USD",
  );
  const controlCompilationUSD = hit ? 0 : compileUSD;
  const controlSetupUSD = hit ? hotSetupUSD : coldSetupUSD;
  return Object.freeze({
    cacheHit: Boolean(hit),
    cacheEntryDigest: hit && hit.compiledArtifactDigest ? hit.compiledArtifactDigest : null,
    controlCompilationUSD,
    controlSetupUSD,
    controlTotalUSD: controlCompilationUSD + controlSetupUSD,
  });
}

function quoteCacheAware(candidates, rawRequest, basePolicy = {}, economics = {}) {
  const ranked = S.rankContinuations(candidates, rawRequest, basePolicy);
  const cert = ranked.request.acceleratorCertificate;
  const artifactId = controlArtifactId(cert);
  const byId = new Map((candidates || []).map((c) => [String(c.id), c]));
  const rows = ranked.eligible.map((dispatch) => {
    const candidate = byId.get(dispatch.workerId);
    const control = quoteControl(candidate, artifactId, cert, economics);
    const semanticUSD = dispatch.price.totalUSD;
    const totalUSD = semanticUSD + control.controlTotalUSD;
    const semanticWork = cert == null ? null : Object.freeze({
      processId: ranked.request.processId,
      parentContinuationRoot: ranked.request.continuationRoot,
      childContinuationRoot: cert.childContinuationRoot,
      generationBefore: cert.generationBefore,
      generationAfter: cert.generationAfter,
      generationSpan: cert.generationAfter - cert.generationBefore,
      receiptCount: cert.subreceiptIds.length,
      receiptChainDigest: cert.receiptChainDigest,
      continuationChainDigest: cert.continuationChainDigest,
    });
    const body = {
      schema: SCHEMA,
      workerId: dispatch.workerId,
      dispatchDigest: dispatch.dispatchDigest,
      acceleratorCertificateDigest: dispatch.acceleratorCertificateDigest || null,
      controlArtifactId: artifactId,
      cacheHit: control.cacheHit,
      semanticComputeUSD: dispatch.price.computeUSD,
      retainedStateUSD: dispatch.price.retainedUSD,
      transferUSD: dispatch.price.transferUSD,
      genericStartupUSD: dispatch.price.startupUSD,
      semanticAndStateTotalUSD: semanticUSD,
      controlCompilationUSD: control.controlCompilationUSD,
      controlSetupUSD: control.controlSetupUSD,
      controlTotalUSD: control.controlTotalUSD,
      totalUSD,
      retainedUnionDeltaBytes: dispatch.retainedUnionDeltaBytes,
      semanticWork,
    };
    return Object.freeze({ ...body, quoteDigest: S.sha256(body), dispatch });
  });
  rows.sort((a, b) => a.totalUSD - b.totalUSD || a.semanticAndStateTotalUSD - b.semanticAndStateTotalUSD || a.workerId.localeCompare(b.workerId));
  return Object.freeze({
    schema: "holotrade.w33-cache-aware-ranking.v1",
    request: ranked.request,
    controlArtifactId: artifactId,
    eligible: Object.freeze(rows),
    rejected: ranked.rejected,
    winner: rows.length ? rows[0] : null,
  });
}

module.exports = { SCHEMA, controlArtifactBody, controlArtifactId, cacheEntry, quoteControl, quoteCacheAware };
