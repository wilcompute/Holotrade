#############################################################################
##
##  w33_tau2_111_three_cases.g
##
##  The tau_2 = 111 question reduces to exactly THREE cases up to symmetry.
##
##  tensor_111_pencil_excess.json (PASS) proves that any 111-leaf tensor
##  blocker must carry, on EACH coordinate axis, 36 clean lines of load 11 and
##  exactly four dirty lines of load 12 forming one complete point-pencil. A
##  pencil has a centre, so a 111-witness carries a distinguished POINT on each
##  axis: c_row and c_col.
##
##  PSp(4,3) acts on the 40 points of PG(3,3) with rank 3, so the ordered pair
##  (c_row, c_col) has exactly three orbits under the diagonal action:
##  equal, collinear, non-collinear. Fixing a representative of each is a
##  complete and lossless symmetry break, leaving a residual group of order
##  648, 54 or 24 respectively.
##
##  This file certifies that reduction. It does NOT decide feasibility at 111;
##  the search that consumes it is separate and is reported honestly whatever
##  it returns.
##
##  Emits data/tau2_111_three_cases_gap.json. Fails closed.
##
#############################################################################

G := Sp(4,3);;
V := GF(3)^4;;
nz := Filtered(Elements(V), v -> v <> Zero(V));;
pts := Set(List(nz, NormedRowVector));;
act := function(p,g) return NormedRowVector(p*g); end;;
P := Action(G, pts, act);;
S := Stabilizer(P,1);;
orb := Orbits(S,[1..Length(pts)]);;
sizes := SortedList(List(orb, Length));;

# residual symmetry after fixing both pencil centres, per orbit
resid := [];;
selfpaired := [];;
for o in orb do
  r := o[1];
  Add(resid, [Length(o), Size(Stabilizer(S, r))]);
  # an orbital is self-paired iff some g swaps the ordered pair
  Add(selfpaired, [Length(o),
      RepresentativeAction(P, [1,r], [r,1], OnTuples) <> fail]);
od;
resid := SortedList(resid);;
selfpaired := SortedList(selfpaired);;

# Prime-order SUBGROUP classes of each residual group. The order-2 count is
# load-bearing: the odd-order theorem needs every involution class tested, so
# "exactly one class per case" must be certified, not assumed.
primeclasses := [];;
for o in orb do
  r := o[1];
  R := Stabilizer(S, r);;
  cs := ConjugacyClassesSubgroups(R);;
  Add(primeclasses, [Length(o), Size(R),
      Length(Filtered(cs, c -> Size(Representative(c)) = 2)),
      Length(Filtered(cs, c -> Size(Representative(c)) = 3))]);
od;
primeclasses := SortedList(primeclasses);;

checks := rec(
  npoints        := Length(pts) = 40,
  spOrder        := Size(G) = 51840,
  imageOrder     := Size(P) = 25920,
  kernelIsCentre := Size(G)/Size(P) = 2,
  stabOrder      := Size(S) = 648,
  subdegrees     := sizes = [1,12,27],
  rankThree      := Length(sizes) = 3,
  residuals      := List(resid, x -> x[2]) = [648,54,24],
  productsCheck  := ForAll(resid, x -> x[1]*x[2] = 648),
  allSelfPaired  := ForAll(selfpaired, x -> x[2] = true),
  oneTwoClassEach  := ForAll(primeclasses, x -> x[3] = 1),
  threeClassCounts := List(primeclasses, x -> x[4]) = [5,9,1]
);;
allok := ForAll(RecNames(checks), n -> checks.(n) = true);;

Print("PG(3,3) points            : ", Length(pts), "\n");
Print("|Sp(4,3)| / image on pts  : ", Size(G), " / ", Size(P),
      "   (kernel = centre, order ", Size(G)/Size(P), ")\n");
Print("point stabiliser          : ", Size(S), "\n");
Print("subdegrees                : ", sizes, "   rank ", Length(sizes), "\n");
Print("diagonal orbits on pairs  : ", Length(sizes), "\n");
for x in resid do
  Print("   orbit size ", x[1], " -> residual |Stab(c_row,c_col)| = ", x[2],
        "   (", x[1], " * ", x[2], " = ", x[1]*x[2], ")\n");
