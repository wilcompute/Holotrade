#!/usr/bin/env python3
"""Worldsheet-instanton support for the frozen W33 SU(5) exotic masses.

The preceding exact certificate leaves 864 sextic and 12960 nonic operators
which pass gauge, point/space-group, R-charge and Rules 4/5.  This file goes one
step past the binary Rule-5 existence test: for the factorized A2^3 Z3 torus it
evaluates the classical instanton theta sums that distinguish coincident and
distinct fixed points.

For one A2 plane, in the conventional dimensionless Kahler variable T>0,
    K_S(T)=sum_{m,n in Z} exp[-2 pi T (m^2-mn+n^2)]
for coincident fixed points and
    K_D(T)=sum exp[-2 pi T Q(m+1/3,n+2/3)]
for a nontrivial fixed-point separation.  Every summand is positive, hence both
kernels are strictly positive for real T>0.

After the exact Rule-4 location filtering from
w33_exotic_sextic_nonic_completion.py, a surviving sextic entry with its
untwisted 5bar in plane b=1 or 2 has aggregate classical factor
    2 K_S(T0) K_D(Tb) [K_S(Tc)+2 K_D(Tc)],
where c is the remaining plane.  The plane-0 nonic rescue has
    K_S(T0) prod_{j=1,2}[K_S(Tj)+2 K_D(Tj)].
These are strictly positive for every positive real Kahler modulus, so the
allowed entries are not killed by destructive cancellation in the classical
instanton sum.

This does NOT evaluate the complete canonically normalized superpotential
coefficient: quantum correlator normalization, Kahler metrics, singlet VEVs and
possible phases of physical linear combinations still enter.  The conclusion is
therefore 'instanton-supported structural rank 9', not a measured mass spectrum.

References: Choi-Kobayashi, arXiv:0711.4894 (arbitrary-order twisted-string
correlators); Kobayashi-Parameswaran-Ramos-Sanchez-Zavala, arXiv:1107.2137
(Rules 4/5).
"""
from __future__ import annotations
import json,math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data'/'w33_exotic_worldsheet_instanton_kernel.json'


def Q(x,y): return x*x-x*y+y*y

def kernel(T,shift=(0.0,0.0),cut=8):
    a,b=shift
    return sum(math.exp(-2*math.pi*T*Q(m+a,n+b))
               for m in range(-cut,cut+1) for n in range(-cut,cut+1))

def KS(T,cut=8): return kernel(T,(0.0,0.0),cut)
def KD(T,cut=8): return kernel(T,(1/3,2/3),cut)

def sextic_factor(T,b,cut=8):
    assert b in (1,2); c=3-b
    return 2*KS(T[0],cut)*KD(T[b],cut)*(KS(T[c],cut)+2*KD(T[c],cut))
def nonic_factor(T,cut=8):
    return KS(T[0],cut)*(KS(T[1],cut)+2*KD(T[1],cut))*(KS(T[2],cut)+2*KD(T[2],cut))

def main(write=True):
    parent=json.loads((ROOT/'data'/'w33_exotic_sextic_nonic_completion.json').read_text())
    assert parent['status']=='PASS' and parent['sextic']['candidate_monomials']==864 and parent['nonic']['candidate_monomials']==12960
    T=(1.0,1.0,1.0)
    ks=KS(1.0);kd=KD(1.0)
    s1=sextic_factor(T,1);s2=sextic_factor(T,2);n=nonic_factor(T)
    # Convergence teeth: cut 6 and 8 are stable at machine precision.
    assert abs(KS(1,6)-ks)<1e-14 and abs(KD(1,6)-kd)<1e-14
    assert ks>0 and kd>0 and s1>0 and s2>0 and n>0
    out={
      'schema':'holotrade.w33_exotic_worldsheet_instanton_kernel.v1','status':'PASS',
      'headline':'The Rule-4/Rule-5-safe sextic and nonic exotic-mass entries have strictly positive classical Z3 worldsheet-instanton theta sums for every positive real factorized A2^3 Kahler modulus. Hence the combined K9,12 support is not destroyed by classical-instanton cancellation; its structural rank 9 is instanton-supported.',
      'plane_kernels':{
        'same':'K_S(T)=sum exp[-2 pi T (m^2-mn+n^2)]',
        'distinct':'K_D(T)=sum exp[-2 pi T Q(m+1/3,n+2/3)]',
        'positivity':'Each is a sum of strictly positive real terms for T>0.'},
      'aggregate_factors':{
        'sextic_plane_b':'2 K_S(T0) K_D(Tb) [K_S(Tc)+2 K_D(Tc)], {b,c}={1,2}',
        'nonic_plane0':'K_S(T0)[K_S(T1)+2K_D(T1)][K_S(T2)+2K_D(T2)]'},
      'benchmark_T_1':{'K_S':ks,'K_D':kd,'K_D_over_K_S':kd/ks,'sextic_each_plane':s1,'nonic':n},
      'parent_counts':{'sextic_candidates':864,'nonic_candidates':12960,'combined_structural_rank':9},
      'literature':['Choi-Kobayashi, arXiv:0711.4894','Kobayashi-Parameswaran-Ramos-Sanchez-Zavala, arXiv:1107.2137'],
      'boundary':'This evaluates the classical instanton lattice sums and proves positivity of the surviving geometric kernels. It does not fix Kahler metrics, singlet VEVs, complete quantum/OPE normalization, or phases from physical linear combinations. Therefore it upgrades the result to instanton-supported structural/generic rank 9, not an explicit numerical low-energy mass matrix.',
      'checks':{'parent_counts':True,'kernel_convergence':True,'same_positive':True,'distinct_positive':True,'sextic_positive':True,'nonic_positive':True}}
    if write:OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2));return out
if __name__=='__main__':main(True)
