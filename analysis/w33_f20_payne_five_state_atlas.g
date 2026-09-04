#############################################################################
## Exact F20 five-state atlas across the qutrit block, W33 Payne covers,
## the 216 slow-target circuit carrier, and a GQ(4,2) ROM bank.
#############################################################################

LoadPackage("grape");;
SizeScreen([1000000,1000000]);;
Read("analysis/w33_f20_payne_five_state_input.g");;

JoinIntsAtlas := xs -> JoinStringsWithSeparator(List(xs,String),",");;
OrbitSizesAtlas := function(group,domain,action)
  if action=fail then return SortedList(List(Orbits(group,domain),Length)); fi;
  return SortedList(List(Orbits(group,domain,action),Length));
end;;
AdjacentFromLinesAtlas := function(lines,x,y)
  return x<>y and ForAny(lines,line->x in line and y in line);
end;;

GraphAAtlas := Graph(Group(()),[1..45],OnPoints,
  function(x,y) return AdjacentFromLinesAtlas(GQLinesA,x,y); end,true);;
AutAAtlas := AutGroupGraph(GraphAAtlas);;
InnerAAtlas := DerivedSubgroup(AutAAtlas);;
BaseLineAtlas := Set(GQLinesA[1]);;
InnerLineStabAtlas := Stabilizer(InnerAAtlas,BaseLineAtlas,OnSets);;
FullLineStabAtlas := Stabilizer(AutAAtlas,BaseLineAtlas,OnSets);;
InnerLineHomAtlas := ActionHomomorphism(InnerLineStabAtlas,BaseLineAtlas,OnPoints);;
FullLineHomAtlas := ActionHomomorphism(FullLineStabAtlas,BaseLineAtlas,OnPoints);;
InnerLineImageAtlas := Image(InnerLineHomAtlas);;
FullLineImageAtlas := Image(FullLineHomAtlas);;
InnerLineKernelAtlas := Kernel(InnerLineHomAtlas);;
FullLineKernelAtlas := Kernel(FullLineHomAtlas);;

# Lift the AGL(1,5) normalizer from the S5 line image, then enumerate the
# complements of its elementary-abelian 2^4 kernel inside the order-320
# preimage.  This solvable preimage makes the complement census exact and fast.
ImageFiveAtlas := SylowSubgroup(FullLineImageAtlas,5);;
ImageF20Atlas := Normalizer(FullLineImageAtlas,ImageFiveAtlas);;
PreF20Atlas := PreImage(FullLineHomAtlas,ImageF20Atlas);;
PreClassesAtlas := ConjugacyClassesSubgroups(PreF20Atlas);;
OuterF20CandidatesAtlas := Filtered(List(PreClassesAtlas,Representative),
  subgroup->Size(subgroup)=20 and Size(Intersection(subgroup,FullLineKernelAtlas))=1);;
if Length(OuterF20CandidatesAtlas)<>1 then Error("outer F20 complement class is not unique"); fi;
OuterF20Atlas := OuterF20CandidatesAtlas[1];;
OuterAAtlas := First(Elements(OuterF20Atlas),element->Order(element)=5);;
OuterBAtlas := First(Elements(OuterF20Atlas),element->Order(element)=4 and
  OuterAAtlas^element=OuterAAtlas^3 and Size(Group(OuterAAtlas,element))=20);;
if OuterBAtlas=fail then Error("outer F20 presentation failed"); fi;

# The fibre theorem used the alternating-pair symplectic basis (12)(34), while
# the Payne certificate uses (13)(24).  Conjugate by the explicit coordinate
# swap 2<->3 before comparing the two canonical forty-point lists.
F3Atlas := GF(3);; Zero3Atlas := Zero(F3Atlas);;
NormalizeAtlas := function(vector)
  local first,scale;
  first:=PositionProperty(vector,x->x<>Zero3Atlas);;
  scale:=vector[first]^-1;
  return List(vector,x->x*scale);
end;;
Points40Atlas := Set(List(Filtered(Tuples(Elements(F3Atlas),4),
  vector->ForAny(vector,x->x<>Zero3Atlas)),NormalizeAtlas));;
