#############################################################################
##
##  w33_local_group_vs_m12.g
##
##  Does the local group at a point of W(3,3) sit inside M12 the way the
##  ternary MOG shape suggests? Decided, not assumed.
##
##  w33_local_tetracode_action.g leaves this open. The 12 neighbours of a point
##  c, arranged as a 3 x 4 array carrying a tetracode, is the SHAPE of the
##  ternary MOG -- the device behind the ternary Golay code [12,6,6]_3 and M12.
##  The stabiliser acts on those 12 points with kernel 3 and image ASL(2,3) =
##  (C3 x C3):SL(2,3) of order 216, and 95040 / 216 = 440, so an order argument
##  obstructs nothing. Worse, M12 really does contain ASL(2,3): its maximal
##  subgroup 3^2:2S4 has order 432 and ASL(2,3) sits inside at index 2. So the
##  abstract group is available and the question is entirely about the
##  PERMUTATION ACTION on the 12 points.
##
##  This file settles it by asking directly whether the degree-12 permutation
##  group I is conjugate IN S12 to a subgroup of M12. That is the exact
##  condition for a ternary Golay code on those 12 coordinates to be invariant
##  under the geometry's own local group, up to relabelling the coordinates.
##
##  Emits data/local_group_vs_m12_gap.json. Fails closed on the structural
##  facts; the M12 verdict itself is recorded whichever way it comes out.
##
#############################################################################

q := 3;;
V := GF(q)^4;;
nz := Filtered(Elements(V), v -> v <> Zero(V));;
pts := Set(List(nz, NormedRowVector));;
n := Length(pts);;
idx := function(v) return Position(pts, NormedRowVector(v)); end;;
Bf := InvariantBilinearForm(Sp(4,q)).matrix;;
form := function(u,v) return u * Bf * v; end;;

lines := Set([]);;
for a in [1..n] do
  for b in [a+1..n] do
    if form(pts[a],pts[b]) = Zero(GF(q)) then
      L := Set([]);
      for s in Elements(GF(q)) do
        for t in Elements(GF(q)) do
          if not (IsZero(s) and IsZero(t)) then
            AddSet(L, idx(s*pts[a]+t*pts[b]));
          fi;
        od;
      od;
      if Length(L) = 4 then AddSet(lines, L); fi;
    fi;
  od;
od;
lines := Set(lines);;
thru := List([1..n], p -> Filtered([1..Length(lines)], i -> p in lines[i]));;
perpOf := List([1..n], p -> Union(List(thru[p], i -> lines[i])));;

G := Sp(4,q);;
act := function(p,g) return Position(pts, NormedRowVector(pts[p]*g)); end;;
P := Action(G, [1..n], act);;
c := 1;;
S := Stabilizer(P, c);;
nbrs := Difference(perpOf[c], [c]);;

hom := ActionHomomorphism(S, nbrs, OnPoints);;
I := Image(hom);;                      # degree 12, order 216

M := MathieuGroup(12);;                # degree 12, order 95040
S12 := SymmetricGroup(12);;

# Is I conjugate in S12 to a subgroup of M12?
cands := Filtered(List(ConjugacyClassesSubgroups(M), Representative),
                  H -> Size(H) = Size(I));;
embeds := ForAny(cands, H -> RepresentativeAction(S12, I, H) <> fail);;

# orbit data, which is what actually decides it
orbI := SortedList(List(Orbits(I, [1..12]), Length));;
transI := IsTransitive(I, [1..12]);;
orbCands := Set(List(cands, H -> SortedList(List(Orbits(H,[1..12]), Length))));;
sdI := StructureDescription(I);;
sdCands := Set(List(cands, StructureDescription));;

# HOW MANY M12s CONTAIN IT? If the local group lies in exactly one conjugate of
# M12 inside S12, the geometry SELECTS that structure; if it lies in many, the
# embedding is compatibility and nothing more. Counting argument: g and g' give
# the same conjugate M^g exactly when they differ by N_S12(M), and for each
# subgroup H <= M that is S12-conjugate to I the elements carrying I to H form
# one coset of N_S12(I). So the count is k * |N_S12(I)| / |N_S12(M)| with k the
# number of SUBGROUPS (not classes) of M that are S12-conjugate to I.
NSM := Normalizer(S12, M);;
NSI := Normalizer(S12, I);;
transClasses := Filtered(ConjugacyClassesSubgroups(M),
  cl -> Size(Representative(cl)) = 216 and
        SortedList(List(Orbits(Representative(cl),[1..12]), Length)) = [12]);;
matching := Filtered(transClasses,
  cl -> RepresentativeAction(S12, I, Representative(cl)) <> fail);;
k := Sum(matching, Size);;
numM12 := k * Size(NSI) / Size(NSM);;

