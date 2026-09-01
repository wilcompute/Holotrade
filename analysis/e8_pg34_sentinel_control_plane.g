#############################################################################
## Exact PG(3,4) polarity / W33 sentinel control plane.
##
## Reconstructs the 40x45 cross-incidence B from W(3,3), proves the full
## 2-(85,21,5) polarity identity, enumerates the binary [40,15,8] code and
## its dependency shell, and verifies the 216-circuit PSp(4,3)/S5 orbit.
#############################################################################

LoadPackage("grape");;
SizeScreen([1000000, 1000000]);;

F3 := GF(3);;
F2 := GF(2);;

NormalizeProjective := function(v)
  local first, scale;
  first := PositionProperty(v, x -> x <> Zero(F3));
  scale := v[first]^-1;
  return List(v, x -> x * scale);
end;;

SymplecticForm := function(u, v)
  return u[1]*v[2] - u[2]*v[1] + u[3]*v[4] - u[4]*v[3];
end;;

JoinInts := function(xs)
  return JoinStringsWithSeparator(List(xs, String), ",");
end;;

BitIndicator := function(condition)
  if condition then return 1; else return 0; fi;
end;;

Points := Set(List(
  Filtered(Tuples(Elements(F3), 4), v -> ForAny(v, x -> x <> Zero(F3))),
  NormalizeProjective));;
if Length(Points) <> 40 then Error("projective point count failed"); fi;

Lines := [];;
for pair in Combinations([1..40], 2) do
  if SymplecticForm(Points[pair[1]], Points[pair[2]]) = Zero(F3) then
    coeffs := Filtered(Tuples(Elements(F3), 2), c ->
      c[1] <> Zero(F3) or c[2] <> Zero(F3));;
    line := Set(List(coeffs, c -> Position(Points, NormalizeProjective(
      List([1..4], k -> c[1]*Points[pair[1]][k] + c[2]*Points[pair[2]][k])))));;
    if Length(line) = 4 then AddSet(Lines, line); fi;
  fi;
od;
if Length(Lines) <> 40 then Error("W33 line count failed"); fi;

N := NullMat(40, 40);;
A := NullMat(40, 40);;
for li in [1..40] do
  for p in Lines[li] do N[li][p] := 1; od;
  for pair in Combinations(Lines[li], 2) do
    A[pair[1]][pair[2]] := 1;
    A[pair[2]][pair[1]] := 1;
  od;
od;
if Set(List(A, Sum)) <> [12] then Error("W33 degree failed"); fi;

# Two four-subsets with the same line-incidence sum form one eight-support.
TradeDictionary := NewDictionary("", true);;
Supports := [];;
for four in Combinations([1..40], 4) do
  signature := List([1..40], l -> Sum(four, p -> N[l][p]));;
  key := JoinInts(signature);;
  bucket := LookupDictionary(TradeDictionary, key);;
  if bucket = fail then
    AddDictionary(TradeDictionary, key, [ShallowCopy(four)]);
  else
    Add(bucket, ShallowCopy(four));
    if Length(bucket) = 2 then
      Add(Supports, Union(bucket[1], bucket[2]));
    elif Length(bucket) > 2 then
      Error("trade signature multiplicity exceeded two");
    fi;
  fi;
od;
Supports := Set(Supports);;
if Length(Supports) <> 45 or Set(List(Supports, Length)) <> [8] then
  Error("45 eight-support reconstruction failed");
fi;

B := List([1..40], i -> List(Supports, S -> BitIndicator(i in S)));;
if Set(List(B, Sum)) <> [9] or
   Set(List(TransposedMat(B), Sum)) <> [8] then
  Error("cross-incidence degrees failed");
fi;

G45 := NullMat(45, 45);;
for pair in Combinations([1..45], 2) do
  if IsEmpty(Intersection(Supports[pair[1]], Supports[pair[2]])) then
    G45[pair[1]][pair[2]] := 1;
    G45[pair[2]][pair[1]] := 1;
  fi;
