#!/usr/bin/env python3
"""O(5,3) polar incidence gives the exact 24+15 harmonic split of W33.

Let N be the 40 point x 40 line incidence matrix of W(3,3). Identify the 40
W33 lines with the isotropic points of the orthogonal 5-space W inside
Lambda^2(F_3^4). Define

    D[y,c] = 1  iff isotropic y is perpendicular to square c,      40 x 45
    C[y,z] = 1  iff isotropic y is perpendicular to nonsquare z.  40 x 36

Then exact finite computation gives

    N N^T = 4I + A_points,      N^T N = 4I + A_lines,
    D D^T = 12I + 6J + 3A_lines,
    C C^T =  6I + 3J - 3A_lines,
    D D^T + C C^T = 18I + 9J.

Center the orbit columns:

    D0 = D - (2/5)J   [column size 16/40],
    C0 = C - (1/4)J   [column size 10/40].

Then

    D0 D0^T = 18 P_24,      rank D0 = 24,
    C0 C0^T = 18 P_15,      rank C0 = 15,
    P_24 P_15 = 0,          P_24 + P_15 = I - J/40.

Thus the square and nonsquare orthogonal orbits are tight-frame realizations of
the two nontrivial W33 line-permutation modules.

Now let B be the 40 W33-point x 45 slow-target Payne/minimum-word incidence.
The square polar section through c contains 16 W33 lines. A W33 point lies on
four of them exactly when B[x,c]=1, otherwise on one. Therefore, objectwise,

    N D = J + 3B.

After centering B0=B-(1/5)J,

    N D0 = 3 B0.

By contrast every nonsquare polar section is a spread, so every W33 point lies
on exactly one of its ten lines:

    N C = J,      N C0 = 0.

This explains the recurring 24/15 split: point-line incidence annihilates the
15-dimensional spread/nonsquare sector and transmits exactly the 24-dimensional
square sector into the fast/slow Payne channel. The earlier rank-25 B is the
trivial dimension plus this transmitted 24-space.
"""
from __future__ import annotations
import itertools,json,sys
from fractions import Fraction as F
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
def mm(A,B):return [[sum(A[i][k]*B[k][j] for k in range(len(B))) for j in range(len(B[0]))] for i in range(len(A))]
def tr(A):return list(map(list,zip(*A)))
def add(A,B):return [[A[i][j]+B[i][j] for j in range(len(A[0]))] for i in range(len(A))]
def equal(A,B):return A==B
def rank(A):
    M=[[F(x) for x in r] for r in A];m=len(M);n=len(M[0]);r=0
    for c in range(n):
        p=next((i for i in range(r,m) if M[i][c]),None)
        if p is None:continue
        M[r],M[p]=M[p],M[r];z=M[r][c];M[r]=[x/z for x in M[r]]
        for i in range(m):
            if i!=r and M[i][c]:
                z=M[i][c];M[i]=[M[i][j]-z*M[r][j] for j in range(n)]
        r+=1
    return r
def centered(M,mean):return [[F(x)-mean for x in r] for r in M]
def fmm(A,B):return [[sum(A[i][k]*B[k][j] for k in range(len(B))) for j in range(len(B[0]))] for i in range(len(A))]

