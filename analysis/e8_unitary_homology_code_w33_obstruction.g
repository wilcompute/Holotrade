#############################################################################
## Exact code and module structure of the characteristic-two differential.
##
## Starting from the GAP-owned 120-state graph adjacency A, this witness:
##   * proves the image is a 40-dimensional doubly-even self-orthogonal code
##     and its dual/kernel has dimension 80; the paired JavaScript freezer
##     proves their respective minimum distances 16 and 8 exhaustively;
##   * exposes a 15+25 decomposition that lets the JavaScript freezer
##     enumerate all 2^40 image words without sampling;
##   * computes the F2[2^5:S6] composition factors of image, homology, and
##     coimage with GAP's MeatAxe;
##   * rebuilds the genuine 40 points of W(3,3), restricts them to a spread
##     stabilizer S6, and exhausts both inner/outer S6 identifications.
#############################################################################

SizeScreen([4000, 1000]);;
E8CrossPrimeLibraryOnly := true;;
Read("analysis/e8_unitary_crossprime_fibre_differential.g");;
RCode := CrossPrimeFibreDifferential();;
FCode := GF(2);;
ACode := RCode.adjacencyF2;;

BitCode := function(value)
  if value then return One(FCode); fi;
  return Zero(FCode);
end;;

WeightCode := vector -> Number(vector, value -> value = One(FCode));;

ExtendBasisCode := function(subbasis, spanning)
  local basis, rank, row;
  basis := ShallowCopy(subbasis);
  rank := RankMat(basis);
  for row in spanning do
    if RankMat(Concatenation(basis, [row])) > rank then
      Add(basis, row);
      rank := rank + 1;
    fi;
  od;
  return basis;
end;;

ActionOnBasisCode := function(basis, ambientActions)
  return List(ambientActions, matrix ->
    List(basis, row -> SolutionMat(basis, row * matrix)));
end;;

PermutationMatrixCode := function(permutation, degree)
  return List([1..degree], i ->
    List([1..degree], j -> BitCode(j = i^permutation)));
end;;

FibreWordCode := function(indices)
  local word, index;
  word := List([1..120], ignored -> Zero(FCode));
  for index in indices do word[index] := One(FCode); od;
  return word;
end;;

ImageBasisCode := BaseMat(ACode);;
KernelBasisCode := BaseMat(NullspaceMat(ACode));;
if Length(ImageBasisCode) <> 40 or Length(KernelBasisCode) <> 80 then
  Error("unexpected image/kernel dimensions");
fi;
if ImageBasisCode * TransposedMat(ImageBasisCode)
   <> NullMat(40, 40, FCode) then
  Error("image code is not self-orthogonal");
fi;
if not ForAll(ImageBasisCode, row -> WeightCode(row) mod 4 = 0) then
  Error("image basis is not doubly even");
fi;
if RankMat(Concatenation(ImageBasisCode, KernelBasisCode)) <> 80 then
  Error("image is not contained in kernel");
fi;

# A structured 15-dimensional image subcode.  Fourteen generators flip an
# even number of complete fibres; the fifteenth chooses one K4,4 half in every
# fibre.  Its 25-dimensional complement is the exhaustive-enumeration handle.
FullFibreWordsCode := List(RCode.blocks, FibreWordCode);;
EvenFibreWordsCode := List([2..15], i ->
  FullFibreWordsCode[1] + FullFibreWordsCode[i]);;
LocalHalfWordsCode := [];;
for block in RCode.blocks do
  vertex := block[1];
  half := Intersection(Adjacency(RCode.graph, vertex), block);
  Add(LocalHalfWordsCode, FibreWordCode(half));
  Add(LocalHalfWordsCode, FibreWordCode(Difference(block, half)));
od;
LocalIntersectionCode := Intersection(
  VectorSpace(FCode, ImageBasisCode),
  VectorSpace(FCode, LocalHalfWordsCode));;
GlobalHalfCode := First(BasisVectors(Basis(LocalIntersectionCode)), word ->
  ForAll(RCode.blocks, block ->
    Number(block, index -> word[index] = One(FCode)) = 4));;
if GlobalHalfCode = fail then Error("global half word not recovered"); fi;
StructuredSubcode := Concatenation(EvenFibreWordsCode, [GlobalHalfCode]);;
if RankMat(StructuredSubcode) <> 15 or
   RankMat(Concatenation(ImageBasisCode, StructuredSubcode)) <> 40 then
  Error("15-dimensional structured subcode failed");
