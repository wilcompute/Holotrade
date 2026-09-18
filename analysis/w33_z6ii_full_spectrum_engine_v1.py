#!/usr/bin/env python3
"""All-sector Z6-II spectrum engine v1 with anomaly sentinel.

This is the first single executable on this branch that covers every orbifold
sector type needed for the explicit witness:

  U      exact E8-root projections;
  T1     full Chemtob--Hosteins B.3-B.5 six-h GSO including all massless
         oscillator shells and all 12 fixed points;
  T5     typed as the CPT partner of T1;
  T2/T4 fixed-torus B.8 projections, both 4D chiralities, both gamma
         eigenvalues, and all allowed left oscillator energies;
  T3     self-conjugate B.8 projection, both 4D chiralities, gamma=1,w,w^2
         with geometric multiplicities D=4,2,2, and all allowed oscillator
         energies.

The engine deliberately contains anomaly sentinels.  After benchmarking the
T2/T4 multiplicities and T3 vector right-movers against Chemtob--Hosteins,
the combined SU(3)^3 anomaly closes exactly.  Hypercharge-related anomalies
do not yet close, so the output is still NOT admitted as a physical spectrum.
This is exactly what the sentinel is for: some remaining convention in the
T2/T3/T4 chirality/CPT bookkeeping or projection must be audited before any
three-family/MSSM claim.

The engine nevertheless closes the software architecture: all sector formulas,
oscillator shells, gamma multiplicities and representation decompositions now
live in one place and the failure is reproducible rather than hidden.
"""
from __future__ import annotations
import json
from collections import Counter
from fractions import Fraction as F
from pathlib import Path
import w33_z6ii_t1_full_oscillator_ledger as t1

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/w33_z6ii_full_spectrum_engine_v1.json'
V,W2,W3,Y,v=t1.V,t1.W2,t1.W3,t1.Y,t1.v
dot=t1.dot;shell=t1.shell;orbits=t1.orbits;label=t1.label

def key(k):
    d,h,y=k
    return f'{d}|{h}|{y}'
def parse(s):
    # only used for the frozen T1 aggregate: recover simple tuple enough for anomaly map.
    d,h,y=s.split('|');h=tuple(int(x.strip()) for x in h.strip('()').split(','))
    return int(d),h,F(y)

# U-sector certificate from the exact root projection already frozen on this branch.
U=Counter({
 (3,(0,1,0),F(-2,3)):1,(1,(0,0,0),F(1)):1,
 (6,(1,0,1),F(1,6)):1,
 (2,(0,0,1),F(1,2)):1,(2,(0,0,1),F(-1,2)):1,
 (1,(0,0,0),F(0)):2})

# Right movers from Chemtob--Hosteins Table VII conventions.
r2L=(0,0,1,0); r2R=(-1,-1,1,0)
r3L=(0,-1,2,0)
r3R=(-1,-1,1,0)

def project_t2(q,phase,qgamma,chir):
    r=r2L if chir=='L' else r2R
    rg=tuple(F(r[i])+2*v[i] for i in range(4))
    return (3*(phase+qgamma-dot(rg,v)+dot(q,V))).denominator==1 and dot(q,W2).denominator==1

def project_t3(q,phase,qgamma,chir):
    r=r3L if chir=='L' else r3R
    rg=tuple(F(r[i])+3*v[i] for i in range(4))
    return (2*(phase+qgamma-dot(rg,v)+dot(q,V))).denominator==1 and dot(q,W3).denominator==1

T2_CFG={
 F(0):[(F(0),'none')],
 F(1,3):[(F(1,6),'I1'),(F(-1,3),'bar2')],
 F(2,3):[(F(1,3),'I1^2'),(F(-1,6),'I1*bar2'),(F(1,3),'bar2^2'),
          (F(-1,6),'bar1'),(F(1,3),'I2')]}
T3_CFG={
 F(0):[(F(0),'none')],
 F(1,2):[(F(1,6),'I1'),(F(-1,6),'bar1'),(F(-1,2),'I3'),(F(1,2),'bar3')]}

def sector_t2():
    LR={'L':Counter(),'R':Counter()};ledger=[]
    for n3 in range(3):
        sh=tuple(2*V[i]+n3*W3[i] for i in range(8))
        for N,cfgs in T2_CFG.items():
            target=2*(1-F(2,9)-N)
            raw=shell(sh,target) if target>=0 else []
            for ph,name in cfgs:
                for chir in ('L','R'):
                    for gamma,qg,D in ((1,F(0),1),(-1,F(1,2),2)):
                        keep=[q for P,q in raw if project_t2(q,ph,qg,chir)]
                        if not keep:continue
                        rp=Counter(label(O) for O in orbits(keep))
                        for k,m in rp.items():LR[chir][k]+=D*m
                        ledger.append({'n3':n3,'N_L':str(N),'oscillator':name,'chirality':chir,
                          'gamma':gamma,'D':D,'surviving_weights':len(keep),
                          'reps':{key(k):m for k,m in sorted(rp.items(),key=str)}})
    return LR,ledger

