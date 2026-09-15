#!/usr/bin/env python3
"""Exact W(3,3)/Pauli geometry of Holotrade's frozen net-three Wilson-line witness.

This does NOT claim a Standard-Model hypercharge solution.  It asks the narrower,
rigorous question motivated by the E8 -> F_3^4 Pauli grading certificate:
are the three E8 Wilson-line components of the already-verified net-three witness
contained in one totally isotropic 2-space (one W33 line / Pauli Cartan)?

Answer: no.  Their quotient labels have rank 3 and symplectic Gram rank 2.  One
label is orthogonal to the other two, while those two are nonorthogonal, so the
configuration is a two-Cartan hinge, not one Cartan.  Hence membership in a
single W33 line/Pauli Cartan is not a necessary condition for the known net-three
chirality witness.  Hypercharge, k_Y, and removal of exotics remain separate open
constraints, exactly as in the parent Wilson-line certificate.
"""
from __future__ import annotations
import itertools, json
from pathlib import Path
import sympy as sp

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'data'/'w33_vacuum_wilson_line_families.json'
OUT=ROOT/'data'/'w33_pauli_geometry_of_heterotic_witness.json'

SIMPLE_ROOTS=[
 [ 1,-1,-1,-1,-1,-1,-1, 1],
 [ 2, 2, 0, 0, 0, 0, 0, 0],
 [-2, 2, 0, 0, 0, 0, 0, 0],
 [ 0,-2, 2, 0, 0, 0, 0, 0],
 [ 0, 0,-2, 2, 0, 0, 0, 0],
 [ 0, 0, 0,-2, 2, 0, 0, 0],
 [ 0, 0, 0, 0,-2, 2, 0, 0],
 [ 0, 0, 0, 0, 0,-2, 2, 0],
]

def reflection(r):
    v=sp.Matrix(r)
    return sp.eye(8)-(v*v.T)/4

def rref_mod(A,p):
    A=[[int(x)%p for x in row] for row in A]
    m,n=len(A),len(A[0]); piv=[]; r=0
    for c in range(n):
        z=next((i for i in range(r,m) if A[i][c]),None)
        if z is None: continue
        A[r],A[z]=A[z],A[r]
        q=pow(A[r][c],-1,p); A[r]=[(q*x)%p for x in A[r]]
        for i in range(m):
            if i!=r and A[i][c]:
                q=A[i][c]; A[i]=[(A[i][j]-q*A[r][j])%p for j in range(n)]
        piv.append(c); r+=1
    return A,piv

def inv_mod(A,p):
    A=[[int(A[i,j])%p for j in range(A.cols)] for i in range(A.rows)]
    n=len(A); aug=[A[i]+[int(i==j) for j in range(n)] for i in range(n)]
    for c in range(n):
        z=next(i for i in range(c,n) if aug[i][c]%p)
        aug[c],aug[z]=aug[z],aug[c]
        q=pow(aug[c][c],-1,p); aug[c]=[(q*x)%p for x in aug[c]]
        for i in range(n):
            if i!=c and aug[i][c]%p:
                q=aug[i][c]%p; aug[i]=[(aug[i][j]-q*aug[c][j])%p for j in range(2*n)]
    return sp.Matrix([row[n:] for row in aug])

def rank_mod(rows,p=3):
    if not rows: return 0
    _,piv=rref_mod(rows,p); return len(piv)

def psymp(v,w):
    x,z,u,t=v; y,s,r,k=w
    return (z*y-s*x+t*r-k*u)%3

def canon(v):
    v=tuple(x%3 for x in v)
    nv=tuple((-x)%3 for x in v)
    return min(v,nv)

def span2(a,b):
    return {tuple((i*a[k]+j*b[k])%3 for k in range(4))
            for i in range(3) for j in range(3)}

def proj_line(a,b):
    S=span2(a,b); assert len(S)==9
    return sorted({canon(v) for v in S if any(v)})