fi;
CompleteImageBasisCode := ShallowCopy(StructuredSubcode);;
TransversalBasisCode := [];;
rankCode := 15;;
for row in ImageBasisCode do
  if RankMat(Concatenation(CompleteImageBasisCode, [row])) > rankCode then
    Add(CompleteImageBasisCode, row);
    Add(TransversalBasisCode, row);
    rankCode := rankCode + 1;
  fi;
od;
if rankCode <> 40 or Length(TransversalBasisCode) <> 25 then
  Error("25-dimensional transversal basis failed");
fi;

# Exact F2[2^5:S6] actions on image, homology, and coimage.
ExecutionGeneratorsCode := GeneratorsOfGroup(RCode.cosetAction);;
ExecutionMatricesCode := List(ExecutionGeneratorsCode,
  generator -> PermutationMatrixCode(generator, 120));;
KernelCompleteBasisCode := ExtendBasisCode(ImageBasisCode, KernelBasisCode);;
AmbientCompleteBasisCode := ExtendBasisCode(
  KernelBasisCode, IdentityMat(120, FCode));;
ImageActionsCode := ActionOnBasisCode(ImageBasisCode, ExecutionMatricesCode);;
KernelActionsCode := ActionOnBasisCode(
  KernelCompleteBasisCode, ExecutionMatricesCode);;
HomologyActionsCode := List(KernelActionsCode, matrix ->
  List([41..80], i -> matrix[i]{[41..80]}));;
AmbientActionsCode := ActionOnBasisCode(
  AmbientCompleteBasisCode, ExecutionMatricesCode);;
CoimageActionsCode := List(AmbientActionsCode, matrix ->
  List([81..120], i -> matrix[i]{[81..120]}));;

ImageModuleCode := GModuleByMats(ImageActionsCode, FCode);;
HomologyModuleCode := GModuleByMats(HomologyActionsCode, FCode);;
CoimageModuleCode := GModuleByMats(CoimageActionsCode, FCode);;
FactorDimensionsCode := module -> SortedList(List(
  MTX.CompositionFactors(module), factor -> MTX.Dimension(factor)));;
ImageFactorsCode := FactorDimensionsCode(ImageModuleCode);;
HomologyFactorsCode := FactorDimensionsCode(HomologyModuleCode);;
CoimageFactorsCode := FactorDimensionsCode(CoimageModuleCode);;
ImageCoimageIsoCode :=
  MTX.IsomorphismModules(ImageModuleCode, CoimageModuleCode) <> fail;;
ImageHomologyIsoCode :=
  MTX.IsomorphismModules(ImageModuleCode, HomologyModuleCode) <> fail;;

TwoCoreCode := PCore(RCode.cosetAction, 2);;
TwoCoreMatricesCode := List(Elements(TwoCoreCode),
  generator -> PermutationMatrixCode(generator, 120));;
TwoCoreHomologyActionsCode := List(
  ActionOnBasisCode(KernelCompleteBasisCode, TwoCoreMatricesCode),
  matrix -> List([41..80], i -> matrix[i]{[41..80]}));;
TwoCoreImageActionsCode := ActionOnBasisCode(
  ImageBasisCode, TwoCoreMatricesCode);;
FixedDimensionCode := function(actions)
  local stacked;
  stacked := Concatenation(List(actions, matrix ->
    TransposedMat(matrix - IdentityMat(40, FCode))));
  return 40 - RankMat(stacked);
end;;
CoinvariantDimensionCode := actions -> 40 - RankMat(Concatenation(
  List(actions, matrix -> matrix - IdentityMat(40, FCode))));;
HomologyMoveRankListCode := List(TwoCoreHomologyActionsCode, matrix ->
  RankMat(matrix - IdentityMat(40, FCode)));;
ImageMoveRankListCode := List(TwoCoreImageActionsCode, matrix ->
  RankMat(matrix - IdentityMat(40, FCode)));;
HomologyMoveRanksCode := Set(HomologyMoveRankListCode);;
ImageMoveRanksCode := Set(ImageMoveRankListCode);;
HomologyMoveRankDistributionCode := Collected(HomologyMoveRankListCode);;
ImageMoveRankDistributionCode := Collected(ImageMoveRankListCode);;
HomologyFixedCode := FixedDimensionCode(TwoCoreHomologyActionsCode);;
HomologyCoinvariantsCode :=
  CoinvariantDimensionCode(TwoCoreHomologyActionsCode);;
