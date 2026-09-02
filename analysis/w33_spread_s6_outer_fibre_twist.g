#############################################################################
## The two nonconjugate 216 actions over the common 36-spread quotient.
##
## The previous double-coset certificate proves that the circuit-216 and
## hemisystem-216 actions share a rank-36 valency-6 relation, hence both fibre
## six-to-one over the same degree-36 spread action.  The spread stabilizer has
## order 720 and structure S6.
##
## This script asks the sharper question suggested by that factorisation:
## inside one common spread stabilizer H ~= S6, are the two six-point fibres
## the two nonconjugate index-six S5 actions?  If so they are interchanged by
## the exceptional outer automorphism of S6.  We then check that inducing those
## two S5 fibre types back to G=PSp4(3) gives the complementary 81/64 selector
## pattern already seen globally.
#############################################################################

Read("analysis/e8_pg34_sentinel_control_plane.g");;

Gens40 := GeneratorsOfGroup(PSpGroup);;
Gens45 := Generators45;;

# Circuit degree-216 action.
Gens216 := List(Gens45, generator ->
  PermList(List(Circuits, circuit -> Position(Circuits,
    Set(List(circuit, point -> point^generator))))));;
CircuitGroup := Group(Gens216);;
Iso40to216 := GroupHomomorphismByImages(PSpGroup, CircuitGroup,
  Gens40, Gens216);;
if not IsBijective(Iso40to216) or Size(CircuitGroup) <> 25920 then
  Error("circuit action crosswalk failed");
fi;

# Hemisystem degree-216 action.
HemiSeed := [1,2,3,4,6,8,9,10,16,17,18,21,25,27,28,29,34,35,37,40];;
HemiCanonical := function(support)
  local normalized;
  normalized := Set(support);
  if 1 in normalized then return normalized; fi;
  return Difference([1..40], normalized);
end;;
OnHemi := function(support, permutation)
  return HemiCanonical(List(support, point -> point^permutation));
end;;
HemiLines := List(Orbit(PSpGroup,HemiCanonical(HemiSeed),OnHemi),ShallowCopy);;
Sort(HemiLines);;
if Length(HemiLines) <> 216 then Error("hemisystem orbit failed"); fi;

# Reconstruct the smallest circuit-to-hemi double-coset relation.  Its 36
# repeated row supports and 36 repeated column supports are the common spread
# blocks, each of size six.
CircuitStab := Stabilizer(CircuitGroup,1);;
CircuitStab40 := PreImage(Iso40to216,CircuitStab);;
HemiOrbits := List(OrbitsDomain(CircuitStab40,HemiLines,OnHemi),ShallowCopy);;
SortBy(HemiOrbits,orbit -> [Length(orbit),orbit[1]]);;
if Length(HemiOrbits) <> 5 then Error("five double cosets failed"); fi;
O := HemiOrbits[1];;
if Length(O) <> Minimum(List(HemiOrbits,Length)) then Error("smallest orbit failed"); fi;

R := NullMat(216,216);;
for s in [1..216] do
  t := RepresentativeAction(CircuitGroup,1,s,OnPoints);;
  g40 := PreImage(Iso40to216,t);;
  for h in O do
    image := OnHemi(h,g40);
    R[s][Position(HemiLines,image)] := 1;
  od;
od;
if Set(List(R,Sum)) <> [6] or Set(List(TransposedMat(R),Sum)) <> [6] then
  Error("expected valency-six relation failed");
fi;
RowTypes := Set(R);;
CircuitBlocks := List(RowTypes,row -> Filtered([1..216],i -> R[i]=row));;
HemiBlocks := List(RowTypes,row -> Filtered([1..216],i -> row[i]=1));;
if Length(RowTypes) <> 36 or Set(List(CircuitBlocks,Length)) <> [6] or
   Set(List(HemiBlocks,Length)) <> [6] then
  Error("36-by-six block system failed");
fi;

# Pick one common spread block.  Its stabilizer is S6.
CF := CircuitBlocks[1];;
HF := HemiBlocks[1];;
H := Stabilizer(CircuitGroup,CF,OnSets);;
H40 := PreImage(Iso40to216,H);;
if Size(H) <> 720 or StructureDescription(H) <> "S6" then
  Error("spread stabilizer is not S6");
fi;
if Set(Orbit(H,CF[1],OnPoints)) <> Set(CF) then
  Error("circuit fibre is not transitive");
fi;
if Set(Orbit(H40,HemiLines[HF[1]],OnHemi)) <>
   Set(List(HF,i -> HemiLines[i])) then
  Error("hemi fibre is not transitive");
