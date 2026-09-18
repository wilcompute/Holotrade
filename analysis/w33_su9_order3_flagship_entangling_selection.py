#!/usr/bin/env python3
"""Order-three SU(9) census: the flagship selects the entangling qutrit Clifford branch.

For an order-three element of SU(9), let (n0,n1,n2) be multiplicities of
(1,omega,omega^2) on the defining 9.  The determinant condition is
n1+2 n2 = 0 mod 3.  Multiplying by a central cube root cycles the labels, and
inversion swaps the two charged labels, so for centralizer/root-count purposes
we can classify by the unordered multiplicity multiset.

The complete unordered census is
  9,
  7+1+1,
  6+3,
  5+2+2,
  4+4+1,
  3+3+3.

For type (n0,n1,n2):
  neutral roots = sum_i n_i(n_i-1),
  each charged root grade = n0*n1+n1*n2+n2*n0,
  centralizer dim in su9 = sum_i n_i^2 - 1.

The recorded W33-class flagship has 24 neutral roots, 24 roots in each charged
grade, and neutral A4+A1+A1 with an SU5 factor.  Among all six spectral types,
the simultaneous conditions "contains SU5" and "charged grade = 24" select
5+2+2 uniquely.  This is the spectrum of qutrit CZ_3.

The adjacent known Clifford branch is the local quadratic phase gate S_1 x I:
its spectrum is 6+3, its sl9 grading is 44+18+18, and its symplectic action is a
rank-one transvection with W33 point cycle profile 1^13 3^9.  CZ_3 has spectrum
5+2+2, sl9 grading 32+24+24, rank-two Lagrangian-unipotent action and W33 point
profile 1^4 3^12.  Hence the flagship lies on the entangling, not local, branch.

Scope: this classifies spectral/root-centralizer types, not all physical string
Wilson-line equivalences.  The phrase "selects" refers to the exact measured
flagship root grading plus the presence of its neutral SU5.
"""
from __future__ import annotations
import itertools,json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/w33_su9_order3_flagship_entangling_selection.json'

def canon(v):
    v=tuple(x%3 for x in v)
    nz=next(x for x in v if x)
    return tuple((2*x)%3 for x in v) if nz==2 else v

def point_profile(M):
    P=sorted({canon(v) for v in itertools.product(range(3),repeat=4) if any(v)})
    idx={p:i for i,p in enumerate(P)}
    perm=[]
    for p in P:
        q=tuple(sum(M[i][j]*p[j] for j in range(4))%3 for i in range(4))
        perm.append(idx[canon(q)])
    seen=set(); cyc=Counter()
    for i in range(40):
        if i in seen: continue
        u=i;n=0
        while u not in seen:
            seen.add(u);n+=1;u=perm[u]
        cyc[n]+=1
    return dict(sorted(cyc.items()))

def adjoint_grades(n):
    n0,n1,n2=n
    m=n0*n1+n1*n2+n2*n0
    return [n0*n0+n1*n1+n2*n2-1,m,m]

