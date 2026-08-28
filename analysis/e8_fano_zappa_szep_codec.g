# Exact GAP witness for the 168-state Fano control-plane address codec.
#
# The carrier is the abstract automorphism group of the Fano plane.  It is not
# a machine inventory.  Every group element is uniquely encoded as h*k with
# h in the Singer normalizer H=C7:C3 and k in the base-flag stabilizer K=D8.
# Multiplication uses the matched actions obtained by refactoring k*h; it is
# deliberately not coordinatewise multiplication in H x K.

SetInfoLevel(InfoWarning, 0);
SizeScreen([1000, 1000]);

modp := function(x, p)
  return ((x mod p) + p) mod p;
end;

PermKey := function(g)
  return List([1..7], i -> i^g);
end;

PermCsv := function(g)
  return JoinStringsWithSeparator(List(PermKey(g), String), ",");
end;

IndexOf := function(xs, x)
  local p;
  p := Position(xs, x);
  if p = fail then Error("element missing from canonical table"); fi;
  return p - 1;
end;

AddressId := function(hid, kid)
  return 8 * hid + kid;
end;

Pow2 := [1, 2, 4];
FanoDifferenceSet := [1, 2, 4];
FanoLines := Set(List([0..6], a ->
  Set(List(FanoDifferenceSet, d -> modp(a + d, 7) + 1))));

translation := PermList(List([0..6], x -> modp(x + 1, 7) + 1));
frobenius := PermList(List([0..6], x -> modp(2 * x, 7) + 1));
H := Group(translation, frobenius);

IsFanoAutomorphism := function(g)
  return Set(List(FanoLines, line -> Set(List(line, x -> x^g)))) = FanoLines;
end;

GElements := Filtered(Elements(SymmetricGroup(7)), IsFanoAutomorphism);
G := Group(GElements);

# Residue 1 on the Singer line {1,2,4}; GAP points are residues plus one.
BaseFanoPoint := 2;
BaseFanoLine := [2, 3, 5];
KElements := Filtered(GElements, g ->
  BaseFanoPoint^g = BaseFanoPoint and
  Set(List(BaseFanoLine, x -> x^g)) = Set(BaseFanoLine));
K := Group(KElements);

if Size(G) <> 168 then Error("Fano automorphism order mismatch"); fi;
if Size(H) <> 21 then Error("Singer normalizer order mismatch"); fi;
if Size(K) <> 8 then Error("flag stabilizer order mismatch"); fi;
if Size(Intersection(H, K)) <> 1 then Error("factor intersection is nontrivial"); fi;
if StructureDescription(H) <> "C7 : C3" then Error("unexpected H structure"); fi;
if StructureDescription(K) <> "D8" then Error("unexpected K structure"); fi;

# Choose a deterministic D8 chart r^i s^j by lexicographic permutation key.
rCandidates := Filtered(KElements, x -> Order(x) = 4);
SortBy(rCandidates, PermKey);
r := rCandidates[1];
sCandidates := Filtered(KElements, x ->
  Order(x) = 2 and not x in Group(r) and r^x = r^-1);
SortBy(sCandidates, PermKey);
s := sCandidates[1];

# H labels: (a,e) denotes frobenius^e * translation^a.  With GAP's right
# action this maps x to 2^e*x+a.  K labels are r^i*s^j.
HLabels := [];
HElements := [];
for a in [0..6] do
  for e in [0..2] do
    Add(HLabels, [a, e]);
    Add(HElements, frobenius^e * translation^a);
  od;
od;

KLabels := [];
KChart := [];
for j in [0..1] do
  for i in [0..3] do
    Add(KLabels, [i, j]);
    Add(KChart, r^i * s^j);
  od;
od;

if Length(Set(HElements)) <> 21 or Set(HElements) <> Set(Elements(H)) then
  Error("H chart is not bijective");
fi;
if Length(Set(KChart)) <> 8 or Set(KChart) <> Set(KElements) then
  Error("K chart is not bijective");
fi;

FlagAction := function(g, flag)
  return [flag[1]^g, Set(List(flag[2], x -> x^g))];
