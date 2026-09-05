#!/usr/bin/env python3
"""
The hemisystem structure in 5aa4ff1's witness is RARE, not typical: one
solution in sixty has it, and the solution space is heterogeneous.

WHAT 5aa4ff1 SAID.  It found a 2-balanced set, noticed that its row counts
split the forty points 20/20 and that BOTH halves are hemisystems, and wrote
"the object sits over a COMPLEMENTARY PAIR of hemisystems ... 20 x 6 + 20 x 4 =
200 is where the size comes from. That was not imposed; the solver was given
only the balance equations."

Every word of that is true OF THAT WITNESS. But "where the size comes from"
invites reading it as a property of 2-balanced sets, and this repository's own
rule is that a structure with no exceptions on one sample is not a finding until
the sample is varied. It was one witness.

VARYING IT.  Enumerating C5-invariant 2-balanced sets and looking at every row
profile:

    solutions collected                                 60
    distinct row-count profiles among them              22
    solutions whose row-classes are ALL hemisystems      1

One. The structure was a property of the witness I happened to print, not of the
object. Had I stopped at the first solution and generalised, that would have
been the fifth failure mode in CLAUDE.md exactly.

THE SPACE IS HETEROGENEOUS, AND ONE PROFILE IS ARGUABLY MORE CANONICAL.  Among
the twenty-two profiles is the perfectly UNIFORM one -- all forty points
carrying exactly five partners each -- which occurs three times. If any single
2-balanced set deserved to be called canonical it is that one, not the
hemisystem-split witness: a uniform profile needs no explanation for "where the
size comes from", since 40 x 5 = 200 immediately.

WHAT SURVIVES.  m = 2 is feasible, the witness is verified, and the spectrum
result (c74fbb1) is untouched -- none of that depended on the row structure. The
hemisystem observation stays true of its witness and stops being suggestive of
anything more.

SCOPE.  Sixty solutions is a sample, not an enumeration: the search was capped,
and all sixty are C5-invariant, so nothing here describes 2-balanced sets
without that symmetry. That makes the negative STRONGER, not weaker -- one
hemisystem case in sixty already refutes universality -- but it means the true
proportion is unmeasured, and the profile count is a lower bound on the
variety. tau_2 is untouched.
"""

import collections
import itertools
import json
import os
import sys

from ortools.sat.python import cp_model

