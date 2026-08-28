#!/usr/bin/env python3
"""Exact structural reduction of the still-open |X|=111 tensor blocker case.

Let X be a depth-2 blocker on W(3,3)^2.  For a first-coordinate line L write
B_L for its row shadow (the union of the four fibres above L), s_L=|B_L| and
R_L for the number of leaves of X whose first coordinate lies on L.  Since
every B_L blocks all 40 second-coordinate lines, s_L>=tau_1=11.  Also
R_L>=s_L, with equality iff the four fibres on L are pairwise disjoint.

At |X|=111,

  sum_L R_L = 4|X| = 444,
  sum_L (s_L-11 + R_L-s_L) = 444-40*11 = 4.

Thus there are at most four non-clean rows, where clean means simultaneously
s_L=11 and R_L=s_L.  The same holds on columns.  Hence at least 36 rows and 36
columns are clean.

A clean shadow is one of the 360 minimum blockers.  If c_L is its centre, then
for every second-coordinate line M the tile occupancy is exactly

  |X cap (L x M)| = |B_L cap M| = 1 + [c_L in M].

For a clean column M with centre d_M the same tile occupancy is
1+[d_M in L].  Therefore on every clean x clean tile

  c_L in M  <=>  d_M in L.

This is the exact partial-duality condition inherited from the excluded 110
case.  At 111 there is a second constraint that a center-only relaxation misses.
Let r,c be the counts of clean rows/columns, and Dcc the number of clean-clean
tiles on which the common indicator above is one.  All 1600 product tiles have
occupancy at least one.  Each clean row forces four extra occupancies, each
clean column forces four, and Dcc is exactly the double-counted overlap.  Since
each leaf lies in 16 product tiles,

  16*111 >= 1600 + 4r + 4c - Dcc,

so

  Dcc >= 4r+4c-176 >= 112.

This kills the simplest apparent escape from the 110 self-duality obstruction.
If the four dirty lines on each side form the pencil through p and all 36 clean
shadows use centre p, clean-clean reciprocity holds vacuously (no clean line
contains p), but Dcc=0.  Equivalently the clean-clean, clean-dirty and
dirty-clean tile regions already force 1296+288+288=1872 incidences, exceeding
16*111=1776 before the 16 dirty-dirty tiles are counted.

The result does NOT yet prove tau_2>=112.  It proves that any 111 witness must
carry a dense, nondegenerate partial duality with at least 112 clean-clean
doubled incidences and must also satisfy the actual minimum-blocker/fibre
compatibility, not merely the center reciprocity equations.
"""
from __future__ import annotations
import itertools,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/tensor_111_near_duality_budget.json'
Q=3

def norm(v):
    i=next(k for k,x in enumerate(v) if x%3);z=pow(v[i]%3,-1,3)
    return tuple((z*x)%3 for x in v)
def form(u,v):return (u[0]*v[1]-u[1]*v[0]+u[2]*v[3]-u[3]*v[2])%3

def geometry():
    pts=sorted({norm(v) for v in itertools.product(range(3),repeat=4) if any(v)})
    idx={v:i for i,v in enumerate(pts)};lines=set()
    for a,b in itertools.combinations(range(40),2):
        if form(pts[a],pts[b]):continue
        S=set()
        for s,t in itertools.product(range(3),repeat=2):
            if s==t==0:continue
            S.add(idx[norm(tuple((s*pts[a][k]+t*pts[b][k])%3 for k in range(4)))])
        if len(S)==4:lines.add(tuple(sorted(S)))
    return sorted(lines)

def main():
    lines=geometry();assert len(lines)==40
    pls=[[] for _ in range(40)]
    for li,L in enumerate(lines):
        for p in L:pls[p].append(li)
    assert all(len(x)==4 for x in pls)

    size=111;total_line_fibre_count=4*size;baseline=40*11
    slack=total_line_fibre_count-baseline
    assert slack==4
    min_clean=40-slack;assert min_clean==36
    total_tile_occupancy=16*size;assert total_tile_occupancy==1776
    min_Dcc=4*min_clean+4*min_clean-(total_tile_occupancy-1600)
    assert min_Dcc==112

    # Explicit negative control for center-only reciprocity: dirty pencil at 0,
    # all clean centers 0.  No clean line contains 0, so reciprocity is true on
    # the 36x36 core, yet the occupancy lower bound is impossible.
    dirty=set(pls[0]);assert len(dirty)==4
    clean=set(range(40))-dirty;assert len(clean)==36
    assert all(0 not in lines[L] for L in clean)
    centre_only_reciprocity=all((0 in lines[M])==(0 in lines[L]) for L in clean for M in clean)
    assert centre_only_reciprocity
    regions={'clean_clean':36*36,'clean_dirty':36*4*2,'dirty_clean':4*36*2}
    forced=sum(regions.values());assert forced==1872 and forced>total_tile_occupancy

    # All integer partitions of the four axis-slack units, included so future
    # searches cover every possible excess/overlap profile rather than only
    # four size-12 shadows.
    parts=set()
    def rec(rem,last,out):
        if rem==0:parts.add(tuple(out));return
        for z in range(min(last,rem),0,-1):rec(rem-z,z,out+[z])
    rec(4,4,[])
    assert parts=={(4,),(3,1),(2,2),(2,1,1),(1,1,1,1)}

    out={
      'schema':'holotrade.tensor-111-near-duality-budget.v1','valid':True,
      'candidateSize':111,'axisSlackUnits':4,'axisSlackPartitions':[list(x) for x in sorted(parts,reverse=True)],
      'cleanShadow':{'definition':'shadow size 11 and no fibre overlap on that line','minimumPerAxis':36},
      'cleanCoreReciprocity':'for clean row L and clean column M: c_L in M iff d_M in L',
      'tileOccupancyBudget':{'total':1776,'baselineOnePerTile':1600,
        'formula':'Dcc >= 4r+4c-176','minimumDccAt36By36':112},
      'centerOnlyNegativeControl':{'dirtyLines':'four-line pencil through point 0','cleanCenters':'all point 0',
        'cleanCoreReciprocityHolds':True,'forcedTileOccupancyBeforeDirtyDirty':forced,
        'availableTotalTileOccupancy':1776,'impossible':True},
      'theorem':'Any 111-leaf tensor blocker has at least 36 clean shadows on each axis, exact center reciprocity on their core, and at least 112 clean-clean forced doubled tiles. The constant-center/pencil-deletion near-duality escape is impossible by tile-incidence count.',
      'boundary':'This does not yet exclude every dense partial-duality/blocker-label configuration at size 111. The certified tensor interval remains [111,115].'}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':'PASS','candidate':111,'clean_each':36,'Dcc_min':112,'constant_center_forced':1872}))
if __name__=='__main__':main()
