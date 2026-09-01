#!/usr/bin/env python3
"""
The depth-3 obstruction is not a missing line. The line exists in PG(3,3) and
fails to be a measurement context.

WHERE THIS STARTS.  one_seed_is_a_depth_two_fact.py showed no single Sp(4,3)
orbit blocks at depth 3, and located the obstruction: of the C(40,3) = 9,880
triples of W(3,3) lines, 1,080 admit no common transversal LINE OF W(3,3), so
the cocollinear triples cannot reach the corresponding tiles.

That reads like an absence. It is not.

THE AMBIENT PICTURE.  W(3,3) lives inside PG(3,3), which has 130 lines in
total, of which exactly 40 are totally isotropic -- and those 40 ARE the lines
of W(3,3). The other 90 are ordinary projective lines carrying pairs of
non-commuting observables.

Classically, three pairwise skew lines of PG(3,q) determine a unique regulus,
and the OPPOSITE regulus supplies q+1 transversals -- always, with no
exception. So a triple of skew W(3,3) lines never actually lacks transversals.
It lacks isotropic ones.

Computed over all 1,080, and the answer is perfectly uniform:

    (ambient transversals, of which isotropic)  ->  count
    (4, 0)                                      ->  1080

Every single transversal-free triple has the full complement of FOUR
transversals in PG(3,3), and in every case ZERO of them are totally isotropic.
Not "few". Not "usually none". Exactly four, exactly none, 1,080 times.

AND THEY ARE ONE ORBIT.  Starting from a single transversal-free triple and
closing under Sp(4,3) reaches all 1,080. So this is not a scattered accident
but a single distinguished class of the group.

WHAT THE OBSTRUCTION ACTUALLY IS.  Not "the connecting line does not exist" but
"the connecting line is not a measurement context". In Pauli terms: three
mutually disjoint contexts always admit a projective line meeting all three,
and for these 1,080 configurations that line carries NON-COMMUTING observables,
so it is not a context and cannot be measured jointly.

The depth-3 failure is therefore invisible from inside W(3,3). Seen only in
the quadrangle, a transversal simply is not there. Seen in PG(3,3), it is there
four times over and each copy fails the isotropy condition. The obstruction
lives in the gap between the projective space and its symplectic polarity --
which is exactly the gap between "a set of observables" and "a set of jointly
measurable observables".

HOW THIS FITS.  Every certification result in this thread has turned on the
same distinction, from the opposite side. Ovoids fail for odd q, the free lunch
is rank two, the non-commuting orbit is bigger than the commuting one and still
fails at depth 2 -- each time the commuting condition, not the counting, does
the work. Here it does the work again: 4 transversals, 0 usable.

SCOPE.  This explains the depth-3 obstruction; it does not remove it, and it
does not bear on tau_2, which stays open in [111, 115]. The regulus fact is
classical projective geometry; what is computed here is that the isotropic
count is uniformly zero across all 1,080 and that they form one orbit.
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
    def nm(v):
        i = next(k for k, x in enumerate(v) if x % Q)
        z = pow(v[i] % Q, -1, Q)
        return tuple((z * x) % Q for x in v)

    def form(u, v):
        return (u[0] * v[1] - u[1] * v[0] + u[2] * v[3] - u[3] * v[2]) % Q

    allpts = sorted({nm(v) for v in itertools.product(range(Q), repeat=4)
                     if any(v)})
    idx = {v: i for i, v in enumerate(allpts)}

    def span_line(a, b):
        S = set()
        for x, y in itertools.product(range(Q), repeat=2):
            if x == y == 0:
                continue
            w = tuple((x * allpts[a][k] + y * allpts[b][k]) % Q
                      for k in range(4))
            if any(w):
                S.add(idx[nm(w)])
        return tuple(sorted(S))

    alllines = set()
    for a, b in itertools.combinations(range(N), 2):
        L = span_line(a, b)
        if len(L) == 4:
            alllines.add(L)
    alllines = sorted(alllines)
    iso = [L for L in alllines
           if all(form(allpts[x], allpts[y]) == 0
                  for x, y in itertools.combinations(L, 2))]
    isoset = set(iso)
    isosets = [set(L) for L in iso]

    print("THE DEPTH-3 OBSTRUCTION IS NON-ISOTROPY")
    print("=" * 72)
    print("  PG(3,3): %d points, %d lines, of which %d are totally isotropic"
          % (len(allpts), len(alllines), len(iso)))
    print("  -- and those %d ARE the lines of W(3,3). The other %d carry"
          % (len(iso), len(alllines) - len(iso)))
    print("  pairs of NON-COMMUTING observables.")
    print()

    free = []
    for i, j, k in itertools.combinations(range(len(iso)), 3):
        if any(isosets[t] & isosets[i] and isosets[t] & isosets[j]
               and isosets[t] & isosets[k] for t in range(len(iso))):
            continue
        free.append((i, j, k))

    stats = collections.Counter()
    for (i, j, k) in free:
        tr = [L for L in alllines
              if (set(L) & isosets[i]) and (set(L) & isosets[j])
              and (set(L) & isosets[k])]
        stats[(len(tr), sum(1 for L in tr if L in isoset))] += 1

    print("  transversal-free triples of W(3,3) lines: %d" % len(free))
    print("  (ambient transversals, of which isotropic) -> count:")
    for kk, vv in sorted(stats.items()):
        print("     %s -> %d" % (kk, vv))
    uniform = list(stats.keys()) == [(4, 0)]
    print("  uniform (4 transversals, 0 isotropic) in every case: %s" % uniform)
    print()

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

    rng = random.Random(5)
    gens = []
    while len(gens) < 5:
        A = tuple(tuple(rng.randrange(Q) for _ in range(4)) for _ in range(4))
        if is_sp(A):
            gens.append(tuple(idx[act(A, allpts[p])] for p in range(N)))
    lidx = {L: t for t, L in enumerate(iso)}
    freeset = {frozenset(t) for t in free}
    seed = next(iter(freeset))
    orbit, fr = {seed}, [seed]
    while fr:
        nx = []
        for T in fr:
            for g in gens:
                img = frozenset(lidx[tuple(sorted(g[p] for p in iso[t]))]
                                for t in T)
                if img not in orbit:
                    orbit.add(img)
                    nx.append(img)
        fr = nx
    single = len(orbit) == len(freeset)
    print("  orbit of one such triple under Sp(4,3): %d of %d -> single orbit: %s"
          % (len(orbit), len(freeset), single))
    print()
    print("  So the obstruction is NOT 'the connecting line does not exist'.")
    print("  It is 'the connecting line is not a measurement context'. Three")
    print("  mutually disjoint contexts always admit a projective line meeting")
    print("  all three; for these 1,080 it carries NON-COMMUTING observables.")
    print()
    print("  The failure is invisible from inside W(3,3) -- there the")
    print("  transversal simply is not there. In PG(3,3) it is there four")
    print("  times over, and each copy fails isotropy.")

    ok = (len(iso) == 40 and len(alllines) == 130 and len(free) == 1080
          and uniform and single)

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data",
                         "the_depth3_obstruction_is_non_isotropy.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.depth3-obstruction-non-isotropy.v1",
                "valid": bool(ok),
                "ambient": {"points": len(allpts), "lines": len(alllines),
                            "isotropicLines": len(iso),
                            "nonIsotropicLines": len(alllines) - len(iso),
                            "note": ("the isotropic lines ARE the lines of "
                                     "W(3,3); the rest carry non-commuting "
                                     "pairs")},
                "transversalFreeTriples": len(free),
                "transversalProfile": {str(k): v for k, v in stats.items()},
                "uniformFourZero": uniform,
                "singleOrbit": single,
                "orbitSize": len(orbit),
                "classicalFact": ("three pairwise skew lines of PG(3,q) "
                                  "determine a regulus whose opposite regulus "
                                  "gives q+1 transversals, always"),
                "obstruction": ("not that the connecting line is missing, but "
                                "that it is not a measurement context: the "
                                "transversal exists projectively and carries "
                                "NON-COMMUTING observables"),
                "invisibleFromInside": ("seen only in W(3,3) the transversal is "
                                        "absent; seen in PG(3,3) it is present "
                                        "four times and each copy fails "
                                        "isotropy"),
                "fitsThePattern": ("every certification result in this thread "
                                   "turns on commuting rather than counting; "
                                   "here again 4 transversals, 0 usable"),
                "boundary": ("this explains the depth-3 obstruction, does not "
                             "remove it, and does not bear on tau_2, which "
                             "stays open in [111, 115]"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
