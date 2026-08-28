#############################################################################
##
## H(3,9) HOLE-SYMMETRY INDEX-TWO ORIENTATION / ROLLBACK PROBE
##
## Reconstruct the maximum partial spread and induce its full ambient
## stabilizer on the 120 holes.  Compare that literal subgroup with the full
## hole-graph automorphism group; do not identify groups from orders alone.
##
#############################################################################

E8UnitaryLibraryOnly := true;;
Read("analysis/e8_unitary_elastic_ladders.g");

BoolInt := function(value)
  if value then return 1; fi;
  return 0;
end;

PairOrbitIndex := function(pairOrbits, pair)
  return PositionProperty(pairOrbits, orbit -> pair in orbit);
end;

OrientationRollbackProbe := function()
  local D, neighbours, lineGraph, maxima, witness, covered, holes, holeGraph,
        lineAut, spreadStabilizer, pointPencils, pointImage, holeGenerators,
        holeSpreadGroup, holeAut, maximumFixed, normalizer, holeOrbits,
        fullSuborbits, spreadSuborbits, orderedPairs, pairOrbits, diagonalOrbit,
        normalizerHoleGenerators, normalizerHoleGroup, holePermutation,
        orientationHom, orientationKernel, orientationImage,
        fixedCoveredSets, sameHoleMaxima, fixedIntersection,
        allCoveredSets, coveredFibres, partnerIndices, partnerPerm,
        partnerIntersectionSizes, maximaAction,
        normalizerOuter, outer, outerInvolutions, outerInvolutionOrbits,
        outerInvolutionProfiles, representative, centralizer,
        pairPermutation, pairOrbitAction, orbitIndex, imageIndex,
        pairOrbitDegrees, pairOrbitAdjacency, adjacency, i, orbit,
        quotient, quotientMap, quotientImage, quotientKernel,
        translationCore, spreadCore, fullCore, coreIndex,
        fullAbelianization, indexTwoNormals, indexTwoProfiles,
        subgroup, profile, checks;

  D := BuildHermitianGQ(3);
  neighbours := PointNeighbours(D);
  lineGraph := DisjointLineGraph(D);
  maxima := CompleteSubgraphsOfGivenSize(lineGraph, 16, 1);
  witness := maxima[1];
  covered := Set(Concatenation(D.lines{witness}));
  holes := Difference([1..Length(D.points)], covered);
  holeGraph := Graph(Group(()), holes, OnPoints,
    function(p, r)
      return p <> r and r in neighbours[p];
    end, true);

  lineAut := AutGroupGraph(lineGraph);
  spreadStabilizer := Stabilizer(lineAut, Set(witness), OnSets);
  allCoveredSets := List(maxima,
    candidate -> Set(Concatenation(D.lines{candidate})));
  coveredFibres := Collected(allCoveredSets);
  partnerIndices := List([1..Length(maxima)], i ->
    First([1..Length(maxima)], j ->
      j <> i and allCoveredSets[j] = allCoveredSets[i]));
  partnerPerm := PermList(partnerIndices);
  partnerIntersectionSizes := Set(List(
    Filtered([1..Length(maxima)], i -> i < partnerIndices[i]),
    i -> Length(Intersection(maxima[i], maxima[partnerIndices[i]]))));
  maximaAction := Action(lineAut, maxima, OnSets);
  pointPencils := List([1..Length(D.points)], p ->
    Set(Filtered([1..Length(D.lines)], l -> p in D.lines[l])));
  pointImage := function(p, generator)
    return Position(pointPencils,
      Set(List(pointPencils[p], l -> l ^ generator)));
  end;
  holeGenerators := List(GeneratorsOfGroup(spreadStabilizer), generator ->
    PermList(List(holes, p -> Position(holes, pointImage(p, generator)))));
  holeSpreadGroup := Group(holeGenerators);
  holeAut := AutGroupGraph(holeGraph);

  maximumFixed := Filtered(maxima, candidate ->
    ForAll(GeneratorsOfGroup(spreadStabilizer), generator ->
      Set(List(candidate, l -> l ^ generator)) = Set(candidate)));
  normalizer := Normalizer(lineAut, spreadStabilizer);
  fixedCoveredSets := List(maximumFixed,
    candidate -> Set(Concatenation(D.lines{candidate})));
  sameHoleMaxima := Filtered(maxima, candidate ->
    Set(Concatenation(D.lines{candidate})) = covered);
  fixedIntersection := Length(Intersection(maximumFixed[1], maximumFixed[2]));
  holePermutation := function(generator)
    return PermList(List(holes,
      p -> Position(holes, pointImage(p, generator))));
  end;
  normalizerHoleGenerators := List(GeneratorsOfGroup(normalizer),
    holePermutation);
  normalizerHoleGroup := Group(normalizerHoleGenerators);
  orientationHom := ActionHomomorphism(normalizer, maximumFixed, OnSets);
  orientationKernel := Kernel(orientationHom);
  orientationImage := Image(orientationHom);
  holeOrbits := Orbits(holeSpreadGroup, [1..Length(holes)]);
  fullSuborbits := Orbits(Stabilizer(holeAut, 1), [1..Length(holes)]);
  spreadSuborbits := Orbits(Stabilizer(holeSpreadGroup, 1),
    [1..Length(holes)]);

  orderedPairs := Tuples([1..Length(holes)], 2);
  pairOrbits := OrbitsDomain(holeSpreadGroup, orderedPairs, OnTuples);
  diagonalOrbit := PositionProperty(pairOrbits,
    candidate -> [1, 1] in candidate);
  pairOrbitDegrees := [];
  pairOrbitAdjacency := [];
  adjacency := Adjacency(holeGraph, 1);
  for i in [1..Length(pairOrbits)] do
    orbit := pairOrbits[i];
    if i = diagonalOrbit then
      Add(pairOrbitDegrees, 1);
      Add(pairOrbitAdjacency, false);
    else
      Add(pairOrbitDegrees,
        Number(orbit, pair -> pair[1] = 1));
      Add(pairOrbitAdjacency,
        ForAny(orbit, pair -> pair[1] = 1 and pair[2] in adjacency));
    fi;
  od;

  normalizerOuter := First(Elements(normalizer),
    g -> not g in spreadStabilizer);
  outer := holePermutation(normalizerOuter);
  pairOrbitAction := [];
  for orbitIndex in [1..Length(pairOrbits)] do
    pairPermutation := List(pairOrbits[orbitIndex][1], x -> x ^ outer);
    imageIndex := PairOrbitIndex(pairOrbits, pairPermutation);
    Add(pairOrbitAction, imageIndex);
  od;

  outerInvolutions := Filtered(Elements(holeAut), g ->
    not g in holeSpreadGroup and Order(g) = 2);
  outerInvolutionOrbits := OrbitsDomain(holeSpreadGroup,
    outerInvolutions, OnPoints);
  outerInvolutionProfiles := [];
  for orbit in outerInvolutionOrbits do
    representative := orbit[1];
    Add(outerInvolutionProfiles, [Length(orbit),
      Number([1..Length(holes)], i -> i ^ representative = i),
      CycleStructurePerm(representative)]);
  od;
  centralizer := Centralizer(holeAut, holeSpreadGroup);

  quotientMap := NaturalHomomorphismByNormalSubgroup(holeAut,
    holeSpreadGroup);
  quotientImage := Image(quotientMap);
  quotientKernel := Kernel(quotientMap);
  quotient := FactorGroup(holeAut, holeSpreadGroup);
  fullCore := PCore(holeAut, 2);
  spreadCore := PCore(holeSpreadGroup, 2);
  coreIndex := Index(fullCore, spreadCore);
  fullAbelianization := AbelianInvariants(holeAut);
  indexTwoNormals := Filtered(NormalSubgroups(holeAut),
    candidate -> Index(holeAut, candidate) = 2);
  indexTwoProfiles := [];
  for subgroup in indexTwoNormals do
    profile := [Size(PCore(subgroup, 2)),
      StructureDescription(FactorGroup(subgroup, PCore(subgroup, 2))),
      List(Orbits(subgroup, [1..Length(holes)]), Length),
      BoolInt(IsomorphismGroups(subgroup, holeSpreadGroup) <> fail),
      BoolInt(subgroup = holeSpreadGroup)];
    Add(indexTwoProfiles, profile);
  od;

  checks := [
    Size(lineAut) = 26127360,
    Length(maxima) = 2268,
    Size(spreadStabilizer) = 11520,
    Length(coveredFibres) = 1134,
    Set(List(coveredFibres, fibre -> fibre[2])) = [2],
    Order(partnerPerm) = 2,
    NrMovedPoints(partnerPerm) = Length(maxima),
    partnerIntersectionSizes = [0],
    IsTransitive(maximaAction, [1..Length(maxima)]),
    Size(maximaAction) = Size(lineAut),
    ForAll(GeneratorsOfGroup(maximaAction), generator ->
      generator * partnerPerm = partnerPerm * generator),
    not partnerPerm in maximaAction,
    Size(holeSpreadGroup) = 11520,
    ForAll(GeneratorsOfGroup(holeSpreadGroup), g -> g in holeAut),
    Size(holeAut) = 23040,
    Index(holeAut, holeSpreadGroup) = 2,
    IsNormal(holeAut, holeSpreadGroup),
    normalizerHoleGroup = holeAut,
    Length(holeOrbits) = 1,
    Length(maximumFixed) = 2,
    Length(sameHoleMaxima) = 2,
    Set(maximumFixed) = Set(sameHoleMaxima),
    fixedCoveredSets[1] = fixedCoveredSets[2],
    fixedCoveredSets[1] = covered,
    fixedIntersection = 0,
    Size(normalizer) = 23040,
    orientationKernel = spreadStabilizer,
    Size(orientationImage) = 2,
    Set(List(maximumFixed, candidate -> OnSets(Set(candidate), normalizerOuter))) =
      Set(maximumFixed),
    OnSets(Set(maximumFixed[1]), normalizerOuter) = Set(maximumFixed[2]),
    Size(quotient) = 2,
    StructureDescription(quotient) = "C2",
    quotientKernel = holeSpreadGroup,
    Size(quotientImage) = 2,
    coreIndex = 2,
    Size(centralizer) = 1,
    Length(outerInvolutions) > 0,
    Length(indexTwoNormals) = 3
  ];
  if not ForAll(checks, x -> x) then
    Print("FAILED_CHECK_VECTOR|", List(checks, BoolInt), "\n");
    Error("orientation/rollback probe failed");
  fi;

  Print("ORIENTATION_EXTENSION|lineAut=", Size(lineAut),
        "|maxima=", Length(maxima),
        "|spreadStabilizer=", Size(spreadStabilizer),
        "|inducedHoleGroup=", Size(holeSpreadGroup),
        "|holeAut=", Size(holeAut),
        "|index=", Index(holeAut, holeSpreadGroup),
        "|normal=", BoolInt(IsNormal(holeAut, holeSpreadGroup)), "\n");
  Print("STATE_ACTION|spreadHoleOrbits=", List(holeOrbits, Length),
        "|spreadSuborbits=", List(spreadSuborbits, Length),
        "|fullSuborbits=", List(fullSuborbits, Length), "\n");
  Print("MAXIMUM_SPREAD_ACTION|fixedByStabilizer=", Length(maximumFixed),
        "|sameHoleMaxima=", Length(sameHoleMaxima),
        "|sharedLines=", fixedIntersection,
        "|coveredSetsEqual=", BoolInt(fixedCoveredSets[1] = fixedCoveredSets[2]),
        "|normalizer=", Size(normalizer),
        "|orientationImage=", StructureDescription(orientationImage),
        "|kernel=", Size(orientationKernel),
        "|outerSwaps=1|outerExtends=1\n");
  Print("GLOBAL_PARTNER_INVOLUTION|states=", Length(maxima),
        "|fibres=", Length(coveredFibres),
        "|fibreSizes=", Set(List(coveredFibres, fibre -> fibre[2])),
        "|sharedLines=", partnerIntersectionSizes,
        "|moved=", NrMovedPoints(partnerPerm),
        "|commutesWithAmbient=1|insideAmbient=0",
        "|equivariantCentralizerOrder=", Index(normalizer, spreadStabilizer),
        "\n");
  Print("QUOTIENT_BIT|quotient=", StructureDescription(quotient),
        "|kernel=", Size(quotientKernel),
        "|fullAbelianization=", fullAbelianization,
        "|indexTwoNormals=", Length(indexTwoNormals),
        "|profiles=", indexTwoProfiles, "\n");
  Print("DIRECTED_ORBITALS|count=", Length(pairOrbits),
        "|degrees=", pairOrbitDegrees,
        "|adjacent=", pairOrbitAdjacency,
        "|outerAction=", pairOrbitAction, "\n");
  Print("ROLLBACK_NO_GO|outerInvolutions=", Length(outerInvolutions),
        "|KConjugacyOrbits=", List(outerInvolutionOrbits, Length),
        "|profiles=", outerInvolutionProfiles,
        "|centralizer=", Size(centralizer),
        "|canonicalOuterInvolution=0\n");
  Print("ALL_ORIENTATION_ROLLBACK_CHECKS_PASS\n");
  return rec(checks := checks, group := holeAut,
    subgroup := holeSpreadGroup, pairOrbits := pairOrbits);
end;

OrientationRollback := OrientationRollbackProbe();;
QUIT;
