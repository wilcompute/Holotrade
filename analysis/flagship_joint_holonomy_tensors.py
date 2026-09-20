"""Exact global-holonomy projectors on the prior local nine-weight carrier.
These are endomorphism invariants of the joint holonomy centralizer, not computed
world-sheet amplitudes or intertwiners for every partner representation.
"""
from fractions import Fraction as F
from pathlib import Path
from collections import defaultdict
import json
import sympy as s
from local_nine_spurion_algebra import audit as local_audit
from w33_flagship_orbifolder_model import V,W3

def audit():
    weights=local_audit()['weights_scale_6']
    def phases(a):
        raw=[sum(F(x,6)*y for x,y in zip(w,a)) for w in weights]
        return [(x-raw[0])%1 for x in raw]
    w=phases(W3);h=phases(tuple(3*x for x in V))
    assert all(x in (0,F(1,3),F(2,3)) for x in w) and all(x in (0,F(1,2)) for x in h)
    # Cyclotomic arithmetic reduced modulo z^2+z+1; the parity matrix squares to I.
    z=s.Symbol('z');reduce=lambda p:s.rem(s.expand(p),z*z+z+1,z)
    wd=[z**int(3*x) for x in w];hd=[(-1)**int(2*x) for x in h]
    P0=[reduce((1+x+x*x)/3) for x in wd]
    Pt=[reduce(x*(1+y)/2) for x,y in zip(P0,hd)]
    Pd=[reduce(x*(1-y)/2) for x,y in zip(P0,hd)]
    assert Pt==[1]*3+[0]*6 and Pd==[0]*3+[1]*2+[0]*4
    groups=defaultdict(list)
    for i,key in enumerate(zip(w,h)):groups[key].append(i)
    assert sorted(map(len,groups.values()))==[1,1,1,1,2,3]
    # Every matrix unit inside a phase block commutes with both holonomies.
    units=[(i,j) for group in groups.values() for i in group for j in group]
    assert all(w[i]==w[j] and h[i]==h[j] for i,j in units)
    # A local A8 root generator joining triplet to doublet fails to commute with Pt.
    E=s.zeros(9);E[0,3]=1;P=s.diag(*Pt);assert P*E-E*P==E
    return {'status':'PASS','relative_W3_phases':[str(x) for x in w],'relative_3V_phases':[str(x) for x in h],
            'block_indices':list(groups.values()),'centralizer_dimension':len(units),'traceless_Lie_centralizer_dimension':len(units)-1,
            'triplet_projector':Pt,'doublet_projector':Pd,
            'formulas':{'P0':'(I+W+W^2)/3','P_triplet':'P0 (I+H)/2','P_doublet':'P0 (I-H)/2'},
            'joint_invariant_mass_ansatz':'m_T P_triplet + m_D P_doublet; m_T and m_D remain unspecified coefficients',
            'W3_alone_separates_triplet_doublet':False,'joint_holonomies_separate':True,
            'local_A8_invariant':False,'centralizer':'M3 + M2 + C^4',
            'scope':'Projective common phases removed. Distinct from prior C I9 + M4 spurion algebra despite both dimensions being 17. Global symmetry permits the split; this does not establish an allowed string coupling, its coefficient, or a vacuum.',
            'prior':['the_standard_model_is_the_joint_stabiliser_and_mu_is_universal.py','local_nine_spurion_algebra.py','the_missing_partner_is_the_untwisted_plane_split.py','the_spurion_obstruction_and_the_plane_split_are_the_two_halves.py']}
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();r=audit()
    if a.write:Path(__file__).with_suffix('.json').write_text(json.dumps(r,indent=2,default=int)+'\n')
    print(r['centralizer'],r['formulas'])
