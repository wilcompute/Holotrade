#!/usr/bin/env python3
"""Exact SM-chiral census of every net-|3| class from w33_su5_breaking_exhaustive.

This upgrades bf7ce0a's 10,000-model measurement to an exhaustive computation over
the physical E8/3E8 Wilson-class universe.  The same shell-factorisation used for
the exact quark-doublet census is applied simultaneously to Q,u^c,d^c,L,e^c.
For the negative-Q orientation we exchange the two A2 Dynkin nodes; this is only
the conventional colour 3 <-> 3bar relabelling, after which all models are quoted
with Q=+3.
"""
from __future__ import annotations
import importlib.util, itertools, json
from collections import Counter, defaultdict
from fractions import Fraction as Fr
from pathlib import Path
import numpy as np
import sympy as sp

ROOT=Path(__file__).resolve().parents[1]
S=36
OUT=ROOT/'data'/'w33_su5_sm_chiral_exhaustive.json'
ORDER=['Q','uc','dc','L','ec']
SM5=sorted([Fr(-1,3)]*3+[Fr(1,2)]*2)

def load(name):
    s=importlib.util.spec_from_file_location(name,ROOT/'analysis'/(name+'.py'))
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
fam=load('the_w33_vacuum_families_live_on_the_untwisted_planes')
gut=load('does_the_w33_vacuum_contain_a_three_family_gut')
ex=load('w33_su5_breaking_exhaustive')

def simple8(C,GEN8):
    pos=[r for r in C if r@GEN8>0]; ps={tuple(r) for r in pos}
    return [r for r in pos if not any(tuple(r-s) in ps for s in pos if not np.array_equal(s,r))]

