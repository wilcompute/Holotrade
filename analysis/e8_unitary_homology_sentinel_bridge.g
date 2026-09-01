#############################################################################
## Candidate exact bridge between the 120-state adjacency homology and the
## 40-state W33 sentinel.
##
## This file intentionally reuses the GAP-owned differential/module witness.
## It asks whether the maximal C2^5-trivial quotient (and fixed subspace) of
## the 40-dimensional logical homology is the 15-dimensional sentinel module.
#############################################################################

E8UnitaryHomologyCodeLibraryOnly := true;;
Read("analysis/e8_unitary_homology_code_w33_obstruction.g");;

BuildCoinvariantActionBridge := function(matrix, completeBasis, relationRank)
  local coordinates;
  coordinates := List(completeBasis,
    row -> SolutionMat(completeBasis, row * matrix));
  return List([relationRank + 1..Length(completeBasis)], index ->
    coordinates[index]{[relationRank + 1..Length(completeBasis)]});
end;;

BuildRoutePermutationsBridge := function(useOuter)
  if useOuter then
    return List(QuotientGeneratorsCode, permutation ->
      PreImagesRepresentative(W33RouteToS6Code, OuterS6Code(permutation)));
  fi;
  return List(QuotientGeneratorsCode, permutation ->
    PreImagesRepresentative(W33RouteToS6Code, permutation));
end;;

HomologyRankProfileBridge := function(source, target)
  local homomorphisms, coefficients, ranks, coefficient, matrix, index;
  homomorphisms := MTX.BasisModuleHomomorphisms(source, target);
  if Length(homomorphisms) > 16 then
    Error("Hom-space unexpectedly too large for exhaustive rank profile");
  fi;
  coefficients := Tuples(Elements(FCode), Length(homomorphisms));
  ranks := [];
  for coefficient in coefficients do
    matrix := NullMat(MTX.Dimension(source), MTX.Dimension(target), FCode);
    for index in [1..Length(homomorphisms)] do
      matrix := matrix + coefficient[index] * homomorphisms[index];
    od;
    Add(ranks, RankMat(matrix));
  od;
  return rec(
    dimension := Length(homomorphisms),
    rankDistribution := Collected(ranks),
    nonzeroRanks := Difference(Set(ranks), [0]));
end;;

UniversalImageDataBridge := function(source, target, targetSpace)
  local homomorphisms, allRows, matrix, row;
  homomorphisms := MTX.BasisModuleHomomorphisms(source, target);
  allRows := [];
  for matrix in homomorphisms do
    for row in matrix do Add(allRows, row); od;
  od;
  return rec(
    homDimension := Length(homomorphisms),
    universalImageRank := RankMat(allRows),
    imageContainedInTargetSpace := ForAll(allRows, row -> row in targetSpace),
    homomorphisms := homomorphisms);
end;;

SentinelSignatureBridge := function(subset, incidence)
  return JoinStringsWithSeparator(
    List([1..40], line -> String(Sum(subset, point -> incidence[line][point]))),
    ",");
end;;

# The maximal quotient on which the normal 2-core acts trivially.
CoinvariantRelationsBridge := BaseMat(Concatenation(
  List(TwoCoreHomologyActionsCode,
    matrix -> matrix - IdentityMat(40, FCode))));;
CoinvariantRelationRankBridge := RankMat(CoinvariantRelationsBridge);;
CoinvariantCompleteBasisBridge := ExtendBasisCode(
  CoinvariantRelationsBridge, IdentityMat(40, FCode));;
CoinvariantActionsBridge := List(HomologyActionsCode, matrix ->
  BuildCoinvariantActionBridge(matrix, CoinvariantCompleteBasisBridge,
    CoinvariantRelationRankBridge));;
CoinvariantModuleBridge := GModuleByMats(CoinvariantActionsBridge, FCode);;

# The C2^5-fixed submodule.  Row-vector conventions are checked explicitly.
FixedSpaceBridge := VectorSpace(FCode, IdentityMat(40, FCode));;
for MatrixBridge in TwoCoreHomologyActionsCode do
  FixedSpaceBridge := Intersection(FixedSpaceBridge,
    VectorSpace(FCode, NullspaceMat(MatrixBridge - IdentityMat(40, FCode))));
od;
FixedBasisBridge := BasisVectors(Basis(FixedSpaceBridge));;
if not ForAll(FixedBasisBridge, vector ->
  ForAll(TwoCoreHomologyActionsCode, matrix -> vector * matrix = vector)) then
  Error("fixed-space row convention failed");
