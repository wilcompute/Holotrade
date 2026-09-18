#!/usr/bin/env python3
"""Green-Schwarz universality firewall for the current hypercharge sentinel.

At the perturbative heterotic orbifold point, the anomalous U(1) Green-Schwarz
mechanism is universal across non-Abelian gauge factors: mixed anomaly
coefficients divided by their affine levels must align with one common axion
coefficient.

The current quarantined visible ledger has
  A[SU3^2-Y] = +3/2,
  A[SU2^2-Y] = -3/2,
with k3=k2=1 for the level-one Standard Model current algebras.

These are opposite, not universal. Therefore the residual ledger cannot be
declared consistent by relabeling Y as the single anomalous U(1).  Either:
  * the state/projection ledger is still wrong/incomplete,
  * the hypercharge generator/embedding is changed (but the local-27+kY theorem
    severely constrains that), or
  * the witness is rejected.

Moreover phenomenological hypercharge must remain massless/non-anomalous; a
Green-Schwarz anomalous U(1) would not be acceptable as U(1)_Y anyway.

This is a firewall on the current ledger, not a proof that the underlying
gauge embedding is impossible before the external benchmark is completed.
"""
import json
from fractions import Fraction as F
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/w33_z6ii_hypercharge_gs_universality_firewall.json'

def main(write=True):
    A3=F(3,2);A2=F(-3,2);k3=k2=F(1)
    u3=A3/k3;u2=A2/k2
    assert u3!=u2 and u3==-u2
    out={'schema':'w33.z6ii_hypercharge_gs_universality_firewall.v1',
      'status':'PASS_CURRENT_LEDGER_INCONSISTENT_WITH_UNIVERSAL_GS_RESCUE',
      'current_sentinel':{
        'A_SU3sqY':'3/2','A_SU2sqY':'-3/2','k3':1,'k2':1,
        'normalized_coefficients':['3/2','-3/2']},
      'universality_test':'FAIL: A_SU3sqY/k3 != A_SU2sqY/k2',
      'consequence':'The present residual hypercharge anomaly cannot be dismissed as the usual single universal anomalous-U(1) Green-Schwarz direction at the orbifold point.',
      'phenomenology':'Hypercharge must in any case remain massless/non-anomalous in an MSSM-like vacuum.',
      'interaction_with_uniqueness_theorem':'The local-27 plus kY=5/3 theorem fixes the canonical Y uniquely, so arbitrary Cartan mixing is not a free repair while preserving that family data.',
      'boundary':'This condemns the current spectrum ledger, not yet the bare embedding. Finish the published external benchmark before deciding whether the witness itself is dead.',
      'literature_basis':'Universal anomaly cancellation at heterotic orbifold points; non-universal axionic couplings arise after blowup/smooth resolutions, not as a license for an anomalous MSSM hypercharge.',
      'checks':{'equal_level':True,'mixed_anomaly_universality_fails':True}}
    if write:OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2));return out
if __name__=='__main__':main(True)