BasisCrosswalkAtlas := PermList(List(Points40Atlas,point->Position(Points40Atlas,
  NormalizeAtlas([point[1],point[3],point[2],point[4]]))));;
W33TAtlas := BasisCrosswalkAtlas^-1*PermList(W33RawT)*BasisCrosswalkAtlas;;
W33MAtlas := BasisCrosswalkAtlas^-1*PermList(W33RawM)*BasisCrosswalkAtlas;;
W33F20Atlas := Group(W33TAtlas,W33MAtlas);;
AddressTPermAtlas := PermList(AddressT);;
AddressMPermAtlas := PermList(AddressM);;
AddressF20Atlas := Group(AddressTPermAtlas,AddressMPermAtlas);;
AddressToW33HomAtlas := GroupHomomorphismByImages(AddressF20Atlas,W33F20Atlas,
  [AddressTPermAtlas,AddressMPermAtlas],[W33TAtlas,W33MAtlas]);;
if not IsBijective(AddressToW33HomAtlas) then Error("address-to-W33 F20 isomorphism failed"); fi;

AddressOrbitsAtlas := Orbits(AddressF20Atlas,[1..40]);;
W33OrbitsAtlas := Orbits(W33F20Atlas,[1..40]);;
AddressAxisMapsAtlas := [];;
for SwapAtlas in [[1,2],[2,1]] do
  for XAtlas in W33OrbitsAtlas[SwapAtlas[1]] do
    for YAtlas in W33OrbitsAtlas[SwapAtlas[2]] do
      MapAtlas := List([1..40],z->0);;
      for ElementAtlas in Elements(AddressF20Atlas) do
        MapAtlas[AddressOrbitsAtlas[1][1]^ElementAtlas] :=
          XAtlas^Image(AddressToW33HomAtlas,ElementAtlas);;
        MapAtlas[AddressOrbitsAtlas[2][1]^ElementAtlas] :=
          YAtlas^Image(AddressToW33HomAtlas,ElementAtlas);;
      od;
      Add(AddressAxisMapsAtlas,MapAtlas);;
    od;
  od;
od;
Sort(AddressAxisMapsAtlas);;
CanonicalAddressAxisAtlas := AddressAxisMapsAtlas[1];;

TargetSupportsAtlas := List([1..45],target->Filtered([1..40],axis->
  target in PayneCovers[axis]));;
InducedSlowAtlas := function(axisPermutation)
  return PermList(List([1..45],target->Position(TargetSupportsAtlas,
    Set(List(TargetSupportsAtlas[target],axis->axis^axisPermutation)))));
end;;
SlowTAtlas := InducedSlowAtlas(W33TAtlas);;
SlowMAtlas := InducedSlowAtlas(W33MAtlas);;
SlowF20Atlas := Group(SlowTAtlas,SlowMAtlas);;
GraphBAtlas := Graph(Group(()),[1..45],OnPoints,
  function(x,y) return AdjacentFromLinesAtlas(GQLinesB,x,y); end,true);;
AutBAtlas := AutGroupGraph(GraphBAtlas);;
InnerBAtlas := DerivedSubgroup(AutBAtlas);;
if not (SlowTAtlas in InnerBAtlas and SlowMAtlas in InnerBAtlas) then
  Error("fibre F20 did not land in inner slow-target group");
fi;
if Normalizer(InnerBAtlas,SylowSubgroup(SlowF20Atlas,5))<>SlowF20Atlas then
  Error("fibre F20 is not the full inner Sylow-five normalizer");
fi;
SlowFiveOrbitAtlas := First(Orbits(SlowF20Atlas,[1..45]),orbit->Length(orbit)=5);;
SlowFiveEdgesAtlas := Number(Combinations(SlowFiveOrbitAtlas,2),pair->
  AdjacentFromLinesAtlas(GQLinesB,pair[1],pair[2]));;
SlowFiveStabAtlas := Stabilizer(InnerBAtlas,Set(SlowFiveOrbitAtlas),OnSets);;
SlowFiveActionAtlas := Action(SlowFiveStabAtlas,SlowFiveOrbitAtlas,OnPoints);;

