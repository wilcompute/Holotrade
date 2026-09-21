"""Search the B-L freedom for a choice whose EVEN singlets admit a D-flat direction.

B-L is not unique: the solution set is x0 + span(N).  Adding n in N leaves every SM field
untouched (N annihilates the SM constraint rows) but shifts the singlet parities.  The paper
searches exactly this freedom.  Sample it and test D-flatness on the even-singlet subset.
Control: D-flatness with ALL singlets, which the verified machinery puts at 23 Z6-I / 105 Z6-II.
"""
import glob, itertools, json, os, random
import numpy as np
from scipy.optimize import linprog
from sympy import Matrix, Rational
exec(open('unbroken2.py').read().split("res = {}")[0])
BL = {'q': Rational(1,3), 'bu': Rational(-1,3), 'bd': Rational(-1,3), 'be': Rational(1)}
random.seed(11)

def feas(Q):
    if not len(Q): return False
    Q = np.array(Q, float); n = Q.shape[0]
    Aeq = [Q[:, a] for a in range(1, Q.shape[1])] + [np.ones(n)]
    beq = [0.0] * (Q.shape[1] - 1) + [1.0]
    r = linprog(c=Q[:, 0], A_eq=np.array(Aeq), b_eq=np.array(beq),
                bounds=[(0, None)] * n, method='highs')
    return bool(r.success and r.fun < -1e-9)

GRID = [Rational(k, 2) for k in range(-4, 5)]

def scan(fn, nsample=60):
    nu1, fields = parse(fn)
    left = [f for f in fields if f['susy'] == 2]
    lab = [f for f in left if f['base'] in SMY]
    if not lab: return None
    y = solve_exact(Matrix([f['q'] for f in lab]), Matrix([SMY[f['base']] for f in lab]))
    if y is None: return None
    yv = [y[i] for i in range(nu1)]
    dot = lambda u, v: sum(u[i]*v[i] for i in range(nu1))
    A = Matrix([f['q'] for f in left if f['base'] in BL])
    b = Matrix([BL[f['base']] for f in left if f['base'] in BL])
    x0 = solve_exact(A, b)
    if x0 is None: return None
    N = A.nullspace()
    hid = lambda f: all(abs(d) == 1 for d in f['dim']) and not any(f['adj'])
    sings = [f for f in left if hid(f) and dot(yv, f['q']) == 0]
    allQ = [[float(c) for c in f['q']] for f in sings]
    best = {'nullspace': len(N), 'singlets': len(sings),
            'dflat_all': feas(allQ), 'best_even': 0, 'dflat_even': False, 'samples': 0}
    seen = set()
    cands = [tuple([Rational(0)] * len(N))]
    if N:
        for _ in range(nsample):
            cands.append(tuple(random.choice(GRID) for _ in N))
    for t in cands:
        if t in seen: continue
        seen.add(t); best['samples'] += 1
        xv = [x0[i] + sum(t[j] * N[j][i] for j in range(len(N))) for i in range(nu1)]
        ev = []
        for f in sings:
            v = 3 * dot(xv, f['q'])
            if v.q == 1 and v % 2 == 0: ev.append(f)
        if len(ev) > best['best_even']: best['best_even'] = len(ev)
        if ev and feas([[float(c) for c in f['q']] for f in ev]):
            best['dflat_even'] = True; best['winning_t'] = [str(v) for v in t]
            best['even_at_win'] = len(ev); break
    return best

rows = {}
for tag, pat in (('Z6-I','sp1/*.sp'), ('Z6-II','sp2/*.sp')):
    for fn in sorted(glob.glob(pat)):
        r = scan(fn)
        if r: rows[f'{tag}|{os.path.basename(fn)[:-3]}'] = r
json.dump(rows, open('freedom.json','w'), indent=1)
print('models with a B-L direction: %d' % len(rows))
print('  D-flat with ALL singlets (control): %d' % sum(1 for v in rows.values() if v['dflat_all']))
print('  D-flat on EVEN singlets, any sampled B-L choice: %d'
      % sum(1 for v in rows.values() if v['dflat_even']))
print('  models where some choice gives >0 even singlets: %d'
      % sum(1 for v in rows.values() if v['best_even'] > 0))
hits = [k for k,v in rows.items() if v['dflat_even']]
for k in hits[:10]:
    v = rows[k]
    print('   HIT %-34s even %d of %d, t = %s' % (k[:34], v.get('even_at_win'), v['singlets'], v.get('winning_t')))
