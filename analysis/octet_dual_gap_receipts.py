"""Solver-free verification of dual-certified escape and optimum receipts.
Uses the existing frozen radius-two traps; does not claim to discover them.
"""
from fractions import Fraction as F
from pathlib import Path
from itertools import combinations_with_replacement
import json,hashlib
import signed_pencil_sampling_witness as sp
import the_kernel_is_spanned_by_octet_differences as kg
HERE=Path(__file__).resolve().parent


def digest(move):return 'sha256:'+hashlib.sha256(json.dumps(list(move),separators=(',',':')).encode()).hexdigest()
def image(x,lines):return [sum(x[p] for p in line) for line in lines]
def negative(x):return sum(-v for v in x if v<0)


def verify(receipt,lines):
    start=receipt['start'];end=receipt['end'];move=receipt['move'];e=receipt['lineImage'];y=list(map(F,receipt['dual']))
    if any(len(v)!=40 for v in (start,end,move,e,y)):raise ValueError('wrong dimensions')
    if any(type(v) is not int for row in (start,end,move,e) for v in row):raise ValueError('integer vectors required')
    if receipt['moveDigest']!=digest(move):raise ValueError('wrong move digest')
    if [a+b for a,b in zip(start,move)]!=end or image(start,lines)!=e or image(end,lines)!=e:raise ValueError('wrong transition or fiber')
    h=[sum(y[j] for j,L in enumerate(lines) if p in L) for p in range(40)]
    if any(abs(v)>1 for v in h):raise ValueError('dual infeasible')
    gamma=sum(a*b for a,b in zip(y,e));k=F(sum(e),4);bound=(gamma-k)/2
    gap_before=sum(map(abs,start))-gamma;gap_after=sum(map(abs,end))-gamma
    if negative(end)>=negative(start):raise ValueError('not strict descent')
    if gap_after!=0:raise ValueError('endpoint not certified optimum')
    assert gap_before==sum(abs(a)-a*b for a,b in zip(start,h))
    return dict(status='CERTIFIED_OPTIMUM',negative_mass_lower_bound=str(bound),
                initial_negative_mass=negative(start),final_negative_mass=negative(end),
                gap_before=str(gap_before),gap_after=str(gap_after))


def radius_two(lines):
    pts,sf,iso,hyp,perp=kg.geometry();assert tuple(map(tuple,iso))==tuple(map(tuple,lines))
    pairs={frozenset((frozenset(L),frozenset(perp(L)))) for L in hyp};moves=[]
    for pair in pairs:
        a,b=sorted(pair,key=lambda z:tuple(sorted(z)));v=tuple(int(p in a)-int(p in b) for p in range(40));moves.extend((v,tuple(-x for x in v)))
    ball=set(moves)
    ball.update(tuple(a+b for a,b in zip(u,v)) for u,v in combinations_with_replacement(moves,2))
    ball.discard((0,)*40);assert len(ball)==4140
    return ball


def build():
    lines,_,_=sp.build_geometry();traps=json.loads((HERE/'octet_circuit_decoder_trap_certificate.json').read_text())
    circuit=json.loads((HERE/'octet_single_circuit_obstruction_certificate.json').read_text())['circuit']['vector']
    ball=radius_two(lines);rows=[]
    for trap in traps['traps']:
        start=trap['witness'];move=[trap['orientation']*x for x in circuit];end=[a+b for a,b in zip(start,move)]
        assert all(negative([a+b for a,b in zip(start,v)])>=negative(start) for v in ball)
        dual=sp.fractional_certificate(trap['lineImage'],lines)['dual']
        receipt=dict(start=start,end=end,move=move,moveDigest=digest(move),lineImage=trap['lineImage'],dual=dual)
        result=verify(receipt,lines);assert result['final_negative_mass']==1
        rows.append(dict(receipt=receipt,result=result))
    return dict(schema='holotrade.octet-dual-gap-receipts.v1',status='PASS',rows=rows,radius_two_endpoints_checked=2*len(ball),
                provenance=['octet_circuit_decoder_trap_certificate.json','octet_single_circuit_obstruction_certificate.json'],
                boundary='New portable rational stopping certificate for existing escapes; no new trap, Graver completeness, hardware or quantum speedup claim.')


def audit_export(data):
    from copy import deepcopy
    lines,_,_=sp.build_geometry()
    for row in data['rows']:assert verify(row['receipt'],lines)==row['result']
    for key in ('end','dual','moveDigest'):
        bad=deepcopy(data['rows'][0]['receipt'])
        if key=='moveDigest':bad[key]='sha256:bad'
        else:bad[key][0]=int(F(bad[key][0]))+100
        try:verify(bad,lines)
        except ValueError:pass
        else:raise AssertionError('corrupt receipt accepted')
    return 3

if __name__=='__main__':
    import sys
    path=Path(__file__).with_suffix('.json')
    data=json.loads(path.read_text()) if '--check' in sys.argv else build()
    assert audit_export(data)==3
    if '--check' not in sys.argv:path.write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps(dict(status='PASS',rows=[r['result'] for r in data['rows']],mutation_rejections=3),indent=2))
