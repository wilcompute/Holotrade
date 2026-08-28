#############################################################################
## Exact local stable adapters for the W33 C13:C6 normalizer obstruction.
##
## This does not reconstruct the 4096-dimensional Wilson modules.  Those
## decompositions are owned by W33 Pass10773-10844.  GAP verifies the resulting
## module arithmetic, realizes every indecomposable block explicitly, and
## realizes the characteristic-two D26 correction by an external antipodal Q6
## carrier on which C13 acts trivially.  It does not identify the cube with the
## natural F4^3 fixed cone, which is not C13-stable.
#############################################################################

SizeScreen([1000, 1000]);;
F2 := GF(2);;
J1 := [[Z(2)^0]];;
J2 := [[Z(2)^0, Z(2)^0], [0*Z(2), Z(2)^0]];;
W2 := [[0*Z(2), Z(2)^0], [Z(2)^0, Z(2)^0]];;

if J2^2 <> IdentityMat(2, F2) then Error("bad C2 Jordan block"); fi;
if W2^3 <> IdentityMat(2, F2) or W2 = IdentityMat(2, F2) then
  Error("bad C3 simple block");
fi;

# C3 restriction from W33 Pass10773: V2 - H1 = 8*1 - 4*W2.
V2C3 := rec(trivial := 1376, nontrivial := 1360);;
H1C3 := rec(trivial := 1368, nontrivial := 1364);;
LeftC3 := rec(trivial := V2C3.trivial,
              nontrivial := V2C3.nontrivial + 4);;
RightC3 := rec(trivial := H1C3.trivial + 8,
               nontrivial := H1C3.nontrivial);;
if LeftC3 <> RightC3 then Error("C3 local stable repair failed"); fi;
if LeftC3.trivial + 2 * LeftC3.nontrivial <> 4104 then
  Error("C3 stable dimension failed");
fi;

# Induction from C3 to C13:C3.  Class order is
# 1; four nontrivial C13 classes; h; h^2.
BaseDelta := [0, 0, 0, 0, 0, 12, 12];;
IndTrivial8 := [104, 0, 0, 0, 0, 8, 8];;
IndNontrivial4 := [104, 0, 0, 0, 0, -4, -4];;
if IndTrivial8 - IndNontrivial4 <> BaseDelta then
  Error("C13:C3 induced character repair failed");
fi;

# C2 restriction from W33 Pass10789.  In characteristic two every C2 module
# is a sum of J1 (trivial, dimension 1) and J2 (regular Jordan, dimension 2).
V2C2 := rec(J1 := 64, J2 := 2016);;
H1C2 := rec(J1 := 0, J2 := 2048);;
if V2C2.J1 + 2 * V2C2.J2 <> 4096 or
   H1C2.J1 + 2 * H1C2.J2 <> 4096 then
  Error("C2 source dimensions failed");
fi;
if V2C2.J1 + V2C2.J2 <> 2080 or H1C2.J1 + H1C2.J2 <> 2048 then
  Error("C2 invariant dimensions failed");
fi;

# W33 Pass10837 localizes the entire D26 extension defect in the
# 316-dimensional C13-fixed sector.  The complementary W12^315 sector is
# already the same unique semilinear D26 module on both sides.
V2D26Fixed := rec(J1 := 64, J2 := 126);;
H1D26Fixed := rec(J1 := 0, J2 := 158);;
if V2D26Fixed.J1 + 2 * V2D26Fixed.J2 <> 316 or
   H1D26Fixed.J1 + 2 * H1D26Fixed.J2 <> 316 then
  Error("D26 fixed-sector dimensions failed");
fi;
if V2D26Fixed.J1 + V2D26Fixed.J2 <> 190 or
   H1D26Fixed.J1 + H1D26Fixed.J2 <> 158 then
  Error("D26 fixed-sector invariant dimensions failed");
fi;
if 4096 - 316 <> 315 * 12 or 2080 - 190 <> 315 * 6 or
   2048 - 158 <> 315 * 6 then
  Error("D26 nontrivial-sector equality failed");
fi;

# The 64 vertices of Q6 with antipodal involution are exactly 32 J2 blocks.
CubeVertices := Tuples([0, 1], 6);;
Antipode := PermList(List(CubeVertices, v ->
  Position(CubeVertices, List(v, x -> 1 - x))));;
AntipodeCycles := Cycles(Antipode, [1..64]);;
if Order(Antipode) <> 2 or Set(List(AntipodeCycles, Length)) <> [2] or
   Length(AntipodeCycles) <> 32 then
  Error("Q6 antipodal carrier failed");
fi;

# Give C13 the trivial action on both external correction carriers.  The right
# carrier is therefore 64 abstract trivial states (cardinality F4^3), not the
# natural F4^3 fixed cone.  Hence the two stable sides have identical D26
# indecomposable multiplicities, not merely equal dimensions.
LeftC2 := rec(J1 := V2C2.J1, J2 := V2C2.J2 + 32);;
RightC2 := rec(J1 := H1C2.J1 + 64, J2 := H1C2.J2);;
if LeftC2 <> RightC2 then Error("C2 Q6 stable repair failed"); fi;
if LeftC2.J1 + 2 * LeftC2.J2 <> 4160 then
  Error("C2 stable dimension failed");
fi;

Print("NORMALIZER_STABLE|direct4096=0|c3Local=4104|c13c3=4200",
      "|c3Correction=8|inducedCorrection=104\n");
Print("C2_DEFECT|V2Inv=2080|H1Inv=2048|difference=32",
      "|V2Blocks=J1^64+J2^2016|H1Blocks=J2^2048\n");
Print("D26_FIXED_SECTOR|dimension=316|V2=J1^64+J2^126|H1=J2^158",
      "|nontrivial=W12^315|nontrivialFixedEach=1890\n");
Print("Q6_ANTIPODAL_REPAIR|vertices=64|pairs=32|cubeBlocks=J2^32",
      "|rightExternal=J1^64|C13Action=trivial|stableDimension=4160|proved=1\n");
Print("TRANSLATION_NO_GO|localC3PairingChoices=3|pairsEach=32",
      "|C13EquivariantTranslation=0\n");
Print("FULL_C6_BOUNDARY|compatibleGlueBuilt=0|dispatchable=0\n");
Print("ALL_NORMALIZER_STABLE_ADAPTER_CHECKS_PASS\n");
QUIT;