ImageFixedCode := FixedDimensionCode(TwoCoreImageActionsCode);;
ImageCoinvariantsCode := CoinvariantDimensionCode(TwoCoreImageActionsCode);;

# Recover the literal S6 quotient permutation on the six duad labels.
DuadsCode := Combinations([1..6], 2);;
S6Code := SymmetricGroup(6);;
DuadPermutationCode := permutation -> PermList(List(DuadsCode, duad ->
  Position(DuadsCode, Set(List(duad, x -> x^permutation)))));;
DuadActionTableCode := List(Elements(S6Code), permutation ->
  [DuadPermutationCode(permutation), permutation]);;
BuildQuotientGeneratorsCode := function()
  local quotientGenerators, generator, blockPermutation, duadPermutation;
  quotientGenerators := [];
  for generator in ExecutionGeneratorsCode do
    blockPermutation := PermList(List(RCode.blocks, block ->
      Position(RCode.blocks, Set(List(block, x -> x^generator)))));
    duadPermutation := PermList(List([1..15], duadId ->
      ((duadId^(RCode.zeroToDuad^-1))^blockPermutation)
        ^RCode.zeroToDuad));
    Add(quotientGenerators,
      First(DuadActionTableCode,
        pair -> pair[1] = duadPermutation)[2]);
  od;
  return quotientGenerators;
end;;
QuotientGeneratorsCode := BuildQuotientGeneratorsCode();;
if Size(Group(QuotientGeneratorsCode)) <> 720 then
  Error("execution quotient is not the literal duad S6");
fi;
ExecutionQuotientMapCode := GroupHomomorphismByImages(
  RCode.cosetAction, S6Code,
  ExecutionGeneratorsCode, QuotientGeneratorsCode);;
if ExecutionQuotientMapCode = fail or
   Kernel(ExecutionQuotientMapCode) <> TwoCoreCode then
  Error("literal S6 quotient does not have the certified 2-core kernel");
fi;

# Rebuild genuine W(3,3)=PG(3,3) with symplectic collinearity.
W33CanonicalCode := function(vector)
  local position;
  position := PositionProperty(vector, value -> value <> 0);
  if vector[position] = 2 then
    return List(vector, value -> (2 * value) mod 3);
  fi;
  return ShallowCopy(vector);
end;;
W33FormCode := function(left, right)
  return (left[1]*right[3] - left[3]*right[1]
        + left[2]*right[4] - left[4]*right[2]) mod 3;
end;;
W33PointsCode := Set(List(
  Filtered(Tuples([0..2], 4), vector -> ForAny(vector, value -> value <> 0)),
  W33CanonicalCode));;
W33LinesCode := Filtered(Combinations([1..40], 4), candidate ->
  ForAll(Combinations(candidate, 2), pair ->
    W33FormCode(W33PointsCode[pair[1]], W33PointsCode[pair[2]]) = 0));;
W33TransvectionCode := function(vector)
  return PermList(List(W33PointsCode, point -> Position(W33PointsCode,
    W33CanonicalCode(List([1..4], i ->
      (point[i] + W33FormCode(point, vector) * vector[i]) mod 3)))));
end;;
W33PointGeneratorsCode := Set(List(W33PointsCode, W33TransvectionCode));;
W33PointGroupCode := Group(W33PointGeneratorsCode);;
W33LinePermutationCode := generator -> PermList(List(W33LinesCode, line ->
  Position(W33LinesCode, Set(List(line, point -> point^generator)))));;
W33LineGeneratorsCode := List(
  W33PointGeneratorsCode, W33LinePermutationCode);;
W33LineGroupCode := Group(W33LineGeneratorsCode);;
W33LineMapCode := GroupHomomorphismByImages(
  W33PointGroupCode, W33LineGroupCode,
  W33PointGeneratorsCode, W33LineGeneratorsCode);;
W33PointLinesCode := List([1..40], point ->
  Filtered([1..40], lineId -> point in W33LinesCode[lineId]));;
W33SpreadsCode := [];;
W33SearchSpreadsCode := function(usedPoints, chosenLines)
  local remaining, point, candidates, lineId;
  if Length(usedPoints) = 40 then
    AddSet(W33SpreadsCode, Set(chosenLines));
    return;
  fi;
  remaining := Difference([1..40], usedPoints);
  point := remaining[1];
  candidates := Filtered(W33PointLinesCode[point], lineId ->
    Length(Intersection(W33LinesCode[lineId], usedPoints)) = 0);
  for lineId in candidates do
    W33SearchSpreadsCode(
      Union(usedPoints, W33LinesCode[lineId]),
      Concatenation(chosenLines, [lineId]));
  od;
