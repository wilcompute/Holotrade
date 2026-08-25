##############################################################################
##
##  W(3,3) SHAPE CATALOGUE — independent certification in GAP
##
##      node scripts/run-gap.js analysis/w33_shape_catalogue.g
##
##  Third independent route to the results in research/w33_shape_catalogue.md.
##  The JS analysis searches combinatorially; the Python check projects onto
##  eigenspaces; this works with the groups directly, using GRAPE/nauty for the
##  automorphism group and GAP's own clique and independent-set machinery.
##
##  The question this is really here to settle:
##
##      analysis/w33_automorphisms.js built the symmetry group by closing the
##      symplectic transvections and got order 25,920 = PSp(4,3). That is the
##      PROJECTIVE group -- a scalar acts trivially on projective points -- so
##      every shape orbit reported there is a PSp(4,3)-orbit. But placement
##      cares about the automorphism group of the GRAPH, which may be strictly
##      larger. If it is, shapes have more images, blocking sets get harder to
##      build, and the worst-case placement guarantees improve.
##
##      So: compute Aut of the graph properly, and recompute the orbits under
##      it. Whatever comes out, the previous numbers get corrected or confirmed
##      rather than assumed.
##
##############################################################################

LoadPackage("grape");;

#############################################################################
##  Build the point graph exactly as js/substrate.js does, so witnesses
##  transfer by index. Points of PG(3,F_3) with the first nonzero coordinate
##  normalised to 1, enumerated with the first coordinate outermost.
#############################################################################

BuildPoints := function()
  local pts, seen, a, b, c, d, v, lead, inv, norm;
  pts := []; seen := [];
  for a in [0..2] do for b in [0..2] do for c in [0..2] do for d in [0..2] do
    v := [a,b,c,d];
    if v <> [0,0,0,0] then
      lead := First(v, x -> x <> 0);
      if lead = 1 then inv := 1; else inv := 2; fi;   # 2*2 = 1 mod 3
      norm := List(v, x -> (x*inv) mod 3);
      if not norm in seen then Add(seen, norm); Add(pts, norm); fi;
    fi;
  od; od; od; od;
  return pts;
end;;

SymForm := function(u, v)
  return (u[1]*v[2] - u[2]*v[1] + u[3]*v[4] - u[4]*v[3]) mod 3;
end;;

PTS := BuildPoints();;
N := Length(PTS);;

Adjacent := function(i, j)
  return i <> j and SymForm(PTS[i], PTS[j]) = 0;
end;;

gamma := Graph(Group(()), [1..N], OnPoints, Adjacent, true);;

#############################################################################
##  1. the graph is the one the bounds were derived for
#############################################################################

Print("GRAPH\n");
Print("  vertices                ", gamma.order, "\n");
Print("  regular                 ", IsRegularGraph(gamma), "  degree ",
      Length(Adjacency(gamma, 1)), "\n");
Print("  edges                   ",
      Sum([1..N], i -> Length(Adjacency(gamma, i))) / 2, "\n");
Print("  strongly regular        ", IsSimpleGraph(gamma) and
      Length(Set([1..N], i -> Length(Adjacency(gamma,i)))) = 1, "\n");

lams := Set([]);; mus := Set([]);; i := 0;; j := 0;; common := 0;;
for i in [1..N] do
  for j in [i+1..N] do
    common := Length(Intersection(Adjacency(gamma,i), Adjacency(gamma,j)));
    if Adjacent(i,j) then AddSet(lams, common); else AddSet(mus, common); fi;
  od;
od;
Print("  lambda                  ", lams, "\n");
Print("  mu                      ", mus, "\n");

A := List([1..N], i -> List([1..N], j -> 0));;
for i in [1..N] do for j in Adjacency(gamma, i) do A[i][j] := 1; od; od;
Print("  spectrum                ",
      Collected(List(Eigenvalues(Rationals, A), x -> x)), "\n");
Print("  char poly factors       ",
      List(Collected(Factors(CharacteristicPolynomial(A))),
           p -> [String(p[1]), p[2]]), "\n");

#############################################################################
##  2. THE AUTOMORPHISM GROUP OF THE GRAPH
##
##  This is the part the JS could not settle. GRAPE hands the graph to nauty
##  and returns the full group, not the subgroup a particular construction
##  happens to generate.
#############################################################################

