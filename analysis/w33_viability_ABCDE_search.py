"""Same search, instrumented: which of A-E binds, with the udd requirement as a control."""
import glob, os
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
    dot = lambda u, v: sum(u[i]*v[i] for i in range(nu1))
    hid = lambda f: all(abs(d) == 1 for d in f['dim']) and not any(f['adj'])
    sing = [f['q'] for f in left if hid(f) and dot(yv, f['q']) == 0]
    ns = Matrix(sing).nullspace() if sing else Matrix.eye(nu1).columnspace()
    g = lambda b: [f for f in left if f['base'] == b]
    qs, bus, bds, be = g('q'), g('bu'), g('bd'), g('be')
    dbl = g('l') + g('bl')
    best = Counter()
    for n in ns:
        al = [n[i] for i in range(nu1)]
        V = lambda f: dot(al, f['q'])
        aq = set(V(f) for f in qs)
        if len(aq) != 1 or aq == {0}:
            best['alpha_q_not_uniform_or_zero'] += 1; continue
        s = aq.pop(); v = lambda f: V(f) / s
        D = set(v(f) for f in dbl); U = set(v(f) for f in bus)
        Dc = set(v(f) for f in bds); E = set(v(f) for f in be)
        uddF = all(v(a) + v(bds[j]) + v(bds[k]) != 0
                   for a in bus for j in range(len(bds)) for k in range(j, len(bds)))
        okA = any(-(1 + b) in D for b in U)
        okB = any(-(1 + c) in D for c in Dc)
        okE = any(-(1 + b) in D and -(1 + c) in D and -(1 + b) == (1 + c)
                  for b in U for c in Dc)
        okC = any(L + (-(1 + c)) + ec == 0 for c in Dc if -(1 + c) in D
                  for L in D for ec in E)
        best['A_up_Yukawa'] += okA; best['B_down_Yukawa'] += okB
        best['C_lepton_Yukawa'] += okC; best['E_mu_term'] += okE
        best['D_udd_forbidden'] += uddF
        best['ABCE_control_no_udd_req'] += (okA and okB and okC and okE)
        best['ABCDE_all'] += (okA and okB and okC and okE and uddF)
        best['generators'] += 1
    return best

tot = Counter(); nmod = 0
permodel = Counter()
for pat in ('sp1/*.sp', 'sp2/*.sp'):
    for fn in sorted(glob.glob(pat)):
        b = scan(fn)
        if b is None: continue
        nmod += 1; tot += b
        for k in ('A_up_Yukawa','B_down_Yukawa','C_lepton_Yukawa','E_mu_term',
                  'D_udd_forbidden','ABCE_control_no_udd_req','ABCDE_all'):
            if b[k]: permodel[k] += 1
print('models %d, generators examined %d' % (nmod, tot['generators']))
print()
print('  per-MODEL counts (at least one surviving generator satisfies it):')
for k in ('A_up_Yukawa','B_down_Yukawa','C_lepton_Yukawa','E_mu_term',
          'D_udd_forbidden','ABCE_control_no_udd_req','ABCDE_all'):
    print('    %-28s %3d / %d' % (k, permodel[k], nmod))
