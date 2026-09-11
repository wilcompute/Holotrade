#!/usr/bin/env python3
"""Construct exact M3/M5 matrix units and the 3x5 Steinberg bridge.

The two non-isomorphic degree-1080 PSp(4,3) permutation modules contain the
81-dimensional Steinberg irreducible with multiplicities 3 (obstruction) and 5
(mass-24 exceptional carrier).  The previously materialized 15-dimensional
cross Hom space should therefore be the rectangular Morita bimodule
Mat_{3x5}(Q) on this isotypic sector.

This script proves that statement constructively.  It selects five exact cross
maps into one obstruction Steinberg copy, computes their rational Gram matrix,
dualizes them, obtains five explicit primitive mass-side projectors and all 25
M5 matrix units, constructs normalized inter-copy maps among the three
obstruction copies and all 9 M3 matrix units, then aligns the 15 cross channels
as E_ai with dual reverse channels F_ia.

All matrices are stored compactly in orbital bases.  "Channel" means a finite
G-intertwiner, not a physical communication or quantum hardware channel.
"""
from __future__ import annotations

import json, os, sys
from pathlib import Path

import sympy as sp

HERE=Path(__file__).resolve().parent
W33_ANALYSIS=os.environ.get("W33_ANALYSIS")
if W33_ANALYSIS: sys.path.insert(0,W33_ANALYSIS)

import mass24_steinberg_cross_intertwiners as cross
from w33_20260831_all5_frontier_audit import orbit_ids
from w33_20260831_c5_wedderburn_kernel import orbital_mult, mulvec

N=1080


def zero(n): return sp.zeros(n,1)
def sparse(v): return [[i,str(sp.factor(v[i]))] for i in range(v.rows) if v[i]]
def lincomb(cols,coefs):
    out=sp.zeros(cols[0].rows,1)
    for c,a in zip(cols,coefs):
        if a: out += a*c
    return out


def scalar_against(v,p):
    hit=next(i for i in range(p.rows) if p[i])
    a=sp.cancel(v[hit]/p[hit]); assert v==a*p
    return a


def transpose_coeff(v,rel,reps):
    tr=[]
    for seed in reps:
        a,b=divmod(seed,N); tr.append(int(rel[b,a]))
    out=sp.zeros(v.rows,1)
    for r,s in enumerate(tr): out[s]=v[r]
    return out


def cross_reverse(c,f,obs_rel,obs_reps,cross_rel):
    """(O x M) times (M x O), reverse map encoded by same cross orbital ids."""
    out=sp.zeros(len(obs_reps),1)
    for r,seed in enumerate(obs_reps):
        a,b=divmod(seed,N); z=sp.Rational(0)
        for m in range(N):
            x=c[int(cross_rel[a,m])]; y=f[int(cross_rel[b,m])]
            if x and y: z += x*y
        out[r]=sp.factor(z)
    return out


def reverse_cross(f,c,mass_rel,mass_reps,cross_rel):
    """(M x O) times (O x M)."""
    out=sp.zeros(len(mass_reps),1)
    for r,seed in enumerate(mass_reps):
        m,n=divmod(seed,N); z=sp.Rational(0)
        for o in range(N):
            x=f[int(cross_rel[o,m])]; y=c[int(cross_rel[o,n])]
            if x and y: z += x*y
        out[r]=sp.factor(z)
    return out


def left_obs_cross(u,c,obs_rel,cross_rel,cross_reps):
    out=sp.zeros(len(cross_reps),1)
    for r,seed in enumerate(cross_reps):
        o,m=divmod(seed,N); z=sp.Rational(0)
        for b in range(N):
            x=u[int(obs_rel[o,b])]; y=c[int(cross_rel[b,m])]
            if x and y: z += x*y
        out[r]=sp.factor(z)
    return out


def reverse_right_obs(f,u,obs_rel,cross_rel,cross_reps):
    """Reverse cross F (M x O) times obstruction endomorphism U."""
    out=sp.zeros(len(cross_reps),1)
    for r,seed in enumerate(cross_reps):
        o,m=divmod(seed,N); z=sp.Rational(0)
        for b in range(N):
            x=f[int(cross_rel[b,m])]; y=u[int(obs_rel[b,o])]
            if x and y: z += x*y
        out[r]=sp.factor(z)
    return out


