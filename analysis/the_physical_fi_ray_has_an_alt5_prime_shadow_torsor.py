#!/usr/bin/env python3
"""Model-side verification of the physical FI prime-shadow torsor.

Reads the flagship physical FI certificate produced from Orbifolder data and
classifies its exact five-coordinate permutation orbit. This mirrors the W33
representation theorem while preserving model provenance and vacuum scope.
"""
from __future__ import annotations
import itertools, json, math
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"data/w33_flagship_fi_ray_pure_a4.json"
OUT=ROOT/"data/w33_flagship_fi_prime_shadow_torsor.json"

def parity(p):
    return sum(p[i]>p[j] for i in range(5) for j in range(i+1,5))&1
def act(p,x): return tuple(x[p[i]] for i in range(5))
def orb(G,x): return {act(g,x) for g in G}
def stab(G,x): return [g for g in G if act(g,x)==x]

def main(write=True):
    parent=json.loads(SRC.read_text())
    assert parent["status"]=="PASS_EXACT_FI_RAY_ORTHOGONAL_TO_HYPERCHARGE"
    v=tuple(parent["duad_star"]["six_times_star"])
    assert v==(-5,3,1,-5,6) and sum(v)==0
    S5=list(itertools.permutations(range(5)))
    A5=[g for g in S5 if parity(g)==0]
    assert len(orb(S5,v))==len(orb(A5,v))==60
    assert len(stab(S5,v))==2 and len(stab(A5,v))==1
    values=sorted(set(v))
    Delta=math.prod(b-a for a,b in itertools.combinations(values,2))
    assert Delta==15840
    expected={2:(5,12),3:(10,6),5:(30,2),11:(20,3)}
    shadows={}
    for p,(n,f) in expected.items():
        r=tuple(x%p for x in v)
        O=orb(A5,r); H=stab(A5,r)
        fibers=Counter(tuple(x%p for x in w) for w in orb(A5,v))
        assert len(O)==n and set(fibers.values())=={f}
        shadows[str(p)]={"residue":list(r),"orbit_size":n,
          "stabilizer_order":len(H),"integral_fiber_size":f,
          "multiplicity_partition":sorted(Counter(r).values(),reverse=True)}
    assert shadows["3"]["multiplicity_partition"]==[3,2]
    out={
      "schema":"w33.flagship_fi_prime_shadow_torsor.v1",
      "status":"PASS_MODEL_SIDE_FI_PRIME_SHADOW_TORSOR",
      "model":"SM_20260917_3",
      "physical_FI_star":list(v),
      "integral":{"S5_orbit":60,"S5_stabilizer":2,"Alt5_orbit":60,"Alt5_stabilizer":1},
      "collision_discriminant":Delta,
      "collision_primes":[2,3,5,11],
      "prime_shadows":shadows,
      "mod3_reading":"(1,0,1,1,0): an exact 3+2 partition of the five hypercharge-star coordinates, with ten possible images and six integral FI lifts per image",
      "cross_repo_owner":"wilcompute/W33-Theory analysis/w33_physical_fi_alt5_prime_shadow_torsor.py",
      "boundary":"Exact finite classification of the physical FI ray. It does not construct a D-flat/F-flat vacuum and does not identify the Abelian charge-space 3+2 quotient with non-Abelian SU(5) gauge breaking without an explicit intertwiner."}
    if write: OUT.write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps(out,indent=2)); return out
if __name__=="__main__": main(True)
