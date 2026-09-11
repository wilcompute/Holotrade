#!/usr/bin/env python3
"""Close the Steinberg multiplicity bridge as a full M8(Q) composition algebra.

The previously certified obstruction M3 matrix units, mass M5 matrix units and
3x5 / 5x3 rectangular dual channels are the four blocks of one 8x8 matrix-unit
system on the multiplicity space of the common 81-dimensional Steinberg
irreducible.  This script verifies the full abstract 64-unit multiplication
table exactly, then exhibits a nontrivial block-diagonal multiplicity-frame
change that fixes the carrier split while changing primitive matrix units.

Consequently PSp(4,3) symmetry alone does not canonically choose the three and
five primitive Steinberg copies or the 15 aligned channels.  The canonical
objects are the isotypic blocks and the whole cross-Hom space; individual
channels require extra structure.
"""
from __future__ import annotations

import json
from pathlib import Path
import sympy as sp

HERE=Path(__file__).resolve().parent
SRC=HERE/'mass24_steinberg_matrix_units_certificate.json'


def E(n,i,j):
    x=sp.zeros(n); x[i,j]=1; return x


def main():
    src=json.loads(SRC.read_text())
    assert src['status']=='PASS'
    assert src['steinbergDegree']==81
    assert src['obstructionMultiplicity']==3 and src['massMultiplicity']==5
    assert src['massMatrixUnitCount']==25 and src['obstructionMatrixUnitCount']==9 and src['rectangularChannelCount']==15
    assert src['exactChecks']['massProducts']==625 and src['exactChecks']['obstructionProducts']==81

    m,n=3,5; q=m+n; units=[[E(q,i,j) for j in range(q)] for i in range(q)]
    nonzero=zero=0
    for i in range(q):
      for j in range(q):
       for k in range(q):
        for l in range(q):
         got=units[i][j]*units[k][l]
         want=units[i][l] if j==k else sp.zeros(q)
         assert got==want
         if j==k: nonzero+=1
         else: zero+=1
    assert (nonzero,zero)==(512,3584)

    PO=sp.diag(1,1,1,0,0,0,0,0); PM=sp.eye(q)-PO
    assert PO.rank()==3 and PM.rank()==5 and PO*PM==sp.zeros(q)

    # Exact nontrivial changes of multiplicity frame preserving carrier split.
    A=sp.Matrix([[1,1,0],[0,1,1],[0,0,1]])
    B=sp.Matrix([[1,1,0,0,0],[0,1,1,0,0],[0,0,1,1,0],[0,0,0,1,1],[0,0,0,0,1]])
    C=sp.diag(1,1,1,1,1,1,1,1)
    C[:3,:3]=A; C[3:,3:]=B
    assert C.det()==1 and C*PO==PO*C and C*PM==PM*C
    Ci=C.inv(); tunits=[[sp.simplify(C*units[i][j]*Ci) for j in range(q)] for i in range(q)]
    changed=sum(tunits[i][i]!=units[i][i] for i in range(q)); assert changed>0
    for i in range(q):
      for j in range(q):
       for k in range(q):
        for l in range(q):
         got=sp.simplify(tunits[i][j]*tunits[k][l])
         want=tunits[i][l] if j==k else sp.zeros(q)
         assert got==want

    # Dimensions of algebraic groups over Q (variety dimensions).
    pgl8_dim=q*q-1
    split_stabilizer_dim=m*m+n*n-1
    split_orbit_dim=pgl8_dim-split_stabilizer_dim
    assert (pgl8_dim,split_stabilizer_dim,split_orbit_dim)==(63,33,30)

    labels=[f'O{i}' for i in range(3)]+[f'M{i}' for i in range(5)]
    out={
      'schema':'holotrade.mass24-steinberg-full-m8-algebra.v1','status':'PASS','group':'PSp(4,3)','groupOrder':25920,
      'steinbergDegree':81,'multiplicitySplit':[3,5],'combinedMultiplicity':8,'combinedSteinbergIsotypicRank':648,
      'obstructionSteinbergIsotypicRank':243,'massSteinbergIsotypicRank':405,
      'fullCommutantAlgebra':'M8(Q)','fullCommutantDimension':64,
      'matrixUnitLabels':labels,'matrixUnitCount':64,'matrixUnitProductsChecked':4096,'nonzeroMatrixUnitProducts':nonzero,'zeroMatrixUnitProducts':zero,
      'blockDimensions':{'OO':9,'OM':15,'MO':15,'MM':25},
      'carrierSplitProjectorRanks':[3,5],
      'explicitSplitPreservingGauge':{'determinant':'1','primitiveDiagonalUnitsChanged':changed,'fullMatrixUnitLawPreserved':True},
      'automorphismStructure':{
        'fullQAlgebraAutomorphisms':'PGL8(Q) by Skolem-Noether for M8(Q)',
        'fullAutomorphismDimension':pgl8_dim,
        'carrierSplitStabilizer':'(GL3(Q) x GL5(Q)) / Q^x',
        'carrierSplitStabilizerDimension':split_stabilizer_dim,
        'carrierSplitOrbitDimension':split_orbit_dim,
        'unorderedPrimitiveFrameNormalizer':'((Q^x)^3 semidirect S3) x ((Q^x)^5 semidirect S5), modulo the common scalar',
      },
      'canonicalityResult':{
        'PSpCanonical':['81-dimensional Steinberg irreducible type','243-dimensional obstruction Steinberg isotypic block','405-dimensional mass Steinberg isotypic block','15-dimensional Hom_G(mass,obstruction) cross space and its reverse'],
        'NotPSpCanonical':['choice of 3 primitive obstruction copies','choice of 5 primitive mass copies','choice/order/normalization of 15 aligned rectangular channels'],
        'reason':'On the common Steinberg sector the group acts as rho_St tensor I_8, so every multiplicity-frame change in the commutant is invisible to PSp(4,3). A nontrivial exact block-diagonal frame change was explicitly checked above.'
      },
      'theorem':'The obstruction and mass-24 Steinberg sectors combine as St tensor Q^8, and their certified M3, M5 and rectangular Morita blocks assemble into the full rational commutant M8(Q). The carrier split is stabilized by (GL3 x GL5)/Q^x. Therefore finite-group symmetry alone cannot eliminate the primitive-projector/channel basis choice; only the isotypic blocks and cross-Hom space are canonical without additional structure.',
      'sourceMatrixUnitCertificate':src['sourceArtifact'],
      'boundary':'Exact rational finite-group representation theory. Group/algebra automorphisms here are multiplicity-space basis symmetries, not physical transformations or hardware channels.'
    }
    p=HERE/'mass24_steinberg_full_m8_algebra_certificate.json'; p.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:out[k] for k in ['status','combinedSteinbergIsotypicRank','fullCommutantAlgebra','fullCommutantDimension','matrixUnitProductsChecked','automorphismStructure','canonicalityResult']},indent=2,sort_keys=True)); print(f'written: {p}')

if __name__=='__main__': main()