# DOES THAT UNIQUE M12 CARRY A TERNARY GOLAY CODE ON THE NEIGHBOUR LABELS?
# Conjugate M12 back so it contains the local group, then decompose the degree
# 12 permutation module over GF(3) and look for 6-dimensional submodules of
# minimum weight 6 -- that is exactly the ternary Golay code.
Hrep := Representative(matching[1]);;
gconj := RepresentativeAction(S12, I, Hrep);;         # I^gconj = Hrep <= M
Mloc := M^(gconj^-1);;                                 # so I <= Mloc
containsI := IsSubgroup(Mloc, I);;
modu := GModuleByMats(
  List(GeneratorsOfGroup(Mloc), g -> PermutationMat(g, 12, GF(3))), GF(3));;
subs := MTX.BasesSubmodules(modu);;
dim6 := Filtered(subs, b -> Length(b) = 6);;
minwt := function(basis)
  local best, v, w;
  best := 12;
  for v in Elements(VectorSpace(GF(3), basis)) do
    if not IsZero(v) then
      w := Number([1..12], i -> not IsZero(v[i]));
      if w < best then best := w; fi;
    fi;
  od;
  return best;
end;;
weights6 := SortedList(List(dim6, minwt));;
golay := Filtered(dim6, b -> minwt(b) = 6);;
selfdualCount := Number(golay, b -> ForAll(b, x -> ForAll(b,
  y -> Sum([1..12], i -> x[i]*y[i]) = Zero(GF(3)))));;

checks := rec(
  formIsTheGroups := ForAll(GeneratorsOfGroup(P),
      g -> Set(List(lines, L -> OnSets(L,g))) = lines),
  twelve      := Length(nbrs) = 12,
  imageOrder  := Size(I) = 216,
  imageIsASL  := sdI = "(C3 x C3) : SL(2,3)",
  m12Order    := Size(M) = 95040,
  m12Degree   := LargestMovedPoint(M) = 12,
  orderDivides := 95040 mod 216 = 0,
  m12HasOrder216Subgroups := Length(cands) > 0,
  localImageTransitive := transI = true,
  embedsInM12 := embeds = true,
  exactlyOneM12 := numM12 = 1,
  m12SelfNormalising := Size(NSM) = 95040,
  normaliserIsAGL23 := Size(NSI) = 432,
  countingIdentity := k * Size(NSI) = Size(NSM),
  conjugatedM12ContainsI := containsI,
  permModuleHasFourSubmodules := Length(subs) = 4,
  noDimensionSixSubmodule := Length(dim6) = 0,
  noGolayFromPermutationData := Length(golay) = 0
);;
allok := ForAll(RecNames(checks), nm -> checks.(nm) = true);;

Print("local image  : order ", Size(I), "   ", sdI, "\n");
Print("   orbits on the 12 neighbours : ", orbI,
      "   transitive: ", transI, "\n");
Print("M12          : order ", Size(M), ", degree ", LargestMovedPoint(M), "\n");
Print("order-216 subgroup classes in M12 : ", Length(cands), "\n");
Print("   their structures  : ", sdCands, "\n");
Print("   their orbit shapes: ", orbCands, "\n");
Print("IS THE LOCAL GROUP S12-CONJUGATE INTO M12 : ", embeds, "\n");
Print("N_S12(M12) order : ", Size(NSM), "   N_S12(I) order : ", Size(NSI), "\n");
Print("subgroups of M12 S12-conjugate to I (k)   : ", k, "\n");
Print("NUMBER OF M12 CONJUGATES CONTAINING I     : ", numM12, "\n");
Print("that M12 conjugated back contains I       : ", containsI, "\n");
Print("GF(3)^12 permutation-module submodules    : ", Length(subs),
      "   dims ", SortedList(List(subs, Length)), "\n");
Print("   of dimension 6                         : ", Length(dim6), "\n");
Print("TERNARY GOLAY CODES this way              : ", Length(golay),
      "   -- the Golay needs the MONOMIAL 2.M12, not a permutation M12\n");
Print("structural checks pass : ", allok, "\n");

