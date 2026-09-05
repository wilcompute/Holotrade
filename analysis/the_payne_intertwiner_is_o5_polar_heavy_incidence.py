#!/usr/bin/env python3
"""The 40x45 Payne spectral intertwiner is the O(5,3) polar heavy-incidence map.

This explains rather than merely verifies the matrix B discovered earlier.
For a square point c in the 5D orthogonal module W, c^perp contains exactly 16
isotropic projective points. Under the Pluecker dictionary those are 16 W33
lines. Count their incidences with the 40 W33 points. For every square c the
multiplicity profile is

    8 points with multiplicity 4,   32 points with multiplicity 1.

Declare B[x,c]=1 exactly on the multiplicity-4 points. Then, after labeling c
by the explicit slow-target exterior-square formula, this B is OBJECTWISE the
committed Payne-cover incidence matrix: its column at slow slot s is exactly the
8 cheap axes whose 9-target Payne covers contain s.

The old Gram laws therefore become orthogonal polar-section intersection laws:

    B B^T = 8 I + J + 2 A_W33,
    B^T B = 6 I + 2 J - 2 A_square,

where A_square is perpendicularity on the 45 square points, equivalently the
slow GQ(4,2) collinearity graph. In particular B has rank 25 and its nontrivial
24-dimensional channel is not an accidental spectral match: it is carried by
this canonical polar heavy-incidence transform.
"""
from __future__ import annotations
import itertools,json,sys
from fractions import Fraction
from pathlib import Path
from w33_payne_slowpath_core import Q,D,norm,form
ROOT=Path(__file__).resolve().parents[1]
PAIR=((0,1),(0,2),(0,3),(1,2),(1,3),(2,3))

def normn(v):
    v=tuple(int(x)%Q for x in v);i=next(i for i,x in enumerate(v) if x);z=pow(v[i],-1,Q);return tuple(z*x%Q for x in v)
def wedgev(a,b):return tuple((a[i]*b[j]-a[j]*b[i])%Q for i,j in PAIR)
def omega(b):return (b[1]+b[4])%Q
def qf(b):return (b[0]*b[5]-b[1]*b[4]+b[2]*b[3])%Q
def polar(a,b):return (qf(tuple((a[i]+b[i])%Q for i in range(6)))-qf(a)-qf(b))%Q

def w33():
    P=sorted({norm(v) for v in itertools.product(range(Q),repeat=D) if any(v)});pi={p:i for i,p in enumerate(P)};L=set()
    for i,j in itertools.combinations(range(40),2):
        if form(P[i],P[j]):continue
        S=frozenset(pi[norm(tuple(a*P[i][k]+b*P[j][k] for k in range(D)))] for a,b in itertools.product(range(Q),repeat=2) if (a,b)!=(0,0))
        if len(S)==4:L.add(S)
    return P,sorted(L,key=lambda s:tuple(sorted(s)))
def line_coord(P,L):
    a,b=(P[i] for i in sorted(L)[:2]);return normn(wedgev(a,b))
def rankq(M):
    A=[[Fraction(x) for x in r] for r in M];m=len(A);n=len(A[0]);r=0
    for c in range(n):
        p=next((i for i in range(r,m) if A[i][c]),None)
        if p is None:continue
        A[r],A[p]=A[p],A[r];z=A[r][c];A[r]=[x/z for x in A[r]]
        for i in range(m):
            if i!=r and A[i][c]:
                z=A[i][c];A[i]=[A[i][j]-z*A[r][j] for j in range(n)]
        r+=1
        if r==m:break
    return r
def gram_left(B):return [[sum(B[i][s]*B[j][s] for s in range(45)) for j in range(40)] for i in range(40)]
def gram_right(B):return [[sum(B[x][i]*B[x][j] for x in range(40)) for j in range(45)] for i in range(45)]

