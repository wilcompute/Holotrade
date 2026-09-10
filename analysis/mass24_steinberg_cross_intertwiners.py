#!/usr/bin/env python3
"""Materialize the 15 Steinberg channels between the two 1080 PSp(4,3) carriers.

The mass-24 depth-three permutation module has Steinberg multiplicity five and
the obstruction carrier has multiplicity three.  A character calculation gives
15 for the Steinberg-only cross Hom dimension, but a dimension count is not an
intertwiner.

This script constructs the full 61-dimensional cross orbital Hom space
Hom_G(C[mass], C[obstruction]) and lets each of the obstruction carrier's three
explicit rational primitive rank-81 Steinberg projectors act on it.  Each
projector has rank five on the cross Hom space; the three images are pairwise
orthogonal and their direct sum has rank 15.

Each reported channel is stored as a sparse rational coefficient vector in the
61 cross-orbital basis.  This is an exact compact representation of a
1080x1080 G-equivariant matrix, avoiding fifteen dense million-entry matrices.
"""
from __future__ import annotations

import json, os, sys
from pathlib import Path

import numpy as np
import sympy as sp

HERE=Path(__file__).resolve().parent
W33_ANALYSIS=os.environ.get("W33_ANALYSIS")
if W33_ANALYSIS: sys.path.insert(0,W33_ANALYSIS)

import mass24_depth3_steinberg_real_l1 as m24
import mass24_1080_gset_character_fingerprint as fp
import w33_20260901_obstruction_wedderburn_steinberg_projectors as obs
from w33_20260831_all5_frontier_audit import orbit_ids
from w33_20260831_c5_wedderburn_kernel import orbital_mult, center_equations, generic_center, mulvec

N=1080


def obstruction_primitive_projectors(acts):
    rel,reps,sizes=orbit_ids(acts,acts,N,N)
    assert len(reps)==59
    T=orbital_mult(rel,reps)
    Z=center_equations(T).nullspace(); assert len(Z)==15
    diag=int(rel[0,0]); one=sp.zeros(59,1); one[diag]=1
    z,_L,_cp,factors,_coeff=generic_center(Z,T)
    records,idempotents=obs.central_records(z,factors,T,one,diag)
    si=next(i for i,r in enumerate(records) if r['complexIrrepDegree']==81)
    E=idempotents[si]; assert N*E[diag]==243

    # The deterministic splitter already certified in W33-Theory.
    j,jt=11,25
    tr=[]
    for seed in reps:
        a,b=divmod(seed,N); tr.append(int(rel[b,a]))
    assert tr[j]==jt
    q=sp.zeros(59,1); q[j]=1
    if jt!=j: q[jt]+=1
    B=mulvec(E,q,T)
    vals=[sp.Rational(4),sp.Rational(0),sp.Rational(-4)]
    prim=[]
    for lam in vals:
        p=E; den=sp.Rational(1)
        for mu in vals:
            if mu==lam: continue
            p=mulvec(p,B-mu*E,T); den*=lam-mu
        p/=den
        assert mulvec(p,p,T)==p and N*p[diag]==81
        prim.append((lam,p))
    assert sum((p for _,p in prim),sp.zeros(59,1))==E
    for i in range(3):
        for j2 in range(3):
            if i!=j2: assert mulvec(prim[i][1],prim[j2][1],T)==sp.zeros(59,1)
    return rel,reps,sizes,E,prim


def mass_action():
    _pts,wlines,all_point,all_line=fp.same_generators()
    h_lines,_,_=m24.sp.build_geometry(); hidx={frozenset(L):i for i,L in enumerate(h_lines)}
    rep_w33=tuple(m24.REP[hidx[frozenset(L)]] for L in wlines)
    states,acts=m24.mass_orbit_actions(rep_w33,tuple(all_line[i] for i in fp.GENERATOR_INDICES))
    assert len(states)==N and len(acts)==4
    return acts


def cross_projector_matrix(obs_rel,cross_rel,p):
    """Matrix of left multiplication by obstruction projector p on cross Hom."""
    r=int(cross_rel.max())+1; assert r==61
    # Every cross orbital meets the base mass column because the mass action is transitive.
    base=cross_rel[:,0]
    reps=[]
    for s in range(r):
        hit=np.flatnonzero(base==s); assert len(hit)>0; reps.append(int(hit[0]))
    K=sp.zeros(r,r)
    for s,a in enumerate(reps):
        orel=obs_rel[a,:]
        for b in range(N):
            rr=int(base[b]); j=int(orel[b]); c=p[j]
            if c: K[s,rr]+=c
    return K,reps