od;
if Set(List(G45, Sum)) <> [12] then Error("GQ(4,2) degree failed"); fi;
if B*TransposedMat(B) <>
     8*IdentityMat(40) + 2*A + List([1..40], i -> List([1..40], j -> 1)) or
   TransposedMat(B)*B <> 8*IdentityMat(45) +
     2*(List([1..45], i -> List([1..45], j -> 1)) - IdentityMat(45) - G45) or
   RankMat(B) <> 25 then
  Error("cross-incidence Gram identities failed");
fi;

H := [];;
for i in [1..40] do Add(H, Concatenation(A[i], B[i])); od;
for j in [1..45] do
  Add(H, Concatenation(List([1..40], i -> B[i][j]),
    List([1..45], k -> G45[j][k] + BitIndicator(j = k))));
od;
TargetH2 := 16*IdentityMat(85) + 5*List([1..85], i -> List([1..85], j -> 1));;
if H*H <> TargetH2 or Set(List(H, Sum)) <> [21] or
   Sum([1..85], i -> H[i][i]) <> 45 then
  Error("PG(3,4) polarity identity failed");
fi;

B2 := One(F2)*B;;
Columns2 := TransposedMat(B2);;
Sentinel := VectorSpace(F2, Columns2);;
if Dimension(Sentinel) <> 15 then Error("sentinel rank failed"); fi;

# Chiral index protection: the exact B has 35 zero modes, while a concrete
# off-diagonal perturbation reaches the rectangular maximum rank 40 and leaves
# only the unavoidable |45-40|=5.  This is finite linear algebra, not a claim
# about a physical flat band.
DiagonalPerturbation := NullMat(40, 45);;
for i in [1..40] do DiagonalPerturbation[i][i] := 1; od;
if RankMat(B + DiagonalPerturbation) <> 40 then
  Error("explicit full-rank chiral perturbation failed");
fi;
WeightEnumerator := List([0..40], i -> 0);;
MinimumWords := [];;
for word in Elements(Sentinel) do
  weight := Number(word, x -> x <> Zero(F2));;
  WeightEnumerator[weight+1] := WeightEnumerator[weight+1] + 1;
  if weight = 8 then Add(MinimumWords, word); fi;
  if weight mod 4 <> 0 then Error("code is not doubly even"); fi;
od;
if PositionProperty(WeightEnumerator{[2..41]}, x -> x <> 0) <> 8 or
   Set(MinimumWords) <> Set(Columns2) or Length(MinimumWords) <> 45 then
  Error("minimum-word identification failed");
fi;
Basis2 := BasisVectors(Basis(Sentinel));;
if not ForAll(Basis2, x -> ForAll(Basis2, y ->
  Sum([1..40], k -> x[k]*y[k]) = Zero(F2))) then
  Error("sentinel self-orthogonality failed");
fi;

# Pair metric, unique weight-12 shell, and all five-circuits.
PairDictionary := NewDictionary("", true);;
Distance12 := 0;; Distance16 := 0;; PairCollision := false;;
for pair in Combinations([1..45], 2) do
  pairWord := Columns2[pair[1]] + Columns2[pair[2]];;
  key := String(pairWord);;
  if LookupDictionary(PairDictionary, key) <> fail then PairCollision := true; fi;
  AddDictionary(PairDictionary, key, ShallowCopy(pair));
  intersection := Length(Intersection(Supports[pair[1]], Supports[pair[2]]));;
  if intersection = 2 then Distance12 := Distance12 + 1;
  elif intersection = 0 then Distance16 := Distance16 + 1;
  else Error("unexpected support intersection"); fi;
od;
if PairCollision or [Distance12, Distance16] <> [720, 270] then
  Error("minimum-shell metric failed");
fi;

