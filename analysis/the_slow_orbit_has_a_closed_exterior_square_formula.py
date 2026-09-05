#!/usr/bin/env python3
"""Closed formula for the 45 slow targets inside the O(5,3) square orbit.

Prior work proved by graph search that the 45 expensive/slow involutions are
isomorphic to the 45 square nonisotropic points of the 5D orthogonal module
inside Lambda^2(F_3^4). This file removes the search completely.

For a slow target g, let

    L+ = ker(g-I),        L- = ker(g+I) = L+^perp.

Both are nondegenerate 2-spaces. For a basis a,b of such a space define the
basis-independent normalized Pluecker bivector

    p_hat(L) = (a wedge b) / <a,b>.

The symplectic functional on Lambda^2 sends p_hat(L) to 1. Therefore

    c(g) = p_hat(L+) - p_hat(L-)

lies in its 5D kernel W. Replacing g by -g swaps L+ and L-, hence negates c:
the formula is intrinsically projective, exactly as a PSp target must be.

At q=3 the formula is checked against independent constructions:
  * the 45 c(g) are distinct and exhaust ALL square nonisotropic points of P(W);
  * anticommutation of target lifts is equivalent to perpendicularity for the
    polar form of the Pfaffian quadratic form on ALL 990 target pairs;
  * c(t g t^-1) = Lambda^2(t)c(g) projectively for all 80 transvection
    generators and all 45 targets = 3600 equivariance checks.

Thus the old backtracking isomorphism is replaced by an explicit functorial
formula from the executable 4x4 slow target matrix to its O(5,3) coordinate.
"""
from __future__ import annotations
import itertools,json,sys
from pathlib import Path
from w33_payne_slowpath_core import Q,D,norm,form,mm,inv,mkey,tv
ROOT=Path(__file__).resolve().parents[1]
PAIR=((0,1),(0,2),(0,3),(1,2),(1,3),(2,3))

def normn(v):
    v=tuple(int(x)%Q for x in v);i=next(i for i,x in enumerate(v) if x);z=pow(v[i],-1,Q);return tuple(z*x%Q for x in v)
def wedgev(a,b):return tuple((a[i]*b[j]-a[j]*b[i])%Q for i,j in PAIR)
def omega(b):return (b[1]+b[4])%Q
def qf(b):return (b[0]*b[5]-b[1]*b[4]+b[2]*b[3])%Q
def polar(a,b):return (qf(tuple((a[i]+b[i])%Q for i in range(6)))-qf(a)-qf(b))%Q

def kernel(A,eig):
    M=[[((A[i][j]-(eig if i==j else 0))%Q) for j in range(D)] for i in range(D)];piv=[];r=0
    for c in range(D):
        p=next((i for i in range(r,D) if M[i][c]),None)
        if p is None:continue
        M[r],M[p]=M[p],M[r];z=pow(M[r][c],-1,Q);M[r]=[(z*x)%Q for x in M[r]]
        for i in range(D):
            if i!=r and M[i][c]:
                z=M[i][c];M[i]=[(M[i][j]-z*M[r][j])%Q for j in range(D)]
        piv.append(c);r+=1
    free=[c for c in range(D) if c not in piv];B=[]
    for f in free:
        v=[0]*D;v[f]=1
        for i,c in enumerate(piv):v[c]=(-M[i][f])%Q
        B.append(tuple(v))
    return B

def phat(B):
    assert len(B)==2 and form(B[0],B[1])
    z=pow(form(B[0],B[1]),-1,Q);return tuple(z*x%Q for x in wedgev(B[0],B[1]))
def coord(A):
    bp=kernel(A,1);bm=kernel(A,Q-1);assert len(bp)==len(bm)==2
    p=phat(bp);m=phat(bm);c=tuple((p[i]-m[i])%Q for i in range(6));assert omega(c)==0
    return normn(c)

def wedge_matrix(g):
    M=[[0]*6 for _ in range(6)]
    for c,(i,j) in enumerate(PAIR):
        for r,(k,l) in enumerate(PAIR):M[r][c]=(g[k][i]*g[l][j]-g[l][i]*g[k][j])%Q
    return M
def mv6(M,v):return tuple(sum(M[i][j]*v[j] for j in range(6))%Q for i in range(6))

