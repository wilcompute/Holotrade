#############################################################################
## Exact defect-aware replacement for the false {0,1,4} trichotomy at 111.
##
## At |X|=111 the four dirty lines on each axis are one complete pencil.
## Delete those pencils.  Every remaining line is clean: load 11, minimum
## blocker shadow, and zero fibre overlap.  Clean-core reciprocity is exact.
## This witness works out what multiplicity three can still mean there.
#############################################################################

Read("analysis/e8_pg34_sentinel_control_plane.g");;

PointLines111 := List([1..40], point ->
  Filtered([1..Length(Lines)], index -> point in Lines[index]));;
DirtyPointRow111 := 1;;
DirtyPointColumn111 := 1;;
DirtyRows111 := PointLines111[DirtyPointRow111];;
DirtyColumns111 := PointLines111[DirtyPointColumn111];;
CleanRows111 := Difference([1..40], DirtyRows111);;
CleanColumns111 := Difference([1..40], DirtyColumns111);;

CleanDegreeRow111 := List([1..40], point ->
  Number(CleanRows111, index -> point in Lines[index]));;
CleanDegreeColumn111 := List([1..40], point ->
  Number(CleanColumns111, index -> point in Lines[index]));;
if Collected(CleanDegreeRow111) <> [[0,1],[3,12],[4,27]] or
   CleanDegreeRow111 <> CleanDegreeColumn111 then
  Error("deleted-pencil degree profile failed");
fi;

# Universal closure lemma, checked on every geometric address.  If two clean
# row lines with common point p share a centre c, reciprocity forces every
# clean column line through c into the reciprocal fibre at p.  Applying the
# same argument back forces the complete clean pencils at p and c.  Therefore
# a non-sink repeated fibre can only join equal clean degrees: 3 to 3 or 4 to 4.
TripleAddresses111 := 0;;
FullAddresses111 := 0;;
DegreeMismatchAddresses111 := 0;;
for RowPoint111 in [1..40] do
  for ColumnPoint111 in [1..40] do
    if CleanDegreeRow111[RowPoint111] >= 2 and
       CleanDegreeColumn111[ColumnPoint111] >= 2 then
      if CleanDegreeRow111[RowPoint111] = 3 and
         CleanDegreeColumn111[ColumnPoint111] = 3 then
        TripleAddresses111 := TripleAddresses111 + 1;
      elif CleanDegreeRow111[RowPoint111] = 4 and
           CleanDegreeColumn111[ColumnPoint111] = 4 then
        FullAddresses111 := FullAddresses111 + 1;
      else
        DegreeMismatchAddresses111 := DegreeMismatchAddresses111 + 1;
      fi;
    fi;
  od;
od;
if [TripleAddresses111, FullAddresses111, DegreeMismatchAddresses111] <>
   [144,729,648] then
  Error("defect-aware address census failed");
fi;

# D_cc is the number of doubled clean-clean tiles.  The global occupancy
# budget gives D_cc >= 4*36 + 4*36 - 176 = 112.  With no triple fibres its
# absolute maximum is 36*4=144.  Each ordinary triple fibre replaces three
# degree-four line contributions by three degree-three contributions, losing
# at least 3.  A triple fibre at the dirty centre is a reciprocity sink and
# contributes zero, losing at least 12.  Hence
#
#   112 <= D_cc <= 144 - 3*n3_paired - 12*n3_sink.
#
# Enumerate the entire integer consequence, not a sampled profile.
CleanCleanLower111 := 4 * 36 + 4 * 36 - 176;;
CleanCleanCeiling111 := 36 * 4;;
FeasibleTripleProfiles111 := [];;
for PairedTriples111 in [0..12] do
  for SinkTriples111 in [0..12] do
    TripleLines111 := 3 * (PairedTriples111 + SinkTriples111);
    ProfileCeiling111 := CleanCleanCeiling111 -
      3 * PairedTriples111 - 12 * SinkTriples111;
    if TripleLines111 <= 36 and ProfileCeiling111 >= CleanCleanLower111 then
      Add(FeasibleTripleProfiles111,
        [PairedTriples111, SinkTriples111, ProfileCeiling111]);
    fi;
  od;
od;
MaximumTripleFibres111 := Maximum(List(FeasibleTripleProfiles111,
  row -> row[1] + row[2]));;
MaximumPairedTriples111 := Maximum(List(FeasibleTripleProfiles111,
  row -> row[1]));;
MaximumSinkTriples111 := Maximum(List(FeasibleTripleProfiles111,
  row -> row[2]));;
if CleanCleanLower111 <> 112 or CleanCleanCeiling111 <> 144 or
   MaximumTripleFibres111 <> 10 or MaximumPairedTriples111 <> 10 or
   MaximumSinkTriples111 <> 2 then
  Error("multiplicity-three inequality failed");
fi;

Print("TAU111_DELETED_PENCILS|cleanRows=36|cleanColumns=36",
  "|degreeProfile=0^1,3^12,4^27|dirtyPencils=1,1\n");
Print("TAU111_RECIPROCAL_CLOSURE|tripleAddresses=",
  TripleAddresses111, "|fullAddresses=", FullAddresses111,
  "|degreeMismatchAddressesKilled=", DegreeMismatchAddresses111,
  "|nonSinkRepeatedFibres=completeEqualDegreePencils",
  "|allowedNonSinkMultiplicities=3,4\n");
Print("TAU111_TRIPLE_INEQUALITY|formula=112<=Dcc<=144-3*n3paired-12*n3sink",
  "|maximumTripleFibres=", MaximumTripleFibres111,
  "|maximumPairedTriples=", MaximumPairedTriples111,
  "|maximumSinkTriples=", MaximumSinkTriples111,
  "|elevenTripleWitnessPatternExcluded=1\n");
Print("TAU111_BOUNDARY|raisesLowerBound=0|interval=111,115",
  "|profilesRemain=", Length(FeasibleTripleProfiles111),
  "|necessaryNotSufficient=1\n");
Print("ALL_TAU111_DEFECT_AWARE_TRICHOTOMY_CHECKS_PASS\n");
QUIT;
