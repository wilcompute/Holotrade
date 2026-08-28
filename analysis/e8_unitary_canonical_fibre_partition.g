#############################################################################
## Canonicality of the 15 x 8 fibre partition.
##
## The earlier certificate found the fibres as orbits of O2 in one folded-cube
## model.  Here GAP recomputes the full graph automorphism group and proves its
## intrinsic 2-core has exactly those same fifteen orbits.  Thus the partition
## is graph-canonical even though the eight slots inside each fibre are not.
#############################################################################

E8CrossPrimeLibraryOnly := true;;
Read("analysis/e8_unitary_crossprime_fibre_differential.g");;
R := CrossPrimeFibreDifferential();;
A := R.fullAutomorphismGroup;;
N := PCore(A, 2);;
OrbitsN := List(Orbits(N, [1..120]), Set);;
SortBy(OrbitsN, orbit -> Minimum(orbit));;
MappedOrbits := List(OrbitsN, orbit -> Set(List(orbit,
  vertex -> vertex ^ R.graphIsomorphism)));;
SortBy(MappedOrbits, orbit -> Minimum(orbit));;
CertifiedBlocks := ShallowCopy(R.blocks);;
SortBy(CertifiedBlocks, orbit -> Minimum(orbit));;

BlockAction := Action(A, OrbitsN, OnSets);;
BlockHom := ActionHomomorphism(A, OrbitsN, OnSets);;
BlockKernel := Kernel(BlockHom);;
PointStabilizer := Stabilizer(A, 1);;
FibreKernel := Intersection(N, PointStabilizer);;

ChecksCanonical := [
  Size(A) = 23040,
  Size(N) = 32,
  IsNormal(A, N),
  StructureDescription(N) = "C2 x C2 x C2 x C2 x C2",
  StructureDescription(FactorGroup(A, N)) = "S6",
  Length(OrbitsN) = 15,
  Set(List(OrbitsN, Length)) = [8],
  MappedOrbits = CertifiedBlocks,
  Size(BlockAction) = 720,
  StructureDescription(BlockAction) = "S6",
  BlockKernel = N,
  Size(FibreKernel) = 4,
  StructureDescription(FactorGroup(N, FibreKernel)) = "C2 x C2 x C2",
  ForAll(GeneratorsOfGroup(A), generator ->
    Set(List(OrbitsN, orbit -> Set(List(orbit, x -> x^generator)))) = Set(OrbitsN))
];;
if not ForAll(ChecksCanonical, value -> value) then
  Error("canonical fibre partition checks failed");
fi;

Print("FULL_AUT|order=23040|structure=2^5:S6|O2=32|quotient=S6\n");
Print("CANONICAL_PARTITION|orbits=15|size=8|blockKernel=O2",
      "|matchesFrozen=1|invariantUnderFullAut=1\n");
Print("FIBRE_ACTION|O2pointKernel=4|induced=C2^3",
      "|partitionCanonical=1|slotCanonical=0\n");
Print("ALL_UNITARY_CANONICAL_FIBRE_PARTITION_CHECKS_PASS\n");
QUIT;
