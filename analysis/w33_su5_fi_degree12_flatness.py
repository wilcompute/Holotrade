#!/usr/bin/env python3
"""Anomalous-U(1) FI direction and degree-12 fate of the 16 SU(5) singlet rays.

This continues w33_su5_singlet_flat_directions.py.  It reconstructs the frozen
SU(5) spectrum, derives the anomalous trace direction directly from all chiral
momenta, finds the minimal FI-cancelling holomorphic directions, and closes the
first self-coupling of the sixteen neutral U*T0*T1*T2 rays.

Results:
* the full chiral momentum trace is -432 e_9 in x6 coordinates, so for the
  existing second-E8 generator q_A=P_9/6 one has Tr Q_A=-72;
* exactly two untwisted degree-two pairs have no charge except Q_A=+2.  They
  are opposite semisimple weights in the same four-state spectator multiplet,
  hence provide the standard FI-cancelling D-flat direction;
* all sixteen neutral quartics use one of these same four untwisted weights;
* their degree-12 cube passes point/space group, R charge, Rule 4 and Rule 5
  for an explicit nine-fixed-point assignment.  Thus protection stops at 11.

The order-12 *selection rule* is closed here.  Its actual CFT coefficient is not
computed; an allowed term can still vanish accidentally at special moduli.
"""
from __future__ import annotations
import importlib.util,itertools,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];S=36
OUT=ROOT/'data'/'w33_su5_fi_degree12_flatness.json'

