#!/usr/bin/env python3
"""Exact irreducible decomposition of the two degree-1080 PSp(4,3) actions.

The mass-24 depth-three orbit and the obstruction carrier are reconstructed in
the same faithful 40-point PSp(4,3) permutation group used by the green
character-fingerprint certificate. Their point stabilizers H_m,H_o have order
24. We export those actual subgroups of the same permutation group to GAP and
compute C[G/H_m] and C[G/H_o] against Irr(G). The unique degree-81 irreducible
is recorded explicitly as the Steinberg constituent.
"""
from __future__ import annotations

import json, os, shutil, subprocess, sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
W33_ANALYSIS=os.environ.get("W33_ANALYSIS")
if W33_ANALYSIS: sys.path.insert(0,W33_ANALYSIS)

import mass24_1080_gset_character_fingerprint as fp
import mass24_depth3_steinberg_real_l1 as m24
import w33_20260901_obstruction_wedderburn_steinberg_projectors as obs


def gap_perm(p): return "PermList(["+",".join(str(i+1) for i in p)+"])"
def gap_list(ps): return "["+",".join(gap_perm(p) for p in ps)+"]"


def build_actions():
    pts,wlines,all_point,all_line=fp.same_generators()
    h_lines,_,_=m24.sp.build_geometry(); hidx={frozenset(L):i for i,L in enumerate(h_lines)}
    rep_w33=tuple(m24.REP[hidx[frozenset(L)]] for L in wlines)
    states,mass_selected=m24.mass_orbit_actions(rep_w33,tuple(all_line[i] for i in fp.GENERATOR_INDICES)); assert len(states)==1080
    obstruction_selected,charts,wlines2=obs.build_action(); assert len(obstruction_selected)==4
    point_selected=tuple(all_point[i] for i in fp.GENERATOR_INDICES)
    image,_=fp.build_group_with_base_images(point_selected,mass_selected,tuple(obstruction_selected)); assert len(image)==25920
    Hm=tuple(sorted(g for g,(mi,oi) in image.items() if mi==0)); Ho=tuple(sorted(g for g,(mi,oi) in image.items() if oi==0))
    assert len(Hm)==len(Ho)==24
    return point_selected,Hm,Ho


def run_gap(Ggens,Hm,Ho):
    gap=shutil.which("gap")
    if not gap: raise RuntimeError("GAP is required")
    script=f'''\nG:=Group({gap_list(Ggens)});;\nHm:=Group({gap_list(Hm)});; Ho:=Group({gap_list(Ho)});;\nif Size(G)<>25920 or Size(Hm)<>24 or Size(Ho)<>24 then Error("group size drift"); fi;\nirr:=Irr(G);; cm:=InducedClassFunction(TrivialCharacter(Hm),G);; co:=InducedClassFunction(TrivialCharacter(Ho),G);;\ndm:=List(irr,x->ScalarProduct(cm,x));; dobs:=List(irr,x->ScalarProduct(co,x));;\nidsm:=Filtered([1..Length(irr)],i->dm[i]<>0);; idso:=Filtered([1..Length(irr)],i->dobs[i]<>0);;\nst:=Filtered([1..Length(irr)],i->irr[i][1]=81);; if Length(st)<>1 then Error("Steinberg degree-81 not unique"); fi;\nPrint("irr_count=",Length(irr),"\\n");\nPrint("degrees=",JoinStringsWithSeparator(List(irr,x->String(x[1])),","),"\\n");\nPrint("mass_ids=",JoinStringsWithSeparator(List(idsm,String),","),"\\n");\nPrint("mass_mults=",JoinStringsWithSeparator(List(idsm,i->String(dm[i])),","),"\\n");\nPrint("mass_degrees=",JoinStringsWithSeparator(List(idsm,i->String(irr[i][1])),","),"\\n");\nPrint("obs_ids=",JoinStringsWithSeparator(List(idso,String),","),"\\n");\nPrint("obs_mults=",JoinStringsWithSeparator(List(idso,i->String(dobs[i])),","),"\\n");\nPrint("obs_degrees=",JoinStringsWithSeparator(List(idso,i->String(irr[i][1])),","),"\\n");\nPrint("mass_norm=",ScalarProduct(cm,cm),"\\n"); Print("obs_norm=",ScalarProduct(co,co),"\\n"); Print("cross_hom=",ScalarProduct(cm,co),"\\n");\nPrint("steinberg_index=",st[1],"\\n"); Print("mass_steinberg_mult=",dm[st[1]],"\\n"); Print("obs_steinberg_mult=",dobs[st[1]],"\\n");\nQUIT;\n'''
    cp=subprocess.run([gap,"-q"],input=script,text=True,capture_output=True,check=True,timeout=120)
    parsed={}
    for line in cp.stdout.splitlines():
        if "=" in line:
            k,v=line.strip().split("=",1); parsed[k]=v
    return parsed


