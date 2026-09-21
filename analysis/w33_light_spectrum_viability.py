"""Viability on the LIGHT spectrum.

alpha is exactly unbroken, so a light operator with alpha != 0 is forbidden however the
heavy vector-like exotics are integrated out.  The physically relevant test is therefore
on the light d^c only.  Light content per alpha-value x: n_bd(x) - n_d(-x) (a vector-like
pair bd(x), d(-x) gets mass and decouples).  Colour/weak slots are read off the quark
doublet PER MODEL, never hardcoded.
"""
import glob, json, os
from collections import Counter
from sympy import Matrix, Rational
exec(open('unbroken2.py').read().split("res = {}")[0])

def scan(fn):
    nu1, fields = parse(fn)
    left = [f for f in fields if f['susy'] == 2]
    lab = [f for f in left if f['base'] in SMY]
    if not lab: return None
    y = solve_exact(Matrix([f['q'] for f in lab]), Matrix([SMY[f['base']] for f in lab]))
    if y is None: return None
    yv = [y[i] for i in range(nu1)]
    dot = lambda u, v: sum(u[i] * v[i] for i in range(nu1))
    hid = lambda f: all(abs(d) == 1 for d in f['dim']) and not any(f['adj'])
    sing = [f['q'] for f in left if hid(f) and dot(yv, f['q']) == 0]
    ns = Matrix(sing).nullspace() if sing else Matrix.eye(nu1).columnspace()
    g = lambda b: [f for f in left if f['base'] == b]
    qs, bus, bds, ds, be = g('q'), g('bu'), g('bd'), g('d'), g('be')
    dbl = g('l') + g('bl')
    out = []
    for n in ns:
        al = [n[i] for i in range(nu1)]
        V = lambda f: dot(al, f['q'])
        aq = set(V(f) for f in qs)
        if len(aq) != 1 or aq == {0}: continue
        s = aq.pop(); v = lambda f: V(f) / s
        # light d^c charges: net excess of bd(x) over its conjugate d(-x)
        nb, nd = Counter(v(f) for f in bds), Counter(v(f) for f in ds)
        lightd = sorted(x for x in nb if nb[x] - nd.get(-x, 0) > 0)
        nbu, ndu = Counter(v(f) for f in bus), Counter()
        lightu = sorted(nbu)
        D = sorted(set(v(f) for f in dbl)); E = sorted(set(v(f) for f in be))
        if not lightd or not lightu: continue
        udd_light = all(b + c1 + c2 != 0 for b in lightu
                        for i, c1 in enumerate(lightd) for c2 in lightd[i:])
        udd_all = all(v(a) + v(bds[i]) + v(bds[j]) != 0
                      for a in bus for i in range(len(bds)) for j in range(i, len(bds)))
        hits = []
        for b in lightu:
            hu = -(1 + b)
            if hu not in D: continue
            for c in lightd:
                hd = -(1 + c)
                if hd not in D or hu + hd != 0: continue
                for L in D:
                    for ec in E:
                        if L + hd + ec == 0:
                            hits.append((str(b), str(c), str(hu), str(hd), str(L), str(ec)))
        out.append({'light_dc': [str(x) for x in lightd], 'light_uc': [str(x) for x in lightu],
                    'doublets': [str(x) for x in D], 'udd_light_forbidden': bool(udd_light),
                    'udd_all_forbidden': bool(udd_all), 'yukawa_hits': hits})
    return out

rows = []
for tag, pat in (('Z6-I', 'sp1/*.sp'), ('Z6-II', 'sp2/*.sp')):
    for fn in sorted(glob.glob(pat)):
        m = os.path.basename(fn)[:-3]
        r = scan(fn)
        if not r: continue
        for a in r: rows.append({'track': tag, 'model': m, **a})
json.dump(rows, open('light.json', 'w'), indent=1)
mods = lambda pred: len(set((r['track'], r['model']) for r in rows if pred(r)))
print('generators %d over %d models' % (len(rows), mods(lambda r: True)))
print('  udd forbidden on ALL bd   :', mods(lambda r: r['udd_all_forbidden']))
print('  udd forbidden on LIGHT d^c:', mods(lambda r: r['udd_light_forbidden']))
print('  Yukawas+mu satisfiable    :', mods(lambda r: bool(r['yukawa_hits'])))
print('  BOTH (light udd + Yukawas):', mods(lambda r: r['udd_light_forbidden'] and r['yukawa_hits']))
for r in rows:
    if r['udd_light_forbidden'] and r['yukawa_hits']:
        print('   HIT %-6s %-30s light d^c %s doublets %s' % (r['track'], r['model'][:30],
              r['light_dc'], r['doublets'][:6]))
