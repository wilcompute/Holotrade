"""D-flatness, recomputed with the anomalous direction verified per model.

Control: 3e655d0 established the anomalous generator is the FIRST U(1), because the
LEFT-CHIRAL trace Tr Q_0 equals the orbifolder's own D0_FI_term.  That identity is
re-checked here per model before the LP is trusted.

Condition: D_a = sum q_a |v|^2 = 0 for a != 0, and sum q_0 |v|^2 = -xi < 0.
"""
import glob, json, os
import numpy as np
from scipy.optimize import linprog
from sympy import Matrix, Rational
exec(open('unbroken2.py').read().split("res = {}")[0])

def feas(Q):
    if not len(Q): return False
    Q = np.array(Q, float); n = Q.shape[0]
    Aeq = [Q[:, a] for a in range(1, Q.shape[1])] + [np.ones(n)]
    beq = [0.0] * (Q.shape[1] - 1) + [1.0]
    r = linprog(c=Q[:, 0], A_eq=np.array(Aeq), b_eq=np.array(beq),
                bounds=[(0, None)] * n, method='highs')
    return bool(r.success and r.fun < -1e-9)

def scan(fn):
    nu1, fields = parse(fn)
    anom = fi = None
    for ln in open(fn):
        if ln.startswith('ANOM'):
            p = ln.split(); anom = int(p[1]); fi = float(p[3]); break
    left = [f for f in fields if f['susy'] == 2]
    lab = [f for f in left if f['base'] in SMY]
    if not lab: return None
    y = solve_exact(Matrix([f['q'] for f in lab]), Matrix([SMY[f['base']] for f in lab]))
    if y is None: return None
    yv = [y[i] for i in range(nu1)]
    dot = lambda u, v: sum(u[i]*v[i] for i in range(nu1))
    # CONTROL: left-chiral trace on direction 0 vs the orbifolder's D0_FI_term
    mult = lambda f: abs(np.prod([abs(d) for d in f['dim']]))
    tr0 = sum(mult(f) * f['q'][0] for f in left)
    hid = lambda f: all(abs(d) == 1 for d in f['dim']) and not any(f['adj'])
    sings = [f for f in left if hid(f) and dot(yv, f['q']) == 0]
    Q = [[float(c) for c in f['q']] for f in sings]
    return {'anom': anom, 'fi': fi, 'trace0': float(tr0),
            'trace_matches_fi': abs(float(tr0) - fi) < 0.05 if fi is not None else None,
            'singlets': len(sings), 'dflat': feas(Q)}

rows = {}
for tag, pat in (('Z6-I','sp1/*.sp'), ('Z6-II','sp2/*.sp')):
    for fn in sorted(glob.glob(pat)):
        r = scan(fn)
        if r: rows[f'{tag}|{os.path.basename(fn)[:-3]}'] = r
json.dump(rows, open('dflat2.json','w'), indent=1)
for tag in ('Z6-I','Z6-II'):
    sub = {k: v for k, v in rows.items() if k.startswith(tag + '|')}
    an = [v for v in sub.values() if v['anom'] == 1]
    print('%-6s %3d models | anomalous %3d | trace0 == D0_FI_term in %3d of %3d | D-flat %3d'
          % (tag, len(sub), len(an), sum(1 for v in an if v['trace_matches_fi']), len(an),
             sum(1 for v in sub.values() if v['dflat'])))
