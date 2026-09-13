"""Export canonical geometry beside existing exact dual receipts for JS regression."""
from pathlib import Path
import json
from signed_pencil_sampling_witness import build_geometry
ROOT=Path(__file__).resolve().parent

def build():
    lines,_,_=build_geometry()
    receipts=json.loads((ROOT/'octet_dual_gap_receipts.json').read_text())
    assert receipts['status']=='PASS'
    return {'schema':'holotrade.octet-dual-transaction-fixture.v1','lines':[list(L) for L in lines],
            'receipts':[row['receipt'] for row in receipts['rows']],
            'source':'octet_dual_gap_receipts.json','boundary':'Existing mathematical witnesses; attestation tests use simulated verifier verdicts.'}

if __name__=='__main__':
    import sys
    result=build();path=Path(__file__).with_name('octet_dual_transaction_fixture.json')
    if '--check' in sys.argv:assert json.loads(path.read_text())==result
    else:path.write_text(json.dumps(result,indent=2)+'\n')
    print('Dual transaction fixture PASS')
