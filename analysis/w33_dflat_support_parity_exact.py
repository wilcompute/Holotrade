"""Targeted, non-sampled test on the models that are D-flat at all.

For a model with a D-flat solution, take the LP solution's SUPPORT S, then ask exactly whether
a B-L shift t exists making every s in S matter-even.  Solving 3((x0 + N t).Q_s) = 0 for all
s in S is a sufficient condition and is an exact linear solve, not a search.
"""
import glob, json, os
import numpy as np
from scipy.optimize import linprog
from sympy import Matrix, Rational
exec(open('unbroken2.py').read().split("res = {}")[0])
BL = {'q': Rational(1,3), 'bu': Rational(-1,3), 'bd': Rational(-1,3), 'be': Rational(1)}

def lp(Q):
    Q = np.array(Q, float); n = Q.shape[0]
    Aeq = [Q[:, a] for a in range(1, Q.shape[1])] + [np.ones(n)]
    r = linprog(c=Q[:, 0], A_eq=np.array(Aeq),
                b_eq=np.array([0.0]*(Q.shape[1]-1)+[1.0]),
                bounds=[(0, None)]*n, method='highs')
    if not (r.success and r.fun < -1e-9): return None
    return [i for i, w in enumerate(r.x) if w > 1e-7]

out = {}
for tag, pat in (('Z6-I','sp1/*.sp'), ('Z6-II','sp2/*.sp')):
    for fn in sorted(glob.glob(pat)):
        nu1, fields = parse(fn)
        left = [f for f in fields if f['susy'] == 2]
        lab = [f for f in left if f['base'] in SMY]
        if not lab: continue
        y = solve_exact(Matrix([f['q'] for f in lab]), Matrix([SMY[f['base']] for f in lab]))
        if y is None: continue
        yv = [y[i] for i in range(nu1)]
        dot = lambda u, v: sum(u[i]*v[i] for i in range(nu1))
        A = Matrix([f['q'] for f in left if f['base'] in BL])
        b = Matrix([BL[f['base']] for f in left if f['base'] in BL])
        x0 = solve_exact(A, b)
        if x0 is None: continue
        N = A.nullspace()
        hid = lambda f: all(abs(d) == 1 for d in f['dim']) and not any(f['adj'])
        sings = [f for f in left if hid(f) and dot(yv, f['q']) == 0]
        sup = lp([[float(c) for c in f['q']] for f in sings])
        if sup is None: continue
        S = [sings[i] for i in sup]
        # exact: does t exist with 3((x0 + N t).Q_s) = 0 for every s in S?
        if N:
            M = Matrix([[3 * dot([N[j][i] for i in range(nu1)], f['q']) for j in range(len(N))]
                        for f in S])
            c = Matrix([-3 * dot([x0[i] for i in range(nu1)], f['q']) for f in S])
            t = solve_exact(M, c)
        else:
            t = None
        base_par = []
        for f in S:
            v = 3 * dot([x0[i] for i in range(nu1)], f['q'])
            base_par.append('frac' if v.q != 1 else ('even' if v % 2 == 0 else 'odd'))
        out[f'{tag}|{os.path.basename(fn)[:-3]}'] = {
            'support': len(S), 'nullspace': len(N),
            'exact_shift_exists': t is not None,
            'base_support_all_even': all(p == 'even' for p in base_par),
            'base_parities': {p: base_par.count(p) for p in set(base_par)}}
json.dump(out, open('targeted.json','w'), indent=1)
print('D-flat models examined: %d' % len(out))
print('  an exact B-L shift makes the whole D-flat support matter-even: %d'
      % sum(1 for v in out.values() if v['exact_shift_exists']))
print('  support already all-even with the base choice          : %d'
      % sum(1 for v in out.values() if v['base_support_all_even']))
print()
for k, v in list(out.items())[:12]:
    print('  %-36s support %-3d nullspace %-2d shift %-6s parities %s'
          % (k[:36], v['support'], v['nullspace'], v['exact_shift_exists'], v['base_parities']))
