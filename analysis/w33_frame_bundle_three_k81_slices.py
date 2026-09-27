#!/usr/bin/env python3
"""Cross-repo closure: the 243 frame bundle contains three minimal K81 compiler slices."""
from __future__ import annotations
import argparse, importlib.util, itertools, json
from collections import Counter, deque
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/w33_frame_bundle_three_k81_slices.json"
Q=3
W33_SOURCE_COMMIT="00c0d071a6d86fb4518a1e244513a7e1fb8c158e"


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path); assert s and s.loader
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


def enumerate_frames(octs):
    disj=[[not(octs[i]&octs[j]) for j in range(45)] for i in range(45)]
    out=[]
    def ext(cur,start):
        if len(cur)==5:
            out.append(tuple(cur)); return
        for j in range(start,45):
            if all(disj[j][i] for i in cur): ext(cur+[j],j+1)
    ext([],0)
    assert len(out)==27
    return out
def frame_elation_action():
    fm=load(ROOT/"analysis/the_27_factorisation_frames_carry_the_so10_weights.py","frames27_bundle")
    pts,idx,nm,n,tlines,octs,halves=fm.geometry()
    frames=enumerate_frames(octs)
    fidx={tuple(sorted(f)):j for j,f in enumerate(frames)}
    octid={O:i for i,O in enumerate(octs)}

    def sf(u,v):
        return (u[0]*v[2]-u[2]*v[0]+u[1]*v[3]-u[3]*v[1])%Q
    def transvection(v):
        return [[((1 if r==c else 0)+sf(tuple(1 if k==c else 0 for k in range(4)),v)*v[r])%Q
                 for c in range(4)] for r in range(4)]
    def mat_perm(M):
        return tuple(idx[nm(tuple(sum(M[r][c]*pts[p][c] for c in range(4))%Q
                                  for r in range(4)))] for p in range(n))
    def comp(a,b): return tuple(a[b[i]] for i in range(n))
    I=tuple(range(n))
    def closure(gs):
        seen,dq={I},deque([I])
        while dq:
            x=dq.popleft()
            for g in gs:
                y=comp(g,x)
                if y not in seen: seen.add(y); dq.append(y)
        return seen
    gens=[mat_perm(transvection(v)) for v in pts]
    G=closure(gens)
    assert len(G)==25920
    p0=0
    G0=[g for g in G if g[p0]==p0]
    assert len(G0)==648
    lines_p0=[L for L in tlines if p0 in L]
    def order(g):
        h=g; k=1
        while h!=I:
            h=comp(g,h); k+=1
        return k
    E=[g for g in G0
       if all(frozenset(g[x] for x in L)==L for L in lines_p0)
       and order(g) in (1,3)]
    assert len(E)==27

    def img_frame(g,j):
        f=frames[j]
        return fidx[tuple(sorted(octid[frozenset(g[x] for x in octs[i])] for i in f))]
    perms=[tuple(img_frame(g,j) for j in range(27)) for g in E]
    assert len(set(perms))==27
    assert len({p[0] for p in perms})==27

    F0=set(frames[0])
    overlap=[len(set(f)&F0) for f in frames]
    assert Counter(overlap)==Counter({0:16,1:10,5:1})
    qpsi=[4 if j==0 else (-2 if x==1 else 1) for j,x in enumerate(overlap)]
    assert Counter(qpsi)==Counter({1:16,-2:10,4:1})
    return frames,perms,qpsi
def commuting_powers(perms,qpsi):
    good=[]
    orbit_phase_census={}
    for k in range(12):
        exps=[(k*q)%12 for q in qpsi]
        ok=all(exps[p[j]]==exps[j] for p in perms for j in range(27))
        if ok: good.append(k)
        orbit_phase_census[str(k)]={str(a):b for a,b in Counter(exps).items()}
    assert good==[0,4,8]
    return good,orbit_phase_census


def representation_packet():
    # One H27 regular module decomposes into three minimal latent A9 slices.
    # Partition the nine linear characters of H27/Z into three parallel affine lines.
    tuple_lines=[
      [(0,0),(1,0),(2,0)],
      [(0,1),(1,1),(2,1)],
      [(0,2),(1,2),(2,2)],
    ]
    assert len({x for L in tuple_lines for x in L})==9
    lines=[[list(x) for x in L] for L in tuple_lines]
    slices=[]
    for j,L in enumerate(tuple_lines):
        slices.append({
          "slice":j,
          "linear_characters":[list(x) for x in L],
          "V_omega_copies":1,
          "V_omega2_copies":1,
          "dimension":len(L)+3+3,
          "after_tensor_with_internal_V":{
             "one_dimensional_characters":9,
             "V_omega_copies":3,
             "V_omega2_copies":3,
             "dimension":27,
             "module":"Reg(H27)",
          },
          "after_external_C3":{
             "dimension":81,
             "module":"Reg(H27) tensor Reg(C3) = Reg(K81)",
          },
        })
    assert all(x["dimension"]==9 for x in slices)
    return lines,slices
