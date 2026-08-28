#############################################################################
##
## GAP-OWNED 120-COSET -> H(3,9) HOLE COORDINATE / ADJACENCY CERTIFICATE
##
## The q=3 ceiling hole graph was identified as the degree-(16+4) coset
## graph of Aut(folded Q6) on G/H, H = SmallGroup(192,1485).  This witness
## turns that abstract classification into a hardware carrier.  GAP:
##
##   1. reconstructs H(3,9) and a maximum partial spread;
##   2. reconstructs G/H and its degree-20 orbital union;
##   3. asks GRAPE for the graph isomorphism;
##   4. transports every coset to a normalized GF(9)^4 hole coordinate;
##   5. emits the complete adjacency rows and the smaller coordinate table.
##
## JavaScript is permitted to freeze this output, but it does not choose the
## graph, the carrier, the isomorphism, or any edge.
##
#############################################################################

E8UnitaryLibraryOnly := true;;
Read("analysis/e8_unitary_elastic_ladders.g");

CanonicalFoldedVectorRTL := function(v)
  local complement;
  complement := List(v, x -> 1 - x);
  if v < complement then return v; fi;
  return complement;
end;

FoldedVectorsRTL := Set(List(Tuples([0,1], 6),
  CanonicalFoldedVectorRTL));;

FoldedTranslationRTL := function(i)
  return PermList(List(FoldedVectorsRTL, function(v)
    local image;
    image := ShallowCopy(v);
    image[i] := 1 - image[i];
    return Position(FoldedVectorsRTL, CanonicalFoldedVectorRTL(image));
  end));
end;

FoldedCoordinateSwapRTL := function(i)
  return PermList(List(FoldedVectorsRTL, function(v)
    local image, entry;
    image := ShallowCopy(v);
    entry := image[i];
    image[i] := image[i + 1];
    image[i + 1] := entry;
    return Position(FoldedVectorsRTL, CanonicalFoldedVectorRTL(image));
  end));
end;

FoldedQ6AutRTL := Group(Concatenation(
  List([1..5], FoldedTranslationRTL),
  List([1..5], FoldedCoordinateSwapRTL)));;

EmitCosetRTL := function()
  local D, neighbours, lineGraph, maxima, witness, covered, holes, holeGraph,
        fullAut, targetId, embeddings, embedding, H, cosets, cosetGroup,
        singleOrbitals, degreeTwenty, graph, iso, found, selectedDegrees,
        baseNeighbours, orbital, F, basis, coeffPair, coordinates, inverseIso,
        cosetVertex, holeVertex, coordinate, flattened, adjacencyRows,
        i, j, row, hermitian, checks;

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

  fullAut := AutGroupGraph(holeGraph);
  targetId := IdGroup(Stabilizer(fullAut, 1));
  embeddings := IsomorphicSubgroups(FoldedQ6AutRTL, SmallGroup(targetId));
  found := fail;
  for embedding in embeddings do
    H := Image(embedding);
    cosets := RightCosets(FoldedQ6AutRTL, H);
    cosetGroup := Action(FoldedQ6AutRTL, cosets, OnRight);
    for graph in Filtered(GeneralizedOrbitalGraphs(cosetGroup, 2),
      candidate -> VertexDegrees(candidate) = [20]) do
      iso := GraphIsomorphism(holeGraph, graph);
      if iso <> fail then
        found := rec(H := H, cosets := cosets, group := cosetGroup,
                     graph := graph, iso := iso);
        break;
      fi;
    od;
    if found <> fail then break; fi;
  od;
  if found = fail then Error("certified coset carrier was not recovered"); fi;

  # The two selected nontrivial orbitals are exactly the two H-double-coset
  # relations of valencies 16 and 4.
  singleOrbitals := GeneralizedOrbitalGraphs(found.group, 1);
  baseNeighbours := Adjacency(found.graph, 1);
  selectedDegrees := [];
  for orbital in singleOrbitals do
    if IsSubset(baseNeighbours, Adjacency(orbital, 1)) then
      Add(selectedDegrees, VertexDegrees(orbital)[1]);
    fi;
  od;
  Sort(selectedDegrees);

  # CanonicalBasis(GF(9)) writes x = a + b*alpha with alpha^2=alpha+1.
  # Each coordinate therefore becomes two base-3 digits [a,b].
  F := GF(9);
  basis := CanonicalBasis(F);
  coeffPair := function(x)
    return List(Coefficients(basis, x), IntFFE);
  end;
  inverseIso := Inverse(found.iso);
  coordinates := [];
  for cosetVertex in [1..120] do
    holeVertex := cosetVertex ^ inverseIso;
    coordinate := D.points[holes[holeVertex]];
    flattened := Concatenation(List(coordinate, coeffPair));
    Add(coordinates, flattened);
    Print("MAP|", cosetVertex - 1, "|", holeVertex - 1,
          "|", holes[holeVertex] - 1, "\n");
    Print("COORD|", cosetVertex - 1, "|", flattened, "\n");
  od;

  adjacencyRows := [];
  for i in [1..120] do
    row := List(Adjacency(found.graph, i), x -> x - 1);
    Add(adjacencyRows, row);
    Print("ADJ|", i - 1, "|", row, "\n");
  od;

  hermitian := function(x, y)
    return Sum([1..4], k -> x[k] * y[k]^3);
  end;
  checks := [
    Length(FoldedVectorsRTL) = 32,
    Size(FoldedQ6AutRTL) = 23040,
    targetId = [192,1485],
    Length(embeddings) = 1,
    Length(found.cosets) = 120,
    Size(found.H) = 192,
    VertexDegrees(found.graph) = [20],
    selectedDegrees = [4,16],
    Length(Set(coordinates)) = 120,
    ForAll(coordinates, c -> Length(c) = 8),
    ForAll(adjacencyRows, r -> Length(r) = 20),
    ForAll([1..120], i -> not (i - 1 in adjacencyRows[i])),
    ForAll([1..120], i -> ForAll(adjacencyRows[i],
      j -> i - 1 in adjacencyRows[j + 1])),
    ForAll([1..120], i -> ForAll([1..120], j ->
      ((j - 1 in adjacencyRows[i]) =
       (i <> j and hermitian(
         D.points[holes[(i ^ inverseIso)]],
         D.points[holes[(j ^ inverseIso)]]) = Zero(F)))))
  ];
  if not ForAll(checks, x -> x) then
    Error("coset coordinate/adjacency hardware certificate failed");
  fi;

  Print("RTL_PROFILE|vertices=120|degree=20|edges=1200",
        "|group=23040|stabilizer=192|stabilizerId=[ 192, 1485 ]",
        "|adjacencyDoubleCosetDegrees=", selectedDegrees,
        "|coordinateTrits=8|coordinateBits=16|rowBits=120\n");
  Print("GF9_MODEL|basis=[1,alpha]|alphaSquared=alpha+1",
        "|conjugate(a+b*alpha)=(a+b)+2*b*alpha\n");
  Print("ALL_COSET_RTL_CHECKS_PASS\n");
  return rec(coordinates := coordinates, rows := adjacencyRows,
             graph := found.graph, iso := found.iso);
end;

CosetRTL := EmitCosetRTL();;
QUIT;