def ints(s): return [] if not s else [int(x) for x in s.split(",")]

def main():
    Ggens,Hm,Ho=build_actions(); p=run_gap(Ggens,Hm,Ho)
    req={"irr_count","degrees","mass_ids","mass_mults","mass_degrees","obs_ids","obs_mults","obs_degrees","mass_norm","obs_norm","cross_hom","steinberg_index","mass_steinberg_mult","obs_steinberg_mult"}
    miss=req-set(p); assert not miss,miss
    mass=list(zip(ints(p["mass_ids"]),ints(p["mass_degrees"]),ints(p["mass_mults"])))
    obstruction=list(zip(ints(p["obs_ids"]),ints(p["obs_degrees"]),ints(p["obs_mults"])))
    assert sum(d*m for _,d,m in mass)==1080 and sum(d*m for _,d,m in obstruction)==1080
    mass_map={i:m for i,d,m in mass}; obs_map={i:m for i,d,m in obstruction}
    differing=[]
    degrees=ints(p["degrees"])
    for i in sorted(set(mass_map)|set(obs_map)):
        a=mass_map.get(i,0); b=obs_map.get(i,0)
        if a!=b: differing.append({"irreducibleIndex":i,"degree":degrees[i-1],"massMultiplicity":a,"obstructionMultiplicity":b})
    sm=int(p["mass_steinberg_mult"]); so=int(p["obs_steinberg_mult"])
    out={
      "schema":"holotrade.mass24-1080-irreducible-decomposition.v2","status":"PASS","group":"PSp(4,3)=U4(2)","groupOrder":25920,
      "massStabilizerOrder":24,"obstructionStabilizerOrder":24,"irreducibleCharacterCount":int(p["irr_count"]),
      "massConstituents":[{"index":i,"degree":d,"multiplicity":m} for i,d,m in mass],
      "obstructionConstituents":[{"index":i,"degree":d,"multiplicity":m} for i,d,m in obstruction],
      "massOrbitalRank":int(p["mass_norm"]),"obstructionOrbitalRank":int(p["obs_norm"]),"complexHomDimension":int(p["cross_hom"]),
      "steinberg":{"irreducibleIndex":int(p["steinberg_index"]),"degree":81,"massMultiplicity":sm,"obstructionMultiplicity":so,"crossSteinbergHomDimension":sm*so},
      "differingConstituents":differing,"permutationModulesIsomorphic":not differing,
      "theorem":"The two degree-1080 permutation modules are decomposed against Irr(PSp(4,3)) using their actual order-24 stabilizers in one faithful permutation group. The Steinberg cross-Hom dimension is the product of the exact Steinberg multiplicities.",
      "boundary":"Finite complex representation theory only. Shared constituents, including Steinberg-81, do not identify the underlying G-sets or physical systems."
    }
    path=HERE/"mass24_1080_irreducible_decomposition_certificate.json"; path.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":"PASS","mass":mass,"obstruction":obstruction,"ranks":[out["massOrbitalRank"],out["obstructionOrbitalRank"]],"hom":out["complexHomDimension"],"steinberg":out["steinberg"],"differing":differing},indent=2,sort_keys=True)); print(f"written: {path}")

if __name__=="__main__": main()
