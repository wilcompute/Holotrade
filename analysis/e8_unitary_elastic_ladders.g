#############################################################################
##
## E8 UNITARY RESIDUES AS PARTIAL ELASTIC LADDERS
##
## The W33 repository identifies E8/2E8 with H(3,4)=GQ(4,2) and E8/3E8
## with H(3,9)=GQ(9,3).  This independent GAP witness rebuilds the standard
## Hermitian models over GF(4) and GF(9), computes their lines, proves the
## maximum partial-spread sizes 6 and 16, and verifies every prefix rung.
##
## A union of i mutually skew lines in a GQ(s,t) has
##
##   m = i(s+1),  degree_in = s+i-1,
##   e = (s+1)i(s+i-1)/2,
##   boundary = (s+1)i(st+1-i).
##
## The boundary is exactly the one-sided spectral minimum.  Unlike W(3,3),
## neither unitary carrier has a full spread at q=2 or q=3: the ladders stop
## at 30/45 and 160/280 points.  That incomplete coverage is a theorem and
## an operational hole sector, not something the adapter may hide.
##
## Run:
##   gap -q analysis/e8_unitary_elastic_ladders.g
##
#############################################################################

if LoadPackage("grape") <> true then
  Error("GRAPE is required");
fi;
SizeScreen([100000, 100000]);;
Print("VERSION|", GAPInfo.Version, "\n");

BuildHermitianGQ := function(q)
  local F, els, zero, projective, vector, lead, normalized, hermitian,
        points, i, j, lines, line, a, b, w, indexedLines;
  F := GF(q^2);
  els := AsSSortedList(F);
  zero := Zero(F);
  projective := [];
  for vector in Tuples(els, 4) do
    if vector <> [zero, zero, zero, zero] then
      lead := First(vector, x -> x <> zero);
      normalized := List(vector, x -> x / lead);
      AddSet(projective, normalized);
    fi;
  od;
  hermitian := function(x, y)
    return Sum([1..4], k -> x[k] * y[k]^q);
  end;
  points := Filtered(projective, x -> hermitian(x, x) = zero);
  lines := [];
  for i in [1..Length(points)] do
    for j in [i+1..Length(points)] do
      if hermitian(points[i], points[j]) = zero then
        line := [];
        for a in els do
          for b in els do
            w := List([1..4], k -> a * points[i][k] + b * points[j][k]);
            if w <> [zero, zero, zero, zero] then
              lead := First(w, x -> x <> zero);
              AddSet(line, List(w, x -> x / lead));
            fi;
          od;
        od;
        AddSet(lines, line);
      fi;
    od;
  od;
  indexedLines := List(lines, L -> List(L, x -> Position(points, x)));
  return rec(q := q, s := q^2, t := q, points := points,
             lines := indexedLines);
end;

PointNeighbours := function(D)
  local neighbours, line, p, q;
  neighbours := List([1..Length(D.points)], x -> []);
  for line in D.lines do
    for p in line do
      for q in line do
        if p <> q then AddSet(neighbours[p], q); fi;
      od;
    od;
  od;
  return neighbours;
end;

ConnectedOn := function(vertices, neighbours)
  local allowed, seen, queue, at, next;
  if Length(vertices) <= 1 then return true; fi;
  allowed := Set(vertices);
  seen := [allowed[1]];
  queue := [allowed[1]];
  while Length(queue) > 0 do
    at := Remove(queue, 1);
    for next in Intersection(neighbours[at], allowed) do
      if not next in seen then
        AddSet(seen, next);
        Add(queue, next);
      fi;
    od;
  od;
  return seen = allowed;
end;

DisjointLineGraph := function(D)
  return Graph(Group(()), [1..Length(D.lines)], OnPoints,
    function(i, j)
      return i <> j and IsEmpty(Intersection(D.lines[i], D.lines[j]));
    end, true);
end;

