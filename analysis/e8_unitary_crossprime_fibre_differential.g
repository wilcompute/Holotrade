#############################################################################
## Exact q=3 -> q=2 fibre quotient and characteristic-two differential.
##
## GAP reconstructs both Hermitian maximum-partial-spread hole graphs.  It
## then rebuilds the certified 120-coset action of Aut(folded Q6), takes the
## orbits of its elementary abelian 2-core, and compares the resulting
## weighted 15-state quotient with the q=2 hole graph.  The same 120-state
## adjacency matrix is finally treated over GF(2), where it becomes a
## square-zero rank-40 differential.
#############################################################################

SetInfoLevel(InfoWarning, 0);;
SizeScreen([2000, 1000]);;
E8UnitaryLibraryOnly := true;;
Read("analysis/e8_unitary_elastic_ladders.g");

BoolIntCross := function(value)
  if value then return 1; fi;
  return 0;
end;

CanonicalFoldedCross := function(v)
  local complement;
  complement := List(v, x -> 1 - x);
  if v < complement then return v; fi;
  return complement;
end;

FoldedVectorsCross := Set(List(Tuples([0, 1], 6),
  CanonicalFoldedCross));;

FoldedTranslationCross := function(i)
  return PermList(List(FoldedVectorsCross, function(v)
    local image;
    image := ShallowCopy(v);
    image[i] := 1 - image[i];
    return Position(FoldedVectorsCross, CanonicalFoldedCross(image));
  end));
end;

FoldedSwapCross := function(i)
  return PermList(List(FoldedVectorsCross, function(v)
    local image, entry;
    image := ShallowCopy(v);
    entry := image[i];
    image[i] := image[i + 1];
    image[i + 1] := entry;
    return Position(FoldedVectorsCross, CanonicalFoldedCross(image));
  end));
end;

FoldedAutCross := Group(Concatenation(
  List([1..5], FoldedTranslationCross),
  List([1..5], FoldedSwapCross)));;

BuildHoleCross := function(q)
  local D, neighbours, lineGraph, maximumSize, maxima, witness, covered,
        holes, graph;
  D := BuildHermitianGQ(q);
  neighbours := PointNeighbours(D);
  lineGraph := DisjointLineGraph(D);
  maximumSize := (q^3 + q + 2) / 2;
  maxima := CompleteSubgraphsOfGivenSize(lineGraph, maximumSize, 1);
  witness := maxima[1];
  covered := Set(Concatenation(D.lines{witness}));
  holes := Difference([1..Length(D.points)], covered);
  graph := Graph(Group(()), holes, OnPoints,
    function(p, r)
      return p <> r and r in neighbours[p];
    end, true);
  return rec(D := D, neighbours := neighbours, graph := graph,
             holes := holes, maxima := maxima);
end;

ConnectorProfilesCross := function(graph, blocks, quotient, crossOnly)
  local profiles, i, j, universe, unseen, sizes, todo, seen, vertex,
        neighbours;
  profiles := [];
  for i in [1..Length(blocks)-1] do
    for j in [i+1..Length(blocks)] do
      if quotient[i][j] = 2 then
        universe := Union(blocks[i], blocks[j]);
        unseen := Set(universe);
        sizes := [];
        while Length(unseen) > 0 do
          todo := [unseen[1]];
          seen := [];
          while Length(todo) > 0 do
            vertex := Remove(todo);
            if not vertex in seen then
              Add(seen, vertex);
              RemoveSet(unseen, vertex);
              if crossOnly then
                if vertex in blocks[i] then
                  neighbours := Intersection(Adjacency(graph, vertex), blocks[j]);
                else
                  neighbours := Intersection(Adjacency(graph, vertex), blocks[i]);
                fi;
              else
                neighbours := Intersection(Adjacency(graph, vertex), universe);
              fi;
              Append(todo, neighbours);
            fi;
          od;
          Add(sizes, Length(seen));
        od;
        AddSet(profiles, SortedList(sizes));
      fi;
    od;
  od;
  return profiles;
end;

