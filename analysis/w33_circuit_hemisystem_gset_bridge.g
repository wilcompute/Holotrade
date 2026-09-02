#############################################################################
## Exact PSp(4,3)-set comparison: 216 sentinel five-circuits versus the 216
## W(3,3) hemisystems modulo complementation.
#############################################################################

Read("analysis/e8_pg34_sentinel_control_plane.g");;

HemiPropagate := function(input)
  local assignment, changed, line, values, unknown, total, point;
  assignment := ShallowCopy(input);
  changed := true;
  while changed do
    changed := false;
    for line in Lines do
      values := List(line, point -> assignment[point]);
      unknown := Filtered(line, point -> assignment[point] = -1);
      total := Sum(Filtered(values, value -> value <> -1));
      if total > 2 or total + Length(unknown) < 2 then return fail; fi;
      if Length(unknown) > 0 and total = 2 then
        for point in unknown do assignment[point] := 0; od;
        changed := true;
      elif Length(unknown) > 0 and total + Length(unknown) = 2 then
        for point in unknown do assignment[point] := 1; od;
        changed := true;
      fi;
    od;
  od;
  return assignment;
end;;

PointLinesHemi := List([1..40], point ->
  Filtered([1..Length(Lines)], index -> point in Lines[index]));;
HemiSolutions := [];;

HemiSearch := function(input)
  local assignment, unknown, chosen, bestScore, point, score, lineIndex,
    branch;
  assignment := HemiPropagate(input);
  if assignment = fail then return; fi;
  unknown := Filtered([1..40], point -> assignment[point] = -1);
  if IsEmpty(unknown) then
    if Sum(assignment) <> 20 then Error("hemisystem size failed"); fi;
    Add(HemiSolutions,
      Filtered([1..40], point -> assignment[point] = 1));
    return;
  fi;
  chosen := unknown[1];
  bestScore := -1;
  for point in unknown do
    score := Sum(PointLinesHemi[point], lineIndex ->
      10 - Number(Lines[lineIndex], p -> assignment[p] = -1));
    if score > bestScore then
      chosen := point;
      bestScore := score;
    fi;
  od;
  for branch in [0, 1] do
    assignment[chosen] := branch;
    HemiSearch(assignment);
    assignment[chosen] := -1;
  od;
end;;

# One member of every complementary pair contains point 1.
InitialHemi := List([1..40], point -> -1);;
InitialHemi[1] := 1;;
HemiSearch(InitialHemi);;
HemiLines := Set(HemiSolutions);;
if Length(HemiLines) <> 216 then
  Error("hemisystem/complement-pair enumeration failed");
fi;

HemiCanonical := function(support)
  local normalized;
  normalized := Set(support);
  if 1 in normalized then return normalized; fi;
  return Difference([1..40], normalized);
end;;
OnHemiLine := function(support, permutation)
  return HemiCanonical(List(support, point -> point^permutation));
end;;

HemiOrbits := OrbitsDomain(PSpGroup, HemiLines, OnHemiLine);;
if List(HemiOrbits, Length) <> [216] then
  Error("hemisystem lines are not one PSp orbit");
fi;

Generators40Bridge := GeneratorsOfGroup(PSpGroup);;
Iso40to45Bridge := GroupHomomorphismByImages(PSpGroup, PSp45,
  Generators40Bridge, Generators45);;
if not IsBijective(Iso40to45Bridge) then
  Error("paired 40/45 PSp action is not an isomorphism");
fi;

CircuitBaseBridge := Circuits[1];;
CircuitStabilizer45Bridge := Stabilizer(PSp45,
  CircuitBaseBridge, OnSets);;
CircuitStabilizer40Bridge := PreImage(Iso40to45Bridge,
  CircuitStabilizer45Bridge);;
if Size(CircuitStabilizer40Bridge) <> 120 then
  Error("circuit stabilizer order failed");
fi;

# They are not the same inner PSp action: their order-120 stabilizers are in
# different conjugacy classes.  Test whether the outer involution in the full
# order-51840 graph automorphism group fuses those classes.
HemiStabilizerPSpBridge := Stabilizer(PSpGroup,
  HemiLines[1], OnHemiLine);;
PSpActionsConjugateBridge := IsConjugate(PSpGroup,
  CircuitStabilizer40Bridge, HemiStabilizerPSpBridge);;
if PSpActionsConjugateBridge then
  Error("unexpected inner PSp identification");
fi;

GeneratorsAut40Bridge := GeneratorsOfGroup(WAut);;
GeneratorsAut45Bridge := List(GeneratorsAut40Bridge, generator ->
  PermList(List(Supports, support -> Position(Supports,
    Set(List(support, point -> point^generator))))));;
WAut45Bridge := Group(GeneratorsAut45Bridge);;
if Size(WAut45Bridge) <> 51840 then Error("full 45-action failed"); fi;
IsoAut40to45Bridge := GroupHomomorphismByImages(WAut, WAut45Bridge,
  GeneratorsAut40Bridge, GeneratorsAut45Bridge);;
if not IsBijective(IsoAut40to45Bridge) then
  Error("paired full 40/45 action is not an isomorphism");
fi;
CircuitStabilizerAut45Bridge := Stabilizer(WAut45Bridge,
  CircuitBaseBridge, OnSets);;
