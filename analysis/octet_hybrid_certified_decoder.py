#!/usr/bin/env python3
"""Certified hybrid decoder for signed-pencil preimages.

Fast path: best strict descent among all 4,140 one/two-octet displacements.
Fallback: best strict descent among the finite PSp(4,3)-orbit of the certified
primitive circuit lying outside that radius-two ball (and its negatives).

Every library move is independently verified to lie in ker_Z(N^T), and the
canonical move lists are content-addressed. Every accepted step strictly lowers
the nonnegative integer negativity objective, so every run terminates after at
most its starting negativity many accepted steps. No complete Graver basis is
needed at runtime.

The decoder is conservative: if neither finite library offers a strict descent,
it returns STALLED rather than claiming global optimality. The regression suite
audits deterministic perturbed starts in all seven certified mass-16 exceptional
cosets and, crucially, the frozen mass-28 radius-two traps that require the
outside-radius-two circuit fallback.
"""
from __future__ import annotations

from collections import deque
import hashlib, json
from pathlib import Path

import mass20_born_depth_and_extension_barcode as m20
import mass24_birth_mass20_census_real_l1 as m24c
import signed_pencil_sampling_witness as sp
import octet_gauge_local_minimum_counterexample as g1
import octet_gauge_radius_two_cutting_plane as r2

HERE=Path(__file__).resolve().parent
CIRCUIT_CERT=HERE/'octet_single_circuit_obstruction_certificate.json'
TRAP_CERT=HERE/'octet_circuit_decoder_trap_certificate.json'


def addv(a,b): return tuple(x+y for x,y in zip(a,b))
def negmass(x): return sum(-v for v in x if v<0)
def act_point_vector(v,g):
    out=[0]*40
    for i,x in enumerate(v): out[g[i]]=x
    return tuple(out)
def orbit_vectors(seed,gens):
    seen={tuple(seed)}; q=deque([tuple(seed)])
    while q:
        x=q.popleft()
        for g in gens:
            y=act_point_vector(x,g)
            if y not in seen: seen.add(y); q.append(y)
    return seen
def digest_moves(moves):
    blob=json.dumps([list(v) for v in sorted(moves)],separators=(',',':')).encode()
    return 'sha256:'+hashlib.sha256(blob).hexdigest()
def best_strict(x,moves):
    d0=negmass(x); best=d0; mv=None
    for m in moves:
        d=negmass(addv(x,m))
        if d<best: best=d; mv=m
    return best,mv

def decode(start,optimum,radius2,circuits,max_steps=200):
    x=tuple(start); initial=negmass(x); steps=[]; rcount=ccount=0
    for _ in range(max_steps):
        d0=negmass(x)
        if d0==optimum: return {'status':'OPTIMUM','initialNegativeMass':initial,'finalNegativeMass':d0,'steps':steps,'radiusTwoSteps':rcount,'circuitSteps':ccount,'final':list(x)}
        b,m=best_strict(x,radius2)
        kind='radius2'
        if m is None:
            b,m=best_strict(x,circuits); kind='circuit'
        if m is None:
            return {'status':'STALLED','initialNegativeMass':initial,'finalNegativeMass':d0,'steps':steps,'radiusTwoSteps':rcount,'circuitSteps':ccount,'final':list(x)}
        y=addv(x,m); d1=negmass(y); assert d1<d0
        steps.append({'kind':kind,'before':d0,'after':d1,'moveDigest':'sha256:'+hashlib.sha256(json.dumps(list(m),separators=(',',':')).encode()).hexdigest()})
        if kind=='radius2': rcount+=1
        else: ccount+=1
        x=y
    raise AssertionError('strict descent exceeded starting-negativity termination bound')


