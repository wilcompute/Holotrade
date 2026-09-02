#!/usr/bin/env python3
"""
W33-Theory minimised the instruction COUNT. Nobody minimised the program
LENGTH, and the set they froze is not optimal for it.

WHAT THEY SETTLED.  BT1228 compressed the two-qutrit Clifford target from all
40 projective transvections to a concrete four-transvection generating set;
BT1230 ruled out one and two; BT1231 closed the gap exhaustively over all
C(40,3) = 9880 triples, whose closure histogram tops out at order 648. So the
minimal projective-transvection generating count is exactly

    m_min = 4,

which is a complete answer to the question they asked.

WHAT NOBODY ASKED.  A generating set has a second cost: the diameter of its
Cayley graph, which is the worst-case program length. b363f7c computed that for
the FULL transvection ISA. Running it on BT1228's minimal set gives the number
neither track had:

    BT1228's four-transvection set      Cayley diameter  11
                                        routing diameter  6
    the full 80-transvection ISA        Cayley diameter   4
                                        routing diameter  2

So minimality costs roughly THREE TIMES the program length in both measures.
Forty opcodes buy a worst case of four; four opcodes pay eleven. That is the
architectural tradeoff stated end to end, and both endpoints are now exact.

AND THEIR SET IS NOT LENGTH-OPTIMAL.  Sampling other four-transvection sets
that also generate the whole group, 257 of them, turns up one with Cayley
diameter 10. BT1228's achieves 11. Nothing is wrong with their certificate --
it was built to witness the COUNT, and it does that exhaustively -- but count
minimality and length minimality are different objectives, and only the first
had ever been optimised. A better four-instruction ISA exists.

A PORTABILITY CAVEAT WORTH RECORDING.  BT1228/1230/1231 use the symplectic
form J = [[0, I], [-I, 0]], pairing coordinates (0,2) and (1,3). Under the
other common pairing, (0,1) and (2,3), those same four vectors close to a group
of order 288 rather than 25,920. The four-vector certificate is therefore
convention-bound: it is a certificate about vectors AND a form, and quoting the
vectors alone does not transport. That is not an error in their work, which
states its J, but it is a trap for anything that reuses the numbers.

WHY IT MATTERS ARCHITECTURALLY.  The instruction set has two independent knobs
and the substrate answers them differently. Universality is cheap -- two
generators suffice for any simple group, four transvections suffice inside the
transvection family. Latency is not: the natural forty-opcode set is the only
one measured that reaches diameter four, and every compression away from it
costs program length roughly linearly in how far you compress.

SCOPE.  BT1228's diameters are exact, from full BFS over the group and over
every point. The diameter-10 alternative is the best of 257 sampled generating
sets, so it is an UPPER bound on the optimal four-transvection diameter, not a
proven minimum. The 216-carrier routing diameter is not computed here because
that labelling is bound to the control-plane's own convention rather than
BT1228's. tau_2 is untouched.
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

    # BT1228/1230/1231 convention: J = [[0,I],[-I,0]], pairing (0,2) and (1,3)
    def form_theirs(u, v):
        return (u[0] * v[2] - u[2] * v[0] + u[1] * v[3] - u[3] * v[1]) % Q

    # the other common pairing, for the portability check
    def form_alt(u, v):
        return (u[0] * v[1] - u[1] * v[0] + u[2] * v[3] - u[3] * v[2]) % Q

    pts = sorted({nm(v) for v in itertools.product(range(Q), repeat=4)
                  if any(v)})
    idx = {v: i for i, v in enumerate(pts)}
    ident = tuple(range(N))

    def transvection(vv, form, lam=1):
        out = []
        for p in range(N):
            x = pts[p]
            c = (lam * form(x, vv)) % Q
            out.append(idx[nm(tuple((x[k] + c * vv[k]) % Q
                                    for k in range(4)))])
        return tuple(out)

    def inv(a):
        o = [0] * N
        for i in range(N):
            o[a[i]] = i
        return tuple(o)

    def closure(gs):
        S, fr = {ident}, [ident]
        while fr:
            nx = []
            for a in fr:
                for g in gs:
                    c = tuple(a[g[i]] for i in range(N))
                    if c not in S:
                        S.add(c)
                        nx.append(c)
            fr = nx
        return len(S)

    def diam_group(gs):
        dist, fr, d = {ident: 0}, [ident], 0
        while fr:
            nx = []
            for a in fr:
                for g in gs:
                    c = tuple(a[g[i]] for i in range(N))
                    if c not in dist:
                        dist[c] = d + 1
                        nx.append(c)
            fr = nx
            if nx:
                d += 1
        return max(dist.values()), len(dist)

    def diam_states(perms, n):
        worst = 0
        for s0 in range(n):
            dist, fr, d = {s0: 0}, [s0], 0
            while fr:
                nx = []
                for s in fr:
                    for p in perms:
                        t = p[s]
                        if t not in dist:
                            dist[t] = d + 1
                            nx.append(t)
                fr = nx
                if nx:
                    d += 1
            if len(dist) < n:
                return None
            worst = max(worst, max(dist.values()))
        return worst

    BT = [(0, 0, 0, 2), (0, 2, 0, 0), (0, 0, 2, 2), (1, 0, 0, 0)]
    gens = [transvection(v, form_theirs) for v in BT]
    order_theirs = closure(gens)
    order_alt = closure([transvection(v, form_alt) for v in BT])
    S = gens + [inv(g) for g in gens]
    gd, reach = diam_group(S)
    d40 = diam_states(S, N)

    allT = [transvection(pts[p], form_theirs) for p in range(N)]
    fullS = allT + [inv(g) for g in allT]
    fgd, _ = diam_group(fullS)
    fd40 = diam_states(fullS, N)

    rng = random.Random(5)
    best, tested = None, 0
    for _ in range(400):
        S4 = rng.sample(range(N), 4)
        gs = [allT[i] for i in S4]
        if closure(gs) != 25920:
            continue
        tested += 1
        g2, _ = diam_group(gs + [inv(g) for g in gs])
        if best is None or g2 < best:
            best = g2

    print("MINIMAL INSTRUCTION COUNT IS NOT MINIMAL PROGRAM LENGTH")
    print("=" * 72)
    print("  BT1228's four-transvection set generates: %d (PSp(4,3): %s)"
          % (order_theirs, order_theirs == 25920))
    print()
    print("                          opcodes   Cayley diam   routing diam")
    print("  BT1228 minimal set          4          %2d            %d"
          % (gd, d40))
    print("  full transvection ISA      %d          %2d            %d"
          % (len(allT), fgd, fd40))
    print()
    print("  minimality costs about %.1fx on the group and %.1fx on routing"
          % (gd / fgd, d40 / fd40))
    print()
    print("  sampled %d other generating four-transvection sets;" % tested)
    print("  best Cayley diameter found: %d, against BT1228's %d" % (best, gd))
    print("  -> their set is count-minimal but NOT length-optimal: %s"
          % (best < gd))
    print()
    print("  PORTABILITY: under the other common pairing (0,1),(2,3) the same")
    print("  four vectors close to only %d. The certificate is about vectors"
          % order_alt)
    print("  AND a form; quoting the vectors alone does not transport.")

    ok = (order_theirs == 25920 and order_alt != 25920 and gd == 11
          and d40 == 6 and fgd == 4 and fd40 == 2 and best is not None
          and best < gd and reach == 25920)

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data",
                         "minimal_count_is_not_minimal_length.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.count-vs-length-minimality.v1",
                "valid": bool(ok),
                "whatTheySettled": ("BT1228 compressed the target to four "
                                    "projective transvections, BT1230 ruled out "
                                    "one and two, BT1231 closed the gap "
                                    "exhaustively over all C(40,3) = 9880 "
                                    "triples whose closures top out at 648; so "
                                    "the minimal generating count is exactly 4"),
                "whatNobodyAsked": ("a generating set also has a diameter, which "
                                    "is the worst-case program length"),
                "bt1228Set": {
                    "vectors": [list(v) for v in BT],
                    "generates": order_theirs,
                    "opcodes": 4,
                    "cayleyDiameter": gd,
                    "routingDiameter": d40,
                    "reached": reach,
                },
                "fullTransvectionISA": {
                    "opcodes": len(allT),
                    "cayleyDiameter": fgd,
                    "routingDiameter": fd40,
                },
                "minimalityCost": {
                    "group": gd / fgd,
                    "routing": d40 / fd40,
                    "reading": ("forty opcodes buy a worst case of four; four "
                                "opcodes pay eleven"),
                },
                "notLengthOptimal": {
                    "sampled": tested,
                    "bestFound": best,
                    "bt1228": gd,
                    "theirSetIsBeaten": best < gd,
                    "reading": ("nothing is wrong with their certificate -- it "
                                "was built to witness the COUNT and does that "
                                "exhaustively -- but count minimality and "
                                "length minimality are different objectives and "
                                "only the first had been optimised"),
                },
                "portabilityCaveat": {
                    "theirForm": "J = [[0,I],[-I,0]], pairing (0,2) and (1,3)",
                    "underOtherPairing": order_alt,
                    "reading": ("under the pairing (0,1),(2,3) the same four "
                                "vectors close to %d rather than 25920, so the "
                                "certificate is about vectors AND a form; "
                                "quoting the vectors alone does not transport. "
                                "Not an error in their work, which states its "
                                "J, but a trap for anything reusing the numbers"
                                % order_alt),
                },
                "architecturalReading": ("the instruction set has two "
                                         "independent knobs and the substrate "
                                         "answers them differently: "
                                         "universality is cheap, latency is "
                                         "not, and every compression away from "
                                         "the natural forty-opcode set costs "
                                         "program length"),
                "boundary": ("BT1228's diameters are exact, from full BFS over "
                             "the group and over every point; the diameter-%d "
                             "alternative is the best of %d sampled generating "
                             "sets and is an UPPER bound on the optimal "
                             "four-transvection diameter, not a proven minimum. "
                             "The 216-carrier routing diameter is not computed "
                             "here because that labelling is bound to the "
                             "control plane's convention rather than BT1228's. "
                             "tau_2 is untouched" % (best, tested)),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