Circuits := [];;
for triple in Combinations([1..45], 3) do
  tripleWord := Columns2[triple[1]] + Columns2[triple[2]] + Columns2[triple[3]];;
  pair := LookupDictionary(PairDictionary, String(tripleWord));;
  if pair <> fail and IsEmpty(Intersection(pair, triple)) then
    AddSet(Circuits, Set(Concatenation(pair, triple)));
  fi;
od;
if Length(Circuits) <> 216 then Error("five-circuit count failed"); fi;
PairCircuitCounts := NullMat(45, 45);;
for circuit in Circuits do
  for pair in Combinations(circuit, 2) do
    if Length(Intersection(Supports[pair[1]], Supports[pair[2]])) <> 2 then
      Error("five-circuit is not a GQ coclique");
    fi;
    PairCircuitCounts[pair[1]][pair[2]] := PairCircuitCounts[pair[1]][pair[2]] + 1;
    PairCircuitCounts[pair[2]][pair[1]] := PairCircuitCounts[pair[2]][pair[1]] + 1;
  od;
od;
for pair in Combinations([1..45], 2) do
  intersection := Length(Intersection(Supports[pair[1]], Supports[pair[2]]));
  if (intersection = 2 and PairCircuitCounts[pair[1]][pair[2]] <> 3) or
     (intersection = 0 and PairCircuitCounts[pair[1]][pair[2]] <> 0) then
    Error("circuit pair multiplicity failed");
  fi;
od;

# Full graph automorphisms induce PSp(4,3) on the 45 minimum words.
WGraph := Graph(Group(()), [1..40], OnPoints,
  function(i, j) return A[i][j] = 1; end, true);;
WAut := AutGroupGraph(WGraph);;
PSpGroup := DerivedSubgroup(WAut);;
if Size(WAut) <> 51840 or Size(PSpGroup) <> 25920 then
  Error("W33 automorphism orders failed");
fi;
Generators45 := List(GeneratorsOfGroup(PSpGroup), g -> PermList(List(Supports, S ->
  Position(Supports, Set(List(S, x -> x^g))))));;
PSp45 := Group(Generators45);;
CircuitOrbit := Orbit(PSp45, Circuits[1], OnSets);;
CircuitStabilizer := Stabilizer(PSp45, Circuits[1], OnSets);;
CircuitAction := Action(CircuitStabilizer, Circuits[1], OnPoints);;
if Size(PSp45) <> 25920 or Length(CircuitOrbit) <> 216 or
   Size(CircuitStabilizer) <> 120 or Size(CircuitAction) <> 120 then
  Error("PSp/S5 circuit orbit failed");
fi;

WeightTerms := Filtered([0..40], w -> WeightEnumerator[w+1] <> 0);;
Print("PG34|points=85|absolute=45|nonabsolute=40|row=21|lambda=5",
  "|trace=45|identity=H2=16I+5J|spectrum=21^1,4^45,-4^39\n");
Print("SENTINEL|length=40|dimension=15|distance=8|minimumWords=45",
  "|doublyEven=1|selfOrthogonal=1|weights=",
  JoinStringsWithSeparator(List(WeightTerms, w -> Concatenation(
    String(w), ":", String(WeightEnumerator[w+1]))), ","), "\n");
Print("SHELL|distance12=720|distance16=270|weight12Unique=720",
  "|girth=5|circuits=216|nonedgeMultiplicity=3\n");
Print("GROUP|autW33=51840|psp=25920|circuitOrbit=216",
  "|stabilizer=120|stabilizerAction=120\n");
Print("FLATBAND|rankExact=25|zeroExact=35|rankPerturbed=40",
  "|zeroPerturbed=5|indexFloor=5|extraSymmetry=30\n");
Print("SUPPORTS|", JoinStringsWithSeparator(List(Supports, JoinInts), ";"), "\n");
Print("CIRCUITS|", JoinStringsWithSeparator(List(Circuits, JoinInts), ";"), "\n");
