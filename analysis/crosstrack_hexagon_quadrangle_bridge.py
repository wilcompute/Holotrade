#!/usr/bin/env python3
"""
Reading the other track's Pass 10453-10548, and what does and does not carry
over to the quadrangle side.

The Theory-of-Everything track spent Passes 10453-10548 on split Cayley
hexagons, F4/F9 polarization and 27-state carriers.  Two of their results
touch this repository's W(3,3) work directly.  One extends cleanly, one looks
like a bridge and is not.  Both are recorded, because a defused bridge is
worth as much as a live one -- it stops someone building on a coincidence.

----------------------------------------------------------------------
1. THE BETTI COMPANION.  Extends cleanly.
----------------------------------------------------------------------

Their Pass 10501-10516 proves beta1(Levi(H(q))) = q^6 for every split Cayley
hexagon, and uses it to identify H1(Levi(H4); F2) with F2[V2] as a C13-module.
The quadrangle case is the same one-line count.  A generalized quadrangle of
order (s,t) has (s+1)(st+1) points and (t+1)(st+1) lines, so its Levi graph
has

    V = (st+1)(s+t+2),      E = (s+1)(t+1)(st+1),

and it is connected, so

    beta1 = E - V + 1 = (st+1)[(s+1)(t+1) - (s+t+2)] + 1
          = (st+1)(st-1) + 1
          = (st)^2.

For W(3,3) that is 81 = 3^4, checked directly against the repository's own
incidence structure and not only against the formula.

The uniform reading: for a generalized 2m-gon of order (q,q),
beta1(Levi) = q^(2m).  Quadrangles (m=2) give q^4, hexagons (m=3) give q^6 --
their theorem.  This is elementary, an Euler characteristic of a connected
bipartite graph, and is recorded as the quadrangle companion to their
computation rather than as a discovery of ours.

----------------------------------------------------------------------
2. THE NINE-TRIPLE ARCHITECTURE.  Looks like a bridge.  Is not.
----------------------------------------------------------------------

Their Pass 10477-10484 certifies "a canonical nine-triple organization of the
27 states", arising from the Wilson 13:6 normalizer acting on H(4): a
105-state C13 quotient, then a 27-state C6 orbit quotient whose C105 torsor
factors as C3 x C35, forcing nine triples.

Independently, and from nothing but minimum blocking sets, this repository's
centre theorem produces the same shape.  Every minimum blocker of W(3,3) has
a centre p that it avoids, and relative to the rank-3 shell 1 + 12 + 27
around p it takes 8 of the 12 collinear points and exactly 3 of the 27
others.  There are 9 blockers per centre.  Verified here: those 9 triples are
pairwise disjoint, each is a coclique, and together they PARTITION the 27 --
for every one of the 40 centres.  Nine triples on 27 states, canonically, with
no choices made.

That is a genuine structural fact and it is a tempting bridge.  It is not one.

The far-27 graph has degree 8, lambda = 1, mu in {0,3}, 36 triangles and four
lines of size three through each point.  It carries at least 200,000 distinct
partitions into nine disjoint 3-cocliques -- the enumeration was capped there,
so the true count is larger.  A "nine-triple organization of 27" is therefore
a common architecture, not a rare one, and two constructions landing on that
shape is close to no evidence that they land on the same object.

The honest statement is the one their own certificates use for exactly this
situation: matching carrier architecture is certified, objectwise
identification is rejected without an explicit intertwiner.  Here there is not
even a matching adjacency to compare -- their Pass 10477-10484 explicitly
rejects graph-isomorphism to H27 or Schlaefli for their own quotient.

What survives is narrower and still worth having: the 360 minimum blockers of
W(3,3) select exactly 40 of those many partitions, one per centre, with no
choices.  That canonicity is the content; the 9x3 shape is not.
"""

import itertools as it
import json
import os
import subprocess
import sys

ROOT = r"C:\Repos\Holotrade"
N = 40
PARTITION_CAP = 200000


def load():
    out = subprocess.run(
        ["node", "-e",
         "global.window=global;"
         "const S=require('./js/substrate.js');"
         "const R=require('./analysis/tensor_blocking_reformulation.js');"
         "const a=[];for(let i=0;i<40;i++){const r=[];"
         "for(let j=0;j<40;j++)r.push(i!==j&&S.isAdjacent(i,j)?1:0);a.push(r);}"
         "process.stdout.write(JSON.stringify({adj:a,"
         "lines:S.LINES.map(l=>[...l].sort((x,y)=>x-y)),"
         "blockers:R.minimumBlockers().map(b=>[...b].sort((x,y)=>x-y))}));"],
        cwd=ROOT, capture_output=True, text=True)
    if out.returncode:
        sys.exit("node failed: " + out.stderr[:600])
    d = json.loads(out.stdout)
    return d["adj"], d["lines"], d["blockers"]


def betti_table():
    rows = []
    for s, t in [(2, 2), (3, 3), (2, 4), (4, 2), (3, 9), (4, 4), (5, 5)]:
        V = (s * t + 1) * (s + t + 2)
        E = (s + 1) * (t + 1) * (s * t + 1)
        rows.append({"s": s, "t": t, "V": V, "E": E,
                     "beta1": E - V + 1, "stSquared": (s * t) ** 2,
                     "matches": E - V + 1 == (s * t) ** 2})
    return rows


