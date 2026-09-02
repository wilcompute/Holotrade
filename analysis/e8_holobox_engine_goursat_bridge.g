#############################################################################
## Exact local Goursat bridge: one radix-40 HoloBox routing digit versus the
## 20,160-state E8 control/execution chart.
##
## Scope matters.  The 40-point router has a connected simple symmetry
## PSp(4,3) of order 25,920 and a full graph automorphism group
## PGSp(4,3)=PSp(4,3):2 of order 51,840.  The E8 engine action has the already
## certified product shape PSL(3,2) x (2^5:S6).  This witness reconstructs the
## W33 graph and folded-cube factor independently, enumerates their normal
## quotients, and classifies every local subdirect coupling.
#############################################################################

if LoadPackage("grape") <> true then
  Error("GRAPE is required for the HoloBox/engine Goursat bridge");
fi;
SetInfoLevel(InfoWarning, 0);;
SizeScreen([2000, 1000]);;

BoolIntBridge := function(value)
  if value then return 1; fi;
  return 0;
end;

CanonicalProjectiveBridge := function(vector)
  local index, scale;
  for index in [1..4] do
    if vector[index] <> 0 then
      if vector[index] = 1 then scale := 1; else scale := 2; fi;
      return List(vector, entry -> (scale * entry) mod 3);
    fi;
  od;
  Error("zero vector has no projective representative");
end;

SymplecticBridge := function(left, right)
  return (left[1] * right[3] - left[3] * right[1]
        + left[2] * right[4] - left[4] * right[2]) mod 3;
end;

NonzeroVectorsBridge := Filtered(Tuples([0, 1, 2], 4),
  vector -> ForAny(vector, entry -> entry <> 0));;
PointsBridge := Set(List(NonzeroVectorsBridge, CanonicalProjectiveBridge));;
W33Bridge := Graph(Group(()), [1..40], OnPoints,
  function(first, second)
    return first <> second and
      SymplecticBridge(PointsBridge[first], PointsBridge[second]) = 0;
  end, true);;
RouterFullBridge := AutGroupGraph(W33Bridge);;
RouterConnectedBridge := DerivedSubgroup(RouterFullBridge);;
RouterNormalsBridge := NormalSubgroups(RouterFullBridge);;
RouterPointFullBridge := Stabilizer(RouterFullBridge, 1);;
RouterPointConnectedBridge := Intersection(
  RouterPointFullBridge, RouterConnectedBridge);;

CanonicalFoldedBridge := function(vector)
  local complement;
  complement := List(vector, entry -> 1 - entry);
  if vector < complement then return vector; fi;
  return complement;
end;

FoldedVectorsBridge := Set(List(Tuples([0, 1], 6),
  CanonicalFoldedBridge));;

FoldedTranslationBridge := function(index)
  return PermList(List(FoldedVectorsBridge, function(vector)
    local image;
    image := ShallowCopy(vector);
    image[index] := 1 - image[index];
    return Position(FoldedVectorsBridge, CanonicalFoldedBridge(image));
  end));
end;

FoldedSwapBridge := function(index)
  return PermList(List(FoldedVectorsBridge, function(vector)
    local image, entry;
    image := ShallowCopy(vector);
    entry := image[index];
    image[index] := image[index + 1];
    image[index + 1] := entry;
    return Position(FoldedVectorsBridge, CanonicalFoldedBridge(image));
  end));
end;

TranslationGeneratorsBridge := List([1..5], FoldedTranslationBridge);;
PermutationGeneratorsBridge := List([1..5], FoldedSwapBridge);;
TranslationCoreBridge := Group(TranslationGeneratorsBridge);;
PermutationComplementBridge := Group(PermutationGeneratorsBridge);;
ExecutionBridge := Group(Concatenation(
  TranslationGeneratorsBridge, PermutationGeneratorsBridge));;
ExecutionNormalsBridge := NormalSubgroups(ExecutionBridge);;
ExecutionIndexTwoBridge := Filtered(ExecutionNormalsBridge,
  subgroup -> Index(ExecutionBridge, subgroup) = 2);;

KernelProfileBridge := function(kernel)
  local translationIntersection, permutationIntersection, label;
  translationIntersection := Size(Intersection(kernel,
    TranslationCoreBridge));
  permutationIntersection := Size(Intersection(kernel,
    PermutationComplementBridge));
  if translationIntersection = 32 and permutationIntersection = 360 then
    label := "permutation_sign";
  elif translationIntersection = 16 and permutationIntersection = 720 then
    label := "translation_parity";
  elif translationIntersection = 16 and permutationIntersection = 360 then
    label := "translation_xor_sign";
  else
    Error("unrecognised index-two execution kernel");
  fi;
  return rec(
    label := label,
    kernel := kernel,
    order := Size(kernel),
    translationIntersection := translationIntersection,
    permutationIntersection := permutationIntersection,
    structure := StructureDescription(kernel)
  );
end;

CharacterProfilesBridge := List(ExecutionIndexTwoBridge,
  KernelProfileBridge);;
SortBy(CharacterProfilesBridge, profile -> profile.label);;

# This is an independent exhaustive cross-check of the Goursat count before
# the perfect 168-factor is restored.  SubdirectProducts returns conjugacy
# classes inside the product of the two parent permutation groups.
RouterExecutionSubdirectsBridge := SubdirectProducts(
  RouterFullBridge, ExecutionBridge);;
