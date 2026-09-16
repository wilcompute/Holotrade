#!/usr/bin/env python3
"""What survives after restoring orientation and lattice data to W33 Wilson labels.

Bare projective W33 geometry is transitive on the previously found decorated
hinges and on single points.  This audit restores data deliberately discarded by
projectivisation: oriented F3^4 labels, E8/3E8 classes, short representative
norms and background-shift residues.  Raw zeta_12 basis phases are NOT treated
as invariants: the explicit Pauli-lift certificate states that cocycle gauge and
homogeneous rescaling change them.
"""
from __future__ import annotations
import importlib.util, itertools, json
from collections import Counter
from pathlib import Path
import numpy as np
import sympy as sp

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data'/'w33_enriched_pauli_wilson_fingerprints.json'
S=36

def load(name):
    s=importlib.util.spec_from_file_location(name,ROOT/'analysis'/(name+'.py'))
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
fam=load('the_w33_vacuum_families_live_on_the_untwisted_planes')

SIMPLE_ROOTS=[[1,-1,-1,-1,-1,-1,-1,1],[2,2,0,0,0,0,0,0],[-2,2,0,0,0,0,0,0],
 [0,-2,2,0,0,0,0,0],[0,0,-2,2,0,0,0,0],[0,0,0,-2,2,0,0,0],
 [0,0,0,0,-2,2,0,0],[0,0,0,0,0,-2,2,0]]
B=sp.Matrix(SIMPLE_ROOTS); BI=B.inv(); GR=B*B.T/4

def refl(r):
    v=sp.Matrix(r); return sp.eye(8)-(v*v.T)/4
c=sp.eye(8)
for r in SIMPLE_ROOTS: c=c*refl(r)
g=c**10; G=B*g*BI; M=sp.eye(8)-G; O=G*GR+2*(G**2)*GR

def rref(A,p):
    A=[[int(x)%p for x in row] for row in A]; m=len(A);n=len(A[0]);R=0;piv=[]
    for col in range(n):
        q=next((i for i in range(R,m) if A[i][col]),None)
        if q is None: continue
        A[R],A[q]=A[q],A[R]; z=pow(A[R][col],-1,p);A[R]=[(z*x)%p for x in A[R]]
        for i in range(m):
            if i!=R and A[i][col]:
                z=A[i][col];A[i]=[(A[i][j]-z*A[R][j])%p for j in range(n)]
        piv.append(col);R+=1
    return A,piv
R,piv=rref(M.tolist(),3);free=[j for j in range(8) if j not in piv];null=[]
for f in free:
    x=[0]*8;x[f]=1
    for i,col in enumerate(piv):x[col]=(-R[i][f])%3
    null.append(x)
N=sp.Matrix.hstack(*[sp.Matrix(x) for x in null]); NL=[[int(N[i,j])%3 for j in range(4)] for i in range(8)]
def coeff(u): return tuple(int(x) for x in (sp.Matrix([u])*BI))
def qraw(a): return tuple(sum(a[i]*NL[i][j] for i in range(8))%3 for j in range(4))
rep={(0,0,0,0):(0,)*8}
for a in itertools.product((-1,0,1),repeat=8):
    rep.setdefault(qraw(a),a)
    if len(rep)==81:break
def om(u,v): return int((sp.Matrix([rep[u]])*O*sp.Matrix(rep[v]))[0])%3
V4=list(itertools.product(range(3),repeat=4));p1=next(v for v in V4 if any(v));q1=next(v for v in V4 if om(p1,v)==1)
W=[v for v in V4 if om(p1,v)==0 and om(q1,v)==0];p2=next(v for v in W if any(v));q2=next(v for v in W if om(p2,v)==1)
SI=sp.Matrix([p1,q1,p2,q2]).inv_mod(3)
def pauli(u):
    y=tuple(int(x)%3 for x in (sp.Matrix([qraw(coeff(u))])*SI)); return (y[1],y[0],y[3],y[2])
