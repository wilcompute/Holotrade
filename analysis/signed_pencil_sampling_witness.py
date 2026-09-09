"""Export exact signed preimages and audit integer/fractional sampling costs.

Reuses the existing geometry. Depth lower bounds use exact pencil-cover search,
not solver status or a rerun of the full mass-16 census. LP results are admitted
only after exact rational primal/dual checks.
"""
from collections import Counter
from functools import lru_cache
from fractions import Fraction as F
from itertools import combinations, product
import json
from pathlib import Path
from the_mass12_census_is_complete_and_has_one_exception import geometry


def build_geometry():
    pts,idx,sf,lines=geometry()
    thru=tuple(tuple(i for i,L in enumerate(lines) if p in L) for p in range(40))
    pencils=tuple(tuple(int(p in L) for L in lines) for p in range(40))
    assert len(lines)==40 and all(len(t)==4 for t in thru)
    return lines,thru,pencils


def cover_solver(lines,thru):
    @lru_cache(maxsize=100000)
    def cover(e):
        if any(v<0 for v in e) or sum(e)%4:
            return None
        if not any(e):
            return ()
        # Every cover must use one of the four points on a positive line.
        choices=[]
        for i,v in enumerate(e):
            if v:
                cs=[p for p in lines[i] if all(e[j]>0 for j in thru[p])]
                if not cs:
                    return None
                choices.append(cs)
        for p in min(choices,key=len):
            rest=list(e)
            for j in thru[p]:
                rest[j]-=1
            found=cover(tuple(rest))
            if found is not None:
                return (p,)+found
        return None
    return cover


def depth_at_most_one(e,pencils,cover):
    pos=cover(e)
    if pos is not None:
        return 0,pos,()
    for p,pen in enumerate(pencils):
        pos=cover(tuple(a+b for a,b in zip(e,pen)))
        if pos is not None:
            return 1,pos,(p,)
    return None


def signed_vector(pos,neg):
    x=[0]*40
    for p in pos:x[p]+=1
    for p in neg:x[p]-=1
    return tuple(x)


def discover(lines,thru,pencils,cover):
    def excess(pos,neg):
        x=signed_vector(pos,neg)
        return tuple(sum(x[p] for p in L) for L in lines),x
    # One negative pencil: choose one other point on each of its four lines.
    first=None
    for pos in product(*[tuple(p for p in lines[L] if p!=0) for L in thru[0]]):
        e,x=excess(pos,(0,))
        if cover(e) is None:
            first=(e,x,1)
            break
    assert first is not None
    # Two noncollinear negatives. Two common neighbours cover four of the
    # eight incident lines; choose one positive on each remaining line.
    neighbours=[set(p for L in thru[a] for p in lines[L])-{a} for a in range(40)]
    for b in range(1,40):
        if b in neighbours[0]:continue
        common=neighbours[0]&neighbours[b]
        for shared in combinations(sorted(common),2):
            neg=(0,b)
            covered={L for p in shared for L in thru[p]}
            remaining=[L for p in neg for L in thru[p] if L not in covered]
            assert len(remaining)==4
            choices=[tuple(p for p in lines[L] if p not in neg) for L in remaining]
            for tail in product(*choices):
                e,x=excess(shared+tail,neg)
                if min(e)<0 or max(e)>2:continue
                if depth_at_most_one(e,pencils,cover) is None:
                    return first,(e,x,2)
    raise AssertionError('constructive depth-two search exhausted')


def fractional_certificate(e,lines):
    import numpy as np
    from scipy.optimize import linprog
    B=np.array([[int(p in L) for p in range(40)] for L in lines])
    result=linprog(np.ones(80),A_eq=np.concatenate((B,-B),axis=1),b_eq=e,
                   bounds=(0,None),method='highs')
    if not result.success:raise AssertionError(result.message)
    x=[F(float(result.x[p]-result.x[p+40])).limit_denominator(100000) for p in range(40)]
    y=[F(float(v)).limit_denominator(100000) for v in result.eqlin.marginals]
    assert all(sum(x[p] for p in L)==e[i] for i,L in enumerate(lines))
    assert all(abs(sum(y[i] for i,L in enumerate(lines) if p in L))<=1 for p in range(40))
    primal=sum(map(abs,x))
    dual=sum(v*w for v,w in zip(y,e))
    assert primal==dual
    return dict(primal=[str(v) for v in x],dual=[str(v) for v in y],l1=str(primal))