od;
Print("all orbitals self-paired  : ", ForAll(selfpaired, x -> x[2]), "\n");
Print("prime-order subgroup classes per residual group:\n");
for x in primeclasses do
  Print("   orbit ", x[1], " |R|=", x[2], " : order-2 classes ", x[3],
        " , order-3 classes ", x[4], "\n");
od;
Print("exactly ONE involution class in each: ",
      ForAll(primeclasses, x -> x[3] = 1), "\n");
Print("ALL CHECKS PASS           : ", allok, "\n");

if allok then
  out := Concatenation(
    "{\n",
    "  \"schema\": \"holotrade.tau2-111-three-cases-gap.v1\",\n",
    "  \"valid\": true,\n",
    "  \"engine\": \"GAP\",\n",
    "  \"points\": 40,\n",
    "  \"spOrder\": ", String(Size(G)), ",\n",
    "  \"imageOrder\": ", String(Size(P)), ",\n",
    "  \"kernelIsCentre\": 2,\n",
    "  \"pointStabiliser\": ", String(Size(S)), ",\n",
    "  \"subdegrees\": [1, 12, 27],\n",
    "  \"rank\": 3,\n",
    "  \"diagonalOrbitsOnOrderedPairs\": 3,\n",
    "  \"residualStabilisers\": ",
    "{\"equal\": 648, \"collinear\": 54, \"noncollinear\": 24},\n",
    "  \"orbitTimesResidualIs648\": true,\n",
    "  \"allOrbitalsSelfPaired\": true,\n",
    "  \"primeOrderSubgroupClasses\": ",
    "{\"equal\": {\"order2\": 1, \"order3\": 5}, ",
    "\"collinear\": {\"order2\": 1, \"order3\": 9}, ",
    "\"noncollinear\": {\"order2\": 1, \"order3\": 1}},\n",
    "  \"exactlyOneInvolutionClassPerCase\": true,\n",
    "  \"whyThatMatters\": \"the odd-order conclusion in ",
    "the_111_symmetric_witnesses.py needs EVERY involution class tested. Each ",
    "residual group has exactly ONE conjugacy class of order-2 subgroups, ",
    "certified here by ConjugacyClassesSubgroups, so three instances cover all ",
    "involutions and the completeness of that slice is certified rather than ",
    "assumed.\",\n",
    "  \"whyItReduces\": \"tensor_111_pencil_excess.json proves any 111-leaf ",
    "blocker has, on each axis, 36 clean lines of load 11 and exactly four ",
    "dirty lines of load 12 forming one complete point-pencil. A pencil has a ",
    "centre, so a witness carries a distinguished point on each axis. PSp(4,3) ",
    "on the 40 points is rank 3, so the ordered pair of centres has exactly ",
    "three orbits -- equal, collinear, non-collinear -- and fixing one ",
    "representative of each is a COMPLETE and lossless symmetry break.\",\n",
    "  \"whatItDoesNotDo\": \"it does not decide feasibility at 111. The ",
    "reduction is structural; the search that consumes it is separate and is ",
    "reported whatever it returns.\",\n",
    "  \"boundary\": \"exact: the full group, the full point set, all orbits ",
    "and stabiliser orders computed in GAP, and each orbital checked ",
    "self-paired by exhibiting a group element swapping an ordered pair ",
    "(RepresentativeAction), not by an indirect argument. The forced pencil ",
    "structure it rests on is QUOTED from tensor_111_pencil_excess.json and ",
    "is not re-derived here. tau_2 remains open in [111,115].\"\n",
    "}\n");;
  f := OutputTextFile("data/tau2_111_three_cases_gap.json", false);;
  WriteAll(f, out);
  CloseStream(f);
  Print("written: data/tau2_111_three_cases_gap.json\n");
else
  Print("CHECKS FAILED -- no certificate written\n");
fi;

QUIT;