def sector_t3():
    LR={'L':Counter(),'R':Counter()};ledger=[]
    for n2 in range(2):
        sh=tuple(3*V[i]+n2*W2[i] for i in range(8))
        for N,cfgs in T3_CFG.items():
            target=2*(1-F(1,4)-N)
            raw=shell(sh,target) if target>=0 else []
            for ph,name in cfgs:
                for chir in ('L','R'):
                    for gamma,qg,D in (('1',F(0),4),('w',F(1,3),2),('w2',F(2,3),2)):
                        keep=[q for P,q in raw if project_t3(q,ph,qg,chir)]
                        if not keep:continue
                        rp=Counter(label(O) for O in orbits(keep))
                        for k,m in rp.items():LR[chir][k]+=D*m
                        ledger.append({'n2':n2,'N_L':str(N),'oscillator':name,'chirality':chir,
                          'gamma':gamma,'D':D,'surviving_weights':len(keep),
                          'reps':{key(k):m for k,m in sorted(rp.items(),key=str)}})
    return LR,ledger

def index(LR):
    z=LR['L'].copy()
    for k,m in LR['R'].items():z[k]-=m
    return Counter({k:m for k,m in z.items() if m})

def anomalies(C):
    A3=A33Y=A22Y=Y3=grav=F(0);par=0
    for (dim,h,y),m in C.items():
        if not m:continue
        a,b,su2=h
        cdim=3 if (a,b) in ((1,0),(0,1)) else 1
        wdim=2 if su2==1 else 1
        A=1 if (a,b)==(1,0) else (-1 if (a,b)==(0,1) else 0)
        A3+=m*A*wdim
        if cdim==3:A33Y+=m*F(1,2)*wdim*y
        if wdim==2:
            A22Y+=m*F(1,2)*cdim*y
            par+=m*cdim
        Y3+=m*dim*y**3;grav+=m*dim*y
    return {'SU3^3':str(A3),'SU3^2Y':str(A33Y),'SU2^2Y':str(A22Y),
            'Y^3':str(Y3),'gravY':str(grav),'WittenParity':par%2}

def main(write=True):
    t1dat=json.loads((ROOT/'data/w33_z6ii_t1_full_oscillator_ledger.json').read_text())
    T1=Counter({parse(k):m for k,m in t1dat['aggregate_T1_left_chiral_representations'].items()})
    LR2,led2=sector_t2();I2=index(LR2)
    LR3,led3=sector_t3();I3=index(LR3)
    total=U+T1
    for k,m in I2.items():total[k]+=m
    for k,m in I3.items():total[k]+=m
    aa={name:anomalies(C) for name,C in [('U',U),('T1',T1),('T2_T4_index',I2),('T3_index',I3),('combined',total)]}
    assert aa['U']=={'SU3^3':'1','SU3^2Y':'-1/6','SU2^2Y':'1/4','Y^3':'5/36','gravY':'0','WittenParity':1}
    assert aa['T2_T4_index']=={'SU3^3':'1','SU3^2Y':'-1/6','SU2^2Y':'1/4','Y^3':'5/36','gravY':'0','WittenParity':1}
    nonabelian_ok=(aa['combined']['SU3^3']=='0')
    hypercharge_ok=(aa['combined']['SU3^2Y']=='0' and aa['combined']['SU2^2Y']=='0' and aa['combined']['Y^3']=='0' and aa['combined']['gravY']=='0')
    assert nonabelian_ok and not hypercharge_ok
    out={'schema':'w33.z6ii_full_spectrum_engine_v1','status':'PASS_SU3_CUBIC__HYPERCHARGE_SENTINEL_FAIL',
      'sector_coverage':{
        'U':'exact root projection','T1':'full B.3-B.5 plus oscillators and 12 fixed points',
        'T5':'CPT partner typed from T1','T2_T4':'B.8 both chiralities, gamma D=(1,2), all oscillator shells',
        'T3':'B.8 both chiralities, gamma D=(4,2,2), all oscillator shells'},
      'T2_T4_chiral_index':{key(k):m for k,m in sorted(I2.items(),key=str)},
      'T3_chiral_index':{key(k):m for k,m in sorted(I3.items(),key=str)},
      'anomaly_sentinel':aa,
      'nonabelian_SU3_cubic_closure':nonabelian_ok,
      'hypercharge_anomaly_closure':hypercharge_ok,
      'anomaly_closure':nonabelian_ok and hypercharge_ok,
      'combined_nonabelian':'SU3^3='+aa['combined']['SU3^3'],
      'diagnosis':'Published T2/T4 multiplicities and T3 vector right movers close SU3^3 exactly. Hypercharge-related visible anomalies remain nonzero, so the ledger is still quarantined and must not be called a viable MSSM spectrum.',
      'important_correction':'Published D(gamma=+1,-1)=(1,2) and Table-VII T3 vector weights restore exact SU3^3 anomaly closure. Hypercharge-related anomalies remain nonzero, so the ledger stays quarantined.',
      'next_debug_targets':['reproduce a published Z6-II benchmark model state-by-state with this engine','audit the full U(1)^5 charge basis and hypercharge generator on every state','check Green-Schwarz anomaly universality and hidden-E8 contributions before deciding whether the witness itself fails'],
      'raw_ledgers':{'T2_entries':led2,'T3_entries':led3}}
    if write:OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2));return out
if __name__=='__main__':main(True)
