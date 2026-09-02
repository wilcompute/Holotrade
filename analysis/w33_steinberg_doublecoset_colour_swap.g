#############################################################################
## Five-front continuation, exact GAP owner for three representation fronts.
##
##  1. Construct Hom_PSp(St_81^3,St_81) from actual 1080x216 orbit relations.
##  2. Enumerate the double-coset correspondences between the two index-216
##     S5 actions and prove every such correspondence kills circuit Steinberg.
##  3. Realize bicolour exchange by an outer involution and resolve its action
##     on common60 = circuit45 direct-sum diagonal15.
#############################################################################

Read("analysis/e8_pg34_sentinel_control_plane.g");;

BoolIntFive := function(value)
  if value then return 1; fi;
  return 0;
end;;
JoinIntsFive := row -> JoinStringsWithSeparator(List(row, String), ",");;
JoinRowsFive := rows -> JoinStringsWithSeparator(List(rows, JoinIntsFive), ";");;

Generators40Five := GeneratorsOfGroup(PSpGroup);;
Generators45Five := Generators45;;
Generators40LineFive := List(Generators40Five, generator ->
  PermList(List(Lines, line -> Position(Lines,
    Set(List(line, point -> point^generator))))));;

# The 27 five-packet charts of GQ(2,4): five mutually disjoint sentinel octets.
ChartsFive := Filtered(Combinations([1..45], 5), chart ->
  ForAll(Combinations(chart, 2), pair ->
    IsEmpty(Intersection(Supports[pair[1]], Supports[pair[2]]))));;
if Length(ChartsFive) <> 27 then Error("27-chart reconstruction failed"); fi;

Generators27Five := List(Generators45Five, generator ->
  PermList(List(ChartsFive, chart -> Position(ChartsFive,
    Set(List(chart, point -> point^generator))))));;

# The 216 circuit action and the true 1080 = 27 charts x 40 W33 lines
# obstruction-product action.  The 40-point action is outer-related but is not
# interchangeable with this line action inside the fixed PSp representation.
Generators216Five := List(Generators45Five, generator ->
  PermList(List(Circuits, circuit -> Position(Circuits,
    Set(List(circuit, point -> point^generator))))));;
CircuitGroupFive := Group(Generators216Five);;

Generators1080Five := List([1..Length(Generators40Five)], index ->
  PermList(List([1..1080], encoded ->
    ((QuoInt(encoded - 1, 40) + 1)^Generators27Five[index] - 1) * 40 +
      (RemInt(encoded - 1, 40) + 1)^Generators40LineFive[index])));;
ObstructionGroupFive := Group(Generators1080Five);;
if Size(CircuitGroupFive) <> 25920 or Size(ObstructionGroupFive) <> 25920 or
   Length(Orbit(ObstructionGroupFive, 1)) <> 1080 then
  Error("paired 216/1080 actions failed");
fi;
Iso1080to216Five := GroupHomomorphismByImages(
  ObstructionGroupFive, CircuitGroupFive,
  Generators1080Five, Generators216Five);;
if not IsBijective(Iso1080to216Five) then
  Error("1080-to-216 group crosswalk failed");
fi;

# Unique circuit-visible degree-81 irreducible and its exact rational central
# projector, formed from the character sum rather than a guessed eigenspace.
CircuitStabilizer216Five := Stabilizer(CircuitGroupFive, 1);;
CircuitPermutationCharacterFive := PermutationCharacter(
  CircuitGroupFive, CircuitStabilizer216Five);;
CircuitTableFive := CharacterTable(CircuitGroupFive);;
CircuitIrreduciblesFive := Irr(CircuitTableFive);;
SteinbergPositionsFive := Filtered([1..Length(CircuitIrreduciblesFive)],
  index -> CircuitIrreduciblesFive[index][1] = 81 and
    ScalarProduct(CircuitIrreduciblesFive[index],
      CircuitPermutationCharacterFive) = 1);;
if Length(SteinbergPositionsFive) <> 1 then
  Error("unique circuit Steinberg character failed");
fi;
SteinbergCharacterFive := CircuitIrreduciblesFive[SteinbergPositionsFive[1]];;
SteinbergValueDistributionFive := Collected(SteinbergCharacterFive);;
CircuitClassesFive := ConjugacyClasses(CircuitGroupFive);;
if Length(CircuitClassesFive) <> Length(SteinbergCharacterFive) or
   not ForAll(SteinbergCharacterFive, IsRat) then
  Error("rational Steinberg class values failed");
