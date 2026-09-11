#!/usr/bin/env python3
"""Exact intrinsic-kernel Graver attack for the W33 signed-octet decoder.

The 40x40 W33 line/point incidence matrix N^T has rank 25 and integer kernel
rank 15.  A deterministic 25-row basis of its row space has *exactly the same
integer kernel*, so 4ti2 can work on 25 equations rather than 40 without
changing any feasible lattice fiber.

Independently, the 45 signed octet differences generate ker_Z(N^T) as a
saturated lattice.  Hermite normal form of their transpose therefore yields a
15-vector integer basis B.  Every exact Graver vector is expressed in this
intrinsic coordinate system and also checked against the exact one/two-octet
move ball.

If the exact Graver basis is contained in that ball, separable-convex Graver
augmentation proves global radius-two negativity descent.  If not, the first
missing Graver vector is preserved together with its intrinsic coordinates;
that is an exact missing universal augmentation direction, not automatically a
local-minimum counterexample.
"""
from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path

from sympy import Matrix
from sympy.matrices.normalforms import hermite_normal_form

import signed_pencil_sampling_witness as sp
import octet_gauge_local_minimum_counterexample as gauge

HERE=Path(__file__).resolve().parent
STEM=HERE/"octet_graver_intrinsic15"


def add(a,b): return tuple(x+y for x,y in zip(a,b))
def neg(a): return tuple(-x for x in a)
def digest_obj(x): return "sha256:"+hashlib.sha256(json.dumps(x,separators=(",",":"),sort_keys=True).encode()).hexdigest()
def sha256_file(path): return "sha256:"+hashlib.sha256(path.read_bytes()).hexdigest()


def incidence():
    lines,_,_=sp.build_geometry()
    A=Matrix([[1 if p in L else 0 for p in range(40)] for L in lines])
    assert A.shape==(40,40) and A.rank()==25
    return lines,A


def reduced_presentation(A):
    # Pivot columns of A^T are pivot ROWS of A.
    piv=list(A.T.rref()[1]); assert len(piv)==25
    R=Matrix([list(A[i,:]) for i in piv])
    assert R.shape==(25,40) and R.rank()==25
    # Same rational row space => same equations over Z because both are
    # homogeneous: x is killed by R iff killed by A.
    assert A.rowspace()==R.rowspace()
    return piv,R


def intrinsic_basis(lines,A):
    gauge_rows,moves=gauge.gauges(lines)
    D=Matrix(gauge_rows); assert D.shape==(45,40) and D.rank()==15
    assert (A*D.T).is_zero_matrix
    H=hermite_normal_form(D.T)
    cols=[H[:,j] for j in range(H.cols) if any(H[:,j])]
    B=Matrix.hstack(*cols).T
    assert B.shape==(15,40),B.shape
    assert B.rank()==15 and (A*B.T).is_zero_matrix
    # Every octet generator must have integral coordinates in B.  This also
    # checks that the HNF basis spans the saturated octet row lattice we use.
    piv=list(B.rref()[1]); assert len(piv)==15
    P=B[:,piv]; PinvT=P.T.inv()
    coords=[]
    for row in gauge_rows:
        c=PinvT*Matrix([row[i] for i in piv])
        assert all(z.q==1 for z in c)
        assert tuple(int(z) for z in (c.T*B))==tuple(row)
        coords.append(tuple(int(z) for z in c))
    return tuple(tuple(map(int,row)) for row in gauge_rows),tuple(moves),B,piv,PinvT,coords


def write_4ti2(path,R):
    path.write_text(f"{R.rows} {R.cols}\n"+"\n".join(" ".join(str(int(R[i,j])) for j in range(R.cols)) for i in range(R.rows))+"\n")


def read_4ti2(path):
    toks=[int(x) for x in path.read_text().split()]; assert len(toks)>=2
    m,n=toks[:2];body=toks[2:]; assert len(body)==m*n
    return [tuple(body[i*n:(i+1)*n]) for i in range(m)]


def coords_of(v,B,piv,PinvT):
    c=PinvT*Matrix([v[i] for i in piv]); assert all(z.q==1 for z in c)
    ci=tuple(int(z) for z in c); assert tuple(int(z) for z in (c.T*B))==tuple(v)
    return ci


def conformal_leq(u,v):
    return all((a==0 or (a>0)==(b>0)) and abs(a)<=abs(b) for a,b in zip(u,v))


