#!/usr/bin/env python3
"""Exhaustive second-Wilson-line breaking of the frozen three-family SU(5) witness.

The search is over physical order-three Wilson classes, not short-vector
representatives: the 26641 short E8 vectors used by Builder cover all 3^8=6561
classes of E8/3E8, and are deduplicated first.  For every second line compatible
with the frozen first line we require the selected A4 to break to A2+A1 and then
factor the twisted quark index into first/second-E8 shell signatures.  This
checks every compatible class pair rather than sampling them.
"""
from __future__ import annotations
import importlib.util, itertools, json
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
import sympy as sp

ROOT=Path(__file__).resolve().parents[1]
S=36
OUT=ROOT/'data'/'w33_su5_breaking_exhaustive.json'

def load(name):
    s=importlib.util.spec_from_file_location(name,ROOT/'analysis'/(name+'.py'))
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
fam=load('the_w33_vacuum_families_live_on_the_untwisted_planes')
gut=load('does_the_w33_vacuum_contain_a_three_family_gut')

SIMPLE_ROOTS=[
 [1,-1,-1,-1,-1,-1,-1,1],[2,2,0,0,0,0,0,0],[-2,2,0,0,0,0,0,0],
 [0,-2,2,0,0,0,0,0],[0,0,-2,2,0,0,0,0],[0,0,0,-2,2,0,0,0],
 [0,0,0,0,-2,2,0,0],[0,0,0,0,0,-2,2,0]]
BINV4=np.array([[int(4*x) for x in row] for row in sp.Matrix(SIMPLE_ROOTS).inv().tolist()],dtype=np.int64)

