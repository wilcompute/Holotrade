#!/usr/bin/env python3
"""
The 216 is not 36 x 6 by arithmetic. It is a canonical principal 6-fibration
over the double-sixes, and its fibre is Schlafli's six letters.

WHAT WAS ONLY NUMERICAL.  7f0d0a3 identified the other track's "hidden common
36-state quotient" as the 36 spreads, by matching a stabiliser order of 720 and
an index of 36, and noted 216 = 36 x 6. Matching integers is how this repository
gets things wrong, so the map itself has to be built.

GROUP THEORY SAYS WHAT IT SHOULD BE.  The circuit stabiliser has order 120 and
the spread stabiliser 720, with 720/120 = 6. That is the index-six inclusion
S5 <= S6. If it is a real containment rather than an arithmetic coincidence,
each circuit's stabiliser lies in exactly one spread stabiliser and the
resulting map is canonical.

    circuit stabiliser order                      120
    spread stabilisers containing it              1        <- canonical
    that spread stabiliser's order                720
    index of the circuit stabiliser in it         6

BUILT BY TRANSPORT, not by brute force. Stabilisers conjugate, so the map is
equivariant; PSp(4,3) is transitive on the 216 and on the 36; hence every fibre
has the same size and it must be 216/36 = 6. Transporting circuit 0 to every
circuit and carrying its spread along:

    circuits mapped                      216 of 216
    independent of the transporting g    yes, no mismatches
    spreads hit                          36 of 36
    fibre sizes                          {6: 36}
    equivariance                         no violations

So the 216-state carrier is a PSp(4,3)-equivariant principal 6-fibration over
the 36 spreads, with fibre the coset space S6/S5.

AND THE FIBRE HAS A NAME.  BT810's Schlafli dictionary identifies the 36
spreads of W(3,3) with the 36 DOUBLE-SIXES of the cubic surface, and the
stabiliser of one is S6 acting naturally on six letters. The circuit stabiliser
is the point stabiliser S5 of that action. Therefore

    216 circuits  =  (double-six, letter) pairs,

the fibre being exactly Schlafli's six letters. What the other track's 36
copies of K(6,6) were showing is this bundle, seen through a correspondence.

THE ARCHITECTURE READING, which is why it is worth having. This is a TYPE
SYSTEM, and a derived one rather than a designed one: the type of a 216-state
is which double-six it lies over, and its tag is which of the six letters it
carries. Types are not a convention imposed on the carrier; they are the only
equivariant decomposition the carrier admits, because the fibration is
canonical -- there is exactly one spread stabiliser containing each circuit
stabiliser, so there is exactly one way to type a state.

That is what rtl/verify_w33_216_typed_microvm.ys was reaching for. It is a
formal harness for a module named "216 typed microvm" that was never written
(7f0d0a3 records it as an orphan). The type discipline it would need is the one
derived here, and it is forced.

SCOPE.  The fibration is verified in full -- unique containment, well-defined
under transport, all 36 fibres of size exactly 6, equivariance sampled clean.
The naming of the fibre as Schlafli's letters rests on BT810's spread /
double-six identification and on the standard degree-6 action of S6; it is a
dictionary entry, not a new computation. Nothing here is a hardware claim, and
no module is written. tau_2 is untouched.
"""

import collections
import itertools
import json
import os
import random
import sys

ROOT = r"C:\Repos\Holotrade"
Q = 3
N = 40


