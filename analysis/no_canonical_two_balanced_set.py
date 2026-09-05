#!/usr/bin/env python3
"""
There is no evidence of a canonical 2-balanced set. The uniform one I called
more canonical carries no symmetry beyond the C5 that was imposed on it.

WHAT I SUGGESTED.  c1f4357 refuted the idea that the hemisystem split in
5aa4ff1's witness was a property of 2-balanced sets -- one solution in sixty
has it -- and then offered a replacement: among the twenty-two row profiles is
the perfectly uniform one, all forty points carrying exactly five partners, and
"if any single 2-balanced set deserves to be called canonical it is that one ...
40 x 5 = 200 needs no explanation". That was an aesthetic judgement dressed as a
structural one, and it does not survive.

IT CARRIES NO EXTRA SYMMETRY.

    row-uniform solutions found                    12
    stabiliser in PSp(4,3)                          5, every one
    doubly uniform (rows AND columns) found         12
    stabiliser in PSp(4,3)                          5, every one

Five is exactly the C5 that was imposed to make the search tractable. Nothing
in these objects is fixed by anything else, so "uniform" buys no structure at
all -- the stabiliser is the same as for the hemisystem witness and for every
other solution in the family.

AND ROW-UNIFORM DOES NOT EVEN IMPLY COLUMN-UNIFORM.  Of six row-uniform
solutions inspected, two had column profiles {4:15, 6:15, 8:5, 2:5}. The
"uniformity" I was pointing at is one-sided unless both margins are constrained
explicitly, and constraining both changes nothing about the symmetry.

NOR IS ANY OF THEM A SYMMETRIC RELATION.  X is never closed under swapping the
two coordinates, in any solution examined.

THE PATTERN IS WORTH NAMING.  Two consecutive instincts about this object --
"the hemisystem split explains the size" and then "the uniform profile is the
canonical one" -- both looked structural and both failed on inspection. The
balance equations by themselves do not single anything out; the solution space
is large, heterogeneous, and flat, and every apparent landmark in it so far has
been an artefact of which solution the solver happened to print first.

SCOPE.  All solutions here are C5-invariant, so the stabiliser can never come
out below 5 and the measurement is really "is it bigger than 5" -- it is not, in
24 solutions across two constraint sets. Twelve of each is a capped sample, not
an enumeration, so this shows no canonical object was FOUND, not that none
exists. The stabiliser is computed against the full 25,920-element PSp(4,3)
acting diagonally, not sampled. tau_2 is untouched.
"""

import collections
import itertools
import json
import os
import sys

from ortools.sat.python import cp_model

ROOT = r"C:\Repos\Holotrade"
Q, D = 3, 4


