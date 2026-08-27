#############################################################################
##
## H(3,9) MAXIMUM-SPREAD HOLES AS A KUMMER / FOLDED-Q6 DUAD GRAPH
##
## This script starts independently from the Hermitian generalized
## quadrangle and from Q6/{x~x+111111}.  It asks GAP/GRAPE for an explicit
## graph isomorphism; equal orders or spectra are not treated as evidence.
##
#############################################################################

E8UnitaryLibraryOnly := true;;
Read("analysis/e8_unitary_elastic_ladders.g");

BoolInt := function(value)
  if value then return 1; fi;
  return 0;
end;

CanonicalFoldedVector := function(v)
  local complement;
  complement := List(v, x -> 1 - x);
  if v < complement then return v; fi;
  return complement;
end;

FoldedVectors := Set(List(Tuples([0,1], 6), CanonicalFoldedVector));;

FoldedTranslation := function(i)
  return PermList(List(FoldedVectors, function(v)
    local image;
    image := ShallowCopy(v);
    image[i] := 1 - image[i];
    return Position(FoldedVectors, CanonicalFoldedVector(image));
  end));
end;

FoldedCoordinateSwap := function(i)
  return PermList(List(FoldedVectors, function(v)
    local image, entry;
    image := ShallowCopy(v);
    entry := image[i];
    image[i] := image[i + 1];
    image[i + 1] := entry;
    return Position(FoldedVectors, CanonicalFoldedVector(image));
  end));
end;

FoldedQ6Aut := Group(Concatenation(
  List([1..5], FoldedTranslation),
  List([1..5], FoldedCoordinateSwap)));;

FoldedAdjacent := function(i, j)
  local distance;
  distance := Number([1..6], k -> FoldedVectors[i][k] <> FoldedVectors[j][k]);
  return distance = 1 or distance = 5;
end;

