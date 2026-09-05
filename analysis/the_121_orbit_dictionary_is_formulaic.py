#!/usr/bin/env python3
"""The full PG(4,3) orbit dictionary is formulaic: 40 lines + 45 slow + 36 spreads.

The corrected orthogonal partition is

    P(W), |P(W)|=121 = 40 isotropic + 45 square + 36 nonsquare,

where W=ker(omega) inside Lambda^2(F_3^4), with Pfaffian quadratic form Q.
Earlier work established the three PSp-set identifications, but the 45 and 36
legs used searched equivariant bijections. The 45 leg is now closed by the
explicit eigenspace/Pluecker formula in slow_o5_closed_form.json. This file
closes the other two directly and packages all three as one dictionary.

ISOTROPIC LEG. Every isotropic point y in P(W) is decomposable. Its four-point
projective 2-space is exactly one totally isotropic line of W(3,3). Conversely,
the Pluecker coordinate a wedge b of every W33 line lies in W and has Q=0.
The two 40-sets agree objectwise.

NONSQUARE LEG. For a nonsquare z in P(W), take

    S(z) = { isotropic y : B_Q(z,y)=0 }.

At q=3 this has ten isotropic points. Translating them through the isotropic
Pluecker dictionary gives ten W33 lines. They are pairwise disjoint and cover
all 40 W33 points, hence a spread. The 36 nonsquare points yield 36 distinct
spreads, and an independent exact-cover enumeration finds exactly those same
36 spreads. No orbit-isomorphism search is used.

SQUARE LEG. The separately gated closed formula

    c(g)=p_hat(ker(g-I))-p_hat(ker(g+I))

already maps the 45 executable slow target matrices bijectively onto all square
points and is equivariant on all 80*45 cases.

The result is a single exterior-algebra dictionary for all 121 orthogonal
points. Important correction preserved: the 40 isotropic points are W33 LINES,
not the 40 fast opcode POINTS. The fast point set is the dual 40-set and is not
silently identified with this orbit.
"""
from __future__ import annotations
import itertools,json,sys
from pathlib import Path
from w33_payne_slowpath_core import Q,D,norm,form,tv,mv
ROOT=Path(__file__).resolve().parents[1]
PAIR=((0,1),(0,2),(0,3),(1,2),(1,3),(2,3))

def normn(v):
    v=tuple(int(x)%Q for x in v);i=next(i for i,x in enumerate(v) if x);z=pow(v[i],-1,Q);return tuple(z*x%Q for x in v)
def wedgev(a,b):return tuple((a[i]*b[j]-a[j]*b[i])%Q for i,j in PAIR)
def omega(b):return (b[1]+b[4])%Q
def qf(b):return (b[0]*b[5]-b[1]*b[4]+b[2]*b[3])%Q
def polar(a,b):return (qf(tuple((a[i]+b[i])%Q for i in range(6)))-qf(a)-qf(b))%Q

def wedge_matrix(g):
    M=[[0]*6 for _ in range(6)]
    for c,(i,j) in enumerate(PAIR):
        for r,(k,l) in enumerate(PAIR):M[r][c]=(g[k][i]*g[l][j]-g[l][i]*g[k][j])%Q
    return M
def mv6(M,v):return tuple(sum(M[i][j]*v[j] for j in range(6))%Q for i in range(6))

def w33_points_lines():
    P=sorted({norm(v) for v in itertools.product(range(Q),repeat=D) if any(v)});pi={p:i for i,p in enumerate(P)};L=set()
    for i,j in itertools.combinations(range(40),2):
        if form(P[i],P[j]):continue
        S=frozenset(pi[norm(tuple(a*P[i][k]+b*P[j][k] for k in range(D)))] for a,b in itertools.product(range(Q),repeat=2) if (a,b)!=(0,0))
        if len(S)==4:L.add(S)
    return P,sorted(L,key=lambda s:tuple(sorted(s)))

def line_plucker(P,L):
    a,b=(P[i] for i in sorted(L)[:2]);p=wedgev(a,b);assert omega(p)==0 and qf(p)==0;return normn(p)

def enumerate_spreads(L):
    inc={p:[i for i,l in enumerate(L) if p in l] for p in range(40)};out=[]
    def rec(ch,used):
        if len(used)==40:out.append(frozenset(ch));return
        p=next(i for i in range(40) if i not in used)
        for li in inc[p]:
            if not (set(L[li])&used):rec(ch+[li],used|set(L[li]))
    rec([],set());return sorted(set(out),key=lambda s:tuple(sorted(s)))