end;
BaseFlag := [BaseFanoPoint, Set(BaseFanoLine)];
Flags := Set(Concatenation(List(FanoLines, line ->
  List(line, point -> [point, line]))));
HFlagOrbit := Set(List(HElements, h -> FlagAction(h, BaseFlag)));
if Length(Flags) <> 21 or HFlagOrbit <> Flags then
  Error("Singer normalizer is not regular on Fano flags");
fi;

# Canonical h*k address chart and inverse lookup.
BusElements := [];
for hid in [0..20] do
  for kid in [0..7] do
    Add(BusElements, HElements[hid + 1] * KChart[kid + 1]);
  od;
od;
if Length(Set(BusElements)) <> 168 or Set(BusElements) <> Set(GElements) then
  Error("h*k address chart does not cover G uniquely");
fi;

# Exact factor lookup.  The 168-entry table is small enough that keeping this
# elementary makes the certificate independent of optional GAP packages.
Decompose := function(g)
  local pos;
  pos := Position(BusElements, g);
  if pos = fail then Error("group element cannot be decoded"); fi;
  return [QuoInt(pos - 1, 8), modp(pos - 1, 8)];
end;

HProduct := [];
for h1 in [0..20] do
  Add(HProduct, []);
  for h2 in [0..20] do
    Add(HProduct[h1 + 1], IndexOf(HElements,
      HElements[h1 + 1] * HElements[h2 + 1]));
  od;
od;

KProduct := [];
for k1 in [0..7] do
  Add(KProduct, []);
  for k2 in [0..7] do
    Add(KProduct[k1 + 1], IndexOf(KChart,
      KChart[k1 + 1] * KChart[k2 + 1]));
  od;
od;

# Matched-action table: k*h = hCross*kCross.
CrossH := [];
CrossK := [];
for kid in [0..7] do
  Add(CrossH, []);
  Add(CrossK, []);
  for hid in [0..20] do
    dec := Decompose(KChart[kid + 1] * HElements[hid + 1]);
    Add(CrossH[kid + 1], dec[1]);
    Add(CrossK[kid + 1], dec[2]);
  od;
od;

KOnHAction := Group(List([0..7], kid ->
  PermList(List([0..20], hid -> CrossH[kid + 1][hid + 1] + 1))));
HOnKAction := Group(List([0..20], hid ->
  PermList(List([0..7], kid -> CrossK[kid + 1][hid + 1] + 1))));
KOnHOrbitSizes := List(Orbits(KOnHAction, [1..21]), Length);
HOnKOrbitSizes := List(Orbits(HOnKAction, [1..8]), Length);
if Size(KOnHAction) <> 8 or KOnHOrbitSizes <> [1, 2, 4, 8, 4, 2] then
  Error("unexpected K action on H");
fi;
if Size(HOnKAction) <> 21 or HOnKOrbitSizes <> [1, 7] then
  Error("unexpected H action on K");
fi;
if IsNormal(G, H) or IsNormal(G, K) then
  Error("factorization unexpectedly degenerates to a semidirect product");
fi;

CodecProduct := function(leftId, rightId)
  local lh, lk, rh, rk, crossh, crossk, outh, outk;
  lh := QuoInt(leftId, 8); lk := modp(leftId, 8);
  rh := QuoInt(rightId, 8); rk := modp(rightId, 8);
  crossh := CrossH[lk + 1][rh + 1];
  crossk := CrossK[lk + 1][rh + 1];
  outh := HProduct[lh + 1][crossh + 1];
  outk := KProduct[crossk + 1][rk + 1];
  return AddressId(outh, outk);
end;

ProductChecks := 0;
CoordinatewiseMismatches := 0;
FirstMismatch := fail;
for leftId in [0..167] do
  for rightId in [0..167] do
    actualId := CodecProduct(leftId, rightId);
    expected := BusElements[leftId + 1] * BusElements[rightId + 1];
    if BusElements[actualId + 1] <> expected then
      Error("matched-action multiplication mismatch");
    fi;
    ProductChecks := ProductChecks + 1;
    lh := QuoInt(leftId, 8); lk := modp(leftId, 8);
    rh := QuoInt(rightId, 8); rk := modp(rightId, 8);
    naiveId := AddressId(HProduct[lh + 1][rh + 1],
                         KProduct[lk + 1][rk + 1]);
    if actualId <> naiveId then
      CoordinatewiseMismatches := CoordinatewiseMismatches + 1;
      if FirstMismatch = fail then
        FirstMismatch := [leftId, rightId, actualId, naiveId];
      fi;
    fi;
  od;