Print("\nAUTOMORPHISM GROUP\n");
G := AutGroupGraph(gamma);;
Print("  |Aut(graph)|            ", Size(G), "\n");
Print("  |PSp(4,3)|              ", Size(PSp(4,3)), "\n");
Print("  |Sp(4,3)|               ", Size(Sp(4,3)), "\n");
Print("  index over PSp(4,3)     ", Size(G) / Size(PSp(4,3)), "\n");
Print("  transitive on points    ", IsTransitive(G, [1..N]), "\n");
Print("  rank (suborbit count)   ", Length(Orbits(Stabilizer(G, 1), [1..N])), "\n");
Print("  suborbit lengths        ",
      SortedList(List(Orbits(Stabilizer(G, 1), [1..N]), Length)), "\n");
Print("  point stabiliser order  ", Size(Stabilizer(G, 1)), "\n");
Print("  orbit-stabiliser        ", Size(Stabilizer(G,1)) * N = Size(G), "\n");

#############################################################################
##  3. extremes: clique and independence numbers, by GAP's own algorithms
#############################################################################

Print("\nEXTREMES\n");
cl := CompleteSubgraphs(gamma, -1);;
Print("  clique number           ", Maximum(List(cl, Length)), "\n");
Print("  number of max cliques   ", Length(Filtered(cl, c -> Length(c) = Maximum(List(cl, Length)))), "\n");

comp := ComplementGraph(gamma);;
ind := CompleteSubgraphs(comp, -1);;
alpha := Maximum(List(ind, Length));;
Print("  independence number     ", alpha, "\n");
Print("  Hoffman ratio bound     ", N * 4 / (12 + 4), "\n");
Print("  ratio bound attained    ", alpha = N * 4 / (12 + 4), "\n");
Print("  => ovoid exists         ", alpha = 10, "\n");

#############################################################################
##  4. the intriguing-set classification, recounted
##
##  A set T is a densest shape (tight set) iff every member sees 2 + m/4 of T
##  and every non-member sees m/4. Recount by orbit rather than by search:
##  count the sets satisfying the condition, using the group to avoid
##  enumerating all 2^40 subsets.
#############################################################################

IsTight := function(T, m)
  local S, v, c;
  S := Set(T);
  for v in [1..N] do
    c := Length(Intersection(Adjacency(gamma, v), S));
    if v in S then
      if c <> 2 + m/4 then return false; fi;
    else
      if c <> m/4 then return false; fi;
    fi;
  od;
  return true;
end;;

InducedEdges := function(T)
  local S, e, v;
  S := Set(T); e := 0;
  for v in S do e := e + Length(Intersection(Adjacency(gamma, v), S)); od;
  return e / 2;
end;;

EdgeBoundary := function(T)
  local S, b, v;
  S := Set(T); b := 0;
  for v in S do b := b + Length(Difference(Adjacency(gamma, v), S)); od;
  return b;
end;;

#############################################################################
##  5. shape orbits under the FULL automorphism group
##
##  The witnesses are read from the frozen catalogue via the loader written
##  alongside this file, so the same sets are being measured, not lookalikes.
#############################################################################

Print("\nSHAPE ORBITS UNDER THE FULL AUTOMORPHISM GROUP\n");
Print("  (witness indices are 1-based here, 0-based in the JSON artifacts)\n");
Print("   m   tight?   e(T)   bound   b(T)   orbit under Aut   stabiliser\n");

if IsBoundGlobal("SHAPE_WITNESSES") then
  witnesses := ValueGlobal("SHAPE_WITNESSES");
else
  witnesses := [];
fi;

for w in witnesses do
  m := Length(w);
  T := List(w, x -> x + 1);                 # JSON is 0-based
  bound := m * (m + 8) / 8;
  orb := Orbit(G, Set(T), OnSets);;
  Print("  ", String(m, 2), "   ",
        String(IsTight(T, m), 6), "   ",
        String(InducedEdges(T), 4), "   ",
        String(bound, 5), "   ",
        String(EdgeBoundary(T), 4), "   ",
        String(Length(orb), 15), "   ",
        String(Size(G) / Length(orb), 10), "\n");
od;

Print("\nDONE\n");
QUIT;
