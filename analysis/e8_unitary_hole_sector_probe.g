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

SignedCoordinateSwap := function(i)
  local images;
  images := [1..12];
  images[i] := i + 1;
  images[i + 1] := i;
  images[i + 6] := i + 7;
  images[i + 7] := i + 6;
  return PermList(images);
end;

EvenSignFlip := PermList([7,8,3,4,5,6,1,2,9,10,11,12]);;
WD6 := Group(Concatenation([EvenSignFlip],
  List([1..5], SignedCoordinateSwap)));;

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

HoleSectorProfile := function(q)
  local D, neighbours, disjointGraph, maximumSize, maxima, lineAut,
        maximumOrbits, witness, covered, holes, holeDegrees, lineCuts,
        holeGraph, holeAut, stabilizer, adjacency, charpoly, factors,
        adjacentCommon, nonadjacentCommon, i, j, common, attachment,
        checks, wd6Iso, foldedIso, twoCore, outerQuotient,
        stabilizerCore, stabilizerQuotient;
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
  charpoly := CharacteristicPolynomial(Rationals, Rationals, adjacency);
  factors := Collected(Factors(charpoly));
  wd6Iso := fail;
  foldedIso := fail;
  twoCore := fail;
  outerQuotient := fail;
  stabilizerCore := fail;
  stabilizerQuotient := fail;
  if q = 3 then
    wd6Iso := IsomorphismGroups(holeAut, WD6);
    foldedIso := IsomorphismGroups(holeAut, FoldedQ6Aut);
    twoCore := PCore(holeAut, 2);
    outerQuotient := FactorGroup(holeAut, twoCore);
    stabilizerCore := PCore(stabilizer, 2);
    stabilizerQuotient := FactorGroup(stabilizer, stabilizerCore);
  fi;

  checks := [
    Length(maximumOrbits) = 1,
    Length(holes) = Length(D.points) - maximumSize * (q^2 + 1),
    holeDegrees = [q^2 * (q + 1) - maximumSize],
    attachment = [maximumSize],
    Size(stabilizer) * Length(maxima) = Size(lineAut),
    Size(holeAut) >= Size(stabilizer),
    Diameter(holeGraph) > 0
  ];
  if q = 3 then
    Add(checks, Size(WD6) = 23040);
    Add(checks, wd6Iso = fail);
    Add(checks, Size(Centre(WD6)) = 2);
    Add(checks, Size(Centre(holeAut)) = 1);
    Add(checks, Size(FoldedQ6Aut) = 23040);
    Add(checks, foldedIso <> fail);
    Add(checks, Size(twoCore) = 32);
    Add(checks, Size(outerQuotient) = 720);
    Add(checks, Size(stabilizerCore) = 16);
    Add(checks, Size(stabilizerQuotient) = 720);
  fi;

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
        "|holeStructure=", StructureDescription(holeAut),
        "|stabilizerStructure=", StructureDescription(stabilizer),
        "|wd6Iso=", BoolInt(wd6Iso <> fail),
        "|lineCuts=", lineCuts,
        "|adjCommon=", adjacentCommon,
        "|nonadjCommon=", nonadjacentCommon,
        "\n");
  Print("CHARPOLY|", q, "|", charpoly, "\n");
  Print("FACTORS|", q, "|", factors, "\n");
  if q = 3 then
    Print("EXCEPTIONAL_OUTER|twoCore=", Size(twoCore),
          "|quotient=", StructureDescription(outerQuotient),
          "|stabilizerQuotient=", StructureDescription(stabilizerQuotient),
          "|holeCentre=", Size(Centre(holeAut)),
          "|wd6Centre=", Size(Centre(WD6)),
          "|foldedQ6Iso=", BoolInt(foldedIso <> fail), "\n");
  fi;
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