def main(write=True):
    # All determinant-one ordered spectra, collapsed only by unordered multiset.
    raw=[]
    for n0 in range(10):
        for n1 in range(10-n0):
            n2=9-n0-n1
            if (n1+2*n2)%3: continue
            raw.append((n0,n1,n2))
    classes={}
    for n in raw:
        key=tuple(sorted(n,reverse=True))
        classes.setdefault(key,[]).append(n)
    assert set(classes)=={
      (9,0,0),(7,1,1),(6,3,0),(5,2,2),(4,4,1),(3,3,3)
    }

    census=[]
    for n in sorted(classes,reverse=True):
        neutral=sum(x*(x-1) for x in n)
        charged=n[0]*n[1]+n[1]*n[2]+n[2]*n[0]
        cent=sum(x*x for x in n)-1
        census.append({
          'multiplicities':list(n),
          'neutral_roots':neutral,
          'charged_roots_each':charged,
          'centralizer_dimension':cent,
          'contains_SU5':max(n)>=5,
          'ordered_det1_representatives':[list(x) for x in classes[n]],
        })

    selected=[x for x in census if x['contains_SU5'] and x['charged_roots_each']==24]
    assert len(selected)==1 and selected[0]['multiplicities']==[5,2,2]
    assert selected[0]['neutral_roots']==24 and selected[0]['centralizer_dimension']==32

    # Known two-qutrit Clifford representatives on (x1,x2,p1,p2).
    S1=((1,0,0,0),(0,1,0,0),(1,0,1,0),(0,0,0,1))
    CZ=((1,0,0,0),(0,1,0,0),(0,1,1,0),(1,0,0,1))
    ps=point_profile(S1); pcz=point_profile(CZ)
    assert ps=={1:13,3:9}
    assert pcz=={1:4,3:12}
    assert adjoint_grades((6,3,0))==[44,18,18]
    assert adjoint_grades((5,2,2))==[32,24,24]

    parent=json.loads((ROOT/'data/w33_flagship_wilson_line_cz_bridge.json').read_text())
    assert parent['status']=='PASS'
    assert parent['heterotic']['W3_root_grades']=={'0':24,'1':24,'2':24}
    assert parent['heterotic']['neutral_semisimple_type']=='A4 + A1 + A1'
    assert parent['heterotic']['flagship_SU5_inside_A4_component'] is True

    checks={
      'six_unordered_order3_SU9_spectral_types':len(classes)==6,
      'flagship_conditions_uniquely_select_5_2_2':len(selected)==1,
      '5_2_2_has_24_24_24_root_split':selected[0]['neutral_roots']==selected[0]['charged_roots_each']==24,
      '5_2_2_centralizer_dim_32':selected[0]['centralizer_dimension']==32,
      'local_S1_spectrum_6_3_has_44_18_18_adjoint':adjoint_grades((6,3,0))==[44,18,18],
      'local_S1_W33_profile_1pow13_3pow9':ps=={1:13,3:9},
      'entangling_CZ_W33_profile_1pow4_3pow12':pcz=={1:4,3:12},
      'parent_flagship_is_A4_A1_A1_with_SU5':True,
    }
    assert all(checks.values())
    out={
      'schema':'w33.su9_order3_flagship_entangling_selection.v1',
      'status':'PASS',
      'headline':'Among the six unordered determinant-one order-three spectral types in SU(9), the exact flagship conditions (neutral SU5 present and 24 roots in each nonzero Z3 grade) uniquely select 5+2+2. This is qutrit CZ_3. The neighboring local Clifford S_1 x I has 6+3 spectrum, sl9 grading 44+18+18 and W33 profile 1^13 3^9; the flagship/CZ branch has 32+24+24 and 1^4 3^12, so the viable Wilson line is the entangling branch.',
      'census':census,
      'selection':{
        'conditions':['neutral centralizer contains SU5','each nonzero root grade has size 24'],
        'unique_type':[5,2,2],
        'neutral_roots':24,
        'charged_each':24,
        'centralizer':'S(U(5) x U(2) x U(2))',
        'centralizer_dimension':32,
      },
      'clifford_comparison':{
        'local_phase':{
          'gate':'S_1 tensor I',
          'fundamental_spectrum':[6,3,0],
          'sl9_grading':[44,18,18],
          'W33_point_cycle_profile':{'1':13,'3':9},
          'reading':'rank-one/local transvection branch',
        },
        'entangler':{
          'gate':'CZ_3',
          'fundamental_spectrum':[5,2,2],
          'sl9_grading':[32,24,24],
          'W33_point_cycle_profile':{'1':4,'3':12},
          'reading':'rank-two entangling Lagrangian-unipotent branch',
        }},
      'parent':'data/w33_flagship_wilson_line_cz_bridge.json',
      'scope':'Spectral/root-centralizer classification. Selection uses exact flagship root data; it is not a claim that every heterotic Wilson line with an SU5 factor must be CZ.',
      'checks':checks,
    }
    if write: OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))
    return out
if __name__=='__main__': main(True)
