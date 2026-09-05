#!/usr/bin/env python3
"""Derive every slow target's 8-axis W33 support directly from its matrix.

Previous certificates reached the same 45 objects by two independent routes:
  * the cost model: a slow anomaly is the projective class of an involution that
    is -1 on a nondegenerate 2-space L and +1 on L^perp;
  * the Payne/code route: a slow ROM slot is a weight-8 word of C2(W33), split
    as a complementary pair of 4-point center-quads.

This closes the objectwise dictionary without search. For each committed 4x4
slow target matrix g, compute ker(g-I) and ker(g+I) over F3. Each kernel has
dimension two and therefore four projective points. Their union is exactly the
slot's committed weight-8 support, and the two four-sets are exactly its
committed center-quad pair. Conversely, rebuilding the involution as +I on one
kernel and -I on the other reproduces the original projective target class.

Operational consequence: the 8-axis Payne/minimum-word metadata is a function
of the target matrix itself; the 45-row JSON dictionary is a certificate/cache,
not logically required to decode the geometry.
"""
from __future__ import annotations
import itertools,json,sys
from pathlib import Path
from w33_payne_slowpath_core import Q,D,norm,form,mkey
ROOT=Path(__file__).resolve().parents[1]

def rref_kernel(A):
    M=[[int(x)%Q for x in row] for row in A]
    piv=[];r=0
    for c in range(D):
        p=next((i for i in range(r,D) if M[i][c]%Q),None)
        if p is None:continue
        M[r],M[p]=M[p],M[r]
        z=pow(M[r][c],-1,Q);M[r]=[(z*x)%Q for x in M[r]]
        for i in range(D):
            if i!=r and M[i][c]%Q:
                z=M[i][c]%Q;M[i]=[(M[i][j]-z*M[r][j])%Q for j in range(D)]
        piv.append(c);r+=1
    free=[c for c in range(D) if c not in piv]
    basis=[]
    for f in free:
        v=[0]*D;v[f]=1
        for i,c in enumerate(piv):v[c]=(-M[i][f])%Q
        basis.append(tuple(v))
    return basis

def eigenspace(A,eig):
    K=[[((A[i][j]-(eig if i==j else 0))%Q) for j in range(D)] for i in range(D)]
    b=rref_kernel(K)
    pts=sorted({norm(tuple(sum(coeff[t]*b[t][j] for t in range(len(b)))%Q for j in range(D)))
                for coeff in itertools.product(range(Q),repeat=len(b)) if any(coeff)})
    return b,pts

def matmul(A,B):return [[sum(A[i][k]*B[k][j] for k in range(D))%Q for j in range(D)] for i in range(D)]
def inv(A):
    M=[[int(A[i][j])%Q for j in range(D)]+[int(i==j) for j in range(D)] for i in range(D)]
    for c in range(D):
        p=next(i for i in range(c,D) if M[i][c]%Q);M[c],M[p]=M[p],M[c]
        z=pow(M[c][c],-1,Q);M[c]=[(z*x)%Q for x in M[c]]
        for i in range(D):
            if i!=c and M[i][c]%Q:
                z=M[i][c]%Q;M[i]=[(M[i][j]-z*M[c][j])%Q for j in range(2*D)]
    return [r[D:] for r in M]
def cols(vs):return [[vs[j][i] for j in range(D)] for i in range(D)]
def rebuild(bplus,bminus):
    B=cols(list(bplus)+list(bminus));Di=[[0]*D for _ in range(D)]
    for i in range(D):Di[i][i]=1 if i<2 else Q-1
    return matmul(matmul(B,Di),inv(B))

def main():
    rom=json.loads((ROOT/'data/the_45_slot_rom_bijection.json').read_text())
    cert=json.loads((ROOT/'data/slow_targets_are_w33_minimum_words.json').read_text())
    rows=sorted(rom['table'],key=lambda r:r['slot']);P=sorted({norm(v) for v in itertools.product(range(Q),repeat=D) if any(v)});pi={p:i for i,p in enumerate(P)}
    outrows=[];checks=[]
    for row in rows:
        slot=int(row['slot']);A=[[int(x)%Q for x in r] for r in row['spMatrix']]
        bp,pp=eigenspace(A,1);bm,pm=eigenspace(A,Q-1)
        ip=sorted(pi[x] for x in pp);im=sorted(pi[x] for x in pm)
        got_pair=sorted([ip,im]);want=cert['dictionary'][str(slot)];want_pair=sorted([sorted(x) for x in want['centerQuadPair']]);union=sorted(ip+im)
        nondeg=(len(bp)==2 and len(bm)==2 and form(bp[0],bp[1])!=0 and form(bm[0],bm[1])!=0)
        orth=all(form(x,y)==0 for x in pp for y in pm)
        back=rebuild(bp,bm)
        # Choosing + on E_+ and - on E_- reconstructs A exactly; swapping signs
        # would reconstruct -A, the same PSp projective target.
        ok=(len(pp)==len(pm)==4 and set(pp).isdisjoint(pm) and union==sorted(want['weight8Support']) and got_pair==want_pair and nondeg and orth and mkey(back)==mkey(A))
        checks.append(ok)
        outrows.append({'slot':slot,'plusAxes':ip,'minusAxes':im,'weight8Support':union,'nondegenerate':nondeg,'mutuallyOrthogonal':orth,'reconstructsProjectiveTarget':mkey(back)==mkey(A)})
    global_checks={
      'all_45_targets_checked':len(rows)==45,
      'every_target_has_two_2d_eigenspaces':all(len(r['plusAxes'])==len(r['minusAxes'])==4 for r in outrows),
      'eigenspace_unions_equal_committed_minwords':all(checks),
      'all_eigenspaces_nondegenerate':all(r['nondegenerate'] for r in outrows),
      'plus_minus_spaces_are_perpendicular':all(r['mutuallyOrthogonal'] for r in outrows),
      'all_targets_reconstruct_projectively':all(r['reconstructsProjectiveTarget'] for r in outrows),
      '45_distinct_eigenspace_supports':len({tuple(r['weight8Support']) for r in outrows})==45,
    }
    out={'schema':'holotrade.slow-target-eigenspaces-minword.v1','status':'PASS' if all(global_checks.values()) else 'FAIL','checks':global_checks,
         'theorem':'For every committed slow target g, ker(g-I) and ker(g+I) are complementary nondegenerate 2-spaces of F3^4. Their four projective points each are exactly the two center-quads of that slot, and their eight-point union is exactly its C2(W33) minimum-word support. The target is recovered projectively by acting +1 on the first space and -1 on the second.',
         'runtimeReading':'The eight compatible cheap axes and the center-quad split can be decoded directly from the slow target matrix. The 45-row dictionary is a frozen certificate/cache, not a mathematical dependency.',
         'rows':outrows,'boundary':'Exact over F3 for the 45 committed slow target matrices. This is an objectwise finite theorem; no q-general minimum-word or GQ claim is inferred.'}
    if '--write' in sys.argv:(ROOT/'data/slow_target_eigenspaces_are_the_minword_support.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,indent=2,sort_keys=True));return 0 if out['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
