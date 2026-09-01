#############################################################################
## Exact characteristic-zero repair of the 216x540 bicolour stack theorem.
##
## The companion W33 audit obtained rank 372 modulo 1,000,003 and promoted it
## to a rational rank.  Modular rank is only a lower bound.  This GAP witness
## reconstructs both colour matrices and performs the missing exact rational
## row-space calculation, then resolves the common 60-space sector-by-sector.
#############################################################################

Read("analysis/e8_pg34_sentinel_control_plane.g");;

TripleRowsBicolour := [];;
for TripleBicolour in Combinations([1..45], 3) do
  TripleWordBicolour := Columns2[TripleBicolour[1]] +
    Columns2[TripleBicolour[2]] + Columns2[TripleBicolour[3]];
  Add(TripleRowsBicolour,
    [String(TripleWordBicolour), ShallowCopy(TripleBicolour)]);
od;
SortBy(TripleRowsBicolour, row -> row[1]);;

SixCircuitsBicolour := [];;
RunStartBicolour := 1;;
while RunStartBicolour <= Length(TripleRowsBicolour) do
  RunEndBicolour := RunStartBicolour;;
  while RunEndBicolour < Length(TripleRowsBicolour) and
        TripleRowsBicolour[RunEndBicolour + 1][1] =
          TripleRowsBicolour[RunStartBicolour][1] do
    RunEndBicolour := RunEndBicolour + 1;;
  od;
  BucketBicolour := TripleRowsBicolour{[RunStartBicolour..RunEndBicolour]};;
  for PairBicolour in Combinations(BucketBicolour, 2) do
    if IsEmpty(Intersection(PairBicolour[1][2], PairBicolour[2][2])) then
      AddSet(SixCircuitsBicolour,
        Union(PairBicolour[1][2], PairBicolour[2][2]));
    fi;
  od;
  RunStartBicolour := RunEndBicolour + 1;;
od;
if Length(SixCircuitsBicolour) <> 540 then
  Error("six-circuit shell reconstruction failed");
fi;

IncidenceBicolour := List(Circuits, five ->
  List(SixCircuitsBicolour, six ->
    BitIndicator(Length(Intersection(five, six)) = 3)));;
if Set(List(IncidenceBicolour, Sum)) <> [20] or
   Set(List(TransposedMat(IncidenceBicolour), Sum)) <> [8] then
  Error("maximal-overlap biregularity failed");
fi;

Generators45Bicolour := GeneratorsOfGroup(PSp45);;
Generators5Bicolour := List(Generators45Bicolour, generator ->
  PermList(List(Circuits, circuit -> Position(Circuits,
    Set(List(circuit, point -> point^generator))))));;
Generators6Bicolour := List(Generators45Bicolour, generator ->
  PermList(List(SixCircuitsBicolour, circuit -> Position(SixCircuitsBicolour,
    Set(List(circuit, point -> point^generator))))));;

Seed5Bicolour := 1;;
Seed6Bicolour := PositionProperty(IncidenceBicolour[Seed5Bicolour],
  value -> value = 1);;
SeedPairBicolour := (Seed5Bicolour - 1) * 540 + Seed6Bicolour;;
SeenBicolour := BlistList([1..216*540], [SeedPairBicolour]);;
QueueBicolour := [SeedPairBicolour];;
QueuePositionBicolour := 1;;
while QueuePositionBicolour <= Length(QueueBicolour) do
  EncodedBicolour := QueueBicolour[QueuePositionBicolour];;
  FiveIndexBicolour := QuoInt(EncodedBicolour - 1, 540) + 1;;
  SixIndexBicolour := RemInt(EncodedBicolour - 1, 540) + 1;;
  for GeneratorIndexBicolour in [1..Length(Generators45Bicolour)] do
    NextFiveBicolour := FiveIndexBicolour^
      Generators5Bicolour[GeneratorIndexBicolour];;
    NextSixBicolour := SixIndexBicolour^
      Generators6Bicolour[GeneratorIndexBicolour];;
    NextEncodedBicolour := (NextFiveBicolour - 1) * 540 +
      NextSixBicolour;;
    if not SeenBicolour[NextEncodedBicolour] then
      SeenBicolour[NextEncodedBicolour] := true;;
      Add(QueueBicolour, NextEncodedBicolour);;
    fi;
  od;
  QueuePositionBicolour := QueuePositionBicolour + 1;;
od;
if Length(QueueBicolour) <> 2160 then Error("colour orbit failed"); fi;

MPlusBicolour := NullMat(216, 540);;
for EncodedBicolour in QueueBicolour do
  FiveIndexBicolour := QuoInt(EncodedBicolour - 1, 540) + 1;;
  SixIndexBicolour := RemInt(EncodedBicolour - 1, 540) + 1;;
  MPlusBicolour[FiveIndexBicolour][SixIndexBicolour] := 1;;
