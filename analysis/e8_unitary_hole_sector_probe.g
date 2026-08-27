#############################################################################
##
## MAXIMUM-PARTIAL-SPREAD HOLE SECTORS IN H(3,4) AND H(3,9)
##
## This probe continues the elastic-ladder certificate at its exact ceiling.
## It classifies the uncovered point graph, the action on all maximum partial
## spreads, and the way original lines meet the hole sector.  The q=2
## KG(6,2) residual is W33 prior art (BT1837); q=3 is searched here only after
## exact result-signature scans found no 120-hole classification in either
## repository.
##
#############################################################################

E8UnitaryLibraryOnly := true;;
Read("analysis/e8_unitary_elastic_ladders.g");

BoolInt := function(value)
  if value then return 1; fi;
  return 0;
end;

HoleSectorProfile := function(q)
  local D, neighbours, disjointGraph, maximumSize, maxima, lineAut,
        maximumOrbits, witness, covered, holes, holeDegrees, lineCuts,
        holeGraph, holeAut, stabilizer, adjacency, charpoly, factors,
        adjacentCommon, nonadjacentCommon, i, j, common, attachment,
        checks;
  D := BuildHermitianGQ(q);
  neighbours := PointNeighbours(D);
  disjointGraph := DisjointLineGraph(D);
  maximumSize := (q^3 + q + 2) / 2;
  maxima := CompleteSubgraphsOfGivenSize(disjointGraph, maximumSize, 1);
  lineAut := AutGroupGraph(disjointGraph);
  maximumOrbits := Orbits(lineAut, maxima, OnSets);
  witness := maxima[1];
  covered := Set(Concatenation(D.lines{witness}));
  holes := Difference([1..Length(D.points)], covered);
  holeDegrees := Set(List(holes,
    p -> Length(Intersection(neighbours[p], holes))));
  attachment := Set(List(holes,
    p -> Length(Intersection(neighbours[p], covered))));
  lineCuts := Collected(List(D.lines,
    line -> Length(Intersection(line, holes))));

  holeGraph := Graph(Group(()), holes, OnPoints,
    function(p, r)
      return p <> r and r in neighbours[p];
    end, true);
  holeAut := AutGroupGraph(holeGraph);
  stabilizer := Stabilizer(lineAut, Set(witness), OnSets);

  adjacentCommon := [];
  nonadjacentCommon := [];
  for i in [1..Length(holes)] do
    for j in [i+1..Length(holes)] do
      common := Length(Intersection(
        Intersection(neighbours[holes[i]], neighbours[holes[j]]), holes));
      if holes[j] in neighbours[holes[i]] then
        AddSet(adjacentCommon, common);
      else
        AddSet(nonadjacentCommon, common);
      fi;
    od;
  od;

  adjacency := List(holes, p -> List(holes,
    r -> BoolInt(r in neighbours[p])));
  charpoly := CharacteristicPolynomial(Matrix(Integers, adjacency));
  factors := Collected(Factors(Rationals, charpoly));

  checks := [
    Length(maximumOrbits) = 1,
    Length(holes) = Length(D.points) - maximumSize * (q^2 + 1),
    holeDegrees = [q^2 * (q + 1) - maximumSize],
    attachment = [maximumSize],
    Size(stabilizer) * Length(maxima) = Size(lineAut),
    Size(holeAut) >= Size(stabilizer),
    Diameter(holeGraph) > 0
  ];

  Print("HOLE_PROFILE|", q,
        "|maxima=", Length(maxima),
        "|orbits=", List(maximumOrbits, Length),
        "|lineAut=", Size(lineAut),
        "|stabilizer=", Size(stabilizer),
        "|holes=", Length(holes),
        "|degree=", holeDegrees,
        "|attachment=", attachment,
        "|diameter=", Diameter(holeGraph),
        "|holeAut=", Size(holeAut),
        "|lineCuts=", lineCuts,
        "|adjCommon=", adjacentCommon,
        "|nonadjCommon=", nonadjacentCommon,
        "\n");
  Print("CHARPOLY|", q, "|", charpoly, "\n");
  Print("FACTORS|", q, "|", factors, "\n");
  Print("WITNESS_HOLES|", q, "|", holes, "\n");
  if not ForAll(checks, x -> x) then Error("hole-sector audit failed"); fi;
  return rec(q := q, checks := checks, holeGraph := holeGraph,
             holeAut := holeAut, lineAut := lineAut,
             maximumOrbits := maximumOrbits);
end;

H2 := HoleSectorProfile(2);;
H3 := HoleSectorProfile(3);;
Print("ALL_HOLE_CHECKS_PASS\n");
QUIT;
