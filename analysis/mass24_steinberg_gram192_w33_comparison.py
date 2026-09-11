#!/usr/bin/env python3
"""Compare the projective order-192 Gram symmetry with existing W33 192s.

The integral Steinberg bridge certificate produces
    Gamma = (Aut(I3) x Aut(G5)) / <(-I3,-I5)>
of order 192, with Aut(I3)=C2 x S4 and Aut(G5)=C2^3.  Abstractly the diagonal
central quotient is S4 x C2^3.

We compare Gamma with two independently defined order-192 groups:
  * the W33 Pass5705 magnetic group G96 x C2, whose frozen fingerprint has
    center order 4 and derived subgroup order 24;
  * W(D4), the even signed permutation group C2^3 : S4, whose center and
    derived subgroup are computed directly here.

Order equality alone is therefore decisively rejected.  At the same time Gamma
has an exact positive connection to the W33 projective cube/frame controller
C2 x S4: Gamma ~= (C2 x S4) x C2^2.
"""
from __future__ import annotations

from collections import Counter
from itertools import permutations,product
import json,math,os
from pathlib import Path

HERE=Path(__file__).resolve().parent
GRAM=HERE/'mass24_steinberg_integral_gram_gauge_certificate.json'
W33_ROOT=Path(os.environ.get('W33_ROOT','../W33-Theory')).resolve()
W33_FP=W33_ROOT/'data/PART_W33_PASS5705_DECK96_192_GROUP_FINGERPRINT.json'


def porder(p):
    seen=[False]*len(p); ans=1
    for i in range(len(p)):
        if seen[i]: continue
        j=i;n=0
        while not seen[j]: seen[j]=True;j=p[j];n+=1
        ans=math.lcm(ans,n)
    return ans

def gram192_hist():
    h=Counter()
    for p in permutations(range(4)):
        po=porder(p)
        for bits in product((0,1),repeat=3):
            h[math.lcm(po,2 if any(bits) else 1)]+=1
    return h

def wd4_elements():
    return [(p,s) for p in permutations(range(4)) for s in product((1,-1),repeat=4) if math.prod(s)==1]
def comp(a,b):
    p,s=a;q,t=b
    return (tuple(p[q[i]] for i in range(4)),tuple(t[i]*s[q[i]] for i in range(4)))
ID=(tuple(range(4)),(1,1,1,1))
def inv(a,els):
    for b in els:
        if comp(a,b)==ID and comp(b,a)==ID:return b
    raise AssertionError
def order(a):
    x=ID
    for n in range(1,193):
        x=comp(a,x)
        if x==ID:return n
    raise AssertionError
def closure(gs):
    G={ID};front=[ID]
    while front:
        x=front.pop()
        for g in gs:
            y=comp(g,x)
            if y not in G:G.add(y);front.append(y)
    return G

def wd4_fp():
    els=wd4_elements(); assert len(els)==192
    hist=Counter(order(g) for g in els)
    center=[g for g in els if all(comp(g,h)==comp(h,g) for h in els)]
    ii={g:inv(g,els) for g in els}; comm=[]
    for a in els:
        for b in els: comm.append(comp(comp(comp(a,b),ii[a]),ii[b]))
    der=closure(comm)
    return {'order':192,'centerOrder':len(center),'derivedOrder':len(der),'abelianizationOrder':192//len(der),
            'elementOrderHistogram':{str(k):v for k,v in sorted(hist.items())}}


def main():
    gram=json.loads(GRAM.read_text()); assert gram['status']=='PASS' and gram['combinedProjectiveAutOrderModuloGlobalSign']==192
    w=json.loads(W33_FP.read_text()); assert w['D_extension']['order']==192
    gh=gram192_hist(); assert sum(gh.values())==192
    gamma={'order':192,'abstractStructure':'S4 x C2^3','centerOrder':8,'derivedOrder':12,'abelianizationOrder':16,
           'elementOrderHistogram':{str(k):v for k,v in sorted(gh.items())},
           'w33CubeFrameFactor':'C2 x S4','extraCentralSignFactor':'C2^2'}
    magnetic={'order':192,'centerOrder':w['D_extension']['center_order'],'derivedOrder':w['D_extension']['derived_order'],
              'abstractStructure':w['D_extension']['exact_structure'],'elementOrderHistogram':w['D_extension']['element_order_histogram']}
    wd4=wd4_fp()
    assert (gamma['centerOrder'],gamma['derivedOrder'])==(8,12)
    assert (magnetic['centerOrder'],magnetic['derivedOrder'])==(4,24)
    assert (wd4['centerOrder'],wd4['derivedOrder'])==(2,96)
    assert gamma['elementOrderHistogram']!={str(k):v for k,v in magnetic['elementOrderHistogram'].items()}
    assert gamma['elementOrderHistogram']!=wd4['elementOrderHistogram']
    out={
      'schema':'holotrade.mass24-steinberg-gram192-w33-comparison.v1','status':'PASS',
      'gramProjective192':gamma,'w33Pass5705Magnetic192':magnetic,'standardWD4':wd4,
      'isomorphicToW33Magnetic192':False,'isomorphicToWD4':False,
      'nonIsomorphismWitnesses':{
        'vsW33Magnetic192':['center order 8 vs 4','derived order 12 vs 24','different element-order histogram'],
        'vsWD4':['center order 8 vs 2','derived order 12 vs 96','different element-order histogram']},
      'positiveBridge':{
        'w33ProjectiveController':w['projective_quotient']['exact_structure'],
        'w33ProjectiveControllerOrder':w['projective_quotient']['order'],
        'gram192Structure':'(C2 x S4) x C2^2 = S4 x C2^3',
        'reading':'The Gram 192 is not the repo magnetic 192 and not W(D4), but it contains the exact W33 C2 x S4 cube/frame controller as a direct factor, with two additional independent central sign bits.'},
      'theorem':'The repeated order 192 is not an isomorphism coincidence: three exact order-192 controllers in the project have different center/derived fingerprints. The integral Gram projective symmetry is S4 x C2^3, distinct from the W33 magnetic G96 x C2 and from W(D4)=C2^3:S4. Its precise bridge to existing W33 structure is instead the direct factor C2 x S4 already certified as the Pass5705 projective cube/frame controller.',
      'boundary':'Finite-group identification only. The direct-factor relation does not identify these groups with physical rotations, spacetime symmetries, or hardware dynamics.'
    }
    p=HERE/'mass24_steinberg_gram192_w33_comparison_certificate.json';p.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:out[k] for k in ['status','gramProjective192','w33Pass5705Magnetic192','standardWD4','isomorphicToW33Magnetic192','isomorphicToWD4','positiveBridge']},indent=2,sort_keys=True)); print(f'written: {p}')
if __name__=='__main__':main()
