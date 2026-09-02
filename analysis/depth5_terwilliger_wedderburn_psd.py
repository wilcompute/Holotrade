#!/usr/bin/env python3
"""Exact Wedderburn/PSD closure of the W33 Terwilliger branch for depth five.

The first noncommutative depth-five attack proved that pairwise conflict packing
cannot improve the global lower bound 13 and constructed the point-based W33
Terwilliger algebra T with dim(T)=16 and dim Z(T)=5.  This script performs the
next exact algebraic step needed by any Schrijver/Lovasz-Schrijver moment lift:
it block-diagonalizes T over Q.

T is generated on the 40-point standard module by the W33 adjacency matrix A
and the three dual distance idempotents E_i* for the base point, with distance
layers 1,12,27.  We:
  * build an exact Q-basis of the full algebra;
  * build its exact centre;
  * choose a separating rational central element;
  * construct the five primitive central idempotents by Lagrange interpolation;
  * compute the rank of each idempotent on the 40-space and the dimension of
    each simple two-sided ideal eTe;
  * verify each ideal dimension is a square d_i^2 and record the simple block
    size d_i and standard-module multiplicity rank(e_i)/d_i;
  * verify sum d_i^2=16 and sum rank(e_i)=40.

Because T is a transpose-closed rational matrix *-algebra, its symmetric PSD
cone reduces to PSD constraints on the resulting d_i x d_i blocks.  The output
therefore freezes the exact block sizes for the next genuine N+/Schrijver
moment program.  This script does NOT pretend that the block decomposition by
itself is a new depth-five bound; the missing object is the valid lifted moment
map from the 5294 seed-orbit variables into these blocks.
"""
from __future__ import annotations

import itertools
import json
import math
from pathlib import Path

import sympy as sp

import depth5_induced_subgroup_cuts as old

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/depth5_terwilliger_wedderburn_psd.json'


def vec(M): return sp.Matrix(M.rows*M.cols,1,list(M))


def independent_append(basis,M):
    if not basis:return [M]
    B=sp.Matrix.hstack(*[vec(X) for X in basis]);r=B.rank()
    C=sp.Matrix.hstack(B,vec(M))
    return basis+[M] if C.rank()>r else basis


def build_algebra():
    pts,_idx,lines,_supports,_charts,_edge=old.geometry()
    A=sp.zeros(40,40)
    for L in lines:
        for a,b in itertools.combinations(L,2):A[a,b]=A[b,a]=1
    assert set(sum(A[i,j] for j in range(40)) for i in range(40))=={12}
    x=0;d0={0};d1={j for j in range(40) if A[x,j]};d2=set(range(40))-d0-d1
    assert list(map(len,(d0,d1,d2)))==[1,12,27]
    E=[]
    for S in (d0,d1,d2):
        M=sp.zeros(40,40)
        for i in S:M[i,i]=1
        E.append(M)
    gens=[A]+E
    basis=[sp.eye(40)]
    changed=True
    while changed:
        changed=False
        snap=list(basis)
        for B in snap:
            for G in gens:
                nb=independent_append(basis,B*G)
                if len(nb)>len(basis):basis=nb;changed=True
    assert len(basis)==16
    # closure and transpose closure
    Bmat=sp.Matrix.hstack(*[vec(B) for B in basis])
    for X in basis:
        sol,_=Bmat.gauss_jordan_solve(vec(X.T));assert Bmat*sol==vec(X.T)
        for G in gens:
            sol,_=Bmat.gauss_jordan_solve(vec(X*G));assert Bmat*sol==vec(X*G)
    return A,E,gens,basis,Bmat


