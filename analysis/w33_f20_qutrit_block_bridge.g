# Exact local-Clifford symmetry audit for the cyclic [[5,1,3]]_3 block.
#
# The 1296-state W33 fibre product has point stabilizer F20 = AGL(1,5).
# The current W33 qutrit storage stack uses cyclic five-qutrit blocks.  This
# witness asks whether that shared integer 5 is structural: first at the level
# of bare coordinate permutations, then allowing an independent one-qutrit
# Clifford (SL(2,3)) on every coordinate.

F := GF(3);;
z := Zero(F);;
o := One(F);;

# Pass 79's generator X Z Z^-1 X^-1 I and shifts 0..3, with coordinates
# ordered X_1,...,X_5,Z_1,...,Z_5.
rows := [];;
for shift in [0..3] do
    x := List([1..5], i -> z);;
    zz := List([1..5], i -> z);;
    x[((0 + shift) mod 5) + 1] := o;;
    zz[((1 + shift) mod 5) + 1] := o;;
    zz[((2 + shift) mod 5) + 1] := 2 * o;;
    x[((3 + shift) mod 5) + 1] := 2 * o;;
    Add(rows, Concatenation(x, zz));;
od;;
code := VectorSpace(F, rows);;

PermuteRow := function(r, p)
    return Concatenation(
        List([1..5], i -> r[i^p]),
        List([1..5], i -> r[5 + i^p])
    );
end;;

S5 := SymmetricGroup(5);;
plain := Filtered(Elements(S5), p ->
    ForAll(rows, r -> PermuteRow(r, p) in code)
);;
plainGroup := Group(plain);;

# At site i the X_i and Z_i columns form a 2-frame in the four-dimensional
# stabilizer-generator space.  A row-basis change R together with local 2x2
# maps N_i witnesses monomial equivalence precisely when
#
#        R * C_i = C_{p(i)} * N_i.
#
# Enumerating R does not require GL(4,3): two complementary site frames fix R,
# leaving only 48^2 candidates for each of the 120 coordinate permutations.
sites := [];;
for i in [1..5] do
    Add(sites, List([1..4], r -> [rows[r][i], rows[r][5+i]]));;
od;;

PairMatrix := function(A, B)
    return List([1..4], r -> Concatenation(A[r], B[r]));
end;;

sourcePair := fail;;
sourceIndices := fail;;
for i in [1..4] do
    for j in [i+1..5] do
        candidate := PairMatrix(sites[i], sites[j]);;
        if RankMat(candidate) = 4 then
            sourcePair := candidate;;
            sourceIndices := [i,j];;
            break;
        fi;
    od;
    if sourcePair <> fail then break; fi;
od;;
if sourcePair = fail then Error("no complementary site frames"); fi;

GL2 := Elements(GL(2,3));;

# Cache a left inverse L_i for each 4x2 site frame C_i.  Then the only
# possible local map is N_i=L_i R C_i, and C_target N_i=R C_i is the exact
# membership check.  This removes vector-space construction from the inner
# 120*48^2 loop.
siteLeft := [];;
for i in [1..5] do
    found := fail;;
    for pair in Combinations([1..4], 2) do
        small := sites[i]{pair};;
        if DeterminantMat(small) <> z then
            invsmall := Inverse(small);;
            left := NullMat(2, 4, F);;
            for a in [1..2] do
                for b in [1..2] do
                    left[a][pair[b]] := invsmall[a][b];;
                od;
            od;
            if left * sites[i] <> IdentityMat(2, F) then
                Error("bad cached site left inverse");
            fi;
            found := left;;
            break;
        fi;
    od;
    if found = fail then Error("rank-deficient site frame"); fi;
    Add(siteLeft, found);;
od;;

LocalMatrix := function(targetIndex, image)
    local N;
    N := siteLeft[targetIndex] * image;
    if sites[targetIndex] * N <> image then return fail; fi;
    return N;
end;;

