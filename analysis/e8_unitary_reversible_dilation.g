#############################################################################
## Reversible symplectic dilation of the 120-state characteristic-two
## differential.  If A=A^T, diag(A)=0 and A^2=0 over F2, then
##
##          U(x,y) = (x + A y, y)
##
## is a 240-bit involution preserving the standard alternating form.  This
## script rebuilds A from the exact GAP/GRAPE carrier, proves those identities,
## and emits the rows from which JavaScript deterministically edge-colours the
## 20-regular bipartite CNOT network.
#############################################################################

E8CrossPrimeLibraryOnly := true;;
Read("analysis/e8_unitary_crossprime_fibre_differential.g");;
R := CrossPrimeFibreDifferential();;
A := R.adjacencyF2;;
F2 := GF(2);;
I120 := IdentityMat(120, F2);;
Z120 := NullMat(120, 120, F2);;
I240 := IdentityMat(240, F2);;

U := Concatenation(
  List([1..120], i -> Concatenation(I120[i], A[i])),
  List([1..120], i -> Concatenation(Z120[i], I120[i])));;
J := Concatenation(
  List([1..120], i -> Concatenation(Z120[i], I120[i])),
  List([1..120], i -> Concatenation(I120[i], Z120[i])));;

ChecksReversible := [
  DimensionsMat(A) = [120, 120],
  A = TransposedMat(A),
  ForAll([1..120], i -> A[i][i] = Zero(F2)),
  Set(List(A, row -> Number(row, value -> value = One(F2)))) = [20],
  A * A = Z120,
  RankMat(A) = 40,
  U * U = I240,
  TransposedMat(U) * J * U = J,
  RankMat(U - I240) = 40,
  240 - RankMat(U - I240) = 200,
  Sum(List(A, row -> Number(row, value -> value = One(F2)))) = 2400
];;

if not ForAll(ChecksReversible, value -> value) then
  Error("reversible dilation checks failed");
fi;

Print("REVERSIBLE_DILATION|bits=240|control=120|target=120",
      "|involution=1|symplectic=1|rankUminusI=40|fixed=200\n");
Print("CNOT_NETWORK|directedGates=2400|bipartiteDegree=20",
      "|optimalParallelDepth=20\n");
for i in [1..120] do
  Print("ADJ|", i - 1, "|",
        JoinStringsWithSeparator(List(Filtered([1..120],
          j -> A[i][j] = One(F2)), j -> String(j - 1)), ","), "\n");
od;
Print("ALL_UNITARY_REVERSIBLE_DILATION_CHECKS_PASS\n");
QUIT;