def sparse_column(K,j):
    out=[]
    for i in range(K.rows):
        if K[i,j]: out.append([i,str(sp.factor(K[i,j]))])
    return out


def main():
    obs_acts,_charts,_lines=obs.build_action(); obs_acts=tuple(obs_acts); assert len(obs_acts)==4
    mass_acts=mass_action()
    obs_rel,obs_reps,obs_sizes,E,primitive=obstruction_primitive_projectors(obs_acts)
    cross_rel,cross_reps,cross_sizes=orbit_ids(obs_acts,mass_acts,N,N)
    assert len(cross_reps)==61

    Ks=[]; channels=[]
    for lam,p in primitive:
        K,_base_reps=cross_projector_matrix(obs_rel,cross_rel,p)
        assert K*K==K
        rank=K.rank(); assert rank==5
        _rref,piv=K.rref(); piv=list(piv); assert len(piv)==5
        Ks.append(K)
        for source in piv:
            channels.append({
                "obstructionPrimitiveEigenvalue":str(lam),
                "sourceCrossOrbitalIndex":int(source),
                "crossOrbitalCoefficients":sparse_column(K,source),
            })
    for i in range(3):
        for j in range(3):
            if i!=j: assert Ks[i]*Ks[j]==sp.zeros(61,61)
    stacked=sp.Matrix.hstack(*[K[:,j] for K in Ks for j in K.rref()[1]])
    assert stacked.rank()==15 and len(channels)==15

    # Independent finite-field regression of the 15 selected coefficient vectors.
    pmod=1000003
    A=np.array([[int(sp.numer(x))*pow(int(sp.denom(x)),pmod-2,pmod)%pmod for x in stacked[:,j]] for j in range(stacked.cols)],dtype=np.int64).T
    # simple modular rank
    B=A.copy()%pmod; rr=0
    for c in range(B.shape[1]):
        nz=np.flatnonzero(B[rr:,c])
        if not len(nz): continue
        q=rr+int(nz[0]); B[[rr,q]]=B[[q,rr]]
        B[rr]=(B[rr]*pow(int(B[rr,c]),pmod-2,pmod))%pmod
        rows=np.flatnonzero(B[:,c]); rows=rows[rows!=rr]
        if len(rows): B[rows]=(B[rows]-B[rows,c,None]*B[rr])%pmod
        rr+=1
        if rr==B.shape[0]: break
    assert rr==15

    out={
      "schema":"holotrade.mass24-steinberg-cross-intertwiners.v1","status":"PASS","group":"PSp(4,3)","groupOrder":25920,
      "massDegree":N,"obstructionDegree":N,"crossOrbitalHomDimension":61,
      "obstructionOrbitalRank":59,"obstructionSteinbergMultiplicity":3,"massSteinbergMultiplicity":5,
      "steinbergCrossHomDimension":15,"primitiveImageRanks":[K.rank() for K in Ks],
      "primitivePairwiseOrthogonalOnCrossHom":True,"selectedChannelRankOverQ":15,"selectedChannelRankMod1000003":rr,
      "channels":channels,
      "representation":"A channel coefficient vector c denotes the exact G-equivariant 1080x1080 matrix sum_r c_r C_r, where C_r is the indicator matrix of cross orbital r in obstruction x mass.",
      "theorem":"The 61-dimensional cross Hom space splits under the three explicit obstruction Steinberg projectors into three pairwise-orthogonal rank-five images. Their direct sum is 15-dimensional, and the fifteen sparse rational columns reported here are an explicit basis of all Steinberg-valued intertwiners from the mass-24 carrier to the obstruction carrier.",
      "boundary":"Exact finite complex/rational representation theory. The word channel denotes an intertwiner channel, not a physical communication or quantum hardware channel."
    }
    path=HERE/"mass24_steinberg_cross_intertwiners_certificate.json"; path.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:out[k] for k in ["status","crossOrbitalHomDimension","obstructionSteinbergMultiplicity","massSteinbergMultiplicity","steinbergCrossHomDimension","primitiveImageRanks","selectedChannelRankOverQ","selectedChannelRankMod1000003"]},indent=2,sort_keys=True)); print(f"written: {path}")

if __name__=="__main__": main()
