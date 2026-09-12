#!/usr/bin/env python3
"""Validate the frozen five-frontier depth-5 / decoder synthesis.

Zero-dependency cross-certificate audit.  This intentionally checks identities
that span independently generated certificates so later edits cannot silently
make the synthesis internally inconsistent.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name: str):
    p = HERE / name
    d = json.loads(p.read_text())
    assert d.get("status") == "PASS", (name, d.get("status"))
    return d


def main():
    syn = load("five_frontier_depth5_decoder_synthesis.json")
    mini = load("octet_circuit_library_minimization_certificate.json")
    hybrid = load("octet_hybrid_certified_decoder_minimal_summary.json")
    m40 = load("mass40_no_pencil_exhaustive_summary.json")
    m40s = load("mass40_depth5_structural_types_certificate.json")
    emb = load("mass24_steinberg_gram192_explicit_w33_embedding_certificate.json")
    sep = load("mass36_to_mass40_inheritance_separator_summary.json")
    prov = load("w33_certified_decoder_provenance_certificate.json")

    # Front 1: minimal runtime circuit library is the same identity everywhere.
    cd = mini["minimalLibraryDigest"]
    assert mini["orientationOrbitRelation"] == "same-orbit"
    assert mini["minimalPSpInvariantCircuitMoveCount"] == 1080
    assert hybrid["minimalPSpInvariantCircuitMoveCount"] == 1080
    assert hybrid["circuitLibraryDigest"] == cd
    assert hybrid["radiusTwoMoveCount"] == 4140
    assert hybrid["benchmarkCosetCount"] == 7
    assert hybrid["benchmarkStartCount"] == 37
    assert hybrid["benchmarkReachedCertifiedOptimum"] == 37
    assert hybrid["benchmarkStalled"] == 0
    assert hybrid["fallbackPathExercised"] is True
    assert hybrid["fallbackCircuitStepsUsed"] >= 2

    # Front 2: complete mass-40 theorem and structural split agree exactly.
    assert m40["enumerationComplete"] is True and m40["solverStatus"] == "OPTIMAL"
    assert m40["orbitCount"] == 30
    assert m40["integerDepthHistogram"] == {"4": 28, "5": 2}
    assert m40["strictSeparationOrbitCount"] == 0
    assert m40s["birthOrbitCount"] == 2
    assert sorted(m40s["orbitSizes"]) == [216, 4320]
    assert sorted(m40s["stabilizerOrders"]) == [6, 120]
    assert sorted(x["orbitSize"] for x in m40["depth5Births"]) == [216, 4320]
    for row in m40s["rows"]:
        assert row["exactDepth"] == 5
        assert row["optimalNegativeSupportSize"] == 20
        assert row["childDepthPointHistogram"] == {"4": 20, "5": 20}
    birth_digests = {x["representativeDigest"] for x in m40["depth5Births"]}
    assert birth_digests == {x["representativeDigest"] for x in m40s["rows"]}

    # Front 3: explicit W33 controller embedding is order-48 inside Gram-192.
    assert emb["w33Structure"] == "C2 x S4"
    assert emb["w33ControllerOrder"] == 48
    assert emb["s4ComplementOrder"] == 24
    assert emb["s4ActionImageSize"] == 24
    assert emb["s4ActionOnSylow3Faithful"] is True
    assert emb["centralC2MapsToMinusI3"] is True
    assert emb["signedPermutationImageIsAllOh"] is True
    assert emb["signedPermutationImageOrder"] == 48
    assert emb["embeddedGramProjectiveSubgroupOrder"] == 48
    assert emb["gramProjectiveAmbientOrder"] == 192

    # Front 4: inherited depth-4 children and no-pencil births are disjoint.
    assert sep["mass36Depth4ParentOrbitCount"] == 3
    assert sep["mass40NoPencilDepth4BirthOrbitCount"] == 28
    assert sep["mass40NoPencilDepth5BirthOrbitCount"] == 2
    assert sep["depth4InheritedVsBirthIntersection"] == []
    assert sep["crossParentMergerCount"] == 1

    # Front 5: decoder identity is bound into measured boot and signed delivery.
    assert prov["decoder"]["version"] == "octet-hybrid-v3-minimal-1080"
    assert prov["decoder"]["circuitMoveCount"] == 1080
    assert prov["decoder"]["radiusTwoMoveCount"] == 4140
    assert prov["decoder"]["circuitLibraryDigest"] == cd
    assert prov["adversarialRegression"]["radiusTwoLocalMinimumSubstitutionRejected"] is True
    assert prov["adversarialRegression"]["libraryIdentityMutationChangesMeasuredBootChallenge"] is True
    assert all(prov["agreement"].values())

    f = syn["frontiers"]
    assert f["minimalHybridDecoder"]["circuitLibraryDigest"] == cd
    assert f["mass40Depth5Births"]["orbitSizes"] == [216, 4320]
    assert sorted(f["mass40Depth5Births"]["stabilizerOrders"]) == [6, 120]
    assert f["explicitGramEmbedding"]["w33ControllerOrder"] == 48
    assert f["mass36To40Separator"]["inheritedVsBirthIntersectionSize"] == 0
    assert f["decoderAttestation"]["localMinimumSubstitutionRejected"] is True

    print(json.dumps({
        "status": "PASS",
        "minimalCircuitMoveCount": 1080,
        "decoderBenchmarks": "37/37",
        "mass40DepthHistogram": m40["integerDepthHistogram"],
        "depth5OrbitSizes": sorted(m40s["orbitSizes"]),
        "depth5Stabilizers": sorted(m40s["stabilizerOrders"]),
        "w33EmbeddedControllerOrder": emb["w33ControllerOrder"],
        "gramProjectiveAmbientOrder": emb["gramProjectiveAmbientOrder"],
        "inheritanceBirthIntersection": len(sep["depth4InheritedVsBirthIntersection"]),
        "localMinimumSubstitutionRejected": prov["adversarialRegression"]["radiusTwoLocalMinimumSubstitutionRejected"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
