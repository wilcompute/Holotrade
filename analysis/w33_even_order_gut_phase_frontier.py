#!/usr/bin/env python3
"""Even-order extension frontier for the W33 heterotic branch.

The existing model builder is a T^6/Z3 builder: its Wilson-line consistency,
fixed-point labels F3^3 and local sectors are order-three specific.  This file
therefore does NOT fake a Z6-II spectrum with that machinery.  It closes the
GUT charge arithmetic that any honest even-order extension must satisfy.

For both standard SU(5) and flipped SO(10)->SU(5)xU(1)_X, let t be the phase
of a broken GUT root.  The three species inside the parent family irrep have
pairwise phase gaps t,t,2t.  Hence:
  * all three survive one parent irrep iff t=0, i.e. the GUT is unbroken;
  * exactly a two-species pairing is possible with broken GUT iff 2t=0 but
    t!=0, uniquely t=1/2;
  * in a Z6 character t=k/6, only k=3 (the order-two element) has this property.
Thus an even-order element is necessary but not sufficient: it can repair the
odd-order one-species obstruction only to a two-of-three parent-irrep pairing.
A complete SM family must combine sectors/orbits or use a more general embedding.
"""
import json
from fractions import Fraction as F
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/w33_even_order_gut_phase_frontier.json'

def mod1(x): return x % 1

def survivors(t):
    # normalize first species phase to 0; the other two differ by t and 2t
    ph=[F(0),mod1(t),mod1(2*t)]
    groups={p:[i for i,q in enumerate(ph) if q==p] for p in sorted(set(ph))}
    return ph,sorted(map(len,groups.values()),reverse=True)

def main(write=True):
    rows=[]
    for N in range(2,13):
        for k in range(1,N):
            t=F(k,N); ph,parts=survivors(t)
            rows.append({'N':N,'k':k,'t':str(t),'effective_order':t.denominator,
                         'phase_partition':parts,'two_species_pair':parts==[2,1]})
    two=[r for r in rows if r['two_species_pair']]
    assert all(r['t']=='1/2' for r in two)
    z6=[r for r in rows if r['N']==6]
    assert [r['k'] for r in z6 if r['two_species_pair']]==[3]
    assert survivors(F(1,3))[1]==[1,1,1] and survivors(F(2,3))[1]==[1,1,1]
    assert survivors(F(1,2))[1]==[2,1]
    out={
      'schema':'w33.even_order_gut_phase_frontier.v1','status':'PASS_WITH_BUILDER_BOUNDARY',
      'universal_gap_pattern':{'standard_SU5_10':['t','t','2t'],'flipped_SO10_16_to_SU5':['t','t','2t']},
      'theorem':{'full_three_species_parent_irrep':'iff t=0 mod 1 (GUT unbroken)',
                 'broken_GUT_two_species_pair':'iff t=1/2 mod 1',
                 'odd_order':'never gives a two-species pair','Z6':'only k=3, the order-two subgroup element'},
      'Z3_check':{'t=1/3':survivors(F(1,3))[1],'t=2/3':survivors(F(2,3))[1]},
      'Z2_check':{'t=1/2':survivors(F(1,2))[1]},
      'Z6_characters':z6,
      'existing_builder_boundary':{
        'geometry':'T^6/Z3 with fixed points F3^3','wilson_line_conditions':'3 a_i^2 in 2Z; 3 V.a_i and 3 a_i.a_j integral','can_compute_Z6II_spectrum':False,
        'reason':'Z6-II needs a different geometric twist, fixed-set structure, local vacuum energies and modular-invariance conditions; reusing the Z3 fixed-point/spectrum routine would be invalid.'},
      'physics_consequence':'An even-order extension is necessary but cannot by itself preserve a complete SU5/SO10 family inside one parent irrep. A viable SM construction must combine sectors or use a more general hypercharge embedding.',
      'next_builder_requirement':'Implement an independent Z6-II or Z3xZ2 heterotic lattice/orbifold builder before claiming modular invariance, three-family spectra, hypercharge, exotic decoupling or flatness.',
      'boundary':'Exact charge/character arithmetic plus an explicit software-capability audit; not a Z6-II vacuum construction.'}
    if write:OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2));return out
if __name__=='__main__':main(True)