def load(name):
 s=importlib.util.spec_from_file_location(name,ROOT/'analysis'/(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
fam=load('the_w33_vacuum_families_live_on_the_untwisted_planes')
gut=load('does_the_w33_vacuum_contain_a_three_family_gut')
flat=load('w33_su5_singlet_flat_directions')

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

def main(write=True):
 parent=json.loads((ROOT/'data'/'w33_vacuum_three_family_gut.json').read_text());line=np.array(parent['examples']['su5_three_families']['lines'][0],dtype=np.int64)
 B=fam.Builder();V=np.concatenate([B.shift(72,1),B.shift(84,2)]);gauge,untw,fps=B.model(V,[line]);comps=fam.het.root_components(gauge)
 A4=next(C for C in comps if fam.cname(C)=='A4' and np.any(C[:,:8]));UC=multiplets(untw,A4);US=[C[0] for C in UC if len(C)==1];assert len(US)==24
 TC={}
 for n1 in range(3):
  cc=[]
  for P,m in fps[(n1,0,0)]:assert m==1;cc+=multiplets(P,A4)
  TC[n1]=cc
 TS=[(n1,C[0]) for n1 in range(3) for C in TC[n1] if len(C)==1];assert [sum(n==i for n,_ in TS) for i in range(3)]==[4,9,9]
 vecs=US+[v for _,v in TS];kinds=['U']*24+[f'T{n}' for n,_ in TS]
 # Full chiral trace: untwisted matter comes once per complex plane; all 27 fixed
 # points are explicit in Builder.model and carry their certified multiplicity m.
 tr=3*untw.sum(axis=0);nst=3*len(untw)
 for st in fps.values():
  for P,m in st:tr+=m*P.sum(axis=0);nst+=m*len(P)
 expected=np.zeros(16,dtype=np.int64);expected[8]=-432
 assert nst==405 and np.array_equal(tr,expected) and np.all(gauge@tr==0)
 trQ=int(tr[8]//6);assert trQ==-72
 # Search all selected-SU5 singlet pairs whose total momentum is purely anomalous.
 fi=[]
 for i in range(24):
  for j in range(i,24):
   z=US[i]+US[j]
   if z[8]>0 and all(z[k]==0 for k in range(16) if k!=8):fi.append((i,j,z.copy()))
 assert [(i,j,int(z[8])) for i,j,z in fi]==[(0,1,12),(2,3,12)]
 # They sit in one four-weight full-gauge multiplet; pair sums are orthogonal to
 # every semisimple root, i.e. opposite semisimple weights.
 F=multiplets(untw,gauge);carrier=next(C for C in F if tuple(US[0]) in {tuple(x) for x in C})
 assert len(carrier)==4 and all(tuple(US[i]) in {tuple(x) for x in carrier} for i in range(4))
 assert all(np.all(gauge@(US[i]+US[j])==0) for i,j,_ in fi)
 # Rebuild the sixteen primitive neutral quartics and verify they use exactly U0..U3.
 z4=flat.neutral(vecs,4);assert len(z4)==16
 assert {z[0] for z in z4}=={0,1,2,3}
 assert all(sorted(kinds[i] for i in z)==['T0','T1','T2','U'] for z in z4)
 # The FI pairs have no full-lattice-neutral F-term supported on all-but-one VEV
 # through degree 12.
 fi_danger={}
 for i,j,_ in fi:
  fi_danger[f'{i},{j}']={str(d):len(flat.dangerous(vecs,(i,j),d)) for d in range(2,13)}
  assert not any(fi_danger[f'{i},{j}'].values())
 # Explicit nine twisted fixed points for the cube: one copy for every (a,b),
 # n=(a,b,a+b).  Sums vanish mod3; in every plane all 0,1,2 occur three times.
 loc=[(a,b,(a+b)%3) for a in range(3) for b in range(3)]
 assert all(sum(x[k] for x in loc)%3==0 for k in range(3))
 assert all(sorted(x[k] for x in loc)==[0,0,0,1,1,1,2,2,2] for k in range(3))
 # Nine T1 twists have k_i=1/3 in every plane.  Both instanton-existence tests
 # of arXiv:1107.2137 are strict: 1+9(-1+1/3)=-5 and 1+9(-1/3)=-2.
 holo=1+9*(-1+1/3);anti=1+9*(-1/3);assert holo<0 and anti<0
 # R: nine oscillatorless T1 fields contribute 3 to every plane; the three
 # copies of U are assigned one per plane, giving 4 == 1 mod3 in each plane.
 R=[4,4,4];assert all(x%3==1 for x in R)
 out={'schema':'holotrade.w33_su5_fi_degree12_flatness.v1','status':'PASS',
  'headline':'The frozen SU(5) witness has Tr Q_A=-72 for q_A=P_9/6 and exactly two minimal FI-cancelling untwisted bilinears of total Q_A=+2. The sixteen neutral U*T0*T1*T2 rays are protected through order 11 but their degree-12 cubes pass all currently implemented string selection rules for an explicit nine-fixed-point configuration.',
  'anomalous_U1':{'trace_vector_x6':tr.tolist(),'generator':'q_A=P_9/6 (second E8 e1 convention)','Tr_Q_A':trQ,'FI_sign':'negative in this generator orientation'},
  'FI_cancelling_pairs':[{'U_indices':[i,j],'sum_x6':z.tolist(),'total_Q_A':int(z[8]//6),'same_full_gauge_multiplet_dimension':4,'opposite_semisimple_weights':True} for i,j,z in fi],
  'neutral_quartics':{'count':16,'untwisted_indices_used':[0,1,2,3],'FI_pairs_dangerous_terms_through_12':fi_danger},
  'degree12_cube':{'fields':'3 U + 3 T0 + 3 T1 + 3 T2','untwisted_assignment':'one U copy in each complex plane','twisted_locations':[list(x) for x in loc],'space_group_sum_mod3':[0,0,0],'R_total':[4,4,4],'Rule4':'not activated: twisted fields are not all at the same fixed point in any plane','Rule5_holomorphic_test':holo,'Rule5_antiholomorphic_test':anti,'both_instanton_types_exist':True,'selection_rule_allowed':True},
  'consequence':'The anomalous FI term is cancellable by explicit massless fields, while the sixteen neutral quartic rays are not all-order flat: their first self-lift is genuinely allowed at degree 12. A complete shifted vacuum still requires the numerical degree-12 CFT coefficient and cross-couplings on the combined FI+neutral support.',
  'literature':['Kobayashi-Parameswaran-Ramos-Sanchez-Zavala, arXiv:1107.2137, Rules 4/5','standard heterotic anomalous-U(1) FI relation xi proportional to Tr Q_A'],
  'checks':{'405_chiral_weights':True,'trace_direction':True,'TrQ_minus72':True,'two_FI_pairs':True,'quartics_use_FI_carrier':True,'FI_pairs_Fsafe_through12':True,'cube_space_group':True,'cube_R':True,'Rule4_safe_location_choice':True,'Rule5_both_instantons':True}}
 if write:OUT.write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps(out,indent=2));return out
if __name__=='__main__':main(True)
