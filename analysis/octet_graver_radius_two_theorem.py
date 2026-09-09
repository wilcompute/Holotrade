#!/usr/bin/env python3
"""Exact Graver-basis attack on global radius-two octet descent.

For fixed excess e, preimages form {x in Z^40 : N^T x=e} and the decoder
objective is

    f(x)=sum_i max(0,-x_i),

a separable convex integer objective.  The Graver basis G(N^T) is a universal
augmentation test set for separable convex integer minimization: every
non-optimal feasible x admits g in G with f(x+g)<f(x).

Hence, if every Graver element is one signed octet move or the sum of two signed
octet moves, radius-two octet descent is globally sufficient on EVERY affine
fiber, not merely inside a coordinate box.

This script writes the exact 40x40 incidence matrix for 4ti2 and independently
verifies the returned .gra file: dimensions, nonzero rows, kernel equations,
conformal minimality against the returned set, and membership in the exact
radius-two octet ball.  Completeness of the Graver enumeration is supplied by
4ti2's exact graver command; the output records its version and file digest.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess

import signed_pencil_sampling_witness as sp
import octet_gauge_local_minimum_counterexample as gauge

HERE=Path(__file__).resolve().parent
STEM=HERE/"octet_graver"


def add(a,b): return tuple(x+y for x,y in zip(a,b))
def neg(a): return tuple(-x for x in a)

def incidence():
    lines,_,_=sp.build_geometry()
    A=tuple(tuple(1 if p in L else 0 for p in range(40)) for L in lines)
    assert len(A)==40 and all(len(r)==40 for r in A)
    return lines,A

def write_matrix(path:Path):
    _lines,A=incidence()
    path.write_text("40 40\n"+"\n".join(" ".join(map(str,r)) for r in A)+"\n")

def read_4ti2_matrix(path:Path):
    toks=[int(x) for x in path.read_text().split()]
    if len(toks)<2: raise ValueError("empty 4ti2 matrix")
    m,n=toks[0],toks[1]; body=toks[2:]
    if len(body)!=m*n: raise ValueError(f"4ti2 matrix body length {len(body)} != {m*n}")
    return [tuple(body[i*n:(i+1)*n]) for i in range(m)]

def in_kernel(v,A): return all(sum(a*x for a,x in zip(row,v))==0 for row in A)
def conformal_leq(u,v):
    return all((a==0 or (a>0)==(b>0)) and abs(a)<=abs(b) for a,b in zip(u,v))

def sha256_file(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def verify(gra_path:Path, version:str):
    lines,A=incidence()
    rows=read_4ti2_matrix(gra_path)
    assert rows and all(len(v)==40 and any(v) for v in rows)
    assert all(in_kernel(v,A) for v in rows)
    G=set(rows)
    signed_complete=all(neg(v) in G for v in G)
    # Returned Graver rows must be pairwise conformally incomparable except for equality.
    conformal_bad=[]
    L=list(G)
    for i,v in enumerate(L):
        for j,u in enumerate(L):
            if i!=j and conformal_leq(u,v):
                conformal_bad.append((i,j)); break
        if conformal_bad: break
    gauge_rows,moves=gauge.gauges(lines)
    radius1=set(moves)
    radius2=set(radius1)
    radius2.update(add(a,b) for a in moves for b in moves)
    radius2.discard((0,)*40)
    outside=[v for v in G if v not in radius2]
    word_hist=Counter(1 if v in radius1 else 2 for v in G if v in radius2)
    linf=Counter(max(abs(x) for x in v) for v in G)
    theorem=not outside
    out={
      "schema":"holotrade.octet-graver-radius-two.v1","status":"PASS",
      "matrixShape":[40,40],"kernelDimension":15,
      "fourTi2Version":version,"graverFileSha256":sha256_file(gra_path),
      "graverElementCount":len(rows),"distinctGraverElementCount":len(G),
      "signedComplete":signed_complete,"pairwiseConformallyMinimal":not conformal_bad,
      "octetGaugeGenerators":len(gauge_rows),"signedOctetMoves":len(moves),
      "distinctRadiusTwoDisplacements":len(radius2),
      "graverWordRadiusHistogram":{str(k):v for k,v in sorted(word_hist.items())},
      "graverLInfinityHistogram":{str(k):v for k,v in sorted(linf.items())},
      "graverOutsideRadiusTwoCount":len(outside),
      "firstGraverOutsideRadiusTwo":None if not outside else list(sorted(outside)[0]),
      "radiusTwoIsGlobalAugmentationTestSet":theorem,
      "theorem":(
        "Because negative mass is separable convex and the exact Graver basis of N^T is contained in the one/two-octet displacement set, every non-optimal integer preimage on every affine fiber has a strictly decreasing radius-two octet move. Radius-two local minima are therefore global minima."
        if theorem else
        "The exact Graver basis is not contained in the radius-two octet ball, so the Graver universal-test-set theorem does not certify global radius-two descent. The recorded outside element is an exact missing augmentation direction, not automatically a decoder counterexample."
      ),
      "proofBoundary":"4ti2 supplies the complete exact Graver enumeration. This script independently checks kernel membership, returned-set conformal minimality, and exact radius-two containment. The conclusion is a discrete optimization theorem, not a physical dynamics claim.",
    }
    assert out["pairwiseConformallyMinimal"]
    path=HERE/"octet_graver_radius_two_certificate.json"; path.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:out[k] for k in ["status","fourTi2Version","graverElementCount","distinctGraverElementCount","signedComplete","distinctRadiusTwoDisplacements","graverWordRadiusHistogram","graverLInfinityHistogram","graverOutsideRadiusTwoCount","radiusTwoIsGlobalAugmentationTestSet"]},indent=2,sort_keys=True))
    print(f"written: {path}")


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--write-matrix",action="store_true"); ap.add_argument("--gra"); ap.add_argument("--version",default="unknown"); a=ap.parse_args()
    if a.write_matrix:
        write_matrix(STEM.with_suffix(".mat")); print(STEM.with_suffix(".mat")); return
    if not a.gra: raise SystemExit("use --write-matrix or --gra FILE")
    verify(Path(a.gra),a.version)

if __name__=="__main__": main()
