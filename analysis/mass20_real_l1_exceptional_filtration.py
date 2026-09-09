#!/usr/bin/env python3
"""Exact real-l1 filtration for the complete exceptional mass-20 sector.

This intentionally avoids the slower positive-cover orbit census.  The
exceptional classification is already exhaustive: 51 contained-pencil
mass-16 descendants from the seven complete exceptional parent orbits, plus the
single exhaustively certified no-pencil mass-20 orbit.  Positive mass-20
classes satisfy gamma_R=5 and delta_R=0 analytically.
"""
from __future__ import annotations
from collections import Counter
from fractions import Fraction as F
import json
from pathlib import Path
import signed_pencil_sampling_witness as sp
import mass20_born_depth_and_extension_barcode as m20
from mass24_birth_mass20_census_real_l1 import BORN20_REP, PRIOR_MASS20_BORN, small_depth_witness

def main():
    lines,thru,pencils,adj,gens,order=m20.geometry_data(); assert order==25920
    cover=sp.cover_solver(lines,thru)
    ext=m20.extension_graph(lines,thru,pencils,gens,cover)
    rows=[]
    for r in ext["nodes"]:
        if r["mass"]==20 and r["depth"]>0:
            rows.append({"rep":tuple(r["rep"]),"depth":int(r["depth"]),"orbitSize":int(r["orbitSize"]),"kind":"contained-pencil-descendant"})
    assert Counter(r["depth"] for r in rows)==Counter({1:47,2:4})
    ob=m20.orbit(BORN20_REP,gens); assert len(ob)==5184 and min(ob)==BORN20_REP
    bd,bw=m20.depth_leq_two(BORN20_REP,pencils,cover); assert bd==2
    rows.append({"rep":BORN20_REP,"depth":2,"orbitSize":5184,"kind":"no-pencil-born-at-20"})
    assert len(rows)==52 and len({r["rep"] for r in rows})==52
    outrows=[]
    for r in rows:
        x,w=small_depth_witness(r["rep"],r["depth"],pencils,cover); integer_l1=sum(map(abs,x)); assert integer_l1==5+2*r["depth"]
        frac=sp.fractional_certificate(r["rep"],lines); gamma=F(frac["l1"]); delta=(gamma-F(5))/2
        outrows.append({
          "kind":r["kind"],"orbitSize":r["orbitSize"],"integerDepth":r["depth"],"integerL1":integer_l1,
          "representativeDigest":m20.digest(r["rep"]),"gammaReal":str(gamma),"deltaReal":str(delta),
          "deltaRealEqualsIntegerDepth":delta==r["depth"],"l1IntegralityGap":str(F(integer_l1,gamma)),
          "fractionalCertificate":frac,
        })
    outrows.sort(key=lambda r:(r["integerDepth"],F(r["deltaReal"]),r["orbitSize"],r["representativeDigest"]))
    hist=Counter(r["deltaReal"] for r in outrows); equal=all(r["deltaRealEqualsIntegerDepth"] for r in outrows)
    out={
      "schema":"holotrade.mass20-real-l1-exceptional-filtration.v1","status":"PASS","groupOrder":order,
      "exceptionalOrbitCount":52,"integerDepthCounts":{"1":47,"2":5},"priorNoPencilCertificate":PRIOR_MASS20_BORN,
      "positiveSectorLaw":"Every positive mass-20 class has gamma_R=5 and delta_R=0: |x|_1 >= |sum x|=5 and its nonnegative five-pencil cover attains equality.",
      "deltaRealHistogram":dict(sorted(hist.items(),key=lambda kv:F(kv[0]))),
      "deltaRealEqualsIntegerDepthOnAllExceptionalOrbits":equal,
      "firstIntegralityGap":next((r for r in outrows if not r["deltaRealEqualsIntegerDepth"]),None),
      "rows":outrows,
      "boundary":"Exact rational primal/dual l1 certificates on the finite W(3,3) pencil incidence map; no physical-energy interpretation."
    }
    p=Path(__file__).with_name("mass20_real_l1_exceptional_filtration_certificate.json"); p.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":"PASS","exceptionalOrbits":52,"deltaRealHistogram":out["deltaRealHistogram"],"allEqual":equal,"firstGap":out["firstIntegralityGap"]},indent=2,sort_keys=True))
    print(f"written: {p}")
if __name__=="__main__": main()