def main():
    P,L=w33();N=[[int(x in L[l]) for l in range(40)] for x in range(40)]
    Apoint=[[int(i!=j and form(P[i],P[j])==0) for j in range(40)] for i in range(40)]
    Aline=[[int(i!=j and bool(set(L[i])&set(L[j]))) for j in range(40)] for i in range(40)]
    PW=sorted({normn(v) for v in itertools.product(range(Q),repeat=6) if any(v) and omega(v)==0});iso=[v for v in PW if qf(v)==0];sq=[v for v in PW if qf(v)==1];ns=[v for v in PW if qf(v)==2]
    coord_to_line={line_coord(P,l):i for i,l in enumerate(L)};assert set(coord_to_line)==set(iso)
    iso_by_line=[None]*40
    for y,l in coord_to_line.items():iso_by_line[l]=y
    Dsq=[[int(polar(iso_by_line[l],c)==0) for c in sq] for l in range(40)]
    Cns=[[int(polar(iso_by_line[l],z)==0) for z in ns] for l in range(40)]

    payne=json.loads((ROOT/'data/slow_path_is_payne_derivative.json').read_text());slow=json.loads((ROOT/'data/slow_o5_closed_form.json').read_text())
    coords={int(s):tuple(c) for s,c in slow['coordinatesBySlot'].items()};sq_index={c:i for i,c in enumerate(sq)}
    covers={int(a):set(v) for a,v in payne['equivariant40']['covers'].items()}
    Bslot=[[int(s in covers[x]) for s in range(45)] for x in range(40)]
    # Reorder B columns to the independent square-coordinate order used by Dsq.
    B=[[0]*45 for _ in range(40)]
    for s,c in coords.items():
        j=sq_index[c]
        for x in range(40):B[x][j]=Bslot[x][s]

    I=[[int(i==j) for j in range(40)] for i in range(40)];J=[[1]*40 for _ in range(40)]
    NNt=mm(N,tr(N));NtN=mm(tr(N),N);DD=mm(Dsq,tr(Dsq));CC=mm(Cns,tr(Cns))
    wantNN=[[4*I[i][j]+Apoint[i][j] for j in range(40)] for i in range(40)]
    wantNtN=[[4*I[i][j]+Aline[i][j] for j in range(40)] for i in range(40)]
    wantDD=[[12*I[i][j]+6+3*Aline[i][j] for j in range(40)] for i in range(40)]
    wantCC=[[6*I[i][j]+3-3*Aline[i][j] for j in range(40)] for i in range(40)]
    ND=mm(N,Dsq);NC=mm(N,Cns)
    wantND=[[1+3*B[i][j] for j in range(45)] for i in range(40)];wantNC=[[1]*36 for _ in range(40)]

    D0=centered(Dsq,F(2,5));C0=centered(Cns,F(1,4));B0=centered(B,F(1,5))
    D0D0=fmm(D0,tr(D0));C0C0=fmm(C0,tr(C0));ND0=fmm([[F(x) for x in r] for r in N],D0);NC0=fmm([[F(x) for x in r] for r in N],C0)
    zero40=[[F(0)]*40 for _ in range(40)];zero4036=[[F(0)]*36 for _ in range(40)]
    centered_sum=[[D0D0[i][j]+C0C0[i][j] for j in range(40)] for i in range(40)]
    want_centered_sum=[[F(18)*(F(int(i==j))-F(1,40)) for j in range(40)] for i in range(40)]
    projectors_orthogonal=fmm(D0D0,C0C0)==zero40
    D_idempotent=fmm(D0D0,D0D0)==[[F(18)*x for x in r] for r in D0D0]
    C_idempotent=fmm(C0C0,C0C0)==[[F(18)*x for x in r] for r in C0C0]
    ND0_law=ND0==[[F(3)*x for x in r] for r in B0]

    checks={
      'NNt_equals_4I_plus_A_points':NNt==wantNN,
      'NtN_equals_4I_plus_A_lines':NtN==wantNtN,
      'square_polar_Gram_law':DD==wantDD,
      'nonsquare_polar_Gram_law':CC==wantCC,
      'uncentered_sum_equals_18I_plus_9J':add(DD,CC)==[[18*I[i][j]+9 for j in range(40)] for i in range(40)],
      'ND_equals_J_plus_3B_objectwise':ND==wantND,
      'NC_equals_J_each_nonsquare_is_a_spread':NC==wantNC,
      'centered_D_rank_24':rank(D0)==24,
      'centered_C_rank_15':rank(C0)==15,
      'centered_B_rank_24':rank(B0)==24,
      'centered_projectors_are_orthogonal':projectors_orthogonal,
      'D0D0_is_18_times_a_projector':D_idempotent,
      'C0C0_is_18_times_a_projector':C_idempotent,
      'centered_projectors_resolve_1_perp':centered_sum==want_centered_sum,
      'ND0_equals_3B0':ND0_law,
      'NC0_equals_zero':NC0==zero4036,
    }
    out={'schema':'holotrade.o5-polar-w33-24-15-split.v1','status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,
      'matrices':{'N':'40 W33 points x 40 W33 lines','D':'40 W33 lines x 45 square O5 points, polar incidence','C':'40 W33 lines x 36 nonsquare O5 points, polar incidence','B':'40 W33 points x 45 slow/Payne targets'},
      'exactLaws':['N N^T=4I+A_points','N^T N=4I+A_lines','D D^T=12I+6J+3A_lines','C C^T=6I+3J-3A_lines','D D^T+C C^T=18I+9J','N D=J+3B','N C=J','N D0=3B0','N C0=0'],
      'harmonicDecomposition':{'D0Rank':24,'C0Rank':15,'B0Rank':24,'D0D0t':'18 P_24','C0C0t':'18 P_15','sum':'18(I-J/40)'},
      'theorem':'The square and nonsquare O(5,3) polar incidence matrices are complementary tight frames for the 24- and 15-dimensional nontrivial W33 line modules. W33 point-line incidence N annihilates the 15-dimensional spread sector exactly and transmits the 24-dimensional square sector into the Payne transform via ND0=3B0. Hence the recurring 24/15 split and rank-25 fast/slow channel are one incidence-theoretic decomposition.',
      'boundary':'Exact q=3 finite linear algebra over Q after integer incidence construction. The 40 isotropic objects here are W33 lines, preserving the point/line correction; no equivariant identification with the distinct fast-point 40-set is assumed.'}
    if '--write' in sys.argv:(ROOT/'data/o5_polar_w33_24_15_split.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,indent=2,sort_keys=True));return 0 if out['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