DuadBridge := function()
  local D, neighbours, lineGraph, maxima, witness, covered, holes, holeGraph,
        evenClasses, oddClasses, pointDuads, blockDuads, pointDuals,
        blockDuals, dualPoint, dualBlock, duadImage, duadGenerators,
        duadGroup, colourGroup, colourDuadGroup, colourGenerators,
        singleOrbitals, orbitals, degreeTwenty, candidate, graphIso,
        fullAut, holeSingleOrbitals, holeVertexStabilizer,
        duadVertexStabilizer, lineAut,
        spreadStabilizer, signature, edgeSignatures, nonedgeSignatures,
        subsetOrbits, subsetOrbit, objectGenerators, objectGroup,
        objectStabilizer, objectOrbitals, objectDegreeTwenty, objectGraph,
        objectIso, carrierProfiles, foundCarrier, targetStabilizerId,
        embeddings, embedding, embeddedStabilizer, cosets, cosetGroup,
        cosetOrbitals, cosetDegreeTwenty, cosetGraph, cosetIso,
        cosetProfiles, foundCosetCarrier, k, i, j, checks;

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

  evenClasses := Filtered([1..32],
    i -> Sum(FoldedVectors[i]) mod 2 = 0);
  oddClasses := Difference([1..32], evenClasses);
  pointDuads := Combinations(evenClasses, 2);
  blockDuads := Combinations(oddClasses, 2);

  dualPoint := function(duad)
    return Set(Filtered(oddClasses,
      b -> ForAll(duad, p -> FoldedAdjacent(p, b))));
  end;
  dualBlock := function(duad)
    return Set(Filtered(evenClasses,
      p -> ForAll(duad, b -> FoldedAdjacent(p, b))));
  end;
  pointDuals := List(pointDuads, dualPoint);
  blockDuals := List(blockDuads, dualBlock);

  duadImage := function(duad, generator)
    local image, blockPosition;
    image := Set(List(duad, p -> p ^ generator));
    if image[1] in evenClasses then return Position(pointDuads, image); fi;
    blockPosition := Position(blockDuads, image);
    return Position(pointDuads, blockDuals[blockPosition]);
  end;
  duadGenerators := List(GeneratorsOfGroup(FoldedQ6Aut), generator ->
    PermList(List(pointDuads, duad -> duadImage(duad, generator))));
  duadGroup := Group(duadGenerators);

  colourGroup := Stabilizer(FoldedQ6Aut, Set(evenClasses), OnSets);
  colourGenerators := List(GeneratorsOfGroup(colourGroup), generator ->
    PermList(List(pointDuads, duad -> duadImage(duad, generator))));
  colourDuadGroup := Group(colourGenerators);

  singleOrbitals := GeneralizedOrbitalGraphs(duadGroup, 1);
  orbitals := GeneralizedOrbitalGraphs(duadGroup, 2);
  degreeTwenty := Filtered(orbitals, graph -> VertexDegrees(graph) = [20]);
  Print("ORBITAL_PROBE|singleDegrees=",
        List(singleOrbitals, VertexDegrees),
        "|twoOrbitDegree20=", Length(degreeTwenty), "\n");
  if Length(degreeTwenty) = 0 then
    Error("no degree-20 two-orbital union in Kummer duad action");
  fi;
  candidate := degreeTwenty[1];
  graphIso := GraphIsomorphism(holeGraph, candidate);
  fullAut := AutGroupGraph(holeGraph);
  holeSingleOrbitals := GeneralizedOrbitalGraphs(fullAut, 1);
  holeVertexStabilizer := Stabilizer(fullAut, 1);
  duadVertexStabilizer := Stabilizer(duadGroup, 1);
  targetStabilizerId := IdGroup(holeVertexStabilizer);

  carrierProfiles := [];
  foundCarrier := fail;
  for k in [3..4] do
    subsetOrbits := OrbitsDomain(FoldedQ6Aut,
      Combinations([1..32], k), OnSets);
    for subsetOrbit in Filtered(subsetOrbits,
      orbit -> Length(orbit) = 120) do
      objectGenerators := List(GeneratorsOfGroup(FoldedQ6Aut), generator ->
        PermList(List(subsetOrbit, object -> Position(subsetOrbit,
          Set(List(object, point -> point ^ generator))))));
      objectGroup := Group(objectGenerators);
      objectStabilizer := Stabilizer(objectGroup, 1);
      objectOrbitals := GeneralizedOrbitalGraphs(objectGroup, 1);
      Add(carrierProfiles, [k, subsetOrbit[1],
        IdGroup(objectStabilizer), List(objectOrbitals, VertexDegrees)]);
      if IdGroup(objectStabilizer) = targetStabilizerId then
        objectDegreeTwenty := Filtered(
          GeneralizedOrbitalGraphs(objectGroup, 2),
          graph -> VertexDegrees(graph) = [20]);
        for objectGraph in objectDegreeTwenty do
          objectIso := GraphIsomorphism(holeGraph, objectGraph);
          if objectIso <> fail then
            foundCarrier := rec(k := k, orbit := subsetOrbit,
              representative := subsetOrbit[1], group := objectGroup,
              graph := objectGraph, graphIso := objectIso,
              stabilizer := objectStabilizer);
            break;
          fi;
        od;
      fi;
      if foundCarrier <> fail then break; fi;
    od;
    if foundCarrier <> fail then break; fi;
  od;

  embeddings := IsomorphicSubgroups(FoldedQ6Aut,
    SmallGroup(targetStabilizerId));
  cosetProfiles := [];
  foundCosetCarrier := fail;
  for embedding in embeddings do
    embeddedStabilizer := Image(embedding);
    cosets := RightCosets(FoldedQ6Aut, embeddedStabilizer);
    cosetGroup := Action(FoldedQ6Aut, cosets, OnRight);
    cosetOrbitals := GeneralizedOrbitalGraphs(cosetGroup, 1);
    Add(cosetProfiles, List(cosetOrbitals, VertexDegrees));
    cosetDegreeTwenty := Filtered(
      GeneralizedOrbitalGraphs(cosetGroup, 2),
      graph -> VertexDegrees(graph) = [20]);
    for cosetGraph in cosetDegreeTwenty do
      cosetIso := GraphIsomorphism(holeGraph, cosetGraph);
      if cosetIso <> fail then
        foundCosetCarrier := rec(stabilizer := embeddedStabilizer,
          cosets := cosets, group := cosetGroup, graph := cosetGraph,
          graphIso := cosetIso,
          representative := Representative(cosets[1]));
        break;
      fi;
    od;
    if foundCosetCarrier <> fail then break; fi;
  od;

  lineAut := AutGroupGraph(lineGraph);
  spreadStabilizer := Stabilizer(lineAut, Set(witness), OnSets);

  signature := function(a, b)
    local pointIntersection, blockIntersection, crossAB, crossBA;
    pointIntersection := Length(Intersection(pointDuads[a], pointDuads[b]));
    blockIntersection := Length(Intersection(pointDuals[a], pointDuals[b]));
    crossAB := Sum(List(pointDuads[a], p ->
      Number(pointDuals[b], block -> FoldedAdjacent(p, block))));
    crossBA := Sum(List(pointDuads[b], p ->
      Number(pointDuals[a], block -> FoldedAdjacent(p, block))));
    return [pointIntersection, blockIntersection,
            Minimum(crossAB, crossBA), Maximum(crossAB, crossBA)];
  end;
  edgeSignatures := [];
  nonedgeSignatures := [];
  for i in [1..119] do
    for j in [i+1..120] do
      if j in Adjacency(candidate, i) then
        AddSet(edgeSignatures, signature(i, j));
      else
        AddSet(nonedgeSignatures, signature(i, j));
      fi;
    od;
  od;

  checks := [
    Length(FoldedVectors) = 32,
    Length(evenClasses) = 16,
    Length(oddClasses) = 16,
    Length(pointDuads) = 120,
    Set(List(pointDuals, Length)) = [2],
    Set(List(blockDuals, Length)) = [2],
    Set(pointDuals) = Set(blockDuads),
    Set(blockDuals) = Set(pointDuads),
    Size(FoldedQ6Aut) = 23040,
    Size(duadGroup) = 23040,
    IsTransitive(duadGroup, [1..120]),
    Size(colourDuadGroup) = 11520,
    Length(degreeTwenty) = 1,
    graphIso = fail,
    Size(fullAut) = 23040,
    Size(spreadStabilizer) = 11520,
    IsomorphismGroups(colourDuadGroup, spreadStabilizer) <> fail,
    IsomorphismGroups(fullAut, duadGroup) <> fail
  ];
  if not ForAll(checks, x -> x) then Error("Kummer duad bridge failed"); fi;

  Print("KUMMER_DUAD|foldedVertices=32|halves=16+16|duads=120",
        "|fullGroup=", Size(duadGroup),
        "|colourGroup=", Size(colourDuadGroup),
        "|orbitalDegrees=", List(singleOrbitals, VertexDegrees),
        "|degree20Orbitals=", Length(degreeTwenty),
        "|holeIsomorphic=0|graphAut=", Size(fullAut), "\n");
  Print("ACTION_NO_GO|holeOrbitalDegrees=",
        List(holeSingleOrbitals, VertexDegrees),
        "|holeVertexStabilizer=", StructureDescription(holeVertexStabilizer),
        "|holeVertexId=", IdGroup(holeVertexStabilizer),
        "|duadVertexStabilizer=", StructureDescription(duadVertexStabilizer),
        "|duadVertexId=", IdGroup(duadVertexStabilizer),
        "|abstractGroupsIsomorphic=1\n");
  Print("DUAD_SIGNATURES|edges=", edgeSignatures,
        "|nonedges=", nonedgeSignatures, "\n");
  Print("FOLDED_SUBSET_SEARCH|profiles=", carrierProfiles,
        "|found=", BoolInt(foundCarrier <> fail));
  if foundCarrier <> fail then
    Print("|k=", foundCarrier.k,
          "|representative=", foundCarrier.representative,
          "|stabilizer=", StructureDescription(foundCarrier.stabilizer));
  fi;
  Print("\n");
  Print("FOLDED_COSET_SEARCH|embeddingClasses=", Length(embeddings),
        "|profiles=", cosetProfiles,
        "|found=", BoolInt(foundCosetCarrier <> fail));
  if foundCosetCarrier <> fail then
    Print("|stabilizerId=", IdGroup(foundCosetCarrier.stabilizer),
          "|cosets=", Length(foundCosetCarrier.cosets));
  fi;
  Print("\n");
  Print("ALL_KUMMER_DUAD_NO_GO_CHECKS_PASS\n");
  return rec(checks := checks, graphIso := graphIso,
             candidate := candidate, holeGraph := holeGraph);
end;

Bridge := DuadBridge();;
QUIT;