fi;

Kc := Stabilizer(H,CF[1],OnPoints);;
Kh40 := Stabilizer(H40,HemiLines[HF[1]],OnHemi);;
Kh := Image(Iso40to216,Kh40);;
if Size(Kc) <> 120 or Size(Kh) <> 120 or
   StructureDescription(Kc) <> "S5" or StructureDescription(Kh) <> "S5" then
  Error("fibre point stabilizers are not S5");
fi;
SameInnerClass := IsConjugate(H,Kc,Kh);;
if SameInnerClass then
  Error("two six-point fibres unexpectedly use the same S5 class");
fi;

# Permutation characters inside H.  Each six-point action is doubly transitive,
# so 1+5; if the two 5-dimensional constituents differ then the cross scalar
# product is exactly one (only the common trivial constituent survives).
Pc := PermutationCharacter(H,Kc);;
Ph := PermutationCharacter(H,Kh);;
SelfC := ScalarProduct(Pc,Pc);;
SelfH := ScalarProduct(Ph,Ph);;
Cross := ScalarProduct(Pc,Ph);;
if SelfC <> 2 or SelfH <> 2 or Cross <> 1 then
  Error("outer-twisted six-point character pattern failed");
fi;

# Induce the two fibre stabilizers to the full group and recover the selector
# swap on the two building-homology irreducibles.
Kc40 := PreImage(Iso40to216,Kc);;
PcG := PermutationCharacter(PSpGroup,Kc40);;
PhG := PermutationCharacter(PSpGroup,Kh40);;
T := CharacterTable(PSpGroup);;
I := Irr(T);;
D64 := Filtered([1..Length(I)],i -> I[i][1]=64);;
D81 := Filtered([1..Length(I)],i -> I[i][1]=81);;
if Length(D64) < 1 or Length(D81) < 1 then Error("64/81 characters absent"); fi;
MC64 := Sum(D64,i -> ScalarProduct(I[i],PcG));;
MH64 := Sum(D64,i -> ScalarProduct(I[i],PhG));;
MC81 := Sum(D81,i -> ScalarProduct(I[i],PcG));;
MH81 := Sum(D81,i -> ScalarProduct(I[i],PhG));;
if [MC64,MH64,MC81,MH81] <> [0,1,1,0] then
  Error("global 64/81 selector swap failed");
fi;

Print("SPREAD S6 OUTER FIBRE TWIST: PASS\n");
Print("  H order/structure: ",Size(H)," / ",StructureDescription(H),"\n");
Print("  fibre point stabilizers: ",StructureDescription(Kc)," and ",
  StructureDescription(Kh),", conjugate in H = ",SameInnerClass,"\n");
Print("  six-point permutation character scalar products: ",
  [SelfC,SelfH,Cross],"\n");
Print("  induced multiplicities [c64,h64,c81,h81] = ",
  [MC64,MH64,MC81,MH81],"\n");

out := rec(
  schema := "holotrade.w33-spread-s6-outer-fibre-twist.v1",
  valid := true,
  groupOrder := Size(PSpGroup),
  quotientDegree := 36,
  fibreDegree := 6,
  spreadStabilizerOrder := Size(H),
  spreadStabilizerStructure := StructureDescription(H),
  circuitFibreStabilizerOrder := Size(Kc),
  hemiFibreStabilizerOrder := Size(Kh),
  circuitFibreStabilizerStructure := StructureDescription(Kc),
  hemiFibreStabilizerStructure := StructureDescription(Kh),
  fibreS5SubgroupsConjugateInsideS6 := SameInnerClass,
  permutationCharacterScalarProducts := [SelfC,SelfH,Cross],
  inducedMultiplicity64 := [MC64,MH64],
  inducedMultiplicity81 := [MC81,MH81],
  theorem := Concatenation(
    "The two 216-state PSp4(3) actions are G/S5 actions over one common 36-state spread quotient G/S6. ",
    "Inside the spread stabilizer S6 their six-state fibres have point stabilizers in the two nonconjugate S5 classes. ",
    "Equivalently, the fibres are the two inequivalent six-point S6 actions exchanged by the exceptional outer automorphism. ",
    "Inducing the two S5 types to PSp4(3) gives the complementary selector pattern: circuit sees 81 and not 64, hemisystem sees 64 and not 81."),
  boundary := Concatenation(
    "The outer-automorphism statement is finite permutation-group structure. ",
    "It does not identify the two fibre types with physical flavours, generations, or dynamical dualities."));;
PrintTo("data/w33_spread_s6_outer_fibre_twist.json",out,"\n");
QUIT;
