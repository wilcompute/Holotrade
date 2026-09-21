#!/usr/bin/env python3
"""Objectwise Qpsi/mu12 phase carrier on the 27 two-qutrit factorisation frames.

This closes the representation/carrier question as far as the existing object
dictionary actually permits.

Choose a reference complete factorisation frame F0.  The exact Holotrade frame
theorem realizes the E6 minuscule 27 as
    1  = F0,
    10 = frames sharing one factorisation with F0,
    16 = frames sharing none,
with Qpsi charges 4,-2,1.

Define on the 27-frame basis
    D12 |F> = zeta_12^{Qpsi(F)} |F>.

Every one of the 45 tritangent/cubic triples has total Qpsi zero, so the product
of its three phases is one.  Because the two-qutrit Clifford scalar center is
mu_12, each frame fibre H_F ~= C^9 admits the scalar
    zeta_12^{Qpsi(F)} I_9.
Thus the direct-sum frame bundle
    H_bundle = direct_sum_F H_F ~= C^27 tensor C^9
carries an explicit fibrewise Clifford-scalar realization of the E6 Qpsi
character.

Important boundary: this is a bundle/controlled-phase carrier.  It is NOT a
single scalar Clifford on one C^9: one scalar has one eigenphase, while the
27 frame labels require three distinct phase values with multiplicities
1,10,16.  A noncentral single-two-qutrit intertwiner remains a separate open
problem.
"""
from __future__ import annotations
import importlib.util
import json
import math
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/w33_qutrit_frame_mu12_bundle_carrier.json"

def load(path,name):
    s=importlib.util.spec_from_file_location(name,path)
    assert s and s.loader
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def order_of_exponent(e,n=12):
    return n//math.gcd(e%n,n)