end;;
W33SearchSpreadsCode([], []);;
W33RouteLineCode := Stabilizer(
  W33LineGroupCode, W33SpreadsCode[1], OnSets);;
W33RouteCode := PreImage(W33LineMapCode, W33RouteLineCode);;
W33RouteToS6Code := IsomorphismGroups(W33RouteCode, S6Code);;

# The exceptional outer automorphism is realized on the six K6
# 1-factorizations.  Testing it as well as the chosen route isomorphism
# exhausts the two S6 identification classes.
MatchingsCode := Filtered(Combinations(DuadsCode, 3), matching ->
  Length(Set(Concatenation(matching))) = 6);;
FactorizationsCode := Filtered(
  Combinations([1..Length(MatchingsCode)], 5), factorization ->
    Set(Concatenation(MatchingsCode{factorization})) = Set(DuadsCode));;
OuterS6Code := function(permutation)
  local images, factorization, image;
  images := [];
  for factorization in FactorizationsCode do
    image := Set(List(MatchingsCode{factorization}, matching ->
      Position(MatchingsCode, Set(List(matching, duad ->
        Set(List(duad, x -> x^permutation)))))));
    Add(images, Position(FactorizationsCode, image));
  od;
  return PermList(images);
end;;
if Length(MatchingsCode) <> 15 or Length(FactorizationsCode) <> 6 or
   Size(Group(List(GeneratorsOfGroup(S6Code), OuterS6Code))) <> 720 then
  Error("exceptional outer S6 construction failed");
fi;

BuildW33ModuleCode := function(useOuter)
  local permutations;
  if useOuter then
    permutations := List(QuotientGeneratorsCode, permutation ->
      PreImagesRepresentative(W33RouteToS6Code, OuterS6Code(permutation)));
  else
    permutations := List(QuotientGeneratorsCode, permutation ->
      PreImagesRepresentative(W33RouteToS6Code, permutation));
  fi;
  return GModuleByMats(List(permutations,
    permutation -> PermutationMatrixCode(permutation, 40)), FCode);
end;;
W33ModuleClassACode := BuildW33ModuleCode(false);;
W33ModuleClassBCode := BuildW33ModuleCode(true);;
W33FactorsACode := FactorDimensionsCode(W33ModuleClassACode);;
W33FactorsBCode := FactorDimensionsCode(W33ModuleClassBCode);;

HomologyW33DataCode := function(w33Module)
  local forward, backward, forwardRanks, backwardRanks;
  forward := MTX.BasisModuleHomomorphisms(HomologyModuleCode, w33Module);
  backward := MTX.BasisModuleHomomorphisms(w33Module, HomologyModuleCode);
  forwardRanks := SortedList(Set([
    RankMat(forward[1]), RankMat(forward[2]),
    RankMat(forward[1] + forward[2])]));
  backwardRanks := SortedList(Set([
    RankMat(backward[1]), RankMat(backward[2]),
    RankMat(backward[1] + backward[2])]));
  return rec(
    isomorphic := MTX.IsomorphismModules(HomologyModuleCode, w33Module) <> fail,
    forwardDimension := Length(forward),
    backwardDimension := Length(backward),
    forwardRanks := forwardRanks,
    backwardRanks := backwardRanks);
end;;
W33ComparisonACode := HomologyW33DataCode(W33ModuleClassACode);;
W33ComparisonBCode := HomologyW33DataCode(W33ModuleClassBCode);;
W33RankProfilesCode := SortedList([
  W33ComparisonACode.forwardRanks,
  W33ComparisonBCode.forwardRanks]);;