def weights5(A4,GEN8):
    sr=simple8(A4,GEN8)
    A=np.array([[int(x@y)//S for y in sr] for x in sr],dtype=int)
    adj={i:[j for j in range(4) if i!=j and A[i,j]] for i in range(4)}
    start=next(i for i in adj if len(adj[i])==1); path=[start]; prev=None
    while len(path)<4:
        nxt=[j for j in adj[path[-1]] if j!=prev]; prev=path[-1]; path.append(nxt[0])
    omega=np.array(sp.Matrix(A).inv().tolist(),dtype=float)@np.array(sr,dtype=float)
    w0=omega[path[0]]; W={tuple(np.rint(w0*12).astype(int))}; fr=[w0]
    while fr:
        nf=[]
        for w in fr:
            for al in np.array(sr,float):
                if int(round(float(w@al)/S))>0:
                    w2=w-al; k=tuple(np.rint(w2*12).astype(int))
                    if k not in W: W.add(k); nf.append(w2)
        fr=nf
    return np.array([np.array(k,float)/12 for k in W])

def hypercharge(A4,c3,c2,five):
    basis=np.array(A4,float); _,sv,vt=np.linalg.svd(basis); Bs=vt[:int(np.sum(sv>1e-8))]
    M=np.array(list(c3)+list(c2),float); Mb=M@Bs.T; _,_,vt2=np.linalg.svd(Mb)
    null=[Bs.T@vt2[i] for i in range(vt2.shape[0]) if np.linalg.norm(Mb@vt2[i])<1e-7]
    assert len(null)==1; y=null[0]
    q=np.array([w@y/S for w in five]); uq=sorted(set(round(float(x),10) for x in q)); assert len(uq)==2
    y*=float(Fr(5,6)/Fr(abs(uq[1]-uq[0])).limit_denominator(10**6))
    for z in (y,-y):
        if sorted(Fr(int(round(float(w@z/S)*6)),6) for w in five)==SM5:
            assert abs(2*float(z@z)/S-5/3)<1e-7; return z
    raise AssertionError('hypercharge orientation')

def a2orbit(lam):
    x0=(lam[0]+1,lam[1]+1); orb={x0:1}; fr=[x0]
    while fr:
        nf=[]
        for p,q in fr:
            for y in ((-p,p+q),(p+q,-q)):
                if y not in orb: orb[y]=-orb[(p,q)]; nf.append(y)
        fr=nf
    return orb

def N(M,lam,y6):
    return sum(sg*sg2*M.get((p-1,q-1,r-1,y6),0)
      for (p,q),sg in a2orbit(lam[:2]).items()
      for r,sg2 in ((lam[2]+1,1),(-(lam[2]+1),-1)))

DEFS={
 'Q':((1,0,1),1,(0,1,1),-1),
 'uc':((0,1,0),-4,(1,0,0),4),
 'dc':((0,1,0),2,(1,0,0),-2),
 'L':((0,0,1),-3,(0,0,1),3),
 'ec':((0,0,0),6,(0,0,0),-6)}

def indices(rows,c3,c2,y,GEN8,swap=False):
    a,b=simple8(c3,GEN8)
    if swap: a,b=b,a
    beta=simple8(c2,GEN8)[0]; M={}
    if len(rows):
        L=np.stack([rows@a,rows@b,rows@beta],axis=1)//S
        Y=np.rint((rows@y/S)*6).astype(int)
        assert np.max(np.abs((rows@y/S)*6-Y))<1e-5
        for l,yy in zip(L,Y):
            k=(int(l[0]),int(l[1]),int(l[2]),int(yy)); M[k]=M.get(k,0)+1
    return {n:N(M,d[0],d[1])-N(M,d[2],d[3]) for n,d in DEFS.items()}

def main(write=True):
    parent=json.loads((ROOT/'data'/'w33_vacuum_three_family_gut.json').read_text())
    first=np.array(parent['examples']['su5_three_families']['lines'][0],dtype=np.int64)
    a1u,a1v=first[:8],first[8:]
    B=fam.Builder(); V1=B.shift(72,1); V2=B.shift(84,2); V=np.concatenate([V1,V2]); GEN8=fam.GEN[:8]

    reps={}
    for u in B.U:
        c=ex.e8class(u); key=(int(u@u),tuple(int(x) for x in u))
        if c not in reps or key<reps[c][0]: reps[c]=(key,u.copy())
    U=np.array([reps[c][1] for c in sorted(reps)],dtype=np.int64); assert len(U)==6561

    Z=np.zeros_like(B.R6); R16=np.vstack([np.hstack([B.R6,Z]),np.hstack([Z,B.R6])])
    d=R16@V; gauge=R16[((R16@first)%S==0)&(d%S==0)]
    A4=next(C for C in ex.components(gauge) if ex.cname(C)=='A4' and np.any(C[:,:8]))[:,:8]
    five=weights5(A4,GEN8)
    first_untw=B.R6[((B.R6@V1)%S==12)&((B.R6@a1u)%S==0)]

    breaking=[]
    for u in U:
        cs=ex.components(A4[(A4@u)%S==0])
        if sorted(ex.cname(C) for C in cs)==['A1','A2']: breaking.append(u.copy())
    assert len(breaking)==1620

    vb=defaultdict(list)
    for v in U: vb[(int(v@v)%24,int(V2@v)%12,int(a1v@v)%12)].append(v.copy())
    shell={}
    def shells(X):
        k=tuple(int(x) for x in X)
        if k not in shell: shell[k]=B.coset(np.array(X,dtype=np.int64))
        return shell[k]
    hs=(0,8,16,24,32,40,48)
    def second(v):
        z=[]
        for n1 in range(3):
          for n2 in range(3):
            W,h=shells(V2+n1*a1v+n2*v); C=Counter(int(x) for x in h); z.extend(C.get(x,0) for x in hs)
        return tuple(z)
    vg={k:Counter(second(v) for v in vs) for k,vs in vb.items()}

    def local(s1,s2,fp):
        o=fp*7; ans=0
        for tot,m in ((48,1),(24,3),(0,9)):
          for j,h1 in enumerate(hs):
            h2=tot-h1
            if h2 in hs: ans+=m*s1[o+j]*s2[o+hs.index(h2)]
        return ans

    census=Counter(); twisted=Counter(); models=0; first_class=Counter()
    for u in breaking:
        cs=ex.components(A4[(A4@u)%S==0]); c3=next(C for C in cs if ex.cname(C)=='A2'); c2=next(C for C in cs if ex.cname(C)=='A1')
        unt=first_untw[(first_untw@u)%S==0]
        I=ex.qindex8(c3,c2,unt)
        if abs(I)!=1: continue
        y=hypercharge(A4,c3,c2,five)
        a=indices(unt,c3,c2,y,GEN8,False); b=indices(unt,c3,c2,y,GEN8,True)
        if a['Q']==1: swap=False; Uidx=a
        elif b['Q']==1: swap=True; Uidx=b
        else: raise AssertionError('colour orientation')
        first_class[tuple(Uidx[n] for n in ORDER)]+=len(vb[((-int(u@u))%24,(-int(V1@u))%12,(-int(a1u@u))%12)])
        fs={n:[] for n in ORDER}
        for n1 in range(3):
          for n2 in range(3):
            W,h=shells(V1+n1*a1u+n2*u)
            for hh in hs:
                q=indices(W[h==hh],c3,c2,y,GEN8,swap)
                for n in ORDER: fs[n].append(q[n])
        key=((-int(u@u))%24,(-int(V1@u))%12,(-int(a1u@u))%12)
        for s2,nv in vg[key].items():
            T=[]; ZT=[]
            for n in ORDER:
                tw=3*sum(local(tuple(fs[n]),s2,f) for f in range(9)); ZT.append(tw); T.append(3*Uidx[n]+tw)
            census[tuple(T)]+=nv; twisted[tuple(ZT)]+=nv; models+=nv

    expected=Counter({(3,0,3,3,0):56160,(3,0,0,0,0):56160,(3,0,-3,-3,0):15660})
    assert models==127980 and census==expected
    assert twisted==Counter({(0,0,-3,-3,0):127980})
    out={
      'schema':'holotrade.w33_su5_sm_chiral_exhaustive.v1','status':'PASS',
      'headline':'All 127980 net-|3| A4->A2+A1 Wilson classes have been exhausted. After the conventional colour orientation every model has Q=3 and u^c=e^c=0. Exactly 56160 have (Q,uc,dc,L,ec)=(3,0,3,3,0), 56160 have (3,0,0,0,0), and 15660 have (3,0,-3,-3,0). Hence no class in the complete Builder E8/3E8 universe has the Standard Model chiral vector (3,3,3,3,3).',
      'parent':'data/w33_su5_breaking_exhaustive.json',
      'models_with_abs_Q_3':models,
      'chiral_census':{'(3,0,3,3,0)':56160,'(3,0,0,0,0)':56160,'(3,0,-3,-3,0)':15660},
      'universal_twisted_contribution':{'(Q,uc,dc,L,ec)':[0,0,-3,-3,0],'models':127980},
      'standard_model_target':[3,3,3,3,3],
      'standard_model_models':0,
      'best_species_present':3,
      'vectorlike_minimisation_boundary':'The subset with exact SM chiral content is empty, so there is no vectorlike-matter minimisation problem inside that target set.',
      'scope':'Exhaustive over the same 6561x6561 physical Wilson-class representation and modular-compatibility conditions certified by w33_su5_breaking_exhaustive; no random sampling enters.',
      'checks':{'127980_models':models==127980,'three_patterns_only':census==expected,
                'uc_always_zero':all(k[1]==0 for k in census),'ec_always_zero':all(k[4]==0 for k in census),
                'no_SM_chiral_model':(3,3,3,3,3) not in census}
    }
    if write: OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2)); return out
if __name__=='__main__': main(True)
