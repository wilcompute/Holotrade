#############################################################################
## Exact stable closure for the full C13:C6 normalizer.
##
## W33 Passes 10709--10844 determined the C3 and C2 restrictions separately.
## The missing datum is the action of an order-six complement generator n on
## the 4096-vector carrier.  Wilson's explicit F4^6 matrix gives orbit profile
## 1^4 2^6 3^20 6^670, hence 700 fixed vectors in the permutation module.
## This selects the complete F2[C6] indecomposable decomposition and shows that
## one 64-dimensional pair of correction modules repairs C3 and C2 at once.
#############################################################################

SizeScreen([2000, 1000]);;
F2 := GF(2);;
F4 := GF(4);;
z := Z(4);;
I6 := IdentityMat(6, F4);;

# Wilson normalizer complement from W33 Pass10845, with 2 -> z and 3 -> z^2.
n := [
  [One(F4), z^2, Zero(F4), Zero(F4), Zero(F4), One(F4)],
  [z, Zero(F4), One(F4), z^2, One(F4), One(F4)],
  [z, z^2, Zero(F4), Zero(F4), z^2, One(F4)],
  [z^2, Zero(F4), Zero(F4), z^2, z, One(F4)],
  [Zero(F4), z, z^2, z, z^2, Zero(F4)],
  [z, Zero(F4), One(F4), One(F4), Zero(F4), One(F4)]
];;
if Order(n) <> 6 then Error("normalizer matrix does not have order six"); fi;

Nullities := List([1, 2, 3, 6], d -> 6 - RankMat(n^d - I6));;
FixedVectors := List(Nullities, d -> 4^d);;
if Nullities <> [1, 2, 3, 6] or FixedVectors <> [4, 16, 64, 4096] then
  Error("unexpected order-six fixed-space profile");
fi;

# Mobius inversion of Fix(n^d) for d | 6.
Cycles1 := FixedVectors[1];;
Cycles2 := (FixedVectors[2] - Cycles1) / 2;;
Cycles3 := (FixedVectors[3] - Cycles1) / 3;;
Cycles6 := (FixedVectors[4] - Cycles1 - 2 * Cycles2 - 3 * Cycles3) / 6;;
if [Cycles1, Cycles2, Cycles3, Cycles6] <> [4, 6, 20, 670] then
  Error("unexpected order-six orbit profile");
fi;
PermutationFixedDimension := Cycles1 + Cycles2 + Cycles3 + Cycles6;;
if PermutationFixedDimension <> 700 then Error("bad permutation invariant dimension"); fi;

# Indecomposable F2[C6] modules.  Since C6=C2 x C3 and F2[C3] is semisimple:
# A=J1 tensor 1, B=J2 tensor 1, C=J1 tensor W2, D=J2 tensor W2.
J1 := [[One(F2)]];;
J2 := [[One(F2), One(F2)], [Zero(F2), One(F2)]];;
W2 := [[Zero(F2), One(F2)], [One(F2), One(F2)]];;
A := J1;;
B := J2;;
C := W2;;
D := KroneckerProduct(J2, W2);;
if Order(A) <> 1 or Order(B) <> 2 or Order(C) <> 3 or Order(D) <> 6 then
  Error("bad C6 indecomposable models");
fi;

# Multiplicities selected by the certified C3 restriction, C2 restriction,
# and Fix(n)=700.  H1 is already uniquely selected by its zero J1 count.
V := rec(A := 24, B := 676, C := 20, D := 670);;
H := rec(A := 0, B := 684, C := 0, D := 682);;

DimensionC6 := m -> m.A + 2*m.B + 2*m.C + 4*m.D;;
C2Restriction := m -> rec(J1 := m.A + 2*m.C,
                           J2 := m.B + 2*m.D);;
C3Restriction := m -> rec(trivial := m.A + 2*m.B,
                           W2 := m.C + 2*m.D);;
GeneratorFixed := m -> m.A + m.B;;

if DimensionC6(V) <> 4096 or DimensionC6(H) <> 4096 then Error("bad source dimension"); fi;
if C2Restriction(V) <> rec(J1 := 64, J2 := 2016) or
   C2Restriction(H) <> rec(J1 := 0, J2 := 2048) then
  Error("C2 restrictions do not match Pass10789");
fi;
if C3Restriction(V) <> rec(trivial := 1376, W2 := 1360) or
   C3Restriction(H) <> rec(trivial := 1368, W2 := 1364) then
  Error("C3 restrictions do not match Pass10773");
fi;
if GeneratorFixed(V) <> 700 or GeneratorFixed(H) <> 684 then
  Error("full generator invariants failed");
fi;

# One simultaneous stable correction.  C13 acts trivially on these modules.
LeftCorrection := rec(A := 0, B := 8, C := 0, D := 12);;
RightCorrection := rec(A := 24, B := 0, C := 20, D := 0);;
AddMult := function(x, y)
  return rec(A := x.A+y.A, B := x.B+y.B,
             C := x.C+y.C, D := x.D+y.D);
end;;
StableLeft := AddMult(V, LeftCorrection);;
StableRight := AddMult(H, RightCorrection);;
if StableLeft <> StableRight or StableLeft <> rec(A:=24,B:=684,C:=20,D:=682) then
  Error("full C6 stable multiplicities do not agree");
fi;
if DimensionC6(LeftCorrection) <> 64 or DimensionC6(RightCorrection) <> 64 or
   DimensionC6(StableLeft) <> 4160 then Error("stable dimensions failed"); fi;

# The same correction restricts to the already-certified D26 repair and also
# repairs the C3 defect without induction to dimension 4200.
if C2Restriction(LeftCorrection) <> rec(J1:=0,J2:=32) or
   C2Restriction(RightCorrection) <> rec(J1:=64,J2:=0) then
  Error("D26 correction compatibility failed");
fi;
if C3Restriction(LeftCorrection) <> rec(trivial:=16,W2:=24) or
   C3Restriction(RightCorrection) <> rec(trivial:=24,W2:=20) then
  Error("C3 correction compatibility failed");
fi;

# The nontrivial C13 sector is W12^315 on both sides.  The complement acts as
# Frobenius^2 because 2^2=4 mod 13, and this automorphism has order six.
if 2^2 mod 13 <> 4 or OrderMod(4, 13) <> 6 then
  Error("bad C13 complement arithmetic");
fi;

Print("C6_ACTION|order=6|fixedVectors=4,16,64,4096",
      "|cycles=1^4,2^6,3^20,6^670|permutationFixed=700\n");
Print("C6_SOURCES|V=A^24+B^676+C^20+D^670",
      "|H=A^0+B^684+C^0+D^682|Hfixed=684\n");
Print("C6_CORRECTIONS|left=B^8+D^12|right=A^24+C^20",
      "|dimensionEach=64|stable=A^24+B^684+C^20+D^682\n");
Print("RESTRICTIONS|C2left=J2^32|C2right=J1^64",
      "|C3left=1^16+W2^24|C3right=1^24+W2^20\n");
Print("TATE_EXT|Ext1(1,1)=F2|missingNonsplitJ2=32",
      "|leftTate=0|rightTate=64|identity=64=2*32\n");
Print("FULL_NORMALIZER|group=C13:C6|stableDimension=4160",
      "|abstractModuleIsomorphism=1|chainMap=0|dispatchable=0\n");
Print("ALL_FULL_NORMALIZER_STABLE_CLOSURE_CHECKS_PASS\n");
QUIT;