WitnessesFor := function(p)
    local a, b, targetA, targetB, targetPair, R, k, image, N,
          localDets, good, glWitness, slWitness;
    glWitness := fail;
    slWitness := fail;
    for a in GL2 do
        targetA := sites[sourceIndices[1]^p] * a;
        for b in GL2 do
            targetB := sites[sourceIndices[2]^p] * b;
            targetPair := PairMatrix(targetA, targetB);
            R := targetPair * Inverse(sourcePair);
            localDets := [];
            good := true;
            for k in [1..5] do
                image := R * sites[k];
                N := LocalMatrix(k^p, image);
                if N = fail then
                    good := false;
                    break;
                fi;
                Add(localDets, DeterminantMat(N));
            od;
            if good then
                if glWitness = fail then
                    glWitness := rec(
                        rowChange := R,
                        localDeterminants := localDets,
                        localMatrices := List([1..5], k ->
                            LocalMatrix(k^p, R * sites[k]))
                    );
                fi;
                if ForAll(localDets, d -> d = o) then
                    slWitness := rec(
                        rowChange := R,
                        localDeterminants := localDets,
                        localMatrices := List([1..5], k ->
                            LocalMatrix(k^p, R * sites[k]))
                    );
                    return rec(gl := glWitness, sl := slWitness);
                fi;
            fi;
        od;
    od;
    return rec(gl := glWitness, sl := slWitness);
end;;

localGL := [];;
localSL := [];;
witnessesSL := [];;
for p in Elements(S5) do
    ws := WitnessesFor(p);;
    if ws.gl <> fail then Add(localGL, p); fi;
    if ws.sl <> fail then
        Add(localSL, p);;
        Add(witnessesSL, [p, ws.sl]);;
    fi;
od;;

groupGL := Group(localGL);;
groupSL := Group(localSL);;
multiplierTwo := PermList([1,3,5,2,4]);;
witnessM2 := WitnessesFor(multiplierTwo).sl;;
translation := (1,2,3,4,5);;
qutritConjugationExponent := First([2..4], exponent ->
    translation^multiplierTwo = translation^exponent);;
multiplierTwoInverse := multiplierTwo^-1;;
witnessM2Inverse := WitnessesFor(multiplierTwoInverse).sl;;
qutritInverseConjugationExponent := First([2..4], exponent ->
    translation^multiplierTwoInverse = translation^exponent);;
if witnessM2 = fail or qutritConjugationExponent = fail or
   witnessM2Inverse = fail or qutritInverseConjugationExponent = fail or
   Size(Group(translation, multiplierTwo)) <> 20 then
    Error("explicit qutrit F20 presentation failed");
fi;

PhysicalLift := function(p, localMatrices)
    local Q, k, source, target, a, b;
    Q := NullMat(10, 10, F);
    for k in [1..5] do
        source := [k^p, 5 + k^p];
        target := [k, 5 + k];
        for a in [1..2] do
            for b in [1..2] do
                Q[source[a]][target[b]] := localMatrices[k][a][b];
            od;
        od;
    od;
    return Q;
end;;

MatrixOrderBounded := function(M, bound)
    local power, order;
    power := IdentityMat(Length(M), F);
    for order in [1..bound] do
        power := power * M;
        if power = IdentityMat(Length(M), F) then return order; fi;
    od;
    return fail;
end;;

identityLocals := List([1..5], i -> IdentityMat(2, F));;
translationLift := PhysicalLift(translation, identityLocals);;
multiplierLift := PhysicalLift(multiplierTwo, witnessM2.localMatrices);;
multiplierInverseLift := PhysicalLift(
    multiplierTwoInverse, witnessM2Inverse.localMatrices);;
J := NullMat(10, 10, F);;
for i in [1..5] do
    J[i][5+i] := o;;
    J[5+i][i] := 2 * o;;
od;;
translationLiftOrder := MatrixOrderBounded(translationLift, 20);;
multiplierLiftOrder := MatrixOrderBounded(multiplierLift, 40);;
multiplierInverseLiftOrder := MatrixOrderBounded(multiplierInverseLift, 40);;
physicalConjugationExponent := First([1..4], exponent ->
    Inverse(multiplierLift) * translationLift *
      multiplierLift = translationLift^exponent);;
liftConjugationExponent := First([1..4], exponent ->
    Inverse(multiplierInverseLift) * translationLift *
      multiplierInverseLift = translationLift^exponent);;
liftPreservesCode := ForAll(rows, row -> row * translationLift in code) and
    ForAll(rows, row -> row * multiplierLift in code) and
    ForAll(rows, row -> row * multiplierInverseLift in code);;
liftIsSymplectic := translationLift * J *
      TransposedMat(translationLift) = J and
    multiplierLift * J *
      TransposedMat(multiplierLift) = J and
    multiplierInverseLift * J *
      TransposedMat(multiplierInverseLift) = J;;