fi;
FixedActionsBridge := ActionOnBasisCode(
  FixedBasisBridge, HomologyActionsCode);;
FixedModuleBridge := GModuleByMats(FixedActionsBridge, FCode);;

# Reconstruct the 45 eight-supports in the same W33 point coordinates used by
# the spread-stabilizer calculation, then generate their binary sentinel code.
W33IncidenceBridge := NullMat(40, 40);;
for LineBridge in [1..40] do
  for PointBridge in W33LinesCode[LineBridge] do
    W33IncidenceBridge[LineBridge][PointBridge] := 1;
  od;
od;
TradeDictionaryBridge := NewDictionary("", true);;
SentinelSupportsBridge := [];;
for FourBridge in Combinations([1..40], 4) do
  SignatureBridge := SentinelSignatureBridge(FourBridge, W33IncidenceBridge);;
  BucketBridge := LookupDictionary(TradeDictionaryBridge, SignatureBridge);;
  if BucketBridge = fail then
    AddDictionary(TradeDictionaryBridge, SignatureBridge,
      [ShallowCopy(FourBridge)]);
  else
    Add(BucketBridge, ShallowCopy(FourBridge));
    if Length(BucketBridge) = 2 then
      Add(SentinelSupportsBridge, Union(BucketBridge[1], BucketBridge[2]));
    elif Length(BucketBridge) > 2 then
      Error("trade signature multiplicity exceeded two");
    fi;
  fi;
od;
SentinelSupportsBridge := Set(SentinelSupportsBridge);;
SentinelWordsBridge := List(SentinelSupportsBridge, support ->
  List([1..40], point -> BitCode(point in support)));;
SentinelSpaceBridge := VectorSpace(FCode, SentinelWordsBridge);;
SentinelBasisBridge := BasisVectors(Basis(SentinelSpaceBridge));;

RoutePermutationsInnerBridge := BuildRoutePermutationsBridge(false);;
RoutePermutationsOuterBridge := BuildRoutePermutationsBridge(true);;
SentinelActionsInnerBridge := ActionOnBasisCode(SentinelBasisBridge,
  List(RoutePermutationsInnerBridge,
    permutation -> PermutationMatrixCode(permutation, 40)));;
SentinelActionsOuterBridge := ActionOnBasisCode(SentinelBasisBridge,
  List(RoutePermutationsOuterBridge,
    permutation -> PermutationMatrixCode(permutation, 40)));;
SentinelModuleInnerBridge := GModuleByMats(SentinelActionsInnerBridge, FCode);;
SentinelModuleOuterBridge := GModuleByMats(SentinelActionsOuterBridge, FCode);;

CoinvariantFactorsBridge := FactorDimensionsCode(CoinvariantModuleBridge);;
FixedFactorsBridge := FactorDimensionsCode(FixedModuleBridge);;
SentinelFactorsInnerBridge := FactorDimensionsCode(SentinelModuleInnerBridge);;
SentinelFactorsOuterBridge := FactorDimensionsCode(SentinelModuleOuterBridge);;

CoinvariantSentinelInnerIsoBridge := MTX.IsomorphismModules(
  CoinvariantModuleBridge, SentinelModuleInnerBridge);;
CoinvariantSentinelOuterIsoBridge := MTX.IsomorphismModules(
  CoinvariantModuleBridge, SentinelModuleOuterBridge);;
FixedSentinelInnerIsoBridge := MTX.IsomorphismModules(
  FixedModuleBridge, SentinelModuleInnerBridge);;
FixedSentinelOuterIsoBridge := MTX.IsomorphismModules(
  FixedModuleBridge, SentinelModuleOuterBridge);;
FixedCoinvariantIsoBridge := MTX.IsomorphismModules(
  FixedModuleBridge, CoinvariantModuleBridge);;
SentinelInnerOuterIsoBridge := MTX.IsomorphismModules(
  SentinelModuleInnerBridge, SentinelModuleOuterBridge);;

CoinvariantInnerHomBridge := HomologyRankProfileBridge(
  CoinvariantModuleBridge, SentinelModuleInnerBridge);;
InnerCoinvariantHomBridge := HomologyRankProfileBridge(
  SentinelModuleInnerBridge, CoinvariantModuleBridge);;
