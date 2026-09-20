"""Toy-model scope regressions, not counterexamples to the flagship's charge certificates.
Gordan controls the U(1) charge cone. It does not supply a superpotential or
solve all of its derivatives. Prior: bd6c60e and babfd48, whose scope text already
mentions selection rules and critical points; this makes those limits executable.
"""
from pathlib import Path
import json
import sympy as s

def audit():
    x,y,z=s.symbols('x y z',real=True)
    q=s.Matrix([[1,-1]]);v=s.Matrix([1,1]);assert q*v==s.zeros(1,1)
    # Continuous R symmetry with R(x)=R(y)=0, R(W)=2 allows no polynomial W(x,y).
    assert sum([0,0])!=2
    # Nonempty invariant W can have a nonzero D-flat critical point by cancellation.
    W=(x*y-1)**2;point={x:1,y:1}
    deriv=[s.diff(W,a) for a in (x,y)]
    assert all(d.subs(point)==0 for d in deriv) and (x*x-y*y).subs(point)==0
    individual=s.Add.make_args(s.expand(W))
    assert any(s.diff(t,x).subs(point)!=0 for t in individual)
    # W restricted to a positively charged support is empty, but an OUTSIDE F need not vanish.
    W2=z*x*x;assert W2.subs(z,0)==0 and s.diff(W2,z).subs({x:1,z:0})==1
    assert -2+2*1==0
    return {'status':'PASS','Dflat_with_selection_rule_empty_W':{'charges':[1,-1],'squared_vevs':[1,1],'R_charges':[0,0],'superpotential_R_charge':2},
            'nonempty_W_with_D_and_F_flat_point':{'W':str(W),'point':{'x':1,'y':1},'F':[str(a) for a in deriv],'termwise_F_nonzero_but_sum_zero':True},
            'empty_restriction_not_full_F_flat':{'charges':{'x':1,'z':-2},'W':'z*x^2','support':['x'],'outside_Fz_at_x1_z0':1},
            'scope':'Toy algebraic regressions only, no claim these superpotentials or R charges occur in any scanned orbifold. Gauge-charge neutrality is necessary, not sufficient, for nonabelian/string invariants. Termwise vanishing is sufficient but not necessary for F flatness.',
            'prior':['d_flatness_and_an_empty_superpotential_are_gordan_alternatives.py','f_flatness_and_d_flatness_are_in_direct_conflict.py','https://arxiv.org/abs/1107.2137']}
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();r=audit()
    if a.write:Path(__file__).with_suffix('.json').write_text(json.dumps(r,indent=2)+'\n')
    print(r['status'])