SitePermAtlas := function(addressPermutation)
  return PermList(List([1..5],site->
    QuoInt(((8*(site-1)+1)^addressPermutation)-1,8)+1));
end;;
SiteTAtlas := SitePermAtlas(AddressTPermAtlas);;
SiteMAtlas := SitePermAtlas(AddressMPermAtlas);;
SiteF20Atlas := Group(SiteTAtlas,SiteMAtlas);;
SiteToSlowHomAtlas := GroupHomomorphismByImages(SiteF20Atlas,SlowF20Atlas,
  [SiteTAtlas,SiteMAtlas],[SlowTAtlas,SlowMAtlas]);;
if not IsBijective(SiteToSlowHomAtlas) then Error("site-to-slow F20 isomorphism failed"); fi;
SiteCircuitMapsAtlas := [];;
for TargetAtlas in SlowFiveOrbitAtlas do
  SiteMapAtlas := List([1..5],x->0);; GoodAtlas := true;;
  for ElementAtlas in Elements(SiteF20Atlas) do
    SourceAtlas := 1^ElementAtlas;;
    DestAtlas := TargetAtlas^Image(SiteToSlowHomAtlas,ElementAtlas);;
    if SiteMapAtlas[SourceAtlas]=0 then SiteMapAtlas[SourceAtlas]:=DestAtlas;
    elif SiteMapAtlas[SourceAtlas]<>DestAtlas then GoodAtlas:=false; fi;
  od;
  if GoodAtlas and Length(Set(SiteMapAtlas))=5 then Add(SiteCircuitMapsAtlas,SiteMapAtlas); fi;
od;
if Length(SiteCircuitMapsAtlas)<>1 then Error("site-to-circuit map is not unique"); fi;
CanonicalSiteCircuitAtlas := SiteCircuitMapsAtlas[1];;

EquivariantMapsForAtlas := function(homomorphism)
  local output,swap,x,y,mapping,element;
  output:=[];
  for swap in [[1,2],[2,1]] do
    for x in W33OrbitsAtlas[swap[1]] do
      for y in W33OrbitsAtlas[swap[2]] do
        mapping:=List([1..40],z->0);
        for element in Elements(AddressF20Atlas) do
          mapping[AddressOrbitsAtlas[1][1]^element]:=
            x^Image(homomorphism,element);
          mapping[AddressOrbitsAtlas[2][1]^element]:=
            y^Image(homomorphism,element);
        od;
        Add(output,mapping);
      od;
    od;
  od;
  return output;
end;;
SiteMapsForAtlas := function(slowT,slowM)
  local homomorphism,output,target,mapping,good,element,source,destination;
  homomorphism:=GroupHomomorphismByImages(SiteF20Atlas,Group(slowT,slowM),
    [SiteTAtlas,SiteMAtlas],[slowT,slowM]);
  if not IsBijective(homomorphism) then return []; fi;
  output:=[];
  for target in SlowFiveOrbitAtlas do
    mapping:=List([1..5],x->0);good:=true;
    for element in Elements(SiteF20Atlas) do
      source:=1^element;destination:=target^Image(homomorphism,element);
      if mapping[source]=0 then mapping[source]:=destination;
      elif mapping[source]<>destination then good:=false;fi;
    od;
    if good and Length(Set(mapping))=5 then Add(output,mapping);fi;
  od;
  return output;
end;;