fi;
SteinbergProjectorFive := NullMat(216, 216, Rationals);;
SteinbergScaleFive := 81 / Size(CircuitGroupFive);;
for ClassIndexFive in [1..Length(CircuitClassesFive)] do
  CharacterValueFive := SteinbergCharacterFive[ClassIndexFive];;
  if CharacterValueFive <> 0 then
    for ElementFive in Elements(CircuitClassesFive[ClassIndexFive]) do
      for PointFive in [1..216] do
        SteinbergProjectorFive[PointFive][PointFive^ElementFive] :=
          SteinbergProjectorFive[PointFive][PointFive^ElementFive] +
            SteinbergScaleFive * CharacterValueFive;
      od;
    od;
  fi;
od;
if RankMat(SteinbergProjectorFive) <> 81 or
   SteinbergProjectorFive * SteinbergProjectorFive <>
     SteinbergProjectorFive then
  Error("exact Steinberg projector failed");
fi;

SourceStabilizerFive := Stabilizer(ObstructionGroupFive, 1);;
SourceStabilizer216Five := Image(Iso1080to216Five, SourceStabilizerFive);;
SourceCircuitOrbitsFive := List(OrbitsDomain(SourceStabilizer216Five,
  [1..216], OnPoints), ShallowCopy);;
SortBy(SourceCircuitOrbitsFive, orbit -> [Length(orbit), Minimum(orbit)]);;

# One transporter per obstruction point.  An H-orbit O on the target supplies
# the full equivariant 0/1 incidence relation A_O by transport from source 1.
SourceTransportersFive := List([1..1080], point ->
  RepresentativeAction(ObstructionGroupFive, 1, point, OnPoints));;
SteinbergMapsFive := [];;
for OrbitFive in SourceCircuitOrbitsFive do
  RelationFive := NullMat(1080, 216);;
  for SourcePointFive in [1..1080] do
    CircuitTransporterFive := Image(Iso1080to216Five,
      SourceTransportersFive[SourcePointFive]);;
    for TargetPointFive in OrbitFive do
      RelationFive[SourcePointFive][TargetPointFive^CircuitTransporterFive]
        := 1;
    od;
  od;
  Add(SteinbergMapsFive,
    SteinbergProjectorFive * TransposedMat(RelationFive));;
od;

FrobeniusFive := function(left, right)
  local total, row, column;
  total := 0;
  for row in [1..Length(left)] do
    for column in [1..Length(left[row])] do
      total := total + left[row][column] * right[row][column];
    od;
  od;
  return total / 81;
end;;

SteinbergHomGramFive := List(SteinbergMapsFive, left ->
  List(SteinbergMapsFive, right -> FrobeniusFive(left, right)));;
SteinbergHomRankFive := RankMat(SteinbergHomGramFive);;
if Size(SourceStabilizerFive) <> 24 or SteinbergHomRankFive <> 3 then
  Error("explicit Hom(St^3,St) rank failed");
fi;

# Deterministic three-relation basis: greedily retain Gram-independent rows.
SteinbergBasisIndicesFive := [];;
SteinbergBasisRowsFive := [];;
SteinbergBasisRankFive := 0;;
for OrbitIndexFive in [1..Length(SourceCircuitOrbitsFive)] do
  CandidateRowsFive := Concatenation(SteinbergBasisRowsFive,
    [SteinbergHomGramFive[OrbitIndexFive]]);;
  CandidateRankFive := RankMat(CandidateRowsFive);;
  if CandidateRankFive > SteinbergBasisRankFive then
    Add(SteinbergBasisIndicesFive, OrbitIndexFive);
    Add(SteinbergBasisRowsFive, SteinbergHomGramFive[OrbitIndexFive]);
    SteinbergBasisRankFive := CandidateRankFive;
  fi;
  if SteinbergBasisRankFive = 3 then break; fi;
od;
SteinbergBasisGramFive := List(SteinbergBasisIndicesFive, row ->
  List(SteinbergBasisIndicesFive, column ->
    SteinbergHomGramFive[row][column]));;

#############################################################################
# Two nonconjugate S5 actions: complete cross-double-coset basis.
#############################################################################

HemiSeedFive := [1,2,3,4,6,8,9,10,16,17,18,21,25,27,28,29,34,35,37,40];;
HemiCanonicalFive := function(support)
  local normalized;
  normalized := Set(support);
  if 1 in normalized then return normalized; fi;
  return Difference([1..40], normalized);
