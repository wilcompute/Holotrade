#!/usr/bin/env python3
"""Exact finite core for W33 Payne derivation versus the 45-target slow path."""
from __future__ import annotations
import itertools

Q=3;D=4

def norm(v):
 r=tuple(int(x)%Q for x in v)
 for x in r:
  if x:
   z=pow(x,-1,Q);return tuple(z*y%Q for y in r)
 raise ValueError("zero vector")

def form(u,v):return (u[0]*v[2]-u[2]*v[0]+u[1]*v[3]-u[3]*v[1])%Q

def mm(a,b):return tuple(tuple(sum(a[i][k]*b[k][j] for k in range(D))%Q for j in range(D)) for i in range(D))
def mv(a,v):return tuple(sum(a[i][k]*v[k] for k in range(D))%Q for i in range(D))
def inv(a):
 A=[list(a[i])+[int(i==j) for j in range(D)] for i in range(D)];r=0
 for c in range(D):
  p=next((i for i in range(r,D) if A[i][c]%Q),None)
  if p is None:raise ValueError("singular")
  A[r],A[p]=A[p],A[r];z=pow(A[r][c]%Q,-1,Q);A[r]=[z*x%Q for x in A[r]]
  for i in range(D):
   if i!=r and A[i][c]%Q:
    z=A[i][c]%Q;A[i]=[(A[i][j]-z*A[r][j])%Q for j in range(2*D)]
  r+=1
 return tuple(tuple(A[i][D+j] for j in range(D)) for i in range(D))

def mkey(a):
 f=tuple(x for r in a for x in r);n=tuple(-x%Q for x in f);return min(f,n)

def tv(v,lam):
 E=[tuple(int(k==j) for k in range(D)) for j in range(D)]
 return tuple(tuple((int(i==j)+lam*form(E[j],v)*v[i])%Q for j in range(D)) for i in range(D))

def w33():
 P=sorted({norm(v) for v in itertools.product(range(Q),repeat=D) if any(v)});I={p:i for i,p in enumerate(P)}
 C=[c for c in itertools.product(range(Q),repeat=2) if c!=(0,0)];L=set()
 for i,j in itertools.combinations(range(40),2):
  if form(P[i],P[j]):continue
  s=frozenset(I[norm(tuple(a*P[i][k]+b*P[j][k] for k in range(D)))] for a,b in C)
  if len(s)==4:L.add(s)
 assert len(P)==len(L)==40
 return P,sorted(L,key=lambda s:tuple(sorted(s)))

def col(P,a,b):return a==b or form(P[a],P[b])==0

def payne(P,L,base=0):
 O=[i for i in range(40) if i!=base and not col(P,base,i)];J={p:i for i,p in enumerate(O)}
 old=set()
 for l in L:
  if base in l:continue
  t=frozenset(J[p] for p in l if p in J);assert len(t)==3;old.add(t)
 new=set()
 for y in O:
  C=[z for z in range(40) if col(P,z,base) and col(P,z,y)]
  Dp=[z for z in range(40) if all(col(P,z,u) for u in C)]
  t=[z for z in Dp if z!=base];assert len(t)==3 and all(z in J for z in t)
  new.add(frozenset(J[z] for z in t))
 assert len(O)==27 and len(old)==36 and len(new)==9 and not old&new
 assert all(sum(v in l for l in new)==1 for v in range(27))
 return O,sorted(old,key=lambda s:tuple(sorted(s))),sorted(new,key=lambda s:tuple(sorted(s)))

def slow_dual(rom):
 B=rom["linesB"];L=[]
 for s in range(45):
  t=frozenset(i for i,l in enumerate(B) if s in l);assert len(t)==3;L.append(t)
 assert len(set(L))==45
 return L

def adj(n,L):
 A=[[False]*n for _ in range(n)]
 for l in L:
  for u,v in itertools.combinations(l,2):A[u][v]=A[v][u]=True
 return A

def gq24(A):
 if len(A)!=27 or any(sum(r)!=10 for r in A):return False
 for i,j in itertools.combinations(range(27),2):
  if sum(A[i][k] and A[j][k] for k in range(27))!=(1 if A[i][j] else 5):return False
 return True

def npairs(A,r):
 N=[i for i in range(27) if A[r][i]];E=[(u,v) for u,v in itertools.combinations(N,2) if A[u][v]]
 assert len(E)==5 and set(itertools.chain.from_iterable(E))==set(N)
 return sorted(E)

def isomorphisms(S,T):
 A=adj(27,S);B=adj(27,T);assert gq24(A) and gq24(B);TS=set(T);sp=npairs(A,0);sn=sorted(set(itertools.chain.from_iterable(sp)));so=[x for x in range(27) if x and x not in sn]
 for tr in range(27):
  tp=npairs(B,tr);tn=sorted(set(itertools.chain.from_iterable(tp)));to=[x for x in range(27) if x!=tr and x not in tn]
  for pm in itertools.permutations(range(5)):
   for mask in range(32):
    m={0:tr}
    for i,(u,v) in enumerate(sp):
     x,y=tp[pm[i]]
     if mask>>i&1:x,y=y,x
     m[u]=x;m[v]=y
    C={}
    bad=False
    for s in so:
     sig=frozenset(m[n] for n in sn if A[s][n]);C[s]=[t for t in to if frozenset(n for n in tn if B[t][n])==sig]
     if not C[s]:bad=True;break
    if bad:continue
    order=sorted(so,key=lambda s:(len(C[s]),s));used=set(m.values())
    def rec(k):
     if k==len(order):
      z=tuple(m[i] for i in range(27))
      if len(set(z))==27 and {frozenset(z[x] for x in l) for l in S}==TS:yield z
      return
     s=order[k]
     for t in C[s]:
      if t in used or any(A[s][q]!=B[t][m[q]] for q in m):continue
      m[s]=t;used.add(t);yield from rec(k+1);used.remove(t);del m[s]
    yield from rec(0)

def actions(P,rom):
 V=[v for v in itertools.product(range(Q),repeat=D) if any(v)];G=sorted({tv(tuple(v),l) for v in V for l in (1,2)});assert len(G)==80
 PI={p:i for i,p in enumerate(P)};R=sorted(rom["table"],key=lambda r:r["slot"]);M=[tuple(tuple(int(x)%Q for x in row) for row in r["spMatrix"]) for r in R];K={mkey(g):i for i,g in enumerate(M)};assert len(K)==45
 PA=[];SA=[]
 for t in G:
  ti=inv(t);PA.append(tuple(PI[norm(mv(t,p))] for p in P));a=[]
  for g in M:
   k=mkey(mm(mm(t,g),ti));assert k in K;a.append(K[k])
  assert len(set(a))==45;SA.append(tuple(a))
 return PA,SA

def eset(a,s):return frozenset(a[x] for x in s)
def ovoid(o,banks):return len(o)==9 and all(len(o&set(l))==1 for l in banks)
def equivariant_covers(base,o,PA,SA):
 M={base:o};F=[base]
 while F:
  N=[]
  for p in F:
   for a,b in zip(PA,SA):
    q=a[p];z=eset(b,M[p])
    if q in M and M[q]!=z:return None
    if q not in M:M[q]=z;N.append(q)
  F=N
 return M if len(M)==40 and len(set(M.values()))==40 else None
