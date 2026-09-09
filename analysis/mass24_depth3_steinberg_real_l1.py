#!/usr/bin/env python3
"""Exact cross-repo analysis of the unique mass-24 depth-three orbit.

Two questions are kept logically separate.

1. Is the 1,080-element PSp(4,3) orbit discovered at mass 24 actually the
   existing 1,080-point obstruction carrier used by the W33 Steinberg model?
   We reconstruct the SAME four transvections on both finite G-sets and search
   for an explicit generator-by-generator equivariant bijection.  Matching
   degree or stabilizer order alone is not accepted.
2. What is the exact real l1 optimum of the depth-three representative?  The
   Holotrade rational primal/dual LP certificate gives gamma_R.  For mass 24,
   k=6 and delta_R=(gamma_R-6)/2, while A=gamma_R/6 and A^2 is the signed
   sampling second-moment factor.

The output is finite algebra / exact representation economics.  A, A^2 and
negativity are not physical energy, magic, or a hardware performance claim.
"""
from __future__ import annotations

from collections import deque
from fractions import Fraction as F
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
W33_ANALYSIS = os.environ.get("W33_ANALYSIS")
if W33_ANALYSIS:
    sys.path.insert(0, W33_ANALYSIS)

import signed_pencil_sampling_witness as sp
import mass20_born_depth_and_extension_barcode as m20
import w33_20260829_216_clifford_torsor_nogo as wbase
import w33_20260901_obstruction_wedderburn_steinberg_projectors as obs

REP = (
    0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,2,
    1,2,0,0,1,1,2,2,0,1,2,2,1,2,2,0,1,1,0,0,
)
INT_PREIMAGE = (
    0,0,0,-1,0,0,0,0,0,1,0,0,0,-1,0,1,0,0,2,1,
    0,1,0,0,0,0,0,1,0,0,0,0,0,0,0,1,1,0,0,-1,
)
SOURCE = {
    "repository":"wilcompute/Holotrade",
    "workflowRun":34381463322,
    "workflowJob":102567085256,
    "artifactId":10116305671,
    "artifactZipSha256":"f4c178d85543883abf02bf81689b72748faa2bbcdabf021cb7a7cfc00fe284b5",
    "representativeDigest":"sha256:db8e5654204ace859e17291804dba3bf66c7bbd4a0a29f6bc7e6528e55c0e735",
    "orbitSize":1080,
    "integerDepth":3,
}
GENERATOR_INDICES = (18,62,77,10)


def act_vector(v, g):
    out=[0]*len(v)
    for i,x in enumerate(v): out[g[i]]=x
    return tuple(out)


def matching_line_generators():
    pts,idx,wlines,N=wbase.geometry()
    lidx={frozenset(L):i for i,L in enumerate(wlines)}
    gens40=[]
    for v in pts:
        for alpha in (1,2):
            p=[]
            for q in pts:
                z=alpha*wbase.form(q,v)%3
                y=wbase.norm(tuple((q[k]+z*v[k])%3 for k in range(4)))
                p.append(idx[y])
            gens40.append(tuple(p))
    line_gens=[]
    for gi in GENERATOR_INDICES:
        p40=gens40[gi]
        line_gens.append(tuple(lidx[frozenset(p40[q] for q in L)] for L in wlines))
    return pts,wlines,tuple(line_gens)


def mass_orbit_actions(rep_w33, line_gens):
    states=[rep_w33]; index={rep_w33:0}; q=deque([rep_w33])
    while q:
        x=q.popleft()
        for g in line_gens:
            y=act_vector(x,g)
            if y not in index:
                index[y]=len(states); states.append(y); q.append(y)
    assert len(states)==1080
    perms=[]
    for g in line_gens:
        perms.append(tuple(index[act_vector(x,g)] for x in states))
    return tuple(states),tuple(perms)


def equivariant_bijections(mass_perms, obstruction_perms):
    assert len(mass_perms)==len(obstruction_perms)==4
    n=1080; hits=[]
    for target0 in range(n):
        f=[-1]*n; inv=[-1]*n; f[0]=target0; inv[target0]=0; q=deque([0]); ok=True
        while q and ok:
            a=q.popleft(); b=f[a]
            for pm,po in zip(mass_perms,obstruction_perms):
                aa=pm[a]; bb=po[b]
                if f[aa] == -1:
                    if inv[bb] != -1:
                        ok=False; break
                    f[aa]=bb; inv[bb]=aa; q.append(aa)
                elif f[aa] != bb:
                    ok=False; break
        if ok and all(x>=0 for x in f):
            assert len(set(f))==n
            assert all(f[pm[i]]==po[f[i]] for pm,po in zip(mass_perms,obstruction_perms) for i in range(n))
            hits.append(tuple(f))
    return hits