end;;
OnHemiFive := function(support, permutation)
  return HemiCanonicalFive(List(support, point -> point^permutation));
end;;
HemiLinesFive := List(Orbit(PSpGroup,
  HemiCanonicalFive(HemiSeedFive), OnHemiFive), ShallowCopy);;
Sort(HemiLinesFive);;
if Length(HemiLinesFive) <> 216 then Error("hemisystem orbit failed"); fi;
HemiStabilizerFive := Stabilizer(PSpGroup, HemiLinesFive[1], OnHemiFive);;
Iso40to45Five := GroupHomomorphismByImages(PSpGroup, PSp45,
  Generators40Five, Generators45Five);;
CircuitStabilizer40Five := PreImage(Iso40to45Five, CircuitStabilizer);;
if Size(HemiStabilizerFive) <> 120 or Size(CircuitStabilizer40Five) <> 120 or
   IsConjugate(PSpGroup, HemiStabilizerFive, CircuitStabilizer40Five) then
  Error("two S5 classes failed");
fi;

CircuitOnHemiOrbitsFive := List(OrbitsDomain(CircuitStabilizer40Five,
  HemiLinesFive, OnHemiFive), ShallowCopy);;
SortBy(CircuitOnHemiOrbitsFive, orbit -> [Length(orbit), orbit[1]]);;
DoubleCosetSizesFive := List(CircuitOnHemiOrbitsFive, Length);;
if Length(DoubleCosetSizesFive) <> 5 or Sum(DoubleCosetSizesFive) <> 216 then
  Error("five double-coset relations failed");
fi;

Iso40to216Five := GroupHomomorphismByImages(PSpGroup,
  CircuitGroupFive, Generators40Five, Generators216Five);;
CrossRelationsFive := [];;
CrossRanksFive := [];;
CrossSteinbergRanksFive := [];;
for OrbitFive in CircuitOnHemiOrbitsFive do
  RelationFive := NullMat(216, 216);;
  for SourcePointFive in [1..216] do
    CircuitTransporterFive := RepresentativeAction(CircuitGroupFive,
      1, SourcePointFive, OnPoints);;
    Element40Five := PreImage(Iso40to216Five, CircuitTransporterFive);;
    for TargetPointFive in OrbitFive do
      ImageHemiFive := OnHemiFive(TargetPointFive, Element40Five);
      RelationFive[SourcePointFive][Position(HemiLinesFive, ImageHemiFive)]
        := 1;
    od;
  od;
  if Set(List(RelationFive, Sum)) <> [Length(OrbitFive)] or
     Set(List(TransposedMat(RelationFive), Sum)) <> [Length(OrbitFive)] then
    Error("cross relation biregularity failed");
  fi;
  Add(CrossRelationsFive, RelationFive);
  Add(CrossRanksFive, RankMat(RelationFive));
  SteinbergCrossFive := SteinbergProjectorFive * RelationFive;
  Add(CrossSteinbergRanksFive, RankMat(SteinbergCrossFive));
od;
if CrossSteinbergRanksFive <> [0,0,0,0,0] then
  Error("hemisystem correspondence unexpectedly sees Steinberg");
fi;
OptimalDoubleCosetIndexFive := Position(DoubleCosetSizesFive,
  Minimum(DoubleCosetSizesFive));;
OptimalRelationFive := CrossRelationsFive[OptimalDoubleCosetIndexFive];;
OptimalGramFive := OptimalRelationFive * TransposedMat(OptimalRelationFive);;
OptimalGramPolynomialFive := Factors(CharacteristicPolynomial(OptimalGramFive));;
OptimalGramFactorCountsFive := Collected(List(OptimalGramPolynomialFive, String));;

# The rank-36, valency-six optimum is stronger than a spectral coincidence:
# its repeated row and column supports exhibit 36 disjoint K(6,6) components.
OptimalRowTypesFive := Set(OptimalRelationFive);;
OptimalColumnTypesFive := Set(TransposedMat(OptimalRelationFive));;
OptimalCircuitBlocksFive := List(OptimalRowTypesFive, row ->
  Filtered([1..216], index -> OptimalRelationFive[index] = row));;
OptimalHemiBlocksFive := List(OptimalRowTypesFive, row ->
  Filtered([1..216], index -> row[index] = 1));;
