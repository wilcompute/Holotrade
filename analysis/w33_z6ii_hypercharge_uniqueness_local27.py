#!/usr/bin/env python3
"""Uniqueness of canonical hypercharge for the exact local E6 27 shell.

For the explicit Z6-II witness, enumerate the 27 shifted first-E8 momenta at
the local E6 T1 point.  Solve for every Cartan vector Y' whose charge on all
27 weights equals the certified Standard-Model hypercharge assignment.

The solution space is one-dimensional:
  Y(t)=(t,-2t-1/4,t,5/12,-7/12,1/4,1/4,-5/12).

Its Euclidean E8 Cartan norm is
  Y(t)^2 = 6 t^2 + t + 7/8.
Canonical GUT normalization requires
  kY=2Y^2=5/3, i.e. Y^2=5/6.
Then
  6t^2+t+1/24=0
or
  (12t+1)^2=0,
so t=-1/12 uniquely, exactly the previously certified Y.

Consequence: once the complete spectrum engine is externally benchmarked, a
remaining anomaly of this canonical Y cannot be repaired by mixing with the
other first-E8 Cartan U(1)'s while preserving both the full local-27 charges
and kY=5/3.  One must instead fix the spectrum/projection or reject the witness.
"""
from __future__ import annotations
import itertools,json,math
from fractions import Fraction as F
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/w33_z6ii_hypercharge_uniqueness_local27.json'

V=tuple(map(F,('1/6','1/3','-1/2','0','0','0','0','0')))
Y=tuple(map(F,('-1/12','-1/12','-1/12','5/12','-7/12','1/4','1/4','-5/12')))

def dot(a,b):return sum(x*y for x,y in zip(a,b))
def in_e8(p):
    if all(x.denominator==1 for x in p):return sum(int(x) for x in p)%2==0
    if all(x.denominator==2 and abs(x.numerator)%2==1 for x in p):
        s=sum(p);return s.denominator==1 and int(s)%2==0
    return False
def shell(sh,target):
    R=math.sqrt(float(target));out=[]
    for half in (False,True):
        choices=[]
        for s in sh:
            vals=[]
            for n in range(-4,5):
                p=F(n) if not half else F(2*n+1,2)
                if (p+s)**2<=target:vals.append(p)
            choices.append(vals)
        for P in itertools.product(*choices):
            if not in_e8(P):continue
            q=tuple(P[i]+sh[i] for i in range(8))
            if dot(q,q)==target:out.append(q)
    return sorted(set(out))
def rref_solve(A,b):
    M=[list(A[i])+[b[i]] for i in range(len(A))]
    m=len(M);n=len(A[0]);r=0;piv=[]
    for c in range(n):
        p=next((i for i in range(r,m) if M[i][c]),None)
        if p is None:continue
        M[r],M[p]=M[p],M[r];z=M[r][c];M[r]=[x/z for x in M[r]]
        for i in range(m):
            if i!=r and M[i][c]:
                z=M[i][c];M[i]=[M[i][j]-z*M[r][j] for j in range(n+1)]
        piv.append(c);r+=1
    free=[c for c in range(n) if c not in piv]
    assert free==[0]
    # set x0=t; derive affine coefficients ai*t+bi
    coeff=[(F(0),F(0)) for _ in range(n)]
    coeff[0]=(F(1),F(0))
    for row,c in enumerate(piv):
        # x_c + M[row][0] t = rhs
        coeff[c]=(-M[row][0],M[row][-1])
    return coeff

def main(write=True):
    qs=shell(V,F(25,18));assert len(qs)==27
    charges=[dot(q,Y) for q in qs]
    coeff=rref_solve(qs,charges)
    expected=[
      (F(1),F(0)),(F(-2),F(-1,4)),(F(1),F(0)),(F(0),F(5,12)),
      (F(0),F(-7,12)),(F(0),F(1,4)),(F(0),F(1,4)),(F(0),F(-5,12))]
    assert coeff==expected
    # norm = A t^2+B t+C
    A=sum(a*a for a,b in coeff);B=sum(2*a*b for a,b in coeff);C=sum(b*b for a,b in coeff)
    assert (A,B,C)==(F(6),F(1),F(7,8))
    # norm-5/6 = 6t^2+t+1/24 = (12t+1)^2/24
    assert C-F(5,6)==F(1,24)
    t=F(-1,12)
    vec=tuple(a*t+b for a,b in coeff)
    assert vec==Y and dot(vec,vec)==F(5,6)
    out={'schema':'w33.z6ii_hypercharge_uniqueness_local27.v1','status':'PASS_UNIQUE_CANONICAL_HYPERCHARGE',
      'local_shell_weights':27,
      'charge_preserving_family':'Y(t)=(t,-2t-1/4,t,5/12,-7/12,1/4,1/4,-5/12)',
      'norm':'Y(t)^2=6t^2+t+7/8',
      'canonical_condition':'kY=2Y^2=5/3',
      'factorization':'Y(t)^2-5/6=(12t+1)^2/24',
      'unique_parameter':'t=-1/12',
      'unique_vector':[str(x) for x in Y],
      'consequence':'No first-E8 Cartan mixing can preserve the complete local-27 hypercharges and kY=5/3 while changing Y. If a benchmarked full spectrum remains anomalous under this Y, the witness must be repaired at the spectrum/embedding level or rejected.',
      'checks':{'27_shell':True,'affine_solution_dimension':1,'canonical_norm_unique':True}}
    if write:OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2));return out
if __name__=='__main__':main(True)
