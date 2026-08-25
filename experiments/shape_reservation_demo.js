#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const S = require("../js/substrate.js");
const R = require("../reservations/shape-reservation.js");

function run() {
  const points = [...S.LINES[0]];
  const ledger = new R.ShapeReservationLedger(points.map((point) => ({
    point,
    nodeId: `DEMO-NODE-${String(point).padStart(2, "0")}`,
    vcpus: 4,
    memoryMiB: 2048,
    pricePerNodeSecond: 0.001 + point / 1e6,
  })));
  const contract = R.createContract({
    reservationId: "RSV-W33-LINE-DEMO",
    owner: "holotrade-demo",
    nonce: "shape-demo-seed-v1",
    artifactDigest: `sha256:${"42".repeat(32)}`,
    points,
    requestedSeconds: 10,
    resources: { perNode: { vcpus: 2, memoryMiB: 512 } },
    topology: {
      connected: true,
      isotropicLine: true,
      maxDiameter: 1,
      minDegree: 3,
      survivesNodeFailures: 2,
    },
    failurePolicy: { mode: "minimum-survivors", minSurvivors: 3 },
    maxPricePerNodeSecond: 0.01,
    validFrom: 0,
    validUntil: 60,
  });
  const prepared = ledger.prepare(contract, 1);
  const committed = ledger.commit(contract.reservationId, 2);
  const started = ledger.start(contract.reservationId, 3);
  const failedPoint = points[0];
  ledger.meter(contract.reservationId, 4, { [failedPoint]: false });
  const terminal = ledger.meter(contract.reservationId, 6, { [failedPoint]: false });
  const packetBody = {
    schema: "holotrade.shape-reservation-demo.v1",
    evidenceScope: "EXACT_TOPOLOGY_PLUS_DETERMINISTIC_CONTROL_PLANE_REGRESSION",
    physicalExecutionClaimed: false,
    contract,
    phases: {
      prepare: { ok: prepared.ok, digest: prepared.certificate.digest },
      commit: { ok: committed.ok },
      start: { ok: started.ok },
    },
    injectedFailure: { point: failedPoint, atSecond: 0 },
    receipt: terminal.receipt,
  };
  return { ...packetBody, packetDigest: R.sha256(packetBody) };
}

if (require.main === module) {
  const packet = run();
  if (process.argv.includes("--write")) {
    const target = path.resolve(__dirname, "../data/shape_reservation_demo.json");
    fs.writeFileSync(target, `${JSON.stringify(packet, null, 2)}\n`);
    console.log(target);
  } else {
    console.log(JSON.stringify(packet, null, 2));
  }
}

module.exports = { run };