ExpectedImageFactorsCode := [1,1,1,1,4,4,4,4,4,16];;
ExpectedHomologyFactorsCode := [1,1,1,1,1,1,1,1,4,4,4,4,4,4,4,4];;
ChecksCode := [
  ACode = TransposedMat(ACode),
  ACode * ACode = NullMat(120, 120, FCode),
  ImageFactorsCode = ExpectedImageFactorsCode,
  CoimageFactorsCode = ExpectedImageFactorsCode,
  HomologyFactorsCode = ExpectedHomologyFactorsCode,
  ImageCoimageIsoCode,
  not ImageHomologyIsoCode,
  HomologyMoveRanksCode = [0,12,14,16],
  ImageMoveRanksCode = [0,10,16,18],
  Sum(List(HomologyMoveRankDistributionCode, pair -> pair[2])) = 32,
  Sum(List(ImageMoveRankDistributionCode, pair -> pair[2])) = 32,
  HomologyFixedCode = 15,
  HomologyCoinvariantsCode = 15,
  ImageFixedCode = 14,
  ImageCoinvariantsCode = 14,
  Length(W33PointsCode) = 40,
  Length(W33LinesCode) = 40,
  Set(List(W33PointLinesCode, Length)) = [4],
  Size(W33PointGroupCode) = 25920,
  Length(W33SpreadsCode) = 36,
  Size(W33RouteCode) = 720,
  StructureDescription(W33RouteCode) = "S6",
  Size(Kernel(ExecutionQuotientMapCode)) = 32,
  Kernel(ExecutionQuotientMapCode) = TwoCoreCode,
  IsTransitive(W33RouteCode, [1..40]),
  Size(Stabilizer(W33RouteCode, 1)) = 18,
  W33FactorsACode = ExpectedHomologyFactorsCode,
  W33FactorsBCode = ExpectedHomologyFactorsCode,
  not W33ComparisonACode.isomorphic,
  not W33ComparisonBCode.isomorphic,
  W33ComparisonACode.forwardDimension = 2,
  W33ComparisonBCode.forwardDimension = 2,
  W33ComparisonACode.backwardDimension = 2,
  W33ComparisonBCode.backwardDimension = 2,
  W33ComparisonACode.forwardRanks = W33ComparisonACode.backwardRanks,
  W33ComparisonBCode.forwardRanks = W33ComparisonBCode.backwardRanks,
  W33RankProfilesCode = [[1,6],[1,11]],
  MTX.IsomorphismModules(W33ModuleClassACode, W33ModuleClassBCode) = fail
];;
if not ForAll(ChecksCode, value -> value) then
  Print("DEBUG_MOVE_RANKS|H=", HomologyMoveRanksCode,
        "|I=", ImageMoveRanksCode, "\n");
  Print("FAILED_CHECKS|", List(ChecksCode, BoolIntCross), "\n");
  Error("homology/code/W33 obstruction checks failed");
fi;

Print("CODE_CHAIN|n=120|image=40|kernel=80|homology=40|coimage=40",
      "|selfOrthogonal=1|doublyEven=1\n");
Print("CODE_TRANSVERSAL|structured=15|evenFibre=14|globalHalf=1",
      "|transversal=25|enumeratedCosets=33554432\n");
Print("MODULES|imageFactors=1^4,4^5,16^1",
      "|homologyFactors=1^8,4^8|coimageFactors=1^4,4^5,16^1",
      "|imageIsoCoimage=1|imageIsoHomology=0\n");
Print("O2_ACTION|order=32|homologyMoveRanks=0,12,14,16|homologyFixed=15",
      "|homologyCoinvariants=15|imageMoveRanks=0,10,16,18|imageFixed=14",
      "|imageCoinvariants=14\n");
Print("O2_RANK_DISTRIBUTIONS|homology=", JoinStringsWithSeparator(
        List(HomologyMoveRankDistributionCode,
          pair -> Concatenation(String(pair[1]), ":", String(pair[2]))), ","),
      "|image=", JoinStringsWithSeparator(
        List(ImageMoveRankDistributionCode,
          pair -> Concatenation(String(pair[1]), ":", String(pair[2]))), ","),
      "\n");
Print("GENUINE_W33|points=40|lines=40|PSpOrder=25920",
      "|spreadStabilizer=S6|order=720|transitive=1|pointStabilizer=18\n");
Print("W33_OBSTRUCTION|sameFactors=1|twoS6Classes=2|isomorphisms=0",
      "|homDimensions=2,2|nonzeroRankProfiles=1,6;1,11",
      "|O2HomologyTrivial=0|O2W33Trivial=1\n");

FibreCoordinatesCode := Concatenation(RCode.blocks);;
for row in TransversalBasisCode do
  Print("QBASIS|", JoinStringsWithSeparator(
    List(row{FibreCoordinatesCode}, IntFFE), ""), "\n");
od;
Print("GLOBAL_HALF|", JoinStringsWithSeparator(
  List(GlobalHalfCode{FibreCoordinatesCode}, IntFFE), ""), "\n");
Print("ALL_UNITARY_HOMOLOGY_CODE_W33_OBSTRUCTION_CHECKS_PASS\n");
