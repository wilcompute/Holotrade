#!/usr/bin/env node
"use strict";

const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const { runGap } = require("../scripts/run-gap.js");

const ROOT = path.resolve(__dirname, "..");
const GAP = path.resolve(__dirname, "e8_unitary_orientation_rollback_probe.g");
const OUT = path.resolve(ROOT, "data/e8_unitary_orientation_rollback_probe.json");

function canonical(value) {
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.keys(value).sort().map((key) =>
      `${JSON.stringify(key)}:${canonical(value[key])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

function digest(value) {
  return crypto.createHash("sha256").update(canonical(value)).digest("hex");
}

function execute() {
  const run = runGap(GAP, { cwd: ROOT, quiet: true });
  if (!run.ok || !run.stdout.includes("ALL_ORIENTATION_ROLLBACK_CHECKS_PASS")) {
    throw new Error(`GAP orientation witness failed: ${run.stderr || run.stdout}`);
  }
  return run.stdout;
}

function line(stdout, prefix) {
  const found = stdout.split(/\r?\n/).find((row) => row.startsWith(`${prefix}|`));
  if (!found) throw new Error(`missing GAP row ${prefix}`);
  return found.replace(/\s+/g, "");
}

function ints(text) {
  return [...text.matchAll(/-?\d+/g)].map((match) => Number(match[0]));
}

function parse(stdout) {
  const extension = line(stdout, "ORIENTATION_EXTENSION").match(
    /^ORIENTATION_EXTENSION\|lineAut=(\d+)\|maxima=(\d+)\|spreadStabilizer=(\d+)\|inducedHoleGroup=(\d+)\|holeAut=(\d+)\|index=(\d+)\|normal=(\d+)$/);
  const state = line(stdout, "STATE_ACTION").match(
    /^STATE_ACTION\|spreadHoleOrbits=\[([^\]]+)\]\|spreadSuborbits=\[([^\]]+)\]\|fullSuborbits=\[([^\]]+)\]$/);
  const maxima = line(stdout, "MAXIMUM_SPREAD_ACTION").match(
    /^MAXIMUM_SPREAD_ACTION\|fixedByStabilizer=(\d+)\|sameHoleMaxima=(\d+)\|sharedLines=(\d+)\|coveredSetsEqual=(\d+)\|normalizer=(\d+)\|orientationImage=C2\|kernel=(\d+)\|outerSwaps=(\d+)\|outerExtends=(\d+)$/);
  const partner = line(stdout, "GLOBAL_PARTNER_INVOLUTION").match(
    /^GLOBAL_PARTNER_INVOLUTION\|states=(\d+)\|fibres=(\d+)\|fibreSizes=\[([^\]]+)\]\|sharedLines=\[([^\]]+)\]\|moved=(\d+)\|commutesWithAmbient=(\d+)\|insideAmbient=(\d+)\|equivariantCentralizerOrder=(\d+)$/);
  const quotient = line(stdout, "QUOTIENT_BIT");
  const orbitals = line(stdout, "DIRECTED_ORBITALS").match(
    /^DIRECTED_ORBITALS\|count=(\d+)\|degrees=\[([^\]]+)\]\|adjacent=\[([^\]]+)\]\|outerAction=\[([^\]]+)\]$/);
  const rollback = line(stdout, "ROLLBACK_NO_GO").match(
    /^ROLLBACK_NO_GO\|outerInvolutions=(\d+)\|KConjugacyOrbits=\[([^\]]+)\]\|profiles=(.+)\|centralizer=(\d+)\|canonicalOuterInvolution=(\d+)$/);
  if (![extension, state, maxima, partner, orbitals, rollback].every(Boolean)) {
    throw new Error("invalid GAP orientation output");
  }
  if (!quotient.includes("quotient=C2|kernel=11520|fullAbelianization=[2,2]|indexTwoNormals=3")) {
    throw new Error("unexpected index-two quotient profile");
  }

  const outerClasses = [
    { classSize: 180, fixedHoles: 8, transpositions: 56 },
    { classSize: 60, fixedHoles: 12, transpositions: 54 },
    { classSize: 6, fixedHoles: 40, transpositions: 40 },
    { classSize: 120, fixedHoles: 12, transpositions: 54 },
    { classSize: 10, fixedHoles: 0, transpositions: 60 },
  ];
  if (ints(rollback[2]).join(",") !== outerClasses.map((row) => row.classSize).join(",")) {
    throw new Error("outer involution class sizes changed");
  }

  const extensionValues = extension.slice(1).map(Number);
  const stateValues = [ints(state[1]), ints(state[2]), ints(state[3])];
  const maximaValues = maxima.slice(1).map(Number);
  const partnerValues = [Number(partner[1]), Number(partner[2]), ints(partner[3]),
    ints(partner[4]), Number(partner[5]), Number(partner[6]), Number(partner[7]), Number(partner[8])];
  const orbitalDegrees = ints(orbitals[2]);
  const orbitalAdjacency = orbitals[3].split(",").map((value) => value === "true");
  const outerAction = ints(orbitals[4]);
  if (canonical(extensionValues) !== canonical([26127360, 2268, 11520, 11520, 23040, 2, 1]) ||
      canonical(stateValues) !== canonical([[120], [1, 48, 48, 16, 4, 3], [1, 48, 48, 16, 4, 3]]) ||
      canonical(maximaValues) !== canonical([2, 2, 0, 1, 23040, 11520, 1, 1]) ||
      canonical(partnerValues) !== canonical([2268, 1134, [2], [0], 2268, 1, 0, 2]) ||
      canonical([Number(orbitals[1]), orbitalDegrees, orbitalAdjacency, outerAction]) !==
        canonical([6, [1, 48, 48, 16, 4, 3], [false, false, false, true, true, false], [1, 2, 3, 4, 5, 6]]) ||
      Number(rollback[1]) !== 376 || Number(rollback[4]) !== 1 || Number(rollback[5]) !== 0) {
    throw new Error("orientation invariant mismatch");
  }

  const body = {
    schema: "holotrade.e8-unitary-orientation-rollback-probe.v1",
    evidenceClass: "EXACT_GAP_FINITE_GEOMETRY_NO_GO",
    carrier: {
      holes: 120,
      ambientLineGraphAutomorphismOrder: 26127360,
      spreadStabilizerOrder: 11520,
      inducedHoleGroup: "2^4:S6",
      fullHoleAutomorphismGroup: "2^5:S6",
      fullHoleAutomorphismOrder: 23040,
      index: 2,
      subgroupNormal: true,
    },
    orientationCharacter: {
      quotient: "C2",
      kernelOrder: 11520,
      relativeToEmbeddedSpreadStabilizer: true,
      intrinsicToUnmarkedHoleGraph: false,
      reason: "the full hole group has abelianization C2 x C2 and three distinct index-two normal subgroups",
    },
    maximumSpreadFibre: {
      maximumSpreads: 2268,
      coveredPointSets: 1134,
      fibreSize: 2,
      pairedSpreadsShareLines: 0,
      partnerInvolutionMovesEverySpread: true,
      partnerInvolutionCommutesWithAmbientAction: true,
      partnerInvolutionInsideAmbientAction: false,
      canonicalUnlabelledPairing: true,
      canonicalZeroOneLabelling: false,
    },
    holeOrbitals: {
      subdegrees: orbitalDegrees,
      adjacentOrbitals: orbitalAdjacency,
      unchangedByOuterExtension: true,
      meaning: "the orientation quotient is invisible to the unmarked hole adjacency relation",
    },
    rollback: {
      outerInvolutions: 376,
      conjugacyClassesUnderSpreadGroup: outerClasses,
      holeActionCentralizerOrder: 1,
      canonicalOuterInvolution: false,
      canonicalRollbackOperation: false,
      relativeRollbackRequires: "an explicitly selected and attested outer involution class plus representative",
    },
    theorem:
      "The index-two extension canonically supplies a relative orientation character and an unlabelled partner pairing of maximum spreads, but neither a canonical 0/1 orientation label nor a canonical rollback involution on the 120 holes.",
    evidenceBoundary:
      "Exact abstract group and finite-geometry computation. No outer involution is promoted to a scheduler rollback command; runtime use requires a separately attested representative and policy.",
  };
  return { ...body, sha256: digest(body) };
}

function run() { return parse(execute()); }

if (require.main === module) {
  const result = run();
  if (process.argv.includes("--write")) {
    fs.writeFileSync(OUT, `${JSON.stringify(result, null, 2)}\n`);
    console.log(path.relative(process.cwd(), OUT));
  }
  console.log(JSON.stringify({
    sha256: result.sha256,
    quotient: result.orientationCharacter.quotient,
    canonicalRollback: result.rollback.canonicalRollbackOperation,
    outerInvolutions: result.rollback.outerInvolutions,
  }, null, 2));
}

module.exports = { canonical, digest, execute, parse, run };
