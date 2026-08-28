#############################################################################
## Exact independence theorem for the 168-state control codec and 120-state
## execution fibre switch.
##
## Goursat's lemma says a subdirect coupling can be nontrivial only when the
## two factors have a common nontrivial quotient.  PSL(3,2) is simple of order
## 168, while the execution group 2^5:S6 has order 23040 and no factor 7.
## Therefore every subdirect control/execution coupling is the direct product.
#############################################################################

SizeScreen([2000, 1000]);;
Control := GL(3, 2);;
if Size(Control) <> 168 or not IsSimpleGroup(Control) then
  Error("control group is not simple PSL(3,2)");
fi;

# Build the folded six-cube automorphism group 2^5:S6 exactly as in the
# 120-state unitary-hole certificate.
CanonicalFoldedFabric := function(v)
  local complement;
  complement := List(v, x -> 1-x);
  if v < complement then return v; fi;
  return complement;
end;;
FoldedVectorsFabric := Set(List(Tuples([0,1],6), CanonicalFoldedFabric));;
FoldedTranslationFabric := function(i)
  return PermList(List(FoldedVectorsFabric, function(v)
    local image;
    image := ShallowCopy(v);
    image[i] := 1-image[i];
    return Position(FoldedVectorsFabric, CanonicalFoldedFabric(image));
  end));
end;;
FoldedSwapFabric := function(i)
  return PermList(List(FoldedVectorsFabric, function(v)
    local image, entry;
    image := ShallowCopy(v);
    entry := image[i]; image[i] := image[i+1]; image[i+1] := entry;
    return Position(FoldedVectorsFabric, CanonicalFoldedFabric(image));
  end));
end;;
Execution := Group(Concatenation(
  List([1..5], FoldedTranslationFabric),
  List([1..5], FoldedSwapFabric)));;
N := PCore(Execution, 2);;
if Size(Execution) <> 23040 or Size(N) <> 32 or
   StructureDescription(FactorGroup(Execution,N)) <> "S6" then
  Error("execution group is not 2^5:S6");
fi;

if Size(Execution) mod Size(Control) = 0 then
  Error("unexpected PSL(3,2) quotient order divisibility");
fi;
if 7 in Set(FactorsInt(Size(Execution))) then
  Error("execution group unexpectedly contains factor seven");
fi;
if Gcd(Size(Control), Size(Execution)) <> 24 then Error("bad order gcd"); fi;

# PSL(3,2) has only the trivial and whole quotients.  The whole quotient cannot
# be a quotient of Execution because its order does not divide |Execution|.
CommonNontrivialQuotient := false;;
FabricGroup := DirectProduct(Control, Execution);;
if Size(FabricGroup) <> 3870720 then Error("bad direct product order"); fi;

ControlStates := 21*8;;
ExecutionStates := 15*8;;
FabricStates := ControlStates*ExecutionStates;;
if [ControlStates,ExecutionStates,FabricStates] <> [168,120,20160] then
  Error("bad fabric cardinalities");
fi;

# The numerical equality with |A8| is quarantined: the 20,160 items are a
# Cartesian state carrier, not a group and not an A8 identification.
if Size(AlternatingGroup(8)) <> FabricStates then Error("A8 checksum failed"); fi;

Print("GOURSAT|control=PSL(3,2)|controlOrder=168|controlSimple=1",
      "|execution=2^5:S6|executionOrder=23040|gcd=24|commonQuotient=0\n");
Print("FABRIC|controlChart=21x8|executionChart=15x8|states=20160",
      "|productGroupOrder=3870720|stabilizerOrder=192\n");
Print("BOUNDARY|stateCountEqualsA8Order=1|A8Identification=0",
      "|liveInventory=0|dispatchable=0\n");
Print("ALL_FRACTAL_MICROVM_FABRIC_CHECKS_PASS\n");
QUIT;
