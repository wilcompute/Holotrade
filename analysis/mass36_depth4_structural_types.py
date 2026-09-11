#!/usr/bin/env python3
"""Exact structural classification of the three mass-36 no-pencil depth-4 orbits.

The exhaustive mass-36 census found exactly three depth-four orbits: two of size
4320 and one of size 25920.  This script goes beyond orbit size.  For each
canonical representative it recovers the exact parent stabilizer, its point
orbits, the full optimal-negativity support, local incident-line signatures,
and the complete one-pencil descendant symbol table supplied by the universal
discrete derivative theorem.

The output is an exact finite invariant package intended to explain why the
three depth-four classes are distinct and how each can persist/drop at mass 40.
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

import mass20_born_depth_and_extension_barcode as m20
import exceptional_depth_derivative_automaton as aut

HERE=Path(__file__).resolve().parent
DEPTH=4
PARENTS=[
  {
    'digest':'sha256:2f565cb857cb8fd87167b57738f1d7123ac9e2c310f38b1bd33935e5c8eb02ff','orbitSize':4320,
    'rep':(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,3,2,3,0,0,1,2,3,3,0,1,2,3,2,3,3,1,2,1,0,0),
  },
  {
    'digest':'sha256:6134c05c40f74f2e96631e860ad2e27ed92fa46d9eba0cc3e7b4ff2f8f6d561c','orbitSize':4320,
    'rep':(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,3,2,3,0,0,1,2,3,3,1,2,3,3,2,3,2,0,1,1,0,0),
  },
  {
    'digest':'sha256:4c8f026bf2b47d2fcd4c162e8dcb67e5df53cad33deef105f0be750b3d35ca8c','orbitSize':25920,
    'rep':(0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,2,0,0,0,3,4,2,1,2,0,0,0,0,1,2,0,3,2,1,1,2,0,3,4,2),
  },
]


def addv(a,b): return tuple(x+y for x,y in zip(a,b))

def hist(v): return {str(k):n for k,n in sorted(Counter(v).items())}


def classify(parent,lines,thru,pencils,gens):
    rep=parent['rep']; assert sum(rep)==36 and m20.digest(rep)==parent['digest']
    ob=m20.orbit(rep,gens); assert len(ob)==parent['orbitSize'] and min(ob)==rep
    exact=m20.exact_depth(rep,lines,budget=90); assert exact is not None and exact[0]==DEPTH
    support,witnesses=aut.optimal_negative_support(rep,DEPTH,lines)
    orbit_size,stab_order,point_orbits=aut.parent_stabilizer_point_orbits(rep,lines)
    assert orbit_size==parent['orbitSize'] and orbit_size*stab_order==25920
    symbols=[]; child_reps=set()
    for oi,O in enumerate(point_orbits):
        flags={p in support for p in O}; assert len(flags)==1; drop=next(iter(flags))
        vals={tuple(sorted(rep[L] for L in thru[p])) for p in O}; assert len(vals)==1
        targets={min(m20.orbit(addv(rep,pencils[p]),gens)) for p in O}; assert len(targets)==1
        target=next(iter(targets)); child_reps.add(target)
        symbols.append({
          'pointOrbitIndex':oi,'pointOrbitSize':len(O),'points':list(O),
          'pointStabilizerOrder':stab_order//len(O),
          'optimalNegativeSupport':drop,'depthDerivative':-1 if drop else 0,'targetDepth':DEPTH-1 if drop else DEPTH,
          'incidentParentLineValues':list(next(iter(vals))),
          'targetRepresentativeDigest':m20.digest(target),'targetOrbitSize':len(m20.orbit(target,gens)),
        })
    support_orbit_sizes=sorted(s['pointOrbitSize'] for s in symbols if s['optimalNegativeSupport'])
    point_orbit_sizes=sorted(len(O) for O in point_orbits)
    child_depth_point_hist={str(d):sum(s['pointOrbitSize'] for s in symbols if s['targetDepth']==d) for d in (3,4)}
    signature={
      'orbitSize':orbit_size,'stabilizerOrder':stab_order,'representativeValueHistogram':hist(rep),
      'pointOrbitSizes':point_orbit_sizes,'optimalNegativeSupportSize':len(support),'supportOrbitSizes':support_orbit_sizes,
      'childOrbitCount':len(child_reps),'childDepthPointHistogram':child_depth_point_hist,
    }
    return {
      'representative':list(rep),'representativeDigest':parent['digest'],'orbitSize':orbit_size,'stabilizerOrder':stab_order,
      'representativeValueHistogram':hist(rep),'exactDepth':DEPTH,'oneExactOptimalPreimage':list(exact[1]),
      'pointOrbitCount':len(point_orbits),'pointOrbitSizes':point_orbit_sizes,
      'optimalNegativeSupport':sorted(support),'optimalNegativeSupportSize':len(support),'supportOrbitSizes':support_orbit_sizes,
      'childOrbitCount':len(child_reps),'childDepthPointHistogram':child_depth_point_hist,'symbols':symbols,
      'structuralSignature':signature,
    }


def main():
    lines,thru,pencils,adj,gens,order=m20.geometry_data(); assert order==25920
    rows=[classify(p,lines,thru,pencils,gens) for p in PARENTS]
    sigs=[json.dumps(r['structuralSignature'],sort_keys=True) for r in rows]; assert len(set(sigs))==3
    # The two 4320 classes must be structurally distinguished without using their digest.
    a,b=rows[:2]; assert a['orbitSize']==b['orbitSize']==4320 and a['structuralSignature']!=b['structuralSignature']
    out={
      'schema':'holotrade.mass36-depth4-structural-types.v1','status':'PASS','group':'PSp(4,3)','groupOrder':25920,
      'mass':36,'depth':4,'orbitCount':3,'rows':rows,
      'allThreeStructuralSignaturesDistinct':True,
      'two4320ClassesDistinguishedBeyondOrbitSize':True,
      'theorem':'The three exhaustive mass-36 depth-four PSp(4,3) orbits have distinct exact stabilizer/support/descendant signatures. In particular the two size-4320 classes are not merely duplicate-size phenomena: their parent-stabilizer point-orbit decomposition, optimal-negativity support and/or one-pencil derivative signatures distinguish them exactly.',
      'boundary':'These are exact finite W33 orbit and integer-optimization invariants. The structural signature is a classifier for the three certified mass-36 depth-four orbits, not yet a theorem that the same finite tuple classifies arbitrary masses.'
    }
    path=HERE/'mass36_depth4_structural_types_certificate.json'; path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':'PASS','rows':[{'digest':r['representativeDigest'],'orbitSize':r['orbitSize'],'stabilizerOrder':r['stabilizerOrder'],'pointOrbitSizes':r['pointOrbitSizes'],'supportSize':r['optimalNegativeSupportSize'],'supportOrbitSizes':r['supportOrbitSizes'],'childOrbitCount':r['childOrbitCount'],'childDepthPointHistogram':r['childDepthPointHistogram']} for r in rows]},indent=2,sort_keys=True)); print(f'written: {path}')

if __name__=='__main__': main()
