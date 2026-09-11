#!/usr/bin/env python3
"""Construct an actual decoder instance for the certified outside-radius-two circuit.

The frozen primitive circuit c is a genuine Graver element of ker_Z(N^T) but is
not one of the 4,140 one/two-octet displacements.  That fact alone only kills a
universal Graver proof strategy.  Here we ask the sharper operational question:
can c actually escape a radius-two local minimum of the negativity objective?

We search bounded integer preimages x with nonnegative line image e=N^T x and
positive pencil mass k=sum(x).  The chosen circuit orientation must strictly
lower negativity, while an exact cutting-plane separation oracle enforces that
all 4,140 radius-two endpoints have negativity at least that of x.

If a witness is found, it is unconditional after verification: the coordinate
box is only how the witness was discovered.  If the bounded model is infeasible,
that is only a bounded nonexistence statement.
"""
from __future__ import annotations

import argparse, json, time
from pathlib import Path
from ortools.sat.python import cp_model

import signed_pencil_sampling_witness as sp
import octet_gauge_local_minimum_counterexample as g1
import octet_gauge_radius_two_cutting_plane as r2

HERE=Path(__file__).resolve().parent
CIRCUIT_CERT=HERE/'octet_single_circuit_obstruction_certificate.json'


def addv(a,b): return tuple(x+y for x,y in zip(a,b))
def negmass(x): return sum(-v for v in x if v<0)


def endpoint_expr(model,x,D,d,bound,tag):
    nn=[]
    extra=max(abs(int(z)) for z in d)
    for p in range(40):
        z=model.NewIntVar(0,bound+extra,f"ep{tag}_{p}")
        model.AddMaxEquality(z,[0,-x[p]-int(d[p])]); nn.append(z)
    return nn


def attack(orientation,*,bound,budget,batch,kmax):
    cert=json.loads(CIRCUIT_CERT.read_text()); assert cert['status']=='PASS' and cert['isGraverElement'] is True and cert['insideRadiusTwo'] is False
    base=tuple(int(v) for v in cert['circuit']['vector']); c=tuple(orientation*v for v in base)
    lines,thru,pencils=sp.build_geometry(); gauge,moves=g1.gauges(lines); ball=r2.ball2(moves); assert len(ball)==4140
    assert all(sum(c[p] for p in L)==0 for L in lines)
    assert c not in set(ball)

    model=cp_model.CpModel(); x=[model.NewIntVar(-bound,bound,f"x{p}") for p in range(40)]
    neg=[]
    for p in range(40):
        z=model.NewIntVar(0,bound,f"n{p}"); model.AddMaxEquality(z,[0,-x[p]]); neg.append(z)
    D=model.NewIntVar(1,40*bound,'D'); model.Add(D==sum(neg))
    k=model.NewIntVar(1,kmax,'k'); model.Add(k==sum(x))
    e=[]
    for i,L in enumerate(lines):
        y=model.NewIntVar(0,4*bound,f"e{i}"); model.Add(y==sum(x[p] for p in L)); e.append(y)
    # Circuit must be a strictly improving escape.
    cg=endpoint_expr(model,x,D,c,bound,'circuit')
    Dg=model.NewIntVar(0,40*(bound+2),'Dg'); model.Add(Dg==sum(cg)); model.Add(Dg<=D-1)
    # Prefer the smallest/simple trap discovered.
    absx=[]
    for p in range(40):
        a=model.NewIntVar(0,bound,f"a{p}"); model.AddAbsEquality(a,x[p]); absx.append(a)
    model.Minimize(10000*k+100*D+sum(absx))

    started=time.time(); cuts=set(); iterations=[]; witness=None; final='UNKNOWN'
    while time.time()-started<budget:
        remain=budget-(time.time()-started); sv=cp_model.CpSolver(); sv.parameters.num_workers=8; sv.parameters.random_seed=20260911+(1 if orientation>0 else 2)
        sv.parameters.max_time_in_seconds=max(1.0,min(25.0,remain)); st=sv.Solve(model); status=sv.StatusName(st)
        if st==cp_model.INFEASIBLE:
            final='INFEASIBLE'; break
        if st not in (cp_model.OPTIMAL,cp_model.FEASIBLE):
            final=status; break
        w=tuple(int(sv.Value(v)) for v in x); d0=negmass(w); wc=addv(w,c); dc=negmass(wc)
        assert dc<d0
        vals=sorted((negmass(addv(w,d)),j) for j,d in enumerate(ball)); best=vals[0][0]
        improving=[j for val,j in vals if val<d0 and j not in cuts]
        iterations.append({'solverStatus':status,'k':sum(w),'negativeMass':d0,'circuitEndpointNegativeMass':dc,'bestRadiusTwo':best,'cutsBefore':len(cuts),'newViolations':len(improving)})
        if not improving:
            assert all(val>=d0 for val,_ in vals)
            witness=w; final='COUNTEREXAMPLE'; break
        for j in improving[:batch]:
            r2.add_endpoint_cut(model,x,D,ball[j],bound,len(cuts)); cuts.add(j)

    out={
      'schema':'holotrade.octet-circuit-decoder-instance.v1','status':'PASS','orientation':orientation,
      'coordinateBound':bound,'kMax':kmax,'budgetSeconds':budget,'seconds':time.time()-started,
      'circuit':list(c),'circuitDigestSource':'analysis/octet_single_circuit_obstruction_certificate.json',
      'distinctRadiusTwoDisplacements':len(ball),'cutsAdded':len(cuts),'iterations':iterations,'finalStatus':final,
      'decoderTrapFound':witness is not None,
      'witness':None if witness is None else list(witness),
      'lineImage':None if witness is None else [sum(witness[p] for p in L) for L in lines],
      'mass':None if witness is None else 4*sum(witness),
      'negativeMass':None if witness is None else negmass(witness),
      'circuitEndpoint':None if witness is None else list(addv(witness,c)),
      'circuitEndpointNegativeMass':None if witness is None else negmass(addv(witness,c)),
      'unconditionalWitnessVerification':None if witness is None else {
        'sameLineImage':all(sum(witness[p] for p in L)==sum((witness[p]+c[p]) for p in L) for L in lines),
        'all4140RadiusTwoEndpointsNonImproving':all(negmass(addv(witness,d))>=negmass(witness) for d in ball),
        'circuitStrictlyImproves':negmass(addv(witness,c))<negmass(witness),
        'lineImageNonnegative':all(sum(witness[p] for p in L)>=0 for L in lines),
      },
      'reading':'COUNTEREXAMPLE is a genuine radius-two decoder trap escaped by the certified outside-radius-two Graver circuit. INFEASIBLE is scoped to the stated coordinate and mass box; UNKNOWN is inconclusive.',
      'boundary':'This is exact integer-lattice decoder behavior. It does not assert physical dynamics, quantum advantage, or hardware performance.'
    }
    return out


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--orientation',type=int,choices=[-1,1],required=True); ap.add_argument('--bound',type=int,default=10); ap.add_argument('--kmax',type=int,default=14); ap.add_argument('--budget',type=float,default=600); ap.add_argument('--batch',type=int,default=48); a=ap.parse_args()
    out=attack(a.orientation,bound=a.bound,budget=a.budget,batch=a.batch,kmax=a.kmax)
    path=HERE/f"octet_circuit_decoder_instance_{'plus' if a.orientation>0 else 'minus'}.json"; path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:out[k] for k in ['status','orientation','finalStatus','decoderTrapFound','cutsAdded','mass','negativeMass','circuitEndpointNegativeMass','seconds']},indent=2,sort_keys=True)); print(f'written: {path}')

if __name__=='__main__': main()
