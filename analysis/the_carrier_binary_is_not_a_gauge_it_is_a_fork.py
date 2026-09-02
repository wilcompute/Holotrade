#!/usr/bin/env python3
"""
The carrier binary is not a gauge choice. No symmetry of the substrate relates
the two options -- not chirality, not anything. It is a fork.

TWO UNSELECTABLE BINARIES, and the obvious guess that they are one.  This
corpus has found chirality unselectable from inside: PGSp(4,3) = PSp(4,3).2,
the outer element is a similitude with non-square multiplier, and W33-Theory's
Pass 346 showed the substrate can host the Standard Model's handedness without
selecting it. Then 36701d0 found a second binary: two inequivalent 216-state
carriers over one 36-state base, exchanged by the exceptional outer
automorphism of the fibre group S6. Two unselectable binaries in one object is
suspicious. Are they the same one?

THE TEST.  Build the outer element tau explicitly as a symplectic similitude
with multiplier 2 -- a non-square mod 3 -- and confirm it behaves:

    tau in PSp(4,3)                 False
    tau normalises PSp(4,3)         True
    tau preserves the line set      True

Then ask whether conjugation by tau carries the circuit stabiliser onto the
hemisystem-pair stabiliser class.

    G-conjugate to the pair stabiliser after tau   :  False
    G-conjugate to the pair stabiliser without tau :  False

So the carriers stay inequivalent in the FULL automorphism group PGSp(4,3), not
merely in PSp(4,3). Chirality does not swap them.

WHY NOT, and this is the part that matters.  tau fixes 6 of the 36 spreads and
normalises the spread stabiliser H, order 720, isomorphic to S6. So tau does
induce an automorphism of the fibre group -- the group whose outer
automorphism is supposed to exchange the two carrier types. Testing directly
whether some h in H induces the same map as tau on all of H:

    tau acts on H as an INNER automorphism   :  True
    out(S6) realised by a substrate symmetry :  FALSE

The one automorphism that WOULD exchange the carriers is not induced by
anything in PGSp(4,3). It exists abstractly, as S6's exceptional outer
automorphism, and the substrate does not contain it.

THE CONCLUSION, and it corrects my own wording.  36701d0 called the carrier
choice a "gauge choice". That is wrong, and the word matters: a gauge choice
implies a symmetry relating the options, so that the difference is
unobservable and any two choices are intertranslatable. Here there is no such
symmetry. The two carriers are inequivalent under every automorphism of the
substrate, and the automorphism that would relate them is not available.

    chirality        a symmetry of the substrate, unselectable from inside
    carrier choice   NOT a symmetry at all -- no automorphism relates the two

So it is not a gauge. It is a FORK. The two carriers are two different
machines over the same base, not two coordinate systems on one machine.

WHAT THAT FORBIDS.  There can be no gauge-transformation instruction. An
opcode is a permutation induced by a group element, and no group element -- in
PSp(4,3) or in PGSp(4,3) -- carries one carrier to the other. So a machine
built on the circuit carrier cannot be converted, rotated, or twisted into one
built on the pair carrier by any operation the substrate provides. Combined
with the parallel track's selector pattern (circuit sees 81 and not 64, the
pair carrier sees 64 and not 81), the consequence is concrete: the choice of
which module the machine can address is made once, at construction, and is
irreversible from inside.

SCOPE.  tau is constructed and verified here; the non-conjugacy is exhaustive
over all 25,920 elements before and after tau; the inner/outer verdict is a
direct search over all 720 elements of H. The claim is about PGSp(4,3), the
full automorphism group of W(3,3) -- not about abstract group isomorphisms,
which certainly do exchange the two S5 classes. The 64/81 selector pattern is
the parallel track's ad6e209, cited not reproduced. tau_2 is untouched.
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
SCRATCH = (r"C:\Users\wiljd\AppData\Local\Temp\claude"
           r"\c--Repos-Theory-of-Everything"
           r"\593b31ce-ce26-4c6b-9e86-0847c6c879fd\scratchpad")


def main():
    from ortools.sat.python import cp_model

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
    e = [tuple(1 if k == i else 0 for k in range(4)) for i in range(4)]

    def mult(A):
        lam = None
        for i, j in itertools.combinations(range(4), 2):
            u = tuple(sum(A[r][k] * e[i][k] for k in range(4)) % Q
                      for r in range(4))
            v = tuple(sum(A[r][k] * e[j][k] for k in range(4)) % Q
                      for r in range(4))
            f0, f1 = form(e[i], e[j]), form(u, v)
            if f0 == 0:
                if f1 != 0:
                    return None
                continue
            l = (f1 * pow(f0, -1, Q)) % Q
            if lam is None:
                lam = l
            elif lam != l:
                return None
        return lam

    def act(A, v):
        return nm(tuple(sum(A[i][k] * v[k] for k in range(4)) % Q
                        for i in range(4)))

    rng = random.Random(11)
    gp, tau = [], None
    while len(gp) < 3 or tau is None:
        A = tuple(tuple(rng.randrange(Q) for _ in range(4))
                  for _ in range(4))
        l = mult(A)
        if l == 1 and len(gp) < 3:
            gp.append(tuple(idx[act(A, pts[p])] for p in range(N)))
        elif l == 2 and tau is None:
            try:
                tau = tuple(idx[act(A, pts[p])] for p in range(N))
            except Exception:
                pass
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
    Gi = {g: i for i, g in enumerate(G)}

    def comp(a, b):
        return tuple(a[b[i]] for i in range(N))

    def inv(a):
        o = [0] * N
        for i in range(N):
            o[a[i]] = i
        return tuple(o)

    ti = inv(tau)
    tau_outer = tau not in seen
    tau_norm = all(comp(comp(tau, g), ti) in seen for g in gp)
    tau_lines = all(tuple(sorted(tau[p] for p in L)) in set(lines)
                    for L in lines)

    raw = open(os.path.join(SCRATCH, "circuits.txt")).read().strip().split("\n")
    circuits = [tuple(int(v) - 1 for v in c.split(","))
                for c in raw[0].split("|")[1].split(";")]
    supports = [tuple(int(v) - 1 for v in s.split(","))
                for s in raw[1].split("|")[1].split(";")]
    supset = {frozenset(s): i for i, s in enumerate(supports)}
    cidx = {frozenset(c): i for i, c in enumerate(circuits)}

    def on216(g):
        h = tuple(supset[frozenset(g[p] for p in s)] for s in supports)
        return tuple(cidx[frozenset(h[v] for v in c)] for c in circuits)

    cst = frozenset(i for i, g in enumerate(G) if on216(g)[0] == 0)
    m = cp_model.CpModel()
    x = [m.NewBoolVar("") for _ in range(N)]
    for L in lines:
        m.Add(sum(x[p] for p in L) == 2)
    hemis = []

    class C(cp_model.CpSolverSolutionCallback):
        def __init__(s, v):
            super().__init__()
            s.v = v

        def on_solution_callback(s):
            hemis.append(frozenset(i for i in range(N) if s.Value(s.v[i])))

    sv = cp_model.CpSolver()
    sv.parameters.enumerate_all_solutions = True
    sv.parameters.max_time_in_seconds = 900
    sv.Solve(m, C(x))
    allp = frozenset(range(N))
    P0 = frozenset((hemis[0], allp - hemis[0]))

    def onpair(g, P):
        return frozenset(frozenset(g[p] for p in h) for h in P)

    pst = frozenset(i for i, g in enumerate(G) if onpair(g, P0) == P0)

    def conj_by(Sidx, g, gi):
        return frozenset(Gi[comp(comp(g, G[s]), gi)] for s in Sidx)

    tcst = conj_by(cst, tau, ti)
    after = any(conj_by(tcst, g, inv(g)) == pst for g in G)
    before = any(conj_by(cst, g, inv(g)) == pst for g in G)

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
    lidx = {L: i for i, L in enumerate(lines)}

    def onspread(g, s):
        return frozenset(lidx[tuple(sorted(g[p] for p in lines[j]))]
                         for j in s)

    fixed = [s for s in spreads if onspread(tau, s) == s]
    S0 = fixed[0]
    H = [i for i, g in enumerate(G) if onspread(g, S0) == S0]
    Hs = frozenset(H)
    normH = frozenset(Gi[comp(comp(tau, G[h]), ti)] for h in H) == Hs
    timg = {h: Gi[comp(comp(tau, G[h]), ti)] for h in H}
    innerH = None
    for h in H:
        gh, ghi = G[h], inv(G[h])
        if all(Gi[comp(comp(gh, G[k]), ghi)] == timg[k] for k in H):
            innerH = h
            break

    print("THE CARRIER BINARY IS NOT A GAUGE -- IT IS A FORK")
    print("=" * 72)
    print("  tau (similitude, multiplier 2): in PSp %s, normalises PSp %s,"
          % (tau in seen, tau_norm))
    print("  preserves the lines %s" % tau_lines)
    print()
    print("  carriers G-conjugate after tau : %s" % after)
    print("  carriers G-conjugate before    : %s" % before)
    print("  -> inequivalent in the FULL group PGSp(4,3), not just PSp(4,3)")
    print()
    print("  tau fixes %d of the 36 spreads and normalises the spread"
          % len(fixed))
    print("  stabiliser H (order %d, S6): %s" % (len(H), normH))
    print("  tau acts on H as an INNER automorphism: %s" % (innerH is not None))
    print("  => out(S6) realised by a substrate symmetry: %s"
          % (innerH is None))
    print()
    print("  The one automorphism that WOULD exchange the carriers is not")
    print("  induced by anything in PGSp(4,3). So the choice is not a gauge --")
    print("  a gauge implies a symmetry relating the options. It is a FORK:")
    print("  two different machines over one base, not two coordinate systems")
    print("  on one machine. No gauge-transformation instruction can exist,")
    print("  and the choice of which module the machine addresses is made once")
    print("  at construction and is irreversible from inside.")

    ok = (tau_outer and tau_norm and tau_lines and not after and not before
          and normH and innerH is not None and len(fixed) == 6
          and len(H) == 720)

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data",
                         "the_carrier_binary_is_a_fork.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.carrier-binary-is-a-fork.v1",
                "valid": bool(ok),
                "theGuess": ("this corpus has two unselectable binaries -- "
                             "chirality (PGSp/PSp, unselectable from inside per "
                             "W33-Theory Pass 346) and the carrier choice "
                             "(36701d0) -- and two in one object is suspicious, "
                             "so: are they the same one?"),
                "tau": {"construction": "symplectic similitude, multiplier 2, "
                                        "a non-square mod 3",
                        "inPSp": tau in seen, "normalisesPSp": tau_norm,
                        "preservesLines": tau_lines},
                "carriersUnderTau": {
                    "conjugateAfterTau": after,
                    "conjugateBeforeTau": before,
                    "reading": ("inequivalent in the FULL automorphism group "
                                "PGSp(4,3), not merely in PSp(4,3); chirality "
                                "does not swap them"),
                },
                "whyNot": {
                    "spreadsFixedByTau": len(fixed),
                    "spreadStabiliserOrder": len(H),
                    "tauNormalisesIt": normH,
                    "tauActsInner": innerH is not None,
                    "outS6RealisedBySubstrate": innerH is None,
                    "reading": ("tau does induce an automorphism of the fibre "
                                "group S6, and it is INNER -- so the "
                                "exceptional outer automorphism that would "
                                "exchange the carrier types is not induced by "
                                "anything in PGSp(4,3)"),
                },
                "correctionToMyWording": {
                    "file": "36701d0",
                    "said": "gauge choice",
                    "wrong": ("a gauge choice implies a symmetry relating the "
                              "options, so the difference is unobservable and "
                              "the choices are intertranslatable"),
                    "correct": ("a FORK: the two carriers are inequivalent "
                                "under every automorphism of the substrate, and "
                                "the automorphism that would relate them is not "
                                "available"),
                },
                "contrast": {
                    "chirality": ("a symmetry of the substrate, unselectable "
                                  "from inside"),
                    "carrierChoice": ("not a symmetry at all -- no automorphism "
                                      "relates the two"),
                },
                "whatItForbids": ("no gauge-transformation instruction can "
                                  "exist: an opcode is a permutation induced by "
                                  "a group element, and no element of PSp(4,3) "
                                  "or PGSp(4,3) carries one carrier to the "
                                  "other, so a machine built on one cannot be "
                                  "converted into a machine built on the other "
                                  "by anything the substrate provides; with the "
                                  "parallel track's selector pattern this makes "
                                  "the choice of addressable module a "
                                  "construction-time decision, irreversible "
                                  "from inside"),
                "boundary": ("tau is constructed and verified here; the "
                             "non-conjugacy is exhaustive over all 25,920 "
                             "elements before and after tau; the inner/outer "
                             "verdict is a direct search over all 720 elements "
                             "of H. The claim concerns PGSp(4,3), the full "
                             "automorphism group of W(3,3), not abstract group "
                             "isomorphisms, which certainly do exchange the two "
                             "S5 classes. The 64/81 selector pattern is "
                             "ad6e209's, cited not reproduced. tau_2 is "
                             "untouched"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
