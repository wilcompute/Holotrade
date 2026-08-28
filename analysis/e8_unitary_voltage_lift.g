#############################################################################
## Exact affine-voltage chart for the 120-state q=3 unitary hole graph.
##
## This witness reconstructs the certified coset graph independently, takes
## the fifteen orbits of the normal C2^5, and assigns each eight-state fibre
## a quotient-linear F2^3 coordinate.  It then proves that every T(6) block
## connector is an affine codimension-two relation (four disjoint C4s), while every
## diagonal block is the single equation x_0+y_0=1 (K4,4).
#############################################################################

SetInfoLevel(InfoWarning, 0);;
SizeScreen([4000, 1000]);;
E8UnitaryLibraryOnly := true;;
Read("analysis/e8_unitary_elastic_ladders.g");

VoltageBoolInt := function(value)
  if value then return 1; fi;
  return 0;
end;

VoltageXor := function(a, b)
  return List([1..Length(a)], i -> (a[i] + b[i]) mod 2);
end;

VoltageDot := function(a, b)
  return Sum([1..Length(a)], i -> a[i] * b[i]) mod 2;
end;

VoltageRank := function(rows)
  if Length(rows) = 0 then return 0; fi;
  return RankMat(List(rows, row -> List(row, x -> x * One(GF(2)))));
end;

VoltageBitString := function(bits)
  return JoinStringsWithSeparator(List(bits, String), "");
end;

VoltageCanonicalFolded := function(v)
  local complement;
  complement := List(v, x -> 1 - x);
  if v < complement then return v; fi;
  return complement;
end;

VoltageFoldedVectors := Set(List(Tuples([0, 1], 6),
  VoltageCanonicalFolded));;

VoltageTranslation := function(i)
  return PermList(List(VoltageFoldedVectors, function(v)
    local image;
    image := ShallowCopy(v);
    image[i] := 1 - image[i];
    return Position(VoltageFoldedVectors, VoltageCanonicalFolded(image));
  end));
end;

VoltageSwap := function(i)
  return PermList(List(VoltageFoldedVectors, function(v)
    local image, entry;
    image := ShallowCopy(v);
    entry := image[i];
    image[i] := image[i + 1];
    image[i + 1] := entry;
    return Position(VoltageFoldedVectors, VoltageCanonicalFolded(image));
  end));
end;

VoltageTranslationGenerators := List([1..5], VoltageTranslation);;
VoltageGroup := Group(Concatenation(
  VoltageTranslationGenerators, List([1..5], VoltageSwap)));;

VoltageBuildHole := function()
  local D, neighbours, lineGraph, maxima, covered, holes, graph;
  D := BuildHermitianGQ(3);
  neighbours := PointNeighbours(D);
  lineGraph := DisjointLineGraph(D);
  maxima := CompleteSubgraphsOfGivenSize(lineGraph, 16, 1);
  covered := Set(Concatenation(D.lines{maxima[1]}));
  holes := Difference([1..Length(D.points)], covered);
  graph := Graph(Group(()), holes, OnPoints,
    function(p, r)
      return p <> r and r in neighbours[p];
    end, true);
  return graph;
end;

VoltageIndependentExtension := function(seed, candidates, target)
  local basis, candidate;
  basis := ShallowCopy(seed);
  for candidate in candidates do
    if VoltageRank(Concatenation(basis, [candidate])) > VoltageRank(basis) then
      Add(basis, candidate);
    fi;
    if Length(basis) = target then return basis; fi;
  od;
  Error("could not extend binary basis");
end;

VoltageAffineEquations := function(points)
  local origin, differences, spanBasis, masks, annihilator, equations, mask;
  origin := points[1];
  differences := Set(List(points, point -> VoltageXor(point, origin)));
  spanBasis := VoltageIndependentExtension([], differences, 4);
  masks := Difference(Tuples([0, 1], Length(origin)),
                      [List([1..Length(origin)], i -> 0)]);
  annihilator := Filtered(masks, mask ->
    ForAll(spanBasis, row -> VoltageDot(mask, row) = 0));
  equations := VoltageIndependentExtension([], annihilator, 2);
  return rec(origin := origin, spanBasis := spanBasis,
             equations := List(equations, mask ->
               [mask, VoltageDot(mask, origin)]),
             affineSet := Set(List(Tuples([0, 1], Length(spanBasis)), coeffs ->
               VoltageXor(List([1..Length(origin)], i ->
                 Sum([1..Length(spanBasis)], j ->
                   coeffs[j] * spanBasis[j][i]) mod 2), origin))));
