#!/usr/bin/env python3
"""Find one exact W33 incidence circuit outside the radius-two octet ball.

The 40x40 line/point incidence matrix has rank 25.  Any 26-column subset of
rank 25 for which every 25-column deletion has rank 25 is a matroid circuit.
Its one-dimensional rational nullspace gives, after primitive integer scaling,
a primitive integer circuit and therefore a Graver element.  One such vector
outside all one/two signed-octet displacements is enough to refute radius-two
as a universal Graver test set.

This avoids full circuit or Graver enumeration entirely.
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
    # deterministic sign
    first=next(x for x in ints if x)
    if first<0: ints=[-x for x in ints]
    return ints


def add(a,b): return tuple(x+y for x,y in zip(a,b))
def sub(a,b): return tuple(x-y for x,y in zip(a,b))


def main():
    lines,A=gr.incidence(); assert A.rank()==25
    gauge_rows,moves,B,piv,PinvT,gauge_coords=gr.intrinsic_basis(lines,A)
    radius1=set(moves); radius2=set(radius1); radius2.update(add(x,y) for x in moves for y in moves); radius2.discard((0,)*40)

    rng=random.Random(20260911); tried=0; hit=None
    # Deterministic pseudorandom order followed by structured windows.
    candidates=[]
    for _ in range(600): candidates.append(tuple(sorted(rng.sample(range(40),26))))
    candidates += [tuple((s+i)%40 for i in range(26)) for s in range(40)]
    seen=set()
    for S in candidates:
        S=tuple(sorted(S));
        if S in seen: continue
        seen.add(S); tried+=1
        AS=A[:,S]
        if AS.rank()!=25: continue
        if any(A[:,S[:j]+S[j+1:]].rank()!=25 for j in range(26)): continue
        ns=AS.nullspace(); assert len(ns)==1
        coeff=primitive_integer(ns[0]); assert all(coeff)
        v=[0]*40
        for p,x in zip(S,coeff): v[p]=x
        v=tuple(v)
        assert all(sum(int(A[i,j])*v[j] for j in range(40))==0 for i in range(40))
        if v in radius2 or tuple(-x for x in v) in radius2: continue
        icoord=gr.coords_of(v,B,piv,PinvT)
        word3=any(sub(v,m) in radius2 for m in moves) or any(sub(tuple(-x for x in v),m) in radius2 for m in moves)
        hit={'support':list(S),'vector':list(v),'supportSize':26,'l1':sum(abs(x) for x in v),'linf':max(abs(x) for x in v),
             'gcd':reduce(math.gcd,(abs(x) for x in v if x),0),'intrinsicCoordinates':list(icoord),'octetWordLengthThree':word3}
        break
    assert hit is not None, f'no outside circuit found after {tried} exact support tests'

    out={
      'schema':'holotrade.octet-single-circuit-obstruction.v1','status':'PASS','incidenceRank':25,'kernelDimension':15,
      'supportSubsetsTried':tried,'distinctRadiusTwoDisplacements':len(radius2),'circuit':hit,
      'supportMinimalityProof':'The selected 26 columns have exact rank 25; every one-column deletion also has rank 25. Therefore the support is minimally dependent. The displayed gcd-1 integer null vector is the primitive circuit on that support.',
      'isGraverElement':True,'insideRadiusTwo':False,'radiusTwoIsUniversalGraverTestSet':False,
      'theorem':'A primitive W33 incidence circuit, hence a Graver element of ker_Z(N^T), lies outside the one/two signed-octet displacement set. Radius-two octet moves therefore cannot be a universal Graver augmentation test set.',
      'decoderConnection':'This is not itself a radius-two decoder trap. The direct seven-coset separation searches found no trap and repeatedly found improving radius-two moves, so the failure is specifically of the universal Graver certificate, not a demonstrated failure of the tested decoder instances.',
      'boundary':'Exact rational/integer linear algebra only; no physical dynamics claim.'
    }
    p=HERE/'octet_single_circuit_obstruction_certificate.json'; p.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,indent=2,sort_keys=True)); print(f'written: {p}')

if __name__=='__main__': main()