def main():
    adj, lines, B = load()
    pencil = {p: frozenset(li for li, L in enumerate(lines) if p in L)
              for p in range(N)}
    by_pencil = {v: k for k, v in pencil.items()}
    cent = [by_pencil[frozenset(li for li, L in enumerate(lines)
                                if len(set(b) & set(L)) == 2)] for b in B]

    print("CROSS-TRACK: HEXAGON RESULTS AND THE QUADRANGLE SIDE")
    print("=" * 70)
    print()
    print("1. BETTI COMPANION -- extends cleanly")
    print("   their Pass10501-10516: beta1(Levi(H(q))) = q^6")
    print("   quadrangle companion : beta1(Levi(GQ(s,t))) = (st)^2")
    rows = betti_table()
    for r in rows:
        print("     (s,t)=(%d,%d)  V=%4d E=%4d  beta1=%5d  (st)^2=%5d  %s"
              % (r["s"], r["t"], r["V"], r["E"], r["beta1"], r["stSquared"],
                 "ok" if r["matches"] else "MISMATCH"))
    # direct check against the repository's own incidence structure
    V, E = 80, sum(len(L) for L in lines)
    print("   repo W(3,3) Levi: V=%d E=%d beta1=%d  (= 3^4)" % (V, E, E - V + 1))
    print("   uniform: generalized 2m-gon of order (q,q) has beta1 = q^(2m)")
    print()

    print("2. NINE TRIPLES ON 27 -- looks like a bridge, is not")
    ok_all = True
    for p in range(N):
        near = {q for li in pencil[p] for q in lines[li]} - {p}
        far = set(range(N)) - {p} - near
        fam = [set(b) & far for b, c in zip(B, cent) if c == p]
        flat = [x for s_ in fam for x in s_]
        if not (len(fam) == 9 and all(len(s_) == 3 for s_ in fam)
                and len(set(flat)) == 27 and set(flat) == far):
            ok_all = False
    print("   at every centre, the 9 blockers' far-parts partition the 27:", ok_all)

    p0 = 0
    near = {q for li in pencil[p0] for q in lines[li]} - {p0}
    far = sorted(set(range(N)) - {p0} - near)
    sub = [[adj[a][b] for b in far] for a in far]
    deg = {sum(r) for r in sub}
    lam, mu = set(), set()
    for i, j in it.combinations(range(27), 2):
        c = sum(1 for k in range(27) if sub[i][k] and sub[j][k])
        (lam if sub[i][j] else mu).add(c)
    tri = sum(1 for t in it.combinations(range(27), 3)
              if sub[t[0]][t[1]] and sub[t[0]][t[2]] and sub[t[1]][t[2]])
    print("   far-27 graph: degree %s, lambda %s, mu %s, %d triangles"
          % (sorted(deg), sorted(lam), sorted(mu), tri))

    trip = [t for t in it.combinations(range(27), 3)
            if not (sub[t[0]][t[1]] or sub[t[0]][t[2]] or sub[t[1]][t[2]])]
    byfirst = {}
    for t in trip:
        byfirst.setdefault(t[0], []).append(t)
    count = [0]

    def cover(used):
        if count[0] >= PARTITION_CAP:
            return
        if len(used) == 27:
            count[0] += 1
            return
        lo = min(set(range(27)) - used)
        for t in byfirst.get(lo, ()):
            if not (set(t) & used):
                cover(used | set(t))
    cover(frozenset())
    capped = count[0] >= PARTITION_CAP
    print("   3-cocliques: %d;  partitions into nine disjoint triples: %d%s"
          % (len(trip), count[0], "+ (capped)" if capped else ""))
    print()
    print("   ==> a nine-triple organization of 27 is COMMON, not rare, so the")
    print("       shape matching their Pass10477-10484 carrier is close to no")
    print("       evidence of a shared object. Not claimed as a bridge.")
    print("       What survives: the 360 blockers select exactly 40 of those")
    print("       partitions, one per centre, canonically. That is the content.")

    if "--write" in sys.argv:
        out = os.path.join(ROOT, "data", "crosstrack_hexagon_quadrangle.json")
        with open(out, "w") as fh:
            json.dump({
                "schema": "holotrade.crosstrack-hexagon-quadrangle.v1",
                "bettiCompanion": {
                    "theirs": "beta1(Levi(H(q))) = q^6, Pass10501-10516",
                    "ours": "beta1(Levi(GQ(s,t))) = (st)^2",
                    "w33": 81,
                    "uniform": "generalized 2m-gon of order (q,q): beta1 = q^(2m)",
                    "table": rows,
                    "novelty": "elementary Euler characteristic; recorded as "
                               "the quadrangle companion, not a discovery",
                },
                "nineTriples": {
                    "theirs": "canonical nine-triple organization of 27 states, "
                              "Pass10477-10484, from the Wilson 13:6 normalizer",
                    "ours": "the 9 minimum blockers at each centre partition the "
                            "far-27 into 9 disjoint 3-cocliques, at all 40 centres",
                    "partitionsAtEveryCentre": ok_all,
                    "far27": {"degree": sorted(deg), "lambda": sorted(lam),
                              "mu": sorted(mu), "triangles": tri},
                    "rivalPartitions": count[0],
                    "rivalPartitionsCapped": capped,
                    "isABridge": False,
                    "why": "a nine-triple organization of 27 is a common "
                           "architecture -- at least 200,000 exist on this graph "
                           "alone -- so matching the shape is close to no "
                           "evidence of a shared object",
                    "whatSurvives": "the 360 minimum blockers select exactly 40 "
                                    "of those partitions, one per centre, with "
                                    "no choices made",
                },
                "boundary": "no objectwise identification with any other track's "
                            "carrier is claimed, in line with their own practice "
                            "of rejecting identification without an intertwiner",
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(out, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