def verify(gra_path,version):
    lines,A=incidence(); row_piv,R=reduced_presentation(A)
    gauge_rows,moves,B,bpiv,PinvT,gauge_coords=intrinsic_basis(lines,A)
    rows=read_4ti2(gra_path); assert rows and all(len(v)==40 and any(v) for v in rows)
    G=set(rows); assert len(G)==len(rows)
    assert all(all(sum(int(R[i,j])*v[j] for j in range(40))==0 for i in range(25)) for v in G)
    assert all(all(sum(int(A[i,j])*v[j] for j in range(40))==0 for i in range(40)) for v in G)
    signed_complete=all(neg(v) in G for v in G)
    L=list(G); conformal_bad=None
    for i,v in enumerate(L):
        for j,u in enumerate(L):
            if i!=j and conformal_leq(u,v): conformal_bad=(i,j);break
        if conformal_bad:break
    assert conformal_bad is None

    radius1=set(moves); radius2=set(radius1)
    radius2.update(add(a,b) for a in moves for b in moves); radius2.discard((0,)*40)
    outside=sorted(v for v in G if v not in radius2)
    word_hist=Counter(1 if v in radius1 else 2 for v in G if v in radius2)
    icoords={v:coords_of(v,B,bpiv,PinvT) for v in G}
    intrinsic_l1=Counter(sum(abs(z) for z in c) for c in icoords.values())
    intrinsic_linf=Counter(max(abs(z) for z in c) for c in icoords.values())
    physical_linf=Counter(max(abs(z) for z in v) for v in G)

    basis_rows=[list(map(int,B.row(i))) for i in range(B.rows)]
    out={
      "schema":"holotrade.octet-graver-intrinsic15.v1","status":"PASS",
      "fullIncidenceShape":[40,40],"fullRank":25,"kernelDimension":15,
      "reducedPresentationShape":[25,40],"independentIncidenceRowIndices":row_piv,
      "sameIntegerKernel":True,"reducedMatrixDigest":digest_obj([[int(R[i,j]) for j in range(40)] for i in range(25)]),
      "intrinsicBasisShape":[15,40],"intrinsicBasisDigest":digest_obj(basis_rows),"intrinsicBasisRows":basis_rows,
      "octetGaugeGeneratorCount":len(gauge_rows),"signedOctetMoveCount":len(moves),"gaugeIntrinsicCoordinateDigest":digest_obj([list(c) for c in gauge_coords]),
      "fourTi2Version":version,"graverFileSha256":sha256_file(gra_path),"graverElementCount":len(rows),"signedComplete":signed_complete,
      "distinctRadiusTwoDisplacements":len(radius2),"graverWordRadiusHistogram":{str(k):v for k,v in sorted(word_hist.items())},
      "graverOutsideRadiusTwoCount":len(outside),
      "firstGraverOutsideRadiusTwo":None if not outside else list(outside[0]),
      "firstOutsideIntrinsicCoordinates":None if not outside else list(icoords[outside[0]]),
      "intrinsicL1Histogram":{str(k):v for k,v in sorted(intrinsic_l1.items())},
      "intrinsicLInfinityHistogram":{str(k):v for k,v in sorted(intrinsic_linf.items())},
      "physicalLInfinityHistogram":{str(k):v for k,v in sorted(physical_linf.items())},
      "radiusTwoIsGlobalAugmentationTestSet":not outside,
      "theorem":("The exact Graver basis of ker_Z(N^T) is contained in the one/two-octet displacement set. Since negative mass is separable convex, every nonoptimal integer preimage on every affine fiber has a strictly decreasing radius-two octet move; radius-two local minima are global minima."
        if not outside else "The exact Graver basis contains directions outside the radius-two octet ball. Hence Graver universal augmentation does not certify radius-two descent; the recorded missing vector is an exact universal-test-set obstruction, not by itself a decoder trap."),
      "proofBoundary":"The 25x40 reduction has exactly the same homogeneous integer kernel as the full incidence matrix. The 15x40 HNF basis is derived from the saturated octet-difference lattice. 4ti2 supplies complete exact Graver enumeration. No physical dynamics claim is made.",
    }
    p=HERE/"octet_graver_intrinsic15_certificate.json";p.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:out[k] for k in ("status","reducedPresentationShape","kernelDimension","graverElementCount","signedComplete","graverWordRadiusHistogram","graverOutsideRadiusTwoCount","radiusTwoIsGlobalAugmentationTestSet")},indent=2,sort_keys=True));print(f"written: {p}")


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--write-matrix",action="store_true");ap.add_argument("--gra");ap.add_argument("--version",default="unknown");a=ap.parse_args()
    lines,A=incidence();_rp,R=reduced_presentation(A);_g,_m,B,_bp,_pinv,_gc=intrinsic_basis(lines,A)
    if a.write_matrix:
        write_4ti2(STEM.with_suffix(".mat"),R)
        meta={"reducedShape":[25,40],"kernelDimension":15,"basisDigest":digest_obj([[int(B[i,j]) for j in range(40)] for i in range(15)])}
        (HERE/"octet_graver_intrinsic15_presentation.json").write_text(json.dumps(meta,indent=2,sort_keys=True)+"\n")
        print(STEM.with_suffix(".mat"));return
    if not a.gra:raise SystemExit("use --write-matrix or --gra FILE")
    verify(Path(a.gra),a.version)

if __name__=="__main__":main()
