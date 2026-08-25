# GAP-owned exact certificate for the W(3,3) scheduler invariants.
# Run: gap -q analysis/w33_scheduler_math.g
# The only stdout is one JSON object so tests can parse it directly.

SizeScreen([1000000, 1000000]);;

Mod3 := x -> ((x mod 3) + 3) mod 3;;

NormalizeProjective := function(v)
  local pos, inv;
  pos := PositionProperty(v, x -> x <> 0);
  if pos = fail then return fail; fi;
  if v[pos] = 1 then inv := 1; else inv := 2; fi;
  return List(v, x -> Mod3(x * inv));
end;;

SymplecticForm := function(u, v)
  return Mod3(u[1]*v[2] - u[2]*v[1] + u[3]*v[4] - u[4]*v[3]);
end;;

Points := Set(Filtered(
  List(Cartesian([0..2], [0..2], [0..2], [0..2]), NormalizeProjective),
  x -> x <> fail
));;

Adjacency := List([1..40], i -> List([1..40], function(j)
  if i <> j and SymplecticForm(Points[i], Points[j]) = 0 then return 1; fi;
  return 0;
end));;

Degrees := List(Adjacency, Sum);;
Edges := Sum(Degrees) / 2;;
LambdaValues := [];;
MuValues := [];;
for i in [1..39] do
  for j in [i+1..40] do
    common := Sum([1..40], x -> Adjacency[i][x] * Adjacency[j][x]);
    if Adjacency[i][j] = 1 then Add(LambdaValues, common); else Add(MuValues, common); fi;
  od;
od;

I40 := IdentityMat(40);;
Multiplicity12 := 40 - RankMat(Adjacency - 12*I40);;
Multiplicity2 := 40 - RankMat(Adjacency - 2*I40);;
MultiplicityMinus4 := 40 - RankMat(Adjacency + 4*I40);;

BoundaryStats := function(subset)
  local chosen, internal, boundary, i, j;
  chosen := Set(subset);
  internal := 0;
  boundary := 0;
  for i in [1..39] do
    for j in [i+1..40] do
      if Adjacency[i][j] = 1 then
        if (i in chosen) and (j in chosen) then internal := internal + 1;
        elif (i in chosen) <> (j in chosen) then boundary := boundary + 1;
        fi;
      fi;
    od;
  od;
  return [internal, boundary];
end;;

Line := [1,5,6,7];;
Bisection := [3,5,6,8,9,10,12,13,17,18,20,22,24,25,29,30,33,36,39,40];;
LineStats := BoundaryStats(Line);;
BisectionStats := BoundaryStats(Bisection);;

AddCapacity := function(capacity, u, v, amount)
  capacity[u][v] := capacity[u][v] + amount;
end;;

LocalVertexFlow := function(matrix, sourceVertex, sinkVertex)
  local n, splitN, infinity, capacity, i, j, source, sink, flow,
        parent, queue, qpos, u, v, augment;
  n := Length(matrix);
  splitN := 2*n;
  infinity := n + 1;
  capacity := List([1..splitN], x -> ListWithIdenticalEntries(splitN, 0));
  for i in [1..n] do
    if i = sourceVertex or i = sinkVertex then
      AddCapacity(capacity, 2*i-1, 2*i, infinity);
    else
      AddCapacity(capacity, 2*i-1, 2*i, 1);
    fi;
  od;
  for i in [1..n] do
    for j in [1..n] do
      if matrix[i][j] = 1 then AddCapacity(capacity, 2*i, 2*j-1, infinity); fi;
    od;
  od;
  source := 2*sourceVertex;
  sink := 2*sinkVertex-1;
  flow := 0;
  while true do
    parent := ListWithIdenticalEntries(splitN, 0);
    parent[source] := -1;
    queue := [source];
    qpos := 1;
    while qpos <= Length(queue) and parent[sink] = 0 do
      u := queue[qpos];
      qpos := qpos + 1;
      for v in [1..splitN] do
        if parent[v] = 0 and capacity[u][v] > 0 then
          parent[v] := u;
          Add(queue, v);
          if v = sink then break; fi;
        fi;
      od;
    od;
    if parent[sink] = 0 then break; fi;
    augment := infinity;
    v := sink;
    while v <> source do
      u := parent[v];
      augment := Minimum(augment, capacity[u][v]);
      v := u;
    od;
    v := sink;
    while v <> source do
      u := parent[v];
      capacity[u][v] := capacity[u][v] - augment;
      capacity[v][u] := capacity[v][u] + augment;
      v := u;
    od;
    flow := flow + augment;
  od;
  return flow;
end;;

NonedgeFlows := [];;
for i in [1..39] do
  for j in [i+1..40] do
    if Adjacency[i][j] = 0 then Add(NonedgeFlows, LocalVertexFlow(Adjacency, i, j)); fi;
  od;
od;

if Length(Points) <> 40 or Set(Degrees) <> [12] or Edges <> 240 then Error("W33 size/degree failure"); fi;
if Set(LambdaValues) <> [2] or Set(MuValues) <> [4] then Error("W33 SRG parameter failure"); fi;
if [Multiplicity12, Multiplicity2, MultiplicityMinus4] <> [1,24,15] then Error("W33 spectrum failure"); fi;
if LineStats <> [6,36] or BisectionStats <> [70,100] then Error("reservation equality witness failure"); fi;
if Length(NonedgeFlows) <> 540 or Set(NonedgeFlows) <> [12] then Error("vertex connectivity failure"); fi;

Print("{");
Print("\"schema\":\"holotrade.w33-scheduler-math.gap.v1\",");
Print("\"gapVersion\":\"", GAPInfo.Version, "\",");
Print("\"graph\":{\"vertices\":40,\"edges\":240,\"degree\":12,\"lambda\":2,\"mu\":4,");
Print("\"spectrum\":{\"12\":1,\"2\":24,\"-4\":15}},");
Print("\"spectralBounds\":{");
Print("\"edgeBoundaryLower\":\"m(40-m)/4\",");
Print("\"edgeBoundaryUpper\":\"2m(40-m)/5\",");
Print("\"inducedEdgesUpper\":\"m(m+8)/8\"},");
Print("\"equalityShapes\":{");
Print("\"line4\":{\"points0Based\":[0,4,5,6],\"internalEdges\":6,\"boundary\":36},");
Print("\"half20\":{\"points0Based\":[2,4,5,7,8,9,11,12,16,17,19,21,23,24,28,29,32,35,38,39],\"internalEdges\":70,\"boundary\":100}},");
Print("\"vertexConnectivity\":{");
Print("\"value\":12,\"nonadjacentPairsChecked\":540,\"localFlowValues\":[12],");
Print("\"upperWitness\":\"deleting one open neighbourhood isolates its centre\"," );
Print("\"operationalConsequence\":\"the full 40-node cell remains connected after any 11 node deletions\"},");
Print("\"allChecksPass\":true}", "\n");
QUIT;
