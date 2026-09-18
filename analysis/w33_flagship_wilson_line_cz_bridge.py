#!/usr/bin/env python3
"""Flagship W33 heterotic Wilson line has the exact qutrit-CZ conjugacy fingerprint.

Parent:
  data/w33_twist_hosts_sm_in_even_order_orbifold.json

The Z6-I flagship is a Z2 orbifold of the W33 A8=SU(9) vacuum with one
order-three Wilson line W3.  On the SU(9) E8 factor this script computes the
A8 roots fixed by 2V and grades them by the W3 phase.

Exact result:
  A8 roots: 72 = 24_0 + 24_1 + 24_2.
  Neutral roots: A4 + A1 + A1 (20+2+2 roots, ranks 4+1+1).
  Hence the connected centralizer in SU(9) is
      S(U(5) x U(2) x U(2)),
  with Lie algebra su5 + su2 + su2 + u1^2, dimension 32.

An order-three SU(9) element with this centralizer has defining-representation
eigenvalue multiplicities 5+2+2, up to cycling the cube-root eigenvalues and
multiplying by a central cube root.

The standard two-qutrit controlled-Z
  CZ_3 |x,y> = omega^(x*y) |x,y>,  x,y in F3
has spectrum 1^5, omega^2, (omega^2)^2, determinant one, and adjoint grading
  sl9 = 32_0 + 24_1 + 24_2.
Therefore the flagship Wilson-line holonomy restricted to the W33 SU(9) factor
is PROJECTIVELY SU(9)-CONJUGATE to qutrit CZ_3.

The same CZ Clifford acts on the two-qutrit Pauli phase space F3^4 by
  (x1,x2,p1,p2) -> (x1,x2,p1+x2,p2+x1),
a rank-two order-three symplectic unipotent.  On W33 projective Pauli points its
cycle profile is 1^4 3^12, with the four fixed points one isotropic line.  This
matches the already-certified controlled-add class in W33-Theory because
CZ = F_target^{-1} SUM F_target (in the convention used there).

Scope:
  This is an exact conjugacy/symmetry-breaking bridge for the recorded
  heterotic model.  It does NOT prove that every Wilson line in the 60-model
  census is CZ-conjugate, nor that the five flagship top couplings equal the
  five CZ phase-zero basis states.
"""
from __future__ import annotations
import itertools, json
from collections import Counter
from fractions import Fraction as F
from pathlib import Path
import sympy as sp

ROOT=Path(__file__).resolve().parents[1]
PARENT=ROOT/'data/w33_twist_hosts_sm_in_even_order_orbifold.json'
OUT=ROOT/'data/w33_flagship_wilson_line_cz_bridge.json'

def vec(s):
    return [F(x) for part in s.split('|') for x in part.split(',')]

def dot(a,b):
    return sum(x*y for x,y in zip(a,b))

def roots8():
    out=[]
    for i,j in itertools.combinations(range(8),2):
        for si in (-1,1):
            for sj in (-1,1):
                r=[F(0)]*8;r[i]=F(si);r[j]=F(sj);out.append(tuple(r))
    for signs in itertools.product((-1,1),repeat=8):
        if sum(x<0 for x in signs)%2==0:
            out.append(tuple(F(x,2) for x in signs))
    assert len(out)==len(set(out))==240
    return out

def rank(rows):
    M=sp.Matrix([[sp.Rational(x.numerator,x.denominator) for x in r] for r in rows])
    return int(M.rank())

def components(roots):
    adj=[set() for _ in roots]
    for i in range(len(roots)):
        for j in range(i+1,len(roots)):
            if dot(roots[i],roots[j]) != 0:
                adj[i].add(j);adj[j].add(i)
    seen=set(); out=[]
    for i in range(len(roots)):
        if i in seen: continue
        stack=[i]; seen.add(i); c=[]
        while stack:
            u=stack.pop();c.append(roots[u])
            for v in adj[u]:
                if v not in seen:
                    seen.add(v);stack.append(v)
        out.append(c)
    return out

def mm(A,B):
    return tuple(tuple(sum(A[i][k]*B[k][j] for k in range(4))%3 for j in range(4)) for i in range(4))

