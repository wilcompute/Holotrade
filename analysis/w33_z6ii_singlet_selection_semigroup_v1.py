#!/usr/bin/env python3
"""Exact singlet monomial semigroup / selection-rule engine v1.

The engine is intentionally model-agnostic.  A field record carries:
  * rational continuous charges (full Cartan/U(1) vector when available),
  * point-group residue mod N,
  * discrete R numerators with moduli (6,3,2 here),
  * a localization/gamma Z2 residue for the current G2 rule,
  * sector metadata.

It enumerates exponent vectors in increasing total degree, rejects them by
continuous gauge neutrality and discrete string rules, and returns the first
surviving operators.  This is the combinatorial front end required before a
Groebner/F-term ideal is built.

The seed fixture is the certified D-flat pair
  a=T2(-s), b=T4(+s), u=neutral U3.
It reproduces:
  * no gauge-invariant pair-only superpotential term (ab)^n at any searched
    degree, with an analytic all-order R3 proof;
  * cubic uab rejected by the one-nontrivial-gamma G2 rule;
  * first standard-rule survivor u(ab)^7 at degree 15.

Boundary: a full vacuum Groebner ideal requires the complete singlet ledger
and actual nonzero CFT coefficients. This engine supplies the exact monomial
candidate set and can export it once that ledger exists.
"""
from __future__ import annotations
from fractions import Fraction as F
from itertools import product
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/w33_z6ii_singlet_selection_semigroup_v1.json'

FIELDS=[
 {'name':'a_T2_minus_s','charges':(F(-1,6),F(1,6),F(1,2),F(-1,2),F(-1,2),F(-1,2),F(-1,2),F(-1,2)),
  'point':2,'R':(F(-1,3),F(-2,3),F(0)),'gamma_bit':1},
 {'name':'b_T4_plus_s','charges':(F(1,6),F(-1,6),F(-1,2),F(1,2),F(1,2),F(1,2),F(1,2),F(1,2)),
  'point':4,'R':(F(-2,3),F(-1,3),F(0)),'gamma_bit':0},
 {'name':'u_U3_neutral','charges':(F(0),)*8,'point':0,'R':(F(0),F(0),F(-1)),'gamma_bit':0},
]
R_MOD=(6,3,2)
R_TARGET=(-1,-1,-1)

def gauge_neutral(e):
    return all(sum(e[i]*FIELDS[i]['charges'][j] for i in range(len(FIELDS)))==0 for j in range(8))
def point_ok(e):
    return sum(e[i]*FIELDS[i]['point'] for i in range(len(FIELDS)))%6==0
def R_ok(e):
    vals=[sum(e[i]*FIELDS[i]['R'][j] for i in range(len(FIELDS))) for j in range(3)]
    return all(((vals[j]-R_TARGET[j])/R_MOD[j]).denominator==1 for j in range(3))
def gamma_ok(e):
    # Current G2 rule needed by this fixture: exactly one nontrivial gamma
    # insertion among T2/T4 localized fields is forbidden.
    nontrivial=sum(e[i]*FIELDS[i]['gamma_bit'] for i in range(len(FIELDS)))
    return nontrivial != 1
def enumerate_degree(max_degree):
    survivors=[];rejected={'gauge':0,'point':0,'R':0,'gamma':0}
    for d in range(1,max_degree+1):
        for a in range(d+1):
            for b in range(d-a+1):
                u=d-a-b;e=(a,b,u)
                if not gauge_neutral(e):rejected['gauge']+=1;continue
                if not point_ok(e):rejected['point']+=1;continue
                if not R_ok(e):rejected['R']+=1;continue
                if not gamma_ok(e):rejected['gamma']+=1;continue
                survivors.append({'degree':d,'exponents':dict(zip([x['name'] for x in FIELDS],e))})
    return survivors,rejected

def main(write=True):
    surv,rej=enumerate_degree(30)
    assert surv and surv[0]['degree']==15
    assert surv[0]['exponents']=={'a_T2_minus_s':7,'b_T4_plus_s':7,'u_U3_neutral':1}
    # Pair-only analytic firewall: gauge neutrality forces a=b=n; R3=0 forever.
    assert all(not R_ok((n,n,0)) for n in range(1,100))
    out={'schema':'w33.z6ii_singlet_selection_semigroup.v1','status':'PASS_ENGINE_AND_SEED_FIXTURE',
      'engine':{
        'continuous_exact_rational_charges':True,
        'point_group_modulus':6,
        'R_moduli':[6,3,2],
        'R_targets':[-1,-1,-1],
        'localization_gamma_rule':'fixture rejects exactly one nontrivial G2 gamma insertion',
        'enumeration_order':'increasing total operator degree'},
      'seed_fields':[{'name':f['name'],'charges':[str(x) for x in f['charges']],
                      'point':f['point'],'R':[str(x) for x in f['R']],'gamma_bit':f['gamma_bit']} for f in FIELDS],
      'seed_results':{
        'pair_only_all_order':'for gauge-neutral (ab)^n, R3=0 for every n, so no superpotential term',
        'uab_degree3':'rejected by G2 gamma/localization rule',
        'first_survivor':surv[0],
        'survivors_through_degree30':surv,
        'rejection_counts_through_degree30':rej},
      'groebner_boundary':'Once the full singlet ledger and nonzero superpotential coefficients are known, survivor exponent vectors define the monomial support for the F-term ideal; Groebner decomposition is intentionally not claimed before those coefficients exist.',
      'next_input':'complete witness singlet ledger with all first/second-E8 and U(1)^5 charges, sector/gamma/oscillator labels.'
    }
    if write:OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2));return out
if __name__=='__main__':main(True)