CoinvariantOuterHomBridge := HomologyRankProfileBridge(
  CoinvariantModuleBridge, SentinelModuleOuterBridge);;
OuterCoinvariantHomBridge := HomologyRankProfileBridge(
  SentinelModuleOuterBridge, CoinvariantModuleBridge);;
FixedCoinvariantHomBridge := HomologyRankProfileBridge(
  FixedModuleBridge, CoinvariantModuleBridge);;
CoinvariantFixedHomBridge := HomologyRankProfileBridge(
  CoinvariantModuleBridge, FixedModuleBridge);;

# Universal normal-subgroup factorisation.  Any map from homology to an
# S6-inflated point carrier must kill the C2^5 relation space; any map back
# must land in the C2^5-fixed space.  The non-formal extra claim tested here is
# that every forward image lies inside the explicit [40,15,8] sentinel code.
FullToInnerBridge := UniversalImageDataBridge(
  HomologyModuleCode, W33ModuleClassACode, SentinelSpaceBridge);;
FullToOuterBridge := UniversalImageDataBridge(
  HomologyModuleCode, W33ModuleClassBCode, SentinelSpaceBridge);;
InnerToFullHomsBridge := MTX.BasisModuleHomomorphisms(
  W33ModuleClassACode, HomologyModuleCode);;
OuterToFullHomsBridge := MTX.BasisModuleHomomorphisms(
  W33ModuleClassBCode, HomologyModuleCode);;
InnerBackRowsBridge := Concatenation(InnerToFullHomsBridge);;
OuterBackRowsBridge := Concatenation(OuterToFullHomsBridge);;
FullForwardFactorChecksBridge := ForAll(
  Concatenation(FullToInnerBridge.homomorphisms,
                FullToOuterBridge.homomorphisms), matrix ->
    CoinvariantRelationsBridge * matrix =
      NullMat(CoinvariantRelationRankBridge, 40, FCode));;
FullBackwardFixedChecksBridge :=
  ForAll(InnerBackRowsBridge, row -> row in FixedSpaceBridge) and
  ForAll(OuterBackRowsBridge, row -> row in FixedSpaceBridge);;

ExpectedBridgeFactors := [1, 1, 1, 4, 4, 4];;
BridgeChecks := [
  CoinvariantRelationRankBridge = 25,
  Dimension(FixedSpaceBridge) = 15,
  Dimension(SentinelSpaceBridge) = 15,
  Length(SentinelSupportsBridge) = 45,
  CoinvariantFactorsBridge = ExpectedBridgeFactors,
  FixedFactorsBridge = ExpectedBridgeFactors,
  SentinelFactorsInnerBridge = ExpectedBridgeFactors,
  SentinelFactorsOuterBridge = ExpectedBridgeFactors,
  CoinvariantSentinelInnerIsoBridge = fail,
  CoinvariantSentinelOuterIsoBridge = fail,
  FixedSentinelInnerIsoBridge = fail,
  FixedSentinelOuterIsoBridge = fail,
  FixedCoinvariantIsoBridge = fail,
  SentinelInnerOuterIsoBridge = fail,
  CoinvariantInnerHomBridge.dimension = 2,
  CoinvariantInnerHomBridge.nonzeroRanks = [1, 11],
  InnerCoinvariantHomBridge.dimension = 2,
  InnerCoinvariantHomBridge.nonzeroRanks = [4, 5],
  CoinvariantOuterHomBridge.dimension = 2,
  CoinvariantOuterHomBridge.nonzeroRanks = [1, 6],
  OuterCoinvariantHomBridge.dimension = 1,
  OuterCoinvariantHomBridge.nonzeroRanks = [10],
  FixedCoinvariantHomBridge.dimension = 3,
  FixedCoinvariantHomBridge.nonzeroRanks = [1, 4, 5, 6, 10],
  CoinvariantFixedHomBridge.dimension = 2,
  CoinvariantFixedHomBridge.nonzeroRanks = [1, 6],
  FullToInnerBridge.homDimension = 2,
  FullToInnerBridge.universalImageRank = 11,
  FullToInnerBridge.imageContainedInTargetSpace,
  FullToOuterBridge.homDimension = 2,
  FullToOuterBridge.universalImageRank = 6,
  FullToOuterBridge.imageContainedInTargetSpace,
  FullForwardFactorChecksBridge,
  Length(InnerToFullHomsBridge) = 2,
  RankMat(InnerBackRowsBridge) = 11,
  Length(OuterToFullHomsBridge) = 2,
  RankMat(OuterBackRowsBridge) = 6,
  FullBackwardFixedChecksBridge
];;
if not ForAll(BridgeChecks, value -> value) then
  Print("FAILED_SENTINEL_BRIDGE_CHECKS|",
        List(BridgeChecks, BoolIntCross), "\n");
  Error("unitary homology/sentinel bridge checks failed");
