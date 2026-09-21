"""Does B-L exist as a gauge direction, and what does the Z2 matter parity do to each operator?

Literature condition (arXiv:0708.2691 sec 1): matter parity is the discrete Z2 subgroup of
U(1)_{B-L}; singlets with 3(B-L) = 0 mod 2 may condense.  3(B-L) odd = matter-odd = forbidden.
B-L is solved on the unambiguous fields (q, u^c, d^c, e^c); the DOUBLET values are read off.
"""
import glob, json, os
from collections import Counter
from sympy import Matrix, Rational
exec(open('unbroken2.py').read().split("res = {}")[0])

BL = {'q': Rational(1,3), 'bu': Rational(-1,3), 'bd': Rational(-1,3), 'be': Rational(1)}
par = lambda v: 'frac' if v.q != 1 else ('even' if v % 2 == 0 else 'odd')

def scan(fn):
    nu1, fields = parse(fn)
    left = [f for f in fields if f['susy'] == 2]
    lab = [f for f in left if f['base'] in SMY]
    if not lab: return None
    y = solve_exact(Matrix([f['q'] for f in lab]), Matrix([SMY[f['base']] for f in lab]))
    if y is None: return None
    bl_lab = [f for f in left if f['base'] in BL]
    x = solve_exact(Matrix([f['q'] for f in bl_lab]), Matrix([BL[f['base']] for f in bl_lab]))
    if x is None: return None
    xv = [x[i] for i in range(nu1)]
    V = lambda f: sum(xv[i]*f['q'][i] for i in range(nu1))
    g = lambda t: [f for f in left if f['base'] == t]
    L  = [f for f in g('l')  if V(f) == -1]
    H  = [f for f in g('bl') if V(f) == 0] + [f for f in g('l') if V(f) == 0]
    out = {'n_L': len(L), 'n_H': len(H),
           'l_vals': sorted(set(str(V(f)) for f in g('l'))),
           'bl_vals': sorted(set(str(V(f)) for f in g('bl'))),
           'nullspace_dim': len(Matrix([f['q'] for f in bl_lab]).nullspace())}
    if not L or not H: return {**out, 'viable': False}
    op = lambda fs: par(3 * sum(V(f) for f in fs))
    q, bu, bd, be = g('q'), g('bu'), g('bd'), g('be')
    r = {}
    r['udd']   = Counter(op([a,b,c]) for a in bu for i,b in enumerate(bd) for c in bd[i:])
    r['qLdc']  = Counter(op([a,b,c]) for a in q for b in L for c in bd)
    r['LLec']  = Counter(op([a,b,c]) for i,a in enumerate(L) for b in L[i:] for c in be)
    r['upYuk'] = Counter(op([a,b,c]) for a in q for b in bu for c in H)
    r['dnYuk'] = Counter(op([a,b,c]) for a in q for b in bd for c in H)
    r['lpYuk'] = Counter(op([a,b,c]) for a in L for b in H for c in be)
    r['mu']    = Counter(op([a,b]) for a in H for b in H)
    out['ops'] = {k: dict(v) for k, v in r.items()}
    out['viable'] = (all(r[k].get('even',0)==0 and r[k].get('frac',0)==0 for k in ('udd','qLdc','LLec'))
                     and all(r[k].get('even',0)>0 for k in ('upYuk','dnYuk','lpYuk','mu')))
    return out

rows = {}
for tag, pat in (('Z6-I','sp1/*.sp'), ('Z6-II','sp2/*.sp')):
    for fn in sorted(glob.glob(pat)):
        r = scan(fn)
        if r: rows[f'{tag}|{os.path.basename(fn)[:-3]}'] = r
json.dump(rows, open('matterparity.json','w'), indent=1)
z6i = sum(1 for k in rows if k.startswith('Z6-I|'))
print('B-L exists as a gauge direction: %d of 215   (Z6-I %d, Z6-II %d)' % (len(rows), z6i, len(rows)-z6i))
print('  viable matter-parity structure: %d' % sum(1 for v in rows.values() if v.get('viable')))
print('  exactly one Higgs pair        : %d' % sum(1 for v in rows.values() if v['n_H']==1))
agg = Counter()
for v in rows.values():
    for o,d in v.get('ops',{}).items():
        for p,n in d.items(): agg[(o,p)] += n
print()
print('%-8s %-9s %-9s %-9s' % ('operator','even','odd','frac'))
for o in ('udd','qLdc','LLec','upYuk','dnYuk','lpYuk','mu'):
    print('%-8s %-9d %-9d %-9d' % (o, agg[(o,'even')], agg[(o,'odd')], agg[(o,'frac')]))
print()
print('l values  :', dict(Counter(tuple(v['l_vals']) for v in rows.values())))
print('bl values :', dict(Counter(tuple(v['bl_vals']) for v in rows.values())))
print('nullspace :', dict(Counter(v['nullspace_dim'] for v in rows.values())))
