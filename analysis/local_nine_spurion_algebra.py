"""Exact flagship replay and conditional spurion algebra; not a string amplitude calculation."""
from fractions import Fraction
from itertools import combinations, product
from pathlib import Path
import json
import argparse
import numpy as np
from retraction_the_local_gut_multiplet_is_complete_so_the_coefficients_are_locked import FLAGSHIP_POINT


def scaled(s):
    q = [6 * Fraction(x) for x in s.replace('|', ',').split(',')]
    assert all(x.denominator == 1 for x in q)
    return tuple(map(int, q))


def audit():
    roots = []
    for i, j in combinations(range(8), 2):
        for a, b in product((-6, 6), repeat=2):
            r = [0]*8; r[i] = a; r[j] = b; roots.append(tuple(r))
    roots += [s for s in product((-3, 3), repeat=8) if s.count(-3) % 2 == 0]
    roots = [r+(0,)*8 for r in roots] + [(0,)*8+r for r in roots]
    v = scaled(FLAGSHIP_POINT['V_loc'])
    dot = lambda a,b: sum(x*y for x,y in zip(a,b))
    local = [r for r in roots if dot(r,v) % 36 == 0]
    displayed = [scaled(w) for name in ('bd_2','l_1') for w in FLAGSHIP_POINT['weights'][name]]
    orbit = {displayed[0]}; todo = list(orbit)
    while todo:
        w = todo.pop()
        for r in local:
            d = dot(w,r); assert d % 36 == 0
            z = tuple(a-(d//36)*b for a,b in zip(w,r))
            if z not in orbit: orbit.add(z); todo.append(z)
    assert set(displayed) <= orbit and len(orbit) == 9 and len(local) == 156
    extra = sorted(orbit-set(displayed))
    weights = displayed + extra
    diff = lambda a,b: tuple(x-y for x,y in zip(a,b))
    differences = {diff(a,b) for a in orbit for b in orbit if a != b}
    assert len(differences) == 72 and differences <= set(local)
    visible = [diff(displayed[i],displayed[j]) for i,j in ((0,1),(1,2),(3,4))]
    assert all(dot(w,r) == 0 for w in extra for r in visible)
    cross = sum(diff(a,b) in local for a in displayed[:3] for b in displayed[3:])
    assert cross == 6
    def unit(i,j):
        m = np.zeros((9,9), dtype=np.int64); m[i,j] = 1; return m
    identity = np.eye(9,dtype=np.int64)
    basis = [identity] + [unit(i,j) for i in range(5,9) for j in range(5,9)]
    def in_algebra(m):
        scalar = m[0,0]
        n = m-scalar*identity
        return not np.any(n[:5,:]) and not np.any(n[:,:5])
    assert all(in_algebra(a@b) for a in basis for b in basis)
    # Matrix units force the commutant to M5 plus scalar I4 exactly.
    commutant = [unit(i,j) for i in range(5) for j in range(5)]
    commutant += [np.diag([0]*5+[1]*4)]
    assert all(np.array_equal(a@b,b@a) for a in basis for b in commutant)
    target = np.diag([4]*3+[0]*2+[-3]*4)
    assert np.trace(target) == 0 and not in_algebra(target)
    for i,j in ((0,1),(1,2),(3,4)):
        e = unit(i,j); assert np.array_equal(e@target,target@e)
    return {'status':'PASS','scope':'One flagship; conditional fundamental-antifundamental spurion library, no physical VEV or amplitude claim',
            'local_root_count':len(local),'local_weyl_orbit_size':len(orbit),
            'A8_root_differences':len(differences),'cross_roots':cross,
            'weights_scale_6':weights,'extra_weights_visible_A2_A1_neutral':True,
            'spurion_algebra':'C I9 + M4(C)','algebra_dimension':17,
            'commutant':'M5(C) + C I4','commutant_dimension':26,
            'products_checked':len(basis)**2,'target_diagonal':target.diagonal().tolist(),
            'target_in_spurion_algebra':False,
            'prior_source':'retraction_the_local_gut_multiplet_is_complete_so_the_coefficients_are_locked.py'}

if __name__ == '__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--write',action='store_true'); args=parser.parse_args()
    result=audit()
    if args.write: Path(__file__).with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