def main():
    obs_acts,_charts,_lines=cross.obs.build_action(); obs_acts=tuple(obs_acts)
    mass_acts=cross.mass_action()
    obs_rel,obs_reps,obs_sizes,Eobs,primitive=cross.obstruction_primitive_projectors(obs_acts)
    mass_rel,mass_reps,mass_sizes=orbit_ids(mass_acts,mass_acts,N,N)
    cross_rel,cross_reps,cross_sizes=orbit_ids(obs_acts,mass_acts,N,N)
    ro,rm,rc=len(obs_reps),len(mass_reps),len(cross_reps)
    assert ro==59 and rc==61
    Tobs=orbital_mult(obs_rel,obs_reps); Tmass=orbital_mult(mass_rel,mass_reps)
    p=[q for _lam,q in primitive]; p0=p[0]

    # Five independent maps M -> O_0 from the rank-five cross projector image.
    K0,_=cross.cross_projector_matrix(obs_rel,cross_rel,p0)
    _rref,piv=K0.rref(); piv=list(piv); assert len(piv)==5
    t=[K0[:,j] for j in piv]
    assert sp.Matrix.hstack(*t).rank()==5

    # Exact Schur Gram matrix T_i T_j^T = G_ij P_0.
    G=sp.zeros(5,5)
    for i in range(5):
        for j in range(5): G[i,j]=scalar_against(cross_reverse(t[i],t[j],obs_rel,obs_reps,cross_rel),p0)
    assert G==G.T and G.det()!=0
    Gi=G.inv()
    # S_i = sum_k (G^-1)_{k i} T_k^T, encoded as reverse-cross coefficients.
    s=[lincomb(t,[Gi[k,i] for k in range(5)]) for i in range(5)]
    for j in range(5):
        for i in range(5):
            got=cross_reverse(t[j],s[i],obs_rel,obs_reps,cross_rel)
            assert got==(p0 if j==i else zero(ro))

    # Mass M5 matrix units Q_ij=S_i T_j.
    Q=[[reverse_cross(s[i],t[j],mass_rel,mass_reps,cross_rel) for j in range(5)] for i in range(5)]
    zM=zero(rm)
    for i in range(5):
        for j in range(5):
            for k in range(5):
                for l in range(5):
                    got=mulvec(Q[i][j],Q[k][l],Tmass)
                    assert got==(Q[i][l] if j==k else zM)
    mdiag=int(mass_rel[0,0]); ranks=[]
    for i in range(5):
        assert mulvec(Q[i][i],Q[i][i],Tmass)==Q[i][i]
        ranks.append(sp.factor(N*Q[i][i][mdiag])); assert ranks[-1]==81
    Emass=sum((Q[i][i] for i in range(5)),zM)
    assert mulvec(Emass,Emass,Tmass)==Emass and N*Emass[mdiag]==405

    # Gather five channel bases for each obstruction primitive.
    channels=[]
    for pa in p:
        Ka,_=cross.cross_projector_matrix(obs_rel,cross_rel,pa); assert Ka.rank()==5
        _r,pp=Ka.rref(); pp=list(pp); assert len(pp)==5
        channels.append([Ka[:,j] for j in pp])

    # Normalized inter-copy maps J_a0, J_0a and obstruction M3 units O_ab.
    J_a0=[None]*3; J_0a=[None]*3; J_a0[0]=p0; J_0a[0]=p0
    bridge_seeds=[None]
    for a in (1,2):
        R=None; seed=None
        for r,ca in enumerate(channels[a]):
            for i,si in enumerate(s):
                cand=cross_reverse(ca,si,obs_rel,obs_reps,cross_rel)
                if cand!=zero(ro): R=cand; seed=[r,i]; break
            if R is not None: break
        assert R is not None
        assert mulvec(p[a],R,Tobs)==R and mulvec(R,p0,Tobs)==R
        Rt=transpose_coeff(R,obs_rel,obs_reps)
        h=scalar_against(mulvec(Rt,R,Tobs),p0); assert h!=0
        J_a0[a]=R; J_0a[a]=Rt/h
        assert mulvec(J_0a[a],J_a0[a],Tobs)==p0
        assert mulvec(J_a0[a],J_0a[a],Tobs)==p[a]
        bridge_seeds.append({"channelIndex":seed[0],"massDualIndex":seed[1],"normalization":str(sp.factor(h))})
    O=[[mulvec(J_a0[a],J_0a[b],Tobs) for b in range(3)] for a in range(3)]
    zO=zero(ro)
    for a in range(3):
        for b in range(3):
            for c in range(3):
                for d in range(3):
                    got=mulvec(O[a][b],O[c][d],Tobs)
                    assert got==(O[a][d] if b==c else zO)
    odiag=int(obs_rel[0,0]); assert all(N*O[a][a][odiag]==81 for a in range(3))

    # Aligned rectangular channels and their reverse duals. Core identities
    # T_i S_j=delta_ij P0 plus M3/M5 matrix-unit laws prove the full rectangular
    # relations by associativity. We additionally verify primitive support of all
    # 30 oriented bridges exactly in the orbital algebras.
    Erect=[[left_obs_cross(J_a0[a],t[i],obs_rel,cross_rel,cross_reps) for i in range(5)] for a in range(3)]
    Frect=[[reverse_right_obs(s[i],J_0a[a],obs_rel,cross_rel,cross_reps) for a in range(3)] for i in range(5)]
    for a in range(3):
        for i in range(5):
            # E_ai F_ia = O_aa and F_ia E_ai = Q_ii are diagonal rectangular checks.
            assert cross_reverse(Erect[a][i],Frect[i][a],obs_rel,obs_reps,cross_rel)==O[a][a]
            assert reverse_cross(Frect[i][a],Erect[a][i],mass_rel,mass_reps,cross_rel)==Q[i][i]

    out={
      "schema":"holotrade.mass24-steinberg-matrix-units.v1","status":"PASS","group":"PSp(4,3)","groupOrder":25920,
      "degree":N,"obstructionOrbitalRank":ro,"massOrbitalRank":rm,"crossOrbitalRank":rc,
      "steinbergDegree":81,"obstructionMultiplicity":3,"massMultiplicity":5,"rectangularDimension":15,
      "gramMatrix":[[str(sp.factor(G[i,j])) for j in range(5)] for i in range(5)],
      "gramDeterminant":str(sp.factor(G.det())),"gramInverse":[[str(sp.factor(Gi[i,j])) for j in range(5)] for i in range(5)],
      "massPrimitiveRanks":[int(x) for x in ranks],"massSteinbergIsotypicRank":405,
      "obstructionPrimitiveRanks":[81,81,81],"bridgeSeeds":bridge_seeds,
      "massMatrixUnits":[[{"i":i,"j":j,"coefficients":sparse(Q[i][j])} for j in range(5)] for i in range(5)],
      "obstructionMatrixUnits":[[{"a":a,"b":b,"coefficients":sparse(O[a][b])} for b in range(3)] for a in range(3)],
      "rectangularChannels":[{"a":a,"i":i,"forwardCoefficients":sparse(Erect[a][i]),"reverseDualCoefficients":sparse(Frect[i][a])} for a in range(3) for i in range(5)],
      "matrixUnitLaws":{
        "mass":"Q_ij Q_kl = delta_jk Q_il (all 625 products checked exactly)",
        "obstruction":"O_ab O_cd = delta_bc O_ad (all 81 products checked exactly)",
        "rectangular":"E_ai F_jb = delta_ij O_ab and F_ia E_bj = delta_ab Q_ij. These follow exactly from the checked duality T_i S_j=delta_ij P0 and the checked M3/M5 units; all 15 diagonal bridge identities were also recomputed directly from orbital sums."
      },
      "theorem":"The Steinberg isotypic endomorphism algebras of the obstruction and mass-24 carriers contain explicit matrix-unit systems M3(Q) and M5(Q). The 15 exact aligned cross intertwiners form the corresponding 3x5 rectangular Morita bimodule, constructively realizing the multiplicity-space bridge predicted by Steinberg multiplicities 3 and 5.",
      "boundary":"Exact rational finite-group representation theory. Matrix units and intertwiner channels do not assert physical channels, quantum gates, energies, or hardware implementation."
    }
    path=HERE/"mass24_steinberg_matrix_units_certificate.json";path.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:out[k] for k in ["status","obstructionOrbitalRank","massOrbitalRank","crossOrbitalRank","obstructionMultiplicity","massMultiplicity","rectangularDimension","gramDeterminant","massPrimitiveRanks","massSteinbergIsotypicRank"]},indent=2,sort_keys=True));print(f"written: {path}")

if __name__=="__main__":main()
