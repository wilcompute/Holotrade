#!/usr/bin/env python3
"""Find one exact W33 incidence circuit outside the radius-two octet ball.

The 40x40 line/point incidence matrix has rank 25.  Choose an exact 25-column
basis and add one nonbasis column.  The unique dependence in that 26-column set
is the fundamental circuit of the added column.  After primitive integer
scaling it is a circuit and hence a Graver element.  One such circuit outside
all one/two signed-octet displacements refutes radius-two as a universal Graver
augmentation test set without enumerating all circuits or all Graver elements.
"""
from __future__ import annotations

import json, math, random
from functools import reduce
from pathlib import Path
import sympy as sp

import octet_graver_intrinsic15 as gr
import octet_gauge_local_minimum_counterexample as gauge

HERE=Path(__file__).resolve().parent


def primitive_integer(vec):
    den=1
    for x in vec: den=sp.ilcm(den,int(sp.denom(x)))
    ints=[int(x*den) for x in vec]
    g=reduce(math.gcd,(abs(x) for x in ints if x),0); assert g
    ints=[x//g for x in ints]
    first=next(x for x in ints if x)
    if first<0: ints=[-x for x in ints]
    return ints


def add(a,b): return tuple(x+y for x,y in zip(a,b))
def sub(a,b): return tuple(x-y for x,y in zip(a,b))


def fundamental_circuits(A,basis):
    basis=tuple(sorted(basis)); AB=A[:,basis]
    assert len(basis)==25 and AB.rank()==25
    # Pick 25 independent rows once so every overdetermined solve reduces to
    # an exact nonsingular 25x25 solve, then verify against all 40 rows.
    row_basis=tuple(AB.T.rref()[1]); assert len(row_basis)==25
    S=AB[list(row_basis),:]; assert S.det()!=0
    for e in range(40):
        if e in basis: continue
        b=A[:,e]
        c=S.inv()*b[list(row_basis),:]
        assert AB*c==b
        # AB*c - b = 0.  The actual circuit support is the nonzero subset.
        rel=[sp.Rational(0)]*40
        for p,x in zip(basis,c): rel[p]=x
        rel[e]=-1
        v=tuple(primitive_integer(rel))
        yield e,v


def main():
    lines,A=gr.incidence(); assert A.rank()==25
    gauge_rows,moves=gauge.gauges(lines)
    radius1=set(moves); radius2=set(radius1); radius2.update(add(x,y) for x in moves for y in moves); radius2.discard((0,)*40)

    rng=random.Random(20260911); bases=[]
    piv=tuple(A.rref()[1]); assert len(piv)==25; bases.append(piv)
    while len(bases)<80:
        B=tuple(sorted(rng.sample(range(40),25)))
        if B not in bases and A[:,B].rank()==25: bases.append(B)

    tried=0; hit=None; hit_basis=None; added=None
    for Bset in bases:
        for e,v in fundamental_circuits(A,Bset):
            tried+=1
            if v in radius2 or tuple(-x for x in v) in radius2: continue
            supp=tuple(i for i,x in enumerate(v) if x)
            AS=A[:,supp]
            assert AS.rank()==len(supp)-1
            assert all(A[:,supp[:j]+supp[j+1:]].rank()==len(supp)-1 for j in range(len(supp)))
            assert reduce(math.gcd,(abs(x) for x in v if x),0)==1
            hit=v; hit_basis=Bset; added=e; break
        if hit is not None: break
    assert hit is not None, f'no outside fundamental circuit found after {tried} exact circuits'

    # Intrinsic 15D coordinate is computed only for the winning circuit.
    _g,_m,IB,pivI,PinvT,_gc=gr.intrinsic_basis(lines,A)
    icoord=gr.coords_of(hit,IB,pivI,PinvT)
    supp=tuple(i for i,x in enumerate(hit) if x)
    word3=any(sub(hit,m) in radius2 for m in moves) or any(sub(tuple(-x for x in hit),m) in radius2 for m in moves)
    row={'basisColumns':list(hit_basis),'addedColumn':added,'support':list(supp),'vector':list(hit),'supportSize':len(supp),
         'l1':sum(abs(x) for x in hit),'linf':max(abs(x) for x in hit),'gcd':1,'intrinsicCoordinates':list(icoord),
         'octetWordLengthThree':word3}

    out={
      'schema':'holotrade.octet-single-circuit-obstruction.v2','status':'PASS','incidenceRank':25,'kernelDimension':15,
      'independentBasesPrepared':len(bases),'fundamentalCircuitsTried':tried,'distinctRadiusTwoDisplacements':len(radius2),'circuit':row,
      'supportMinimalityProof':'The displayed support has exact column rank |S|-1, and every one-column deletion has full column rank |S|-1. Together with gcd 1, the displayed integer null vector is a primitive circuit.',
      'isGraverElement':True,'insideRadiusTwo':False,'radiusTwoIsUniversalGraverTestSet':False,
      'theorem':'A primitive W33 incidence circuit, hence a Graver element of ker_Z(N^T), lies outside the one/two signed-octet displacement set. Radius-two octet moves therefore cannot be a universal Graver augmentation test set.',
      'decoderConnection':'This is not itself a radius-two decoder trap. The direct seven-coset separation searches found no trap and repeatedly found improving radius-two moves, so the failure is specifically of the universal Graver certificate, not a demonstrated failure of the tested decoder instances.',
      'boundary':'Exact rational/integer linear algebra only; no physical dynamics claim.'
    }
    p=HERE/'octet_single_circuit_obstruction_certificate.json'; p.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,indent=2,sort_keys=True)); print(f'written: {p}')

if __name__=='__main__': main()
