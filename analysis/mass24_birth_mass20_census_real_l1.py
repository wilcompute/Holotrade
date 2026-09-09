#!/usr/bin/env python3
"""Complete the mass-20 orbit/depth census, extend delta_R, and attack mass 24.

Three evidence layers are kept separate.

1. Positive mass-20 excesses are exactly the incidence sums of five point
   pencils.  We enumerate every 5-multiset of the 40 points, quotient those
   covers by the exact PSp(4,3) action, and then quotient their excess vectors.
2. Exceptional mass-20 excesses either contain a pencil and descend from the
   complete seven-orbit mass-16 exceptional census, or contain no pencil.  The
   latter sector was exhaustively closed by workflow 34375107072: 5,184 vectors,
   one orbit of size 5,184, exact depth 2.  We re-verify that frozen
   representative against the current geometry and merge it with the complete
   one-pencil descendant frontier.  This gives a complete mass-20 orbit census.
3. A mass-24 depth >=3 class containing a pencil would descend to a mass-20
   class of depth >=3 because +pencil cannot increase integer negativity.
   Therefore, after the complete mass-20 depth<=2 result, depth 3 can only be
   *born* in the no-contained-pencil mass-24 sector.  CP-SAT enumerates that
   sector; completeness is reported explicitly and never inferred from a time
   limit.

For every exceptional mass-20 orbit representative we also solve the real l1
preimage LP and certify it by exact rational primal/dual equality.  We report
    delta_R(e) = (gamma_R(e)-5)/2
next to the exact integer depth.  Positive mass-20 classes have gamma_R=5 and
therefore delta_R=0 by |x|_1 >= |sum x|=5 and their positive cover witness.

Nothing here is physical energy, a blocker theorem, or persistent homology.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
from fractions import Fraction as F
from itertools import combinations_with_replacement
import json
from pathlib import Path
import time

from ortools.sat.python import cp_model
import signed_pencil_sampling_witness as sp
import mass20_born_depth_and_extension_barcode as m20

PRIOR_MASS20_BORN = {
    "repository": "wilcompute/Holotrade",
    "commit": "460618daeddcb9946bce89a7d1c5609fe2f776bc",
    "workflow_run": 34375107072,
    "workflow_job": 102545813880,
    "artifact_id": 10113791450,
    "artifact_zip_sha256": "4f62e50c9e66649825de57160f126988fb9405ed77d970d581fb81fd89d16b9b",
    "certificate_json_sha256": "64c04c599fe80ca283094280201747ce89d47ace176ac944162398337d9a0c64",
    "solutions": 5184,
    "orbit_size": 5184,
    "depth": 2,
}

# Frozen canonical representative emitted by the exhaustive prior certificate.
BORN20_REP = (
    0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,2,
    2,1,0,1,0,0,0,0,0,1,0,2,1,1,1,1,0,2,2,1,
)


def addv(a, b):
    return tuple(x+y for x,y in zip(a,b))


def excess_from_multiset(ms, pencils):
    out=[0]*40
    for p in ms:
        pen=pencils[p]
        for i,v in enumerate(pen): out[i]+=v
    return tuple(out)


def point_action_generators(pencils, line_gens):
    """Induce the exact point permutation from the line-coordinate action."""
    owner={tuple(p):i for i,p in enumerate(pencils)}
    assert len(owner)==40
    out=[]
    for g in line_gens:
        pg=[]
        for p in pencils:
            q=m20.act(p,g)
            assert q in owner
            pg.append(owner[q])
        assert sorted(pg)==list(range(40))
        out.append(tuple(pg))
    return tuple(out)


def multiset_orbit(seed, point_gens):
    seed=tuple(sorted(seed)); seen={seed}; q=deque([seed])
    while q:
        x=q.popleft()
        for g in point_gens:
            y=tuple(sorted(g[p] for p in x))
            if y not in seen:
                seen.add(y); q.append(y)
    return seen


def positive_mass20_orbits(pencils, line_gens):
    """Exact orbit quotient of all C(44,5)=1,086,008 positive covers."""
    point_gens=point_action_generators(pencils,line_gens)
    remaining=set(combinations_with_replacement(range(40),5))
    expected=1
    for a in range(40,45): expected=expected*a//(a-39)
    # Direct combinatorial value; keep a literal independent cross-check too.
    assert len(remaining)==1086008
    cover_orbits=0; excess_classes={}
    while remaining:
        seed=next(iter(remaining))
        ob=multiset_orbit(seed,point_gens)
        remaining.difference_update(ob)
        cover_orbits+=1
        e=excess_from_multiset(seed,pencils)
        rep=min(m20.orbit(e,line_gens))
        row=excess_classes.setdefault(rep,{"coverOrbitCount":0,"coverWitness":list(seed)})
        row["coverOrbitCount"]+=1
    rows=[]
    for rep,data in excess_classes.items():
        ob=m20.orbit(rep,line_gens)
        rows.append({
            "representative":list(rep),"representativeDigest":m20.digest(rep),
            "orbitSize":len(ob),"depth":0,"gammaReal":"5","deltaReal":"0",
            **data,
        })
    rows.sort(key=lambda r:(r["orbitSize"],r["representative"]))
    return {
        "fivePointMultisetsEnumerated":1086008,
        "fivePointMultisetOrbits":cover_orbits,
        "positiveExcessOrbitCount":len(rows),
        "positiveExcessVectorCount":sum(r["orbitSize"] for r in rows),
        "orbits":rows,
        "proof":"Every depth-0 mass-20 excess is a sum of exactly five point pencils; every five-point multiset was enumerated. Orbit quotienting uses the induced exact PSp(4,3) point action and then the exact line-coordinate action.",
    }


def small_depth_witness(e, depth, pencils, cover):
    d,w=m20.depth_leq_two(e,pencils,cover)
    assert d==depth and w is not None
    x=sp.signed_vector(tuple(w["positive"]),tuple(w["negative"]))
    assert tuple(sum(x[p] for p in L) for L in sp.build_geometry()[0])==tuple(e)
    return x,w


def complete_mass20_and_real_l1():
    lines,thru,pencils,adj,gens,order=m20.geometry_data(); assert order==25920
    cover=sp.cover_solver(lines,thru)
    pos=positive_mass20_orbits(pencils,gens)

    ext=m20.extension_graph(lines,thru,pencils,gens,cover)
    descendants=[]
    for r in ext["nodes"]:
        if r["mass"]==20 and r["depth"]>0:
            rep=tuple(r["rep"])
            descendants.append({"rep":rep,"depth":int(r["depth"]),"orbitSize":int(r["orbitSize"]),"kind":"contained-pencil-descendant"})
    assert Counter(r["depth"] for r in descendants)==Counter({1:47,2:4})

    # Re-verify the frozen exhaustive no-pencil orbit against current geometry.
    assert sum(BORN20_REP)==20
    for pen in pencils:
        assert not all(a>=b for a,b in zip(BORN20_REP,pen))
    born_ob=m20.orbit(BORN20_REP,gens)
    assert len(born_ob)==PRIOR_MASS20_BORN["orbit_size"] and min(born_ob)==BORN20_REP
    bd,bw=m20.depth_leq_two(BORN20_REP,pencils,cover); assert bd==2
    exceptional=descendants+[{"rep":BORN20_REP,"depth":2,"orbitSize":len(born_ob),"kind":"no-pencil-born-at-20"}]
    assert len(exceptional)==52
    assert len({r["rep"] for r in exceptional})==52

    real_rows=[]
    for r in exceptional:
        e=r["rep"]; d=r["depth"]
        x,w=small_depth_witness(e,d,pencils,cover)
        int_l1=sum(map(abs,x)); assert int_l1==5+2*d
        frac=sp.fractional_certificate(e,lines)
        gamma=F(frac["l1"]); delta=(gamma-F(5))/2
        assert gamma>=5
        real_rows.append({
            "kind":r["kind"],"orbitSize":r["orbitSize"],"integerDepth":d,
            "representativeDigest":m20.digest(e),"integerL1":int_l1,
            "gammaReal":str(gamma),"deltaReal":str(delta),
            "deltaRealEqualsIntegerDepth":delta==d,
            "l1IntegralityGap":str(F(int_l1)/gamma),
            "integerWitness":{"positive":w["positive"],"negative":w["negative"]},
            "fractionalCertificate":frac,
        })
    real_rows.sort(key=lambda r:(r["integerDepth"],F(r["deltaReal"]),r["orbitSize"],r["representativeDigest"]))
    delta_hist=Counter(r["deltaReal"] for r in real_rows)
    depth_counts=Counter({0:pos["positiveExcessOrbitCount"]})
    depth_counts.update(r["depth"] for r in exceptional)
    total_orbits=sum(depth_counts.values())
    total_vectors=pos["positiveExcessVectorCount"]+sum(r["orbitSize"] for r in exceptional)
    all_equal=all(r["deltaRealEqualsIntegerDepth"] for r in real_rows)

    return {
        "schema":"holotrade.complete-mass20-census-real-l1.v1","status":"PASS","groupOrder":order,
        "priorExhaustiveNoPencilCertificate":PRIOR_MASS20_BORN,
        "positiveSector":pos,
        "exceptionalSector":{
            "orbitCount":len(exceptional),
            "depthCounts":{str(k):v for k,v in sorted(Counter(r["depth"] for r in exceptional).items())},
            "vectorCount":sum(r["orbitSize"] for r in exceptional),
            "bornNoPencilRepresentativeDigest":m20.digest(BORN20_REP),
            "classificationProof":"If exceptional e contains pencil p, then e-p is mass-16 admissible. It cannot be positive (else e would be positive), so the exhaustive seven-orbit mass-16 exceptional census applies. If e contains no pencil, workflow 34375107072 exhaustively proved the single frozen depth-2 orbit.",
        },
        "completeOrbitDepthCounts":{str(k):v for k,v in sorted(depth_counts.items())},
        "completeOrbitCount":total_orbits,"completeAdmissibleVectorCount":total_vectors,
        "noDepthAtLeast3":max(depth_counts)<=2,
        "realL1":{
            "positiveSectorLaw":"gamma_R=5 and delta_R=0 for every positive mass-20 class because |x|_1>=|sum x|=5 and a positive five-pencil cover attains 5.",
            "exceptionalOrbitsCertified":len(real_rows),
            "deltaRealHistogram":dict(sorted(delta_hist.items(),key=lambda kv:F(kv[0]))),
            "deltaRealEqualsIntegerDepthOnAllExceptionalOrbits":all_equal,
            "rows":real_rows,
        },
        "boundary":"Complete finite W(3,3) mass-20 admissible excess orbit census and exact rational real-l1 certificates. No physical-energy or persistent-homology interpretation.",
    }


def mass24_no_pencil_search(*,budget,cap,depth_budget):
    lines,thru,pencils,adj,gens,order=m20.geometry_data(); assert order==25920
    cover=sp.cover_solver(lines,thru)
    model=cp_model.CpModel(); e=[model.NewIntVar(0,24,f"e{i}") for i in range(40)]
    model.Add(sum(e)==24)
    for i in range(40): model.Add(sum(adj[i][j]*e[j] for j in range(40))==2*e[i]+6)
    zero=[]
    for i in range(40):
        z=model.NewBoolVar(f"z{i}"); model.Add(e[i]==0).OnlyEnforceIf(z); model.Add(e[i]>=1).OnlyEnforceIf(z.Not()); zero.append(z)
    for p in range(40): model.AddBoolOr([zero[L] for L in thru[p]])

    class Collector(cp_model.CpSolverSolutionCallback):
        def __init__(self): super().__init__(); self.rows=set(); self.hit_cap=False
        def on_solution_callback(self):
            self.rows.add(tuple(self.Value(v) for v in e))
            if len(self.rows)>=cap: self.hit_cap=True; self.StopSearch()
    cb=Collector(); sv=cp_model.CpSolver(); sv.parameters.enumerate_all_solutions=True; sv.parameters.num_workers=1
    sv.parameters.max_time_in_seconds=float(budget); sv.parameters.random_seed=20260909
    t0=time.time(); st=sv.Solve(model,cb); elapsed=time.time()-t0
    complete=st==cp_model.OPTIMAL and not cb.hit_cap
    remaining=set(cb.rows); orbits=[]; unknown=[]; born3=[]
    while remaining:
        seed=next(iter(remaining)); ob=m20.orbit(seed,gens); remaining.difference_update(ob); rep=min(ob)
        d,w=m20.depth_leq_two(rep,pencils,cover); exact=None
        if d is None:
            exact=m20.exact_depth(rep,lines,budget=depth_budget)
            if exact is None:
                unknown.append(m20.digest(rep)); depth=None
            else: depth=exact[0]
        else: depth=d
        row={"representative":list(rep),"representativeDigest":m20.digest(rep),"orbitSize":len(ob),"depthAtMostTwo":d,"exactDepth":depth,"smallDepthWitness":w}
        if exact is not None: row["exactPreimage"]=list(exact[1])
        orbits.append(row)
        if depth is not None and depth>=3: born3.append(row)
    orbits.sort(key=lambda r:(999 if r["exactDepth"] is None else r["exactDepth"],r["orbitSize"],r["representative"]))
    theorem = bool(born3) or (complete and not unknown)
    no_depth3 = complete and not unknown and not born3
    return {
        "schema":"holotrade.mass24-no-pencil-depth3-birth-search.v1","status":"PASS","groupOrder":order,
        "solverStatus":sv.StatusName(st),"complete":complete,"hitCap":cb.hit_cap,"solutionsFound":len(cb.rows),
        "orbitSeedsFound":len(orbits),"seconds":elapsed,"budgetSeconds":budget,"solutionCap":cap,
        "orbits":orbits,"unknownExactDepthRepresentatives":unknown,"bornDepthAtLeast3":born3,
        "depth3ExistenceProved":bool(born3),"noDepth3Mass24Proved":no_depth3,
        "proofBoundary":("The complete mass-20 census has no depth>=3. Any mass-24 class containing a pencil descends to mass 20 and +pencil cannot increase depth. Therefore depth>=3 at mass 24 can only occur in this no-contained-pencil sector. "
                         + ("The CP-SAT enumeration is complete, so the mass-24 conclusion is exhaustive." if complete else "The CP-SAT enumeration is not complete; absence of a found depth-3 orbit is only scoped evidence.")),
    }


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--skip-mass24",action="store_true"); ap.add_argument("--mass24-only",action="store_true")
    ap.add_argument("--budget",type=float,default=480.0); ap.add_argument("--cap",type=int,default=500000); ap.add_argument("--depth-budget",type=float,default=60.0); ap.add_argument("--write",action="store_true")
    args=ap.parse_args(); outputs={}
    if not args.mass24_only:
        outputs["mass20"]=complete_mass20_and_real_l1()
        if args.write:
            p=Path(__file__).with_name("complete_mass20_census_real_l1_certificate.json"); p.write_text(json.dumps(outputs["mass20"],indent=2,sort_keys=True)+"\n")
    if not args.skip_mass24:
        outputs["mass24"]=mass24_no_pencil_search(budget=args.budget,cap=args.cap,depth_budget=args.depth_budget)
        if args.write:
            p=Path(__file__).with_name("mass24_no_pencil_depth3_birth_certificate.json"); p.write_text(json.dumps(outputs["mass24"],indent=2,sort_keys=True)+"\n")
    summary={"status":"PASS"}
    if "mass20" in outputs:
        m=outputs["mass20"]; summary.update(mass20OrbitCount=m["completeOrbitCount"],mass20DepthCounts=m["completeOrbitDepthCounts"],mass20DeltaRealEqualsDepth=m["realL1"]["deltaRealEqualsIntegerDepthOnAllExceptionalOrbits"],deltaRealHistogram=m["realL1"]["deltaRealHistogram"])
    if "mass24" in outputs:
        m=outputs["mass24"]; summary.update(mass24Complete=m["complete"],mass24Solutions=m["solutionsFound"],mass24OrbitSeeds=m["orbitSeedsFound"],mass24BornDepth3=len(m["bornDepthAtLeast3"]),mass24NoDepth3Proved=m["noDepth3Mass24Proved"])
    print(json.dumps(summary,indent=2,sort_keys=True))

if __name__=="__main__": main()