CrossPrimeFibreDifferential := function()
  local q2, q3, fullQ3, targetId, embeddings, embedding, H, cosets,
        cosetAction, orbital, graph, graphIso, found, G, N, K, HN,
        actionHom, NAction, blocks, blockOf, blockAction, blockKernel,
        quotient, equitable, i, j, vertex, row, supportGraph, zeroGraph,
        duads, triangular, kneser, zeroToDuad, zeroToQ2, x, quotientPoly,
        fibre, fibreGraph, k44, fibrePoly, connectorProfiles,
        crossConnectorProfiles, F2, A2,
        rank2, squareZero, factorsQ3, factorsQ2, block, mappedDuad,
        checks;

  q2 := BuildHoleCross(2);
  q3 := BuildHoleCross(3);
  fullQ3 := AutGroupGraph(q3.graph);
  targetId := IdGroup(Stabilizer(fullQ3, 1));
  embeddings := IsomorphicSubgroups(FoldedAutCross, SmallGroup(targetId));
  found := fail;
  for embedding in embeddings do
    H := Image(embedding);
    cosets := RightCosets(FoldedAutCross, H);
    cosetAction := Action(FoldedAutCross, cosets, OnRight);
    for orbital in Filtered(GeneralizedOrbitalGraphs(cosetAction, 2),
      candidate -> VertexDegrees(candidate) = [20]) do
      graphIso := GraphIsomorphism(q3.graph, orbital);
      if graphIso <> fail then
        found := rec(H := H, cosets := cosets, action := cosetAction,
                     graph := orbital, isomorphism := graphIso);
        break;
      fi;
    od;
    if found <> fail then break; fi;
  od;
  if found = fail then Error("q=3 certified coset carrier not recovered"); fi;

  G := FoldedAutCross;
  H := found.H;
  graph := found.graph;
  actionHom := ActionHomomorphism(G, found.cosets, OnRight);
  N := PCore(G, 2);
  K := Intersection(H, N);
  HN := ClosureGroup(H, N);
  NAction := Image(actionHom, N);
  blocks := List(Orbits(NAction, [1..120]), Set);
  SortBy(blocks, block -> Minimum(block));
  blockOf := List([1..120], vertex -> PositionProperty(blocks,
    block -> vertex in block));
  blockAction := Action(found.action, blocks, OnSets);
  blockKernel := Kernel(ActionHomomorphism(found.action, blocks, OnSets));

  quotient := [];
  equitable := true;
  for i in [1..15] do
    Add(quotient, []);
    for j in [1..15] do
      Add(quotient[i], Length(Intersection(
        Adjacency(graph, blocks[i][1]), blocks[j])));
    od;
    for vertex in blocks[i] do
      row := List([1..15], j -> Length(Intersection(
        Adjacency(graph, vertex), blocks[j])));
      if row <> quotient[i] then equitable := false; fi;
    od;
  od;

  supportGraph := Graph(Group(()), [1..15], OnPoints,
    function(a, b)
      return a <> b and quotient[a][b] > 0;
    end, true);
  zeroGraph := Graph(Group(()), [1..15], OnPoints,
    function(a, b)
      return a <> b and quotient[a][b] = 0;
    end, true);
  duads := Combinations([1..6], 2);
  triangular := Graph(Group(()), [1..15], OnPoints,
    function(a, b)
      return a <> b and Length(Intersection(duads[a], duads[b])) = 1;
    end, true);
  kneser := Graph(Group(()), [1..15], OnPoints,
    function(a, b)
      return a <> b and Intersection(duads[a], duads[b]) = [];
    end, true);
  zeroToDuad := GraphIsomorphism(zeroGraph, kneser);
  zeroToQ2 := GraphIsomorphism(zeroGraph, q2.graph);

  x := Indeterminate(Rationals);
  quotientPoly := CharacteristicPolynomial(Rationals, Rationals, quotient);
  factorsQ2 := Collected(Factors(CharacteristicPolynomial(Rationals,
    Rationals, List([1..15], i -> List([1..15], j ->
      BoolIntCross(j in Adjacency(q2.graph, i)))))));
  factorsQ3 := Collected(Factors(CharacteristicPolynomial(Rationals,
    Rationals, List([1..120], i -> List([1..120], j ->
      BoolIntCross(j in Adjacency(graph, i)))))));

  fibre := blocks[1];
  fibreGraph := Graph(Group(()), [1..8], OnPoints,
    function(a, b)
      return a <> b and fibre[b] in Adjacency(graph, fibre[a]);
    end, true);
  k44 := Graph(Group(()), [1..8], OnPoints,
    function(a, b)
      return a <> b and ((a <= 4 and b > 4) or (a > 4 and b <= 4));
    end, true);
  fibrePoly := CharacteristicPolynomial(Rationals, Rationals,
    List([1..8], i -> List([1..8], j ->
      BoolIntCross(j in Adjacency(fibreGraph, i)))));
  connectorProfiles := ConnectorProfilesCross(graph, blocks, quotient, false);
  crossConnectorProfiles := ConnectorProfilesCross(graph, blocks, quotient, true);

  F2 := GF(2);
  A2 := List([1..120], i -> List([1..120], j ->
    BoolIntCross(j in Adjacency(graph, i)) * One(F2)));
  rank2 := RankMat(A2);
  squareZero := A2 * A2 = NullMat(120, 120, F2);

  checks := [
    Length(q2.holes) = 15,
    VertexDegrees(q2.graph) = [6],
    Length(q3.holes) = 120,
    VertexDegrees(q3.graph) = [20],
    Size(G) = 23040,
    targetId = [192, 1485],
    Length(embeddings) = 1,
    Size(H) = 192,
    Size(N) = 32,
    StructureDescription(N) = "C2 x C2 x C2 x C2 x C2",
    Size(K) = 4,
    StructureDescription(K) = "C2 x C2",
    StructureDescription(FactorGroup(N, K)) = "C2 x C2 x C2",
    Size(HN) = 1536,
    StructureDescription(FactorGroup(HN, N)) = "C2 x S4",
    StructureDescription(FactorGroup(G, N)) = "S6",
    Length(blocks) = 15,
    Set(List(blocks, Length)) = [8],
    Size(blockAction) = 720,
    StructureDescription(blockAction) = "S6",
    Size(blockKernel) = 32,
    equitable,
    ForAll([1..15], i -> quotient[i][i] = 4),
    ForAll([1..15], i -> Collected(quotient[i]) = [[0, 6], [2, 8], [4, 1]]),
    GraphIsomorphism(supportGraph, triangular) <> fail,
    zeroToDuad <> fail,
    zeroToQ2 <> fail,
    quotientPoly = (x - 20) * (x - 8)^5 * x^9,
    factorsQ2 = [[x - 6, 1], [x - 1, 9], [x + 3, 5]],
    factorsQ3 = [[x - 20, 1], [x - 8, 5], [x - 4, 45],
                 [x, 9], [x + 4, 60]],
    GraphIsomorphism(fibreGraph, k44) <> fail,
    fibrePoly = (x - 4) * (x + 4) * x^6,
    connectorProfiles = [[16]],
    crossConnectorProfiles = [[4, 4, 4, 4]],
    squareZero,
    rank2 = 40,
    120 - rank2 = 80,
    120 - 2 * rank2 = 40
  ];
  if not ForAll(checks, value -> value) then
    Print("FAILED|", List(checks, BoolIntCross), "\n");
    Error("cross-prime fibre/differential certificate failed");
  fi;

  Print("GROUP_TOWER|G=", Size(G), "|H=", Size(H), "|N=", Size(N),
        "|HcapN=", Size(K), "|HN=", Size(HN),
        "|Nquotient=", StructureDescription(FactorGroup(N, K)),
        "|HNquotient=", StructureDescription(FactorGroup(HN, N)),
        "|Gquotient=", StructureDescription(FactorGroup(G, N)), "\n");
  Print("FIBRE_QUOTIENT|vertices=120|blocks=15|fibre=8|blockAction=S6",
        "|kernel=32|equitable=1|weights=diag4,T6x2,KG0\n");
  Print("SPECTRAL_DESCENT|q3=20^1,8^5,4^45,0^9,-4^60",
        "|quotient=20^1,8^5,0^9|q2KG=6^1,1^9,-3^5",
        "|zero9FromKGplus1=1\n");
  Print("LOCAL_FIBRE|group=C2^3|graph=K4,4|spectrum=4^1,0^6,-4^1",
        "|crossOnlyT6Connector=4C4|twoFibreUnionConnected=1",
        "|twoFibreUnionDegree=6\n");
  Print("MOD2_DIFFERENTIAL|squareZero=1|rank=40|image=40|kernel=80",
        "|homology=40|graded=40,40,40\n");
  for i in [1..15] do
    mappedDuad := duads[i ^ zeroToDuad];
    Print("BLOCK|", i - 1, "|duad=", mappedDuad[1] - 1, ",",
          mappedDuad[2] - 1, "|vertices=",
          JoinStringsWithSeparator(List(blocks[i], value -> String(value - 1)), ","), "\n");
    Print("QROW|", i - 1, "|",
          JoinStringsWithSeparator(List(quotient[i], String), ","), "\n");
  od;
  Print("ALL_CROSSPRIME_FIBRE_DIFFERENTIAL_CHECKS_PASS\n");
  return rec(blocks := blocks, quotient := quotient, blockOf := blockOf,
             zeroToDuad := zeroToDuad, checks := checks, graph := graph,
             graphIsomorphism := graphIso, fullAutomorphismGroup := fullQ3,
             foldedGroup := G, twoCore := N, cosetAction := found.action,
             adjacencyF2 := A2);
end;

if not IsBound(E8CrossPrimeLibraryOnly) then
  CrossPrimeFibre := CrossPrimeFibreDifferential();;
fi;
