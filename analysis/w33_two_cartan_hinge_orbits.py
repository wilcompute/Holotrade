#!/usr/bin/env python3
"""Classify W(3,3) two-Cartan hinges under PSp(4,3).

A hinge is a pair of W33 lines (Pauli Cartans) meeting in one projective point.
A decorated hinge additionally chooses one nonshared projective point on each
Cartan.  The frozen net-three heterotic witness from
w33_pauli_geometry_of_heterotic_witness.json is tested against these orbits.
"""
import itertools, json
from collections import defaultdict, deque
from pathlib import Path
p=3
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data'/'w33_two_cartan_hinge_orbits.json'

def add(a,b): return tuple((x+y)%p for x,y in zip(a,b))
def smul(c,a): return tuple((c*x)%p for x in a)
def symp(v,w):
    x,z,u,t=v; y,s,r,k=w
    return (z*y-s*x+t*r-k*u)%3

def canon(v):
    v=tuple(x%3 for x in v)
    if not any(v): raise ValueError
    j=next(i for i,x in enumerate(v) if x)
    inv=1 if v[j]==1 else 2
    return tuple((inv*x)%3 for x in v)

def main(write=True):
    V=[v for v in itertools.product(range(3), repeat=4) if any(v)]
    P=sorted({canon(v) for v in V}); assert len(P)==40
    pindex={v:i for i,v in enumerate(P)}
    lines=set()
    for a,b in itertools.combinations(P,2):
        if symp(a,b)!=0: continue
        pts=frozenset(canon(add(smul(x,a),smul(y,b))) for x,y in itertools.product(range(3),repeat=2) if x or y)
        assert len(pts)==4; lines.add(pts)
    lines=sorted(lines,key=lambda L:sorted(L)); assert len(lines)==40
    lindex={L:i for i,L in enumerate(lines)}
    through=defaultdict(list)
    for i,L in enumerate(lines):
        for q in L: through[q].append(i)
    assert set(map(len,through.values()))=={4}

    hinges=[]
    for q in P:
        for a,b in itertools.combinations(through[q],2): hinges.append((q,a,b))
    assert len(hinges)==240
    D=[]
    for q,a,b in hinges:
        A=lines[a]-{q}; B=lines[b]-{q}
        for x in sorted(A):
            for y in sorted(B):
                assert symp(x,y)!=0; D.append((q,a,b,x,y))
    assert len(D)==2160

    def transvection(v,x): return canon(add(x,smul(symp(x,v),v)))
    gens=[]
    for v in P:
        perm=tuple(pindex[transvection(v,x)] for x in P)
        if perm not in gens: gens.append(perm)
    assert len(gens)==40
    def act_point(perm,x): return P[perm[pindex[x]]]
    def act_line(perm,li): return lindex[frozenset(act_point(perm,x) for x in lines[li])]
    def act_h(perm,h):
        q,a,b=h; q2=act_point(perm,q); aa,bb=sorted((act_line(perm,a),act_line(perm,b))); return (q2,aa,bb)
    def normalize_d(t):
        q,a,b,x,y=t
        return t if a<b else (q,b,a,y,x)
    def act_d(perm,t):
        q,a,b,x,y=t
        return normalize_d((act_point(perm,q),act_line(perm,a),act_line(perm,b),act_point(perm,x),act_point(perm,y)))

    h0=hinges[0]; seen={h0}; dq=deque([h0])
    while dq:
        h=dq.popleft()
        for g in gens:
            z=act_h(g,h)
            if z not in seen: seen.add(z); dq.append(z)
    assert len(seen)==240
    d0=normalize_d(D[0]); seenD={d0}; dq=deque([d0])
    while dq:
        h=dq.popleft()
        for g in gens:
            z=act_d(g,h)
            if z not in seenD: seenD.add(z); dq.append(z)
    assert len(seenD)==2160

    witness=json.loads((ROOT/'data'/'w33_pauli_geometry_of_heterotic_witness.json').read_text())
    wlabels=[tuple(v) for v in witness['pauli_labels_x1z1x2z2']]
    wp=[canon(v) for v in wlabels]
    shared=next(q for q in wp if all(symp(q,x)==0 for x in wp if x!=q))
    outer=[x for x in wp if x!=shared]; assert symp(*outer)!=0
    L1=next(i for i,L in enumerate(lines) if shared in L and outer[0] in L)
    L2=next(i for i,L in enumerate(lines) if shared in L and outer[1] in L)
    wdec=normalize_d((shared,L1,L2,outer[0],outer[1])); assert wdec in seenD

    idp=tuple(range(40)); Gset={idp}; qg=deque([idp])
    def compose(a,b): return tuple(a[b[i]] for i in range(40))
    while qg:
        a=qg.popleft()
        for g in gens:
            z=compose(g,a)
            if z not in Gset: Gset.add(z); qg.append(z)
    assert len(Gset)==25920
    stab_h=sum(act_h(g,h0)==h0 for g in Gset)
    stab_d=sum(act_d(g,d0)==d0 for g in Gset)
    assert stab_h==108 and stab_d==12

    out={
      'schema':'w33.two_cartan_hinge_orbits.v1','status':'PASS',
      'headline':'All W33 two-Cartan hinges form one PSp(4,3) orbit, and all hinges decorated by one nonshared point on each Cartan form one orbit of size 2160. The frozen net-three heterotic witness lies in this unique decorated-hinge orbit.',
      'geometry':{'projective_points':40,'W33_lines_as_pauli_cartans':40,'lines_through_point':4,'undecorated_hinges':240,'decorated_hinges':2160},
      'group':{'generated_by_projective_symplectic_transvections':True,'projective_group_order':len(Gset),'identification':'PSp(4,3)','undecorated_orbit_size':len(seen),'undecorated_stabilizer_order':stab_h,'decorated_orbit_size':len(seenD),'decorated_stabilizer_order':stab_d},
      'witness':{'pauli_labels_x1z1x2z2':[list(v) for v in wlabels],'projective_labels':[list(v) for v in wp],'shared_projective_point':list(shared),'outer_pair_symplectic_product_mod3':symp(*outer),'cartan_indices':[L1,L2],'decorated_hinge_in_unique_orbit':True},
      'consequence':'At the level of W33/PSp(4,3) incidence alone, the two-Cartan hinge of the net-three witness is not exceptional: every decorated hinge is symmetry-equivalent. Any selector for hypercharge or exotic removal must use additional data (orientation/phases, second-E8 data, lattice norms, or spectrum data), not the bare projective hinge orbit.',
      'checks':{'40_points':len(P)==40,'40_cartans':len(lines)==40,'240_undecorated_hinges':len(hinges)==240,'2160_decorated_hinges':len(D)==2160,'projective_symplectic_group_order_25920':len(Gset)==25920,'undecorated_single_orbit':len(seen)==len(hinges),'decorated_single_orbit':len(seenD)==len(D),'witness_in_decorated_orbit':wdec in seenD}
    }
    assert all(out['checks'].values())
    if write: OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2)); return out
if __name__=='__main__': main(True)