def main():
    P,L=w33_points_lines();assert len(P)==len(L)==40
    PW=sorted({normn(v) for v in itertools.product(range(Q),repeat=6) if any(v) and omega(v)==0});iso=[v for v in PW if qf(v)==0];sq=[v for v in PW if qf(v)==1];ns=[v for v in PW if qf(v)==2]
    by_iso={line_plucker(P,l):i for i,l in enumerate(L)}

    # Nonsquare polar sections -> spreads.
    ns_to_spread={};spread_ok=True
    for z in ns:
        ys=[y for y in iso if polar(z,y)==0]
        lis=frozenset(by_iso[y] for y in ys);chosen=[L[i] for i in lis];used=set()
        for l in chosen:
            spread_ok &= not bool(used&set(l));used|=set(l)
        spread_ok &= len(ys)==10 and len(lis)==10 and len(used)==40
        ns_to_spread[z]=lis
    independent=enumerate_spreads(L);indset=set(independent);derived=set(ns_to_spread.values())

    # Square leg imported only as an already-gated explicit formula certificate.
    slow=json.loads((ROOT/'data/slow_o5_closed_form.json').read_text());slowcoords={tuple(v) for v in slow['coordinatesBySlot'].values()}

    # Full generator equivariance for the newly formulaic isotropic and spread legs.
    vecs=[v for v in itertools.product(range(Q),repeat=D) if any(v)];gens=sorted({tv(tuple(v),lam) for v in vecs for lam in (1,2)});assert len(gens)==80
    pi={p:i for i,p in enumerate(P)};line_index={l:i for i,l in enumerate(L)};spread_index={s:i for i,s in enumerate(independent)}
    iso_equiv=True;spread_equiv=True;iso_checks=0;spread_checks=0
    for g in gens:
        W=wedge_matrix(g)
        point_act=[pi[norm(mv(g,p))] for p in P]
        line_act=[]
        for l in L:
            image=frozenset(point_act[i] for i in l);line_act.append(line_index[image])
        for y,li in by_iso.items():
            yy=normn(mv6(W,y));iso_equiv &= by_iso.get(yy)==line_act[li];iso_checks+=1
        for z,S in ns_to_spread.items():
            zz=normn(mv6(W,z));image=frozenset(line_act[i] for i in S);spread_equiv &= ns_to_spread.get(zz)==image;spread_checks+=1

    checks={
      'P_W_has_121_points':len(PW)==121,
      'partition_is_40_45_36':(len(iso),len(sq),len(ns))==(40,45,36),
      'isotropic_points_equal_W33_line_plueckers':set(by_iso)==set(iso) and len(by_iso)==40,
      'nonsquare_polar_sections_are_10_line_spreads':spread_ok,
      '36_nonsquares_give_36_distinct_spreads':len(derived)==36,
      'independent_exact_cover_has_36_spreads':len(independent)==36,
      'derived_spreads_equal_independent_spreads':derived==indset,
      'square_orbit_equal_explicit_slow_coordinates':slow.get('status')=='PASS' and slowcoords==set(sq),
      'isotropic_line_formula_equivariant_all_3200_cases':iso_equiv and iso_checks==80*40,
      'nonsquare_spread_formula_equivariant_all_2880_cases':spread_equiv and spread_checks==80*36,
    }
    out={'schema':'holotrade.orthogonal-121-formulaic-dictionary.v1','status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,
      'partition':{
        'ambient':'P(ker omega in Lambda^2 F3^4)','total':121,
        'isotropic':{'count':40,'machineObject':'W33 LINES','formula':'decomposable Pluecker point a wedge b'},
        'square':{'count':45,'machineObject':'slow target matrices','formula':'phat(ker(g-I))-phat(ker(g+I))','certificate':'data/slow_o5_closed_form.json'},
        'nonsquare':{'count':36,'machineObject':'W33 spreads','formula':'z -> ten isotropic y with B_Q(z,y)=0 -> ten W33 lines'},
      },
      'theorem':'All three orthogonal orbits in PG(4,3)=40+45+36 have explicit exterior-algebra machine dictionaries. The 40 isotropic points are exactly W33 lines by Pluecker coordinates; the 45 square points are exactly slow targets by the eigenspace-difference formula; the 36 nonsquare points are exactly spreads via their ten-point isotropic polar sections. The 40 and 36 new formulas are equivariant on every transvection case and the spread image equals an independent exact-cover enumeration.',
      'correctionPreserved':'The isotropic 40 are W33 LINES, not the fast opcode POINTS. W33 points form a distinct dual 40-set at odd q.',
      'boundary':'Exact at q=3. Exterior-square and polar-section constructions are algebraic, but no claim that the q>3 square orbit is a generalized quadrangle is made; prior work shows that GQ collapse is q=3-only.'}
    if '--write' in sys.argv:(ROOT/'data/orthogonal_121_formulaic_dictionary.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,indent=2,sort_keys=True));return 0 if out['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