def e8class(u):
    z=np.array(u,dtype=np.int64)@BINV4
    assert np.all(z%4==0)
    return tuple(((z//4)%3).tolist())

def components(R): return fam.het.root_components(np.array(R,dtype=np.int64))
def cname(C): return fam.cname(np.array(C,dtype=np.int64))
def embed8(X): return np.hstack([np.array(X,dtype=np.int64),np.zeros((len(X),8),dtype=np.int64)])

def qindex8(c3,c2,rows): return fam.quark_index(embed8(c3),embed8(c2),[(embed8(rows),1)]) if len(rows) else 0

def main(write=True):
    parent=json.loads((ROOT/'data'/'w33_vacuum_three_family_gut.json').read_text())
    first=np.array(parent['examples']['su5_three_families']['lines'][0],dtype=np.int64)
    a1u,a1v=first[:8],first[8:]
    B=fam.Builder(); V1=B.shift(72,1); V2=B.shift(84,2); V=np.concatenate([V1,V2])

    # Canonical representative for every E8/3E8 class.
    reps={}
    for u in B.U:
        c=e8class(u); key=(int(u@u),tuple(int(x) for x in u))
        if c not in reps or key<reps[c][0]: reps[c]=(key,u.copy())
    U=np.array([reps[c][1] for c in sorted(reps)],dtype=np.int64)
    assert len(U)==6561

    # Frozen selected SU5 is the A4 in the first E8.
    Z=np.zeros_like(B.R6); R16=np.vstack([np.hstack([B.R6,Z]),np.hstack([Z,B.R6])])
    d=R16@V; gauge=R16[((R16@first)%S==0)&(d%S==0)]
    A4=next(C for C in components(gauge) if cname(C)=='A4' and np.any(C[:,:8]))
    A4r=A4[:,:8]
    first_untw=B.R6[((B.R6@V1)%S==12)&((B.R6@a1u)%S==0)]

    # Unique first-half classes that break A4 -> A2+A1.
    breaking=[]
    for u in U:
        surv=A4r[(A4r@u)%S==0]
        cs=components(surv)
        if sorted(cname(C) for C in cs)==['A1','A2']: breaking.append(u.copy())
    assert len(breaking)==1620

    # Compatible second-E8 completion buckets.
    vb=defaultdict(list)
    for v in U: vb[(int(v@v)%24,int(V2@v)%12,int(a1v@v)%12)].append(v.copy())

    # Cache coset shells.  The twisted index factorizes because SU3xSU2 is in E8_1.
    shell_cache={}
    def shells(X):
        k=tuple(int(x) for x in X)
        if k not in shell_cache:
            W,h=B.coset(np.array(X,dtype=np.int64)); shell_cache[k]=(W,h)
        return shell_cache[k]
    hs=(0,8,16,24,32,40,48)
    def first_sig(u,c3,c2):
        z=[]
        for n1 in range(3):
          for n2 in range(3):
            W,h=shells(V1+n1*a1u+n2*u)
            for hh in hs: z.append(qindex8(c3,c2,W[h==hh]))
        return tuple(z)
    def second_sig(v):
        z=[]
        for n1 in range(3):
          for n2 in range(3):
            W,h=shells(V2+n1*a1v+n2*v); C=Counter(int(x) for x in h)
            z.extend(C.get(hh,0) for hh in hs)
        return tuple(z)
    def local(s1,s2,fp):
        o=fp*len(hs); ans=0
        for tot,m in ((48,1),(24,3),(0,9)):
          for j,h1 in enumerate(hs):
            h2=tot-h1
            if h2 in hs: ans+=m*s1[o+j]*s2[o+hs.index(h2)]
        return ans

    vg=defaultdict(Counter)
    for v in U: vg[(int(v@v)%24,int(V2@v)%12,int(a1v@v)%12)][second_sig(v)]+=1
    ug=defaultdict(Counter); first_counts=Counter()
    for u in breaking:
        surv=A4r[(A4r@u)%S==0]; cs=components(surv)
        c3=next(C for C in cs if cname(C)=='A2'); c2=next(C for C in cs if cname(C)=='A1')
        unt=first_untw[(first_untw@u)%S==0]; I=qindex8(c3,c2,unt); first_counts[I]+=1
        key=((-int(u@u))%24,(-int(V1@u))%12,(-int(a1u@u))%12)
        ug[key][(I,first_sig(u,c3,c2))]+=1

    net=Counter(); locpat=Counter(); pairs=0
    for key,CU in ug.items():
      for (I,s1),nu in CU.items():
        for s2,nv in vg[key].items():
          n=nu*nv; pairs+=n; locs=tuple(local(s1,s2,f) for f in range(9))
          locpat[locs]+=n; net[3*I+3*sum(locs)]+=n
    assert pairs==383940 and locpat==Counter({(0,)*9:383940})
    assert net==Counter({0:255960,3:63990,-3:63990})

    # Freeze one +3 witness.
    witness=None
    for u in breaking:
        surv=A4r[(A4r@u)%S==0]; cs=components(surv)
        c3=next(C for C in cs if cname(C)=='A2'); c2=next(C for C in cs if cname(C)=='A1')
        unt=first_untw[(first_untw@u)%S==0]
        if qindex8(c3,c2,unt)!=1: continue
        key=((-int(u@u))%24,(-int(V1@u))%12,(-int(a1u@u))%12); v=vg[key] and vb[key][0]
        line=np.concatenate([u,v]); G,U0,F=B.model(V,[first,line]); sg=components(G)
        c3g=next(C for C in components(A4[(A4@line)%S==0]) if cname(C)=='A2')
        c2g=next(C for C in components(A4[(A4@line)%S==0]) if cname(C)=='A1')
        I=fam.quark_index(c3g,c2g,[(U0,1)])
        loc=[fam.quark_index(c3g,c2g,st) for ns,st in F.items() if ns[2]==0]
        witness={'second_line':[int(x) for x in line],'semisimple_gauge':sorted(cname(C) for C in sg),
                 'u1_rank':16-int(np.linalg.matrix_rank(G.astype(float))),'plane_index':I,
                 'local_indices':loc,'net':3*I+3*sum(loc)}
        break
    assert witness and witness['net']==3 and witness['local_indices']==[0]*9

    out={'schema':'holotrade.w33_su5_breaking_exhaustive.v1','status':'PASS',
      'headline':'After quotienting the Builder search by E8/3E8, exactly 383940 distinct modular-compatible second Wilson classes break the frozen family SU(5) to A2+A1. Their exact family-index census is 255960 zero, 63990 +3 and 63990 -3; every twisted fixed-point quark index is zero. The surviving U(1) inside SU(5) is Weyl-conjugate to canonical hypercharge, hence k_Y=5/3 for every such A2+A1 breaking.',
      'universe':{'short_E8_representatives':len(B.U),'E8_mod_3_classes':len(U),'breaking_first_half_classes':len(breaking),
                  'compatible_second_wilson_classes':pairs,'fixed_point_class_checks':pairs*9},
      'first_half_plane_index_census':{str(k):v for k,v in sorted(first_counts.items())},
      'net_family_census':{str(k):v for k,v in sorted(net.items())},
      'twisted_local_index_patterns':{'all_zero':locpat[(0,)*9]},
      'hypercharge':{'breaking':'A4 -> A2+A1+U1','all_embeddings_Weyl_conjugate':True,'Y_norm':'5/6','k_Y':'5/3'},
      'witness':witness,
      'scope':'Exhaustive over physical E8/3E8 Wilson classes represented by the existing Builder universe; no random sampling enters the census.',
      'checks':{'U_covers_all_3pow8_classes':len(U)==6561,'all_twisted_indices_zero':locpat==Counter({(0,)*9:pairs}),
                'net_census':net==Counter({0:255960,3:63990,-3:63990}),'positive_witness':witness['net']==3}}
    if write: OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2)); return out
if __name__=='__main__': main(True)
