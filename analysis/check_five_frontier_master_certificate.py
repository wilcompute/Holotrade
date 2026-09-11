#!/usr/bin/env python3
"""Validate the frozen 2026-09-11 five-frontier synthesis against source certificates."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def load(name: str):
    return json.loads((ROOT / name).read_text())


def main():
    top = load("five_frontier_master_certificate_20260911.json")
    assert top["status"] == "PASS"

    r2 = load("octet_gauge_radius_two_all7_merged_certificate.json")
    assert r2["exceptionalCosetCount"] == 7
    assert r2["distinctRadiusTwoDisplacements"] == 4140
    assert r2["counterexampleFound"] is False
    assert r2["boundedNoTrapProvedOnAny"] is False
    assert r2["finalStatusHistogram"] == {"UNKNOWN": 7}
    assert all(row["lastIteration"]["bestRadiusTwo"] == row["certifiedGlobalDepth"] for row in r2["rows"])

    circ = load("octet_single_circuit_obstruction_certificate.json")
    assert circ["isGraverElement"] is True
    assert circ["insideRadiusTwo"] is False
    assert circ["radiusTwoIsUniversalGraverTestSet"] is False
    assert circ["circuit"]["supportSize"] == 18
    assert circ["circuit"]["l1"] == 20
    assert circ["circuit"]["linf"] == 2

    cross = load("octet_decoder_graver_direct_crosscheck.json")
    assert cross["graverObstruction"]["isGraverElement"] is True
    assert cross["directDecoderSearch"]["counterexampleFound"] is False
    assert cross["directDecoderSearch"]["finalStatusHistogram"] == {"UNKNOWN": 7}

    m36 = load("mass36_no_pencil_exhaustive_summary.json")
    assert m36["enumerationComplete"] is True
    assert m36["solverStatus"] == "OPTIMAL"
    assert m36["rawSolutionsFound"] == 586080
    assert m36["orbitCount"] == 55
    assert m36["integerDepthHistogram"] == {"3": 52, "4": 3}
    assert m36["deltaRealHistogram"] == {"3": 52, "4": 3}
    assert m36["depthAtLeastFiveOrbitCount"] == 0
    assert m36["strictSeparationOrbitCount"] == 0
    assert m36["unresolvedOrbitCount"] == 0

    hunts = load("mass36_hunt_exhaustive_crosscheck.json")
    assert hunts["allHuntOrbitsInExhaustiveCensus"] is True
    assert hunts["totalOptimizationTrials"] == 288
    assert hunts["huntDepth4CoverageCount"] == 2
    assert hunts["exhaustiveDepth4OrbitCount"] == 3
    assert hunts["huntDepth4CoverageFraction"] == "2/3"

    m8 = load("mass24_steinberg_full_m8_algebra_certificate.json")
    assert m8["steinbergDegree"] == 81
    assert m8["multiplicitySplit"] == [3, 5]
    assert m8["combinedMultiplicity"] == 8
    assert m8["combinedSteinbergIsotypicRank"] == 648
    assert m8["fullCommutantAlgebra"] == "M8(Q)"
    assert m8["fullCommutantDimension"] == 64
    assert m8["matrixUnitCount"] == 64
    assert m8["matrixUnitProductsChecked"] == 4096
    assert m8["automorphismStructure"]["fullQAlgebraAutomorphisms"] == "PGL8(Q) by Skolem-Noether for M8(Q)"

    # Cross-check the frozen synthesis mirrors the source values and, importantly,
    # does not conflate a failed universal Graver certificate with a decoder trap.
    f = top["frontiers"]
    assert f["radiusTwoDirectDecoder"]["counterexampleFound"] is False
    assert f["graverUniversality"]["insideRadiusTwo"] is False
    assert f["mass36NoPencil"]["orbitCount"] == 55
    assert f["mass36ExtremalHunts"]["huntDepth4CoverageFraction"] == "2/3"
    assert f["steinbergFullCommutant"]["fullCommutantAlgebra"] == "M8(Q)"

    print(json.dumps({
        "status": "PASS",
        "radiusTwoDirectSearch": "UNKNOWN x7, no trap",
        "graverUniversality": "DISPROVED by primitive circuit outside radius two",
        "mass36": "586080 solutions / 55 orbits / max depth 4 / no gap",
        "extremalHunts": "2 of 3 depth-4 orbits sampled",
        "steinbergCommutant": "M8(Q), multiplicity split 3+5"
    }, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