RouterExecutionSubdirectOrdersBridge := SortedList(List(
  RouterExecutionSubdirectsBridge, Size));;

ControlBridge := GL(3, 2);;
ControlOrderBridge := Size(ControlBridge);;
ExecutionOrderBridge := Size(ExecutionBridge);;
EngineOrderBridge := ControlOrderBridge * ExecutionOrderBridge;
ConnectedCouplingOrderBridge := Size(RouterConnectedBridge) *
  EngineOrderBridge;
FullProductOrderBridge := Size(RouterFullBridge) * EngineOrderBridge;
ParityCouplingOrderBridge := FullProductOrderBridge / 2;
LocalCarrierStatesBridge := 40 * 20160;

ChecksBridge := [
  Length(PointsBridge) = 40,
  VertexDegrees(W33Bridge) = [12],
  Size(RouterFullBridge) = 51840,
  AbelianInvariants(RouterFullBridge) = [2],
  SortedList(List(RouterNormalsBridge, Size)) = [1, 25920, 51840],
  Size(RouterConnectedBridge) = 25920,
  IsSimpleGroup(RouterConnectedBridge),
  IsPerfectGroup(RouterConnectedBridge),
  IsTransitive(RouterConnectedBridge, [1..40]),
  Size(RouterPointFullBridge) = 1296,
  Size(RouterPointConnectedBridge) = 648,
  Size(TranslationCoreBridge) = 32,
  StructureDescription(TranslationCoreBridge) =
    "C2 x C2 x C2 x C2 x C2",
  Size(PermutationComplementBridge) = 720,
  StructureDescription(PermutationComplementBridge) = "S6",
  ExecutionOrderBridge = 23040,
  AbelianInvariants(ExecutionBridge) = [2, 2],
  Size(DerivedSubgroup(ExecutionBridge)) = 5760,
  Length(ExecutionIndexTwoBridge) = 3,
  List(CharacterProfilesBridge, profile -> profile.label) =
    ["permutation_sign", "translation_parity", "translation_xor_sign"],
  List(CharacterProfilesBridge, profile ->
    [profile.translationIntersection, profile.permutationIntersection]) =
    [[32, 360], [16, 720], [16, 360]],
  ControlOrderBridge = 168,
  IsSimpleGroup(ControlBridge),
  IsPerfectGroup(ControlBridge),
  EngineOrderBridge = 3870720,
  EngineOrderBridge mod Size(RouterConnectedBridge) <> 0,
  EngineOrderBridge mod Size(RouterFullBridge) <> 0,
  Length(RouterExecutionSubdirectsBridge) = 4,
  RouterExecutionSubdirectOrdersBridge =
    [597196800, 597196800, 597196800, 1194393600],
  ConnectedCouplingOrderBridge = 100329062400,
  FullProductOrderBridge = 200658124800,
  ParityCouplingOrderBridge = ConnectedCouplingOrderBridge,
  LocalCarrierStatesBridge = 806400,
  ParityCouplingOrderBridge / LocalCarrierStatesBridge = 124416,
  FullProductOrderBridge / LocalCarrierStatesBridge = 248832
];;

if not ForAll(ChecksBridge, value -> value) then
  Print("FAILED|", List(ChecksBridge, BoolIntBridge), "\n");
  Error("HoloBox/engine Goursat bridge failed");
fi;

Print("ROUTER|vertices=40|degree=12|connected=PSp(4,3)",
      "|connectedOrder=25920|connectedSimple=1",
      "|full=PGSp(4,3)|fullOrder=51840|fullAbelianization=C2",
      "|normalOrders=1,25920,51840|pointStabilizers=648,1296\n");
Print("ENGINE|control=PSL(3,2)|controlOrder=168|controlPerfect=1",
      "|execution=2^5:S6|executionOrder=23040",
      "|executionAbelianization=C2xC2|engineOrder=3870720",
      "|engineAbelianization=C2xC2|indexTwoCharacters=3\n");
for ProfileBridge in CharacterProfilesBridge do
  Print("CHARACTER|", ProfileBridge.label,
        "|kernelOrder=", ProfileBridge.order,
        "|translationIntersection=", ProfileBridge.translationIntersection,
        "|permutationIntersection=", ProfileBridge.permutationIntersection,
        "|kernelStructure=", ProfileBridge.structure, "\n");
od;
Print("GOURSAT|connectedClasses=1|connectedKind=direct_product",
      "|fullClasses=4|fullKinds=direct_product_plus_three_C2_pullbacks",
      "|fullExecutionClassOrders=597196800,597196800,597196800,1194393600",
      "|connectedEngineOrder=100329062400",
      "|parityPullbackOrder=100329062400",
      "|fullProductOrder=200658124800\n");
Print("CARRIER|localShape=40x20160|states=806400",
      "|connectedOrParityStabilizer=124416|fullProductStabilizer=248832",
      "|routerOuterVisibleInPointStabilizer=1\n");
Print("BOUNDARY|couplingsCanonical=0|parityChoiceCount=3",
      "|dispatchable=0|recursiveParityPolicyBuilt=0",
      "|liveBindingBuilt=0\n");
Print("ALL_HOLOBOX_ENGINE_GOURSAT_BRIDGE_CHECKS_PASS\n");
QUIT;