def exact_real_l1(h_lines):
    assert sum(REP)==24
    assert sum(INT_PREIMAGE)==6
    assert sum(-x for x in INT_PREIMAGE if x<0)==3
    assert sum(abs(x) for x in INT_PREIMAGE)==12
    assert tuple(sum(INT_PREIMAGE[p] for p in L) for L in h_lines)==REP
    frac=sp.fractional_certificate(REP,h_lines)
    gamma=F(frac["l1"]); k=F(6); delta=(gamma-k)/2; A=gamma/k; A2=A*A
    return {
        "integerDepth":3,
        "integerL1":12,
        "integerPreimage":list(INT_PREIMAGE),
        "gammaReal":str(gamma),
        "deltaReal":str(delta),
        "deltaRealEqualsIntegerDepth":delta==3,
        "l1IntegralityGap":str(F(12)/gamma),
        "representationAmplification":str(A),
        "signedSamplingSecondMomentFactor":str(A2),
        "fractionalCertificate":frac,
    }


def main():
    h_lines,_,_=sp.build_geometry()
    _pts,wlines,line_gens=matching_line_generators()
    hidx={frozenset(L):i for i,L in enumerate(h_lines)}
    assert len(hidx)==40 and len(wlines)==40 and set(hidx)=={frozenset(L) for L in wlines}
    rep_w33=tuple(REP[hidx[frozenset(L)]] for L in wlines)
    states,mass_perms=mass_orbit_actions(rep_w33,line_gens)
    obstruction_perms,charts,wlines2=obs.build_action()
    assert tuple(map(frozenset,wlines2))==tuple(map(frozenset,wlines))
    maps=equivariant_bijections(mass_perms,tuple(obstruction_perms))
    first=None
    if maps:
        b=maps[0][0]
        first={
            "massBaseOrbitIndex":0,
            "obstructionBaseIndex":b,
            "completionChartIndex":b//40,
            "w33LineIndex":b%40,
            "completionChart":list(charts[b//40]),
            "w33Line":list(wlines[b%40]),
            "bijectionSha256":m20.digest(maps[0]),
        }
    real=exact_real_l1(h_lines)
    out={
        "schema":"holotrade.mass24-depth3-steinberg-real-l1.v1",
        "status":"PASS",
        "source":SOURCE,
        "groupOrder":25920,
        "massOrbitSize":len(states),
        "massStabilizerOrder":25920//len(states),
        "obstructionCarrierSize":1080,
        "obstructionStabilizerOrder":24,
        "sameFourGeneratorIndices":list(GENERATOR_INDICES),
        "equivariantBijectionCount":len(maps),
        "equivariantlyIsomorphicToObstructionCarrier":bool(maps),
        "firstEquivariantBijection":first,
        "realL1":real,
        "theorem":(
            "An explicit generator-by-generator PSp(4,3)-equivariant bijection identifies the unique mass-24 depth-three orbit with the existing 1080-point obstruction carrier."
            if maps else
            "The matching degree 1080 does not extend to an equivariant bijection for the same four PSp(4,3) generators; the orbit-size coincidence alone is not an identification."
        ),
        "boundary":"Exact finite G-set and rational l1 statements only. Signed amplification is a representation/estimator factor, not physical energy or a device metric.",
    }
    path=HERE/"mass24_depth3_steinberg_real_l1_certificate.json"
    path.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "status":"PASS",
        "equivariantlyIsomorphic":out["equivariantlyIsomorphicToObstructionCarrier"],
        "equivariantBijectionCount":out["equivariantBijectionCount"],
        "gammaReal":real["gammaReal"],
        "deltaReal":real["deltaReal"],
        "deltaEqualsDepth":real["deltaRealEqualsIntegerDepth"],
        "A":real["representationAmplification"],
        "A2":real["signedSamplingSecondMomentFactor"],
        "certificate":str(path),
    },indent=2,sort_keys=True))

if __name__=="__main__": main()
