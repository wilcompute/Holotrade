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
        fullAut, lineAut,
        spreadStabilizer, signature, edgeSignatures, nonedgeSignatures,
        i, j, checks;

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
  candidate := fail;
  graphIso := fail;
  for i in [1..Length(degreeTwenty)] do
    graphIso := GraphIsomorphism(holeGraph, degreeTwenty[i]);
    if graphIso <> fail then
      candidate := degreeTwenty[i];
      break;
    fi;
  od;
  if candidate = fail then Error("degree-20 duad unions miss hole graph"); fi;
  fullAut := AutGroupGraph(candidate);

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
    graphIso <> fail,
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
        "|holeIsomorphic=1|graphAut=", Size(fullAut), "\n");
  Print("DUAD_SIGNATURES|edges=", edgeSignatures,
        "|nonedges=", nonedgeSignatures, "\n");
  Print("ALL_KUMMER_DUAD_CHECKS_PASS\n");
  return rec(checks := checks, graphIso := graphIso,
             candidate := candidate, holeGraph := holeGraph);
end;

Bridge := DuadBridge();;
QUIT;
