#!/usr/bin/env python3
"""Exact separator between inherited and born mass-40 depth-four W33 classes.

Mass 36 is exhaustively capped at integer negativity depth 4.  Pencil addition
never raises depth.  Therefore any mass-40 depth-4 vector that contains a
removable point-pencil must reduce to a mass-36 depth-4 parent, hence to one of
the three exhaustive parent orbits classified by mass36_depth4_structural_types.
Conversely the exhaustive mass-40 no-pencil census contains exactly the born
sector.  This script canonicalizes every one-pencil child symbol from the three
parents, compares all depth-4 child orbit digests with all 28 no-pencil depth-4
birth digests, and quantifies cross-parent orbit mergers.
"""
from __future__ import annotations

from collections import defaultdict,Counter
import json
from pathlib import Path

import mass20_born_depth_and_extension_barcode as m20
import mass36_depth4_structural_types as m36

HERE=Path(__file__).resolve().parent
INDEX40=HERE/'mass40_no_pencil_30_orbit_index.json'


def main():
    idx=json.loads(INDEX40.read_text()); assert idx['status']=='PASS' and idx['orbitCount']==30
    births4={r['representativeDigest'] for r in idx['rows'] if r['integerDepth']==4}; births5={r['representativeDigest'] for r in idx['rows'] if r['integerDepth']==5}
    assert len(births4)==28 and len(births5)==2
    lines,thru,pencils,adj,gens,order=m20.geometry_data(); assert order==25920
    parents=[m36.classify(p,lines,thru,pencils,gens) for p in m36.PARENTS]
    records=[]
    for parent in parents:
        prep=tuple(parent['representative']); pd=parent['representativeDigest']
        for s in parent['symbols']:
            p=s['points'][0]
            child=tuple(prep[i]+pencils[p][i] for i in range(40))
            assert all(x>=0 for x in child) and tuple(child[i]-pencils[p][i] for i in range(40))==prep
            canon=min(m20.orbit(child,gens)); digest=m20.digest(canon)
            assert digest==s['targetRepresentativeDigest']
            records.append({
              'parentDigest':pd,'parentOrbitSize':parent['orbitSize'],'parentPointOrbitIndex':s['pointOrbitIndex'],
              'pointOrbitSize':s['pointOrbitSize'],'sourcePoint':p,'targetDepth':s['targetDepth'],
              'targetDigest':digest,'targetOrbitSize':s['targetOrbitSize'],'removablePencilWitnessPoint':p,
            })
    by_digest=defaultdict(list)
    for r in records: by_digest[r['targetDigest']].append(r)
    depth4_children={d for d,rs in by_digest.items() if {r['targetDepth'] for r in rs}=={4}}
    depth3_children={d for d,rs in by_digest.items() if {r['targetDepth'] for r in rs}=={3}}
    assert not depth4_children & births4
    assert not set(by_digest) & births5
    mergers=[]
    for d,rs in sorted(by_digest.items()):
        parents_here=sorted({r['parentDigest'] for r in rs})
        if len(parents_here)>1:
            mergers.append({'targetDigest':d,'targetDepth':rs[0]['targetDepth'],'parentDigests':parents_here,'sourceSymbolCount':len(rs),'targetOrbitSize':rs[0]['targetOrbitSize']})
    parent_pairs=Counter()
    for m in mergers:
        ps=m['parentDigests']
        for i in range(len(ps)):
            for j in range(i+1,len(ps)): parent_pairs[(ps[i],ps[j])]+=1
    out={
      'schema':'holotrade.mass36-to-mass40-inheritance-separator.v1','status':'PASS','group':'PSp(4,3)','groupOrder':25920,
      'mass36Depth4ParentOrbitCount':3,'mass40NoPencilDepth4BirthOrbitCount':28,'mass40NoPencilDepth5BirthOrbitCount':2,
      'sourceSymbolCount':len(records),'uniqueInheritedChildOrbitCount':len(by_digest),
      'uniqueInheritedDepth4ChildOrbitCount':len(depth4_children),'uniqueInheritedDepth3ChildOrbitCount':len(depth3_children),
      'depth4InheritedDigests':sorted(depth4_children),'depth4NoPencilBirthDigests':sorted(births4),
      'depth4InheritedVsBirthIntersection':sorted(depth4_children & births4),
      'crossParentMergerCount':len(mergers),'crossParentMergers':mergers,
      'crossParentMergerPairHistogram':[{'parentDigests':list(k),'mergedChildOrbitCount':v} for k,v in sorted(parent_pairs.items())],
      'records':records,
      'separator':{
        'property':'contains a removable point-pencil',
        'inheritedDepth4':True,'bornNoPencilDepth4':False,
        'logic':'If mass40 depth4 e contains P_p, then e-P_p is admissible mass36. Pencil addition changes depth by 0 or -1, so a depth4 child requires a mass36 parent of depth at least4. The exhaustive mass36 maximum is4, hence the parent lies in one of the three exhaustive depth4 orbits. If no P_p is removable, e belongs to the exhaustive no-pencil birth sector.'
      },
      'theorem':'At mass 40 and depth 4, removable-pencil containment is an exact inheritance-vs-birth separator. Every inherited depth-four orbit arises as a one-pencil child of one of the three exhaustive mass-36 depth-four parents, while the 28 exhaustive no-pencil depth-four birth orbits are disjoint from all such child digests. The certificate also records every cross-parent merger among inherited child orbits.',
      'boundary':'Exact finite W33 orbit/combinatorial statement. This separator concerns point-pencil ancestry, not physical causality or dynamical history.'
    }
    p=HERE/'mass36_to_mass40_inheritance_separator_certificate.json'; p.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:out[k] for k in ['status','sourceSymbolCount','uniqueInheritedChildOrbitCount','uniqueInheritedDepth4ChildOrbitCount','uniqueInheritedDepth3ChildOrbitCount','mass40NoPencilDepth4BirthOrbitCount','depth4InheritedVsBirthIntersection','crossParentMergerCount','crossParentMergerPairHistogram']},indent=2,sort_keys=True)); print(f'written: {p}')

if __name__=='__main__': main()