# Exhaust every abstract F20 generator identification compatible with the
# fixed T^5=M^4=1, T^M=T^3 presentation.  None also makes the eight address
# labels over each site equal the eight Payne covers through its slow target.
AllF20IsomorphismsAtlas := 0;;
AllIncidenceCandidatesAtlas := 0;;
CoherentIncidenceMapsAtlas := 0;;
IncidenceOverlapTotalsAtlas := [];;
IncidenceOverlapProfilesAtlas := [];;
for UAtlas in Elements(W33F20Atlas) do
  for VAtlas in Elements(W33F20Atlas) do
    if Order(UAtlas)=5 and Order(VAtlas)=4 and UAtlas^VAtlas=UAtlas^3 and
       Size(Group(UAtlas,VAtlas))=20 then
      HomAtlas := GroupHomomorphismByImages(AddressF20Atlas,W33F20Atlas,
        [AddressTPermAtlas,AddressMPermAtlas],[UAtlas,VAtlas]);;
      if IsBijective(HomAtlas) then
        AllF20IsomorphismsAtlas:=AllF20IsomorphismsAtlas+1;
        CandidateMapsAtlas:=EquivariantMapsForAtlas(HomAtlas);;
        CandidateSiteMapsAtlas:=SiteMapsForAtlas(
          InducedSlowAtlas(UAtlas),InducedSlowAtlas(VAtlas));;
        AllIncidenceCandidatesAtlas:=AllIncidenceCandidatesAtlas+
          Length(CandidateMapsAtlas)*Length(CandidateSiteMapsAtlas);
        for CandidateMapAtlas in CandidateMapsAtlas do
          for CandidateSiteMapAtlas in CandidateSiteMapsAtlas do
            OverlapProfileAtlas:=List([1..5],site->Size(Intersection(
              Set(CandidateMapAtlas{[8*(site-1)+1..8*site]}),
              Set(TargetSupportsAtlas[CandidateSiteMapAtlas[site]]))));;
            Add(IncidenceOverlapTotalsAtlas,Sum(OverlapProfileAtlas));;
            Add(IncidenceOverlapProfilesAtlas,
              JoinIntsAtlas(SortedList(OverlapProfileAtlas)));;
            if ForAll(OverlapProfileAtlas,x->x=8) then
                CoherentIncidenceMapsAtlas:=CoherentIncidenceMapsAtlas+1;
            fi;
          od;
        od;
      fi;
    fi;
  od;
od;

SelectedOverlapProfileAtlas:=List([1..5],site->Size(Intersection(
  Set(CanonicalAddressAxisAtlas{[8*(site-1)+1..8*site]}),
  Set(TargetSupportsAtlas[CanonicalSiteCircuitAtlas[site]]))));;
MaximumOverlapAtlas:=Maximum(IncidenceOverlapTotalsAtlas);;
OverlapTotalHistogramAtlas:=JoinStringsWithSeparator(List(
  Set(IncidenceOverlapTotalsAtlas),total->Concatenation(String(total),":",
    String(Number(IncidenceOverlapTotalsAtlas,x->x=total)))),",");;
OverlapProfileHistogramAtlas:=JoinStringsWithSeparator(List(
  Set(IncidenceOverlapProfilesAtlas),profile->Concatenation(profile,":",
    String(Number(IncidenceOverlapProfilesAtlas,x->x=profile)))),";");;
BestOverlapProfilesAtlas:=Set(List(Filtered([1..Length(IncidenceOverlapTotalsAtlas)],
  i->IncidenceOverlapTotalsAtlas[i]=MaximumOverlapAtlas),
  i->IncidenceOverlapProfilesAtlas[i]));;

# Compose the chosen address gauge with the already-proved Payne staging rule.
# Every selected address axis misses its matched circuit target, yet has a
# commuting W33-axis neighbour among the eight covers through that target.
SymplecticAtlas:=function(a,b)
  local x,y;
  x:=Points40Atlas[a];y:=Points40Atlas[b];
  return x[1]*y[3]-x[3]*y[1]+x[2]*y[4]-x[4]*y[2];
end;;
StageDistanceAtlas:=function(axis,target)
  if axis in TargetSupportsAtlas[target] then return 0;fi;
  if ForAny(TargetSupportsAtlas[target],candidate->
    SymplecticAtlas(axis,candidate)=Zero3Atlas) then return 1;fi;
  return 2;
end;;
SelectedStageDistancesAtlas:=List([1..40],address->StageDistanceAtlas(
  CanonicalAddressAxisAtlas[address],
  CanonicalSiteCircuitAtlas[QuoInt(address-1,8)+1]));;

# Generator-level identification of the qutrit D10<F20 chain with the
# line-preserving inner/outer chain in W(E6).
SiteToOuterHomAtlas := GroupHomomorphismByImages(SiteF20Atlas,OuterF20Atlas,
  [SiteTAtlas,SiteMAtlas],[OuterAAtlas,OuterBAtlas]);;