od;

# Check the compiled address table itself, not merely the ambient group law.
AssociativityChecks := 0;
for x in [0..167] do
  for y in [0..167] do
    xy := CodecProduct(x, y);
    for z in [0..167] do
      if CodecProduct(xy, z) <> CodecProduct(x, CodecProduct(y, z)) then
        Error("compiled address product is not associative");
      fi;
      AssociativityChecks := AssociativityChecks + 1;
    od;
  od;
od;

identityId := IndexOf(BusElements, One(G));
InverseIds := [];
for x in [0..167] do
  invId := IndexOf(BusElements, BusElements[x + 1]^-1);
  if CodecProduct(x, invId) <> identityId or
     CodecProduct(invId, x) <> identityId then
    Error("compiled inverse mismatch");
  fi;
  Add(InverseIds, invId);
od;

CommutingCrossPairs := 0;
for kid in [0..7] do
  for hid in [0..20] do
    if KChart[kid + 1] * HElements[hid + 1] =
       HElements[hid + 1] * KChart[kid + 1] then
      CommutingCrossPairs := CommutingCrossPairs + 1;
    fi;
  od;
od;

Print("VERSION|", GAPInfo.Version, "\n");
Print("SUMMARY|G=", Size(G), "|H=", Size(H), "|K=", Size(K),
      "|intersection=", Size(Intersection(H, K)),
      "|flags=", Length(Flags), "|identity=", identityId, "\n");
Print("STRUCTURES|G=", StructureDescription(G),
      "|H=", StructureDescription(H),
      "|K=", StructureDescription(K), "\n");
Print("BASE_FLAG|point=", BaseFanoPoint - 1,
      "|line=", JoinStringsWithSeparator(List(List(BaseFanoLine, x -> x - 1), String), ","), "\n");
Print("D8_GENERATORS|r=", PermCsv(r), "|s=", PermCsv(s), "\n");
Print("MATCHED_ACTIONS|K_on_H_image=", Size(KOnHAction),
      "|K_on_H_orbits=", JoinStringsWithSeparator(List(KOnHOrbitSizes, String), ","),
      "|H_on_K_image=", Size(HOnKAction),
      "|H_on_K_orbits=", JoinStringsWithSeparator(List(HOnKOrbitSizes, String), ","),
      "|H_normal=0|K_normal=0\n");

for hid in [0..20] do
  Print("H|", hid, "|", HLabels[hid + 1][1], "|",
        HLabels[hid + 1][2], "|", PermCsv(HElements[hid + 1]), "\n");
od;
for kid in [0..7] do
  Print("K|", kid, "|", KLabels[kid + 1][1], "|",
        KLabels[kid + 1][2], "|", PermCsv(KChart[kid + 1]), "\n");
od;
for kid in [0..7] do
  for hid in [0..20] do
    Print("CROSS|", kid, "|", hid, "|",
          CrossH[kid + 1][hid + 1], "|",
          CrossK[kid + 1][hid + 1], "\n");
  od;
od;
for x in [0..167] do
  Print("BUS|", x, "|", QuoInt(x, 8), "|", modp(x, 8), "|",
        PermCsv(BusElements[x + 1]), "|", InverseIds[x + 1], "\n");
od;

Print("CHECKS|decompositions=168|products=", ProductChecks,
      "|associativity=", AssociativityChecks,
      "|coordinatewiseMismatches=", CoordinatewiseMismatches,
      "|commutingCrossPairs=", CommutingCrossPairs, "\n");
Print("NONTRIVIAL_WITNESS|left=", FirstMismatch[1],
      "|right=", FirstMismatch[2],
      "|zappa=", FirstMismatch[3],
      "|coordinatewise=", FirstMismatch[4], "\n");
Print("ALL_FANO_ZAPPA_SZEP_CODEC_CHECKS_PASS\n");
QUIT;