def main(write=True):
    src=json.loads(SRC.read_text())
    assert src['valid'] and src['checks']['witness_verified']
    witness=src['witness']
    assert any(abs(p['net'])==3 for p in witness['pairs'])
    W=[row[:8] for row in witness['lines']]

    B=sp.Matrix(SIMPLE_ROOTS); Binv=B.inv(); Gram=B*B.T/4
    c=sp.eye(8)
    for r in SIMPLE_ROOTS: c=c*reflection(r)
    g=c**10; G=B*g*Binv; M=sp.eye(8)-G
    Omega=G*Gram+2*(G**2)*Gram

    # Right-kernel quotient coordinates exactly as the W33 Pauli-lift certificate.
    R,piv=rref_mod(M.tolist(),3); free=[j for j in range(8) if j not in piv]
    null=[]
    for f in free:
        x=[0]*8; x[f]=1
        for i,col in enumerate(piv): x[col]=(-R[i][f])%3
        null.append(x)
    N=sp.Matrix.hstack(*[sp.Matrix(x) for x in null])
    Nlist=[[int(N[i,j])%3 for j in range(4)] for i in range(8)]
    def coeff(w):
        q=sp.Matrix([w])*Binv
        assert all(sp.Rational(x).q==1 for x in q)
        return tuple(int(x) for x in q)
    def qraw(a): return tuple(sum(a[i]*Nlist[i][j] for i in range(8))%3 for j in range(4))

    # Build quotient representative dictionary from all 3^4 raw labels by small integer rows.
    # Symplectic Gram-Schmidt only needs Omega on representatives.  A deterministic search
    # over coefficient rows in {-1,0,1}^8 supplies every quotient label.
    rep={(0,0,0,0):(0,)*8}
    for a in itertools.product((-1,0,1),repeat=8):
        q=qraw(a)
        rep.setdefault(q,a)
        if len(rep)==81: break
    assert len(rep)==81
    def omq(u,v):
        a,b=rep[u],rep[v]
        return int((sp.Matrix([a])*Omega*sp.Matrix(b))[0])%3
    V=list(itertools.product(range(3),repeat=4))
    p1=next(v for v in V if any(v)); q1=next(v for v in V if omq(p1,v)==1)
    WW=[v for v in V if omq(p1,v)==0 and omq(q1,v)==0]
    p2=next(v for v in WW if any(v)); q2=next(v for v in WW if omq(p2,v)==1)
    SB=sp.Matrix([p1,q1,p2,q2]); SBi=inv_mod(SB,3)
    def plabel(a):
        y=tuple(int(x)%3 for x in (sp.Matrix([qraw(a)])*SBi))
        return (y[1],y[0],y[3],y[2])

    coeffs=[coeff(w) for w in W]
    labels=[plabel(a) for a in coeffs]
    assert all(any(v) for v in labels)
    Gs=[[psymp(a,b) for b in labels] for a in labels]
    r=rank_mod([list(v) for v in labels],3)
    sr=rank_mod(Gs,3)
    pair_orth={(i,j):Gs[i][j]==0 for i in range(3) for j in range(i+1,3)}
    orth_pairs=[list(k) for k,v in pair_orth.items() if v]
    nonorth_pairs=[list(k) for k,v in pair_orth.items() if not v]
    assert r==3 and sr==2 and len(orth_pairs)==2 and len(nonorth_pairs)==1

    # The common orthogonal label forms one W33 line with each of the noncommuting pair.
    common=next(i for i in range(3) if all(psymp(labels[i],labels[j])==0 for j in range(3) if j!=i))
    others=[i for i in range(3) if i!=common]
    L1=proj_line(labels[common],labels[others[0]])
    L2=proj_line(labels[common],labels[others[1]])
    assert len(L1)==len(L2)==4 and set(L1)&set(L2)=={canon(labels[common])}

    single_cartan=(r<=2 and sr==0)
    checks={
      'parent_witness_is_verified':src['checks']['witness_verified'],
      'parent_witness_has_net_three_pair':any(abs(p['net'])==3 for p in witness['pairs']),
      'all_three_first_E8_wilson_components_have_nonzero_pauli_labels':all(any(v) for v in labels),
      'three_labels_have_rank_3':r==3,
      'symplectic_gram_has_rank_2':sr==2,
      'exactly_one_nonorthogonal_pair':len(nonorth_pairs)==1,
      'exactly_two_orthogonal_pairs':len(orth_pairs)==2,
      'not_contained_in_one_W33_line_or_pauli_cartan':not single_cartan,
      'configuration_is_two_cartans_sharing_one_projective_point':len(set(L1)&set(L2))==1,
    }
    assert all(checks.values())
    out={
      'schema':'holotrade.w33_pauli_geometry_of_heterotic_witness.v1',
      'status':'PASS',
      'headline':'The frozen verified net-three heterotic Wilson-line witness is not contained in one W33 isotropic line/Pauli Cartan: its three first-E8 Pauli labels have rank 3 and one noncommuting pair. Instead it is a two-Cartan hinge sharing one W33 projective point.',
      'parent_certificate':'data/w33_vacuum_wilson_line_families.json',
      'first_E8_wilson_components':W,
      'simple_root_coefficients':coeffs,
      'pauli_labels_x1z1x2z2':labels,
      'symplectic_gram_mod3':Gs,
      'label_rank_F3':r,
      'symplectic_gram_rank_F3':sr,
      'orthogonal_pairs_zero_based':orth_pairs,
      'nonorthogonal_pairs_zero_based':nonorth_pairs,
      'two_cartans':{
        'shared_label_index':common,
        'line_1_projective_points':L1,
        'line_2_projective_points':L2,
        'intersection':[canon(labels[common])],
      },
      'consequence':'A single W33 line/Pauli Cartan condition is not necessary for the already-certified net-three quark-doublet chirality witness. Therefore any future W33 selection effect for hypercharge or exotic removal must be more subtle than requiring all Wilson lines to lie in one Cartan.',
      'open_boundary':'The parent certificate does not assign U(1)_Y, determine k_Y, or prove removal of vector-like exotics. This certificate does not invent those missing constraints; it only gives the exact Pauli/W33 geometry of the frozen witness.',
      'checks':checks,
    }
    if write: OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2)); return out
if __name__=='__main__': main(True)
