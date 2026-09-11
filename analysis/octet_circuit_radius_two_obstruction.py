#!/usr/bin/env python3
"""Exact circuit obstruction to radius-two universal octet augmentation.

A primitive support-minimal integer kernel vector is a circuit, hence a Graver
basis element.  Therefore a single exact circuit outside the one/two-octet
ball is enough to disprove the claim that radius-two octet displacements form a
universal Graver augmentation test set; the full Graver enumeration is not
needed for that yes/no question.

The 4ti2 circuit output is independently checked by exact SymPy ranks: the
support-restricted incidence matrix has nullity one and deleting any supported
column makes the remaining columns independent.  Primitive gcd=1 then proves a
primitive circuit.  We also determine whether the first missing circuit has
exact octet word length three.
"""
from __future__ import annotations

import argparse, json, math
from pathlib import Path
from functools import reduce

import sympy as sp

import octet_graver_intrinsic15 as gr
import octet_gauge_local_minimum_counterexample as gauge

HERE=Path(__file__).resolve().parent


def add(a,b): return tuple(x+y for x,y in zip(a,b))
def sub(a,b): return tuple(x-y for x,y in zip(a,b))
def gcd_entries(v): return reduce(math.gcd,(abs(x) for x in v if x),0)


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--cir',required=True); ap.add_argument('--version',default='unknown'); a=ap.parse_args()
    lines,A=gr.incidence(); _rp,R=gr.reduced_presentation(A)
    gauge_rows,moves,B,piv,PinvT,gauge_coords=gr.intrinsic_basis(lines,A)
    rows=gr.read_4ti2(Path(a.cir)); assert rows

    radius1=set(moves); radius2=set(radius1)
    radius2.update(add(x,y) for x in moves for y in moves); radius2.discard((0,)*40)
    outside=[v for v in rows if v not in radius2]

    certified=[]
    for v in outside:
        assert any(v) and len(v)==40
        assert all(sum(int(A[i,j])*v[j] for j in range(40))==0 for i in range(40))
        supp=[j for j,x in enumerate(v) if x]
        AS=A[:,supp]
        assert len(supp)>=2 and AS.rank()==len(supp)-1
        # Every proper support obtained by deleting one column is independent;
        # hence no nonzero kernel vector has strictly smaller support.
        for j in range(len(supp)):
            cols=supp[:j]+supp[j+1:]
            assert A[:,cols].rank()==len(cols)
        g=gcd_entries(v); assert g==1
        c=gr.coords_of(v,B,piv,PinvT)
        # Exact word length relative to signed octet moves.
        wl=3 if any(sub(v,m) in radius2 for m in moves) else None
        certified.append({
            'vector':list(v),'supportSize':len(supp),'l1':sum(abs(x) for x in v),'linf':max(abs(x) for x in v),
            'gcd':g,'intrinsicCoordinates':list(c),'octetWordLength':wl,
        })
        # One independently certified obstruction is sufficient for theorem.
        break

    first=certified[0] if certified else None
    out={
      'schema':'holotrade.octet-circuit-radius-two-obstruction.v1','status':'PASS','fourTi2Version':a.version,
      'fullIncidenceShape':[40,40],'rank':25,'kernelDimension':15,'circuitCount':len(rows),
      'distinctRadiusTwoDisplacements':len(radius2),'outsideRadiusTwoCircuitCount':len(outside),
      'firstCertifiedOutsideCircuit':first,
      'radiusTwoIsUniversalGraverTestSet':False if first else None,
      'theorem':('A primitive support-minimal integer kernel circuit lies outside the one/two-octet displacement set. Every circuit is a Graver element, so radius-two octet moves are not a universal Graver augmentation test set for ker_Z(N^T).'
                 if first else 'No outside-radius-two circuit was found in the exact 4ti2 circuit output; this alone does not settle the full Graver question.'),
      'decoderConnection':('This obstruction does not itself produce a radius-two local minimum. It explains why Graver universality cannot certify the decoder even though direct seven-coset cutting-plane searches kept finding improving radius-two moves.'
                           if first else None),
      'proofBoundary':'Exact finite integer/rational linear algebra. The result concerns augmentation directions in the W33 incidence kernel and makes no physical dynamics claim.'
    }
    p=HERE/'octet_circuit_radius_two_obstruction_certificate.json'; p.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:out[k] for k in ['status','circuitCount','outsideRadiusTwoCircuitCount','radiusTwoIsUniversalGraverTestSet','firstCertifiedOutsideCircuit']},indent=2,sort_keys=True)); print(f'written: {p}')

if __name__=='__main__': main()
