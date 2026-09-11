#!/usr/bin/env python3
"""Minimize the certified outside-radius-two circuit fallback under PSp(4,3).

The exact primitive circuit c and its negative each escape a certified mass-28
radius-two trap.  A runtime library should not carry redundant group images.
This script computes the exact PSp(4,3) point-action orbit of c and -c, determines
whether they are one orbit or two, and solves the tiny set-cover problem over
those PSp-invariant orientation orbits for the two frozen trap witnesses.

The resulting minimality statement is scoped to PSp-invariant libraries built
from the certified circuit orientation orbits and to the frozen exact traps.
It is not a claim that no other primitive-circuit orbit is useful on other
fibers.
"""
from __future__ import annotations

from collections import deque
import hashlib,json
from itertools import combinations
from pathlib import Path

import mass20_born_depth_and_extension_barcode as m20
import mass24_birth_mass20_census_real_l1 as m24c

HERE=Path(__file__).resolve().parent
BASE_CERT=HERE/'octet_single_circuit_obstruction_certificate.json'
TRAPS=[HERE/'octet_circuit_decoder_instance_plus.json',HERE/'octet_circuit_decoder_instance_minus.json']


def addv(a,b): return tuple(x+y for x,y in zip(a,b))
def negmass(x): return sum(-v for v in x if v<0)
def act(v,g):
    out=[0]*40
    for i,x in enumerate(v): out[g[i]]=x
    return tuple(out)
def orbit(seed,gens):
    seed=tuple(seed); seen={seed}; q=deque([seed])
    while q:
        x=q.popleft()
        for g in gens:
            y=act(x,g)
            if y not in seen: seen.add(y); q.append(y)
    return frozenset(seen)
def digest_moves(moves):
    blob=json.dumps([list(v) for v in sorted(moves)],separators=(',',':')).encode()
    return 'sha256:'+hashlib.sha256(blob).hexdigest()
def escape_info(w,moves):
    d0=negmass(w); best=d0; count=0; example=None
    for m in moves:
        d=negmass(addv(w,m))
        if d<d0: count+=1
        if d<best: best=d; example=m
    return {'startNegativeMass':d0,'bestEndpointNegativeMass':best,'strictImprovingMoveCount':count,
            'strictEscapeExists':best<d0,'oneBestMove':None if example is None else list(example)}


def main():
    lines,thru,pencils,adj,line_gens,order=m20.geometry_data(); assert order==25920
    point_gens=m24c.point_action_generators(pencils,line_gens)
    bc=json.loads(BASE_CERT.read_text()); assert bc['isGraverElement'] and not bc['insideRadiusTwo']
    c=tuple(bc['circuit']['vector']); cm=tuple(-x for x in c)
    op=orbit(c,point_gens); om=orbit(cm,point_gens)
    relation='same-orbit' if op==om else ('disjoint-orbits' if op.isdisjoint(om) else 'overlapping-distinct')
    assert relation in ('same-orbit','disjoint-orbits')
    orientation_orbits=[op] if op==om else [op,om]
    names=['plus'] if op==om else ['plus','minus']
    traps=[]
    for p in TRAPS:
        d=json.loads(p.read_text()); assert d['decoderTrapFound'] and d['unconditionalWitnessVerification']['all4140RadiusTwoEndpointsNonImproving']
        w=tuple(d['witness'])
        infos={name:escape_info(w,O) for name,O in zip(names,orientation_orbits)}
        traps.append({'source':p.name,'orientation':d['orientation'],'witness':list(w),'orbitEscapes':infos})
    covers=[]
    for mask in range(1,1<<len(orientation_orbits)):
        chosen=[i for i in range(len(orientation_orbits)) if mask>>i&1]
        union=frozenset().union(*(orientation_orbits[i] for i in chosen))
        ok=all(escape_info(tuple(t['witness']),union)['strictEscapeExists'] for t in traps)
        if ok: covers.append((len(union),len(chosen),chosen,union))
    assert covers
    covers.sort(key=lambda z:(z[1],z[0],z[2])); _,_,chosen,lib=covers[0]
    # Minimality among PSp-invariant unions of the certified ±c orientation orbits.
    assert not any(cov[1]<len(chosen) for cov in covers)
    out={
      'schema':'holotrade.octet-circuit-library-minimization.v1','status':'PASS','group':'PSp(4,3)','groupOrder':25920,
      'baseCircuitDigest':bc['circuit']['digest'],'baseCircuitSupportSize':bc['circuit']['supportSize'],
      'plusOrbitSize':len(op),'minusOrbitSize':len(om),'orientationOrbitRelation':relation,
      'orientationOrbitDigests':{name:digest_moves(O) for name,O in zip(names,orientation_orbits)},
      'trapCount':len(traps),'traps':traps,
      'minimalSelectedOrientationOrbits':[names[i] for i in chosen],
      'minimalPSpInvariantCircuitMoveCount':len(lib),'minimalLibraryDigest':digest_moves(lib),
      'minimalLibraryEscapes':[{ 'source':t['source'], **escape_info(tuple(t['witness']),lib)} for t in traps],
      'minimalityScope':'Exact among PSp(4,3)-invariant unions of the certified primitive circuit orientation orbits {Orb(c), Orb(-c)} for simultaneously escaping the two frozen exact mass-28 radius-two traps.',
      'theorem':'The certified circuit fallback can be quotiented and minimized at the PSp(4,3)-orbit level. The certificate determines whether sign reversal is already a group image and returns the smallest orientation-orbit union that escapes both exact radius-two traps.',
      'boundary':'This does not claim completeness of primitive circuits or universal optimality of the minimized library on every affine fiber. It is an exact minimization relative to the certified circuit orbit(s) and frozen traps.'
    }
    p=HERE/'octet_circuit_library_minimization_certificate.json'; p.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:out[k] for k in ['status','plusOrbitSize','minusOrbitSize','orientationOrbitRelation','minimalSelectedOrientationOrbits','minimalPSpInvariantCircuitMoveCount','minimalLibraryDigest']},indent=2,sort_keys=True)); print(f'written: {p}')

if __name__=='__main__':main()