AuditProfile := function(q)
  local D, s, t, v, expectedLines, neighbours, degrees, lambdas, mus,
        i, j, common, disjointGraph, sharpBound, tooLarge, maxima, witness,
        selected, union, insideDegrees, outsideDegrees, internalEdges,
        boundary, expectedVertices, expectedDegree, expectedEdges,
        expectedBoundary, spectralBoundary, checks, allChecks, covered, holes,
        fullSpreadSize;
  D := BuildHermitianGQ(q);
  s := D.s;
  t := D.t;
  v := (s + 1) * (s * t + 1);
  expectedLines := (t + 1) * (s * t + 1);
  neighbours := PointNeighbours(D);
  degrees := Set(List(neighbours, Length));
  lambdas := [];
  mus := [];
  for i in [1..v] do
    for j in [i+1..v] do
      common := Length(Intersection(neighbours[i], neighbours[j]));
      if j in neighbours[i] then AddSet(lambdas, common);
      else AddSet(mus, common);
      fi;
    od;
  od;

  disjointGraph := DisjointLineGraph(D);
  sharpBound := (q^3 + q + 2) / 2;
  tooLarge := CompleteSubgraphsOfGivenSize(disjointGraph, sharpBound + 1, 1);
  maxima := CompleteSubgraphsOfGivenSize(disjointGraph, sharpBound, 1);
  if Length(tooLarge) <> 0 or Length(maxima) = 0 then
    Error("partial-spread maximum did not certify");
  fi;
  witness := maxima[1];
  covered := Length(Set(Concatenation(D.lines{witness})));
  holes := v - covered;
  fullSpreadSize := s * t + 1;

  checks := [
    Length(D.points) = v,
    Length(D.lines) = expectedLines,
    Set(List(D.lines, Length)) = [s + 1],
    degrees = [s * (t + 1)],
    lambdas = [s - 1],
    mus = [t + 1],
    Length(witness) = sharpBound,
    covered = sharpBound * (s + 1),
    sharpBound < fullSpreadSize
  ];

  Print("PROFILE|", q, "|", v, "|", Length(D.lines), "|", s + 1,
        "|", degrees[1], "|", lambdas[1], "|", mus[1], "|",
        sharpBound, "|", Length(maxima), "|", covered, "|", holes,
        "|", fullSpreadSize, "\n");
  Print("WITNESS|", q, "|", D.lines{witness}, "\n");

  # Preserve the carrier-level incidence and SRG checks when the rung checks
  # are folded in.  Resetting this accumulator to true would make the first
  # nine checks informative only, rather than part of the certificate.
  allChecks := ForAll(checks, x -> x);
  for i in [1..Length(witness)] do
    selected := witness{[1..i]};
    union := Set(Concatenation(D.lines{selected}));
    insideDegrees := Set(List(union,
      p -> Length(Intersection(neighbours[p], union))));
    outsideDegrees := Set(List(Difference([1..v], union),
      p -> Length(Intersection(neighbours[p], union))));
    internalEdges := Sum(union,
      p -> Length(Intersection(neighbours[p], union))) / 2;
    boundary := Sum(union,
      p -> Length(Difference(neighbours[p], union)));
    expectedVertices := i * (s + 1);
    expectedDegree := s + i - 1;
    expectedEdges := (s + 1) * i * (s + i - 1) / 2;
    expectedBoundary := (s + 1) * i * (s * t + 1 - i);
    spectralBoundary := (s * t + 1) * expectedVertices *
                        (v - expectedVertices) / v;
    checks := [
      Length(union) = expectedVertices,
      insideDegrees = [expectedDegree],
      outsideDegrees = [i],
      internalEdges = expectedEdges,
      boundary = expectedBoundary,
      boundary = spectralBoundary,
      ConnectedOn(union, neighbours)
    ];
    allChecks := allChecks and ForAll(checks, x -> x);
    Print("RUNG|", q, "|", i, "|", expectedVertices, "|",
          internalEdges, "|", boundary, "|", insideDegrees[1], "|",
          outsideDegrees[1], "\n");
  od;
  if not ForAll(checks, x -> x) or not allChecks then
    Error("unitary elastic rung audit failed");
  fi;
  return rec(q := q, allChecks := allChecks);
end;

if not IsBound(E8UnitaryLibraryOnly) or E8UnitaryLibraryOnly <> true then
  P2 := AuditProfile(2);;
  P3 := AuditProfile(3);;
  if not P2.allChecks or not P3.allChecks then Error("audit failed"); fi;
  Print("ALL_CHECKS_PASS\n");
fi;