def main():
    P,L=w33();iso_to_line={line_coord(P,l):i for i,l in enumerate(L)};assert len(iso_to_line)==40
    slow=json.loads((ROOT/'data/slow_o5_closed_form.json').read_text());coords={int(s):tuple(c) for s,c in slow['coordinatesBySlot'].items()};assert set(coords)==set(range(45))
    payne=json.loads((ROOT/'data/slow_path_is_payne_derivative.json').read_text());covers={int(a):set(v) for a,v in payne['equivariant40']['covers'].items()};by_target={s:{a for a in range(40) if s in covers[a]} for s in range(45)}
    PW=sorted({normn(v) for v in itertools.product(range(Q),repeat=6) if any(v) and omega(v)==0});iso=[v for v in PW if qf(v)==0];sq={v for v in PW if qf(v)==1};assert set(coords.values())==sq

    B=[[0]*45 for _ in range(40)];profiles={};polar_lines={};heavy={}
    for s in range(45):
        c=coords[s];ys=[y for y in iso if polar(c,y)==0];assert len(ys)==16
        lis=[iso_to_line[y] for y in ys];cnt=[0]*40
        for li in lis:
            for x in L[li]:cnt[x]+=1
        prof=tuple(sorted((n,cnt.count(n)) for n in set(cnt)));profiles[s]=prof
        H={x for x,n in enumerate(cnt) if n==4};heavy[s]=H;polar_lines[s]=lis
        for x in H:B[x][s]=1

    A40=[[0]*40 for _ in range(40)]
    for i,j in itertools.combinations(range(40),2):A40[i][j]=A40[j][i]=int(form(P[i],P[j])==0)
    A45=[[0]*45 for _ in range(45)]
    for i,j in itertools.combinations(range(45),2):A45[i][j]=A45[j][i]=int(polar(coords[i],coords[j])==0)
    G40=gram_left(B);G45=gram_right(B)
    left_ok=all(G40[i][j]==(9 if i==j else 3 if A40[i][j] else 1) for i in range(40) for j in range(40))
    right_ok=all(G45[i][j]==(8 if i==j else 0 if A45[i][j] else 2) for i in range(45) for j in range(45))
    intertwine_ok=all(sum(A40[i][x]*B[x][s] for x in range(40))+sum(B[i][t]*A45[t][s] for t in range(45))==(4 if B[i][s] else 5) for i in range(40) for s in range(45))

    checks={
      'all_45_polar_sections_have_16_isotropic_lines':all(len(v)==16 for v in polar_lines.values()),
      'all_45_multiplicity_profiles_are_8x4_plus_32x1':all(p==((1,32),(4,8)) for p in profiles.values()),
      'heavy_sets_match_committed_Payne_columns_objectwise':all(heavy[s]==by_target[s] for s in range(45)),
      'every_row_has_9_square_targets':all(sum(r)==9 for r in B),
      'every_column_has_8_W33_points':all(sum(B[x][s] for x in range(40))==8 for s in range(45)),
      'left_Gram_identity_8I_plus_J_plus_2A':left_ok,
      'right_Gram_identity_6I_plus_2J_minus_2A':right_ok,
      'intertwiner_identity_A40B_plus_BA45_equals_5J_minus_B':intertwine_ok,
      'polar_heavy_incidence_rank_25':rankq(B)==25,
    }
    out={'schema':'holotrade.payne-is-o5-polar-heavy-incidence.v1','status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,
      'construction':'For square c, take the 16 isotropic O5 points in c^perp, translate them to 16 W33 lines by Pluecker coordinates, and mark the 8 W33 points incident with four of those lines. The other 32 points have multiplicity one.',
      'identification':'After c is labeled by the closed slow-target exterior-square formula, the 8 heavy points are exactly the eight Payne covers containing that slow target. Thus this construction reproduces the existing 40x45 B objectwise.',
      'GramLaws':['B B^T = 8 I + J + 2 A_W33','B^T B = 6 I + 2 J - 2 A_square','A_W33 B + B A_square = 5 J - B'],
      'rank':25,
      'theorem':'The previously certified Payne/minimum-word spectral transform is canonically the heavy-incidence transform of polar sections of the 45 square points in the O(5,3) module. Its 1+24 rank decomposition is therefore intrinsic to the common orthogonal geometry, not an independent numerical coincidence.',
      'boundary':'Exact at q=3. The polar-section construction makes sense more generally, but the q=3 identification with the slow GQ(4,2) is exceptional and no q-general GQ statement is made.'}
    if '--write' in sys.argv:(ROOT/'data/payne_o5_polar_heavy_incidence.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,indent=2,sort_keys=True));return 0 if out['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
