#!/usr/bin/env python3
"""Construct the W33 C2 x S4 cube/frame controller explicitly inside Gram-192.

The Pass5705 W33 projective controller P has order 48 and exact structure
C2 x S4.  This script reconstructs its explicit S4 complement H from the same
16-point projective action, finds the four Sylow-3 subgroups of H, and uses
conjugation on those four subgroups to obtain a faithful H -> S4 permutation
representation.

We then identify that S4 with the rotational signed-permutation subgroup of O_h
on the four body-diagonal lines of the cube.  The central C2 of P maps to -I3.
This yields an explicit isomorphism from the W33 controller to all 48 signed 3x3
permutation matrices.  Finally diag(rho(p), I5) embeds those 48 matrices as
integral isometries of the certified Steinberg split lattice I3 direct-sum G5,
and hence as an explicit order-48 subgroup of the projective Gram-192 group.
"""
from __future__ import annotations

from collections import Counter
from itertools import permutations,product
import json,math,os,sys
from pathlib import Path
import sympy as sp

HERE=Path(__file__).resolve().parent
W33_ANALYSIS=Path(os.environ['W33_ANALYSIS']).resolve()
sys.path.insert(0,str(W33_ANALYSIS))
import w33_pass5630_deck_bdg_commutant_mass_ratio_unprotected as core

GRAM_CERT=HERE/'mass24_steinberg_integral_gram_gauge_certificate.json'
G5=sp.Matrix([[8,4,0,4,-4],[4,16,-9,-1,6],[0,-9,19,3,-13],[4,-1,3,11,-5],[-4,6,-13,-5,16]])
I3=sp.eye(3); I5=sp.eye(5); H8=sp.diag(1,1,1,*[1]*5)
for i in range(5):
    for j in range(5): H8[3+i,3+j]=G5[i,j]


def pcomp(a,b): return tuple(a[b[i]] for i in range(len(a)))
def pinv(p):
    q=[0]*len(p)
    for i,j in enumerate(p): q[j]=i
    return tuple(q)
def porder(p):
    seen=[False]*len(p); ans=1
    for i in range(len(p)):
        if seen[i]: continue
        j=i;n=0
        while not seen[j]: seen[j]=True;j=p[j];n+=1
        ans=math.lcm(ans,n)
    return ans
def pclosure(gs):
    e=tuple(range(len(gs[0]))); G={e};front=[e]
    while front:
        x=front.pop()
        for g in gs:
            y=pcomp(g,x)
            if y not in G:G.add(y);front.append(y)
    return G
def subgroup3(a):
    e=tuple(range(len(a))); return frozenset((e,a,pcomp(a,a)))
def conj(h,x): return pcomp(pcomp(h,x),pinv(h))
def det3(M): return int(sp.Matrix(M).det())
def mm3(A,B): return tuple(tuple(sum(A[i][k]*B[k][j] for k in range(3)) for j in range(3)) for i in range(3))
def neg3(A): return tuple(tuple(-x for x in row) for row in A)
def matkey(A): return tuple(x for row in A for x in row)

def signed_perm_matrices(det=None):
    out=[]
    for p in permutations(range(3)):
        for s in product((-1,1),repeat=3):
            A=tuple(tuple(s[i] if j==p[i] else 0 for j in range(3)) for i in range(3))
            if det is None or det3(A)==det: out.append(A)
    return tuple(out)

def mv(A,v): return tuple(sum(A[i][j]*v[j] for j in range(3)) for i in range(3))

def line_perm(A,diags):
    out=[]
    for v in diags:
        w=mv(A,v)
        found=None
        for j,u in enumerate(diags):
            if w==u or w==tuple(-x for x in u): found=j;break
        assert found is not None
        out.append(found)
    return tuple(out)

def block8(A):
    M=sp.eye(8)
    for i in range(3):
        for j in range(3): M[i,j]=A[i][j]
    return M

def canonical_projective_8(M):
    vals=tuple(int(x) for x in list(M)); neg=tuple(-x for x in vals)
    return min(vals,neg)


