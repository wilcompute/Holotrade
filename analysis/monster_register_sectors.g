m := CharacterTable("M");;
chi := First(Irr(m), x -> x[1] = 196883);;
all := Maxes(m);;
names := Filtered(all, s -> PositionSublist(s, "3^(1+12)") <> fail or PositionSublist(s, "5^(1+6)") <> fail
                         or PositionSublist(s, "7^(1+4)") <> fail or PositionSublist(s, "13^(1+2)") <> fail
                         or PositionSublist(s, "2^1+24") <> fail);;
Print("ladder normalisers: ", names, "\n");
pn := function(nm)
  if PositionSublist(nm, "2^1+24") <> fail then return 4096; fi;
  if PositionSublist(nm, "3^(1+12)") <> fail then return 729; fi;
  if PositionSublist(nm, "5^(1+6)") <> fail then return 125; fi;
  if PositionSublist(nm, "7^(1+4)") <> fail then return 49; fi;
  return 13;
end;;
for nm in names do
  h := CharacterTable(nm);
  rest := RestrictedClassFunction(chi, h);
  dec := Decomposition(Irr(h), [rest], "nonnegative")[1];
  degs := List(Irr(h), x -> x[1]);
  parts := Filtered([1..Length(dec)], i -> dec[i] > 0);
  d := pn(nm);
  fa := Filtered(parts, i -> degs[i] mod d = 0);
  Print(nm, ": register dim ", d, "\n  divisible by register: mult x (deg/", d, ") = ",
        List(fa, i -> [dec[i], degs[i] / d]), "\n  mass in register sectors: ", Sum(fa, i -> dec[i] * degs[i]),
        " of ", Sum(parts, i -> dec[i] * degs[i]), "\n");
od;
QUIT;