def audit(e,x,depth,lines,thru,pencils,cover):
    k=sum(e)//4
    assert sum(e)==4*k and sum(x)==k
    assert tuple(sum(x[p] for p in L) for L in lines)==e
    assert sum(-v for v in x if v<0)==depth
    if depth==1:assert cover(e) is None
    if depth==2:assert depth_at_most_one(e,pencils,cover) is None
    norm=sum(map(abs,x))
    assert norm==k+2*depth
    # Exact signed sampler, all 40 indicator observables plus alternating signs.
    observables=[tuple(int(i==j) for i in range(40)) for j in range(40)]
    observables.append(tuple((-1)**i for i in range(40)))
    for f in observables:
        mean=second=F(0)
        for p,v in enumerate(x):
            if not v:continue
            for L in thru[p]:
                prob=F(abs(v),4*norm)
                estimate=F(norm,k)*(1 if v>0 else -1)*f[L]
                mean+=prob*estimate
                second+=prob*estimate**2
        assert mean==sum(F(v,4*k)*w for v,w in zip(e,f))
        assert second<=F(norm,k)**2
    frac=fractional_certificate(e,lines)
    return dict(mass=4*k,depth=depth,excess=list(e),integer_preimage=list(x),
                histogram=dict(Counter(e)),integer_l1=norm,
                signed_sampler_second_moment_bound=str(F(norm,k)**2),
                exact_observables_checked=len(observables),fractional=frac,
                l1_integrality_gap=str(F(norm)/F(frac['l1'])),
                exact_depth_lower_bound='exhaustive positive-pencil covers for all smaller negative mass')


def verify():
    lines,thru,pencils=build_geometry()
    cover=cover_solver(lines,thru)
    objects=discover(lines,thru,pencils,cover)
    rows=[audit(e,x,d,lines,thru,pencils,cover) for e,x,d in objects]
    # Controls test both positive cover and depth-one reconstruction.
    assert cover(pencils[0]) is not None
    assert depth_at_most_one(objects[0][0],pencils,cover)[0]==1
    return dict(schema='holotrade.signed-pencil-sampler.v1',status='PASS',
                lines=[list(L) for L in lines],rows=rows,
                boundary='Two exact representatives, not a new census or blocker; fractional LP claims include exact rational primal/dual certificates')


def check_export(row):
    lines,thru,pencils=build_geometry()
    assert row['lines']==[list(L) for L in lines]
    assert len(row['rows'])==2
    for item in row['rows']:
        e=item['excess'];x=item['integer_preimage'];depth=item['depth']
        assert len(e)==len(x)==40
        assert all(type(v) is int for v in e+x) and min(e)>=0
        k=sum(e)//4
        assert item['mass']==sum(e)==4*k
        assert all(sum(x[p] for p in L)==e[i] for i,L in enumerate(lines))
        assert sum(x)==k and sum(-v for v in x if v<0)==depth
        norm=sum(map(abs,x))
        assert norm==item['integer_l1']==k+2*depth
        assert F(item['signed_sampler_second_moment_bound'])==F(norm,k)**2
        f=item['fractional'];a=list(map(F,f['primal']));y=list(map(F,f['dual']))
        assert len(a)==len(y)==40
        assert all(sum(a[p] for p in L)==e[i] for i,L in enumerate(lines))
        assert all(abs(sum(y[i] for i,L in enumerate(lines) if p in L))<=1 for p in range(40))
        optimum=sum(map(abs,a))
        assert optimum==sum(v*w for v,w in zip(y,e))==F(f['l1'])
        assert F(item['l1_integrality_gap'])==F(norm)/optimum
        assert optimum==norm  # Also proves the integer depth is minimal.
    return True


def mutation_checks(row):
    import copy
    for key in ('integer_preimage','dual','primal'):
        bad=copy.deepcopy(row)
        target=bad['rows'][0] if key=='integer_preimage' else bad['rows'][0]['fractional']
        target[key][0]=int(target[key][0])+7
        try:check_export(bad)
        except AssertionError:pass
        else:raise AssertionError('corrupt '+key+' was accepted')
    return 3


if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true')
    args=ap.parse_args()
    if args.check:
        row=json.loads(Path(__file__).with_name('signed_pencil_sampling_certificate.json').read_text())
        check_export(row)
        print(json.dumps(dict(status='PASS',mutation_rejections=mutation_checks(row),solver_required=False)))
        raise SystemExit(0)
    row=verify()
    check_export(row)
    mutation_checks(row)
    Path(__file__).with_name('signed_pencil_sampling_certificate.json').write_text(json.dumps(row,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in row.items() if k!='lines'},indent=2))
