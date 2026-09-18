#!/usr/bin/env python3
"""Anomaly fingerprint of the current Z6-II three-family frontier.

Certified chiral content already present:
  * two complete localized SM families from the two T1 E6 27s;
  * an exact untwisted split third-family SU5 ten Q+u^c+e^c.
All complete families are anomaly free, and vectorlike 5+5bar/Higgs pairs
cancel from perturbative gauge anomalies.

Therefore the remaining anomaly is exactly the anomaly of one isolated SU5 ten.
It is cancelled term-by-term by one anti-five d^c+L.  This gives an exact
fingerprint for any proposed twisted completion and an independent check on
the orbifold projection.

Conventions: left-chiral Weyl fermions, T(fund)=1/2, SU3 cubic index
A(3)=+1, A(3bar)=-1.
"""
from fractions import Fraction as F
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/w33_z6ii_third_family_anomaly_fingerprint.json'

fields={
 'Q':   {'d3':3,'d2':2,'Y':F(1,6),'A3':1},
 'uc':  {'d3':3,'d2':1,'Y':F(-2,3),'A3':-1},
 'dc':  {'d3':3,'d2':1,'Y':F(1,3),'A3':-1},
 'L':   {'d3':1,'d2':2,'Y':F(-1,2),'A3':0},
 'ec':  {'d3':1,'d2':1,'Y':F(1),'A3':0},
 'nuc': {'d3':1,'d2':1,'Y':F(0),'A3':0},
}
def anomalies(names):
    A3=A33Y=A22Y=Y3=grav=F(0); doublets=0
    for n in names:
        f=fields[n]; d3,d2,Y=f['d3'],f['d2'],f['Y']
        A3 += f['A3']*d2
        if d3==3: A33Y += F(1,2)*d2*Y
        if d2==2:
            A22Y += F(1,2)*d3*Y
            doublets += d3
        Y3 += d3*d2*Y**3
        grav += d3*d2*Y
    return {'SU3^3':A3,'SU3^2Y':A33Y,'SU2^2Y':A22Y,'Y^3':Y3,'gravY':grav,'SU2_doublet_parity':doublets%2}
def js(d): return {k:str(v) if isinstance(v,F) else v for k,v in d.items()}
def main(write=True):
    full=anomalies(['Q','uc','dc','L','ec','nuc']); assert all(v==0 for k,v in full.items() if k!='SU2_doublet_parity') and full['SU2_doublet_parity']==0
    ten=anomalies(['Q','uc','ec'])
    af=anomalies(['dc','L'])
    for k in ('SU3^3','SU3^2Y','SU2^2Y','Y^3','gravY'): assert ten[k]+af[k]==0
    assert ten['SU2_doublet_parity']==1 and af['SU2_doublet_parity']==1
    expected={'SU3^3':F(1),'SU3^2Y':F(-1,6),'SU2^2Y':F(1,4),'Y^3':F(5,36),'gravY':F(0),'SU2_doublet_parity':1}
    assert ten==expected
    out={'schema':'w33.z6ii_third_family_anomaly_fingerprint.v1','status':'PASS',
      'certified_chiral_core':'two complete localized families + one split untwisted ten Q+u^c+e^c',
      'partial_third_ten_anomaly':js(ten),
      'required_antifive_anomaly':js(af),
      'termwise_sum_zero':True,
      'Witten_SU2':'the partial ten contributes three color copies of Q, odd mod 2; one L doublet flips the parity back to even. Vectorlike doublet pairs do not change parity.',
      'fingerprint':'Any proposed third-family completion must supply net d^c+L with anomaly vector (-1,+1/6,-1/4,-5/36,0) in these conventions, up to additional vectorlike matter.',
      'use':'independent teeth for future T1/T3/full-spectrum projection code; a candidate with the right SM labels but wrong net anomaly is rejected.',
      'boundary':'This predicts the anomaly deficit of the certified partial spectrum. It is not a full anomaly census until all twisted sectors and U(1)^5 charges are enumerated.'}
    if write:OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2));return out
if __name__=='__main__':main(True)