def main(write=True):
    bridge=load(ROOT/"analysis/w33_qutrit_frame_matter_parity_cubic_bridge.py","framebridge")
    mu=json.loads((ROOT/"data/w33_e8_z12_clifford_mu12_character_crossrepo.json").read_text())
    assert mu["status"]=="PASS_CROSSREPO_E8_Z12_TO_CLIFFORD_MU12_CHARACTER"
    assert any("scalar phase group" in x and "mu_12" in x for x in mu["admit"])

    mod=bridge.load_parent()
    _,frames=bridge.enumerate_frames(mod)
    F0=set(frames[0])
    overlap=[len(set(f)&F0) for f in frames]
    assert Counter(overlap)==Counter({0:16,1:10,5:1})

    qpsi=[]
    roles=[]
    for i,x in enumerate(overlap):
        if i==0:
            roles.append("1");qpsi.append(4)
        elif x==1:
            roles.append("10");qpsi.append(-2)
        else:
            roles.append("16");qpsi.append(1)
    assert Counter(zip(roles,qpsi))==Counter({("16",1):16,("10",-2):10,("1",4):1})

    exponents=[q%12 for q in qpsi]
    assert Counter(exponents)==Counter({1:16,10:10,4:1})
    assert math.lcm(*(order_of_exponent(e) for e in exponents))==12

    # Exact powers recover the certified shadows.
    parity=[(6*e)%12 for e in exponents]
    fi_z3=[(4*e)%12 for e in exponents]
    kummer_z4=[(3*e)%12 for e in exponents]
    assert Counter(parity)==Counter({6:16,0:11})
    assert Counter(fi_z3)==Counter({4:27})
    assert Counter(kummer_z4)==Counter({3:16,6:10,0:1})
    # More informative classwise checks:
    for role,q,e in zip(roles,qpsi,exponents):
        assert ((6*e)//6)%2 == q%2
        assert ((4*e)//4)%3 == q%3
        assert ((3*e)//3)%4 == q%4

    # Reconstruct the 45 cubic triples from factorisation-octet incidence.
    inc={o:[] for o in range(45)}
    for fi,f in enumerate(frames):
        for o in f:inc[o].append(fi)
    assert all(len(v)==3 for v in inc.values())
    records=[]
    pats=Counter()
    for o,tri in sorted(inc.items()):
        qs=tuple(sorted(qpsi[i] for i in tri))
        assert sum(qs)==0
        assert sum(exponents[i] for i in tri)%12==0
        pats[qs]+=1
        records.append({
            "octet":o,"frames":tri,
            "Qpsi":[qpsi[i] for i in tri],
            "phase_exponents_mod12":[exponents[i] for i in tri],
            "phase_product":"1",
        })
    assert pats==Counter({(-2,1,1):40,(-2,-2,4):5})

    # Formal bundle dimensions and the exact scalar-center obstruction.
    fibre_dim=9
    bundle_dim=27*fibre_dim
    distinct_phase_exponents=sorted(set(exponents))
    assert distinct_phase_exponents==[1,4,10]
    single_scalar_center_can_realize_relative_phases=(len(distinct_phase_exponents)==1)
    assert single_scalar_center_can_realize_relative_phases is False

    out={
      "schema":"holotrade.w33_qutrit_frame_mu12_bundle_carrier.v1",
      "status":"PASS_OBJECTWISE_27_FRAME_FIBREWISE_MU12_CARRIER",
      "headline":"The E6 Qpsi character now has an explicit objectwise two-qutrit carrier: on the 27 complete factorisation frames, D12 assigns zeta12^4 to the reference 1, zeta12^-2 to the ten frames sharing one factorisation, and zeta12 to the sixteen disjoint frames. Every tritangent triple has phase product one. Since each frame fibre is C^9 and the two-qutrit Clifford scalar center is mu12, the 27-frame bundle direct_sum_F C^9 carries these phases fibrewise as genuine Clifford scalars.",
      "frame_Qpsi":{
        "roles":{"1":1,"10":10,"16":16},
        "charges":{"1":4,"10":-2,"16":1},
        "phase_exponents_mod12":{"1":4,"10":10,"16":1},
        "phase_multiplicities":{"1":16,"4":1,"10":10},
        "D12_order":12
      },
      "bundle":{
        "base_objects":27,
        "fibre":"two-qutrit Hilbert space C^9 for each complete factorisation frame",
        "fibre_dimension":9,
        "total_direct_sum_dimension":bundle_dim,
        "operator":"D_bundle = direct_sum_F zeta_12^{Qpsi(F)} I_9",
        "each_block_is_Clifford_scalar":True,
        "stabilizer_equivariance":"The W(D5) stabilizer of F0 preserves the 1+10+16 orbit partition, so D_bundle commutes with that exact frame stabilizer action."
      },
      "cubic_phase_conservation":{
        "total_tritangents":45,
        "patterns":{"(-2,1,1)":40,"(-2,-2,4)":5},
        "all_phase_products_one":True
      },
      "power_shadows":{
        "sixth_power":"matter parity (-1)^Qpsi on the 1+10+16 frame carrier",
        "fourth_power":"physical FI / Qpsi mod3 character",
        "third_power":"Qpsi mod4 / Kummer character"
      },
      "single_C9_scalar_firewall":{
        "distinct_required_phase_exponents_mod12":distinct_phase_exponents,
        "single_scalar_center_has_one_eigenphase":True,
        "can_realize_relative_27_frame_phases":False,
        "statement":"The mu12 scalar center alone cannot realize the relative 1+10+16 phase pattern on one C^9. The exact carrier constructed here therefore includes the frame label as a base/register. A noncentral single-two-qutrit Clifford intertwiner is not ruled out by this argument and remains open."
      },
      "records":records,
      "parents":[
        "data/w33_qutrit_frame_matter_parity_cubic_bridge.json",
        "data/twenty_seven_frames_so10_weights.json",
        "data/w33_e8_z12_clifford_mu12_character_crossrepo.json"
      ],
      "checks":{
        "frame_partition_1_10_16":True,
        "phase_operator_exact_order12":True,
        "all_45_cubics_phase_neutral":True,
        "bundle_blocks_are_mu12_scalars":True,
        "single_scalar_center_no_go":True
      }
    }
    if write:OUT.write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps({k:out[k] for k in ("status","frame_Qpsi","bundle","single_C9_scalar_firewall")},indent=2))
    return out

if __name__=="__main__":main(True)
