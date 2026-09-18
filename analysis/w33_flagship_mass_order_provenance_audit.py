#!/usr/bin/env python3
"""Audit the coupling-order convention in the flagship exotic-mass certificate.

The parent source says:
  "searched through order five, i.e. A B n^k for k <= 3"
and stores ORDERS_SEARCHED=[2,3,4,5], but its prose says the support is only
"through order four" and that orders five to eight remain.

The orbifolder manual resolves the semantic convention:
  auto create mass matrix(A B) ... max order(X)
specifies the maximal order X IN THE SINGLET FIELDS whose VEVs generate M_ij.

Thus a mass operator A B n^k has:
  k singlet insertions,
  total superpotential field order = 2+k.

Therefore k<=3 is total order <=5.  Under the parent artifact's own stated
measurement provenance, order five WAS searched.  Since the committed support
matrix contains only entries labelled 3 or 4 and no entry labelled 5, it
reports no new support first appearing at total order five.

This is a provenance/terminology repair, not a rerun of orbifolder.  It is
conditional on the parent comment truthfully describing the actual generation
range.  A future reproducibility packet should store the literal orbifolder
command/config and raw coupling list.
"""
from __future__ import annotations
import json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/w33_flagship_mass_order_provenance_audit.json'
SRC=ROOT/'analysis/the_w33_flagship_exotics_decouple_at_order_four.py'

def main(write=True):
    src=SRC.read_text()
    assert 'searched through order five, i.e. A B n^k for k <= 3' in src
    assert 'ORDERS_SEARCHED = [2, 3, 4, 5]' in src
    parent=json.loads((ROOT/'data/w33_flagship_exotics_decouple.json').read_text())
    assert parent['ordersSearched']==[2,3,4,5]

    # Recover all nonzero digit labels in the committed supports from source
    # literals, then inspect the explicit parent support artifact where needed.
    # Parent summary only stores ranks, so source is the authoritative support.
    block=src.split('SECTORS = {',1)[1].split('ORDERS_SEARCHED',1)[0]
    labels={int(x) for x in re.findall(r'(?<!\\d)([1-9])(?!\\d)', block)}
    # Restrict to coupling-order digits visible in support definitions.
    order_labels={x for x in labels if x in {2,3,4,5,6,7,8}}
    assert 3 in order_labels and 4 in order_labels and 5 not in order_labels

    out={
      'schema':'w33.flagship_mass_order_provenance_audit.v1',
      'status':'PASS_COMMITTED_PROVENANCE_IMPLIES_ORDER5_SEARCHED',
      'parent':'analysis/the_w33_flagship_exotics_decouple_at_order_four.py',
      'orbifolder_semantics':{
        'manual_command':'auto create mass matrix(A B) ... max order(X)',
        'manual_meaning':'X is the maximal order in singlet fields whose VEVs generate the mass-matrix entry',
        'mass_operator':'A B n^k',
        'total_field_order':'2+k'},
      'parent_metadata':{
        'comment':'searched through order five, i.e. A B n^k for k <= 3',
        'ordersSearched':[2,3,4,5],
        'support_order_labels_present':sorted(order_labels),
        'order5_entries_present':False},
      'conclusion':'If the parent comment accurately records the executed coupling-generation range, total order five was already searched and added no new support. The remaining untested range is total orders 6-8, not 5-8.',
      'provenance_boundary':'This audit does not rerun orbifolder. The repository should preserve the raw command/config and coupling list to remove the remaining provenance dependence.',
      'external_reference':'Nilles, Ramos-Sanchez, Vaudrevange, Wingerter, The Orbifolder, Comput.Phys.Commun.183 (2012) 1363-1380, Appendix B.2.5.',
      'checks':{
        'parent_says_k_le_3':True,
        'parent_ordersSearched_through_5':True,
        'orbifolder_k_to_total_order_relation':'total=2+k',
        'no_committed_order5_support_entries':True}}
    if write:OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2));return out

if __name__=='__main__':main(True)
