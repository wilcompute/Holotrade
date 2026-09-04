#!/usr/bin/env python3
"""The 45 concrete slow targets ARE the 45 minimum words of C2(W33), objectwise.

The new Payne cover certificate assigns to every expensive target the eight W33
axes whose nine-new-line cover contains it.  Independently, W33-Theory already
proved that the binary adjacency-row code C2(W33) is [40,16,8]_2 with exactly
45 minimum words, and that every minimum support induces K4,4 whose two four-
sets are the paired center-quads (Passes 7163--7170).

This script reconstructs C2(W33) from scratch inside Holotrade and checks set
equality, not just counts:

    {eight cover axes of each of the 45 concrete slow slots}
      = {45 weight-eight words of C2(W33)}.

It then recovers the K4,4 bipartition of every support and verifies each side is
a hyperbolic four-set H={x,y}^{perp perp}; the other side is H^perp.  Therefore
each slow slot is explicitly one complementary pair of W33 center-quads.

The E8 statement remains cited from W33-Theory, not re-derived here: that prior
work identifies these 90 center-quads objectwise with 90 D4 root subsystems and
the 45 pairs with selected D4 perp D4 subsystems.
"""
from __future__ import annotations
import itertools,json
from pathlib import Path
from w33_payne_slowpath_core import w33,form
ROOT=Path(__file__).resolve().parents[1]

def bits(s):
 x=0
 for i in s:x|=1<<i
 return x

def support(x):return frozenset(i for i in range(40) if x>>i&1)

def binary_code_minwords(P):
 rows=[]
 for i in range(40):rows.append(bits(j for j in range(40) if i!=j and form(P[i],P[j])==0))
 span={0}
 for r in rows:span|={x^r for x in tuple(span)}
 weights=[x.bit_count() for x in span if x]
 d=min(weights);mins={support(x) for x in span if x.bit_count()==d}
 return len(span),d,mins

def adj(P,a,b):return a!=b and form(P[a],P[b])==0

def bipartition_k44(P,S):
 S=sorted(S);side={S[0]:0};q=[S[0]]
 while q:
  u=q.pop()
  for v in S:
   if not adj(P,u,v):continue
   want=1-side[u]
   if v in side and side[v]!=want:raise AssertionError('not bipartite')
   if v not in side:side[v]=want;q.append(v)
 A=frozenset(x for x in S if side[x]==0);B=frozenset(x for x in S if side[x]==1)
 assert len(A)==len(B)==4
 assert all(adj(P,a,b) for a in A for b in B)
 assert all(not adj(P,a,b) for a,b in itertools.combinations(A,2))
 assert all(not adj(P,a,b) for a,b in itertools.combinations(B,2))
 return tuple(sorted((A,B),key=lambda z:tuple(sorted(z))))

def double_perp(P,a,b):
 common=[z for z in range(40) if (z==a or adj(P,z,a)) and (z==b or adj(P,z,b))]
 return frozenset(z for z in range(40) if all(z==u or adj(P,z,u) for u in common))

def perp_set(P,S):return frozenset(z for z in range(40) if all(z==u or adj(P,z,u) for u in S))

def main():
 C=json.loads((ROOT/'data/slow_path_is_payne_derivative.json').read_text());assert C['status']=='PASS'
 P,_=w33();order,d,mins=binary_code_minwords(P);assert order==2**16 and d==8 and len(mins)==45
 covers={int(k):set(v) for k,v in C['equivariant40']['covers'].items()}
 target_support={t:frozenset(a for a in range(40) if t in covers[a]) for t in range(45)}
 supports=set(target_support.values());pairs={};all_h=set();pair_ok=True
 for t,S in target_support.items():
  A,B=bipartition_k44(P,S);all_h|={A,B}
  a,b=next(iter(itertools.combinations(sorted(A),2)));c,d0=next(iter(itertools.combinations(sorted(B),2)))
  if double_perp(P,a,b)!=A or double_perp(P,c,d0)!=B or perp_set(P,A)!=B or perp_set(P,B)!=A:pair_ok=False
  pairs[t]=(A,B)
 # each hyperbolic/center-quad four-set appears in exactly one complementary pair
 incidence={H:sum(H in pair for pair in pairs.values()) for H in all_h}
 checks={
  'binary_code_order_2pow16':order==2**16,
  'binary_code_min_distance_8':d==8,
  'exactly_45_minimum_words':len(mins)==45,
  '45_slow_supports_unique_weight8':len(supports)==45 and all(len(s)==8 for s in supports),
  'slow_supports_equal_minimum_words_objectwise':supports==mins,
  'every_support_is_K4_4':all(sum(adj(P,u,v) for v in S)==4 for S in supports for u in S),
  'each_bipartition_is_hyperbolic_pair':pair_ok,
  'exactly_90_distinct_hyperbolic_foursets':len(all_h)==90,
  'each_hyperbolic_fourset_has_one_complementary_partner':set(incidence.values())=={1},
 }
 out={
  'schema':'holotrade.slow-targets-are-w33-minimum-words.v1','status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,
  'code':{'length':40,'dimension':16,'minimumDistance':8,'minimumWords':45},
  'dictionary':{str(t):{'weight8Support':sorted(target_support[t]),'centerQuadPair':[sorted(x) for x in pairs[t]]} for t in range(45)},
  'theorem':'For each concrete 45-target ROM slot, the eight W33 Payne covers containing that slot are exactly one minimum-weight support of the binary adjacency-row code C2(W33). The resulting 45 supports exhaust all weight-8 words. Each support is K4,4, and its two four-point parts are mutually perpendicular hyperbolic four-sets, yielding the old 90->45 center-quad quotient objectwise.',
  'e8PriorWork':'W33-Theory Passes 7163-7170 independently proved these same 90 center-quads are the 90 D4 root subsystems in the sixfold E8 lift, and the 45 complementary pairs are selected D4 perp D4 subsystems. This script does not rederive the E8 lift.',
  'boundary':'Exact finite computation at q=3. The C2(W33) code and center-quad pairing are reconstructed here independently; the E8 D4 interpretation is cited repo prior work and is not a new derivation in this file.'
 }
 if '--write' in __import__('sys').argv:(ROOT/'data/slow_targets_are_w33_minimum_words.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
 print(json.dumps(out,indent=2,sort_keys=True));return 0 if out['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