def main():
    lines,thru,pencils,adj,line_gens,order=m20.geometry_data(); assert order==25920
    gauge,moves=g1.gauges(lines); radius2=tuple(sorted(r2.ball2(moves))); assert len(radius2)==4140
    cert=json.loads(CIRCUIT_CERT.read_text()); base=tuple(cert['circuit']['vector']); assert cert['isGraverElement'] and not cert['insideRadiusTwo']
    point_gens=m24c.point_action_generators(pencils,line_gens)
    co=orbit_vectors(base,point_gens); circuits=set(co)|{tuple(-v for v in x) for x in co}; circuits=tuple(sorted(circuits))
    radius2_set=set(radius2); outside=[c for c in circuits if c not in radius2_set]
    assert outside and all(all(sum(v[p] for p in L)==0 for L in lines) for v in radius2 for L in lines)
    assert all(all(sum(v[p] for p in L)==0 for L in lines) for v in circuits for L in lines)

    cover=sp.cover_solver(lines,thru)
    # Exact same seven canonical exceptional cosets used by the decoder studies.
    import the_mass12_census_is_complete_and_has_one_exception as m12
    pts,idx,sf,lines2=m12.geometry(); assert tuple(map(tuple,lines2))==tuple(map(tuple,lines))
    gens2,order2=m12.line_action_generators(pts,idx,sf,lines2); assert order2==25920
    parents=g1.parents(lines,thru,pencils,gens2,cover); assert len(parents)==7
    rows=[]; total_starts=total_opt=total_stall=fallback_used=0
    for pi,parent in enumerate(parents):
        exact=m20.exact_depth(parent['e'],lines,budget=60); assert exact is not None and exact[0]==parent['depth']
        x0=tuple(exact[1]); starts=[]; seen=set()
        # Deterministic increasingly nonlocal gauge perturbations.
        for t in range(1,80):
            w=x0
            count=2+(t%5)
            for j in range(count): w=addv(w,moves[(pi*17+t*11+j*23)%len(moves)])
            if w in seen: continue
            seen.add(w)
            if negmass(w)>parent['depth']: starts.append(w)
            if len(starts)>=5: break
        assert starts, pi
        runs=[]
        for s in starts:
            out=decode(s,parent['depth'],radius2,circuits,max_steps=negmass(s)+1); runs.append(out); total_starts+=1
            assert out['finalNegativeMass']>=parent['depth']
            if out['status']=='OPTIMUM': total_opt+=1
            else: total_stall+=1
            fallback_used+=out['circuitSteps']
        rows.append({'index':pi,'kind':parent['kind'],'orbitSize':parent['orbitSize'],'certifiedGlobalDepth':parent['depth'],'startCount':len(starts),'runs':runs})

    # Operational fallback regression from the independently frozen trap search.
    trap_cert=json.loads(TRAP_CERT.read_text()); assert trap_cert['status']=='PASS' and len(trap_cert['traps'])==2
    trap_rows=[]
    for tr in trap_cert['traps']:
        w=tuple(tr['witness']); e=tuple(tr['lineImage']); assert negmass(w)==2
        exact=m20.exact_depth(e,lines,budget=60); assert exact is not None
        optimum=exact[0]; assert optimum<=1
        br,mr=best_strict(w,radius2); assert mr is None and br==2
        bc,mc=best_strict(w,circuits); assert mc is not None and bc<2
        run=decode(w,optimum,radius2,circuits,max_steps=negmass(w)+1)
        assert run['status']=='OPTIMUM' and run['circuitSteps']>=1
        fallback_used+=run['circuitSteps']; total_starts+=1; total_opt+=1
        trap_rows.append({'orientation':tr['orientation'],'certifiedGlobalDepth':optimum,'bestRadiusTwo':br,'bestCircuit':bc,'run':run})

    out={
      'schema':'holotrade.octet-hybrid-certified-decoder.v2','status':'PASS','group':'PSp(4,3)','groupOrder':25920,
      'radiusTwoMoveCount':len(radius2),'radiusTwoLibraryDigest':digest_moves(radius2),
      'circuitOrbitSize':len(co),'signedCircuitMoveCount':len(circuits),'outsideRadiusTwoCircuitMoveCount':len(outside),'circuitLibraryDigest':digest_moves(circuits),
      'allMovesKernelVerified':True,'benchmarkCosetCount':len(rows),'benchmarkStartCount':total_starts,'benchmarkReachedCertifiedOptimum':total_opt,'benchmarkStalled':total_stall,'fallbackCircuitStepsUsed':fallback_used,
      'mass16RegressionRows':rows,'mass28CircuitTrapRegression':trap_rows,'fallbackPathExercised':fallback_used>0,
      'terminationTheorem':'Each accepted decoder step strictly decreases the nonnegative integer negativity objective. Therefore every run terminates after at most its initial negativity many accepted steps, without requiring the full Graver basis at runtime.',
      'optimalityBoundary':'OPTIMUM is asserted only when the run reaches an independently certified exact depth. STALLED is explicit and is not promoted to global optimality.',
      'theorem':'The runtime move set is finite, content-addressed and independently kernel-verified: radius-two octet descent is attempted first, followed by the finite signed PSp orbit of the certified outside-radius-two primitive circuit. Strict objective descent proves termination. The frozen mass-28 traps explicitly exercise the fallback: radius two has no improving move while the circuit library lowers negativity and reaches the independently certified optimum.',
      'boundary':'This is an integer-lattice decoding algorithm and certificate format. It is not a physical dynamics, quantum speedup, or hardware-efficiency claim.'
    }
    p=HERE/'octet_hybrid_certified_decoder_certificate.json'; p.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:out[k] for k in ['status','radiusTwoMoveCount','circuitOrbitSize','signedCircuitMoveCount','outsideRadiusTwoCircuitMoveCount','benchmarkStartCount','benchmarkReachedCertifiedOptimum','benchmarkStalled','fallbackCircuitStepsUsed','fallbackPathExercised']},indent=2,sort_keys=True)); print(f'written: {p}')

if __name__=='__main__':main()