# The two physical lifts act faithfully on the 40 addressed nonidentity
# one-site Paulis (five sites times eight nonzero X/Z labels).  Freeze that
# action as the exact truth table for the hardware controller.
localPaulis := [];;
for site in [1..5] do
    for xv in [0..2] do
        for zv in [0..2] do
            if xv <> 0 or zv <> 0 then
                pauli := List([1..10], i -> z);;
                pauli[site] := xv * o;;
                pauli[5+site] := zv * o;;
                Add(localPaulis, pauli);;
            fi;
        od;
    od;
od;;
translationPauliAction := PermList(List(localPaulis, pauli ->
    Position(localPaulis, pauli * translationLift)));;
multiplierPauliAction := PermList(List(localPaulis, pauli ->
    Position(localPaulis, pauli * multiplierLift)));;
physicalPauliGroup := Group(translationPauliAction,
    multiplierPauliAction);;
physicalPauliConjugationExponent := First([1..4], exponent ->
    translationPauliAction^multiplierPauliAction =
      translationPauliAction^exponent);;

FlatMatrix := function(matrix)
    return JoinStringsWithSeparator(
        List(Concatenation(matrix), entry -> String(Int(entry))), ",");
end;;

Print("F20_QUTRIT_BLOCK|status=PASS");;
Print("|codeDimension=", Dimension(code));;
Print("|plainPermutationOrder=", Size(plainGroup));;
Print("|plainPermutationStructure=", StructureDescription(plainGroup));;
Print("|localGLCoordinateOrder=", Size(groupGL));;
Print("|localGLCoordinateStructure=", StructureDescription(groupGL));;
Print("|localCliffordCoordinateOrder=", Size(groupSL));;
Print("|localCliffordCoordinateStructure=", StructureDescription(groupSL));;
Print("|multiplierTwoPlain=", multiplierTwo in plainGroup);;
Print("|multiplierTwoLocalClifford=", witnessM2 <> fail);;
Print("|F20Realized=", Size(groupSL) = 20 and StructureDescription(groupSL) = "C5 : C4");;
Print("|presentationOrders=", Order(translation), ",", Order(multiplierTwo));;
Print("|presentationExponent=", qutritConjugationExponent);;
Print("|multiplierTwoPermutation=", JoinStringsWithSeparator(
    List(ListPerm(multiplierTwo, 5), String), ","));;
Print("|multiplierTwoRowChange=", FlatMatrix(witnessM2.rowChange));;
Print("|multiplierTwoLocalMatrices=", JoinStringsWithSeparator(
    List(witnessM2.localMatrices, FlatMatrix), "/"));;
Print("|inversePresentationExponent=", qutritInverseConjugationExponent);;
Print("|multiplierTwoInversePermutation=", JoinStringsWithSeparator(
    List(ListPerm(multiplierTwoInverse, 5), String), ","));;
Print("|multiplierTwoInverseRowChange=", FlatMatrix(
    witnessM2Inverse.rowChange));;
Print("|multiplierTwoInverseLocalMatrices=", JoinStringsWithSeparator(
    List(witnessM2Inverse.localMatrices, FlatMatrix), "/"));;
Print("|liftOrders=", translationLiftOrder, ",", multiplierLiftOrder,
    ",", multiplierInverseLiftOrder);;
Print("|physicalPresentationExponent=", physicalConjugationExponent);;
Print("|inverseLiftConjugationExponent=", liftConjugationExponent);;
Print("|liftPreservesCode=", liftPreservesCode);;
Print("|liftIsSymplectic=", liftIsSymplectic);;
Print("|physicalPauliDegree=", Length(localPaulis));;
Print("|physicalPauliGroupOrder=", Size(physicalPauliGroup));;
Print("|physicalPauliGeneratorOrders=", Order(translationPauliAction),
    ",", Order(multiplierPauliAction));;
Print("|physicalPauliConjugationExponent=",
    physicalPauliConjugationExponent);;
Print("|physicalTranslationAction=", JoinStringsWithSeparator(
    List(ListPerm(translationPauliAction, 40), String), ","));;
Print("|physicalMultiplierAction=", JoinStringsWithSeparator(
    List(ListPerm(multiplierPauliAction, 40), String), ","));;
Print("\n");;

QUIT_GAP(0);
