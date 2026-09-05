# Independent group-order witness for the six simple-root matrices used by
# analysis/the_rank_three_exact_sp6_orbit_census.py.
F := GF(3);
one := One(F);
minus := -one;
I := IdentityMat(6,F);

g1 := ShallowCopy(I); g1[1][2] := one;   g1[5][4] := minus;
g2 := ShallowCopy(I); g2[2][1] := one;   g2[4][5] := minus;
g3 := ShallowCopy(I); g3[2][3] := one;   g3[6][5] := minus;
g4 := ShallowCopy(I); g4[3][2] := one;   g4[5][6] := minus;
g5 := ShallowCopy(I); g5[3][6] := one;
g6 := ShallowCopy(I); g6[6][3] := one;

G := Group([g1,g2,g3,g4,g5,g6]);
s := Size(G);
Print("Sp6 generator order = ", s, "\n");
if s <> 9170703360 then
  Error("simple-root generators did not generate Sp(6,3)");
fi;
Print("PASS\n");
QUIT_GAP(0);