od;
MMinusBicolour := IncidenceBicolour - MPlusBicolour;;
if Set(List(MPlusBicolour, Sum)) <> [10] or
   Set(List(TransposedMat(MPlusBicolour), Sum)) <> [4] or
   Set(List(MMinusBicolour, Sum)) <> [10] or
   Set(List(TransposedMat(MMinusBicolour), Sum)) <> [4] then
  Error("colour biregularity failed");
fi;

# This is the missing proof: RankMat over integer matrices computes exact
# characteristic-zero rank, not a modular lower bound.
RankPlusBicolour := RankMat(MPlusBicolour);;
RankMinusBicolour := RankMat(MMinusBicolour);;
StackRankBicolour := RankMat(Concatenation(
  MPlusBicolour, MMinusBicolour));;
CommonDimensionBicolour := RankPlusBicolour + RankMinusBicolour -
  StackRankBicolour;;

RationalsBicolour := Rationals;;
PlusSpaceBicolour := VectorSpace(RationalsBicolour,
  BaseMat(MPlusBicolour));;
MinusSpaceBicolour := VectorSpace(RationalsBicolour,
  BaseMat(MMinusBicolour));;
CommonSpaceBicolour := Intersection(
  PlusSpaceBicolour, MinusSpaceBicolour);;

Identity216Bicolour := IdentityMat(216);;
A30Bicolour := MPlusBicolour * TransposedMat(MPlusBicolour) -
  10 * Identity216Bicolour;;
CrossBicolour := MPlusBicolour * TransposedMat(MMinusBicolour) +
  MMinusBicolour * TransposedMat(MPlusBicolour);;
if ForAny(Flat(CrossBicolour), value -> value mod 4 <> 0) then
  Error("cross Gram is not divisible by four");
fi;
A20Bicolour := CrossBicolour / 4;;
if A30Bicolour * A20Bicolour <> A20Bicolour * A30Bicolour then
  Error("symmetric colour algebra stopped commuting");
fi;

# The already canonical 216 x 45 five-circuit incidence carrier supplies an
# independent operator on the same 216-state shell.  Keeping this construction
# inside the GAP witness makes the comparison with the bicolour sectors exact,
# rather than inferring it from matching dimensions.
CircuitIncidenceBicolour := List(Circuits, circuit ->
  List([1..45], point -> BitIndicator(point in circuit)));;
if Set(List(CircuitIncidenceBicolour, Sum)) <> [5] or
   Set(List(TransposedMat(CircuitIncidenceBicolour), Sum)) <> [24] or
   RankMat(CircuitIncidenceBicolour) <> 45 then
  Error("five-circuit incidence carrier failed");
fi;
CircuitGramBicolour := CircuitIncidenceBicolour *
  TransposedMat(CircuitIncidenceBicolour);;

SectorDataBicolour := [
  [-58, 12, -10, 15],
  [-22, 6, -4, 15],
  [-18, -4, -2, 81],
  [8, -6, 2, 20],
  [14, 0, 2, 60],
  [62, 6, 8, 24],
  [170, 30, 20, 1]
];;
TransportedSectorsBicolour := [];;
LeftSectorsBicolour := [];;
SectorCommonDimensionsBicolour := [];;
for SectorBicolour in SectorDataBicolour do
  SectorSpaceBicolour := Intersection(
    VectorSpace(RationalsBicolour,
      NullspaceMat(A30Bicolour - SectorBicolour[2] * Identity216Bicolour)),
    VectorSpace(RationalsBicolour,
      NullspaceMat(A20Bicolour - SectorBicolour[3] * Identity216Bicolour)));
  if Dimension(SectorSpaceBicolour) <> SectorBicolour[4] then
    Error("joint sector dimension failed");
  fi;
  Add(LeftSectorsBicolour, SectorSpaceBicolour);;
  TransportedSectorBicolour := VectorSpace(RationalsBicolour,
    List(BasisVectors(Basis(SectorSpaceBicolour)),
      vector -> vector * MPlusBicolour));;
  Add(TransportedSectorsBicolour, TransportedSectorBicolour);;
  Add(SectorCommonDimensionsBicolour,
    Dimension(Intersection(CommonSpaceBicolour,
      TransportedSectorBicolour)));;
od;