if not IsBijective(SiteToOuterHomAtlas) then Error("site-to-outer F20 map failed"); fi;
OuterSiteLineMapsAtlas := [];;
for TargetAtlas in BaseLineAtlas do
  SiteMapAtlas:=List([1..5],x->0);GoodAtlas:=true;
  for ElementAtlas in Elements(SiteF20Atlas) do
    SourceAtlas:=1^ElementAtlas;
    DestAtlas:=TargetAtlas^Image(SiteToOuterHomAtlas,ElementAtlas);
    if SiteMapAtlas[SourceAtlas]=0 then SiteMapAtlas[SourceAtlas]:=DestAtlas;
    elif SiteMapAtlas[SourceAtlas]<>DestAtlas then GoodAtlas:=false;fi;
  od;
  if GoodAtlas and Length(Set(SiteMapAtlas))=5 then Add(OuterSiteLineMapsAtlas,SiteMapAtlas);fi;
od;
if Length(OuterSiteLineMapsAtlas)<>1 then Error("site-to-ROM-line map is not unique");fi;
OuterIntersectionAtlas:=Intersection(OuterF20Atlas,InnerAAtlas);;
BareD10Atlas:=Group(SiteTAtlas,SiteMAtlas^2);;
if PreImage(SiteToOuterHomAtlas,OuterIntersectionAtlas)<>BareD10Atlas then
  Error("D10 inner/outer preimage mismatch");
fi;

PayneEquivarianceAtlas :=
  ForAll([1..40],axis->Set(List(PayneCovers[axis],x->x^SlowTAtlas))=
    Set(PayneCovers[axis^W33TAtlas])) and
  ForAll([1..40],axis->Set(List(PayneCovers[axis],x->x^SlowMAtlas))=
    Set(PayneCovers[axis^W33MAtlas]));;

ChecksAtlas := [
  Size(AutAAtlas)=51840,Size(InnerAAtlas)=25920,
  Size(InnerLineImageAtlas)=60,StructureDescription(InnerLineImageAtlas)="A5",
  Size(FullLineImageAtlas)=120,StructureDescription(FullLineImageAtlas)="S5",
  Size(InnerLineKernelAtlas)=16,Size(FullLineKernelAtlas)=16,
  Size(OuterF20Atlas)=20,StructureDescription(OuterF20Atlas)="C5 : C4",
  Size(OuterIntersectionAtlas)=10,StructureDescription(OuterIntersectionAtlas)="D10",
  Size(BareD10Atlas)=10,Size(Kernel(ActionHomomorphism(OuterF20Atlas,BaseLineAtlas,OnPoints)))=1,
  OrbitSizesAtlas(AddressF20Atlas,[1..40],fail)=[20,20],
  OrbitSizesAtlas(W33F20Atlas,[1..40],fail)=[20,20],
  Length(AddressAxisMapsAtlas)=800,Order(BasisCrosswalkAtlas)=2,
  Size(SlowF20Atlas)=20,StructureDescription(SlowF20Atlas)="C5 : C4",
  OrbitSizesAtlas(SlowF20Atlas,[1..45],fail)=[5,10,10,20],
  OrbitSizesAtlas(SlowF20Atlas,GQLinesB,OnSets)=[2,5,10,10],
  SlowFiveEdgesAtlas=0,Size(SlowFiveStabAtlas)=120,
  StructureDescription(SlowFiveActionAtlas)="S5",
  Length(Orbit(InnerBAtlas,Set(SlowFiveOrbitAtlas),OnSets))=216,
  Length(SiteCircuitMapsAtlas)=1,PayneEquivarianceAtlas,
  AllF20IsomorphismsAtlas=20,AllIncidenceCandidatesAtlas=16000,
  CoherentIncidenceMapsAtlas=0,
  Length(IncidenceOverlapTotalsAtlas)=AllIncidenceCandidatesAtlas,
  MaximumOverlapAtlas<40,SelectedOverlapProfileAtlas=[0,0,0,0,0],
  Set(SelectedStageDistancesAtlas)=[1]
];;
if not ForAll(ChecksAtlas,x->x) then Error("F20 Payne five-state atlas failed");fi;

