#!/usr/bin/env python3
"""Exact structural classification of the two first mass-40 depth-5 births.

The exhaustive mass-40 no-pencil census proves exactly two depth-five births,
of orbit sizes 216 and 4320.  This pass compares them at the stabilizer/support
level: exact stabilizer point orbits, the union of coordinates that can be
negative in an optimal preimage, incident-line signatures on every stabilizer
symbol, and the complete one-pencil depth derivative/target-orbit table to mass
44.

The depth derivative is exact: for a depth-d parent, adding P_p drops depth iff
p lies in the optimal-negative-support union.  No child depth optimization is
needed, although target PSp orbits are canonicalized independently.
"""
from __future__ import annotations

from collections import Counter
import hashlib,json
from pathlib import Path

import mass20_born_depth_and_extension_barcode as m20
import exceptional_depth_derivative_automaton as aut

HERE=Path(__file__).resolve().parent
SUMMARY=HERE/'mass40_no_pencil_exhaustive_summary.json'
DEPTH=5


def addv(a,b): return tuple(x+y for x,y in zip(a,b))
def hist(v): return {str(k):n for k,n in sorted(Counter(v).items())}
def digest_obj(x): return 'sha256:'+hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def classify(row,lines,thru,pencils,gens):
    rep=tuple(row['representative']); digest=row['representativeDigest']; orbit_size=row['orbitSize']
    assert sum(rep)==40 and m20.digest(rep)==digest and row['integerDepth']==DEPTH
    ob=m20.orbit(rep,gens); assert len(ob)==orbit_size and min(ob)==rep
    exact=m20.exact_depth(rep,lines,budget=120); assert exact is not None and exact[0]==DEPTH
    support,witnesses=aut.optimal_negative_support(rep,DEPTH,lines)
    osize,stab_order,point_orbits=aut.parent_stabilizer_point_orbits(rep,lines)
    assert osize==orbit_size and osize*stab_order==25920
    symbols=[]; child_reps=set()
    for oi,O in enumerate(point_orbits):
        flags={p in support for p in O}; assert len(flags)==1; drop=next(iter(flags))
        incident={tuple(sorted(rep[L] for L in thru[p])) for p in O}; assert len(incident)==1
        targets={min(m20.orbit(addv(rep,pencils[p]),gens)) for p in O}; assert len(targets)==1
        target=next(iter(targets)); child_reps.add(target)
        symbols.append({
          'pointOrbitIndex':oi,'pointOrbitSize':len(O),'points':list(O),
          'pointStabilizerOrder':stab_order//len(O),
          'optimalNegativeSupport':drop,'supportIntersectionSize':sum(p in support for p in O),
          'depthDerivative':-1 if drop else 0,'targetDepth':DEPTH-1 if drop else DEPTH,
          'incidentParentLineValues':list(next(iter(incident))),
          'targetRepresentativeDigest':m20.digest(target),'targetOrbitSize':len(m20.orbit(target,gens)),
        })
    support_orbits=[s['pointOrbitSize'] for s in symbols if s['optimalNegativeSupport']]
    derivative_hist={str(d):sum(s['pointOrbitSize'] for s in symbols if s['targetDepth']==d) for d in (4,5)}
    signature={
      'orbitSize':orbit_size,'stabilizerOrder':stab_order,'representativeValueHistogram':hist(rep),
      'pointOrbitSizes':sorted(map(len,point_orbits)),'optimalNegativeSupportSize':len(support),
      'supportOrbitSizes':sorted(support_orbits),'childOrbitCount':len(child_reps),
      'childDepthPointHistogram':derivative_hist,
      'symbolMultiset':sorted((s['pointOrbitSize'],s['optimalNegativeSupport'],tuple(s['incidentParentLineValues']),s['targetDepth'],s['targetOrbitSize']) for s in symbols),
    }
    return {
      'representative':list(rep),'representativeDigest':digest,'orbitSize':orbit_size,'stabilizerOrder':stab_order,
      'representativeValueHistogram':hist(rep),'exactDepth':DEPTH,'oneExactOptimalPreimage':list(exact[1]),
      'pointOrbitCount':len(point_orbits),'pointOrbitSizes':sorted(map(len,point_orbits)),
      'optimalNegativeSupport':sorted(support),'optimalNegativeSupportSize':len(support),
      'optimalNegativeSupportOrbitSizes':sorted(support_orbits),
      'optimalNegativeSupportWitnessCount':len(witnesses),
      'childOrbitCount':len(child_reps),'childDepthPointHistogram':derivative_hist,'symbols':symbols,
      'structuralSignature':signature,'structuralSignatureDigest':digest_obj(signature),
    }


def main():
    src=json.loads(SUMMARY.read_text()); assert src['status']=='PASS' and src['enumerationComplete'] and src['depth5BirthOrbitCount']==2
    births=src['depth5Births']; assert sorted(r['orbitSize'] for r in births)==[216,4320]
    lines,thru,pencils,adj,gens,order=m20.geometry_data(); assert order==25920
    rows=[classify(r,lines,thru,pencils,gens) for r in births]
    assert sorted(r['stabilizerOrder'] for r in rows)==[6,120]
    assert len({r['structuralSignatureDigest'] for r in rows})==2
    out={
      'schema':'holotrade.mass40-depth5-structural-types.v1','status':'PASS','group':'PSp(4,3)','groupOrder':25920,
      'mass':40,'depth':5,'birthOrbitCount':2,'rows':rows,
      'stabilizerOrders':sorted(r['stabilizerOrder'] for r in rows),
      'orbitSizes':sorted(r['orbitSize'] for r in rows),
      'mass44DerivativeLaw':'Every one-pencil child has depth 4 or 5; depth drops exactly on the certified optimal-negative-support union.',
      'theorem':'The two first depth-five mass-40 births are structurally inequivalent far beyond orbit size: their stabilizers have orders 120 and 6, and the certificate gives the exact stabilizer point-orbit partition, optimal-negative-support orbit union, incident-line signatures, and complete mass-44 one-pencil derivative/target-orbit table for each.',
      'boundary':'Exact finite W33 group action and integer optimization only. The stabilizer/support distinction is not a physical symmetry-breaking or energy claim.'
    }
    p=HERE/'mass40_depth5_structural_types_certificate.json'; p.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':'PASS','rows':[{'digest':r['representativeDigest'],'orbitSize':r['orbitSize'],'stabilizerOrder':r['stabilizerOrder'],'pointOrbitSizes':r['pointOrbitSizes'],'supportSize':r['optimalNegativeSupportSize'],'supportOrbitSizes':r['optimalNegativeSupportOrbitSizes'],'childOrbitCount':r['childOrbitCount'],'childDepthPointHistogram':r['childDepthPointHistogram']} for r in rows]},indent=2,sort_keys=True)); print(f'written: {p}')

if __name__=='__main__': main()