if Length(OptimalRowTypesFive) <> 36 or
   Length(OptimalColumnTypesFive) <> 36 or
   Set(List(OptimalCircuitBlocksFive, Length)) <> [6] or
   Set(List(OptimalHemiBlocksFive, Length)) <> [6] or
   Union(OptimalCircuitBlocksFive) <> [1..216] or
   Union(OptimalHemiBlocksFive) <> [1..216] then
  Error("optimal relation is not the 36 K6,6 quotient");
fi;
OptimalBlockStabilizerFive := Stabilizer(CircuitGroupFive,
  OptimalCircuitBlocksFive[1], OnSets);;
if Size(OptimalBlockStabilizerFive) <> 720 then
  Error("degree-36 quotient stabilizer failed");
fi;
OptimalBlockStabilizerTypeFive := StructureDescription(
  OptimalBlockStabilizerFive);;
CircuitBlockIdFive := List([1..216], point -> PositionProperty(
  OptimalCircuitBlocksFive, block -> point in block));;
HemiBlockIdFive := List([1..216], point -> PositionProperty(
  OptimalHemiBlocksFive, block -> point in block));;
QuotientGeneratorsCircuitFive := [];;
QuotientGeneratorsHemiFive := [];;
for GeneratorIndexFive in [1..Length(Generators216Five)] do
  Add(QuotientGeneratorsCircuitFive, List([1..36], block ->
    CircuitBlockIdFive[
      OptimalCircuitBlocksFive[block][1]^Generators216Five[GeneratorIndexFive]]));
  Add(QuotientGeneratorsHemiFive, List([1..36], block ->
    HemiBlockIdFive[Position(HemiLinesFive, OnHemiFive(
      HemiLinesFive[OptimalHemiBlocksFive[block][1]],
      Generators40Five[GeneratorIndexFive]))]));
od;
if QuotientGeneratorsCircuitFive <> QuotientGeneratorsHemiFive then
  Error("the K6,6 relation failed to identify quotient actions");
fi;

# The minimum K(6,6) relation is the fibre product of the two 216 carriers
# over their common 36-state quotient.  Its point stabilizer is the
# intersection of the two nonconjugate S5 classes.  Compute exactly which
# building-homology species the resulting degree-1296 permutation carrier sees.
FibreHemiFive := CircuitOnHemiOrbitsFive[
  OptimalDoubleCosetIndexFive][1];;
FibreHemiStabilizerFive := Stabilizer(PSpGroup, FibreHemiFive, OnHemiFive);;
FibreProductStabilizerFive := Intersection(
  CircuitStabilizer40Five, FibreHemiStabilizerFive);;
if Size(FibreProductStabilizerFive) <> 20 then
  Error("fibre-product stabilizer is not order 20");
fi;
CircuitCharacter40Five := PermutationCharacter(
  PSpGroup, CircuitStabilizer40Five);;
HemiCharacter40Five := PermutationCharacter(
  PSpGroup, FibreHemiStabilizerFive);;
FibreProductCharacterFive := PermutationCharacter(
  PSpGroup, FibreProductStabilizerFive);;
Irr40Five := Irr(CharacterTable(PSpGroup));;
Building81PositionsFive := Filtered([1..Length(Irr40Five)], index ->
  Irr40Five[index][1] = 81 and
  ScalarProduct(Irr40Five[index], CircuitCharacter40Five) = 1 and
  ScalarProduct(Irr40Five[index], HemiCharacter40Five) = 0);;
Building64PositionsFive := Filtered([1..Length(Irr40Five)], index ->
  Irr40Five[index][1] = 64 and
  ScalarProduct(Irr40Five[index], CircuitCharacter40Five) = 0 and
  ScalarProduct(Irr40Five[index], HemiCharacter40Five) = 1);;
if Length(Building81PositionsFive) <> 1 or
   Length(Building64PositionsFive) <> 1 then
  Error("complementary building-character selection failed");
fi;
FibreProductMultiplicity81Five := ScalarProduct(
  Irr40Five[Building81PositionsFive[1]], FibreProductCharacterFive);;
FibreProductMultiplicity64Five := ScalarProduct(
  Irr40Five[Building64PositionsFive[1]], FibreProductCharacterFive);;
if FibreProductMultiplicity81Five < 1 or FibreProductMultiplicity64Five < 1 then
  Error("fibre product does not see both building homologies");