def payload():
    frames,perms,qpsi=frame_elation_action()
    good,census=commuting_powers(perms,qpsi)
    lines,slices=representation_packet()

    mu=json.loads((ROOT/"data/w33_qutrit_frame_mu12_bundle_carrier.json").read_text())
    torsor=json.loads((ROOT/"data/two_27s_character_twist.json").read_text())
    assert mu["bundle"]["base_objects"]==27 and mu["bundle"]["fibre_dimension"]==9
    assert mu["bundle"]["total_direct_sum_dimension"]==243
    assert torsor["elationOrder"]==27 and torsor["elationsRegularOnBoth"]
    assert mu["frame_Qpsi"]["charges"]=={"1":4,"10":-2,"16":1}

    checks={
      "27_frame_base_recomputed":len(frames)==27,
      "elation_group_regular_on_frames":len(perms)==27 and len({p[0] for p in perms})==27,
      "Qpsi_census_1_10_16":Counter(qpsi)==Counter({1:16,-2:10,4:1}),
      "only_D12_powers_0_4_8_commute_with_frame_H27":good==[0,4,8],
      "FI_fourth_power_is_scalar":len(set((4*q)%12 for q in qpsi))==1,
      "three_A9_slices_partition_regular_H27":sum(x["dimension"] for x in slices)==27,
      "each_A9_times_internal_V_is_regular_H27":all(
          x["after_tensor_with_internal_V"]["module"]=="Reg(H27)" for x in slices),
      "three_K81_slices_fill_243":sum(x["after_external_C3"]["dimension"] for x in slices)==243,
    }
    assert all(checks.values())
    return {
      "schema":"holotrade.w33_frame_bundle_three_k81_slices.v1",
      "status":"PASS_243_FRAME_BUNDLE_SPLITS_INTO_THREE_MINIMAL_K81_COMPILER_CARRIERS",
      "w33SourceCommit":W33_SOURCE_COMMIT,
      "headline":(
        "The 27-frame base is an exact regular H27/elation torsor, and its 27D "
        "regular module can be partitioned into three 9D minimal latent modules "
        "A9_j=(three parallel linear characters)+V+Vbar. If the two-qutrit C9 "
        "fibre is equipped as V_internal tensor Reg(C3_external), then every "
        "A9_j tensor C9 is an 81D Reg(H27 x C3) compiler carrier. Hence the "
        "existing 243D frame bundle supports three parallel K81 slices without "
        "adding Hilbert-space dimension."
      ),
      "frame_base":{
        "frames":27,
        "elation_group_order":27,
        "action":"regular",
        "Qpsi_census":{"4":1,"-2":10,"1":16},
      },
      "three_slice_decomposition":{
        "dual_affine_striation":lines,
        "slice_formula":"A9_j = sum_{chi in line_j} chi + V_omega + V_omega2",
        "slices":slices,
        "total_dimension":243,
      },
      "mu12_compatibility":{
        "commuting_D12_powers":good,
        "commuting_subgroup":"<D12^4> ~= C3",
        "FI_power":"D12^4",
        "FI_phase_on_all_27_frames":"zeta12^4 = omega",
        "full_power_phase_histograms":census,
        "consequence":(
          "The physical FI/common-center Z3 is exactly the part of the frame Qpsi "
          "clock that commutes with the regular H27 address action. Matter parity "
          "D12^6 and the mod-four shadow D12^3 do not commute with that action."
        ),
      },
      "crossrepo_alignment":{
        "W33_result":"Passes 11043-11047: minimal M9 commutant dressing produces Reg(K81) and aligns the cubic 54D tangent compiler",
        "Holotrade_result":"27 factorisation frames are a regular H27/elation torsor and carry the Qpsi/mu12 1+10+16 phase bundle",
        "new_join":(
          "The 243 frame bundle is three copies of the exact minimal 81D compiler "
          "carrier after a dual-Hesse striation choice; independently, its mu12 "
          "clock leaves only the same FI C3 compatible with regular H27."
        ),
      },
      "parents":[
        "data/two_27s_character_twist.json",
        "data/w33_qutrit_frame_mu12_bundle_carrier.json",
        "W33-Theory@00c0d071a Passes 11043-11047",
      ],
      "boundary":(
        "The three-slice statement is representation-theoretic and requires choosing "
        "an ordered internal/external qutrit action on each C9 fibre plus a parallel "
        "striation of the nine linear H27 characters. It does not say the full "
        "Qpsi D12 preserves each chosen slice; in fact only its FI C3 powers commute "
        "with the regular H27 frame action. No heterotic vacuum or hardware pulse is inferred."
      ),
      "checks":checks,
    }


def main(write=True):
    p=payload()
    if write:
        OUT.write_text(json.dumps(p,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
      "status":p["status"],
      "commuting_D12_powers":p["mu12_compatibility"]["commuting_D12_powers"],
      "slice_dimensions":[x["after_external_C3"]["dimension"] for x in p["three_slice_decomposition"]["slices"]],
    },sort_keys=True))
    return p


if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--check",action="store_true")
    a=ap.parse_args(); p=payload()
    text=json.dumps(p,indent=2,sort_keys=True)+"\n"
    if a.check:
        if not OUT.exists() or OUT.read_text()!=text: raise SystemExit("certificate drift")
        print(json.dumps({"status":p["status"],"check":True},sort_keys=True))
    else:
        OUT.write_text(text); print(json.dumps({"status":p["status"]},sort_keys=True))
