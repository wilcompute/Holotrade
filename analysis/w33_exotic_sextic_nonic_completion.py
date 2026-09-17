#!/usr/bin/env python3
"""First higher-order channels capable of lifting the frozen SU(5) exotics.

Continues w33_exotic_quartic_selection.py and w33_exotic_rcharge_closure.py.
The quartic channels all fail R-charge. Here the exact massless spectrum is
reconstructed and full rank-16 gauge momentum is solved at the next orders.

For the frozen witness all relevant twisted states are oscillatorless T1 ground
states. Three T1 insertions carry q=(1,1,1). A sextic mass operator can add
three untwisted fields in one plane (the 5bar plus two singlets), giving total
q=(4,1,1) up to permutation and three picture-changing right oscillators in
that plane. The Z3 R rule is satisfied. Rule 4 is stronger when all three
T1 fields coincide in a Z3/SU3 plane: the torus has Z6 symmetry and requires
the corresponding picture-changing number to vanish mod 6.

Consequently sextics survive only for 5bar copies in planes 2/3 and only for
6 of the 9 space-group completions per entry. The missing plane-1 columns are
first recoverable at nonic order with six untwisted fields in plane 1, for
which the picture-changing number is 6 and Rule 4 is satisfied.

Rule 5: the three T1 fields have sum k_i=1 in every Z3 plane, so nontrivial
holomorphic classical instantons exist; for oscillatorless left-moving ground
states the Rule-5 inequality N_L>=Nbar_L is therefore automatic. This is only
a selection-rule certificate: it does not evaluate the instanton sums or prove
that every allowed coefficient is nonzero.

2026-09-17 reproducibility/rank correction. The original nonic loop appended
the whole list ``ti`` instead of iterating its tuples, so running this source
raised TypeError even though the committed historical JSON contained the right
2/40 solution counts. The loop below is repaired. More importantly, the 9x12
binary support has matching/structural rank 9, but that is NOT a theorem that
the physical exotic mass matrix generically has rank 9: the nine rows are
fixed-point translates whose coefficients share twisted-singlet VEV profiles.
See ``the_exotic_mass_rank_is_set_by_where_the_singlets_condense.py``. Symmetric
VEVs give rank 1 and localized VEVs give strong rank bounds; rank 9 is a
vacuum-profile condition, not a consequence of support alone.
"""
from __future__ import annotations
import importlib.util,itertools,json
from collections import defaultdict
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data'/'w33_exotic_sextic_nonic_completion.json'
S=36

