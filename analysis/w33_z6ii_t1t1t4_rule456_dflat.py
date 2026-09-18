#!/usr/bin/env python3
"""Close Rule 4/5/6 for the explicit T1*T1*T4 exotic mass channel.

Parent channel:
  T1(local E6 5) * T1(local E6 5bar_exotic) * T4 singlet s
with no left-moving oscillator excitations on any of the three fields.

For the extra heterotic-orbifold worldsheet rules:
  * Rule 4 and Rule 6 are congruence conditions on oscillator-number
    differences when the relevant lattice/coset symmetries are active.
    Every oscillator number is zero here, so every such congruence is 0 mod K.
  * Rule 5 depends on which holomorphic/anti-holomorphic instantons exist.
    With zero oscillator numbers every allowed inequality N_L>=Nbar_L or
    N_L<=Nbar_L+Nbar_R and every no-instanton equality
    N_L=Nbar_L+Nbar_R is satisfied identically.

Thus Rules 4,5,6 do not kill this cubic.

A separate exact D-flat observation is also frozen.  The T4 singlet
  s=(1,-1,-3,3,3,3,3,3)/6
has the opposite shifted gauge momentum -s in the T2 N_L=0 shell.  The latter
passes the order-two Wilson projection and one of the physical gamma/chirality
projections. Equal magnitudes |<s>|=|<-s>| cancel every first-E8 Cartan
D-term exactly because the charge vectors are opposite.

F-flatness is NOT certified.  A D-flat pair is only a candidate until the
full singlet superpotential (including possible T2*T4*U moduli and higher
couplings) is enumerated.  No claim of exotic decoupling is made without that.
"""
from fractions import Fraction as F
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/w33_z6ii_t1t1t4_rule456_dflat.json'

V=(F(1,6),F(1,3),F(-1,2),0,0,0,0,0)
W2=(F(-1),F(1,2),0,F(-1),F(-1),F(-1,2),F(-1,2),F(-1,2))
s=tuple(F(x,6) for x in (1,-1,-3,3,3,3,3,3))
v=(F(1,6),F(1,3),F(-1,2),0)
rL=(0,0,1,0);rR=(-1,-1,1,0)
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def t2_project(q,chir,gamma):
    r=rL if chir=='L' else rR
    qg=F(0) if gamma==1 else F(1,2)
    rg=tuple(F(r[i])+2*v[i] for i in range(4))
    return (3*(qg-dot(rg,v)+dot(q,V))).denominator==1 and dot(q,W2).denominator==1

def main(write=True):
    sm=tuple(-x for x in s)
    proj={(c,g):t2_project(sm,c,g) for c in ('L','R') for g in (1,-1)}
    assert proj[('L',-1)] and proj[('R',1)]
    assert dot(sm,W2).denominator==1
    assert all(s[i]+sm[i]==0 for i in range(8))
    # No-oscillator Rule 4/6 congruence representatives.
    osc_delta=[0,0,0]
    assert all(x==0 for x in osc_delta)
    # T1,T1,T4 twist fractions in the three complex planes.
    twists=[(F(1,6),F(1,6),F(2,3)),
            (F(1,3),F(1,3),F(1,3)),
            (F(1,2),F(1,2),F(0))]
    assert all(sum(t)==1 for t in twists)
    out={'schema':'w33.z6ii_t1t1t4_rule456_dflat.v1',
      'status':'PASS_RULE456_AND_DFLAT__FFLAT_OPEN',
      'coupling':'T1*T1*T4 local vectorlike 5*5bar*s',
      'worldsheet_rules':{
        'Rule4':'PASS: all oscillator-number differences vanish, hence every active torus-lattice congruence is 0 mod K',
        'Rule5':'PASS: with no oscillators all holomorphic/antiholomorphic inequalities and no-instanton equalities are satisfied',
        'Rule6':'PASS: all oscillator-number differences vanish, hence every active coset-vector congruence is 0',
        'twist_sum_per_plane':['1','1','1']},
      'D_flat_pair':{
        'T4_s':[str(x) for x in s],
        'T2_opposite':[str(x) for x in sm],
        'opposite_full_rank8_charge':True,
        'T2_projection_survival':{f'{c}_gamma{g:+d}':ok for (c,g),ok in proj.items()},
        'equal_magnitude_vevs_cancel_all_first_E8_Cartan_D_terms':True},
      'F_flatness':'OPEN: requires the complete singlet superpotential; an opposite-charge D-flat pair alone is not an all-order F-flat proof',
      'mass_channel_consequence':'The extra Rule 4/5/6 worldsheet constraints do not remove the previously certified cubic exotic mass channel. Decoupling still requires a compatible supersymmetric VEV and nonzero CFT coefficient.',
      'literature':['Kobayashi et al. 2011 Rule 4/5','Cabo Bizet et al. 2013 Rule 4/6'] }
    if write:OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2));return out
if __name__=='__main__':main(True)