end;

VoltageApplyAffineMap := function(map, point)
  return List([1..3], i ->
    (map.offset[i] + Sum([1..3], j -> map.matrix[i][j] * point[j])) mod 2);
end;

VoltageAffinePermutations := [];;
for VoltageMatrixBits in Tuples([0, 1], 9) do
  VoltageMatrix := List([0..2], i -> VoltageMatrixBits{[3*i+1..3*i+3]});
  if VoltageRank(VoltageMatrix) = 3 then
    for VoltageOffset in Tuples([0, 1], 3) do
      Add(VoltageAffinePermutations,
          rec(matrix := VoltageMatrix, offset := VoltageOffset));
    od;
  fi;
od;

VoltageMapGraph := function(map)
  return Set(List(Tuples([0, 1], 3), point ->
    Concatenation(point, VoltageApplyAffineMap(map, point))));
end;

VoltageAffineMapPair := function(equations, relation)
  local candidates, decompositions, i, j, leftGraph, rightGraph;
  candidates := Filtered(VoltageAffinePermutations, map ->
    ForAll(VoltageMapGraph(map), point ->
      ForAll(equations, equation ->
        VoltageDot(equation[1], point) = equation[2])));
  decompositions := [];
  for i in [1..Length(candidates)-1] do
    leftGraph := VoltageMapGraph(candidates[i]);
    for j in [i+1..Length(candidates)] do
      rightGraph := VoltageMapGraph(candidates[j]);
      if Intersection(leftGraph, rightGraph) = [] and
         Union(leftGraph, rightGraph) = relation then
        Add(decompositions, [i, j]);
      fi;
    od;
  od;
  if Length(decompositions) = 0 then
    Error("affine connector has no two-permutation decomposition");
  fi;
  return rec(candidateCount := Length(candidates),
             decompositionCount := Length(decompositions),
             maps := candidates{decompositions[1]});
end;

