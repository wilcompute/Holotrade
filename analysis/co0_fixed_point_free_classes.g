t := CharacterTable("2.Co1");;
irr := Irr(t);;
chi := First(irr, x -> x[1] = 24);;
ords := OrdersClassRepresentatives(t);;
# fixed-point-free elements g of order d with char poly Phi_d^m: trace equals m*mu(d)-type values;
# check d = 3,5,7,9,13: for each class of order d print chi(g), and chi of powers
for d in [3, 4, 5, 7, 9, 13] do
  for i in [1..Length(ords)] do
    if ords[i] = d then
      vals := List(DivisorsInt(d), k -> chi[PowerMap(t, k)[i]]);
      Print("d=", d, " class ", ClassNames(t)[i], " chi(g^k) for k|d ", DivisorsInt(d), " : ", vals, "\n");
    fi;
  od;
od;
QUIT;