# The circuit Gram is the exact spectral selector for the 1+20+24 part of the
# bicolour common carrier.  Its seven scalars are tested on full rational bases.
CircuitGramScalarsBicolour := [0, 0, 0, 12, 0, 30, 120];;
for SectorIndexBicolour in [1..Length(LeftSectorsBicolour)] do
  if not ForAll(BasisVectors(Basis(
      LeftSectorsBicolour[SectorIndexBicolour])), vector ->
      vector * CircuitGramBicolour =
        CircuitGramScalarsBicolour[SectorIndexBicolour] * vector) then
    Error("five-circuit Gram scalar failed on a bicolour sector");
  fi;
od;
CircuitCarrierBicolour := VectorSpace(RationalsBicolour,
  BaseMat(TransposedMat(CircuitIncidenceBicolour)));;
CircuitSectorDimensionsBicolour := List(LeftSectorsBicolour, sector ->
  Dimension(Intersection(CircuitCarrierBicolour, sector)));;
TransportedCircuitCarrierBicolour := VectorSpace(RationalsBicolour,
  List(BasisVectors(Basis(CircuitCarrierBicolour)),
    vector -> vector * MPlusBicolour));;
TransportedCircuitCarrierMinusBicolour := VectorSpace(RationalsBicolour,
  List(BasisVectors(Basis(CircuitCarrierBicolour)),
    vector -> vector * MMinusBicolour));;
TransportedCircuitCommonDimensionBicolour := Dimension(Intersection(
  CommonSpaceBicolour, TransportedCircuitCarrierBicolour));;
TransportedCircuitMinusCommonDimensionBicolour := Dimension(Intersection(
  CommonSpaceBicolour, TransportedCircuitCarrierMinusBicolour));;

FifteenIsotypicBicolour := VectorSpace(RationalsBicolour,
  Concatenation(
    BasisVectors(Basis(TransportedSectorsBicolour[1])),
    BasisVectors(Basis(TransportedSectorsBicolour[2]))));;
FifteenCommonDimensionBicolour := Dimension(Intersection(
  CommonSpaceBicolour, FifteenIsotypicBicolour));;

ChecksBicolour := [
  RankPlusBicolour = 216,
  RankMinusBicolour = 216,
  StackRankBicolour = 372,
  CommonDimensionBicolour = 60,
  Dimension(CommonSpaceBicolour) = 60,
  SectorCommonDimensionsBicolour = [0, 0, 0, 20, 0, 24, 1],
  CircuitGramScalarsBicolour = [0, 0, 0, 12, 0, 30, 120],
  CircuitSectorDimensionsBicolour = [0, 0, 0, 20, 0, 24, 1],
  Dimension(CircuitCarrierBicolour) = 45,
  Dimension(TransportedCircuitCarrierBicolour) = 45,
  Dimension(TransportedCircuitCarrierMinusBicolour) = 45,
  TransportedCircuitCommonDimensionBicolour = 45,
  TransportedCircuitMinusCommonDimensionBicolour = 45,
  TransportedCircuitCarrierBicolour =
    TransportedCircuitCarrierMinusBicolour,
  FifteenCommonDimensionBicolour = 15,
  15 + Dimension(TransportedCircuitCarrierBicolour) = 60
];;
if not ForAll(ChecksBicolour, value -> value) then
  Print("FAILED_BICOLOUR_EXACT_CHECKS|", List(ChecksBicolour, BoolIntCross),
    "\n");
  Error("exact bicolour stack theorem failed");
fi;

Print("BICOLOUR_EXACT_RANK|rankPlus=", RankPlusBicolour,
  "|rankMinus=", RankMinusBicolour,
  "|stackRankQ=", StackRankBicolour,
  "|commonDimensionQ=", CommonDimensionBicolour, "\n");
Print("BICOLOUR_EXACT_COMMON|sectorIntersections=",
  JoinStringsWithSeparator(List(SectorCommonDimensionsBicolour, String), ","),
  "|doubled15IsotypicIntersection=", FifteenCommonDimensionBicolour,
  "|decomposition=1+15+20+24\n");
Print("BICOLOUR_CIRCUIT_BRIDGE|gramScalars=",
  JoinStringsWithSeparator(List(CircuitGramScalarsBicolour, String), ","),
  "|sectorIntersections=",
  JoinStringsWithSeparator(List(CircuitSectorDimensionsBicolour, String), ","),
  "|circuitCarrier=1+20+24|circuitDimension=45",
  "|plusTransportedIntoCommon=45|minusTransportedIntoCommon=45",
  "|plusMinusImagesEqual=1|commonComplement=15\n");
Print("BICOLOUR_EXACT_BOUNDARY|modularRankUsedAsProof=0",
  "|characteristicZeroRankComputed=1",
  "|commonIsSymmetric60Sector=0\n");
Print("ALL_SENTINEL_BICOLOUR_EXACT_STACK_RANK_CHECKS_PASS\n");
QUIT;