Print("F20_PAYNE_ATLAS|status=PASS",
  "|autOrder=",Size(AutAAtlas),"|innerOrder=",Size(InnerAAtlas),
  "|innerLineStabOrder=",Size(InnerLineStabAtlas),
  "|innerLineImageOrder=",Size(InnerLineImageAtlas),
  "|innerLineImage=",StructureDescription(InnerLineImageAtlas),
  "|fullLineStabOrder=",Size(FullLineStabAtlas),
  "|fullLineImageOrder=",Size(FullLineImageAtlas),
  "|fullLineImage=",StructureDescription(FullLineImageAtlas),
  "|lineKernelOrder=",Size(FullLineKernelAtlas),
  "|outerF20ComplementClasses=",Length(OuterF20CandidatesAtlas),
  "|outerF20Order=",Size(OuterF20Atlas),
  "|outerF20Structure=",StructureDescription(OuterF20Atlas),
  "|outerInnerIntersectionOrder=",Size(OuterIntersectionAtlas),
  "|outerInnerIntersectionStructure=",StructureDescription(OuterIntersectionAtlas),
  "|outerSiteLineMap=",JoinIntsAtlas(OuterSiteLineMapsAtlas[1]),
  "|outerVertexOrbits=",JoinIntsAtlas(OrbitSizesAtlas(OuterF20Atlas,[1..45],fail)),
  "|outerLineOrbits=",JoinIntsAtlas(OrbitSizesAtlas(OuterF20Atlas,GQLinesA,OnSets)),
  "|basisCrosswalkOrder=",Order(BasisCrosswalkAtlas),
  "|addressOrbits=",JoinIntsAtlas(OrbitSizesAtlas(AddressF20Atlas,[1..40],fail)),
  "|w33Orbits=",JoinIntsAtlas(OrbitSizesAtlas(W33F20Atlas,[1..40],fail)),
  "|addressAxisBijections=",Length(AddressAxisMapsAtlas),
  "|canonicalAddressAxis=",JoinIntsAtlas(CanonicalAddressAxisAtlas),
  "|slowOrbits=",JoinIntsAtlas(OrbitSizesAtlas(SlowF20Atlas,[1..45],fail)),
  "|slowLineOrbits=",JoinIntsAtlas(OrbitSizesAtlas(SlowF20Atlas,GQLinesB,OnSets)),
  "|slowFiveOrbit=",JoinIntsAtlas(SortedList(SlowFiveOrbitAtlas)),
  "|slowFiveEdges=",SlowFiveEdgesAtlas,
  "|slowFiveStabOrder=",Size(SlowFiveStabAtlas),
  "|slowFiveStabImage=",StructureDescription(SlowFiveActionAtlas),
  "|slowFiveCarrierOrbit=",Length(Orbit(InnerBAtlas,Set(SlowFiveOrbitAtlas),OnSets)),
  "|siteCircuitMaps=",Length(SiteCircuitMapsAtlas),
  "|siteCircuitMap=",JoinIntsAtlas(CanonicalSiteCircuitAtlas),
  "|payneEquivariance=",PayneEquivarianceAtlas,
  "|presentationIsomorphisms=",AllF20IsomorphismsAtlas,
  "|incidenceCandidates=",AllIncidenceCandidatesAtlas,
  "|coherentIncidenceMaps=",CoherentIncidenceMapsAtlas,
  "|selectedOverlapProfile=",JoinIntsAtlas(SelectedOverlapProfileAtlas),
  "|maximumMatchedAddresses=",MaximumOverlapAtlas,
  "|bestOverlapProfiles=",JoinStringsWithSeparator(BestOverlapProfilesAtlas,";"),
  "|overlapTotalHistogram=",OverlapTotalHistogramAtlas,
  "|overlapProfileHistogram=",OverlapProfileHistogramAtlas,
  "|selectedStageDistances=",JoinIntsAtlas(SelectedStageDistancesAtlas),"\n");