ROOT = r"C:\Repos\Holotrade"
Q = 3
D = 4
CAP = 60


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

    idp = tuple(range(40))
    g5 = None
    seen, fr = {I}, [I]
    while fr and g5 is None:
        nx = []
        for A in fr:
            for t in T:
                B = mul(t, A)
                if B not in seen:
                    seen.add(B)
                    nx.append(B)
                    pm = perm(B)
                    o, cur = 1, pm
                    while cur != idp:
                        cur = tuple(pm[x] for x in cur)
                        o += 1
                    if o == 5 and g5 is None:
                        g5 = pm
        fr = nx

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

    mdl = cp_model.CpModel()
    y = [mdl.NewBoolVar("") for _ in groups]
    for L in range(NL):
        for M in range(NL):
            t = collections.Counter()
            for p_ in WL[L]:
                for r in WL[M]:
                    t[c2g[p_ * 40 + r]] += 1
            mdl.Add(sum(t[gi] * y[gi] for gi in t) == 2)

    class Collect(cp_model.CpSolverSolutionCallback):
        def __init__(self):
            super().__init__()
            self.sols = []

        def on_solution_callback(self):
            X = [c for gi in range(len(y)) if self.Value(y[gi])
                 for c in groups[gi]]
            self.sols.append(sorted(X))
            if len(self.sols) >= CAP:
                self.StopSearch()

    cb = Collect()
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = 420
    s.parameters.num_search_workers = 1
    s.parameters.enumerate_all_solutions = True
    s.Solve(mdl, cb)

    prof = collections.Counter()
    hemi = collections.Counter()
    uniform = 0
    for X in cb.sols:
        rows = collections.Counter(c // 40 for c in X)
        pkey = tuple(sorted(collections.Counter(rows.values()).items()))
        prof[pkey] += 1
        if pkey == ((5, 40),):
            uniform += 1
        allh = True
        for cnt in set(rows.values()):
            Sset = {pp for pp in range(40) if rows[pp] == cnt}
            pr = collections.Counter(len(Sset & set(l)) for l in WL)
            if dict(pr) != {2: NL}:
                allh = False
        hemi[allh] += 1

    print("THE HEMISYSTEM STRUCTURE WAS RARE")
    print("=" * 72)
    print("  5aa4ff1 found one 2-balanced set, saw its rows split 20/20 into")
    print("  two hemisystems, and said that is 'where the size comes from'.")
    print("  True of that witness. It was one witness.")
    print()
    print("  solutions collected                              %3d" % len(cb.sols))
    print("  distinct row-count profiles among them           %3d" % len(prof))
    print("  solutions whose row-classes are ALL hemisystems  %3d"
          % hemi[True])
    print()
    print("  One. The structure was a property of the witness I happened to")
    print("  print, not of the object.")
    print()
    print("  and among the profiles is the perfectly UNIFORM one -- all forty")
    print("  points carrying exactly five partners -- occurring %d times."
          % uniform)
    print("  If any 2-balanced set deserves to be called canonical it is that")
    print("  one: 40 x 5 = 200 needs no explanation at all.")
    print()
    print("  WHAT SURVIVES: m = 2 is feasible, the witness is verified, and")
    print("  the spectrum result c74fbb1 is untouched -- none of it depended")
    print("  on the row structure.")

    ok = (len(cb.sols) >= 40 and hemi[True] <= 2 and len(prof) >= 10
          and uniform >= 1)

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "hemisystem_structure_was_rare.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.hemisystem-structure-rare.v1",
                "valid": bool(ok),
                "whatWasSaid": ("5aa4ff1 found a 2-balanced set, noticed its row "
                                "counts split the forty points 20/20 with BOTH "
                                "halves hemisystems, and wrote that this is "
                                "'where the size comes from'. True of that "
                                "witness -- but the phrasing invites reading it "
                                "as a property of 2-balanced sets, and it was "
                                "ONE witness"),
                "varyingIt": {
                    "solutionsCollected": len(cb.sols),
                    "distinctRowProfiles": len(prof),
                    "allRowClassesAreHemisystems": hemi[True],
                    "notHemisystems": hemi[False],
                    "reading": ("the structure was a property of the witness "
                                "that happened to be printed, not of the object; "
                                "stopping at the first solution and generalising "
                                "would have been CLAUDE.md's fifth failure mode "
                                "exactly"),
                },
                "uniformProfileExists": {
                    "count": uniform,
                    "profile": "all forty points carry exactly five partners",
                    "reading": ("if any single 2-balanced set deserves to be "
                                "called canonical it is this one, not the "
                                "hemisystem-split witness: 40 x 5 = 200 needs no "
                                "explanation for where the size comes from"),
                },
                "profiles": {str(k): v for k, v in prof.items()},
                "whatSurvives": ("m = 2 is feasible, the witness is verified, "
                                 "and the spectrum result c74fbb1 is untouched "
                                 "-- none of that depended on the row structure. "
                                 "The hemisystem observation stays true of its "
                                 "witness and stops being suggestive of anything "
                                 "more"),
                "boundary": ("sixty solutions is a SAMPLE, not an enumeration: "
                             "the search was capped and all sixty are "
                             "C5-invariant, so nothing here describes 2-balanced "
                             "sets without that symmetry. That makes the "
                             "negative STRONGER, not weaker -- one hemisystem "
                             "case in sixty already refutes universality -- but "
                             "the true proportion is unmeasured and the profile "
                             "count is a LOWER bound on the variety. tau_2 is "
                             "untouched"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