CircuitStabilizerAut40Bridge := PreImage(IsoAut40to45Bridge,
  CircuitStabilizerAut45Bridge);;
if Size(CircuitStabilizerAut40Bridge) <> 240 then
  Error("full circuit stabilizer order failed");
fi;
HemiStabilizerAutBridge := Stabilizer(WAut,
  HemiLines[1], OnHemiLine);;
if Size(HemiStabilizerAutBridge) <> 240 then
  Error("full hemisystem stabilizer order failed");
fi;
AutActionsConjugateBridge := IsConjugate(WAut,
  CircuitStabilizerAut40Bridge, HemiStabilizerAutBridge);;
if AutActionsConjugateBridge then
  Error("unexpected full-automorphism identification");
fi;

ElementOrderHistogramBridge := function(group)
  return Collected(List(Elements(group), Order));
end;;
CircuitPSpOrdersBridge := ElementOrderHistogramBridge(
  CircuitStabilizer40Bridge);;
HemiPSpOrdersBridge := ElementOrderHistogramBridge(
  HemiStabilizerPSpBridge);;
CircuitAutOrdersBridge := ElementOrderHistogramBridge(
  CircuitStabilizerAut40Bridge);;
HemiAutOrdersBridge := ElementOrderHistogramBridge(
  HemiStabilizerAutBridge);;

FixedRowBridge := function(class)
  local representative, supportPermutation, circuitFixed, hemiFixed;
  representative := Representative(class);
  supportPermutation := PermList(List(Supports, support ->
    Position(Supports, Set(List(support,
      point -> point^representative)))));
  circuitFixed := Number(Circuits, circuit ->
    Set(List(circuit, point -> point^supportPermutation)) = circuit);
  hemiFixed := Number(HemiLines, hemi ->
    OnHemiLine(hemi, representative) = hemi);
  return [Order(representative), Size(class), circuitFixed, hemiFixed];
end;;
FixedRowsBridge := List(ConjugacyClasses(WAut), FixedRowBridge);;
if ForAll(FixedRowsBridge, row -> row[3] = row[4]) then
  Error("permutation characters failed to separate the actions");
fi;

CharacterDecompositionRowsBridge := function(group, circuitStabilizer,
    hemiStabilizer)
  local table, irreducibles, circuitCharacter, hemiCharacter, rows, index,
    circuitMultiplicity, hemiMultiplicity;
  table := CharacterTable(group);
  irreducibles := Irr(table);
  circuitCharacter := PermutationCharacter(group, circuitStabilizer);
  hemiCharacter := PermutationCharacter(group, hemiStabilizer);
  rows := [];
  for index in [1..Length(irreducibles)] do
    circuitMultiplicity := ScalarProduct(irreducibles[index],
      circuitCharacter);
    hemiMultiplicity := ScalarProduct(irreducibles[index], hemiCharacter);
    if circuitMultiplicity <> 0 or hemiMultiplicity <> 0 then
      Add(rows, [index, irreducibles[index][1], circuitMultiplicity,
        hemiMultiplicity]);
    fi;
  od;
  return rows;
end;;
PSpDecompositionRowsBridge := CharacterDecompositionRowsBridge(PSpGroup,
  CircuitStabilizer40Bridge, HemiStabilizerPSpBridge);;
AutDecompositionRowsBridge := CharacterDecompositionRowsBridge(WAut,
  CircuitStabilizerAut40Bridge, HemiStabilizerAutBridge);;

Print("CIRCUIT_HEMISYSTEM_GSET|circuits=216|hemisystemPairs=216",
  "|pspCircuitStabilizer=120|pspHemisystemStabilizer=120",
  "|pspActionsConjugate=0|autCircuitStabilizer=240",
  "|autHemisystemStabilizer=240|autActionsConjugate=0",
  "|equivariantBijectionExists=0\n");
Print("CIRCUIT_HEMISYSTEM_STABILIZERS|pspCircuitOrders=",
  CircuitPSpOrdersBridge, "|pspHemisystemOrders=", HemiPSpOrdersBridge,
  "|autCircuitOrders=", CircuitAutOrdersBridge,
  "|autHemisystemOrders=", HemiAutOrdersBridge, "\n");
Print("CIRCUIT_HEMISYSTEM_CHARACTER|rows=",
  JoinStringsWithSeparator(List(FixedRowsBridge, row ->
    JoinStringsWithSeparator(List(row, String), ",")), ";"), "\n");
Print("CIRCUIT_HEMISYSTEM_DECOMPOSITION|pspRows=",
  JoinStringsWithSeparator(List(PSpDecompositionRowsBridge, row ->
    JoinStringsWithSeparator(List(row, String), ",")), ";"),
  "|autRows=",
  JoinStringsWithSeparator(List(AutDecompositionRowsBridge, row ->
    JoinStringsWithSeparator(List(row, String), ",")), ";"), "\n");
Print("CIRCUIT_HEMISYSTEM_BOUNDARY|countMatchOnly=1",
  "|innerActionsIdentified=0|outerTwistRepairs=0",
  "|fullAutCharactersDiffer=1|physicalInterpretation=0\n");
Print("ALL_CIRCUIT_HEMISYSTEM_GSET_CHECKS_PASS\n");
QUIT;