fi;
Iso40to1080Five := GroupHomomorphismByImages(
  PSpGroup, ObstructionGroupFive, Generators40Five, Generators1080Five);;
if not IsBijective(Iso40to1080Five) then
  Error("40-to-1080 obstruction crosswalk failed");
fi;
ObstructionStabilizer40Five := PreImage(Iso40to1080Five,
  Stabilizer(ObstructionGroupFive, 1));;
ObstructionCharacter40Five := PermutationCharacter(
  PSpGroup, ObstructionStabilizer40Five);;
ObstructionMultiplicity81Five := ScalarProduct(
  Irr40Five[Building81PositionsFive[1]], ObstructionCharacter40Five);;
ObstructionMultiplicity64Five := ScalarProduct(
  Irr40Five[Building64PositionsFive[1]], ObstructionCharacter40Five);;
CommonBuildingDimensionFive := 81 * FibreProductMultiplicity81Five +
  64 * FibreProductMultiplicity64Five;;
BuildingCrossHomDimensionFive :=
  FibreProductMultiplicity81Five * ObstructionMultiplicity81Five +
  FibreProductMultiplicity64Five * ObstructionMultiplicity64Five;;
if [FibreProductMultiplicity81Five, FibreProductMultiplicity64Five] <>
     [3,3] or
   [ObstructionMultiplicity81Five, ObstructionMultiplicity64Five] <>
     [3,3] or CommonBuildingDimensionFive <> 435 or
   BuildingCrossHomDimensionFive <> 18 then
  Error("fibre product / obstruction building-block match failed");
fi;

#############################################################################
# The outer involution is the actual bicolour exchange.  Resolve its parity on
# common60 and on the circuit45 submodule/diagonal15 quotient.
#############################################################################

# Reconstruct six-circuits and the two PSp colour orbits.
TripleRowsSwapFive := [];;
for TripleSwapFive in Combinations([1..45], 3) do
  TripleWordSwapFive := Columns2[TripleSwapFive[1]] +
    Columns2[TripleSwapFive[2]] + Columns2[TripleSwapFive[3]];
  Add(TripleRowsSwapFive, [String(TripleWordSwapFive),
    ShallowCopy(TripleSwapFive)]);
od;
SortBy(TripleRowsSwapFive, row -> row[1]);;
SixCircuitsSwapFive := [];;
RunStartSwapFive := 1;;
while RunStartSwapFive <= Length(TripleRowsSwapFive) do
  RunEndSwapFive := RunStartSwapFive;
  while RunEndSwapFive < Length(TripleRowsSwapFive) and
        TripleRowsSwapFive[RunEndSwapFive + 1][1] =
          TripleRowsSwapFive[RunStartSwapFive][1] do
    RunEndSwapFive := RunEndSwapFive + 1;
  od;
  BucketSwapFive := TripleRowsSwapFive{[RunStartSwapFive..RunEndSwapFive]};
  for PairSwapFive in Combinations(BucketSwapFive, 2) do
    if IsEmpty(Intersection(PairSwapFive[1][2], PairSwapFive[2][2])) then
      AddSet(SixCircuitsSwapFive,
        Union(PairSwapFive[1][2], PairSwapFive[2][2]));
    fi;
  od;
  RunStartSwapFive := RunEndSwapFive + 1;
od;
if Length(SixCircuitsSwapFive) <> 540 then Error("six-circuit swap shell failed"); fi;

IncidenceSwapFive := List(Circuits, five ->
  List(SixCircuitsSwapFive, six ->
    BoolIntFive(Length(Intersection(five, six)) = 3)));;
Generators6SwapFive := List(Generators45Five, generator ->
  PermList(List(SixCircuitsSwapFive, circuit -> Position(
    SixCircuitsSwapFive, Set(List(circuit, point -> point^generator))))));;
Seed6SwapFive := PositionProperty(IncidenceSwapFive[1], value -> value = 1);;
PairGroupSwapFive := Group(List([1..Length(Generators216Five)], index ->
  PermList(Concatenation(
    List([1..216], point -> point^Generators216Five[index]),
    List([1..540], point -> 216 + point^Generators6SwapFive[index])))));;

# DirectProduct uses the second domain shifted by 216.  Decode one orbit.
PairSeedSwapFive := [1, 216 + Seed6SwapFive];;
PairOrbitSwapFive := Orbit(PairGroupSwapFive, PairSeedSwapFive, OnTuples);;
if Length(PairOrbitSwapFive) <> 2160 then Error("bicolour pair orbit failed"); fi;
MPlusSwapFive := NullMat(216, 540);;
for PairSwapFive in PairOrbitSwapFive do
  MPlusSwapFive[PairSwapFive[1]][PairSwapFive[2] - 216] := 1;