def main():
    def mul(A, B):
        return tuple(tuple(sum(A[i][k] * B[k][j] for k in range(D)) % Q
                           for j in range(D)) for i in range(D))

    I = tuple(tuple(1 if i == j else 0 for j in range(D)) for i in range(D))

    def form(u, v):
        return (u[0] * v[2] - u[2] * v[0] + u[1] * v[3] - u[3] * v[1]) % Q

    E = [tuple(1 if k == j else 0 for k in range(D)) for j in range(D)]

    def tv(vv, lam):
        return tuple(tuple(((1 if i == j else 0)
                            + lam * form(E[j], vv) * vv[i]) % Q
                           for j in range(D)) for i in range(D))

    def nm(v):
        i = next(k for k, x in enumerate(v) if x % Q)
        z = pow(v[i] % Q, -1, Q)
        return tuple((z * x) % Q for x in v)

    vecs = [v for v in itertools.product(range(Q), repeat=D) if any(v)]
    pts = sorted({nm(v) for v in vecs})
    pidx = {p: i for i, p in enumerate(pts)}
    T = sorted({tv(v, l) for v in vecs for l in (1, 2)} - {I})
    wl = set()
    for a, b in itertools.combinations(pts, 2):
        if form(a, b) % Q:
            continue
        S = set()
        for x in range(Q):
            for y in range(Q):
                if x == y == 0:
                    continue
                w = tuple((x * a[k] + y * b[k]) % Q for k in range(D))
                if any(w):
                    S.add(nm(w))
        if len(S) == 4 and all(form(u, v) % Q == 0
                               for u, v in itertools.combinations(sorted(S), 2)):
            wl.add(frozenset(pidx[z] for z in S))
    WL = [sorted(l) for l in wl]
    NL = len(WL)

    def perm(A):
        return tuple(pidx[nm(tuple(sum(A[i][k] * pts[j][k] for k in range(D)) % Q
                                   for i in range(D)))] for j in range(40))

    seenm, fr = {I}, [I]
    while fr:
        nx = []
        for A in fr:
            for t in T:
                B = mul(t, A)
                if B not in seenm:
                    seenm.add(B)
                    nx.append(B)
        fr = nx
    G = sorted({perm(A) for A in seenm})
    idp = tuple(range(40))
    g5 = None
    for g in G:
        o, cur = 1, g
        while cur != idp:
            cur = tuple(g[x] for x in cur)
            o += 1
        if o == 5:
            g5 = g
            break

    par = list(range(1600))

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    for p_ in range(40):
        for r in range(40):
            a, b = find(p_ * 40 + r), find(g5[p_] * 40 + g5[r])
            if a != b:
                par[a] = b
    orb = collections.defaultdict(list)
    for c in range(1600):
        orb[find(c)].append(c)
    groups = list(orb.values())
    c2g = {}
    for gi, cells in enumerate(groups):
        for c in cells:
            c2g[c] = gi

    def solve(both, cap=12):
        mdl = cp_model.CpModel()
        y = [mdl.NewBoolVar("") for _ in groups]
        for L in range(NL):
            for M in range(NL):
                t = collections.Counter()
                for p_ in WL[L]:
                    for r in WL[M]:
                        t[c2g[p_ * 40 + r]] += 1
                mdl.Add(sum(t[gi] * y[gi] for gi in t) == 2)
        for p_ in range(40):
            tr, tc = collections.Counter(), collections.Counter()
            for r in range(40):
                tr[c2g[p_ * 40 + r]] += 1
                tc[c2g[r * 40 + p_]] += 1
            mdl.Add(sum(tr[gi] * y[gi] for gi in tr) == 5)
            if both:
                mdl.Add(sum(tc[gi] * y[gi] for gi in tc) == 5)

        class C(cp_model.CpSolverSolutionCallback):
            def __init__(s_):
                super().__init__()
                s_.sols = []

            def on_solution_callback(s_):
                s_.sols.append(sorted(c for gi in range(len(y))
                                      if s_.Value(y[gi]) for c in groups[gi]))
                if len(s_.sols) >= cap:
                    s_.StopSearch()

        cb = C()
        s = cp_model.CpSolver()
        s.parameters.max_time_in_seconds = 300
        s.parameters.num_search_workers = 1
        s.parameters.enumerate_all_solutions = True
        s.Solve(mdl, cb)
        out = []
        for X in cb.sols:
            S = set(X)
            stab = sum(1 for g in G
                       if {g[c // 40] * 40 + g[c % 40] for c in X} == S)
            cols = collections.Counter(c % 40 for c in X)
            out.append({
                "size": len(X), "stabiliser": stab,
                "columnProfile": {str(k): v for k, v in
                                  collections.Counter(cols.values()).items()},
                "columnUniform": set(cols.values()) == {5},
                "symmetric": all((c % 40) * 40 + (c // 40) in S for c in X)})
        return out

    rowonly = solve(False)
    both = solve(True)

    print("NO CANONICAL 2-BALANCED SET")
    print("=" * 72)
    print("  c1f4357 called the uniform solution 'canonical'. That was an")
    print("  aesthetic judgement dressed as a structural one.")
    print()
    print("  row-uniform solutions          %2d ; stabilisers %s"
          % (len(rowonly), sorted({r["stabiliser"] for r in rowonly})))
    print("  doubly uniform (rows+columns)  %2d ; stabilisers %s"
          % (len(both), sorted({r["stabiliser"] for r in both})))
    print("  five is exactly the C5 imposed to make the search tractable.")
    print()
    print("  row-uniform implies column-uniform: %s"
          % all(r["columnUniform"] for r in rowonly))
    print("  any solution a SYMMETRIC relation:  %s"
          % any(r["symmetric"] for r in rowonly + both))
    print()
    print("  THE PATTERN: two consecutive instincts about this object -- the")
    print("  hemisystem split 'explains the size', then the uniform profile is")
    print("  'canonical' -- both looked structural and both failed on")
    print("  inspection. The balance equations single nothing out; the space")
    print("  is large, heterogeneous and flat, and every apparent landmark so")
    print("  far has been an artefact of which solution printed first.")

    ok = (len(rowonly) > 0 and len(both) > 0
          and {r["stabiliser"] for r in rowonly} == {5}
          and {r["stabiliser"] for r in both} == {5}
          and not any(r["symmetric"] for r in rowonly + both))

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "no_canonical_two_balanced_set.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.no-canonical-2-balanced.v1",
                "valid": bool(ok),
                "whatISuggested": ("c1f4357 refuted the hemisystem structure as "
                                   "a property and then offered a replacement: "
                                   "'if any single 2-balanced set deserves to be "
                                   "called canonical it is that one'. That was "
                                   "an aesthetic judgement dressed as a "
                                   "structural one"),
                "rowUniform": rowonly,
                "doublyUniform": both,
                "stabilisers": {
                    "rowUniform": sorted({r["stabiliser"] for r in rowonly}),
                    "doublyUniform": sorted({r["stabiliser"] for r in both}),
                    "imposedC5": 5,
                    "reading": ("five is exactly the C5 imposed to make the "
                                "search tractable; nothing in these objects is "
                                "fixed by anything else, so 'uniform' buys no "
                                "structure at all"),
                },
                "rowUniformDoesNotImplyColumnUniform": not all(
                    r["columnUniform"] for r in rowonly),
                "noneIsSymmetric": not any(r["symmetric"]
                                           for r in rowonly + both),
                "thePattern": ("two consecutive instincts about this object -- "
                               "the hemisystem split 'explains the size', then "
                               "the uniform profile is 'canonical' -- both "
                               "looked structural and both failed on "
                               "inspection. The balance equations by themselves "
                               "single nothing out: the solution space is large, "
                               "heterogeneous and flat, and every apparent "
                               "landmark in it so far has been an artefact of "
                               "which solution the solver happened to print "
                               "first"),
                "boundary": ("all solutions here are C5-invariant so the "
                             "stabiliser can never come out below 5, and the "
                             "measurement is really 'is it bigger than 5' -- it "
                             "is not, in 24 solutions across two constraint "
                             "sets. Twelve of each is a CAPPED sample, not an "
                             "enumeration, so this shows no canonical object was "
                             "FOUND, not that none exists. The stabiliser is "
                             "computed against the full 25,920-element PSp(4,3) "
                             "acting diagonally, not sampled. tau_2 is "
                             "untouched"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
