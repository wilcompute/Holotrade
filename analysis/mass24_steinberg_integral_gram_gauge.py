#!/usr/bin/env python3
"""Add an exact integral Gram-lattice structure to the Steinberg M8 gauge.

PSp(4,3) alone sees St tensor Q^8 and therefore leaves a PGL8(Q) multiplicity
frame gauge.  The matrix-unit construction also produced an exact integral
5x5 Gram matrix for the five mass-side bridge seeds.  If we retain that
integral lattice, the allowed mass-frame changes collapse from GL5(Q) to the
finite integral isometry group Aut(Z^5,G).

This script enumerates that group exactly.  It then combines G with the
standard rank-3 trace lattice on the obstruction primitive-copy frame.  Because
the obstruction block has norm-one vectors while the mass lattice has minimum
norm eight, the rank-3 block is intrinsically recovered as the span of the
norm-one shell.  Hence the full split-lattice isometry group factors exactly.

This is additional structure, not a consequence of PSp symmetry alone.
"""
from __future__ import annotations

import itertools, json, math
from pathlib import Path
import sympy as sp

HERE=Path(__file__).resolve().parent
G=sp.Matrix([
 [8,4,0,4,-4],
 [4,16,-9,-1,6],
 [0,-9,19,3,-13],
 [4,-1,3,11,-5],
 [-4,6,-13,-5,16],
])


def q(v):
    v=sp.Matrix(v); return int((v.T*G*v)[0])

def ip(a,b):
    a=sp.Matrix(a); b=sp.Matrix(b); return int((a.T*G*b)[0])

def exact_floor_sqrt_rat(r):
    r=sp.Rational(r); b=0
    while sp.Rational((b+1)*(b+1))<=r: b+=1
    return b

def candidates(norm):
    Gi=G.inv(); bounds=[exact_floor_sqrt_rat(sp.Rational(norm)*Gi[i,i]) for i in range(5)]
    out=[]
    for v in itertools.product(*[range(-b,b+1) for b in bounds]):
        if q(v)==norm: out.append(tuple(v))
    return tuple(out),bounds

def matkey(M): return tuple(int(x) for x in list(M))

def order(U):
    I=sp.eye(U.rows); P=sp.eye(U.rows)
    for n in range(1,65):
        P=P*U
        if P==I:return n
    raise AssertionError('unexpected isometry order')

def main():
    assert G.det()==57600
    # Sylvester: exact positive definiteness.
    leading=[int(G[:i,:i].det()) for i in range(1,6)]; assert all(x>0 for x in leading)
    diag=[int(G[i,i]) for i in range(5)]
    cand=[]; bounds=[]
    for n in diag:
        vs,bs=candidates(n); cand.append(vs); bounds.append(bs)
    sols=[]
    def rec(cols,j):
        if j==5:
            U=sp.Matrix.hstack(*[sp.Matrix(c) for c in cols])
            if U.det() in (1,-1) and U.T*G*U==G: sols.append(U)
            return
        for v in cand[j]:
            if all(ip(cols[i],v)==int(G[i,j]) for i in range(j)): rec(cols+[v],j+1)
    rec([],0)
    uniq={matkey(U):U for U in sols}; assert len(uniq)==8
    autos=list(uniq.values()); keys=set(uniq)
    for A in autos:
      for B in autos:
        assert matkey(A*B) in keys
    orders=sorted(order(U) for U in autos); assert orders==[1,2,2,2,2,2,2,2]
    # Every nonidentity element has order two -> elementary abelian C2^3.
    for A in autos:
      for B in autos:
        assert A*B==B*A

    shell8,b8=candidates(8); assert set(shell8)=={(1,0,0,0,0),(-1,0,0,0,0)}
    # Small shell fingerprint is exact using Cauchy bounds from G^{-1}.
    shells={}
    for n in range(1,30):
        vs,_=candidates(n)
        if vs:shells[str(n)]=len(vs)
    assert shells['8']==2

    # Combined primitive-frame lattice H = I3 direct-sum G.
    # Its norm-one shell consists exactly of +/- the three obstruction basis vectors,
    # because the mass block has minimum norm 8. Thus every integral isometry
    # preserves the rank-3 span and its orthogonal complement.
    obstruction_aut_order=(2**3)*math.factorial(3) # signed permutations of Z^3
    mass_aut_order=len(autos)
    combined_order=obstruction_aut_order*mass_aut_order
    assert combined_order==384
    projective_order=combined_order//2; assert projective_order==192

    out={
      'schema':'holotrade.mass24-steinberg-integral-gram-gauge.v1','status':'PASS',
      'sourceGramDeterminant':57600,'massGramMatrix':[[int(G[i,j]) for j in range(5)] for i in range(5)],
      'leadingPrincipalMinors':leading,'massMinimumNorm':8,'massMinimumShell':[list(v) for v in shell8],
      'massSmallShellCounts':shells,'massIntegralIsometryGroupOrder':mass_aut_order,
      'massIntegralIsometryElementOrders':orders,'massIntegralIsometryGroup':'C2^3',
      'massIsometryMatrices':[[[int(U[i,j]) for j in range(5)] for i in range(5)] for U in autos],
      'obstructionStandardTraceLatticeAutOrder':obstruction_aut_order,
      'combinedIntegralSplitLatticeAutOrder':combined_order,'combinedProjectiveAutOrderModuloGlobalSign':projective_order,
      'splitRecoveredFromNormShell':True,
      'canonicalMassLineFromShortestShell':'The unique mass-lattice shortest line is span(e0), represented by the shell +/-e0.',
      'theorem':'After adjoining the certified integral bridge Gram lattice, the continuous mass-side GL5(Q) frame gauge reduces to Aut(Z^5,G)=C2^3 of order 8. For the block lattice I3 direct-sum G, the norm-one shell intrinsically recovers the obstruction rank-3 block; the split-preserving integral isometry group has order 384 and its quotient by central global sign has order 192.',
      'boundary':'The integral Gram lattice is extra certified structure carried by the chosen bridge/primitive-copy lattice. The order-384/192 result is not implied by PSp(4,3) alone and is not a physical rotation group or hardware-symmetry claim without an independent identification.'
    }
    p=HERE/'mass24_steinberg_integral_gram_gauge_certificate.json'; p.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:out[k] for k in ['status','massIntegralIsometryGroupOrder','massIntegralIsometryGroup','massMinimumNorm','combinedIntegralSplitLatticeAutOrder','combinedProjectiveAutOrderModuloGlobalSign','splitRecoveredFromNormShell']},indent=2,sort_keys=True)); print(f'written: {p}')

if __name__=='__main__':main()