VoltageLiftCertificate := function()
  local geometricGraph, fullAut, targetId, embeddings, embedding, H, cosets,
        action, candidate, graphIso, found, graph, G, N, actionHom, nAction,
        blocks, blockOf, bitVectors, translations, translationAction,
        zeroBits, blockBases, blockKernels, blockRows, stateCoordinates,
        coordinateVertices, i, j, block, base, vertex, bit, image, candidates,
        kernelBits, annihilator, adjacentDifferences, functional, rows,
        coordinate, slot, quotient, duads, supportGraph, triangular,
        supportIso, mappedDuads, points, affine, crossRecords, localChecks,
        crossChecks, relation, expected, lhs, equation, mapPair, connectorGraph,
        universe, connectorSizes, unseen, todo, seen, current, checks;

  geometricGraph := VoltageBuildHole();
  fullAut := AutGroupGraph(geometricGraph);
  targetId := IdGroup(Stabilizer(fullAut, 1));
  embeddings := IsomorphicSubgroups(VoltageGroup, SmallGroup(targetId));
  found := fail;
  for embedding in embeddings do
    H := Image(embedding);
    cosets := RightCosets(VoltageGroup, H);
    action := Action(VoltageGroup, cosets, OnRight);
    for candidate in Filtered(GeneralizedOrbitalGraphs(action, 2),
      graph -> VertexDegrees(graph) = [20]) do
      graphIso := GraphIsomorphism(geometricGraph, candidate);
      if graphIso <> fail then
        found := rec(H := H, cosets := cosets, action := action,
                     graph := candidate);
        break;
      fi;
    od;
    if found <> fail then break; fi;
  od;
  if found = fail then Error("certified q=3 coset graph not recovered"); fi;

  G := VoltageGroup;
  H := found.H;
  graph := found.graph;
  cosets := found.cosets;
  actionHom := ActionHomomorphism(G, cosets, OnRight);
  N := PCore(G, 2);
  nAction := Image(actionHom, N);
  blocks := List(Orbits(nAction, [1..120]), Set);
  SortBy(blocks, block -> Minimum(block));
  blockOf := List([1..120], vertex -> PositionProperty(blocks,
    block -> vertex in block));

  bitVectors := Tuples([0, 1], 5);
  translations := List(bitVectors, bit -> Product([1..5],
    i -> VoltageTranslationGenerators[i]^bit[i]));
  translationAction := List(translations, element -> Image(actionHom, element));
  zeroBits := [0, 0, 0, 0, 0];
  blockBases := [];
  blockKernels := [];
  blockRows := [];
  stateCoordinates := List([1..120], x -> fail);
  coordinateVertices := [];
  localChecks := [];

  for i in [1..15] do
    block := blocks[i];
    base := block[1];
    Add(blockBases, base);
    kernelBits := Filtered(bitVectors,
      bit -> (base ^ translationAction[Position(bitVectors, bit)]) = base);
    Add(blockKernels, kernelBits);
    annihilator := Filtered(Difference(bitVectors, [zeroBits]),
      mask -> ForAll(kernelBits, row -> VoltageDot(mask, row) = 0));

    adjacentDifferences := [];
    for bit in bitVectors do
      image := base ^ translationAction[Position(bitVectors, bit)];
      if image in Adjacency(graph, base) then AddSet(adjacentDifferences, bit); fi;
    od;
    functional := First(annihilator, mask ->
      ForAll(bitVectors, bit ->
        ((bit in adjacentDifferences) = (VoltageDot(mask, bit) = 1))));
    if functional = fail then Error("local K4,4 functional not found"); fi;
    candidates := Filtered(annihilator, mask -> mask <> functional);
    rows := VoltageIndependentExtension([functional], candidates, 3);
    Add(blockRows, rows);
    Add(coordinateVertices, List(Tuples([0, 1], 3), x -> fail));
    for vertex in block do
      bit := First(bitVectors, candidate ->
        (base ^ translationAction[Position(bitVectors, candidate)]) = vertex);
      coordinate := List(rows, mask -> VoltageDot(mask, bit));
      slot := Position(Tuples([0, 1], 3), coordinate);
      stateCoordinates[vertex] := coordinate;
      coordinateVertices[i][slot] := vertex;
    od;
    Add(localChecks,
      Set(coordinateVertices[i]) = Set(block) and
      ForAll(Tuples([0, 1], 3), x -> ForAll(Tuples([0, 1], 3), y ->
        ((coordinateVertices[i][Position(Tuples([0, 1], 3), y)] in
          Adjacency(graph, coordinateVertices[i][Position(Tuples([0, 1], 3), x)])) =
         ((x[1] + y[1]) mod 2 = 1)))));
  od;

  quotient := List([1..15], i -> List([1..15], j ->
    Length(Intersection(Adjacency(graph, blocks[i][1]), blocks[j]))));
  supportGraph := Graph(Group(()), [1..15], OnPoints,
    function(a, b)
      return a <> b and quotient[a][b] = 2;
    end, true);
  duads := Combinations([1..6], 2);
  triangular := Graph(Group(()), [1..15], OnPoints,
    function(a, b)
      return a <> b and Length(Intersection(duads[a], duads[b])) = 1;
    end, true);
  supportIso := GraphIsomorphism(supportGraph, triangular);
  mappedDuads := List([1..15], i -> duads[i ^ supportIso]);

  crossRecords := [];
  crossChecks := [];
  connectorSizes := [];
  for i in [1..14] do
    for j in [i+1..15] do
      if quotient[i][j] = 2 then
        points := [];
        for coordinate in Tuples([0, 1], 3) do
          for rows in Tuples([0, 1], 3) do
            vertex := coordinateVertices[i][Position(Tuples([0, 1], 3), coordinate)];
            image := coordinateVertices[j][Position(Tuples([0, 1], 3), rows)];
            if image in Adjacency(graph, vertex) then
              Add(points, Concatenation(coordinate, rows));
            fi;
          od;
        od;
        affine := VoltageAffineEquations(points);
        expected := Set(points);
        relation := Filtered(Tuples([0, 1], 6), point ->
          ForAll(affine.equations, equation ->
            VoltageDot(equation[1], point) = equation[2]));

        universe := Union(blocks[i], blocks[j]);
        unseen := Set(universe);
        connectorGraph := [];
        while Length(unseen) > 0 do
          todo := [unseen[1]];
          seen := [];
          while Length(todo) > 0 do
            current := Remove(todo);
            if not current in seen then
              Add(seen, current);
              RemoveSet(unseen, current);
              if current in blocks[i] then
                Append(todo, Intersection(Adjacency(graph, current), blocks[j]));
              else
                Append(todo, Intersection(Adjacency(graph, current), blocks[i]));
              fi;
            fi;
          od;
          Add(connectorGraph, Length(seen));
        od;
        AddSet(connectorSizes, SortedList(connectorGraph));
        mapPair := VoltageAffineMapPair(affine.equations, expected);
        Add(crossChecks, Length(points) = 16 and affine.affineSet = expected and
          Set(relation) = expected and SortedList(connectorGraph) = [4,4,4,4]);
        Add(crossRecords, rec(left := i, right := j,
          equations := affine.equations,
          affineMapPair := mapPair));
      fi;
    od;
  od;

  checks := [
    Size(G) = 23040,
    Size(H) = 192,
    targetId = [192, 1485],
    Length(embeddings) = 1,
    Size(N) = 32,
    Length(blocks) = 15,
    Set(List(blocks, Length)) = [8],
    ForAll(blockKernels, kernel -> Length(kernel) = 4),
    ForAll(blockRows, rows -> VoltageRank(rows) = 3),
    ForAll(localChecks, x -> x),
    supportIso <> fail,
    VertexDegrees(supportGraph) = [8],
    Length(crossRecords) = 60,
    ForAll(crossChecks, x -> x),
    ForAll(crossRecords, record ->
      record.affineMapPair.candidateCount = 8 and
      record.affineMapPair.decompositionCount = 4),
    connectorSizes = [[4,4,4,4]],
    Set(Concatenation(coordinateVertices)) = [1..120]
  ];
  if not ForAll(checks, x -> x) then
    Print("FAILED|", List(checks, VoltageBoolInt), "\n");
    Error("affine voltage lift certificate failed");
  fi;

  Print("VOLTAGE_PROFILE|vertices=120|base=T6|blocks=15|fibre=F2^3",
        "|local=K4,4|cross=4C4|crossEdges=60|group=2^5:S6\n");
  Print("AFFINE_RELATIONS|localEquations=1|crossEquations=2",
        "|allCrossAffine=1|coordinateBits=7",
        "|affineMapsPerCross=8|twoMapDecompositions=4\n");
  for i in [1..15] do
    Print("BLOCK|", i - 1, "|duad=", mappedDuads[i][1] - 1, ",",
          mappedDuads[i][2] - 1, "|kernel=",
          JoinStringsWithSeparator(List(blockKernels[i], VoltageBitString), ","),
          "|rows=", JoinStringsWithSeparator(List(blockRows[i], VoltageBitString), ","),
          "|vertices=", JoinStringsWithSeparator(
            List(coordinateVertices[i], x -> String(x - 1)), ","), "\n");
  od;
  for relation in crossRecords do
    Print("CROSS|", relation.left - 1, "|", relation.right - 1, "|",
          VoltageBitString(relation.equations[1][1]), "|",
          relation.equations[1][2], "|",
          VoltageBitString(relation.equations[2][1]), "|",
          relation.equations[2][2], "\n");
    Print("MAPS|", relation.left - 1, "|", relation.right - 1);
    for mapPair in relation.affineMapPair.maps do
      Print("|", VoltageBitString(Concatenation(mapPair.matrix)), "|",
            VoltageBitString(mapPair.offset));
    od;
    Print("\n");
  od;
  Print("ALL_E8_UNITARY_VOLTAGE_LIFT_CHECKS_PASS\n");
  return rec(checks := checks, coordinateVertices := coordinateVertices,
             blockRows := blockRows, blockKernels := blockKernels,
             crossRecords := crossRecords);
end;

if not IsBound(E8VoltageLibraryOnly) then
  E8UnitaryVoltageLift := VoltageLiftCertificate();;
fi;