def main():
    import subprocess
    out = subprocess.run(
        ["node", "-e", "const {runGap}=require('./scripts/run-gap.js');const r=runGap('analysis/e8_pg34_sentinel_control_plane.g',{cwd:process.cwd(),quiet:true});const L=r.stdout.split(/\\r?\\n/);process.stdout.write(L.find(x=>x.startsWith('CIRCUITS|'))+'\\n'+L.find(x=>x.startsWith('SUPPORTS|')));"],
        cwd=ROOT, capture_output=True, text=True)
    if out.returncode:
        sys.exit("gap/node failed: " + out.stderr[:300])
    cl, sl = out.stdout.strip().split(chr(10))
    circuits = [tuple(int(x) - 1 for x in c.split(","))
                for c in cl.split("|")[1].split(";")]
    supports = [tuple(int(x) - 1 for x in s.split(","))
                for s in sl.split("|")[1].split(";")]

    def nm(v):
        i = next(k for k, x in enumerate(v) if x % Q)
        z = pow(v[i] % Q, -1, Q)
        return tuple((z * x) % Q for x in v)

    def form(u, v):
        return (u[0] * v[1] - u[1] * v[0] + u[2] * v[3] - u[3] * v[2]) % Q

    pts = sorted({nm(v) for v in itertools.product(range(Q), repeat=4)
                  if any(v)})
    idx = {v: i for i, v in enumerate(pts)}
    lines = set()
    for a, b in itertools.combinations(range(N), 2):
        if form(pts[a], pts[b]):
            continue
        S = set()
        for x in range(Q):
            for y in range(Q):
                if x == y == 0:
                    continue
                S.add(idx[nm(tuple((x * pts[a][k] + y * pts[b][k]) % Q
                                   for k in range(4)))])
        if len(S) == 4:
            lines.add(tuple(sorted(S)))
    lines = sorted(lines)
    LS = [set(L) for L in lines]
    spreads = []

    def ext(cur, cov, start):
        if len(cur) == 10:
            if len(cov) == 40:
                spreads.append(frozenset(cur))
            return
        for j in range(start, 40):
            if LS[j] & cov:
                continue
            ext(cur + [j], cov | LS[j], j + 1)

    ext([], set(), 0)

    e = [tuple(1 if k == i else 0 for k in range(4)) for i in range(4)]

    def is_sp(A):
        for i, j in itertools.combinations(range(4), 2):
            u = tuple(sum(A[r][k] * e[i][k] for k in range(4)) % Q
                      for r in range(4))
            v = tuple(sum(A[r][k] * e[j][k] for k in range(4)) % Q
                      for r in range(4))
            if form(u, v) != form(e[i], e[j]):
                return False
        return True

    def act(A, v):
        return nm(tuple(sum(A[i][k] * v[k] for k in range(4)) % Q
                        for i in range(4)))

    rng = random.Random(11)
    gp = []
    while len(gp) < 3:
        A = tuple(tuple(rng.randrange(Q) for _ in range(4))
                  for _ in range(4))
        if is_sp(A):
            gp.append(tuple(idx[act(A, pts[p])] for p in range(N)))
    ident = tuple(range(N))
    G, seen, fr = [ident], {ident}, [ident]
    while fr:
        nx = []
        for a in fr:
            for g in gp:
                c = tuple(a[g[i]] for i in range(N))
                if c not in seen:
                    seen.add(c)
                    G.append(c)
                    nx.append(c)
        fr = nx

    supset = {frozenset(s): i for i, s in enumerate(supports)}
    cidx = {frozenset(c): i for i, c in enumerate(circuits)}
    lidx = {L: i for i, L in enumerate(lines)}

    def on45(g):
        return tuple(supset[frozenset(g[p] for p in s)] for s in supports)

    def on216(g):
        h = on45(g)
        return tuple(cidx[frozenset(h[v] for v in c)] for c in circuits)

    def onspread(g, s):
        return frozenset(lidx[tuple(sorted(g[p] for p in lines[j]))]
                         for j in s)

    g216 = [on216(g) for g in G]
    cstab = [i for i in range(len(G)) if g216[i][0] == 0]
    sp0 = [i for i, s in enumerate(spreads)
           if all(onspread(G[k], s) == s for k in cstab)]
    S0 = spreads[sp0[0]]
    sstab = sum(1 for g in G if onspread(g, S0) == S0)
    sidx = {s: i for i, s in enumerate(spreads)}

    mp = {}
    for k in range(len(G)):
        c = g216[k][0]
        if c not in mp:
            mp[c] = sidx[onspread(G[k], S0)]
        if len(mp) == 216:
            break
    bad = sum(1 for k in range(0, len(G), 7)
              if mp[g216[k][0]] != sidx[onspread(G[k], S0)])
    fib = collections.Counter(mp.values())
    sizes = dict(collections.Counter(fib.values()))
    eq = 0
    for k in range(0, len(G), 13):
        for c in (0, 17, 100, 215):
            if sidx[onspread(G[k], spreads[mp[c]])] != mp[g216[k][c]]:
                eq += 1

    print("THE 216 IS A PRINCIPAL 6-FIBRATION OVER THE DOUBLE-SIXES")
    print("=" * 72)
    print("  circuits %d, supports %d, spreads %d, PSp(4,3) %d"
          % (len(circuits), len(supports), len(spreads), len(G)))
    print("  circuit stabiliser order          %d" % len(cstab))
    print("  spread stabilisers containing it  %d   <- canonical" % len(sp0))
    print("  that spread stabiliser's order    %d" % sstab)
    print("  index of the circuit stabiliser   %d   = S5 <= S6"
          % (sstab // len(cstab)))
    print()
    print("  built by transport, not brute force:")
    print("     circuits mapped        %d of 216" % len(mp))
    print("     independent of g       %s (%d mismatches)" % (bad == 0, bad))
    print("     spreads hit            %d of 36" % len(fib))
    print("     fibre sizes            %s" % sizes)
    print("     equivariance           %s (%d violations)" % (eq == 0, eq))
    print()
    print("  BT810 identifies the 36 spreads with the 36 DOUBLE-SIXES, whose")
    print("  stabiliser is S6 on six letters, and the circuit stabiliser is")
    print("  its point stabiliser S5. So the 216 circuits are")
    print("  (double-six, letter) pairs, the fibre being Schlafli's letters.")
    print()
    print("  A TYPE SYSTEM, derived rather than designed: the type of a state")
    print("  is which double-six it lies over, its tag is which letter it")
    print("  carries, and because exactly ONE spread stabiliser contains each")
    print("  circuit stabiliser there is exactly one way to type a state.")
    print("  That is what the orphaned verify_w33_216_typed_microvm.ys was")
    print("  reaching for; the discipline is forced, not chosen.")

    ok = (len(circuits) == 216 and len(spreads) == 36 and len(G) == 25920
          and len(cstab) == 120 and len(sp0) == 1 and sstab == 720
          and sstab // len(cstab) == 6 and len(mp) == 216 and bad == 0
          and len(fib) == 36 and sizes == {6: 36} and eq == 0)

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data",
                         "the_216_is_a_principal_six_fibration.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.216-principal-six-fibration.v1",
                "valid": bool(ok),
                "wasOnlyNumerical": ("7f0d0a3 matched a stabiliser order of 720 "
                                     "and an index of 36 and noted 216 = 36 x 6; "
                                     "matching integers is how this repository "
                                     "gets things wrong, so the map had to be "
                                     "built"),
                "groupTheory": {
                    "circuitStabiliser": len(cstab),
                    "spreadStabilisersContainingIt": len(sp0),
                    "canonical": len(sp0) == 1,
                    "spreadStabiliser": sstab,
                    "index": sstab // len(cstab),
                    "inclusion": "S5 <= S6 at index 6",
                },
                "fibration": {
                    "method": ("transport, not brute force: stabilisers "
                               "conjugate so the map is equivariant, and "
                               "PSp(4,3) is transitive on both 216 and 36, so "
                               "all fibres have size 216/36 = 6"),
                    "circuitsMapped": len(mp),
                    "wellDefined": bad == 0,
                    "spreadsHit": len(fib),
                    "fibreSizes": {str(k): v for k, v in sizes.items()},
                    "equivarianceViolations": eq,
                },
                "theFibreHasAName": ("BT810 identifies the 36 spreads with the "
                                     "36 double-sixes, whose stabiliser is S6 "
                                     "on six letters, and the circuit "
                                     "stabiliser is its point stabiliser S5; so "
                                     "the 216 circuits are (double-six, letter) "
                                     "pairs and the fibre is Schlafli's six "
                                     "letters"),
                "whatTheK66Were": ("the other track's 36 copies of K(6,6) are "
                                   "this bundle seen through a correspondence"),
                "architectureReading": ("a TYPE SYSTEM, derived rather than "
                                        "designed: the type of a state is which "
                                        "double-six it lies over and its tag is "
                                        "which letter it carries, and because "
                                        "exactly one spread stabiliser contains "
                                        "each circuit stabiliser there is "
                                        "exactly one way to type a state -- the "
                                        "discipline the orphaned "
                                        "verify_w33_216_typed_microvm.ys was "
                                        "reaching for is forced, not chosen"),
                "boundary": ("the fibration is verified in full; the naming of "
                             "the fibre as Schlafli's letters rests on BT810's "
                             "spread / double-six identification and the "
                             "standard degree-6 action of S6, a dictionary "
                             "entry rather than a new computation. Nothing here "
                             "is a hardware claim and no module is written. "
                             "tau_2 is untouched"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
