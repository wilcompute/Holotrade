"""Unbroken U(1)s after singlet condensation, and whether u^c d^c d^c is charged under one.

Hypercharge is solved for exactly as a general direction y (A y = b over the labelled SM
fields), not assumed to be a basis vector.  Condensable singlets are the left-chiral fields
trivial under SU(3) x SU(2) with y.Q = 0.  The surviving U(1)s are the null space of their
charge matrix; udd is forbidden to all orders iff every (u^c, d^c, d^c) charge sum has a
nonzero pairing with that null space.
"""
import glob, json, os, re
from fractions import Fraction as F
from sympy import Matrix, Rational

SMY = {'q': Rational(1,6), 'bu': Rational(-2,3), 'bd': Rational(1,3),
       'l': Rational(-1,2), 'bl': Rational(1,2), 'be': Rational(1)}


def solve_exact(A, b):
    """Exact particular solution of A x = b, or None if inconsistent (free vars set to 0)."""
    n = A.cols
    M = A.row_join(b)
    R, piv = M.rref()
    if n in piv: return None            # pivot in the augmented column => inconsistent
    x = [Rational(0)] * n
    for r, c in enumerate(piv):
        x[c] = R[r, n]
    return Matrix(x)

def parse(fn):
    fields = []; nu1 = None
    for ln in open(fn):
        if ln.startswith('NU1'): nu1 = int(ln.split()[1]); continue
        if not ln.startswith('S '): continue
        p = ln.split()
        dims = p[4][4:].split(',')
        q = []
        for x in ln.rsplit('q=', 1)[1].strip().split(','):
            f = F(float(x)).limit_denominator(10**6)
            assert 18 % f.denominator == 0, (fn, x)
            q.append(Rational(f.numerator, f.denominator))
        fields.append(dict(lab=p[1], base=p[1].rsplit('_',1)[0], susy=int(p[3][5:]),
                           dim=[int(re.match(r'-?\d+', d).group()) for d in dims],
                           adj=[bool(re.search(r'[a-z]', d)) for d in dims], q=q))
    return nu1, fields

def analyse(fn):
    nu1, fields = parse(fn)
    left = [f for f in fields if f['susy'] == 2]
    lab = [f for f in left if f['base'] in SMY]
    if not lab: return {'error': 'no labelled SM fields'}
    A = Matrix([f['q'] for f in lab]); b = Matrix([SMY[f['base']] for f in lab])
    y = solve_exact(A, b)
    if y is None: return {'error': 'hypercharge not a linear combination of the dumped U(1)s'}
    yv = [y[i] for i in range(nu1)]
    def dot(u, v): return sum(u[i]*v[i] for i in range(nu1))
    def smneutral(f): return abs(f['dim'][0])==1 and abs(f['dim'][1])==1 and not f['adj'][0] and not f['adj'][1]
    def hidneutral(f): return all(abs(d)==1 for d in f['dim']) and not any(f['adj'])
    out = {'nu1': nu1}
    bu = [f for f in left if f['base']=='bu']; bd = [f for f in left if f['base']=='bd']
    out['n_bu'] = len(bu); out['n_bd'] = len(bd)
    for tag, pred in (('strict', hidneutral), ('loose', smneutral)):
        sing = [f['q'] for f in left if pred(f) and dot(yv, f['q']) == 0]
        out['n_' + tag] = len(sing)
        ns = Matrix(sing).nullspace() if sing else Matrix.eye(nu1).columnspace()
        out['dim_' + tag] = len(ns)
        ey = Matrix(yv)
        NS = Matrix.hstack(*ns) if ns else Matrix.zeros(nu1, 0)
        out['Y_survives_' + tag] = bool(ns) and NS.rank() == Matrix.hstack(NS, ey).rank()
        ntot = 0; nfree = 0
        for a in bu:
            for j in range(len(bd)):
                for k in range(j, len(bd)):
                    ntot += 1
                    v = Matrix([a['q'][t] + bd[j]['q'][t] + bd[k]['q'][t] for t in range(nu1)])
                    if not any((Matrix(n).T * v)[0] != 0 for n in ns): nfree += 1
        out['udd_tot_'+tag] = ntot; out['udd_uncharged_'+tag] = nfree
        out['udd_forbidden_'+tag] = (ntot > 0 and nfree == 0)
    return out

res = {}
for fn in sorted(glob.glob('sp2/*.sp')):
    m = os.path.basename(fn)[:-3]
    try: res[m] = analyse(fn)
    except Exception as e: res[m] = {'error': repr(e)[:120]}
    print('.', end='', flush=True)
print()
json.dump(res, open('unbroken_z6ii.json','w'), indent=1)
bad = [m for m,r in res.items() if 'error' in r]
print('models %d, failed %d' % (len(res), len(bad)))
for m in bad[:6]: print('  ', m, res[m]['error'][:70])