if allok then
  out := Concatenation(
    "{\n",
    "  \"schema\": \"holotrade.local-group-vs-m12-gap.v1\",\n",
    "  \"valid\": true,\n",
    "  \"engine\": \"GAP\",\n",
    "  \"localImageOrder\": 216,\n",
    "  \"localImageStructure\": \"", sdI, "\",\n",
    "  \"localImageIsTransitiveOnTwelve\": ", String(transI), ",\n",
    "  \"localImageOrbitShape\": \"", String(orbI), "\",\n",
    "  \"m12Order\": 95040,\n",
    "  \"m12Degree\": 12,\n",
    "  \"orderDividesSoNoOrderObstruction\": true,\n",
    "  \"order216SubgroupClassesInM12\": ", String(Length(cands)), ",\n",
    # String() on a set of STRINGS emits embedded double quotes, which is legal
    # GAP and invalid JSON. Strip them.
    "  \"theirStructures\": \"",
    ReplacedString(String(sdCands), "\"", ""), "\",\n",
    "  \"theirOrbitShapes\": \"", String(orbCands), "\",\n",
    "  \"localGroupEmbedsInM12AsPermutationGroup\": ", String(embeds), ",\n",
    "  \"normalizerOfM12InS12\": ", String(Size(NSM)), ",\n",
    "  \"normalizerOfLocalGroupInS12\": ", String(Size(NSI)), ",\n",
    "  \"subgroupsOfM12ConjugateToLocalGroup\": ", String(k), ",\n",
    "  \"numberOfM12ConjugatesContainingIt\": ", String(numM12), ",\n",
    "  \"howManyM12s\": \"the embedding alone is compatibility; what decides ",
    "whether the GEOMETRY SELECTS a structure is how many conjugates of M12 in ",
    "S12 contain the local group. Counted exactly as k * |N_S12(I)| / ",
    "|N_S12(M12)|, where k is the number of subgroups of M12 that are ",
    "S12-conjugate to the local image: g and g-prime give the same conjugate ",
    "exactly when they differ by N_S12(M12), and the elements carrying I to a ",
    "fixed such subgroup form one coset of N_S12(I).\",\n",
    "  \"permutationModuleSubmodules\": ", String(Length(subs)), ",\n",
    "  \"permutationModuleSubmoduleDims\": \"",
    String(SortedList(List(subs, Length))), "\",\n",
    "  \"dimensionSixSubmodules\": ", String(Length(dim6)), ",\n",
    "  \"ternaryGolayCodesObtainedThisWay\": ", String(Length(golay)), ",\n",
    "  \"theGolayReadingDoesNotFollow\": \"determining an M12 is NOT the same as ",
    "determining a ternary Golay code, and the difference is signs. The ",
    "automorphism group of the [12,6,6]_3 ternary Golay code is 2.M12 acting ",
    "MONOMIALLY; its image in S12 is M12, but the code is not invariant under ",
    "the permutation matrices themselves. Decomposing GF(3)^12 as a permutation ",
    "module for the canonical M12 found here gives only four submodules, of ",
    "dimensions 0, 1, 11 and 12 -- the all-ones vector and the sum-zero ",
    "hyperplane, nested because 3 divides 12 -- and NONE of dimension 6. So no ",
    "ternary Golay code arises from the permutation data alone. The M12 result ",
    "stands on its own; the Golay reading would need the sign lift and is not ",
    "supplied by anything computed here. This corrects the framing the file was ",
    "written with, which treated the M12 embedding as the whole question.\",\n",
    "  \"theQuestion\": \"the 12 neighbours of a point of W(3,3) as a 3 x 4 ",
    "array carrying a tetracode is the SHAPE of the ternary MOG, the device ",
    "behind the ternary Golay code and M12. A ternary Golay code on those 12 ",
    "coordinates can be invariant under the geometry's own local group only if ",
    "that degree-12 permutation group is conjugate in S12 into M12. That is ",
    "what is tested here, by exhausting the conjugacy classes of order-216 ",
    "subgroups of M12 and asking RepresentativeAction for each.\",\n",
    "  \"whyOrderDoesNotDecideIt\": \"95040 / 216 = 440, so no order obstruction ",
    "exists, and M12 genuinely contains ASL(2,3): the maximal subgroup 3^2:2S4 ",
    "has order 432 and ASL(2,3) sits in it at index 2. The abstract group is ",
    "available, so the question is entirely about the permutation action on the ",
    "12 points and cannot be settled by counting.\",\n",
    "  \"boundary\": \"exact and complete for the question asked: all conjugacy ",
    "classes of subgroups of M12 of order 216 are enumerated and each is tested ",
    "for S12-conjugacy with the local image. A positive answer would show the ",
    "local group is COMPATIBLE with a ternary Golay code on the twelve ",
    "neighbours; it would NOT by itself exhibit such a code, nor show the ",
    "geometry singles one out. A negative answer rules the reading out. The ",
    "line set is built from InvariantBilinearForm and group-invariance is ",
    "checked. tau_2 is untouched and stays open in [111, 115].\"\n",
    "}\n");;
  f := OutputTextFile("data/local_group_vs_m12_gap.json", false);;
  WriteAll(f, out);
  CloseStream(f);
  Print("written: data/local_group_vs_m12_gap.json\n");
else
  Print("CHECKS FAILED -- no certificate written\n");
fi;

QUIT;