def main():
    rom=json.loads((ROOT/'data/the_45_slot_rom_bijection.json').read_text());rows=sorted(rom['table'],key=lambda r:r['slot'])
    mats=[tuple(tuple(int(x)%Q for x in rr) for rr in r['spMatrix']) for r in rows];coords=[coord(A) for A in mats]

    # Independent square orbit: all projective points of the omega-hyperplane.
    PW=sorted({normn(v) for v in itertools.product(range(Q),repeat=6) if any(v) and omega(v)==0})
    sq={v for v in PW if qf(v)==1};iso={v for v in PW if qf(v)==0};ns={v for v in PW if qf(v)==2}

    pair_ok=True;pair_checks=0
    for i,j in itertools.combinations(range(45),2):
        anti=mm(mats[i],mats[j])==tuple(tuple((-x)%Q for x in r) for r in mm(mats[j],mats[i]))
        perp=polar(coords[i],coords[j])==0
        pair_ok &= anti==perp;pair_checks+=1

    # Full 80-generator projective equivariance.
    vecs=[v for v in itertools.product(range(Q),repeat=D) if any(v)]
    gens=sorted({tv(tuple(v),lam) for v in vecs for lam in (1,2)});assert len(gens)==80
    bykey={mkey(A):i for i,A in enumerate(mats)};equiv=True;equiv_checks=0
    for t in gens:
        ti=inv(t);W=wedge_matrix(t)
        for A,c in zip(mats,coords):
            B=mm(mm(t,A),ti);k=mkey(B)
            if k not in bykey:equiv=False;continue
            lhs=coord(B);rhs=normn(mv6(W,c));equiv &= lhs==rhs;equiv_checks+=1

    # Direct consequences of eigenspace construction.
    eig_ok=True;swap_ok=True
    for A,c in zip(mats,coords):
        bp,bm=kernel(A,1),kernel(A,Q-1)
        eig_ok &= len(bp)==len(bm)==2 and form(bp[0],bp[1])!=0 and form(bm[0],bm[1])!=0 and all(form(x,y)==0 for x in bp for y in bm)
        neg=tuple(tuple((-x)%Q for x in r) for r in A);swap_ok &= coord(neg)==c  # norm makes c~-c identical

    checks={
      'projective_W_has_121_points':len(PW)==121,
      'orthogonal_partition_is_40_45_36':(len(iso),len(sq),len(ns))==(40,45,36),
      'all_45_slow_coordinates_distinct':len(set(coords))==45,
      'slow_coordinates_exhaust_square_orbit':set(coords)==sq,
      'all_slow_eigenspaces_are_complementary_nondegenerate':eig_ok,
      'formula_is_projective_under_g_to_minus_g':swap_ok,
      'anticommutation_equals_O5_perpendicularity_all_990_pairs':pair_ok and pair_checks==990,
      'exterior_square_equivariance_all_3600_cases':equiv and equiv_checks==3600,
    }
    out={'schema':'holotrade.slow-o5-closed-form.v1','status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,
      'formula':'c(g)=phat(ker(g-I))-phat(ker(g+I)), phat(span(a,b))=(a wedge b)/<a,b>',
      'quadraticModule':{'ambient':'W=ker(omega: Lambda^2 F3^4 -> F3)','omegaCoordinateLaw':'b_02+b_13=0','Q':'b_01 b_23 - b_02 b_13 + b_03 b_12','partition':[40,45,36]},
      'coordinatesBySlot':{str(rows[i]['slot']):list(coords[i]) for i in range(45)},
      'theorem':'The executable 45 slow targets map by an explicit basis-independent exterior-square formula onto exactly the square nonisotropic orbit of P(W). The map intertwines every transvection and turns slow-target anticommutation into O(5,3) perpendicularity. No graph-isomorphism search is required.',
      'machineReading':'A slow target matrix determines, without a lookup search, both its 8-axis K4,4/minimum-word support (from its two eigenspaces) and its unique square O(5,3) coordinate (from the difference of their normalized Pluecker bivectors).',
      'boundary':'Exact at q=3 for the committed Sp/PSp realization. The exterior-square construction itself is classical/q-general, but the identification of the cost orbit with a GQ is q=3-only and no q-general GQ claim is made.'}
    if '--write' in sys.argv:(ROOT/'data/slow_o5_closed_form.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,indent=2,sort_keys=True));return 0 if out['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