fi;

Print("SENTINEL_BRIDGE_DIMS|relations=", CoinvariantRelationRankBridge,
      "|coinvariants=", 40 - CoinvariantRelationRankBridge,
      "|fixed=", Dimension(FixedSpaceBridge),
      "|sentinel=", Dimension(SentinelSpaceBridge),
      "|supports=", Length(SentinelSupportsBridge), "\n");
Print("SENTINEL_BRIDGE_FACTORS|coinvariants=", CoinvariantFactorsBridge,
      "|fixed=", FixedFactorsBridge,
      "|sentinelInner=", SentinelFactorsInnerBridge,
      "|sentinelOuter=", SentinelFactorsOuterBridge, "\n");
Print("SENTINEL_BRIDGE_ISO|coinvariantInner=",
      BoolIntCross(CoinvariantSentinelInnerIsoBridge <> fail),
      "|coinvariantOuter=",
      BoolIntCross(CoinvariantSentinelOuterIsoBridge <> fail),
      "|fixedInner=", BoolIntCross(FixedSentinelInnerIsoBridge <> fail),
      "|fixedOuter=", BoolIntCross(FixedSentinelOuterIsoBridge <> fail),
      "|fixedCoinvariant=", BoolIntCross(FixedCoinvariantIsoBridge <> fail),
      "|sentinelInnerOuter=",
      BoolIntCross(SentinelInnerOuterIsoBridge <> fail),
      "\n");
Print("SENTINEL_BRIDGE_HOM|coinvariantToInnerDim=",
      CoinvariantInnerHomBridge.dimension,
      "|coinvariantToInnerRanks=", CoinvariantInnerHomBridge.nonzeroRanks,
      "|innerToCoinvariantDim=", InnerCoinvariantHomBridge.dimension,
      "|innerToCoinvariantRanks=", InnerCoinvariantHomBridge.nonzeroRanks,
      "|coinvariantToOuterDim=", CoinvariantOuterHomBridge.dimension,
      "|coinvariantToOuterRanks=", CoinvariantOuterHomBridge.nonzeroRanks,
      "|outerToCoinvariantDim=", OuterCoinvariantHomBridge.dimension,
      "|outerToCoinvariantRanks=", OuterCoinvariantHomBridge.nonzeroRanks,
      "|fixedToCoinvariantDim=", FixedCoinvariantHomBridge.dimension,
      "|fixedToCoinvariantRanks=", FixedCoinvariantHomBridge.nonzeroRanks,
      "|coinvariantToFixedDim=", CoinvariantFixedHomBridge.dimension,
      "|coinvariantToFixedRanks=", CoinvariantFixedHomBridge.nonzeroRanks,
      "\n");
Print("SENTINEL_BRIDGE_UNIVERSAL|innerForwardHomDim=",
      FullToInnerBridge.homDimension,
      "|innerUniversalImageRank=", FullToInnerBridge.universalImageRank,
      "|innerImageInSentinel=",
      BoolIntCross(FullToInnerBridge.imageContainedInTargetSpace),
      "|outerForwardHomDim=", FullToOuterBridge.homDimension,
      "|outerUniversalImageRank=", FullToOuterBridge.universalImageRank,
      "|outerImageInSentinel=",
      BoolIntCross(FullToOuterBridge.imageContainedInTargetSpace),
      "|forwardKillsO2Relations=",
      BoolIntCross(FullForwardFactorChecksBridge),
      "|innerBackwardHomDim=", Length(InnerToFullHomsBridge),
      "|innerBackwardUniversalImageRank=", RankMat(InnerBackRowsBridge),
      "|outerBackwardHomDim=", Length(OuterToFullHomsBridge),
      "|outerBackwardUniversalImageRank=", RankMat(OuterBackRowsBridge),
      "|backwardImagesInFixed=",
      BoolIntCross(FullBackwardFixedChecksBridge), "\n");
Print("ALL_UNITARY_HOMOLOGY_SENTINEL_BRIDGE_CHECKS_PASS\n");
QUIT;