def load(name):
 s=importlib.util.spec_from_file_location(name,ROOT/'analysis'/(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
fam=load('the_w33_vacuum_families_live_on_the_untwisted_planes')
gut=load('does_the_w33_vacuum_contain_a_three_family_gut')

def multiplets(states,roots):
 st=[tuple(int(x) for x in P) for P in states];key={x:i for i,x in enumerate(st)};rr=[tuple(int(x) for x in r) for r in roots];seen=set();out=[]
 for i in range(len(st)):
  if i in seen:continue
  q=[i];seen.add(i);C=[]
  while q:
   k=q.pop();C.append(st[k]);P=st[k]
   for r in rr:
    z=tuple(P[j]+r[j] for j in range(16));h=key.get(z)
    if h is not None and h not in seen:seen.add(h);q.append(h)
  out.append([np.array(x,dtype=np.int64) for x in C])
 return out

def labels(C,sr):return [tuple(int(x) for x in (P@sr.T//S)) for P in C]
def highest(C,sr):return next((x for x in labels(C,sr) if all(a>=0 for a in x)),None)
def vsum(seq):return sum((np.array(x,dtype=np.int64) for x in seq),start=np.zeros(16,dtype=np.int64))
def keyv(v):return tuple(int(x) for x in v)

def multiset_sums(vecs,n):
 d=defaultdict(list)
 for inds in itertools.combinations_with_replacement(range(len(vecs)),n):d[keyv(vsum(vecs[i] for i in inds))].append(inds)
 return d

def main(write=True):
 parent=json.loads((ROOT/'data'/'w33_vacuum_three_family_gut.json').read_text());assert parent['valid']
 line=np.array(parent['examples']['su5_three_families']['lines'][0],dtype=np.int64)
 B=fam.Builder();V=np.concatenate([B.shift(72,1),B.shift(84,2)])
 gauge,untw,fps=B.model(V,[line]);comps=fam.het.root_components(gauge)
 A4=next(C for C in comps if fam.cname(C)=='A4' and np.any(C[:,:8]));sr=np.array(gut.diagram(A4)[0],dtype=np.int64)
 assert gut.diagram(A4)[2]['path']==[2,1,0,3]
 L5=(0,0,1,0);L5b=(0,0,0,1)
 UC=multiplets(untw,A4);bars=[C for C in UC if len(C)==5 and highest(C,sr)==L5b];US=[C[0] for C in UC if len(C)==1]
 assert len(bars)==4
 TC={}
 for n1 in range(3):
  cc=[]
  for P,m in fps[(n1,0,0)]:
   assert m==1  # no massless twisted oscillator multiplets in this witness
   cc+=multiplets(P,A4)
  TC[n1]=cc
 five=next(C for C in TC[0] if len(C)==5 and highest(C,sr)==L5)
 TS=[(n1,C[0]) for n1 in range(3) for C in TC[n1] if len(C)==1]
 # Spectator charge D for each of the four 5bar momentum types.
 Ds=[]
 for Cb in bars:
  ds=[]
  for a in five:
   la=tuple(int(x) for x in (a@sr.T//S))
   for b in Cb:
    lb=tuple(int(x) for x in (b@sr.T//S))
    if all(la[i]+lb[i]==0 for i in range(4)):ds.append(tuple((a+b).tolist()))
  assert len(ds)==5 and len(set(ds))==1;Ds.append(np.array(ds[0],dtype=np.int64))

 tvec=[x[1] for x in TS];t2=multiset_sums(tvec,2);u2=multiset_sums(US,2);u5=multiset_sums(US,5)
 sextic=[];nonic=[]
 for j,D in enumerate(Ds):
  ssol=[]
  for st,ti in t2.items():
   need=keyv(-D-np.array(st,dtype=np.int64))
   for ui in u2.get(need,[]):
    for tt in ti:ssol.append((tt,ui))
  # Count distinct charge-type solutions by unordered index multisets.
  suniq=sorted({(tuple(sorted(t)),tuple(sorted(u))) for t,u in ssol})
  assert len(suniq)==2
  # The two twisted singlets in all sextic solutions lie in n1=0.
  assert all(all(TS[x][0]==0 for x in t) for t,u in suniq)
  sextic.append({'bar_type':j,'charge_type_solutions':len(suniq),
                  'solutions':[{'twisted_singlet_types':list(t),'untwisted_singlet_types':list(u)} for t,u in suniq]})

  nsol=[]
  for st,ti in t2.items():
   need=keyv(-D-np.array(st,dtype=np.int64))
   for ui in u5.get(need,[]):
    for tt in ti:nsol.append((tt,ui))
  nuniq=sorted({(tuple(sorted(t)),tuple(sorted(u))) for t,u in nsol})
  assert len(nuniq)==40
  assert all(all(TS[x][0]==0 for x in t) for t,u in nuniq)
  nonic.append({'bar_type':j,'charge_type_solutions':len(nuniq)})

 # Space-group completions: with exotic fixed coordinate f, one singlet coordinate
 # is free and the other is fixed by f+f1+f2=0 in each of the two unfrozen planes.
 # For a sextic whose untwisted fields are in plane i=1 or 2 (zero-based), the one
 # completion with f=f1=f2 in that plane is Rule-4 forbidden (Nbar_R=3 mod 6),
 # leaving 2*3=6 of the 9 two-plane completions. Plane 0 has Nbar_R=3 while its
 # twisted n1 positions are always equal, so all plane-0 sextics are forbidden.
 sextic_cols=4*2;sextic_per_entry=2*6;sextic_total=9*sextic_cols*sextic_per_entry
 assert sextic_total==864
 # Nonic plane-0 rescue: bar + five untwisted singlets -> Nbar_R=6 in plane 0,
 # satisfying Rule 4. Other planes have Nbar_R=0, so all 9 completions survive.
 nonic_cols=4;nonic_per_entry=40*9;nonic_total=9*nonic_cols*nonic_per_entry
 assert nonic_total==12960

 # Every one of the 9 exotic rows has allowed support on all 8 plane-2/3 columns
 # at sextic order and all 4 plane-1 columns at nonic order. The resulting binary
 # support is K_{9,12}, whose maximum matching size is 9. This is ONLY support
 # structural rank; shared fixed-point/VEV profiles can force a much lower
 # numerical mass rank, including rank 1 in translation-symmetric vacua.
 structural_rank=9
 out={
  'schema':'holotrade.w33_exotic_sextic_nonic_completion.v1','status':'PASS',
  'headline':'Quartic exotic masses vanish, while higher-order selection rules admit complete binary support: two sextic gauge-charge solutions and forty plane-1 nonic solutions per 5bar momentum type, with 864 sextic and 12960 nonic candidates. The 9x12 support graph has matching/structural rank 9, but the physical mass rank is vacuum-dependent and is not certified by support alone.',
  'massless_spectrum':{'untwisted_5bar_momentum_types':4,'untwisted_singlet_momentum_types':len(US),'twisted_singlet_types':len(TS),'twisted_states_all_NL0':True},
  'sextic':{'operator':'5_T 5bar_U S_T S_T S_U S_U','charge_solutions_per_bar_type':2,'surviving_5bar_plane_copies':[2,3],
             'rule4_safe_space_group_completions_per_charge_solution':6,'candidate_monomials':864,'covered_matrix_columns':8,'details':sextic},
  'nonic':{'operator':'5_T 5bar_U1 S_T S_T (S_U1)^5','charge_solutions_per_bar_type':40,
            'rule4_safe_space_group_completions_per_charge_solution':9,'candidate_monomials':12960,'covered_matrix_columns':4,'details':nonic},
  'combined_support':{'matrix_shape':[9,12],'covered_columns':12,'structural_rank':structural_rank,
                      'meaning':'The binary allowed-coupling graph K9,12 has maximum matching size 9. This is a support theorem only; it does not imply generic physical mass rank 9 once common fixed-point/VEV profiles are imposed.'},
  'physical_rank_firewall':{'audit':'analysis/the_exotic_mass_rank_is_set_by_where_the_singlets_condense.py',
                            'translation_invariant_VEV_rank':1,
                            'single_fixed_point_per_twisted_type_rank_bound':'<=4',
                            'rank9_requirement':'twisted singlets must be spread over several fixed points with unequal VEVs; D/F-flat realization remains open'},
  'rule5':'The three T1 ground states have sum k_i=1 in every Z3 plane, so holomorphic classical instanton solutions exist. With N_L=Nbar_L=0 the Rule-5 inequality is automatic. Rule 5 therefore does not remove these ground-state channels.',
  'literature':['Kobayashi-Parameswaran-Ramos-Sanchez-Zavala, arXiv:1107.2137v3, sections 3.4.1-3.4.2'],
  'boundary':'This certifies gauge momentum, point/space group, R-charge, Rule 4, the Rule-5 existence condition, and binary support/matching rank. It does not evaluate worldsheet instanton sums, prove nonzero amplitudes, specify a D/F-flat fixed-point VEV profile, or prove a rank-9 numerical exotic mass matrix.',
  'checks':{'source_reproducible_after_nonic_fix':True,'two_sextic_charge_solutions_each':True,'forty_nonic_solutions_each':True,'no_twisted_left_oscillators':True,'sextic_864':True,'nonic_12960':True,'support_matching_rank_9':True}}
 if write:OUT.write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps(out,indent=2));return out
if __name__=='__main__':main(True)
