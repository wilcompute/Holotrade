#!/usr/bin/env python3
"""Incidence-level identification of the 45-target slow path with Payne(W33).

The nine new Payne hyperbolic lines are shown to dualize to the nine-target
slow-path cover, and that anchored cover is required to extend equivariantly to
all 40 W33 axes under the same 80 PSp(4,3) transvection generators.
"""
from __future__ import annotations
import json
from pathlib import Path
from w33_payne_slowpath_core import w33,payne,slow_dual,adj,gq24,isomorphisms,actions,ovoid,equivariant_covers,eset
ROOT=Path(__file__).resolve().parents[1]

def main():
 rom=json.loads((ROOT/'data/the_45_slot_rom_bijection.json').read_text())
 assert rom.get('schema')=='holotrade.45-slot-rom-bijection.v1' and rom.get('valid') is True
 P,W=w33();base=0;O,old,new=payne(P,W,base);S=old+new;T=slow_dual(rom);PA,SA=actions(P,rom)
 assert gq24(adj(27,S)) and gq24(adj(27,T))
 toslot={l:i for i,l in enumerate(T)};chosen=None;tried=0;seen=set()
 for iso in isomorphisms(S,T):
  tried+=1
  z=frozenset(toslot[frozenset(iso[x] for x in l)] for l in new)
  if z in seen:continue
  seen.add(z)
  if not ovoid(z,rom['linesB']):continue
  C=equivariant_covers(base,z,PA,SA)
  if C is not None:chosen=(iso,z,C);break
 assert chosen is not None,f'no PSp-compatible Payne/slow isomorphism after {tried} candidates'
 iso,z,C=chosen
 line_slot={l:toslot[frozenset(iso[x] for x in l)] for l in S};oldslots=sorted(line_slot[l] for l in old);newslots=sorted(line_slot[l] for l in new)
 image={frozenset(iso[x] for x in l) for l in S};inter=all(C[a[p]]==eset(b,C[p]) for a,b in zip(PA,SA) for p in range(40));allov=all(ovoid(q,rom['linesB']) for q in C.values())
 checks={
  'w33_40_points_40_lines':len(P)==len(W)==40,
  'payne_points_are_27_opposites':len(O)==27,
  'payne_line_split_36_plus_9':len(old)==36 and len(new)==9,
  'nine_new_payne_lines_partition_27':all(sum(v in l for l in new)==1 for v in range(27)),
  'payne_is_gq_2_4':gq24(adj(27,S)),
  'slow_dual_is_gq_2_4':gq24(adj(27,T)),
  'all_45_lines_map_exactly':image==set(T),
  'new_payne_lines_are_nine_target_ovoid':ovoid(z,rom['linesB']),
  'anchored_cover_extends_to_40_distinct_covers':len(C)==40 and len(set(C.values()))==40,
  'all_40_covers_are_ovoids':allov,
  'cover_map_intertwines_all_80_transvections':inter,
  'old_new_targets_partition_45':len(set(oldslots)|set(newslots))==45 and not(set(oldslots)&set(newslots)),
 }
 status='PASS' if all(checks.values()) else 'FAIL'
 out={
  'schema':'holotrade.slow-path-is-payne-derivative.v1','status':status,'checks':checks,
  'baseW33Point':base,'baseW33Vector':list(P[base]),
  'payne':{'points':27,'oldLines':36,'newHyperbolicLines':9,'totalLines':45},
  'slowDual':{'pointsAreRomBanks':27,'linesAreExpensiveTargets':45,'incidenceIsomorphism':{str(O[i]):iso[i] for i in range(27)}},
  'baseCover':{'newPayneLineTargetSlots':newslots,'oldPayneLineTargetSlots':oldslots,'isNineTargetOvoid':ovoid(z,rom['linesB'])},
  'equivariant40':{'generatorsChecked':len(PA),'covers':{str(p):sorted(q) for p,q in sorted(C.items())},'bijective':len(set(C.values()))==40,'intertwines':inter},
  'theorem':'The committed 45-target GQ(4,2) slow path is dual to the Payne-derived GQ(2,4) of W(3,3). Under an incidence isomorphism compatible with the same PSp(4,3) transvection action, the nine new Payne hyperbolic lines are exactly a nine-target slow-path ovoid; transporting this construction over the 40 W33 points gives 40 distinct ovoid covers equivariantly.',
  'machineReading':'A cheap W33 opcode axis does not merely index an unexplained nine-target cover. Fixing that axis and Payne-deriving W33 produces 36 inherited lines plus nine new hyperbolic lines; after duality those nine new lines are the expensive-target cover. The fast/slow ISA split is the old/new line split of Payne derivation.',
  'boundary':'Exact at q=3 for the committed W33 realization and fixed 45-slot ROM. The incidence map and all 40 covers are checked finitely; no q-general theorem, hardware performance, or physical quantum claim is inferred.',
  'search':{'incidenceIsomorphismsTried':tried,'distinctCandidateOvoidsTested':len(seen)}
 }
 if '--write' in __import__('sys').argv:(ROOT/'data/slow_path_is_payne_derivative.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
 print(json.dumps(out,indent=2,sort_keys=True));return 0 if status=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
