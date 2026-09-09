"""Interpret existing exact duals as point potentials and optimal support faces."""
from fractions import Fraction as F
from pathlib import Path
from collections import Counter
import json
import sympy as s
from signed_pencil_sampling_witness import check_export


def analyze(row,lines):
    y=list(map(F,row['fractional']['dual']));x=list(map(F,row['fractional']['primal']));e=row['excess']
    h=[sum(y[j] for j,line in enumerate(lines) if p in line) for p in range(40)]
    assert all(abs(v)<=1 for v in h)
    assert all(abs(a)==a*b for a,b in zip(x,h))
    active=[p for p in range(40) if abs(h[p])==1]
    B=s.Matrix([[int(p in line) for p in active] for line in lines]);rank=B.rank()
    # Any optimum must vanish off active and have sign h on active:
    # ||z||1-y.Bz = sum_p (|z_p|-h_p z_p), a sum of nonnegative terms.
    positive=[p for p in active if h[p]==1];negative=[p for p in active if h[p]==-1]
    adjacency=lambda a,b:any(a in line and b in line for line in lines)
    norm=F(row['fractional']['l1']);k=F(sum(e),4);margin=norm-k
    assert margin==2*row['depth']
    return dict(mass=row['mass'],point_potential=list(map(str,h)),potential_histogram=dict(Counter(map(str,h))),
        positive_saturated_points=positive,negative_saturated_points=negative,
        forced_zero_points=[p for p in range(40) if p not in active],
        negative_induced_degrees=[sum(adjacency(p,q) for q in negative if p!=q) for p in negative],
        active_column_rank=rank,optimal_affine_dimension_upper_bound=len(active)-rank,
        cone_separation_margin=str(margin),unavoidable_negative_mass=str(margin/2),
        theorem='Every real l1 minimizer is zero at unsaturated points and sign-constrained at saturated points. Nullity bounds the optimal face dimension; positivity may reduce it.')

if __name__=='__main__':
    source=Path(__file__).with_name('signed_pencil_sampling_certificate.json');data=json.loads(source.read_text())
    check_export(data)
    rows=[analyze(row,data['lines']) for row in data['rows']]
    result=dict(status='PASS',source=source.name,rows=rows,scope='Two existing representatives; exact rational dual interpretation, not a new orbit census')
    Path(__file__).with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