def main():
    gram=json.loads(GRAM_CERT.read_text()); assert gram['status']=='PASS' and gram['combinedProjectiveAutOrderModuloGlobalSign']==192
    pairs,_Rs,_H=core.build(); proj={g[0] for g in pairs}; assert len(proj)==48
    center=[g for g in proj if all(pcomp(g,h)==pcomp(h,g) for h in proj)]; assert len(center)==2
    z=next(g for g in center if porder(g)==2)
    target=Counter({1:1,2:9,3:8,4:6}); H=None; gensH=None
    els=sorted(proj)
    for a in els:
        for b in els:
            K=pclosure([a,b])
            if len(K)==24 and z not in K and Counter(porder(x) for x in K)==target:
                H=K; gensH=(a,b); break
        if H is not None: break
    assert H is not None and gensH is not None
    assert len({pcomp(c,h) for c in center for h in H})==48

    sylow3=sorted({subgroup3(x) for x in H if porder(x)==3},key=lambda K:sorted(K))
    assert len(sylow3)==4 and all(len(K)==3 for K in sylow3)
    sidx={K:i for i,K in enumerate(sylow3)}
    action={}
    for h in H:
        perm=[]
        for K in sylow3:
            image=frozenset(conj(h,x) for x in K)
            perm.append(sidx[image])
        action[h]=tuple(perm)
    assert len(set(action.values()))==24 and set(action.values())==set(permutations(range(4)))

    diags=((1,1,1),(1,-1,-1),(-1,1,-1),(-1,-1,1))
    rotations=signed_perm_matrices(det=1); assert len(rotations)==24
    rot_by_perm={line_perm(A,diags):A for A in rotations}; assert len(rot_by_perm)==24
    rhoH={h:rot_by_perm[action[h]] for h in H}
    minusI=((-1,0,0),(0,-1,0),(0,0,-1))
    plusI=((1,0,0),(0,1,0),(0,0,1))

    rho={}; decomp={}
    for p in proj:
        if p in H: bit=0;h=p
        else:
            h=pcomp(z,p); assert h in H; bit=1
        A=rhoH[h] if bit==0 else mm3(minusI,rhoH[h])
        rho[p]=A; decomp[p]=(bit,h)
    allB3=set(signed_perm_matrices()); assert len(allB3)==48
    assert set(rho.values())==allB3 and len(rho)==48
    for a in proj:
        for b in proj:
            assert rho[pcomp(a,b)]==mm3(rho[a],rho[b])

    gram8={}
    for p,A in rho.items():
        M=block8(A); assert M.T*H8*M==H8
        gram8[p]=canonical_projective_8(M)
    assert len(set(gram8.values()))==48

    z_image=rho[z]; assert z_image==minusI
    gen_rows=[]
    for name,g in [('s4_a',gensH[0]),('s4_b',gensH[1]),('central_z',z)]:
        gen_rows.append({'name':name,'w33Permutation16':list(g),'order':porder(g),'sylow3Permutation4':list(action[g]) if g in H else None,'signedMatrix3':[list(r) for r in rho[g]],'determinant':det3(rho[g])})

    out={
      'schema':'holotrade.mass24-steinberg-gram192-explicit-w33-embedding.v1','status':'PASS',
      'w33ControllerOrder':48,'w33Structure':'C2 x S4','s4ComplementOrder':24,'sylow3SubgroupCount':4,
      's4ActionOnSylow3Faithful':True,'s4ActionImageSize':24,
      'signedPermutationImageOrder':48,'signedPermutationImageIsAllOh':True,
      'centralC2MapsToMinusI3':True,'gramSplitLattice':'I3 direct-sum G5',
      'embeddedGramProjectiveSubgroupOrder':48,'gramProjectiveAmbientOrder':192,
      'explicitGenerators':gen_rows,
      'sylow3Subgroups16PointPermutations':[[list(x) for x in sorted(K)] for K in sylow3],
      'theorem':'The Pass5705 W33 projective cube/frame controller is explicitly, not merely abstractly, identified with O_h: its S4 complement acts faithfully on its four Sylow-3 subgroups, that action maps bijectively to the 24 determinant+1 signed 3x3 cube rotations, and the central C2 maps to -I3. Block-diagonal extension by I5 embeds all 48 controller elements as integral isometries of the certified Steinberg split Gram lattice and as an order-48 subgroup of Gram-192.',
      'boundary':'Exact finite-group and integral-lattice identification only. This does not identify the group with spacetime rotations or a hardware symmetry without further physical evidence.'
    }
    p=HERE/'mass24_steinberg_gram192_explicit_w33_embedding_certificate.json'; p.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:out[k] for k in ['status','w33ControllerOrder','s4ComplementOrder','sylow3SubgroupCount','s4ActionImageSize','signedPermutationImageOrder','centralC2MapsToMinusI3','embeddedGramProjectiveSubgroupOrder']},indent=2,sort_keys=True)); print(f'written: {p}')

if __name__=='__main__': main()