od;
MMinusSwapFive := IncidenceSwapFive - MPlusSwapFive;

OuterFive := First(Elements(WAut), element ->
  not element in PSpGroup and Order(element) = 2);;
if OuterFive = fail then Error("outer involution not found"); fi;
Outer45Five := PermList(List(Supports, support -> Position(Supports,
  Set(List(support, point -> point^OuterFive)))));;
Outer216Five := PermList(List(Circuits, circuit -> Position(Circuits,
  Set(List(circuit, point -> point^Outer45Five)))));;
Outer540Five := PermList(List(SixCircuitsSwapFive, circuit -> Position(
  SixCircuitsSwapFive, Set(List(circuit, point -> point^Outer45Five)))));;
if Order(Outer216Five) <> 2 or Order(Outer540Five) <> 2 then
  Error("induced outer involutions failed");
fi;
for RowSwapFive in [1..216] do
  for ColumnSwapFive in [1..540] do
    if MPlusSwapFive[RowSwapFive][ColumnSwapFive] <>
       MMinusSwapFive[RowSwapFive^Outer216Five]
         [ColumnSwapFive^Outer540Five] then
      Error("outer involution does not exchange colours");
    fi;
  od;
od;

PlusSpaceSwapFive := VectorSpace(Rationals, BaseMat(MPlusSwapFive));;
MinusSpaceSwapFive := VectorSpace(Rationals, BaseMat(MMinusSwapFive));;
CommonSpaceSwapFive := Intersection(PlusSpaceSwapFive, MinusSpaceSwapFive);;
CircuitIncidenceSwapFive := List(Circuits, circuit ->
  List([1..45], point -> BoolIntFive(point in circuit)));;
CircuitCarrierSwapFive := VectorSpace(Rationals,
  BaseMat(TransposedMat(CircuitIncidenceSwapFive)));;
TransportedCircuitSwapFive := VectorSpace(Rationals,
  List(BasisVectors(Basis(CircuitCarrierSwapFive)),
    vector -> vector * MPlusSwapFive));;
if Dimension(CommonSpaceSwapFive) <> 60 or
   Dimension(TransportedCircuitSwapFive) <> 45 or
   not IsSubspace(CommonSpaceSwapFive, TransportedCircuitSwapFive) then
  Error("common60/circuit45 reconstruction failed");
fi;

PermuteAmbientRowFive := function(vector, permutation)
  local output, index;
  output := List([1..Length(vector)], x -> 0);
  for index in [1..Length(vector)] do
    output[index^permutation] := vector[index];
  od;
  return output;
end;;

CommonBasisSwapFive := Basis(CommonSpaceSwapFive);;
CommonSwapMatrixFive := List(BasisVectors(CommonBasisSwapFive), vector ->
  Coefficients(CommonBasisSwapFive,
    PermuteAmbientRowFive(vector, Outer540Five)));;
CircuitBasisSwapFive := Basis(TransportedCircuitSwapFive);;
CircuitSwapMatrixFive := List(BasisVectors(CircuitBasisSwapFive), vector ->
  Coefficients(CircuitBasisSwapFive,
    PermuteAmbientRowFive(vector, Outer540Five)));;
if CommonSwapMatrixFive * CommonSwapMatrixFive <> IdentityMat(60) or
   CircuitSwapMatrixFive * CircuitSwapMatrixFive <> IdentityMat(45) then
  Error("colour-swap involution law failed");
fi;
CommonPlusFive := 60 - RankMat(CommonSwapMatrixFive - IdentityMat(60));;
CommonMinusFive := 60 - RankMat(CommonSwapMatrixFive + IdentityMat(60));;
CircuitPlusFive := 45 - RankMat(CircuitSwapMatrixFive - IdentityMat(45));;
CircuitMinusFive := 45 - RankMat(CircuitSwapMatrixFive + IdentityMat(45));;
ResidualPlusFive := CommonPlusFive - CircuitPlusFive;;
ResidualMinusFive := CommonMinusFive - CircuitMinusFive;;
if CommonPlusFive + CommonMinusFive <> 60 or
   CircuitPlusFive + CircuitMinusFive <> 45 or
   ResidualPlusFive + ResidualMinusFive <> 15 then
  Error("colour-swap parity dimensions failed");
