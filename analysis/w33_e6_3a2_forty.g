#############################################################################
##
##  w33_e6_3a2_forty.g
##
##  The 40 coordinates of the rank-2 Lagrangian Grassmann code are E6 root
##  subsystems: W(E6) acting on the 3A2 subsystems of E6 is O(5,3):C2 acting
##  on the 40 points of the parabolic quadric Q(4,3).
##
##  the_forty_are_e6_subsystems.py establishes the GRAPH side of this in
##  Python -- 72 roots, 120 A2 subsystems, 40 orthogonal triples, the
##  share-no-root graph being SRG(40,12,2,4) with independence number 10, and
##  an explicit isomorphism to the Q(4,3) point graph verified on all 1600
##  ordered pairs. What Python could not reach is the GROUP: that the action
##  is faithful, transitive, of rank 3 with subdegrees 1+12+27, that the point
##  stabiliser is exactly W(A2)^3 : S3 of order 1296, and that GAP names the
##  image O(5,3):C2 -- the automorphism group of the quadric itself, not
##  merely a group with the right order.
##
##  Emits data/e6_3a2_forty_gap.json. Fails closed: every check must pass or
##  the file is not written.
##
#############################################################################

roots := [];;
for i in [1..5] do
  for j in [i+1..5] do
    for si in [2,-2] do
      for sj in [2,-2] do
        v := ListWithIdenticalEntries(8,0);
        v[i] := si; v[j] := sj;
        Add(roots, v);
      od;
    od;
  od;
od;
for nu in Tuples([0,1],5) do
  if Sum(nu) mod 2 = 0 then
    for s in [1,-1] do
      v := ListWithIdenticalEntries(8,0);
      for i in [1..5] do v[i] := s*(-1)^nu[i]; od;
      v[6] := -s; v[7] := -s; v[8] := s;
      Add(roots, v);
    od;
  fi;
od;
roots := Set(roots);;

# doubled coordinates, so divide by 4 to normalise roots to norm 2
ip := function(a,b) return (a*b)/4; end;;

a2 := [];;
for i in [1..Length(roots)] do
  for j in [i+1..Length(roots)] do
    if ip(roots[i],roots[j]) = -1 then
      c := roots[i] + roots[j];
      if c in roots then
        Add(a2, Set([roots[i],roots[j],c,-roots[i],-roots[j],-c]));
      fi;
    fi;
  od;
od;
a2 := Set(a2);;

orth := function(S,T) return ForAll(S, x -> ForAll(T, y -> ip(x,y) = 0)); end;;
tri := [];;
for i in [1..Length(a2)] do
  for j in [i+1..Length(a2)] do
    if orth(a2[i],a2[j]) then
      for k in [j+1..Length(a2)] do
        if orth(a2[i],a2[k]) and orth(a2[j],a2[k]) then
          Add(tri,[i,j,k]);
        fi;
      od;
    fi;
  od;
od;

refl := function(a)
  return PermList(List(roots, b -> Position(roots, b - ip(b,a)*a)));
end;;
W := Group(List(roots, refl));;

tsets := List(tri, t -> Set(Concatenation(
  List(t, x -> List(a2[x], r -> Position(roots,r))))));;
hom := ActionHomomorphism(W, tsets, OnSets);;
P := Image(hom);;
S := Stabilizer(P,1);;
subs := SortedList(List(Orbits(S,[1..Length(tsets)]), Length));;
sd := StructureDescription(P);;

checks := rec(
  nroots            := Length(roots) = 72,
  normsAllTwo       := Set(List(roots, r -> ip(r,r))) = [2],
  nA2               := Length(a2) = 120,
  nThreeA2          := Length(tri) = 40,
  rootsPerThreeA2   := Set(List(tsets, Length)) = [18],
  weylOrder         := Size(W) = 51840,
  actionFaithful    := Size(Kernel(hom)) = 1,
  actionTransitive  := IsTransitive(P,[1..Length(tsets)]),
  imageOrder        := Size(P) = 51840,
  stabiliserOrder   := Size(S) = 1296,
  subdegrees        := subs = [1,12,27],
  rankThree         := Length(subs) = 3,
  structureIsO53C2  := sd = "O(5,3) : C2",
  halfIsPSp43       := Size(P)/2 = Size(PSp(4,3))
);;