def mpow(A,n):
    I=((1,0,0,0),(0,1,0,0),(0,0,1,0),(0,0,0,1))
    out=I
    for _ in range(n): out=mm(out,A)
    return out

def canon(v):
    v=tuple(int(x)%3 for x in v)
    nz=next(x for x in v if x)
    return tuple((2*x)%3 for x in v) if nz==2 else v

def main(write=True):
    parent=json.loads(PARENT.read_text())
    flag=parent['flagship']
    assert flag['z3Parts']==['D7+U1','A8']
    V=vec(flag['V']); W=vec(flag['W3'])
    su9=slice(8,16)
    V9=V[su9]; W9=W[su9]
    R=roots8()
    A8=[r for r in R if dot(r,[2*x for x in V9]).denominator==1]
    assert len(A8)==72

    grades={q:[] for q in range(3)}
    for r in A8:
        t=3*dot(r,W9)
        assert t.denominator==1
        grades[int(t)%3].append(r)
    counts={q:len(grades[q]) for q in grades}
    assert counts=={0:24,1:24,2:24}

    comps=components(grades[0])
    comp_sig=sorted((len(c),rank(c)) for c in comps)
    assert comp_sig==[(2,1),(2,1),(20,4)]
    neutral_rank=rank(grades[0])
    assert neutral_rank==6

    su5=[tuple(vec(r)[su9]) for r in flag['su5_simple_roots']]
    neutral_set=set(grades[0])
    assert all(r in neutral_set for r in su5)
    big=max(comps,key=len)
    assert all(r in set(big) for r in su5)
    assert rank(su5)==4

    # CZ_3 spectrum on |x,y>: phase = x*y mod 3.
    phases=[(x*y)%3 for x in range(3) for y in range(3)]
    fundamental=Counter(phases)
    assert fundamental==Counter({0:5,1:2,2:2})
    det_phase=sum(phases)%3
    assert det_phase==0

    # Adjoint/M9 phase is phase_i - phase_j; remove scalar identity from grade 0.
    madj=Counter((a-b)%3 for a in phases for b in phases)
    assert madj==Counter({0:33,1:24,2:24})
    sl9={0:madj[0]-1,1:madj[1],2:madj[2]}
    assert sl9=={0:32,1:24,2:24}
    assert sum(n*n for n in fundamental.values())-1==32

    # Standard CZ symplectic action on (x1,x2,p1,p2).
    CZ=((1,0,0,0),(0,1,0,0),(0,1,1,0),(1,0,0,1))
    I=((1,0,0,0),(0,1,0,0),(0,0,1,0),(0,0,0,1))
    assert mpow(CZ,3)==I

    # Projective W33 cycle profile.
    P=sorted({canon(v) for v in itertools.product(range(3),repeat=4) if any(v)})
    idx={p:i for i,p in enumerate(P)}
    perm=[]
    for p in P:
        q=tuple(sum(CZ[i][j]*p[j] for j in range(4))%3 for i in range(4))
        perm.append(idx[canon(q)])
    seen=set(); cyc=Counter(); fixed=[]
    for i in range(40):
        if i in seen: continue
        u=i;c=[]
        while u not in seen:
            seen.add(u);c.append(u);u=perm[u]
        cyc[len(c)]+=1
        if len(c)==1: fixed.append(P[c[0]])
    assert cyc==Counter({3:12,1:4})
    assert len(fixed)==4
    def symp(v,w): return (v[0]*w[2]+v[1]*w[3]-v[2]*w[0]-v[3]*w[1])%3
    assert all(symp(a,b)==0 for a,b in itertools.combinations(fixed,2))

    # Nonprojective 80 Pauli degrees: 8 fixed, 24 three-cycles.
    VV=[v for v in itertools.product(range(3),repeat=4) if any(v)]
    fixed_vec=sum(1 for v in VV if tuple(sum(CZ[i][j]*v[j] for j in range(4))%3 for i in range(4))==v)
    assert fixed_vec==8
    assert (80-fixed_vec)//3==24

    # Explicit Fourier conjugacy to SUM in the W33 x1,x2,p1,p2 convention.
    F2=((1,0,0,0),(0,0,0,1),(0,0,1,0),(0,2,0,0))
    F2inv=mpow(F2,3)  # F has order 4
    SUM=((1,0,0,0),(1,1,0,0),(0,0,1,2),(0,0,0,1))
    assert mm(mm(F2inv,SUM),F2)==CZ

    checks={
      'parent_flagship_has_A8_SU9_side':True,
      'A8_root_count_72':True,
      'wilson_line_root_grading_24_24_24':True,
      'neutral_root_subsystem_A4_A1_A1':True,
      'neutral_rank_6':True,
      'flagship_SU5_is_the_A4_component':True,
      'CZ_fundamental_spectrum_5_2_2':True,
      'CZ_determinant_one':True,
      'CZ_adjoint_sl9_grading_32_24_24':True,
      'centralizer_dimension_32':True,
      'CZ_order_3':True,
      'CZ_W33_cycle_profile_1pow4_3pow12':True,
      'CZ_fixed_points_form_isotropic_line':True,
      'CZ_nonzero_Pauli_profile_8_fixed_plus_24_3cycles':True,
      'CZ_is_target_Fourier_conjugate_to_SUM':True,
    }
    assert all(checks.values())
    out={
      'schema':'w33.flagship_wilson_line_cz_bridge.v1',
      'status':'PASS',
      'headline':'The order-three Wilson line of the recorded W33-class Z6-I Standard Model grades the SU(9) A8 roots as 24+24+24 with neutral subsystem A4+A1+A1. Hence its SU(9) holonomy has projective spectrum 5+2+2 and is projectively SU(9)-conjugate to the two-qutrit CZ_3 gate. CZ gives the same sl9 adjoint grading 32+24+24 and the W33 point action 1^4 3^12 with one fixed isotropic line.',
      'heterotic':{
        'parent':'data/w33_twist_hosts_sm_in_even_order_orbifold.json',
        'model':flag['label'],
        'A8_roots':72,
        'W3_root_grades':counts,
        'neutral_root_components':[{'roots':len(c),'rank':rank(c)} for c in sorted(comps,key=lambda c:-len(c))],
        'neutral_semisimple_type':'A4 + A1 + A1',
        'centralizer':'S(U(5) x U(2) x U(2))',
        'centralizer_lie_dimension':32,
        'flagship_SU5_inside_A4_component':True},
      'qutrit_CZ':{
        'definition':'CZ_3 |x,y> = omega^(x*y) |x,y>',
        'fundamental_eigenvalue_multiplicities':{'1':5,'omega':2,'omega2':2},
        'projective_SU9_conjugacy':'The heterotic holonomy is conjugate to CZ_3 up to multiplication by an SU(9) central cube-root phase and cyclic relabeling of eigenvalues.',
        'sl9_adjoint_grades':sl9,
        'symplectic_matrix_x1_x2_p1_p2':[list(r) for r in CZ],
        'W33_point_cycles':{'fixed':4,'3_cycles':12},
        'nonzero_Pauli_vector_cycles':{'fixed':8,'3_cycles':24},
        'fixed_W33_points':fixed,
        'fixed_points_are_one_isotropic_line':True,
        'relation_to_SUM':'CZ = F_target^{-1} SUM F_target'},
      'cross_repo_prior_art':{
        'W33_CZ_matrix':'analysis/w33_two_switch_generation.py',
        'W33_SUM_fixed_geometry':'data/PART_BT2757_QUTRIT_CX_W33_LAGRANGIAN_UNIPOTENT_results.json',
        'W33_A8_is_two_qutrit_pauli_grading':'analysis/PASS20260915_e8_a8_pauli_grading_closure.md'},
      'scope':{
        'proved':'exact root grading, centralizer type, CZ spectral/adjoint fingerprint, projective SU(9) conjugacy, and standard CZ W33 orbit anatomy',
        'not_proved':'that all 60 W33-class Standard Models use this CZ conjugacy class; that the flagship count of five cubic top couplings is caused by the five CZ phase-zero basis states; simultaneous canonicity of the heterotic Wilson-line basis and the repo fine-Pauli grading'},
      'checks':checks}
    if write: OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))
    return out

if __name__=='__main__':
    main(True)