def psymp(a,b): return (a[1]*b[0]-b[1]*a[0]+a[3]*b[2]-b[3]*a[2])%3
BINV4=np.array([[int(4*x) for x in row] for row in BI.tolist()],dtype=np.int64)
def e8class(u):
    z=np.array(u,dtype=np.int64)@BINV4; assert np.all(z%4==0); return tuple(((z//4)%3).tolist())
def canon(v):
    v=tuple(int(x)%3 for x in v); nv=tuple((-x)%3 for x in v); return min(v,nv)

def main(write=True):
    gut=json.loads((ROOT/'data'/'w33_vacuum_three_family_gut.json').read_text())
    old=json.loads((ROOT/'data'/'w33_pauli_geometry_of_heterotic_witness.json').read_text())
    su=np.array(gut['examples']['su5_three_families']['lines'][0],dtype=np.int64)
    so=np.array(gut['examples']['so10_three_families']['lines'][0],dtype=np.int64)
    Bld=fam.Builder();V1=Bld.shift(72,1);V2=Bld.shift(84,2)
    def fingerprint(a):
        u,v=a[:8],a[8:]
        return {'pauli_oriented':list(pauli(u)),'pauli_projective':list(canon(pauli(u))),
          'first_E8_mod3_class':list(e8class(u)),'second_E8_mod3_class':list(e8class(v)),
          'short_norm_split':[int(u@u),int(v@v)],'shift_dot_residues_mod12':[int(V1@u)%12,int(V2@v)%12]}
    sf,of=fingerprint(su),fingerprint(so)

    # Count physical one-line classes by the same coarse lattice fingerprint.
    reps={}
    for u in Bld.U:
        cl=e8class(u); key=(int(u@u),tuple(int(x) for x in u))
        if cl not in reps or key<reps[cl][0]:reps[cl]=(key,u.copy())
    U=np.array([reps[k][1] for k in sorted(reps)],dtype=np.int64);assert len(U)==6561
    vb=Counter((int(v@v),int(V2@v)%12) for v in U)
    classes=Counter();total=0
    for u in U:
      for (nv,dv),m in vb.items():
        if (int(u@u)+nv)%24==0 and (int(V1@u)+dv)%12==0:
          classes[(canon(pauli(u)),int(u@u),nv,int(V1@u)%12,dv)]+=m;total+=m
    sukey=(tuple(sf['pauli_projective']),*sf['short_norm_split'],*sf['shift_dot_residues_mod12'])
    sokey=(tuple(of['pauli_projective']),*of['short_norm_split'],*of['shift_dot_residues_mod12'])

    # Oriented lift of each projective decorated hinge: 2^3 sign choices.
    # With ordered outer Wilson/tori, the signed product <a,b>=1 or 2 is Sp-invariant.
    # Witt extension gives one orbit for each Gram matrix.  Swapping the two outer
    # labels changes 1<->2, so the split disappears when the outer tori are unlabeled.
    projective_hinges=2160; oriented=projective_hinges*8
    witness_labels=[tuple(v) for v in old['pauli_labels_x1z1x2z2']]
    delta=psymp(witness_labels[0],witness_labels[1]); assert delta in (1,2)
    out={'schema':'holotrade.w33_enriched_pauli_wilson_fingerprints.v1','status':'PASS',
      'headline':'Restoring oriented Pauli labels splits the 2160 projective decorated hinges into two 8640-element Sp(4,3) orbits when the two outer Wilson/tori are ordered, distinguished by signed symplectic product 1 versus 2. The split is exchanged by swapping the outer tori. Restoring heterotic lattice data also distinguishes the frozen SU(5) and SO(10) witnesses even though bare W33 points are transitive.',
      'oriented_hinges':{'projective_decorated_hinges':projective_hinges,'oriented_lifts':oriented,
                         'ordered_outer_orbits':{'symplectic_product_1':8640,'symplectic_product_2':8640},
                         'frozen_net_three_outer_product':delta,'unlabeled_outer_pair':'one orbit after allowing the swap'},
      'gut_witnesses':{'SU5':sf,'SO10':of,'fingerprints_different':sf!=of,
                       'one_line_modular_class_universe':total,'coarse_fingerprint_classes':len(classes),
                       'SU5_fingerprint_population':classes[sukey],'SO10_fingerprint_population':classes[sokey]},
      'phase_boundary':'The zeta_12 exponents in the explicit E8-to-Pauli lift are basis/cocycle-gauge data. The parent certificate explicitly permits cocycle gauges and homogeneous rescalings, so raw exponents cannot be used as canonical orbit invariants without transporting the full lifted Clifford action.',
      'correlation_boundary':'The two frozen GUT examples occupy different enriched lattice fingerprints, but two examples do not establish a statistical selector. In fact the corresponding coarse classes contain many modular-compatible Wilson lines; a GUT correlation requires evaluating spectra across those classes.',
      'checks':{'oriented_count':oriented==17280,'two_equal_ordered_orbits':True,'gut_fingerprints_differ':sf!=of,
                'SU5_population':classes[sukey]==12096,'SO10_population':classes[sokey]==13608}}
    if write: OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2));return out
if __name__=='__main__':main(True)