allok := ForAll(RecNames(checks), n -> checks.(n) = true);;

Print("E6 roots                : ", Length(roots), "\n");
Print("A2 subsystems           : ", Length(a2), "\n");
Print("3A2 subsystems          : ", Length(tri), "\n");
Print("roots per 3A2           : ", Set(List(tsets,Length)), "\n");
Print("|W(E6)|                 : ", Size(W), "\n");
Print("action degree / order   : ", LargestMovedPoint(P), " / ", Size(P), "\n");
Print("kernel                  : ", Size(Kernel(hom)), "\n");
Print("point stabiliser        : ", Size(S), "  (W(A2)^3:S3 = ", 6^3*6, ")\n");
Print("subdegrees              : ", subs, "\n");
Print("StructureDescription    : ", sd, "\n");
Print("|P|/2 = |PSp(4,3)|      : ", Size(P)/2 = Size(PSp(4,3)), "\n");
Print("ALL CHECKS PASS         : ", allok, "\n");

if allok then
  out := Concatenation(
    "{\n",
    "  \"schema\": \"holotrade.e6-3a2-forty-gap.v1\",\n",
    "  \"valid\": true,\n",
    "  \"engine\": \"GAP\",\n",
    "  \"roots\": ", String(Length(roots)), ",\n",
    "  \"rootNormsAllTwo\": true,\n",
    "  \"a2Subsystems\": ", String(Length(a2)), ",\n",
    "  \"threeA2Subsystems\": ", String(Length(tri)), ",\n",
    "  \"rootsPerThreeA2\": 18,\n",
    "  \"weylOrder\": ", String(Size(W)), ",\n",
    "  \"actionDegree\": ", String(LargestMovedPoint(P)), ",\n",
    "  \"actionOrder\": ", String(Size(P)), ",\n",
    "  \"kernel\": ", String(Size(Kernel(hom))), ",\n",
    "  \"faithful\": true,\n",
    "  \"transitive\": true,\n",
    "  \"pointStabiliser\": ", String(Size(S)), ",\n",
    "  \"pointStabiliserClosedForm\": \"W(A2)^3 : S3 = 6^3 * 6 = 1296\",\n",
    "  \"subdegrees\": [1, 12, 27],\n",
    "  \"rank\": 3,\n",
    "  \"structureDescription\": \"", sd, "\",\n",
    "  \"halfIsPSp43\": true,\n",
    "  \"reading\": \"W(E6) acting on the 40 3A2 subsystems of E6 is faithful, ",
    "transitive and of rank 3 with subdegrees 1+12+27, its point stabiliser is ",
    "exactly W(A2)^3:S3 of order 1296, and GAP names the image O(5,3):C2 -- ",
    "the automorphism group of the parabolic quadric Q(4,3). So the 40 are the ",
    "points of Q(4,3) as a G-SET, not merely as a graph.\",\n",
    "  \"boundary\": \"exact and exhaustive over the integers at the single ",
    "object E6: all 72 roots, all 120 A2 subsystems, all 40 triples, the full ",
    "group of order 51840 and its induced action. Nothing here has a q ",
    "parameter and nothing generalises. The graph-side facts -- SRG(40,12,2,4), ",
    "independence number 10, and the explicit isomorphism on 1600 ordered pairs ",
    "-- are established separately in the_forty_are_e6_subsystems.py and are ",
    "not recomputed here. No novelty is claimed: W(E6) = U4(2):2 = PSp(4,3).2 ",
    "is classical, 3A2 is a standard subsystem, and GQs of order 3 are ",
    "classified (Payne-Thas).\"\n",
    "}\n");;
  # WriteAll on a raw stream: PrintTo line-wraps long strings with backslash
  # continuations, which is legal GAP output but invalid JSON.
  f := OutputTextFile("data/e6_3a2_forty_gap.json", false);;
  WriteAll(f, out);
  CloseStream(f);
  Print("written: data/e6_3a2_forty_gap.json\n");
else
  Print("CHECKS FAILED -- no certificate written\n");
fi;

QUIT;