def main():
    A,E,gens,basis,Bmat=build_algebra()
    # Centre coefficients solve [sum c_i B_i, generator]=0.
    blocks=[]
    for G in gens:
        blocks.append(sp.Matrix.hstack(*[vec(B*G-G*B) for B in basis]))
    C=blocks[0]
    for X in blocks[1:]:C=C.col_join(X)
    zns=C.nullspace();assert len(zns)==5
    Z=[]
    for z in zns:
        M=sp.zeros(40,40)
        for c,B in zip(z,basis):M+=c*B
        Z.append(M)
        assert all(M*G==G*M for G in gens)

    # Deterministically find a central element with five distinct rational
    # eigenvalues on the standard module.
    chosen=None
    for shift in range(1,30):
        M=sum(((i+shift)*Z[i] for i in range(5)),sp.zeros(40,40))
        fac=sp.factor_list(M.charpoly().as_expr())[1]
        if len(fac)==5 and all(sp.degree(f)==1 for f,_e in fac):
            vals=[]
            for f,e in fac:
                p=sp.Poly(f);vals.append((sp.factor(-p.nth(0)/p.nth(1)),int(e)))
            if len({v for v,_e in vals})==5:
                chosen=(shift,M,vals);break
    assert chosen is not None
    shift,M,vals=chosen

    records=[];idems=[]
    I=sp.eye(40)
    for lam,mult in sorted(vals,key=lambda z:sp.default_sort_key(z[0])):
        P=I;den=sp.Integer(1)
        for mu,_mm in vals:
            if mu==lam:continue
            P=P*(M-mu*I);den*=lam-mu
        P=sp.simplify(P/den)
        assert P*P==P and P.T==P
        rank=P.rank();assert rank==mult
        idems.append(P)
        # eTe ideal span.
        ideal=[]
        for B in basis:
            X=P*B*P
            ideal=independent_append(ideal,X)
        q=len(ideal);d=math.isqrt(q);assert d*d==q
        assert rank%d==0
        records.append({'centralEigenvalue':str(lam),'standardModuleRank':rank,
                        'simpleIdealDimension':q,'matrixBlockSize':d,
                        'standardModuleMultiplicity':rank//d})
    assert sum(idems,sp.zeros(40,40))==I
    assert all(idems[i]*idems[j]==sp.zeros(40,40) for i,j in itertools.combinations(range(5),2))
    assert sum(r['simpleIdealDimension'] for r in records)==16
    assert sum(r['standardModuleRank'] for r in records)==40
    sizes=sorted(r['matrixBlockSize'] for r in records)

    out={'schema':'holotrade.depth5-terwilliger-wedderburn-psd.v1','valid':True,
      'terwilliger':{'algebraDimension':16,'centerDimension':5,'distanceLayerSizes':[1,12,27],
                     'transposeClosed':True,'separatingCenterShift':shift},
      'primitiveCentralBlocks':records,
      'matrixBlockSizesSorted':sizes,
      'wedderburnReading':' direct-sum '.join('M%d(Q)'%d if d>1 else 'Q' for d in sizes),
      'PSDReduction':{
        'exact':True,
        'statement':'Any symmetric element of this transpose-closed Terwilliger algebra is PSD iff its images in all simple real matrix blocks are PSD. Thus a symmetry-reduced moment relaxation needs only the recorded matrix blocks (plus scalar inequalities for 1x1 blocks).',
        'blockSizes':sizes},
      'depth5Consequence':(
        'The earlier pairwise conflict branch does not improve the depth-five lower bound 13. This certificate supplies the exact noncommutative block architecture for a stronger N+/Schrijver lift, but it is not itself such a lift and does not change [13,22].'),
      'nextLiftContract':(
        'A valid next program must construct moment variables/linear constraints from the 5294 seed-orbit cover model and prove that its moment matrix lies in this Terwilliger *-algebra (or in a tensor/product extension of it) before imposing these PSD blocks. No bound from an unproved embedding may be promoted.'),
      'boundary':'Exact rational algebra decomposition only; no new integer covering lower bound is claimed.'}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'valid':True,'blocks':sizes,'records':records},sort_keys=True))

if __name__=='__main__':main()