fi;

Print("STEINBERG_1080_TO_216|source=1080|target=216|sourceStabilizer=",
  Size(SourceStabilizerFive), "|homOrbitCount=", Length(SourceCircuitOrbitsFive),
  "|sourceFactorization=27chartsx40lines",
  "|orbitSizes=", JoinIntsFive(List(SourceCircuitOrbitsFive, Length)),
  "|steinbergHomRank=", SteinbergHomRankFive,
  "|basisIndices=", JoinIntsFive(SteinbergBasisIndicesFive),
  "|basisOrbitSizes=", JoinIntsFive(List(SteinbergBasisIndicesFive,
    index -> Length(SourceCircuitOrbitsFive[index]))),
  "|basisGram=", JoinRowsFive(SteinbergBasisGramFive), "\n");
Print("STEINBERG_PROJECTOR|degree=81|characterValueDistribution=",
  JoinStringsWithSeparator(List(SteinbergValueDistributionFive, pair ->
    Concatenation(String(pair[1]), "^", String(pair[2]))), ","),
  "|rank=81|idempotent=1\n");
Print("TWO_S5_DOUBLE_COSETS|count=5|valencies=",
  JoinIntsFive(DoubleCosetSizesFive), "|ranks=", JoinIntsFive(CrossRanksFive),
  "|steinbergRanks=", JoinIntsFive(CrossSteinbergRanksFive),
  "|optimalIndex=", OptimalDoubleCosetIndexFive,
  "|optimalValency=", DoubleCosetSizesFive[OptimalDoubleCosetIndexFive],
  "|optimalGramFactors=",
  JoinStringsWithSeparator(List(OptimalGramFactorCountsFive, pair ->
    Concatenation(pair[1], "^", String(pair[2]))), ";"),
  "|components=36|component=K6,6|quotientDegree=36",
  "|quotientStabilizerOrder=720|quotientStabilizerType=",
  OptimalBlockStabilizerTypeFive, "\n");
Print("COLOUR_SWAP|outerOrder=2|exchangesColours=1|commonParity=",
  CommonPlusFive, ",", CommonMinusFive,
  "|circuitParity=", CircuitPlusFive, ",", CircuitMinusFive,
  "|residual15Parity=", ResidualPlusFive, ",", ResidualMinusFive,
  "|common60=45+15|ambient=540\n");
Print("FIBRE_PRODUCT_BUILDINGS|degree=1296|stabilizerOrder=",
  Size(FibreProductStabilizerFive), "|stabilizerType=",
  StructureDescription(FibreProductStabilizerFive),
  "|building81Multiplicity=", FibreProductMultiplicity81Five,
  "|building64Multiplicity=", FibreProductMultiplicity64Five,
  "|obstruction81Multiplicity=", ObstructionMultiplicity81Five,
  "|obstruction64Multiplicity=", ObstructionMultiplicity64Five,
  "|commonBuildingDimension=", CommonBuildingDimensionFive,
  "|buildingCrossHomDimension=", BuildingCrossHomDimensionFive,
  "|abstractIsotypicIsomorphism=1|explicitIntertwinerBuilt=0|seesBoth=1\n");
Print("MICROVM_ACTIONS|generatorCount=", Length(Generators216Five),
  "|circuitGenerators=",
  JoinStringsWithSeparator(List(Generators216Five, generator ->
    JoinIntsFive(List([1..216], point -> point^generator))), "/"),
  "|hemiGenerators=",
  JoinStringsWithSeparator(List(Generators40Five, generator ->
    JoinIntsFive(List([1..216], point -> Position(HemiLinesFive,
      OnHemiFive(HemiLinesFive[point], generator))))), "/"),
  "|quotientGenerators=",
  JoinStringsWithSeparator(List(QuotientGeneratorsCircuitFive,
    JoinIntsFive), "/"),
  "|circuitBlockIds=", JoinIntsFive(CircuitBlockIdFive),
  "|hemiBlockIds=", JoinIntsFive(HemiBlockIdFive), "\n");
Print("FIVE_FRONT_BOUNDARY|finiteRepresentationOnly=1|physicalMixing=0",
  "|equivariant216Bijection=0|commonCoverStillAllowed=1\n");
Print("ALL_STEINBERG_DOUBLECOSET_COLOUR_SWAP_CHECKS_PASS\n");
QUIT;
